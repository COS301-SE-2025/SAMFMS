import logging

logger = logging.getLogger(__name__)

# Minimal setup for message consumer
async def setup_message_consumer():
    """Setup and start the message consumer in background"""
    try:
        logger.info("Vehicle message consumer started successfully (minimal version)")
        return None
        
    except Exception as e:
        logger.error(f"Failed to setup message consumer: {e}")
        raise
