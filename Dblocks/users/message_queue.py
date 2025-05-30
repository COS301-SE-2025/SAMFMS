import pika
import json
import asyncio
import logging
import threading
from models import UserCreatedMessage, UserUpdatedMessage, UserDeletedMessage, UserProfile
from database import user_profiles_collection
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageQueueConsumer:
    def __init__(self, host='rabbitmq', username='guest', password='guest'):
        self.host = host
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.consumer_thread = None
        self.should_stop = False
        self._event_loop = None
        
    def connect(self):
        """Establish connection to RabbitMQ with optimized settings"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            connection_params = pika.ConnectionParameters(
                host=self.host,
                credentials=credentials,
                heartbeat=300,  # Reduced heartbeat interval
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=2,
                socket_timeout=10,
                frame_max=131072,
                channel_max=10  # Limit channels for consumers
            )
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            
            # Set QoS to process one message at a time to reduce CPU load
            self.channel.basic_qos(prefetch_count=1, global_qos=False)
            
            # Declare exchanges and queues
            self._setup_exchanges_and_queues()
            
            logger.info("Successfully connected to RabbitMQ consumer with optimized settings")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
      def _setup_exchanges_and_queues(self):
        """Setup RabbitMQ exchanges and queues with optimized settings"""
        # User-related exchanges
        self.channel.exchange_declare(
            exchange='user_events', 
            exchange_type='topic',
            durable=True,
            auto_delete=False,
            arguments={'x-max-length': 1000}
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
        
        # Bind queues to exchanges
        self.channel.queue_bind(
            exchange='user_events',
            queue='user_profile_updates',
            routing_key='user.profile.*'
        )
      def start_consuming(self):
        """Start consuming messages in a separate thread with optimized settings"""
        if not self.connection:
            if not self.connect():
                logger.error("Cannot start consuming: no connection to RabbitMQ")
                return
        
        # Set up consumers with manual acknowledgment
        self.channel.basic_consume(
            queue='user_profile_updates',
            on_message_callback=self._handle_user_profile_message,
            auto_ack=False  # Manual acknowledgment for better reliability
        )
        
        # Start consuming in a separate thread
        self.consumer_thread = threading.Thread(target=self._consume_messages)
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
        logger.info("Started optimized message queue consumer")
    
    def _consume_messages(self):
        """Consume messages from RabbitMQ with optimized polling"""
        try:
            while not self.should_stop:
                try:
                    # Increased time limit to reduce CPU usage
                    self.connection.process_data_events(time_limit=5)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Brief pause to prevent tight loop on errors
                    threading.Event().wait(1)
        except Exception as e:
            logger.error(f"Error in message consumption: {e}")
      def _handle_user_profile_message(self, channel, method, properties, body):
        """Handle user profile messages with synchronous processing"""
        try:
            message_data = json.loads(body)
            routing_key = method.routing_key
            
            # Process synchronously to avoid async/sync context issues
            if routing_key == 'user.profile.created':
                self._sync_handle_user_created(message_data)
            elif routing_key == 'user.profile.updated':
                self._sync_handle_user_updated(message_data)
            elif routing_key == 'user.profile.deleted':
                self._sync_handle_user_deleted(message_data)
            
            # Acknowledge message after successful processing
            channel.basic_ack(delivery_tag=method.delivery_tag)
            logger.debug(f"Successfully processed message with routing key: {routing_key}")
            
        except Exception as e:
            logger.error(f"Error handling user profile message: {e}")
            # Reject message and don't requeue to prevent infinite loops
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def _sync_handle_user_created(self, message_data):
        """Handle user created event synchronously"""
        try:
            import asyncio
            user_message = UserCreatedMessage(**message_data)
            
            # Run async operation in sync context efficiently
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Create user profile document
                profile_data = {
                    "user_id": user_message.user_id,
                    "full_name": user_message.full_name,
                    "phoneNo": user_message.phoneNo,
                    "details": user_message.details,
                    "preferences": user_message.preferences,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                loop.run_until_complete(user_profiles_collection.insert_one(profile_data))
                logger.info(f"Created user profile for user_id: {user_message.user_id}")
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
    
    def _sync_handle_user_updated(self, message_data):
        """Handle user updated event synchronously"""
        try:
            import asyncio
            user_message = UserUpdatedMessage(**message_data)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Update user profile
                update_data = user_message.updates.copy()
                update_data["updated_at"] = datetime.utcnow()
                
                result = loop.run_until_complete(
                    user_profiles_collection.update_one(
                        {"user_id": user_message.user_id},
                        {"$set": update_data}
                    )
                )
                
                if result.matched_count > 0:
                    logger.info(f"Updated user profile for user_id: {user_message.user_id}")
                else:
                    logger.warning(f"No user profile found for user_id: {user_message.user_id}")
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
    
    def _sync_handle_user_deleted(self, message_data):
        """Handle user deleted event synchronously"""
        try:
            import asyncio
            user_message = UserDeletedMessage(**message_data)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Delete user profile
                result = loop.run_until_complete(
                    user_profiles_collection.delete_one(
                        {"user_id": user_message.user_id}
                    )
                )
                
                if result.deleted_count > 0:
                    logger.info(f"Deleted user profile for user_id: {user_message.user_id}")
                else:
                    logger.warning(f"No user profile found for user_id: {user_message.user_id}")
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error deleting user profile: {e}")

    def stop_consuming(self):
        """Stop consuming messages"""
        self.should_stop = True
        if self.consumer_thread:
            self.consumer_thread.join(timeout=5)
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        logger.info("Stopped message queue consumer")


# Global message queue consumer instance
mq_consumer = MessageQueueConsumer()
