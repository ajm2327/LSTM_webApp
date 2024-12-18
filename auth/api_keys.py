from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from database.db import db
from .middleware import APIKey, SecurityTracker, RateLimit
from .config import AuthConfig
import logging
from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy import text

logger = logging.getLogger('auth')
api_keys = Blueprint('api_keys', __name__)

@staticmethod
def count_user_keys(user_id):
    """Count active keys for a user"""

    sql = text("""
        SELECT COUNT(*) FROM api_keys
        WHERE user_id = :user_id AND is_active = true
    """)
    return db.session.execute(sql, {'user_d': user_id}).scalar()

@api_keys.route('/keys/create', methods=['POST'])
@login_required
def create_key():
    """Create a  new api key for the current user"""
    try:
        #check existing keys count
        current_keys = APIKey.count_user_keys(current_user.user_id)
        if current_keys >= AuthConfig.MAX_KEYS_PER_USER:
            return jsonify({
                "error": "Maximum number of active keys reached",
                "limit": AuthConfig.MAX_KEYS_PER_USER
            }), 400
        
        new_key = APIKey.generate_key()
        expires_at = datetime.now(timezone.utc) + timedelta(days = AuthConfig.KEY_EXPIRY_DAYS)

        sql = text("""
            INSERT INTO api_keys (key_id, user_id, api_key, created_at, expires_at)
            VALUES (:key_id, :user_id, :api_key, :created_at, :expires_at)
        """)

        db.session.execute(sql, {
            'key_id': uuid.uuid4(),
            'user_id': current_user.user_id,
            'api_key': new_key,
            'created_at': datetime.now(timezone.utc),
            'expires_at': expires_at
        })
        
        db.session.commit()
        logger.info(f"API key created for user {current_user.user_id}")

        return jsonify({
            "api_ley": new_key,
            "expires_at": expires_at.isoformat(),
            "rate_limit": {
                "max_requests": AuthConfig.RATE_LIMIT_REQUESTS,
                "window_seconds": AuthConfig.RATE_LIMIT_WINDOW
            }
        })
    
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to create API key"}), 500
    
@api_keys.route('/keys/list', methods=['GET'])
@login_required
def list_keys():
    """List all api keys for the current user"""
    try:
        sql = text("""
            SELECT api_key, created_at, last_used, is_active, expires_at
            FROM api_keys
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """)
        keys = db.session.execute(sql, {'user_id': current_user.user_id}).fetchall()
        
        return jsonify({
            "keys": [{
                "api_key" : key.api_key[-8:], #only show last 8 chars
                "created_at": key.created_at.isoformat(),
                "last_used": key.last_used.isoformat() if key.last_used else None,
                "is_active": key.is_active,
                "expires_at": key.expires_at.isoformat(),
                "is_expired": key.expires_at < datetime.now(timezone.utc)
            } for key in keys]
        })
    
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        return jsonify({"error": "Failed to list api keys"}), 500
    
@api_keys.route('/keys/revoke/<api_key>', methods = ['POST'])
@login_required
def revoke_key(api_key):
    """Revoke an API key"""
    try:
        sql = text("""
            UPDATE api_keys
            SET is_active = false
            WHERE api_key = :api_key AND user_id = :user_id
            RETURNING api_key
        """)
        result = db.session.execute(sql, {'api_key': api_key, 'user_id': current_user.user_id})
        if not result.rowcount:
            return jsonify({"error": "Key not found"}), 404
        
        db.session.commit()
        logger.info(f"API key revoked for user {current_user.user_id}")

        return jsonify({"message": "Key revoked successfully"})

    except Exception as e:
        logger.error(f"Error revoking API key: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "failed to revoke API key"}), 500
    
@api_keys.route('/keys/status/<api_key>', methods=['GET'])
@login_required
def key_status(api_key):
    """Get detailed status of an API key"""
    try:
        sql = text("""
            SELECT created_at, last_used, is_active, expires_at
            FROM api_keys
            WHERE api_key = :api_key AND user_id = :user_id
        """)
        key_info = db.session.execute(sql, {'api_key': api_key, 'user_id': current_user.user_id}).first()
        
        if not key_info:
            return jsonify({"error": "Key not found"}), 404
        
        rate_limiter = RateLimit()
        remaining_requests = rate_limiter.get_remaining_requests(current_user.user_id)

        return jsonify({
            "status": {
                "is_active": key_info.is_active,
                "created_at": key_info.created_at.isoformat(),
                "last_used": key_info.last_used.isofromat() if key_info.last_used else None,
                "expires_at": key_info.expires_at.isoformat(),
                "is_expired": key_info.expires_at < datetime.now(timezone.utc)
            },
            "rate_limit": {
                "remaining_requests": remaining_requests,
                "reset_in": AuthConfig.RATE_LIMIT_WINDOW,
                "max_requests": AuthConfig.RATE_LIMIT_REQUESTS
            }
        })
    except Exception as e:
        logger.error(f"Error getting key status: {str(e)}")
        return jsonify({"error": "Failed to get key status"}), 500