import unittest
from unittest.mock import Mock, patch
import pytest
from datetime import datetime, timedelta, timezone
import redis
import json
from background.tasks import BackgroundTaskManager
from models.lstm_model import StockPredictor
from flask import Flask
import yfinance as yf
import threading
from database.db import db, migrate

class TestBackgroundTasks:
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLAlCHEMY_TRACK_MODIFICATIONS'] = False

        with app.app_context():
            db.init_app(app)
            migrate.init_app(app, db)
            db.create_all()
        return app
    
    @pytest.fixture
    def task_manager(self, app):
        """Create test background task manager instance"""
        with app.app_context():
            manager = BackgroundTaskManager(app)
            manager.redis = Mock(spec=redis.Redis)
            yield manager
            #Cleanup
            manager.scheduler.shutdown()
            #manager.redis.flushall()

    def test_scheduler_initialization(self, task_manager):
        """Test if scheduler is properly initialized"""
        assert task_manager.scheduler.running
        jobs = task_manager.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]

        assert 'model_retraining' in job_ids
        assert 'market_data_update' in job_ids
        assert 'cache_cleanup' in job_ids

    @patch.object(StockPredictor, 'train')
    def test_model_retraining(self, mock_train, task_manager, app):
        """Test model retraining functionality"""

        #mock training results
        mock_train.return_value = (Mock(), Mock(), Mock(), Mock())

        #mock database query
        with patch('sqlalchemy.orm.session.Session.execute') as mock_execute:
            mock_execute.return_value.fetchall.return_value = [('SPY', 100)]

            with app.app_context():
                #Execute retraining
                task_manager.retrain_model()

                #Verify training was called
                assert mock_train.called

                #Check if status was updated in Redis
                status = task_manager.redis.get('task:model_retraining:status')
                assert status is not None
                assert status.decode('utf-8') == 'completed'

    @patch.object(yf, 'download')
    def test_market_data_update(self, mock_download, task_manager, app):
        """Test market data update functionality"""
        #mock yfinance data
        mock_data = Mock()
        mock_data.iterrows.return_value = []
        mock_download.return_value = mock_data

        with app.app_context():
            #execute update
            task_manager.update_market_data()

            #verify download was attempted
            assert mock_download.called

            status = task_manager.redis.get('task:market_data_update:status')
            assert status is not None
            assert status.decode('utf-8') == 'completed'

    def test_cache_cleanup(self, task_manager, app):
        """Test cache cleanup functionality"""
        #add some test data to redis
        test_key = 'cache:test'
        task_manager.redis.set(test_key, 'test_value')
        task_manager.redis.set(f'{test_key}:timestamp',
                               (datetime.now(timezone.utc) - timedelta(days=2)).timestamp())
        
        with app.app_context():
            #execute cleanup
            task_manager.manage_cache()

            #verify old data was cleaned up
            assert task_manager.redis.get(test_key) is None

    def test_rate_limiting(self, task_manager):
        """test rate limiting functionality"""
        test_user_id = 'test_user'

        #simulate requests up to limit
        for _ in range(task_manager.max_requests):
            assert not task_manager.is_rate_limited(test_user_id)

        #next request should be rate limited
        assert task_manager.is_rate_limited(test_user_id)

    def test_error_handling(self, task_manager, app):
        """Test error handling in background tasks"""
        with app.app_context():
            #force an error in market data update
            with patch.object(yf, 'download', side_effect = Exception('Test Error')):
                task_manager.update_market_data()

                status = task_manager.redis.get('task:market_data_update:status')
                error = task_manager.redis.get('task:market_data_update:error')

                assert status.decode('utf-8') == 'error'
                assert 'Test error' in error.decode('utf-8')

    def test_concurrent_execution(self, task_manager, app):
        """test handling of concurrent task execution"""
        def run_task():
            with app.app_context():
                task_manager.update_market_data()

        #stat multiple threads
        threads = [threading.Thread(target=run_task) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()


        #verify only one execution succeeded
        execution_count = int(task_manager.redis.get('task:market_data_update:execution_count') or 0)
        assert execution_count == 1




if __name__ == '__main__':
    pytest.main([__file__])
