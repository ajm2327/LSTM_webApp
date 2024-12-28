from flask import Flask
import time
import logging
import sys
import os
print("Python path:", sys.path)


#add project root to python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

print("Current directory:", current_dir)
print("Project root:", project_root)

try:
    from background.tasks import BackgroundTaskManager
    print("Import 1 successful")
except ImportError as e:
    print("Import 1 failed:", str(e))
    



#configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

def test_background_tasks():
    """Manual test of background tasks"""
    app = create_test_app()

    with app.app_context():
        logger.info("Initializing background tasks...")
        task_manager = BackgroundTaskManager(app)

        try:
            #test model retraining
            logger.info("Testing model retraining...")
            task_manager.retrain_model()
            print_task_status(task_manager, 'model_retraining')

            #test market data update
            logger.info("Testing market data update...")
            task_manager.update_market_data()
            print_task_status(task_manager, 'market_data_update')

            #test cache cleanup
            logger.info("Testing cache cleanup...")
            task_manager.manage_cache()
            print_task_status(task_manager, 'cache_cleanup')

            #Monitor scheduled tasks
            logger.info("Monitoring scheduled tasks for 5 minutes...")
            monitor_tasks(task_manager, duration=300) #5 minutes

        except Exception as e:
            logger.error(f"Error during testing: {str(e)}")
        finally:
            task_manager.scheduler.shutdown()

def print_task_status(task_manager, task_name):
    """Print status of a specific task"""
    status = task_manager.redis.get(f'task:{task_name}:status')
    error = task_manager.redis.get(f'task:{task_name}:error')

    logger.info(f"\nTask: {task_name}")
    logger.info(f"Status: {status.decode('utf-8') if status else 'Unknown'}")
    if error:
        logger.info(f"Error: {error.decode('utf-8')}")
    logger.info("-" * 50)

def monitor_tasks(task_manager, duration):
    """Monitor scheduled tasks for a specified duration"""
    start_time = time.time()
    while time.time() - start_time < duration:
        for task_name in ['model_retraining', 'market_data_update', 'cache_cleanup']:
            print_task_status(task_manager, task_name)
        time.sleep(60)


if __name__ == '__main__':
    test_background_tasks()