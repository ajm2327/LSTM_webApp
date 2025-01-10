from .redis import init_redis

def init_config(app):
    """Initialize all configuration components"""
    init_redis(app)

    #return configuration objects for access elsewhere
    return {
        'redis_client': app.redis_client
    }