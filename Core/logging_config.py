# filepath: c:\Users\user\OneDrive\Documents\capstone\repo\SAMFMS\Core\logging_config.py
"""
Comprehensive Logging Configuration for SAMFMS Core
Provides structured logging with correlation IDs, JSON formatting, and multiple handlers
"""

import logging
import logging.config
import sys
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger

class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records"""
    
    def filter(self, record):
        # Try to get correlation ID from various sources
        correlation_id = getattr(record, 'correlation_id', None)
        if not correlation_id:
            # Try to get from thread local storage or context
            correlation_id = getattr(self, '_correlation_id', 'no-correlation-id')
        
        record.correlation_id = correlation_id
        return True

class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add service information
        log_record['service'] = 'samfms-core'
        log_record['version'] = os.getenv('SERVICE_VERSION', '1.0.0')
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add module and function info
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add correlation ID if present
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id
        
        # Add request ID if present
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        # Add user ID if present
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        
        # Add trace ID if present
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id

class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for development"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        # Format the message
        formatted = super().format(record)
        
        return formatted

def setup_logging(
    log_level: str = None,
    environment: str = None,
    enable_json_logging: bool = None,
    log_file: str = None
):
    """
    Setup comprehensive logging configuration
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        environment: Environment (development, production, etc.)
        enable_json_logging: Whether to use JSON formatting
        log_file: Optional log file path
    """
    
    # Get configuration from environment if not provided
    log_level = log_level or os.getenv('LOG_LEVEL', 'INFO')
    environment = environment or os.getenv('ENVIRONMENT', 'development')
    
    # Determine JSON logging based on environment
    if enable_json_logging is None:
        enable_json_logging = environment.lower() in ['production', 'staging']
    
    # Get log file from environment
    log_file = log_file or os.getenv('LOG_FILE')
    
    # Base logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'correlation_id': {
                '()': CorrelationIdFilter,
            },
        },
        'formatters': {
            'json': {
                '()': StructuredFormatter,
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
                'reserved_attrs': ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 'thread', 'threadName', 'processName', 'process'],
            },
            'console': {
                '()': ColoredConsoleFormatter,
                'format': '%(asctime)s | %(levelname)-8s | %(name)-20s | %(correlation_id)-12s | %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'file': {
                'format': '%(asctime)s | %(levelname)-8s | %(name)-20s | %(correlation_id)-12s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
        },
        'handlers': {
            'console': {
                'level': log_level,
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
                'formatter': 'json' if enable_json_logging else 'console',
                'filters': ['correlation_id'],
            },
        },
        'loggers': {
            '': {  # Root logger
                'level': log_level,
                'handlers': ['console'],
                'propagate': False,
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False,
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False,
            },
            'fastapi': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False,
            },
            'aio_pika': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False,
            },
            'motor': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False,
            },
        },
        'root': {
            'level': log_level,
            'handlers': ['console'],
        },
    }
    
    # Add file handler if log file is specified
    if log_file:
        config['handlers']['file'] = {
            'level': log_level,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': log_file,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json' if enable_json_logging else 'file',
            'filters': ['correlation_id'],
        }
        
        # Add file handler to all loggers
        for logger_config in config['loggers'].values():
            logger_config['handlers'].append('file')
        config['root']['handlers'].append('file')
    
    # Configure logging
    logging.config.dictConfig(config)
    
    # Log configuration info
    logger = logging.getLogger(__name__)
    logger.info("🔧 Logging configuration initialized")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Environment: {environment}")
    logger.info(f"JSON logging: {enable_json_logging}")
    if log_file:
        logger.info(f"Log file: {log_file}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with proper configuration
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    correlation_id: Optional[str] = None,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    **extra_context
):
    """
    Log a message with structured context
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        correlation_id: Correlation ID
        request_id: Request ID
        user_id: User ID
        trace_id: Trace ID
        **extra_context: Additional context fields
    """
    
    # Build extra context
    extra = {}
    if correlation_id:
        extra['correlation_id'] = correlation_id
    if request_id:
        extra['request_id'] = request_id
    if user_id:
        extra['user_id'] = user_id
    if trace_id:
        extra['trace_id'] = trace_id
    
    # Add any additional context
    extra.update(extra_context)
    
    # Get log method
    log_method = getattr(logger, level.lower())
    
    # Log with context
    log_method(message, extra=extra)

class LogContext:
    """Context manager for adding context to all logs within a block"""
    
    def __init__(self, **context):
        self.context = context
        self.old_factory = None
    
    def __enter__(self):
        # Store old factory
        self.old_factory = logging.getLogRecordFactory()
        
        # Create new factory with context
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        # Set new factory
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old factory
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)

# Utility functions for common logging patterns
def log_request_start(logger: logging.Logger, method: str, path: str, correlation_id: str):
    """Log request start"""
    log_with_context(
        logger, 'info',
        f"Request started: {method} {path}",
        correlation_id=correlation_id,
        http_method=method,
        http_path=path
    )

def log_request_end(logger: logging.Logger, method: str, path: str, status_code: int, 
                   duration_ms: float, correlation_id: str):
    """Log request end"""
    log_with_context(
        logger, 'info',
        f"Request completed: {method} {path} - {status_code} ({duration_ms:.2f}ms)",
        correlation_id=correlation_id,
        http_method=method,
        http_path=path,
        http_status_code=status_code,
        duration_ms=duration_ms
    )

def log_service_call(logger: logging.Logger, service: str, operation: str, 
                    correlation_id: str, **context):
    """Log service call"""
    log_with_context(
        logger, 'debug',
        f"Calling service: {service}.{operation}",
        correlation_id=correlation_id,
        service=service,
        operation=operation,
        **context
    )

def log_database_operation(logger: logging.Logger, operation: str, collection: str,
                          correlation_id: str, **context):
    """Log database operation"""
    log_with_context(
        logger, 'debug',
        f"Database operation: {operation} on {collection}",
        correlation_id=correlation_id,
        db_operation=operation,
        db_collection=collection,
        **context
    )

# Legacy support
class StructuredLogger:
    """Legacy structured logger for backward compatibility"""
    
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

# Initialize logging on import if not already configured
if not logging.getLogger().handlers:
    setup_logging()