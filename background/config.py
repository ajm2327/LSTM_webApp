import os 
from datetime import timedelta
from dotenv import load_dotenv


load_dotenv()

class BackgroundConfig:
    """Configuration for background tasks"""

    #model retraining settings
    RETRAINING_INTERVAL_DAYS = int(os.getenv('RETRAINING_INTERVAL_DAYS', '1'))
    RETRAINING_HOUR = int(os.getenv('RETRAINING_HOUR', '1')) #1 am
    TRAINING_HISTORY_DAYS = int(os.getenv('TRAINING_HISTORY_DAYS', '3650')) #ten years
    MAX_RETRAIN_ATTEMPTS = int(os.getenv('MAX_RETRAINING_ATTEMPTS', '3'))


    #MARKET DATA UPDATE settings
    MARKET_UPDATE_INTERVAL_HOURS = int(os.getenv('MARKET_UPDATE_INTERVAL_HOURS', '4'))
    MARKET_HOURS_START = int(os.getenv('MARKET_HOURS_START', '9')) #9 am
    MARKET_HOURS_END = int(os.getenv('MARKET_HOURS_END', '16')) # 4 pm
    UPDATE_HISTORY_DAYS = int(os.getenv('UPDATE_HISTORY_DAYS', '7'))

    #CACHE management settings
    CACHE_CLEANUP_HOUR = int(os.getenv('CACHE_CLEANUP_HOUR', '2')) #2am
    PREDICTION_RETENTION_DAYS = int(os.getenv('PREDICTION_RETENTION_DAYS', '30'))
    REDIS_CACHE_TTL = timedelta(hours = int(os.getenv('REDIS_CACHE_TTL_HOURS', '24')))

    #DATABASE Settings
    DB_BATCH_SIZE = int(os.getenv('DB_BATCH_SIZE', '1000'))
    MAX_CONCURRENT_UPDATES = int(os.getenv('MAX_CONCURRENT_UPDATES', '5'))

    TASK_TIMEOUT = int(os.getenv('TASK_TIMEOUT', '3600')) #1 hour
    ALERT_EMAIL = os.getenv('ALERT_EMAIL', 'admin@example.com')

    #FEATURE FLAGS
    ENABLE_MODEL_RETRAINING = os.getenv('ENABLE_MODEL_RETRAINING', 'true').lower() == 'true'
    ENABLE_MARKET_UPDATES = os.getenv('ENABLE_MARKET_UPDATES', 'true').lower() == 'true'
    ENABLE_CACHE_CLEANUP = os.getenv('ENABLE_CACHE_CLEANUP', 'true').lower() == 'true'

