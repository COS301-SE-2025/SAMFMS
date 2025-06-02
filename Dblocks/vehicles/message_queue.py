import pika
import json
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime, timezone

from .database import SessionLocal, log_vehicle_activity
from .models import Vehicle, MaintenanceRecord, VehicleEventMessage

logger = logging.getLogger(__name__)

class VehicleMessageConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.setup_connection()
    def setup_connection(self):
        """Setup RabbitMQ connection and channel with optimized settings"""
        try:
            credentials = pika.PlainCredentials('guest', 'guest')
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
            db = SessionLocal()
            
            # Check if vehicle already exists
            existing_vehicle = db.query(Vehicle).filter(Vehicle.id == event.vehicle_id).first()
            if existing_vehicle:
                logger.info(f"Vehicle {event.vehicle_id} already exists, skipping creation")
                return
            
            # Create vehicle record from event data
            vehicle_data = event.data
            vehicle = Vehicle(
                id=event.vehicle_id,
                vehicle_number=vehicle_data.get('vehicle_number'),
                make=vehicle_data.get('make'),
                model=vehicle_data.get('model'),
                year=vehicle_data.get('year'),
                vin=vehicle_data.get('vin'),
                license_plate=vehicle_data.get('license_plate'),
                engine_type=vehicle_data.get('engine_type'),
                fuel_type=vehicle_data.get('fuel_type'),
                fuel_capacity=vehicle_data.get('fuel_capacity'),
                seating_capacity=vehicle_data.get('seating_capacity'),
                max_load_capacity=vehicle_data.get('max_load_capacity'),
                transmission_type=vehicle_data.get('transmission_type'),
                drive_type=vehicle_data.get('drive_type'),
                color=vehicle_data.get('color'),
                current_mileage=vehicle_data.get('current_mileage', 0.0),
                is_active=vehicle_data.get('is_active', True),
                purchase_date=datetime.fromisoformat(vehicle_data['purchase_date']) if vehicle_data.get('purchase_date') else None,
                purchase_price=vehicle_data.get('purchase_price'),
                additional_specs=vehicle_data.get('additional_specs')
            )
            db.add(vehicle)
            db.commit()
            
            # Log activity synchronously to avoid async/sync context issues
            try:
                import threading
                def log_async():
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(log_vehicle_activity(
                            vehicle_id=event.vehicle_id,
                            activity_type="vehicle_created_from_event",
                            description="Vehicle record created from management service",
                            details={"source": event.source}
                        ))
                    finally:
                        loop.close()
                
                threading.Thread(target=log_async, daemon=True).start()
            except Exception as log_error:
                logger.warning(f"Failed to log vehicle creation activity: {log_error}")
            
            logger.info(f"Vehicle {event.vehicle_id} created successfully")
            
        except Exception as e:
            logger.error(f"Error handling vehicle creation: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    
    def handle_vehicle_updated(self, event: VehicleEventMessage):
        """Handle vehicle update event"""
        try:
            db = SessionLocal()
            
            vehicle = db.query(Vehicle).filter(Vehicle.id == event.vehicle_id).first()
            if not vehicle:
                logger.warning(f"Vehicle {event.vehicle_id} not found for update")
                return
            
            # Update vehicle with new data
            update_data = event.data.get('changes', {})
            for field, value in update_data.items():
                if hasattr(vehicle, field):
                    setattr(vehicle, field, value)
                vehicle.updated_at = datetime.now(timezone.utc)
            db.commit()
            
            # Log activity synchronously
            try:
                import threading
                def log_async():
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(log_vehicle_activity(
                            vehicle_id=event.vehicle_id,
                            activity_type="vehicle_updated_from_event",
                            description="Vehicle record updated from management service",
                            details={"changes": update_data, "source": event.source}
                        ))
                    finally:
                        loop.close()
                
                threading.Thread(target=log_async, daemon=True).start()
            except Exception as log_error:
                logger.warning(f"Failed to log vehicle update activity: {log_error}")
            
            logger.info(f"Vehicle {event.vehicle_id} updated successfully")
            
        except Exception as e:
            logger.error(f"Error handling vehicle update: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    
    def handle_vehicle_deleted(self, event: VehicleEventMessage):
        """Handle vehicle deletion event"""
        try:
            db = SessionLocal()
            
            vehicle = db.query(Vehicle).filter(Vehicle.id == event.vehicle_id).first()
            if not vehicle:
                logger.warning(f"Vehicle {event.vehicle_id} not found for deletion")
                return
              # Soft delete - mark as inactive instead of hard delete
            vehicle.is_active = False
            vehicle.updated_at = datetime.now(timezone.utc)
            db.commit()
            
            # Log activity synchronously
            try:
                import threading
                def log_async():
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(log_vehicle_activity(
                            vehicle_id=event.vehicle_id,
                            activity_type="vehicle_deleted_from_event",
                            description="Vehicle marked as inactive from management service",
                            details={"source": event.source}
                        ))
                    finally:
                        loop.close()
                
                threading.Thread(target=log_async, daemon=True).start()
            except Exception as log_error:
                logger.warning(f"Failed to log vehicle deletion activity: {log_error}")
            
            logger.info(f"Vehicle {event.vehicle_id} marked as inactive")
            
        except Exception as e:
            logger.error(f"Error handling vehicle deletion: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    def handle_assignment_created(self, event: VehicleEventMessage):
        """Handle vehicle assignment creation"""
        try:
            # Log the assignment activity synchronously
            try:
                import threading
                def log_async():
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(log_vehicle_activity(
                            vehicle_id=event.vehicle_id,
                            activity_type="assignment_created",
                            description=f"Vehicle assigned to user {event.data.get('user_id')}",
                            details=event.data,
                            user_id=event.data.get('user_id')
                        ))
                    finally:
                        loop.close()
                
                threading.Thread(target=log_async, daemon=True).start()
            except Exception as log_error:
                logger.warning(f"Failed to log assignment creation activity: {log_error}")
            
            logger.info(f"Assignment created for vehicle {event.vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling assignment creation: {e}")
    def handle_assignment_updated(self, event: VehicleEventMessage):
        """Handle vehicle assignment update"""
        try:
            # Log the assignment update synchronously
            try:
                import threading
                def log_async():
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(log_vehicle_activity(
                            vehicle_id=event.vehicle_id,
                            activity_type="assignment_updated",
                            description="Vehicle assignment updated",
                            details=event.data
                        ))
                    finally:
                        loop.close()
                
                threading.Thread(target=log_async, daemon=True).start()
            except Exception as log_error:
                logger.warning(f"Failed to log assignment update activity: {log_error}")
            
            logger.info(f"Assignment updated for vehicle {event.vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling assignment update: {e}")
    
    def handle_usage_recorded(self, event: VehicleEventMessage):
        """Handle vehicle usage recording"""
        try:
            db = SessionLocal()
            
            # Update vehicle mileage if provided
            if 'mileage_delta' in event.data and event.data['mileage_delta']:
                vehicle = db.query(Vehicle).filter(Vehicle.id == event.vehicle_id).first()
                if vehicle:
                    vehicle.current_mileage = (vehicle.current_mileage or 0) + event.data['mileage_delta']
                    vehicle.updated_at = datetime.now(timezone.utc)
                    db.commit()
              # Log the usage activity synchronously
            try:
                import threading
                def log_async():
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(log_vehicle_activity(
                            vehicle_id=event.vehicle_id,
                            activity_type="usage_recorded",
                            description="Vehicle usage recorded",
                            details=event.data,
                            user_id=event.data.get('user_id')
                        ))
                    finally:
                        loop.close()
                
                threading.Thread(target=log_async, daemon=True).start()
            except Exception as log_error:
                logger.warning(f"Failed to log usage activity: {log_error}")
            
            logger.info(f"Usage recorded for vehicle {event.vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling usage recording: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    
    def handle_status_updated(self, event: VehicleEventMessage):
        """Handle vehicle status update"""
        try:
            db = SessionLocal()
            
            # Update vehicle mileage if provided in status
            if 'mileage' in event.data:
                vehicle = db.query(Vehicle).filter(Vehicle.id == event.vehicle_id).first()
                if vehicle and event.data['mileage']:
                    vehicle.current_mileage = event.data['mileage']
                    vehicle.updated_at = datetime.now(timezone.utc)
                    db.commit()
              # Log the status update synchronously
            try:
                import threading
                def log_async():
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(log_vehicle_activity(
                            vehicle_id=event.vehicle_id,
                            activity_type="status_updated",
                            description=f"Status: {event.data.get('status')}",
                            details=event.data
                        ))
                    finally:
                        loop.close()
                
                threading.Thread(target=log_async, daemon=True).start()
            except Exception as log_error:
                logger.warning(f"Failed to log status update activity: {log_error}")
            
            logger.info(f"Status updated for vehicle {event.vehicle_id}")
            
        except Exception as e:
            logger.error(f"Error handling status update: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    def handle_maintenance_due(self, event: VehicleEventMessage):
        """Handle maintenance due notification"""
        try:
            # Log the maintenance due activity synchronously
            try:
                import threading
                def log_async():
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(log_vehicle_activity(
                            vehicle_id=event.vehicle_id,
                            activity_type="maintenance_due",
                            description="Maintenance is due for this vehicle",
                            details=event.data
                        ))
                    finally:
                        loop.close()
                
                threading.Thread(target=log_async, daemon=True).start()
            except Exception as log_error:
                logger.warning(f"Failed to log maintenance due activity: {log_error}")
            
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
        credentials = pika.PlainCredentials('guest', 'guest')
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
