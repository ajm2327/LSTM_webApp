from flask import Flask, request, jsonify
from flask_login import LoginManager
from flask_cors import CORS
from models.lstm_model import StockPredictor
from utils.metrics import MetricsManager
from utils.logger_config import setup_logging
from database.db import db, migrate
from models.user import User
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
import yfinance as yf
import os
import json
from auth.routes import auth, login_manager
from auth.api_keys import api_keys
from dotenv import load_dotenv
from background.tasks import init_background_tasks
from config import init_config


load_dotenv()

#set environment variable for tensorflow GPU (just getting rid of missing GPU error)
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

#initialize logging system
loggers = setup_logging()
logger = logging.getLogger('api')


#Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'

#initialize all configurations
config = init_config(app)

#initialize extensions
db.init_app(app)
migrate.init_app(app,db)
CORS(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

#initialize stock predictor
predictor = StockPredictor()
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(api_keys, url_prefix='/api')

#initialize background tasks
background_tasks = init_background_tasks(app)
app.task_manager = background_tasks



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def validate_ticker(ticker):
    """validate if ticker exists and can be fetched"""
    try:
        stock = yf.Ticker(ticker)
        #try to get info - will fall if ticker doesn't exist
        info = stock.info
        return True
    except:
        return False
    
def validate_dates(start_date, end_date):
    """Validate date formats and ranges"""
    try:
        #convert string dates to datetime objects
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        #check if end date is after start date
        if end <= start:
            return False, "End date must be after start date"
        
        #check if date range is reasonable
        if (end - start) > timedelta(days = 365*20):
            return False, "Date range too large (max 20 years)"
        
        #check if end date is not in the future
        if end > datetime.now():
            return False, "End date cannot be in the future"
        
        #check if start date isn't too old (before 1980)
        if start.year < 1980:
            return False, "Start date cannot be before 1980"
        
        return True, "Dates valid"
    except ValueError:
        return False, "Invalid date format. Use YYY-MM-DD"

# Load pre-trained model on startup

try:
    predictor.load_model()
    logging.info("Model loaded successfully")
except Exception as e:
    logging.error(f"Error loading model: {str(e)}")

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "endpoints": {
            "/predict": "POST - Make stock predictions",
            "/health": "GET - Check API Health"
        }
    })

