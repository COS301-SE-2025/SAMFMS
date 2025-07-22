"""
RabbitMQ Configuration for GPS Service
Local copy of standardized configuration
"""

import os
from datetime import datetime

class RabbitMQConfig:
    """RabbitMQ configuration for management service"""
    
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/")
    HEARTBEAT = 60
    BLOCKED_CONNECTION_TIMEOUT = 300
    PREFETCH_COUNT = 10
    
    # Connection parameters with improved timeout handling
    CONNECTION_PARAMS = {
        "heartbeat": 60,
        "blocked_connection_timeout": 300,
        "connection_attempts": 3,
        "retry_delay": 1.0,
        "stack_timeout": 15.0,  # Stack timeout for operations
        "socket_timeout": 15.0
    }
    
    # Queue names (standardized)
    QUEUE_NAMES = {
        "gps": "gps.requests",
        "core": "core.responses"
    }
    
    # Exchange names
    EXCHANGE_NAMES = {
        "requests": "service_requests",
        "responses": "service_responses"
    }
    
    # Routing keys
    ROUTING_KEYS = {
        "core_responses": "core.responses"
    }
    
    def get_rabbitmq_url(self):
        """Get RabbitMQ connection URL"""
        return self.RABBITMQ_URL


def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    elif hasattr(obj, '__str__'):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
