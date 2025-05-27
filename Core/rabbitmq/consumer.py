import aio_pika
import asyncio
import json
import logging
from . import admin

logger = logging.getLogger(__name__)

async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        print("📨 Received:", data)

async def wait_for_rabbitmq(max_retries: int = 30, delay: int = 2):
    """Wait for RabbitMQ to be available with retry logic"""
    for attempt in range(max_retries):
        try:
            connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
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

async def consume_messages(queue_name: str):
    # Wait for RabbitMQ to be ready
    await wait_for_rabbitmq()
    
    try:
        connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.consume(handle_message)
        logger.info(f"🎯 Started consuming messages from queue: {queue_name}")
        
        # Keep the connection alive
        try:
            await asyncio.Future()  # Run forever
        finally:
            await connection.close()
    except Exception as e:
        logger.error(f"❌ Error in consume_messages: {str(e)}")
        raise