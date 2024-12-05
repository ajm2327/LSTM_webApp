from flask_login import UserMixin
from sqlalchemy import Column, String, DateTime, Boolean, UUID
from sqlalchemy.sql import func
from database.config import Base
import uuid

class User(Base, UserMixin):
    __tablename__ = 'users'

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash=Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String(50), default='free')

    def get_id(self):
        return str(self.user_id)
    
    def __repr__(self):
        return f'<User {self.email}>'