"""
Manual startup module for maintenance service
"""
import asyncio
import logging
from datetime import datetime, timezone

from repositories.database import db_manager
from services.request_consumer import maintenance_service_request_consumer
from services.background_jobs import background_jobs

logger = logging.getLogger(__name__)

async def initialize_services():
    """Initialize all services manually"""
    logger.info("🚀 Maintenance Service Manual Initialization...")
    
    try:
        # Initialize database
        await db_manager.connect()
        await db_manager.create_indexes()
        logger.info("✅ Database connected and indexes created")

        # Connect RabbitMQ consumer
        await maintenance_service_request_consumer.connect()
        logger.info("✅ RabbitMQ connected")
        
        # Start consuming in the background - DO NOT await here
        logger.info("🔄 Starting RabbitMQ consumer task...")
        consumer_task = asyncio.create_task(maintenance_service_request_consumer.start_consuming())
        logger.info("✅ RabbitMQ consumer task started")
        
        # Give a moment for the consumer to start
        await asyncio.sleep(2)
        logger.info("🔄 Consumer startup grace period completed")

        # Start background jobs
        await background_jobs.start_background_jobs()
        logger.info("✅ Background jobs started")

        logger.info("🎉 Maintenance Service manual initialization completed")
        return consumer_task
        
    except Exception as e:
        logger.error(f"Failed to initialize Maintenance Service: {e}")
        raise