@app.route('/models', methods=['GET'])
def list_models():
    """List all available model versions"""
    try:
        models_path = 'models_saved/'
        versions = []

        for version_dir in sorted(os.listdir(models_path)):
            metadata_path = os.path.join(models_path, version_dir, 'metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    versions.append(metadata)
        return jsonify({
            'versions': versions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/models/<version>', methods=['GET'])
def model_info(version):
    """Get information about a specific model version"""
    try:
        models_path = 'models_saved/'
        #list all directories that start with v{version}_
        matching_dirs = [d for d in os.listdir(models_path) if d.startswith(f'v{version}_')]

        if not matching_dirs:
            return jsonify({'error': 'Version not found'}), 404
        
        #get the most recent version if multiple exist
        version_dir = sorted(matching_dirs)[-1]
        metadata_path = os.path.join(models_path, version_dir, 'metadata.json')

        if not os.path.exists(metadata_path):
            return jsonify({'error': 'Version metadata not found'}), 404
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        return jsonify(metadata)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': f'No data provided'}), 400
        version = data.get('model_version', None) #version parameter

        if version:
            predictor.load_model(version=version)
        
        #Extract and validate ticker
        ticker = data.get('ticker', 'SPY')
        if not ticker:
            return jsonify({'error': 'Ticker symbol is required'}), 400
        if not validate_ticker(ticker):
            return jsonify({'error': f'Invalid ticker symbol: {ticker}'}), 400
        
        #Extract and validate dates
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if not start_date or not end_date:
            return jsonify({'error': 'Both start_date and end_date are required'}), 400
        
        dates_valid, date_message = validate_dates(start_date, end_date)
        if not dates_valid:
            return jsonify({'error': date_message}), 400
        
        #check if model is loaded
        if predictor.model is None:
            return jsonify({'error': 'Model not loaded. Please train the model first'}), 500

        predictions = predictor.predict(ticker, start_date, end_date)
        return jsonify({
            'ticker': ticker,
            'predictions': predictions.tolist(),
            'start_date': start_date,
            'end_date': end_date
        })
    
    except Exception as e:
        logging.error(f"Prediction error: {str(e)}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500
    

@app.route('/train', methods=['POST'])
def train():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ticker = data.get('ticker', 'SPY')
        if not ticker:
            return jsonify({'error': 'Ticker symbol is required'}), 400
        if not validate_ticker(ticker):
            return jsonify({'error': f'Invalid ticker symbol: {ticker}'}), 400
        
        #extract and validate dates
        start_date = data.get('start_date', '2014-08-01')
        end_date = data.get('end_date', datetime.now().strftime('%Y-%m-%d'))

        dates_valid, date_message = validate_dates(start_date, end_date)
        if not dates_valid:
            return jsonify({'error': date_message}), 400

        model, history, X_test, y_test = predictor.train(ticker, start_date, end_date)
        predictor.save_model()

        return jsonify({
            'message': 'Model trained successfully',
            'training_history': {
                'loss': history.history['loss'],
                'val_loss': history.history['val_loss']
            },
            'training_params': {
                'ticker': ticker,
                'start_date': start_date,
                'end_date': end_date
            }
        })
    except Exception as e:
        logging.error(f"training error: {str(e)}")
        return jsonify({'error': f'Training failed: {str(e)}'}), 500
    
@app.route('/health', methods=['GET'])
def health_status():
    return jsonify({'status': 'healthy'}), 200

@app.route('/health/check', methods=['GET'])
def health_check():
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'components': {}
    }

    #Check database
    try:
        #test query
        test_query = text('SELECT 1')
        db.session.execute(test_query)
        db.session.commit()
        health_status['components']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['components']['database'] = {
            'status': 'error',
            'message': str(e)
        }
        health_status['status'] = 'unhealthy'

    #check redis
    try:
        if hasattr(app, 'redis_client') and app.redis_client:
            test_key = 'health_check_test'
            app.redis_client.set(test_key, 'test_value', ex=60) #60 second expiry
            test_value = app.redis_client.get(test_key)
            if test_value == b'test_value':
                health_status['components']['redis'] = {
                    'status': 'healthy',
                    'message': 'Redis connection successful'
                }
            else:
                raise Exception('Redis value mismatch')
        else:
            health_status['components']['redis'] = {
                'status': 'warning',
                'message': 'Redis client not initialized'
            }
    except Exception as e:
        health_status['components']['redis'] = {
            'status': 'error',
            'message': str(e)
        }
        health_status['status'] = 'unhealthy'

    #Check backgroudn Tasks
    try:
        if hasattr(app, 'task_manager') and app.task_manager:
            jobs = app.task_manager.scheduler.get_jobs()
            job_status = {}
            for job in jobs:
                job_status[job.id] = {
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'last_run': getattr(job, 'last_run_time', None),
                    'status': 'scheduled' if job.next_run_time else 'paused'
                }
            health_status['components']['background_tasks'] = {
                'status': 'healthy',
                'jobs': job_status
            }
        else:
            health_status['components']['background_tasks'] = {
                'status': 'warning',
                'message': 'Task manager not initialized'
            }
    except Exception as e:
        health_status['components']['background_tasks'] = {
            'status': 'error',
            'message': str(e)
        }
        health_status['status'] = 'degraded'

    #check model availability
    try:
        models_path = 'models_saved/'
        available_models = [d for d in os.listdir(models_path) if os.path.isdir(os.path.join(models_path, d))]
        if available_models:
            health_status['components']['models'] = {
                'status': 'healthy',
                'available_models': available_models
            }
        else:
            health_status['components']['models'] = {
                'status': 'warning',
                'message': 'No models available'
            }
    except Exception as e:
        health_status['components']['models'] = {
            'status': 'error',
            'message': str(e)
        }
        health_status['status'] = 'degraded'
    response = jsonify(health_status)
    response.status_code = 200 if health_status['status'] == 'healthy' else 207
    return response


@app.route('/metrics', methods=['GET'])
def get_metrics():
    try:
        metrics_manager = MetricsManager()

        #Get latest predictions and actual values
        if not hasattr(predictor, 'last_predictions') or not hasattr(predictor, 'last_actual'):
            return jsonify({'error': 'No predictions available yet'}), 404
        
        metrics = metrics_manager.calculate_basic_metrics(
            predictor.last_actual,
            predictor.last_predictions
        )

        return jsonify({
            'basic_metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logging.error(f"Error getting metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        log_type = request.args.get('type', 'app') #app or error
        lines = int(request.args.get('lines', 100)) #number of lines to return

        log_file = 'app.log' if log_type == 'app' else 'error.log'
        log_path = os.path.join('logs', log_file)

        if not os.path.exists(log_path):
            return jsonify({'error': 'Log file not found'}), 404
        
        with open(log_path, 'r') as f:
            #get last N lines
            all_logs = f.readlines()
            #Ensure we don't try to get more lines than there are
            num_lines = min(lines, len(all_logs))
            last_n_logs = all_logs[-num_lines:]

        return jsonify({
            'log_type': log_type,
            'lines_requested': lines,
            'lines_returned': len(last_n_logs),
            'logs': last_n_logs
        })
    except Exception as e:
        logging.error(f"Error retrieving logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)