from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models.user import User 

# Initialize Flask-SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database and migrations with the Flask app"""
    db.init_app(app)
    migrate.init_app(app, db)

# Export the database session from config
from database.config import db_config, get_db