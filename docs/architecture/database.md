# database/config.py

This module is for database configurations and connection management for the app. It handles PostgreSQL database connections with connection pooling, session management, and Flask-SQLAlchmey integration. 
The database connection relies on the environment variables for:
- DB_USER – database user
- DB_PASSWORD – database password
- DB_PORT – database port
- DB_NAME –  database name
The connection pool relies on
- DB_POOL_SIZE – initial pool size, default 5
- DB_MAX_OVERFLOW – max number of connection above pool size, default 10
- DB_POOL_TIMEOUT – connection timeout in seconds, default 30

This is a basic database with flask, the database is initialized from the database configuration and there is a context manager for safe session handling and the connection pooling.

The database configuration has the main DatabaseConfig class. This handles the database connection settings, connection pooling configuration, session management, flask application initialization, and table creation and management. 

The methods class initializes the configuration with the environment variables. get_database_url() generates the database URL from configuration. 
Init_db initializes database connection and creates tables. 
get_db_session() is the context manager for database sessions. init_app() initializes flask applications with SQLAlchemy. 

The global instances are:
- Db for the flask-sqlalchemy instance
- Migrate for the flask-migrate instance
- Db_config is for the databaseconfig singleton instance
- Base is the sqlalchemy declarativve base class. 

Always use the get_db() context manager for database operations. Connection pooling helps manage database connections efficiently. Environment variables are retrieved from the hidden .env file. The tables are automatically created on initialization. SQLAlchemy echo can be enabled for query logging. 

# database/db.py
This is a simple initialization file for the core database extension in the app. It uses flask-sqlAlchemy and flask-migrate to provide the central database instance and migration support used throughout the app. 

# database/schema.sql 

The database schema defines the structure of the tables for the LSTM app. It includes user management, stock data storage, model versioning, and prediction tracking. It uses postgersql 12.0 or higher and UUID. 

The database is organized into 
- User management (users, api_keys)
- Stock data (historical_data, technical_indicators)
- Model management (model_versions)
- Predictions (predictions)
- User preferences (user_preferences)
- Rate limiting (rate_limits)

The users table stores core user account information. It holds:
- User_id
- Email
- Password_hash
- Created_at
- Last_login
- Is_active
- Subcription_tier

The api keys table manages API authentication keys
- Key_id
- User_id
- Api_key
- Created_at
- Last_used
- Is_active
- Expires_at

The historical data table caches stock market historical data:
- Data_id
- Ticker
- Date
- Open
- High
- Low
- Close
- Adjusted_close
- Volume
- Last_updated

The technical indicators table stores the calculated indicators for stock data
- Indicator_id
- Data_id
- RSI, EMA, MACD, etc

The model versions table tracks different version of the LSTM - model
- Model_id
- Version
- Created_at
- Parameters
- Metrics
- Is_active

The predictions table stores model predictions and actual values
- Prediction_id
- User_id
- Model_id
- Ticker
- Prediction_date
- Target_data
- Predicted_value
- Actual_value
- Confidence_score

The user preferences table stores user_specific settings
- User_id
- Default_tickers
- Notification_settings
- Ui_preferences

The rate limits table manages API rate limiting per user and endpoint:
- User_id
- Endpoint
- Request_count
- Last_reset

Indexes:
- Idx_historical_data_ticker_date optimizes stock data queries
- Idx_predictions_user_ticker optimizes user prediction queries
- Idx_predictions_date optimizes date-based prediction queries
- Idx_api_keys_key optimizes API key lookups. 

All timestamps use timezone for global compatibility and UUID generation relies on the uuid-ossp extension. JSONB fields provide flexible storage for complex data and foreign key constraints ensure data integrity. Cascading deletes implemented where appropriate for data management. 
