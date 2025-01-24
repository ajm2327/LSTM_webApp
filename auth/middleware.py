from functools import wraps
from flask import request, jsonify, current_app
from models.user import User
from database.db import db
import uuid
from datetime import datetime, timedelta, timezone
import hashlib
import os
import logging
import json
from .config import AuthConfig
from sqlalchemy import text

logger = logging.getLogger('auth')

class SecurityException(Exception):
    """Base exception for security-related errors"""
    pass

class APIKey:
    """Handles API key operations and validation"""

    def __init__(self, user_id, api_key, is_active=True):
        self.key_id = uuid.uuid4()
        self.user_id = user_id
        self.api_key = api_key
        self.created_at = datetime.now(timezone.utc)
        self.last_used = None
        self.is_active = is_active
        self.expires_at = self.created_at + timedelta(days=AuthConfig.KEY_EXPIRY_DAYS)

    @staticmethod
    def generate_key():
        """Genreate a new secure api key"""
        return hashlib.sha256(os.urandom(32)).hexdigest()
    
    @staticmethod
    def get_key_from_header():
        """Extract api key from request header"""
        return request.headers.get('X-API-Key')
    
    @staticmethod
    def validate_key_format(api_key):
        """validate API key format"""
        if not api_key or len(api_key) < AuthConfig.MIN_KEY_LENGTH:
            return False
        try:
            int(api_key, 16) #validate hexadecimal
            return True
        except ValueError:
            return False
        
    @staticmethod
    def count_user_keys(user_id):
        """Count active keys for a user"""
        sql = text("""
            SELECT COUNT(*) FROM api_keys
            WHERE user_id = :user_id AND is_active = true
        """)
        return db.session.execute(sql, {'user_id': user_id}).scalar()
    
class RateLimit:
    """Handles rate limiting logic"""

    def __init__(self):
        self.redis_client = current_app.redis_client
        self.max_requests = AuthConfig.RATE_LIMIT_REQUESTS
        self.window_size = AuthConfig.RATE_LIMIT_WINDOW

    def get_rate_limit_key(self, user_id):
        """Generate redis key for rate limiting"""
        return f"rate_lmit:{user_id}"
    
    def is_rate_limited(self, user_id):
        """Check if user is rate limited"""
        if not self.redis_client:
            return False #Fail open if redis is not available
        
        key = self.get_rate_limit_key(user_id)
        pipe = self.redis_client.pipeline()

        try:
            #Atomic rate limit check
            pipe.incr(key)
            pipe.expire(key, self.window_size)
            current_count = pipe.execute()[0]

            if current_count == 1: #First request in new window
                self.redis_client.expire(key, self.window_size)

            is_limited = current_count > self.max_requests

            if is_limited:
                logger.warning(f"Rate limit exceeded for user {user_id}")

            return is_limited
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            return False #fall open if redis is down
        

    def get_remaining_requests(self, user_id):
        """get remaining requests in current window"""
        if not self.redis_client:
            return self.max_requests
        
        key = self.get_rate_limit_key(user_id)
        current_count = self.redis_client.get(key)
        if current_count is None:
            return self.max_requests
        return max(0, self.max_requests - int(current_count))
    
class SecurityTracker:
    """Tracks security-related events"""

    def __init__(self):
        #using centralized redis client
        self.redis_client = current_app.redis_client

    def track_failed_attempt(self, identifier):
        """Track failed authentication attempts"""
        if not self.redis_client:
            return False #Fail open if Redis is not available
        
        key = f"failed_attempts:{identifier}"
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, int(AuthConfig.FAILED_ATTEMPTS_WINDOW.total_seconds()))
        count = pipe.execute()[0]

        if count >= AuthConfig.FAILED_ATTEMPTS_LIMIT:
            logger.warning(f"Multiple failed attempts detected for {identifier}")
            return True
        return False
    
def require_api_key(f):
    """Decorator for routes requiring API key authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            api_key = APIKey.get_key_from_header()

            if not api_key:
                return jsonify({"error": "No API Key provided"}), 401
            
            if not APIKey.validate_key_format(api_key):
                return jsonify({"error": "invalid API key format"}), 401
            
            #Check if API key exists and is active
            sql = text("""
                SELECT ak.user_id, ak.is_active, ak.created_at, u.is_active as user_active
                FROM api_keys ak
                JOIN users u ON ak.user_id = u.user_id
                WHERE ak.api_key = :api_key
            """)
            key_record = db.session.execute(sql, {'api_key': api_key}).first()
            if not key_record:
                return jsonify({"error": "Invalid API Key"}), 401
            
            if not key_record.is_active or not key_record.user_active:
                return jsonify({"error": "Inactive API Key or user account"}), 401
            
            #check key expiration
            if key_record.created_at + timedelta(days=AuthConfig.KEY_EXPIRY_DAYS) < datetime.now(timezone.utc):
                return jsonify({"error": "Expired API key"}), 401
            
            sql = text("""
                UPDATE api_keys
                SET last_used = :now
                WHERE api_key = :api_key
            """)
            db.session.execute(sql, {'now': datetime.now(timezone.utc), 'api_key': api_key})
            
            #Check rate liimit
            rate_limiter = RateLimit()
            if rate_limiter.is_rate_limited(key_record.user_id):
                remaining_time = rate_limiter.window_size
                return jsonify({
                    "error": "Rate limit exceeded",
                    "reset_in": remaining_time,
                }), 429
            
            #Add rate limit headers
            response = f(*args, **kwargs)
            if isinstance(response, tuple):
                response_obj, status_code = response

            else:
                response_obj, status_code = response, 200

            if isinstance(response_obj, dict):
                response_obj = jsonify(response_obj)

            remaining = rate_limiter.get_remaining_requests(key_record.user_id)
            response_obj.headers['X-RateLimit-Limit'] = str(AuthConfig.RATE_LIMIT_REQUESTS)
            response_obj.headers['X-RateLimit-Remaining'] = str(remaining)
            response_obj.headers['X-RateLimit-Reset'] = str(rate_limiter.window_size)

            return response_obj, status_code
        
        except Exception as e:
            logger.error(f"API key authentication error: {str(e)}")
            return jsonify({"error": "Authentication failed"}), 500
        
    return decorated