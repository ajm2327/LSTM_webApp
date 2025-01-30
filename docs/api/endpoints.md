# App.py
So if you want to read this file in its entirety, it is available on my github repository, LSTM_WebApp on github.com/ajm2327. Since app.py is everything put together, all of the API endpoints, then it will be a fairly comprehensive documentation. All of its dependencies will be the nitty gritty of how it actually works.

# Imports
So obviously, the first portion we have from flask, flask_login, and flask_cors are the important dependencies for our flask App and authentication. These handle the web framework of the setup, request processing, and cross-origin resource sharing which is essential for web security and API functionality. 

Below that we have our local dependencies from the models directory, utils, and database. These imports bring in the custom modules that handle the LSTM model predictions, metrics tracking, logging, the database operations, and user management. These dependencies are the major portions of phase 1, the LSTM refactoring, and phase 2, the database, user authentication system, and automated background tasks. 

The imports after that, aside from auth, background, and config, are our standard library and third party dependencies that handle core functionality like logging, date/time operations, database queries, stock data fetching, and file/JSON operations. 


# App initialization sequence
In order, the application initialization sets up the core Flask app. It loads the environment variables with load_dotenv(), turns of the GPU configuration (I am not working with a GPU), sets up logging, and uses the environment variables to set up the Flask app configuration. These portions are easily discernable with self explanatory comments and structured code. After that we initialize all configurations (we will go deeper into that later), initialize the database, the authentication system with `login_manager`, and turn on the LSTM with `StockPredictor()`. It registers the authentication and api keys and then initializes the background tasks. 

# Endpoint Helper Functions
In order, these simple utility functions validate the environment when the app is running. The first function is load_user, which gets the user_id from the login manager. The validate_ticker(ticker) function is self explanatory and checks if a ticker exists and can be fetched from Yahoo finance before attempting any predictions or processing. Similarly before that, there is a validate_dates(start_date, end_date) function that validates that the time range is valid. Finally for startup, a pretrained model is loaded through predictor.load_model(). 


# ENDPOINTS:

## @app.route('/', methods=['GET'])
This is the root endpoint. It serves as the front door and shows a simple status check and a simplified directory of two endpoints. This should be updated later to list more endpoints. 

# models endpoints:

## @app.route('/models', methods=['GET'])
The /models endpoint is the library catalog of models. It scans through the models_saved directory and collects the metadata of each saved version. The list models sorts the models by the path to ensure they’re in a consistent order. It contains appropriate error handling. 

## @app.route('/models/<version>', methods=['GET'])
The /models/<version> endpoint takes a version number, looks for its directory, takes the most recent one if there are multiple versions, retrieves detailed information about the model, and returns a 404 if the version doesn’t exist. 

# PREDICTIONS AND TRAINING ENDPOINTS

## @app.route('/predict', methods=['POST'])
The prediction endpoint first checks if data was provided, and looks for a specific model version request and loads it. After this it validates the stock ticker symbol, validates the date information. Following the validation is the actual prediction and response. The endpoint makes its predictions after making sure the model is loaded. Then it makes the predictions through the predict function, and returns a json object of the prediction information. The endpoint logs any errors in the process. 


## @app.route('/train', methods=['POST'])
After this is the /train endpoint. The first section of /train has layered input validation. It accepts a POST request with JSON data and check if the data was provided, validates the ticker symbol or defaults to SPY if one isn’t specified, and uses a default range from 2014 to the current date if no date range is provided. After this, the endpoint trains the model with the train function and returns a json formatted object of the training data. The model is automatically saved after training. The response gives a success message, the training metrics (loss and validation), and the parameters used for training. Errors and metrics are registered in the appropriate files in the logs and metrics directory. 


# HEALTH MONITORING

## @app.route('/health', methods=['GET'])
The first /health endpoint is a basic ping checkpoint, it only returns that the status of the app is healthy. It isn’t informational beyond this. The /health/check endpoint is the more important health monitoring endpoint that is more comprehensive. 

## @app.route('/health/check', methods=['GET'])
In the health_check() function, it performs checks for the database health through the test_query test. If it can’t execute the basic query then that indicates an issue with the database connection. 
After this is the Redis Cache health. It writes a value and immediately tries to read it back for caching. This verifies that redis if functioning correctly for reading and writing. 
Beyond this is the background task health. It examines the task scheduler created for automated background tasks. It provides information on the next run, last run, and status of the scheduler. 
After the background task check, there is another check for model availability in the models_saved/ directory. 


# METRICS

## @app.route('/metrics', methods=['GET'])
The metrics endpoint uses get_metrics() to retrieve performance insights from the metrics feature which tracks prediction accuracy. If there are no predictions it will return a 404. 

# LOGGING

## @app.route('/logs', methods=['GET'])
Finally the logs end point handles the logging functionality that collects errors and general messages in the application process. It has automatic handling of missing log files. Protects against requesting more lines than available from logs. 

