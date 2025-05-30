import pika
import json
import logging
from typing import Dict, Any
from models import UserCreatedMessage, UserUpdatedMessage, UserDeletedMessage

logger = logging.getLogger(__name__)


class MessageQueueService:
    def __init__(self, host='rabbitmq', username='guest', password='guest'):
        self.host = host
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self._connection_pool = None
        
    def connect(self):
        """Establish connection to RabbitMQ with optimized settings"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            connection_params = pika.ConnectionParameters(
                host=self.host,
                credentials=credentials,
                heartbeat=300,  # Reduced from 600 to save resources
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=2,
                socket_timeout=10,
                frame_max=131072,  # Optimize frame size
                channel_max=100,   # Limit channels
                virtual_host='/'
            )
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            
            # Set QoS to limit unacknowledged messages and reduce CPU load
            self.channel.basic_qos(prefetch_count=10, global_qos=False)
            
            # Declare exchanges and queues
            self._setup_exchanges_and_queues()
            
            logger.info("Successfully connected to RabbitMQ with optimized settings")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
      def _setup_exchanges_and_queues(self):
        """Setup RabbitMQ exchanges and queues with optimized settings"""
        # User-related exchanges with optimized settings
        self.channel.exchange_declare(
            exchange='user_events', 
            exchange_type='topic',
            durable=True,
            auto_delete=False,
            arguments={'x-max-length': 1000}  # Limit queue length to prevent memory issues
        )
        
        # Queues for user events with TTL and max length
        self.channel.queue_declare(
            queue='user_profile_updates', 
            durable=True,
            arguments={
                'x-message-ttl': 300000,  # 5 minutes TTL
                'x-max-length': 500,      # Max 500 messages
                'x-overflow': 'drop-head' # Drop oldest messages when full
            }
        )
        self.channel.queue_declare(
            queue='user_security_updates', 
            durable=True,
            arguments={
                'x-message-ttl': 300000,
                'x-max-length': 500,
                'x-overflow': 'drop-head'
            }
        )
        
        # Bind queues to exchanges
        self.channel.queue_bind(
            exchange='user_events',
            queue='user_profile_updates',
            routing_key='user.profile.*'
        )
        self.channel.queue_bind(
            exchange='user_events',
            queue='user_security_updates', 
            routing_key='user.security.*'
        )
      def publish_user_created(self, user_data: UserCreatedMessage):
        """Publish user created event to Users Dblock with optimized settings"""
        try:
            if not self.connection or self.connection.is_closed:
                if not self.connect():
                    logger.error("Cannot publish: no connection to RabbitMQ")
                    return
                    
            message = user_data.model_dump_json()
            self.channel.basic_publish(
                exchange='user_events',
                routing_key='user.profile.created',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=1,  # Non-persistent messages for better performance
                    content_type='application/json',
                    expiration='300000'  # 5 minutes expiration
                )
            )
            logger.info(f"Published user created event for user_id: {user_data.user_id}")
        except Exception as e:
            logger.error(f"Failed to publish user created event: {e}")
            # Try to reconnect on next publish
            self.connection = None
      def publish_user_updated(self, user_data: UserUpdatedMessage):
        """Publish user updated event to Users Dblock with optimized settings"""
        try:
            if not self.connection or self.connection.is_closed:
                if not self.connect():
                    logger.error("Cannot publish: no connection to RabbitMQ")
                    return
                    
            message = user_data.model_dump_json()
            self.channel.basic_publish(
                exchange='user_events',
                routing_key='user.profile.updated',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=1,
                    content_type='application/json',
                    expiration='300000'
                )
            )
            logger.info(f"Published user updated event for user_id: {user_data.user_id}")
        except Exception as e:
            logger.error(f"Failed to publish user updated event: {e}")
            self.connection = None

    def publish_user_deleted(self, user_data: UserDeletedMessage):
        """Publish user deleted event to Users Dblock with optimized settings"""
        try:
            if not self.connection or self.connection.is_closed:
                if not self.connect():
                    logger.error("Cannot publish: no connection to RabbitMQ")
                    return
                    
            message = user_data.model_dump_json()
            self.channel.basic_publish(
                exchange='user_events',
                routing_key='user.profile.deleted',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=1,
                    content_type='application/json',
                    expiration='300000'
                )
            )
            logger.info(f"Published user deleted event for user_id: {user_data.user_id}")
        except Exception as e:
            logger.error(f"Failed to publish user deleted event: {e}")
            self.connection = None
    
    def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("Closed RabbitMQ connection")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")


# Global message queue service instance
mq_service = MessageQueueService()
