import logging.handlers
import os

def setup_logging(log_dir = 'logs'):
    """Configure application-wide logging"""
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    #create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    #File handler for everything
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes = 10485760, #10 MB
        backupCount = 5
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)

    #Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10485760,
        backupCount=5
    )
    error_handler.setFormatter(file_formatter)
    error_handler.setLevel(logging.ERROR)

    #Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    #Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)

    #Create separate loggers for different components
    loggers = {
        'api': logging.getLogger('api'),
        'model': logging.getLogger('model'),
        'metrics': logging.getLogger('metrics')
    }

    for logger in loggers.values():
        logger.setLevel(logging.INFO)

    return loggers
