from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class AuthConfig:
    """Authentication and rate limiting Configuration"""

    #api key settings
    MAX_KEYS_PER_USER = int(os.getenv('MAX_KEYS_PER_USER', '5'))
    KEY_EXPIRY_DAYS = int(os.getenv('KEY_EXPIRY_DAYS', '365'))
    MIN_KEY_LENGTH = 64

    #Rate limiting
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '3600')) # 1 hour 
    RATE_LIMIT_CLEANUP_INTERVAL = timedelta(hours=1)

    #Security
    FAILED_ATTEMPTS_LIMIT = int(os.getenv('FAILED_ATTEMPTS_LIMIT', '5'))
    FAILED_ATTEMPTS_WINDOW = timedelta(minutes=15)
    IP_TRACKING_ENABLED = os.getenv('IP_TRACKING_ENABLED', 'true').lower() == 'true'

    #Cache settings
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'redis')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')