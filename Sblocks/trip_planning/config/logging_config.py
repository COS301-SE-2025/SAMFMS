import logging
import sys
from typing import Dict, Any
from config.settings import settings


class TripPlanningLogger:
    """Centralized logging configuration for Trip Planning service"""
    
    def __init__(self):
        self.logger = None
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging for the service"""
        # Create logger
        self.logger = logging.getLogger(settings.SERVICE_NAME)
        self.logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        # Prevent duplicate logs
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        # Create formatter
        formatter = logging.Formatter(settings.LOG_FORMAT)
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(console_handler)
    
    def get_logger(self):
        """Get the configured logger"""
        return self.logger
    
    def log_request(self, method: str, path: str, status_code: int, duration: float, user_id: str = None):
        """Log HTTP request details"""
        self.logger.info(
            f"HTTP {method} {path} - Status: {status_code} - Duration: {duration:.3f}s - User: {user_id or 'Anonymous'}"
        )
    
    def log_database_operation(self, operation: str, collection: str, document_id: str = None, duration: float = None):
        """Log database operation details"""
        message = f"Database {operation} on {collection}"
        if document_id:
            message += f" - ID: {document_id}"
        if duration:
            message += f" - Duration: {duration:.3f}s"
        self.logger.info(message)
    
    def log_rabbitmq_operation(self, operation: str, queue: str, message_type: str = None, correlation_id: str = None):
        """Log RabbitMQ operation details"""
        message = f"RabbitMQ {operation} on {queue}"
        if message_type:
            message += f" - Type: {message_type}"
        if correlation_id:
            message += f" - CorrelationID: {correlation_id}"
        self.logger.info(message)
    
    def log_external_service_call(self, service: str, endpoint: str, status_code: int = None, duration: float = None):
        """Log external service call details"""
        message = f"External call to {service} - {endpoint}"
        if status_code:
            message += f" - Status: {status_code}"
        if duration:
            message += f" - Duration: {duration:.3f}s"
        self.logger.info(message)
    
    def log_trip_operation(self, operation: str, trip_id: str, details: Dict[str, Any] = None):
        """Log trip-specific operation"""
        message = f"Trip {operation} - ID: {trip_id}"
        if details:
            message += f" - Details: {details}"
        self.logger.info(message)
    
    def log_driver_assignment(self, action: str, driver_id: str, trip_id: str, status: str = None):
        """Log driver assignment operations"""
        message = f"Driver assignment {action} - Driver: {driver_id} - Trip: {trip_id}"
        if status:
            message += f" - Status: {status}"
        self.logger.info(message)
    
    def log_analytics_calculation(self, metric_type: str, calculation_time: float, result_count: int = None):
        """Log analytics calculation details"""
        message = f"Analytics calculation - Type: {metric_type} - Time: {calculation_time:.3f}s"
        if result_count is not None:
            message += f" - Results: {result_count}"
        self.logger.info(message)


# Global logger instance
trip_planning_logger = TripPlanningLogger()


def get_logger():
    """Get the configured logger instance"""
    return trip_planning_logger.get_logger()


def log_info(message: str):
    """Log info message"""
    trip_planning_logger.logger.info(message)


def log_error(message: str, exc_info: bool = False):
    """Log error message"""
    trip_planning_logger.logger.error(message, exc_info=exc_info)


def log_warning(message: str):
    """Log warning message"""
    trip_planning_logger.logger.warning(message)


def log_debug(message: str):
    """Log debug message"""
    trip_planning_logger.logger.debug(message)
