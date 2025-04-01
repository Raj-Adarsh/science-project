import logging
import os
from logging.handlers import TimedRotatingFileHandler

def get_logger(name=__name__):
    logger = logging.getLogger(name)
    logger.setLevel(logging.WARNING)

    if not logger.handlers:
        # Create logs directory if it doesn't exist.
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "server.log")

        # Create a handler that rotates logs at midnight and keeps 7 days of logs.
        file_handler = TimedRotatingFileHandler(log_file, when="midnight", backupCount=7)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        # Also add a stream handler to output logs to the console.
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)
        logger.addHandler(stream_handler)
    return logger
