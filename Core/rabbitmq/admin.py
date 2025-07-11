import aio_pika
import asyncio
import json
import logging
import aiohttp
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)




logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://samfms_rabbit:RabbitPass2025!@rabbitmq:5672/")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME", "samfms_rabbit")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "RabbitPass2025!")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_MANAGEMENT_PORT = os.getenv("RABBITMQ_MANAGEMENT_PORT", "15672")

async def wait_for_rabbitmq(max_retries: int = None, delay: int = None):
    # Use environment variables if provided, otherwise use defaults
    max_retries = max_retries or int(os.getenv("RABBITMQ_CONNECTION_RETRY_ATTEMPTS", "30"))
    delay = delay or int(os.getenv("RABBITMQ_CONNECTION_RETRY_DELAY", "2"))
    
    for attempt in range(max_retries):
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            await connection.close()
            logger.info("RabbitMQ connection successful")
            return True
        except Exception as e:
            logger.warning(f"Waiting for RabbitMQ... (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error("Failed to connect to RabbitMQ after all retries")
                raise
    return False



async def create_exchange(exchange_name: str, exchange_type: aio_pika.ExchangeType):
    connection = None
    try:
        # Wait for RabbitMQ to be available before creating exchange
        await wait_for_rabbitmq()
        
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        
        # Try to declare as durable first
        try:
            exchange = await channel.declare_exchange(exchange_name, exchange_type, durable=True)
            logger.info(f"Exchange '{exchange_name}' created with type '{exchange_type}' (durable=True)")
        except Exception as e:
            if "inequivalent arg" in str(e) and "durable" in str(e):
                # Exchange exists with different durability, declare with passive=True to use existing
                logger.warning(f"Exchange '{exchange_name}' exists with different durability, using existing exchange")
                exchange = await channel.declare_exchange(exchange_name, exchange_type, passive=True)
                logger.info(f"Using existing exchange '{exchange_name}' with type '{exchange_type}'")
            else:
                raise
        
        return exchange
    except Exception as e:
        logger.error(f"Failed to create exchange '{exchange_name}': {str(e)}")
        raise
    finally:
        if connection:
            await connection.close()



async def broadcast_topics():
    logger.info("Waiting for RabbitMQ...")
    await wait_for_rabbitmq()
    logger.info("Connected to RabbitMQ")

    while True:
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
                    logger.info(f"Broadcasted topics to fanout exchange: {topics}")
                    await asyncio.sleep(30)
                except Exception as e:
                    logger.error(f"Error broadcasting topics: {str(e)}")
                    await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error in broadcast_topics: {str(e)}")
            await asyncio.sleep(10)



async def removeSblock(username: str):
    logger.info("Waiting for RabbitMQ...")
    await wait_for_rabbitmq()
    logger.info("Connected to RabbitMQ")

    API_URL = f"http://{RABBITMQ_HOST}:{RABBITMQ_MANAGEMENT_PORT}/api/permissions/%2F/{username}"

    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "configure": "",
                "write": "",
                "read": ""
            }
            async with session.put(API_URL, json=payload, auth=aiohttp.BasicAuth(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)) as response:
                if response.status == 200:
                    logger.info(f"Successfully restricted access for user '{username}'")
                else:
                    logger.error(f"Failed to restrict access for user '{username}'. Status: {response.status}")
                    logger.error(f"Response: {await response.text()}")
        except Exception as e:
            logger.error(f"Error while restricting access for user '{username}': {str(e)}")



async def addSblock(username: str):
    logger.info("Waiting for RabbitMQ...")
    await wait_for_rabbitmq()
    logger.info("Connected to RabbitMQ")

    API_URL = f"http://{RABBITMQ_HOST}:{RABBITMQ_MANAGEMENT_PORT}/api/permissions/%2F/{username}"

    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "configure": ".*",
                "write": ".*",
                "read": ".*"
            }
            async with session.put(API_URL, json=payload, auth=aiohttp.BasicAuth(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)) as response:
                if response.status == 200:
                    logger.info(f"Successfully restored access for user '{username}'")
                else:
                    logger.error(f"Failed to restore access for user '{username}'. Status: {response.status}")
                    logger.error(f"Response: {await response.text()}")
        except Exception as e:
            logger.error(f"Error while restoring access for user '{username}': {str(e)}")
