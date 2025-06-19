"""
RabbitMQ Service for SAMFMS Utilities
Handles consuming messages from RabbitMQ queues
"""
import json
import pika
import logging
import threading
import time
from typing import Dict, Any, Callable
from services.email_service import EmailService

logger = logging.getLogger(__name__)

# RabbitMQ connection settings
RABBITMQ_HOST = "rabbitmq"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "guest"
RABBITMQ_PASSWORD = "guest"

# Email queue configuration
EMAIL_QUEUE = "email_notifications"
EMAIL_EXCHANGE = "samfms_notifications"
EMAIL_ROUTING_KEY = "email.send"

class RabbitMQService:
    """Service for handling RabbitMQ connections and message processing"""
    
    def __init__(self):
        """Initialize the RabbitMQ service"""
        self.connection = None
        self.channel = None
        self.consumer_thread = None
        self.running = False
    
    def connect(self) -> bool:
        """
        Connect to RabbitMQ server
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Set up connection parameters
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD),
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            # Create connection and channel
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=EMAIL_EXCHANGE,
                exchange_type='topic',
                durable=True
            )
            
            # Declare queue
            self.channel.queue_declare(
                queue=EMAIL_QUEUE,
                durable=True
            )
            
            # Bind queue to exchange
            self.channel.queue_bind(
                exchange=EMAIL_EXCHANGE,
                queue=EMAIL_QUEUE,
                routing_key=EMAIL_ROUTING_KEY
            )
            
            logger.info(f"Connected to RabbitMQ at {RABBITMQ_HOST}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
    
    def consume_messages(self):
        """
        Start consuming messages from the email queue
        This method will block the current thread
        """
        try:
            # Set up callback for message processing
            self.channel.basic_consume(
                queue=EMAIL_QUEUE,
                on_message_callback=self._process_message,
                auto_ack=False
            )
            
            logger.info(f"Starting to consume messages from queue: {EMAIL_QUEUE}")
            self.running = True
            
            # Start consuming
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            self.running = False
    
    def _process_message(self, channel, method, properties, body):
        """
        Process incoming RabbitMQ message
        
        Args:
            channel: The channel object
            method: The method frame
            properties: The properties
            body: The message body
        """
        try:
            # Parse message
            message = json.loads(body)
            logger.info(f"Received email request: {message}")
            
            # Process message based on type
            email_type = message.get("email_type", "custom")
            result = False
            
            if email_type == "welcome":
                result = EmailService.send_welcome_email(
                    message["to_email"],
                    message["full_name"],
                    message["email"],
                    message["role"]
                )
            elif email_type == "password_reset":
                result = EmailService.send_password_reset(
                    message["to_email"],
                    message["full_name"],
                    message["reset_link"]
                )
            elif email_type == "trip_assignment":
                result = EmailService.send_trip_assignment(
                    message["to_email"],
                    message["full_name"],
                    message["trip_data"]
                )
            elif email_type == "vehicle_maintenance":
                result = EmailService.send_maintenance_alert(
                    message["to_email"],
                    message["full_name"],
                    message["maintenance_data"]
                )
            elif email_type == "alert":
                result = EmailService.send_alert_notification(
                    message["to_email"],
                    message["full_name"],
                    message["alert_data"]
                )
            else:  # Custom email
                result = EmailService.send_custom_email(
                    message["to_email"],
                    message["full_name"],
                    message["subject"],
                    message["message"]
                )
            
            if result:
                logger.info(f"Email sent successfully: {message.get('to_email')}")
                channel.basic_ack(delivery_tag=method.delivery_tag)
            else:
                logger.error(f"Failed to send email: {message.get('to_email')}")
                # Negative acknowledgement, requeue for later processing
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                
        except json.JSONDecodeError:
            logger.error(f"Invalid message format: {body}")
            # Don't requeue invalid messages
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except KeyError as e:
            logger.error(f"Missing required field in message: {e}")
            # Don't requeue messages with missing fields
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Requeue on other errors
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consumer_thread(self):
        """Start the consumer in a separate thread"""
        if self.consumer_thread and self.consumer_thread.is_alive():
            logger.warning("Consumer thread is already running")
            return
            
        self.consumer_thread = threading.Thread(target=self._consumer_thread_target)
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
        logger.info("Consumer thread started")
    
    def _consumer_thread_target(self):
        """Target function for consumer thread with reconnection logic"""
        while True:
            try:
                if not self.connection or self.connection.is_closed:
                    if self.connect():
                        self.consume_messages()
                    else:
                        logger.warning("Connection failed, retrying in 5 seconds...")
                        time.sleep(5)
                else:
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Consumer thread error: {e}")
                time.sleep(5)
    
    def publish_email_request(self, message: Dict[str, Any]) -> bool:
        """
        Publish an email request to the email queue
        
        Args:
            message: Dictionary with email details
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            if not self.connection or self.connection.is_closed:
                if not self.connect():
                    logger.error("Cannot publish message - no connection to RabbitMQ")
                    return False
            
            # Convert message to JSON
            message_json = json.dumps(message)
            
            # Publish message
            self.channel.basic_publish(
                exchange=EMAIL_EXCHANGE,
                routing_key=EMAIL_ROUTING_KEY,
                body=message_json,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type='application/json'
                )
            )
            
            logger.info(f"Published email request: {message.get('to_email')}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish email request: {e}")
            return False
    
    def close(self):
        """Close the RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.running = False
                if self.channel:
                    self.channel.stop_consuming()
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")


# Singleton instance
rabbitmq_service = RabbitMQService()
