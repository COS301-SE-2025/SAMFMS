# filepath: c:\Users\user\OneDrive\Documents\capstone\repo\SAMFMS\Core\logging_config.py
import logging
import sys
from datetime import datetime
import json

def setup_logging():
    """Setup structured logging configuration"""
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set levels for specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

def get_logger(name: str):
    """Get a logger instance"""
    return logging.getLogger(name)

class StructuredLogger:
    """Structured logger for consistent log formatting"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_event(self, level: str, event: str, **kwargs):
        """Log a structured event"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            **kwargs
        }
        
        log_message = json.dumps(log_data)
        
        if level.upper() == "DEBUG":
            self.logger.debug(log_message)
        elif level.upper() == "INFO":
            self.logger.info(log_message)
        elif level.upper() == "WARNING":
            self.logger.warning(log_message)
        elif level.upper() == "ERROR":
            self.logger.error(log_message)
        elif level.upper() == "CRITICAL":
            self.logger.critical(log_message)