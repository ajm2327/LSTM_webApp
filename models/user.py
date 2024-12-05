from flask_login import UserMixin
from sqlalchemy import Column, String, DateTime, Boolean, UUID
from sqlalchemy.sql import func
from database.db import db
import uuid

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    user_id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    last_login = db.Column(db.DateTime(timezone=True))
    is_active = db.Column(db.Boolean, default=True)
    subscription_tier = db.Column(db.String(50), default='free')

    def get_id(self):
        return str(self.user_id)
    
    def __repr__(self):
        return f'<User {self.email}>'