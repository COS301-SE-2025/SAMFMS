"""
Logging configuration for Maintenance Service
"""

import logging
import logging.config
import os
from datetime import datetime


def setup_logging():
    """Setup logging configuration for the maintenance service"""
    
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "detailed")
    
    if log_format == "json":
        formatter_class = "pythonjsonlogger.jsonlogger.JsonFormatter"
        format_string = "%(asctime)s %(name)s %(levelname)s %(message)s"
    else:
        formatter_class = "logging.Formatter"
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "class": formatter_class,
                "format": format_string
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "maintenance": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(config)
    
    # Set up maintenance service logger
    logger = logging.getLogger("maintenance")
    logger.info(f"Logging configured - Level: {log_level}, Format: {log_format}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)


# Setup logging when module is imported
logger = setup_logging()
