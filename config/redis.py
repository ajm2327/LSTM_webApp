from redis import Redis
import os
import logging

logger = logging.getLogger(__name__)

class RedisConfig:
    def __init__(self, app=None):
        self.redis_client = None
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Redis with the Flask App"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = Redis.from_url(redis_url)
            app.redis_client = self.redis_client

            #test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Redis initialization failed: {str(e)}")
            #dont raise - allow app to function without redis
            app.redis_client = None

def init_redis(app):
    return RedisConfig(app)