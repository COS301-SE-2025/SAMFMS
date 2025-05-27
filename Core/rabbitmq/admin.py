import aio_pika
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

RABBITMQ_URL = "amqp://guest:guest@rabbitmq/"

async def wait_for_rabbitmq(max_retries: int = 30, delay: int = 2):
    """Wait for RabbitMQ to be available with retry logic"""
    for attempt in range(max_retries):
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            await connection.close()
            logger.info("✅ RabbitMQ connection successful")
            return True
        except Exception as e:
            logger.warning(f"⏳ Waiting for RabbitMQ... (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error("❌ Failed to connect to RabbitMQ after all retries")
                raise
    return False

async def broadcast_topics():
    # Wait for RabbitMQ to be ready
    await wait_for_rabbitmq()
    
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        exchange = await channel.declare_exchange("fanout_exchange", aio_pika.ExchangeType.FANOUT)
        
        topics = {
            "exchange": "topic_exchange",
            "topics": ["user.created", "user.updated", "order.created", "order.updated"]
        }

        while True:
            try:
                await exchange.publish(
                    aio_pika.Message(body=json.dumps(topics).encode()),
                    routing_key=""  
                )
                logger.info(f"📤 Broadcasted topics to fanout exchange: {topics}")
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"❌ Error broadcasting topics: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
                
    except Exception as e:
        logger.error(f"❌ Error in broadcast_topics: {str(e)}")
        raise


# Note: broadcast_topics() should be called explicitly when needed, not at module import