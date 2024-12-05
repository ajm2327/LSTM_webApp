import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

#Base class for SQlAlchemy models
Base = declarative_base()

class DatabaseConfig:
    def __init__(self):
        #get database connection details from environment variables
        self.DB_USER = os.getenv('DB_USER'. 'lstm_user')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', '')
        self.DB_HOST = os.getenv('DB_HOST', 'localhost')
        self.DB_PORT = os.getenv('DB_PORT', '5432')
        self.DB_NAME = os.getenv('DB_NAME', 'stock_predictions')

        #Connection pooling settings
        self.POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
        self.MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '5'))
        self.MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
        self.POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))

        self.engine = None
        self.SessionLocal = None

    def get_database_url(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    def init_db(self):
        """intialize database connection"""
        try:
            #Create database engine with connection pooling
            self.engine = create_engine(
                self.get_database_url(),
                poolclass=QueuePool,
                pool_size = self.POOL_SIZE,
                max_overflow = self.MAX_OVERFLOW,
                pool_timeout = self.POOL_TIMEOUT,
                echo=False # Set to True for SQL query logging
            )

            #create sessionmaker
            self.SessionLocal = sessionmaker(
                autocommit = False,
                autoflush = False,
                bind = self.engine
            )

            #Create all tables
            Base.metadata.create_all(self.engine)
            logger.info("Database initialize failed: {str(e)}")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

    @contextmanager
    def get_db_session(self):
        """Provide a transactioanl scopre around a series of operations"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()

#Create a singleton instance
db_config = DatabaseConfig()

#Helper function to get database session
def get_db():
    with db_config.get_db_session() as session:
        yield session