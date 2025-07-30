"""
Startup service for Core application
Handles initialization of services and dependencies
"""

import asyncio
import logging
import os
from typing import List

from motor.motor_asyncio import AsyncIOMotorClient
import aio_pika

from rabbitmq.admin import create_exchange, wait_for_rabbitmq
from rabbitmq.producer import publish_message
from rabbitmq.consumer import consume_messages, consume_messages_Direct, consume_messages_Direct_GEOFENCES
from services.request_router import request_router
from services.request_deduplicator import request_deduplicator
from websockets.vehicle_tracking import vehicle_websocket

logger = logging.getLogger(__name__)

class StartupService:
    """Handles application startup and shutdown procedures"""
    
    def __init__(self):
        self.consumer_tasks: List[asyncio.Task] = []
        self.startup_delay = int(os.getenv("SERVICE_STARTUP_DELAY", "10"))
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://mongodb_core:27017")
        self.max_retries = 10
    
    async def startup(self):
        """Execute startup procedures"""
        logger.info("🚀 Core service starting up...")
        
        # Add startup delay to prevent race conditions
        logger.info(f"⏱️ Waiting {self.startup_delay} seconds before initialization...")
        await asyncio.sleep(self.startup_delay)
        
        # Initialize services in order
        await self._test_mongodb_connection()
        await self._initialize_plugin_manager()
        await self._initialize_rabbitmq()
        await self._initialize_request_deduplicator()
        await self._initialize_request_router()
        
        logger.info("✅ Core service startup completed")
    
    async def shutdown(self):
        """Execute shutdown procedures"""
        logger.info("🛑 Core service shutting down...")
        
        # Stop request deduplicator
        await request_deduplicator.stop()
        
        # Properly shutdown consumer tasks
        for task in self.consumer_tasks:
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    logger.info("Consumer task cancelled/timed out during shutdown")
                except Exception as e:
                    logger.warning(f"Error during task shutdown: {e}")
        
        logger.info("✅ Core service shutdown completed")
    
    async def _test_mongodb_connection(self):
        """Test MongoDB connection with retry logic"""
        try:
            for attempt in range(self.max_retries):
                try:
                    client = AsyncIOMotorClient(self.mongodb_url)
                    await client.admin.command('ping')
                    logger.info("✅ Successfully connected to MongoDB")
                    client.close()
                    break
                except Exception as e:
                    logger.warning(f"⚠️ MongoDB connection attempt {attempt + 1}/{self.max_retries} failed: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2)
                    else:
                        logger.error(f"❌ Failed to connect to MongoDB after {self.max_retries} attempts")
                        raise
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            # Don't exit - let the service start and retry later
    
    async def _initialize_plugin_manager(self):
        """Initialize plugin manager"""
        try:
            from services.plugin_service import plugin_manager
            await plugin_manager.initialize_plugins()
            logger.info("✅ Plugin manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize plugin manager: {e}")
    
    async def _initialize_rabbitmq(self):
        """Initialize RabbitMQ connections and consumers"""
        try:
            await wait_for_rabbitmq()
            
            # Create consumer tasks with proper error handling
            consumer_task = asyncio.create_task(consume_messages("service_status"))
            self.consumer_tasks.append(consumer_task)
            
            asyncio.create_task(consume_messages("service_presence"))
            
            # Consumer for live vehicle locations
            asyncio.create_task(consume_messages_Direct(
                "core_responses", 
                "core_responses", 
                vehicle_websocket.handle_vehicle_response
            ))
            
            asyncio.create_task(consume_messages_Direct_GEOFENCES(
                "core_responses_geofence",
                "core_responses_geofence",
                vehicle_websocket.handle_geofence_response
            ))
            
            await create_exchange("general", aio_pika.ExchangeType.FANOUT)
            await publish_message("general", aio_pika.ExchangeType.FANOUT, {"message": "Core service started"})
            
            logger.info("✅ RabbitMQ initialized successfully")
            logger.info("✅ Started consuming messages from service_status queue")
            logger.info("✅ Started consuming messages from service_presence queue")
        except Exception as e:
            logger.error(f"❌ Failed to initialize RabbitMQ: {e}")
            # Continue startup - messaging will retry
    
    async def _initialize_request_deduplicator(self):
        """Initialize request deduplicator"""
        try:
            await request_deduplicator.start()
            logger.info("✅ Request deduplicator initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize request deduplicator: {e}")
    
    async def _initialize_request_router(self):
        """Initialize request router and response manager"""
        try:
            # Start the response consumer for management/generic responses
            asyncio.create_task(request_router.response_manager.consume_responses())
            logger.info("✅ Started response_manager.consume_responses task")
            
            # Initialize request router if it has an initialize method
            if hasattr(request_router, 'initialize'):
                await request_router.initialize()
                logger.info("✅ Request router initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize request router: {e}")

# Global startup service instance
startup_service = StartupService()
