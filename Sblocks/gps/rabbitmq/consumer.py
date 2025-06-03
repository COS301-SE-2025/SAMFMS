import aio_pika
import asyncio
import json
import logging
from . import admin

logger = logging.getLogger(__name__)

async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        
        if data.get('type') == 'service_status':
            if data.get('service') == 'security' and data.get('status') == 'up':
                logger.info(f"Security Sblock is up and running - Message received at {data.get('timestamp')}")
            else:
                logger.info(f"Message Received: {data}")
        else:
            logger.info(f"Message Received: {data}")

async def wait_for_rabbitmq(max_retries: int = 30, delay: int = 2):
    """Wait for RabbitMQ to be available with retry logic"""
    for attempt in range(max_retries):
        try:
            connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
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
    return False

async def consume_messages(queue_name: str):
    await wait_for_rabbitmq()
    
    try:
        connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        
        await queue.consume(handle_message)
        logger.info(f"Started consuming messages from queue: {queue_name}")
        
        try:
            await asyncio.Future()
        finally:
            await connection.close()
    except Exception as e:
        logger.error(f"Error in consume_messages: {str(e)}")
        raise