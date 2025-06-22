import aio_pika
import asyncio
import json
import logging
from typing import Callable, Dict, Any
from . import admin

logger = logging.getLogger(__name__)

async def handle_message(message: aio_pika.IncomingMessage):
    """Default message handler"""
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

async def consume_messages_with_handler(queue_name: str, message_handler: Callable[[Dict[str, Any]], None]):
    """Enhanced message consumer with custom handler"""
    await wait_for_rabbitmq()
    
    async def handle_with_custom_handler(message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                await message_handler(data)
            except Exception as e:
                logger.error(f"Error in custom message handler: {e}")
    
    try:
        connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        
        await queue.consume(handle_with_custom_handler)
        logger.info(f"Started consuming messages from queue {queue_name} with custom handler")
        
        try:
            await asyncio.Future()
        finally:
            await connection.close()
    except Exception as e:
        logger.error(f"Error in consume_messages_with_handler: {str(e)}")
        raise

async def consume_single_message(queue_name: str, message_handler: Callable):
    """Consume a single message from the queue and call the handler, then stop."""
    from . import admin
    await wait_for_rabbitmq()
    connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue(queue_name, durable=True)

    # Use an event to stop after one message
    stop_event = asyncio.Event()

    async def on_message(message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                await message_handler(message)
            except Exception as e:
                logger.error(f"Error in single message handler: {e}")
            finally:
                stop_event.set()  # Signal to stop after one message

    await queue.consume(on_message)
    await stop_event.wait()
    await connection.close()