# RabbitMQ messaging configuration and utilities
import pika
import json
import asyncio
from typing import Dict, Any, Callable
import os
from datetime import datetime

class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.username = os.getenv("RABBITMQ_USERNAME", "guest")
        self.password = os.getenv("RABBITMQ_PASSWORD", "guest")
        
    def connect(self):
        """Establish connection to RabbitMQ"""
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # Declare exchanges and queues
        self._setup_exchanges_and_queues()
        
    def _setup_exchanges_and_queues(self):
        """Setup exchanges and queues for trip planning"""
        # Main exchange for trip planning events
        self.channel.exchange_declare(
            exchange='trip_planning_events',
            exchange_type='topic',
            durable=True
        )
        
        # Queue for outgoing messages to MCore
        self.channel.queue_declare(queue='trip_planning_to_mcore', durable=True)
        self.channel.queue_bind(
            exchange='trip_planning_events',
            queue='trip_planning_to_mcore',
            routing_key='trip.#'
        )
        
        # Queue for incoming messages from MCore
        self.channel.queue_declare(queue='mcore_to_trip_planning', durable=True)
        
        # Queue for vehicle updates
        self.channel.queue_declare(queue='vehicle_updates', durable=True)
        
        # Queue for driver updates  
        self.channel.queue_declare(queue='driver_updates', durable=True)
        
    def publish_trip_event(self, event_type: str, trip_data: Dict[str, Any]):
        """Publish trip-related events"""
        message = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'trip_planning',
            'data': trip_data
        }
        
        routing_key = f"trip.{event_type}"
        
        self.channel.basic_publish(
            exchange='trip_planning_events',
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json'
            )
        )
        
    def publish_to_mcore(self, message_type: str, data: Dict[str, Any]):
        """Send messages to MCore for frontend updates"""
        message = {
            'message_type': message_type,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'trip_planning_service',
            'data': data
        }
        
        self.channel.basic_publish(
            exchange='',
            routing_key='trip_planning_to_mcore',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        
    def setup_consumer(self, queue_name: str, callback: Callable):
        """Setup consumer for incoming messages"""
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=False
        )
        
    def start_consuming(self):
        """Start consuming messages"""
        self.channel.start_consuming()
        
    def stop_consuming(self):
        """Stop consuming messages"""
        self.channel.stop_consuming()
        
    def close(self):
        """Close connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

# Message handlers
def handle_vehicle_update(ch, method, properties, body):
    """Handle vehicle status updates from MCore"""
    try:
        message = json.loads(body)
        # Process vehicle update
        # Update vehicle status in trip planning database
        print(f"Received vehicle update: {message}")
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing vehicle update: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def handle_driver_update(ch, method, properties, body):
    """Handle driver status updates from MCore"""
    try:
        message = json.loads(body)
        # Process driver update
        print(f"Received driver update: {message}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing driver update: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def handle_mcore_request(ch, method, properties, body):
    """Handle requests from MCore"""
    try:
        message = json.loads(body)
        # Process MCore request
        print(f"Received MCore request: {message}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing MCore request: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

# Global instance
rabbitmq_client = RabbitMQClient()
