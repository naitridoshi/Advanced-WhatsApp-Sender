import logging
import os
import logging.config
from logging.handlers import SocketHandler
import pythonjsonlogger.jsonlogger
from src import logcolor

# Create logs directory if it doesn't exist
logs_dir = os.path.join('src', 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Use proper path separator for the logging config file
logging_config_path = os.path.join('src', 'logging.ini')
logging.config.fileConfig(logging_config_path, disable_existing_loggers=True)
log = logging.getLogger(__name__)
try:
    socket_handler = SocketHandler("127.0.0.1", 19996)
except:
    pass
log.addHandler(socket_handler)
