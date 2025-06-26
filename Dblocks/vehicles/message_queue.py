import os
import pika
import json
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime, timezone

from database import log_vehicle_activity, get_mongodb
from models_simple import VehicleEventMessage

logger = logging.getLogger(__name__)

class VehicleMessageConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.setup_connection()
    def setup_connection(self):
        """Setup RabbitMQ connection and channel with optimized settings"""
        try:
            credentials = pika.PlainCredentials(
                os.getenv('RABBITMQ_USER', 'samfms_rabbit'),
                os.getenv('RABBITMQ_PASSWORD', 'samfms_rabbit123')
            )
            parameters = pika.ConnectionParameters(
                host='rabbitmq',
                port=5672,
                credentials=credentials,
                heartbeat=300,  # Reduced heartbeat
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=2,
                socket_timeout=10,
                frame_max=131072,
                channel_max=10
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Set QoS to process one message at a time
            self.channel.basic_qos(prefetch_count=1, global_qos=False)
            
            # Declare exchange with optimized settings
            self.channel.exchange_declare(
                exchange='vehicle_events',
                exchange_type='topic',
                durable=True,
                auto_delete=False,
                arguments={'x-max-length': 1000}
            )
            
            # Declare queue for vehicle specifications with TTL and limits
            self.channel.queue_declare(
                queue='vehicle_technical_updates',
                durable=True,
                arguments={
                    'x-message-ttl': 300000,  # 5 minutes TTL
                    'x-max-length': 500,
                    'x-overflow': 'drop-head'
                }
            )
            
            # Bind queue to exchange with routing keys
            routing_keys = [
                'vehicle.created',
                'vehicle.updated',
                'vehicle.deleted',
                'vehicle.assignment_created',
                'vehicle.assignment_updated',
                'vehicle.usage_recorded',
                'vehicle.status_updated',
                'vehicle.maintenance_due'
            ]
            
            for routing_key in routing_keys:
                self.channel.queue_bind(
                    exchange='vehicle_events',
                    queue='vehicle_technical_updates',
                    routing_key=routing_key
                )
            
            logger.info("RabbitMQ connection and bindings setup successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup RabbitMQ connection: {e}")
            raise
    def process_vehicle_event(self, ch, method, properties, body):
        """Process incoming vehicle events"""
        try:
            # Parse message
            message_data = json.loads(body.decode('utf-8'))
            event = VehicleEventMessage(**message_data)
            
            logger.info(f"Processing vehicle event: {event.event_type} for vehicle {event.vehicle_id}")
            
            # Route to appropriate handler
            if event.event_type == 'vehicle.created':
                self.handle_vehicle_created(event)
            elif event.event_type == 'vehicle.updated':
                self.handle_vehicle_updated(event)
            elif event.event_type == 'vehicle.deleted':
                self.handle_vehicle_deleted(event)
            elif event.event_type == 'assignment_created':
                self.handle_assignment_created(event)
            elif event.event_type == 'assignment_updated':
                self.handle_assignment_updated(event)
            elif event.event_type == 'usage_recorded':
                self.handle_usage_recorded(event)
            elif event.event_type == 'status_updated':
                self.handle_status_updated(event)
            elif event.event_type == 'maintenance_due':
                self.handle_maintenance_due(event)
            else:
                logger.warning(f"Unknown event type: {event.event_type}")
            
            # Acknowledge message after successful processing
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Error processing vehicle event: {e}")
            # Reject message and don't requeue to prevent infinite loops
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    def handle_vehicle_created(self, event: VehicleEventMessage):
        """Handle vehicle creation event"""
        try:
            # Just log the event for now
            logger.info(f"Vehicle {event.vehicle_id} creation event received")
            
        except Exception as e:
            logger.error(f"Error handling vehicle creation: {e}")
    
    def handle_vehicle_updated(self, event: VehicleEventMessage):
        """Handle vehicle update event"""
        try:
            # Just log the event for now
            logger.info(f"Vehicle {event.vehicle_id} update event received")
            
        except Exception as e:
            logger.error(f"Error handling vehicle update: {e}")
    
    def handle_vehicle_deleted(self, event: VehicleEventMessage):
        """Handle vehicle deletion event"""
        try:
            # Just log the event for now
            logger.info(f"Vehicle {event.vehicle_id} deletion event received")
            
        except Exception as e:
            logger.error(f"Error handling vehicle deletion: {e}")    
    def handle_assignment_created(self, event: VehicleEventMessage):
        """Handle vehicle assignment creation"""
        try:
            # Just log the event for now
            logger.info(f"Assignment created for vehicle {event.vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling assignment creation: {e}")
            
    def handle_assignment_updated(self, event: VehicleEventMessage):
        """Handle vehicle assignment update"""
        try:
            # Just log the event for now
            logger.info(f"Assignment updated for vehicle {event.vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling assignment update: {e}")
    def handle_usage_recorded(self, event: VehicleEventMessage):
        """Handle vehicle usage recording"""
        try:
            # Just log the event for now
            logger.info(f"Usage recorded for vehicle {event.vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling usage recording: {e}")
    
    def handle_status_updated(self, event: VehicleEventMessage):
        """Handle vehicle status update"""
        try:
            # Just log the event for now
            logger.info(f"Status updated for vehicle {event.vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling status update: {e}")    
    def handle_maintenance_due(self, event: VehicleEventMessage):
        """Handle maintenance due notification"""
        try:
            # Just log the event for now
            logger.info(f"Maintenance due notification for vehicle {event.vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling maintenance due: {e}")
    def start_consuming(self):
        """Start consuming messages with optimized settings"""
        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue='vehicle_technical_updates',
                on_message_callback=self.process_vehicle_event,
                auto_ack=False  # Manual acknowledgment for better reliability
            )
            
            logger.info("Starting to consume vehicle events...")
            
            # Optimized consumption loop with reduced CPU usage
            while True:
                try:
                    # Increased time limit to reduce CPU usage
                    self.connection.process_data_events(time_limit=5)
                except KeyboardInterrupt:
                    logger.info("Stopping consumer...")
                    break
                except Exception as e:
                    logger.error(f"Error processing vehicle events: {e}")
                    # Brief pause to prevent tight loop on errors
                    import time
                    time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in message consumption: {e}")
        finally:
            self.stop_consuming()
    
    def stop_consuming(self):
        """Stop consuming messages"""
        if self.channel:
            self.channel.stop_consuming()
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        logger.info("Message consumer stopped")

