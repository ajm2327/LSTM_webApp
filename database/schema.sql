-- create extension for uuid generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- users table to store user account info
CREATE TABLE users(
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    subscription_tier VARCHAR(50) DEFAULT 'free'
);

--API keys for user AUTH
CREATE TABLE api_keys(
    key_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(user_id)
);

--historical stock data cache
CREATE TABLE historical_data (
    data_id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10,2) NOT NULL,
    high DECIMAL(10,2) NOT NULL,
    low DECIMAL(10,2) NOT NULL,
    close DECIMAL(10,2) NOT NULL,
    adjusted_close DECIMAL(10,2) NOT NULL,
    volume BIGINT NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)
);

-- technical indicators CACHE
CREATE TABLE technical_indicators (
    indicator_id SERIAL PRIMARY KEY,
    data_id INTEGER REFERENCES historical_data(data_id) ON DELETE CASCADE,
    rsi DECIMAL(10,2),
    ema_fast DECIMAL(10,2),
    hist_volatility DECIMAL(10,4),
    bb_upper DECIMAL(10,2),
    bb_middle DECIMAL(10,2),
    bb_lower DECIMAL(10,2),
    macd DECIMAL(10,2),
    macd_signal DECIMAL(10,2),
    atr DECIMAL(10,2),
    obv BIGINT,
    CONSTRAINT fk_historical_data FOREIGN KEY(data_id) REFERENCES historical_data(data_id)
);

--Model versions table
CREATE TABLE model_versions (
    model_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    parameters JSONB NOT NULL,
    metrics JSONB,
    is_active BOOLEAN DEFAULT true
);

--predictions cache
CREATE TABLE predictions (
    prediction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    model_id UUID REFERENCES model_versions(model_id),
    ticker VARCHAR(10) NOT NULL,
    prediction_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    target_date DATE NOT NULL,
    predicted_value DECIMAL(10,2) NOT NULL,
    actual_value DECIMAL(10,2),
    confidence_score DECIMAL(5,2),
    CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(user_id),
    CONSTRAINT fk_model FOREIGN KEY(model_id) REFERENCES model_versions(model_id)
);

-- user preferences and settings
CREATE TABLE user_preferences(
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    default_tickers JSON DEFAULT '[]',
    notification_settings JSON DEFAULT '{}',
    ui_preferences JSON DEFAULT '{}',
    CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(user_id)
);

--rate limiting table
CREATE TABLE rate_limits(
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 0,
    last_reset TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(user_id),
    PRIMARY KEY (user_id, endpoint)
);

-- create indezes for better query performance
CREATE INDEX idx_historical_data_ticker_date ON historical_data(ticker, date);
CREATE INDEX idx_predictions_user_ticker ON predictions(user_id, ticker);
CREATE INDEX idx_predictions_date ON predictions(target_date);
CREATE INDEX idx_api_keys_key ON api_keys(api_key);