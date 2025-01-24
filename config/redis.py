from redis import Redis, ConnectionPool
import os
import logging
from typing import Optional
from datetime import timedelta

logger = logging.getLogger(__name__)

class RedisConfig:
    def __init__(self, app=None):
        self.redis_client = None
        self.pool = None
        self._health_check_interval = timedelta(seconds=30)
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Redis with the Flask App"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', '10'))
            socket_timeout = float(os.getenv('REDIS_SOCKET_TIMEOUT', '2.0'))

            #configure connection pooling
            self.pool = ConnectionPool.from_url(
                redis_url,
                max_connections = max_connections,
                socket_timeout = socket_timeout,
                socket_keepalive=True,
                health_check_interval=self._health_check_interval.seconds
            )

            #Create redis client with pool
            self.redis_client = Redis(
                connection_pool = self.pool,
                decode_responses=True #Automatically decode responses to str
            )

            #test connection
            self._test_connection()

            #add redis client to app context
            app.redis_client = self.redis_client

            #add configuration to app
            app.config.setdefault('REDIS_URL', redis_url)
            app.config.setdefault('REDIS_MAX_CONNECTIONS', max_connections)

            logger.info("Redis connection established successfully")

        except Exception as e:
            logger.error(f"Redis initialization failed: {str(e)}")
            #dont raise - allow app to function without redis
            app.redis_client = None

    def _test_connection(self) _> bool:
        """Test Redis connection with ping"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis connection test failed: {str(e)}")
            return False

    def get_client(self) -> Optional[Redis]:
        """Get redis client instance"""
        return self.redis_client

    def get_health_status(self) -> dict:
        """Get redis connection health status"""
        status = {
            'connected':  False,
            'pool_size': 0,
            'in_use_connections': 0
        }

        if self.redis_client and self.pool:
            try:
                status['connected'] = self._test_connection()
                status['pool_size'] = self.pool.max_connections
                status['in_use_connections'] = len(self.pool._in_use_connections)
            except Exception as e:
                logger.error(f"Error getting Redis health status: {str(e)}")
        return status

def init_redis(app):
    """Initialize Redis configuration"""
    return RedisConfig(app)