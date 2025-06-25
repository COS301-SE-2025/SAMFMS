"""
Connection management module for GPS Service.
Handles Redis and RabbitMQ connections with proper error handling and logging.
"""

import redis
import pika
import traceback
from typing import Optional
from logging_config import get_logger

logger = get_logger(__name__)

# Global connection instances
_redis_client: Optional[redis.Redis] = None
_rabbitmq_connection = None


class ConnectionManager:
    """Manages database and message queue connections."""
    
    @staticmethod
    def get_redis_connection() -> Optional[redis.Redis]:
        """
        Get Redis connection with connection pooling and error handling.
        
        Returns:
            Redis client instance or None if connection fails
        """
        global _redis_client
        
        try:
            if not _redis_client:
                logger.info("Establishing Redis connection")
                _redis_client = redis.Redis(
                    host='redis', 
                    port=6379, 
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                _redis_client.ping()
                logger.info("Redis connection established successfully")
            
            return _redis_client
            
        except redis.ConnectionError as e:
            logger.error(
                "Redis connection error",
                extra={
                    "error": str(e),
                    "error_type": "ConnectionError",
                    "traceback": traceback.format_exc()
                }
            )
            _redis_client = None
            return None
            
        except redis.TimeoutError as e:
            logger.error(
                "Redis timeout error",
                extra={
                    "error": str(e),
                    "error_type": "TimeoutError",
                    "traceback": traceback.format_exc()
                }
            )
            _redis_client = None
            return None
            
        except Exception as e:
            logger.error(
                "Redis connection failed with unexpected error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            )
            _redis_client = None
            return None
    
    @staticmethod
    def get_rabbitmq_connection():
        """
        Get RabbitMQ connection with error handling.
        
        Returns:
            RabbitMQ connection instance or None if connection fails
        """
        global _rabbitmq_connection
        
        try:
            if not _rabbitmq_connection or _rabbitmq_connection.is_closed:
                logger.info("Establishing RabbitMQ connection")
                _rabbitmq_connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host='rabbitmq',
                        credentials=pika.PlainCredentials('samfms_rabbit', 'RabbitPass2025!'),
                        connection_attempts=3,
                        retry_delay=2
                    )
                )
                logger.info("RabbitMQ connection established successfully")
            
            return _rabbitmq_connection
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(
                "RabbitMQ AMQP connection error",
                extra={
                    "error": str(e),
                    "error_type": "AMQPConnectionError",
                    "traceback": traceback.format_exc()
                }
            )
            _rabbitmq_connection = None
            return None
            
        except Exception as e:
            logger.error(
                "RabbitMQ connection failed with unexpected error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            )
            _rabbitmq_connection = None
            return None
    
    @staticmethod
    def test_redis_connection() -> bool:
        """
        Test Redis connection health.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            redis_conn = ConnectionManager.get_redis_connection()
            if redis_conn:
                redis_conn.ping()
                logger.debug("Redis health check passed")
                return True
            return False
            
        except Exception as e:
            logger.error(
                "Redis health check failed",
                extra={
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            )
            return False
    
    @staticmethod
    def test_rabbitmq_connection() -> bool:
        """
        Test RabbitMQ connection health.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            rabbitmq_conn = ConnectionManager.get_rabbitmq_connection()
            if rabbitmq_conn and not rabbitmq_conn.is_closed:
                logger.debug("RabbitMQ health check passed")
                # Close the test connection
                rabbitmq_conn.close()
                return True
            return False
            
        except Exception as e:
            logger.error(
                "RabbitMQ health check failed",
                extra={
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            )
            return False
    
    @staticmethod
    def close_connections():
        """Close all active connections during shutdown."""
        global _redis_client, _rabbitmq_connection
        
        # Close Redis connection
        if _redis_client:
            try:
                _redis_client.close()
                logger.info("Redis connection closed successfully")
            except Exception as e:
                logger.error(
                    "Error closing Redis connection",
                    extra={"error": str(e)}
                )
            finally:
                _redis_client = None
        
        # Close RabbitMQ connection
        if _rabbitmq_connection and not _rabbitmq_connection.is_closed:
            try:
                _rabbitmq_connection.close()
                logger.info("RabbitMQ connection closed successfully")
            except Exception as e:
                logger.error(
                    "Error closing RabbitMQ connection",
                    extra={"error": str(e)}
                )
            finally:
                _rabbitmq_connection = None


# Convenience functions for backward compatibility
def get_redis_connection():
    """Get Redis connection - convenience function."""
    return ConnectionManager.get_redis_connection()


def get_rabbitmq_connection():
    """Get RabbitMQ connection - convenience function."""
    return ConnectionManager.get_rabbitmq_connection()
