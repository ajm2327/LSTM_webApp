from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
import logging
import json
from datetime import datetime

class MetricsManager:
    def __init__(self):
        self.logger = logging.getLogger('metrics')

    def calculate_basic_metrics(self, y_true, y_pred):
        """Calculate basic model performance metrics"""
        try:
            mse = mean_squared_error(y_true, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)

            metrics = {
                'mse': float(mse),
                'rmse': float(rmse),
                'mae': float(mae),
                'r2': float(r2)
            }

            self.logger.info(f"Metrics calculated successfully: {json.dumps(metrics)}")
            return metrics
        except Exception as e:
            self.logger.error(f"Error calculating metrics {str(e)}")
            raise