# Async wrapper for integration with FastAPI
async def setup_message_consumer():
    """Setup and start the message consumer in background"""
    try:
        consumer = VehicleMessageConsumer()
        
        # Start consuming in a separate thread
        import threading
        consumer_thread = threading.Thread(target=consumer.start_consuming, daemon=True)
        consumer_thread.start()
        
        logger.info("Vehicle message consumer started successfully")
        return consumer
        
    except Exception as e:
        logger.error(f"Failed to setup message consumer: {e}")
        raise

def publish_maintenance_event(event_data: Dict[str, Any]):
    """Publish maintenance-related events"""
    try:
        credentials = pika.PlainCredentials(
            os.getenv('RABBITMQ_USER', 'samfms_rabbit'),
            os.getenv('RABBITMQ_PASSWORD', 'samfms_rabbit123')
        )
        parameters = pika.ConnectionParameters(
            host='rabbitmq',
            port=5672,
            credentials=credentials
        )
        
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declare exchange
        channel.exchange_declare(
            exchange='vehicle_events',
            exchange_type='topic',
            durable=True
        )
        
        # Publish message
        message = json.dumps(event_data)
        channel.basic_publish(
            exchange='vehicle_events',
            routing_key=f"maintenance.{event_data.get('event_type', 'updated')}",
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json'
            )
        )
        
        connection.close()
        logger.info(f"Published maintenance event: {event_data.get('event_type')}")
        
    except Exception as e:
        logger.error(f"Failed to publish maintenance event: {e}")
