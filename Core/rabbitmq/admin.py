import aio_pika
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

RABBITMQ_URL = "amqp://guest:guest@rabbitmq/"

async def wait_for_rabbitmq(max_retries: int = 30, delay: int = 2):
    for attempt in range(max_retries):
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            await connection.close()
            logger.info("RabbitMQ connection successful")
            break
        except Exception as e:
            logger.warning(f"Waiting for RabbitMQ... (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error("Failed to connect to RabbitMQ after all retries")
                raise

async def broadcast_topics():
    logger.info("wait for rabbit")
    print("wait for rabbit")
    await wait_for_rabbitmq()
    logger.info("rabbit connec")
    try:
        logger.info("try :)")
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
                logger.info(f"Broadcasted topics to fanout exchange: {topics}")
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error broadcasting topics: {str(e)}")
                await asyncio.sleep(5)
                
    except Exception as e:
        logger.info ("not work :(")
        logger.error(f"Error in broadcast_topics: {str(e)}")
        raise