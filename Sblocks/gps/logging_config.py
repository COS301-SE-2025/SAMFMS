"""
Logging configuration module for GPS Service.
Provides structured JSON logging with environment-based configuration.
"""

import logging
import json
import os
from datetime import datetime
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging output."""
    
    def __init__(self, service_name: str, environment: str):
        super().__init__()
        self.service_name = service_name
        self.environment = environment
    
    def format(self, record):
        """Format log record as JSON with structured fields."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "environment": self.environment,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        extra_fields = ["request_id", "user_id", "duration_ms", "status_code", 
                       "method", "url", "user_agent", "remote_addr", "error", 
                       "traceback", "version", "metrics"]
        
        for field in extra_fields:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)
                
        return json.dumps(log_entry)


def setup_logging(
    service_name: str,
    log_level: Optional[str] = None,
    environment: Optional[str] = None
) -> logging.Logger:
    """
    Set up structured logging for the service.
    
    Args:
        service_name: Name of the service for log identification
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Environment name (development, staging, production)
    
    Returns:
        Configured logger instance
    """
    # Get configuration from environment or use defaults
    log_level = log_level or os.getenv("LOG_LEVEL", "INFO").upper()
    environment = environment or os.getenv("ENVIRONMENT", "development")
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Set JSON formatter for all handlers
    json_formatter = JSONFormatter(service_name, environment)
    for handler in logging.root.handlers:
        handler.setFormatter(json_formatter)
    
    # Create and return service logger
    logger = logging.getLogger(service_name)
    
    logger.info(
        "Logging configured successfully",
        extra={
            "log_level": log_level,
            "environment": environment,
            "service": service_name
        }
    )
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(name)
