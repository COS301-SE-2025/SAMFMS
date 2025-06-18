"""
Email Client for SAMFMS
Provides functions for sending emails through the utilities service
"""
import json
import pika
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

# RabbitMQ connection settings
RABBITMQ_HOST = "rabbitmq"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "guest"
RABBITMQ_PASSWORD = "guest"

# Email queue configuration
EMAIL_EXCHANGE = "samfms_notifications"
EMAIL_ROUTING_KEY = "email.send"

class EmailClient:
    """Client for sending emails through the utilities service"""
    
    def __init__(self, rabbitmq_host: str = RABBITMQ_HOST):
        """
        Initialize the email client
        
        Args:
            rabbitmq_host (str): RabbitMQ host address
        """
        self.rabbitmq_host = rabbitmq_host
        self.connection = None
        self.channel = None
    
    def connect(self) -> bool:
        """
        Connect to RabbitMQ server
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Set up connection parameters
            parameters = pika.ConnectionParameters(
                host=self.rabbitmq_host,
                port=RABBITMQ_PORT,
                credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD),
                heartbeat=60,
                blocked_connection_timeout=30
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
            
            logger.info(f"Connected to RabbitMQ at {self.rabbitmq_host}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
    
    def send_email(self, message: Dict[str, Any]) -> bool:
        """
        Send an email through the utilities service
        
        Args:
            message: Dictionary with email details
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            if not self.connection or self.connection.is_closed:
                if not self.connect():
                    logger.error("Cannot send email - no connection to RabbitMQ")
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
            
            logger.info(f"Email request sent: {message.get('to_email')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email request: {e}")
            return False
    
    def send_welcome_email(self, to_email: str, full_name: str, email: str, role: str) -> bool:
        """
        Send a welcome email to a new user
        
        Args:
            to_email: Recipient email
            full_name: User's full name
            email: User's email (can be same as to_email)
            role: User's role in the system
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        message = {
            "email_type": "welcome",
            "to_email": to_email,
            "full_name": full_name,
            "email": email,
            "role": role
        }
        return self.send_email(message)
    
    def send_password_reset(self, to_email: str, full_name: str, reset_link: str) -> bool:
        """
        Send a password reset email
        
        Args:
            to_email: Recipient email
            full_name: User's full name
            reset_link: Password reset link
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        message = {
            "email_type": "password_reset",
            "to_email": to_email,
            "full_name": full_name,
            "reset_link": reset_link
        }
        return self.send_email(message)

    def send_trip_assignment(self, to_email: str, full_name: str, trip_data: Dict) -> bool:
        """
        Send trip assignment notification
        
        Args:
            to_email: Recipient email
            full_name: User's full name
            trip_data: Dictionary with trip details
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        message = {
            "email_type": "trip_assignment",
            "to_email": to_email,
            "full_name": full_name,
            "trip_data": trip_data
        }
        return self.send_email(message)
    
    def send_maintenance_alert(self, to_email: str, full_name: str, maintenance_data: Dict) -> bool:
        """
        Send vehicle maintenance alert
        
        Args:
            to_email: Recipient email
            full_name: User's full name
            maintenance_data: Dictionary with maintenance details
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        message = {
            "email_type": "vehicle_maintenance",
            "to_email": to_email,
            "full_name": full_name,
            "maintenance_data": maintenance_data
        }
        return self.send_email(message)
    
    def send_alert(self, to_email: str, full_name: str, alert_data: Dict) -> bool:
        """
        Send general alert notification
        
        Args:
            to_email: Recipient email
            full_name: User's full name
            alert_data: Dictionary with alert details
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        message = {
            "email_type": "alert",
            "to_email": to_email,
            "full_name": full_name,
            "alert_data": alert_data
        }
        return self.send_email(message)
    
    def send_custom_email(self, to_email: str, full_name: str, subject: str, message: str) -> bool:
        """
        Send a custom email
        
        Args:
            to_email: Recipient email
            full_name: User's full name
            subject: Email subject
            message: Email message body
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        message_data = {
            "email_type": "custom",
            "to_email": to_email,
            "full_name": full_name,
            "subject": subject,
            "message": message
        }
        return self.send_email(message_data)
    
    def close(self):
        """Close the RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")


# Create a singleton instance
email_client = EmailClient()
