from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, timezone
import yfinance as yf
import pandas as pd
from models.lstm_model import StockPredictor
from database.db import db
from sqlalchemy import text
import logging
from redis import Redis
import json
import os
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger('background_tasks')

class BackgroundTaskManager:
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.predictor = StockPredictor()
        self.redis = Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize with flask app context"""
        self.app = app
        self.setup_jobs()
        self.scheduler.start()

    def setup_jobs(self):
        """Configure all scheduled jobs"""
        #model retraining - run daily at 1 am
        self.scheduler.add_job(
            self.retrain_model,
            CronTrigger(hour=1, minute=0),
            id = 'model_retraining'
        )

        #Date updates - Run every 4 hours during market hours
        self.scheduler.add_job(
            self.update_market_data,
            CronTrigger(hour = '9-16/4', minute=0),
            id='market_data_update'
        )

        #cache cleanup - run daily at 2 am
        self.scheduler.add_job(
            self.manage_cache,
            CronTrigger(hour = 2, minute=0),
            id = 'cache_cleanup'
        )

    def retrain_model(self):
        """Periodic model retraining"""
        try:
            with self.app.app_context():
                #get list of most requested tickers
                sql = text("""
                    SELECT ticker, COUNT(*) as request_count
                    FROM predictions
                    WHERE predictions_date > NOW() - INTERVAL '7 days'
                    GROUP BY ticker
                    ORDER BY request_count DESC
                    LIMIT 5
                """)
                popular_tickers = db.session.execute(sql).fetchall()

                for ticker, _ in popular_tickers:
                    logger.info(f"Retraining model for {ticker}")
                    try:
                        # Train model with latest data
                        model, history, X_test, y_test = self.predictor.train(
                            ticker, 
                            start_date = (datetime.now(timezone.utc) - timedelta(days = 3650)).strftime('%Y-%m-%d'),
                            end_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                        )

                        #save new model
                        model_path = self.predictor.save_model()

                        #Update model metadata in database
                        sql = text("""
                            INSERT INTO model_versions (version, parameters, metrics)
                            VALUES (:version, :parameters, :metrics)
                        """)
                        db.session.execute(sql, {
                            'versions': self.predictor.version,
                            'parameters': json.dumps(self.predictor.training_metadata),
                            'metrics': json.dumps({
                                'training_loss': history.history['loss'][-1],
                                'val_loss': history.history['val_loss'][-1]
                            })
                        })
                        db.session.commit()

                        logger.info(f"Successfully retraining model for {ticker}")
                    except Exception as e:
                        logger.error(f"Error retraining model for {ticker}: {str(e)}")

        except Exception as e:
            logger.error(f"Model retraining job faied: {str(e)}")

    def update_market_data(self):
        """update market data in database"""
        try:
            with self.app.app_context():
                #get active tickers from database
                sql = text("""
                    SELECT DISTINCT ticker
                    FROM historical_data
                    WHERE last_updated > NOW() - INTERVAL '7 days'
                """)
                active_tickers = [row[0] for row in db.session.execute(sql)]

                for ticker in active_tickers:
                    try:
                        #fetch latest data
                        data = yf.download(ticker, start=(datetime.now(timezone.utc) - timedelta(days=7)).strftime('Y-%m-%d'))

                        for index, row in data.iterrows():
                            #update or insert new data
                            sql = text("""
                                INSERT INTO historical_data
                                (ticker, date, open, high, low, close, adjusted_close, volume, last_updated)
                                VALUES (:ticker, :date, :open, :high, :lowm :close, :adj_close, :volume, NOW())
                                ON CONFLICT (ticker, date)
                                DO UPDATE SET
                                    open = EXCLUDED.open,
                                    high = EXCLUDED.high,
                                    low = EXCLUDED.low,
                                    close = EXCLUDED.close,
                                    adjusted_close = EXCLUDED.adjusted_close,
                                    last_updated = NOW()
                            """)
                            db.session.execute(sql, {
                                'ticker': ticker,
                                'date': index.date(),
                                'open': float(row['Open']),
                                'high': float(row['High']),
                                'low': float(row['Low']),
                                'close': float(row['Close']),
                                'adj_close': float(row['Adj Close']),
                                'volume': int(row['Volume'])
                            })
                        db.session.commit()
                        logger.info(f"Updated market data for {ticker}")
                    except Exception as e:
                        logger.error(f"Error updating data for {ticker}: {str(e)}")
                        db.session.rollback()

        except Exception as e:
            logger.error(f"Market data update job failed: {str(e)}")

    def manage_cache(self):
        """Manage cache data"""
        try:
            with self.app.app_context():
                #clean up old predictions
                sql = text("""
                    DELETE FROM predictions
                    WHERE prediction_data < NOW() - INTERVAL '30 days'
                """)
                db.session.execute(sql)

                #clean up expired API keys
                sql = text("""
                    UPDATE api_keys
                    SET is_active = false
                    WHERE expires_at < NOW()
                """)
                db.session.execute(sql)

                #clean up redis cache
                for key in self.redis.scan_iter("cache:*"):
                    try:
                        #check if cache entry is expired (older than 24 hours)
                        if float(self.redis.get(f"{key}:timestamp") or 0) < (datetime.now(timezone.utc) - timedelta(hours = 24)).timestamp():
                            self.redis.delete(key)
                    except Exception as e:
                        logger.error(f"Error cleaning up Redis key {key}: {str(e)}")

                db.session.commit()
                logger.info("Cache cleanup completed succcessfully")

        except Exception as e:
            logger.error(f"Cache management job failed: {str(e)}")
            db.session.rollback()



# initialize tasks
def init_background_tasks(app):
    task_manager = BackgroundTaskManager(app)
    return task_manager

                    