from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from app import db, app


def insert_test_data():
    """Insert test data to trigger background tasks"""
    with app.app_context():
        try:
            #add test predictions to trigger model retraining
            sql = text("""
                INSERT INTO predictions (
                    prediction_id, ticker, prediction_date, target_date,
                    predicted_value, confidence_score
                ) VALUES (
                       uuid_generate_v4(), :ticker, :pred_date, :target_date,
                       :pred_value, :confidence
                )
            """)

            #insert predictions for last 5 days
            for i in range(5):
                pred_date = datetime.now(timezone.utc) - timedelta(days=i)
                db.session.execute(sql, {
                    'ticker': 'SPY',
                    'pred_date': pred_date,
                    'target_date': pred_date + timedelta(days=1),
                    'pred_value': 100.0 + i,
                    'confidence': 0.95
                })
            
            #add historical data to trigger market updates
            sql = text("""
                INSERT INTO historical_data (
                    ticker, date, open, high, low, close,
                    adjusted_close, volume, last_updated
                ) VALUES (
                    :ticker, :date, :open, :high, :low, :close,
                       :adj_close, :volume, NOW()
                )
                ON CONFLICT (ticker, date) DO NOTHING
            """)

            #insert data for last 10 days
            for i in range(10):
                date = datetime.now(timezone.utc) - timedelta(days=i)
                db.session.execute(sql, {
                    'ticker': 'SPY',
                    'date': date.date(),
                    'open': 100.0 + i,
                    'high': 101.0 + i,
                    'low': 99.0 + i,
                    'close': 100.5 + i,
                    'adj_close': 100.5 + i,
                    'volume': 1000000 + i
                })
            db.session.commit()
            print("Test data inserted successfully")

        except Exception as e:
            print(f"Error inserting test data: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    insert_test_data()