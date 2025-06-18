"""
Logging configuration for SAMFMS Utilities service
"""
import logging
import json
import sys
import os
from datetime import datetime

# Create logs directory if it doesn't exist
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
            
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
            
        if hasattr(record, 'extra_data'):
            log_record.update(record.extra_data)
            
        return json.dumps(log_record)


def setup_logging():
    """
    Configure logging for the application
    """
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # Set the root logger level
    root_logger.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    
    # Create file handler
    log_file = os.path.join(LOG_DIR, f"utilities_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Suppress excessive logs from library code
    logging.getLogger('pika').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name):
    """
    Get a logger with the specified name
    
    Args:
        name: Name for the logger
        
    Returns:
        logging.Logger: A logger instance
    """
    return logging.getLogger(name)
