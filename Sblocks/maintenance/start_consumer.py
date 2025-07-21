"""
Simple consumer startup script for maintenance service
This will be imported to start the consumer immediately
"""

import asyncio
import logging
from services.request_consumer import maintenance_service_request_consumer

logger = logging.getLogger(__name__)

async def start_maintenance_consumer():
    """Start the maintenance service consumer"""
    try:
        logger.info("🚀 Starting maintenance service consumer...")
        
        # Connect to RabbitMQ
        await maintenance_service_request_consumer.connect()
        logger.info("✅ RabbitMQ connected")
        
        # Start consuming in background
        consumer_task = asyncio.create_task(maintenance_service_request_consumer.start_consuming())
        logger.info("✅ RabbitMQ consumer task started")
        
        return consumer_task
        
    except Exception as e:
        logger.error(f"❌ Failed to start maintenance consumer: {e}")
        raise

# Auto-start the consumer when this module is imported
def init_consumer():
    """Initialize consumer in background"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, schedule the task
            asyncio.create_task(start_maintenance_consumer())
        else:
            # If no loop is running, start one
            asyncio.run(start_maintenance_consumer())
    except Exception as e:
        logger.error(f"Error initializing consumer: {e}")

# Start consumer when module is imported
logger.info("Initializing maintenance consumer...")
# We'll call this manually from main.py instead of auto-importing
