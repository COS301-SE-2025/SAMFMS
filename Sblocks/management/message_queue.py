import pika
import json
import logging
from typing import Dict, Any
from models import VehicleCreatedMessage, VehicleUpdatedMessage, VehicleDeletedMessage, VehicleSpecs

logger = logging.getLogger(__name__)


class MessageQueueService:
    def __init__(self, host='rabbitmq', username='guest', password='guest'):
        self.host = host
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self._connection_pool = []
        self._max_pool_size = 5
        
    def _get_connection(self):
        """Get or create a connection with pooling for better efficiency"""
        try:
            # Try to reuse existing connection if available
            if self.connection and not self.connection.is_closed:
                return self.connection
            
            # Create new connection with optimized settings
            credentials = pika.PlainCredentials(self.username, self.password)
            connection_params = pika.ConnectionParameters(
                host=self.host,
                credentials=credentials,
                heartbeat=600,  # Longer heartbeat for publishers
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=2,
                socket_timeout=10,
                frame_max=131072,
                channel_max=50  # Reduced for publisher
            )
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            
            # Set up exchanges and queues
            self._setup_exchanges_and_queues()
            
            logger.info("Created new optimized RabbitMQ connection")
            return self.connection
            
        except Exception as e:
            logger.error(f"Failed to get RabbitMQ connection: {e}")
            return None
          def connect(self):
        """Establish connection to RabbitMQ with optimized settings"""
        try:
            connection = self._get_connection()
            if connection:
                logger.info("Successfully connected to RabbitMQ with optimized settings")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
    
    def _setup_exchanges_and_queues(self):
        """Setup RabbitMQ exchanges and queues with optimized settings"""
        # Vehicle-related exchanges with optimized settings
        self.channel.exchange_declare(
            exchange='vehicle_events', 
            exchange_type='topic',
            durable=True,
            auto_delete=False,
            arguments={'x-max-length': 1000}
        )
        
        # Queues for vehicle events with TTL and max length
        self.channel.queue_declare(
            queue='vehicle_specs_updates', 
            durable=True,
            arguments={
                'x-message-ttl': 300000,  # 5 minutes TTL
                'x-max-length': 500,
                'x-overflow': 'drop-head'
            }
        )
        self.channel.queue_declare(
            queue='vehicle_management_updates', 
            durable=True,
            arguments={
                'x-message-ttl': 300000,
                'x-max-length': 500,
                'x-overflow': 'drop-head'
            }
        )
        
        # Bind queues to exchanges
        self.channel.queue_bind(
            exchange='vehicle_events',
            queue='vehicle_specs_updates',
            routing_key='vehicle.specs.*'
        )
        self.channel.queue_bind(
            exchange='vehicle_events',
            queue='vehicle_management_updates', 
            routing_key='vehicle.management.*'
        )
      def publish_vehicle_created(self, vehicle_data: VehicleCreatedMessage):
        """Publish vehicle created event to Vehicles Dblock"""
        try:
            if not self._get_connection():
                logger.error("No RabbitMQ connection available for publishing")
                return
                
            message = vehicle_data.model_dump_json()
            self.channel.basic_publish(
                exchange='vehicle_events',
                routing_key='vehicle.specs.created',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            logger.info(f"Published vehicle created event for vehicle_id: {vehicle_data.vehicle_id}")
        except Exception as e:
            logger.error(f"Failed to publish vehicle created event: {e}")
            # Reset connection on error
            self.connection = None
      def publish_vehicle_updated(self, vehicle_data: VehicleUpdatedMessage):
        """Publish vehicle updated event to Vehicles Dblock"""
        try:
            if not self._get_connection():
                logger.error("No RabbitMQ connection available for publishing")
                return
                
            message = vehicle_data.model_dump_json()
            self.channel.basic_publish(
                exchange='vehicle_events',
                routing_key='vehicle.specs.updated',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            logger.info(f"Published vehicle updated event for vehicle_id: {vehicle_data.vehicle_id}")
        except Exception as e:
            logger.error(f"Failed to publish vehicle updated event: {e}")
            # Reset connection on error
            self.connection = None
      def publish_vehicle_deleted(self, vehicle_data: VehicleDeletedMessage):
        """Publish vehicle deleted event to Vehicles Dblock"""
        try:
            if not self._get_connection():
                logger.error("No RabbitMQ connection available for publishing")
                return
                
            message = vehicle_data.model_dump_json()
            self.channel.basic_publish(
                exchange='vehicle_events',
                routing_key='vehicle.specs.deleted',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            logger.info(f"Published vehicle deleted event for vehicle_id: {vehicle_data.vehicle_id}")
        except Exception as e:
            logger.error(f"Failed to publish vehicle deleted event: {e}")
            # Reset connection on error
            self.connection = None
      def publish_vehicle_status_changed(self, vehicle_id: str, old_status: str, new_status: str):
        """Publish vehicle status change event"""
        try:
            if not self._get_connection():
                logger.error("No RabbitMQ connection available for publishing")
                return
                
            message_data = {
                "vehicle_id": vehicle_id,
                "old_status": old_status,
                "new_status": new_status,
                "timestamp": json.loads(json.dumps({"timestamp": "now"}, default=str))
            }
            message = json.dumps(message_data)
            self.channel.basic_publish(
                exchange='vehicle_events',
                routing_key='vehicle.management.status_changed',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            logger.info(f"Published vehicle status change event for vehicle_id: {vehicle_id}")
        except Exception as e:
            logger.error(f"Failed to publish vehicle status change event: {e}")
            # Reset connection on error
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
