# background/config.py

Similarly to the previous config.py implementation, the configuration contains all parameters that are used in the background tasks processes. The variable names are self explanatory and clearly defined


# background/tasks.py

The background tasks implementation handles the task scheduling system to maintain the LSTM tool and keep its data up to date. It provides automated handling of model retraining, market data updates, and cache management through scheduled jobs. 

The BackgroundTaskManager class is responsible for managing and executing background tasks. It uses APScheduler for task scheduling and integrates with Redis for task status management. The task manager is initialized with the app context. 

The scheduler is our APScheduler instance, the predictor is our StockPredictor instance for model operations. Redis is the redis connection for status management. Max_requests and window size are parameters similar to the ones used in the previous configuration that makes the system robust to retry loop errors. 

Model retraining is scheduled Daily at 1 am and calls the retrain_model() function. It retrains the model for the most frequently requested stock tickers. It queries the most requested tickers from the last 7 days and trains new model version for each. The model metadata is updated in the database and the new model versions are saved. 

Market data updates are scheduled for every 4 hours during market hours. This currently has no impact as the data retrieved is daily historical data. If the web app was improved to get more current and frequently updated data, this would be a more significant feature. It calls update_market_data() and fetches active tickers from the database, downloads the yahoo finance data, and handles conflicts with existing data. 

The cache management is scheduled daily for 2 am after model retraining. It calls manage_cache to maintain the database and cache hygiene. It removes predictions that are older than 30 days an deactivates expired API keys. It cleans the Redis cache entries older than 24 hours as well. 

set_task_status(task_name, status, error = None) records task execution in Redis. 

get_recent_tickers(days = 7) retrieves the most requested tickers from recent predictions. 

Get_task_metrics() returns metrics about task execution and health. 

Tasks maintain their status in redis using 
- Task:{task_name}:status – current task status
- Task:{task_name}:error – error message if failed
- Task_execution:{task_name} – execution history

Definitions:
- Running – task currently executing
- Completed – task completed successfully
- Error – task failed with error

Tasks can be monitored through the redis status keys, application logs, task metrics endpoint, and database execution records. 
The tasks are configured through REDIS_URL, RATE_LIMIT_REQUESTS, and RATE_LIMIT_WINDOW from the environment variables. 

In updating the background tasks module to rely on the centralized redis client, the module also has a new method, get_task_metrics(self) to track the metrics on the background tasks.  It makes a dictionary of the tasks and overall health then tries to get the jobs from the scheduler. Upon connection with the redis_client it gets the task execution keys, execution history and total runs. After getting this information it counts the successes in the total runs and then calculates the success rate based on the successes in the total runs. The metrics that this function returns are:
- Last_run
- Next_run
- Total_runs
- Success_rate
- status


# monitoring/health_monitor.py 

The dependencies for this module are requests for HTTP requests, SMTP for emails, logging, os for env variables, datetime for timestamps, and signal for graceful shutdown handling.

The health monitor class provides automated health monitoring for the LSTM app which it has an API endpoint for that we reviewed in the documentation for app.py. The constructor takes the base_url of the web app, and check_interval which is the time allotted for health checks in seconds. The default is 300 (5 minutes).

The setup_logging() method configures the logging system for the health monitor. It creates a log directory if it doesn’t exist and sets up file based logging for immediate feedback. Then it configures the console logging for immediate feedback. All monitoring goes to the logs/monitoring.log file. 

shutdown(signum, frame) handles graceful shutdown of the monitor when receiving SIGINT or SIGTERM signals. 

send_alert(subject: str, body: str) sends email alerts when health issues are detected using SMTP. 

The required environment variables for this method is for the SMTP_SERVER address, the SMTP_PORT is the port to send emails. ALERT_EMAIL_SENDER is the sender email address. ALERT_EMAIL_PASSWORD is the sender email password. It can be the same email as the alert sender and the recipient. ALERT_EMAIL_RECIPIENT is the recipient email address. 

The system sends email alerts when any component reports a non-healthy status, when the overall system health is degraded, or when the health check fails. The emails are formatted to include:
- Component name
- Current status
- Error message
- Timestamp
The console output is color coded to be green for healthy components and red for unhealthy/error states. 


check_health() performs a health check on the system by calling the application’s /health/check endpoint. It monitors:
- Database connectivity
- Redis connection status
- Background task status
- Model availability
- Overall system health

Then it returns a dictionary containing health check results. None if the health check fails. 

run() is the main loop to continuously run health checks. 
