import aio_pika
import asyncio
import json
import logging
from typing import Callable, Dict, Any
from . import admin
from database import db

logger = logging.getLogger(__name__)

async def handle_message(message: aio_pika.IncomingMessage):
    """Default message handler"""
    async with message.process():
        data = json.loads(message.body.decode())
        
        # Check if this is a service response (has correlation_id)
        if data.get('correlation_id'):
            # Handle service block responses
            await handle_service_response(data)
        elif data.get('type') == 'service_status':
            if data.get('service') == 'security' and data.get('status') == 'up':
                logger.info(f"Security Sblock is up and running - Message received at {data.get('timestamp')}")
            else:
                logger.info(f"Message Received: {data}")
        elif data.get('type') == 'service_presence':
            db.get_collection("service_presence").insert_one({"service":data.get('service')})
        elif data.get('type') == 'service_response':
            # Handle service block responses (legacy format)
            await handle_service_response(data)
        else:
            logger.info(f"Message Received: {data}")

async def handle_service_response(data: Dict[str, Any]):
    """Handle responses from service blocks"""
    try:
        # Import here to avoid circular imports
        from routes.service_routing import handle_service_response
        await handle_service_response(data)
    except Exception as e:
        logger.error(f"Error handling service response: {e}")

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

async def consume_messages(queue_name: str = "core.responses"):
    """Enhanced message consumer for service routing responses"""
    await wait_for_rabbitmq()
    
    try:
        connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
        channel = await connection.channel()
        
        # Declare response exchange and queue for Core service
        response_exchange = await channel.declare_exchange("service_responses", aio_pika.ExchangeType.DIRECT, durable=True)
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.bind(response_exchange, routing_key="core.responses")
        
        await queue.consume(handle_message)
        logger.info(f"Started consuming service responses from queue: {queue_name}")
        
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

async def consume_messages_Direct(queue_name: str,exchange_name: str, handler):
    await wait_for_rabbitmq()
    
    try:
        connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
        channel = await connection.channel()
        # Declare the exchange
        exchange = await channel.declare_exchange(exchange_name,aio_pika.ExchangeType.DIRECT, durable=True)
        # Declare the queue
        queue = await channel.declare_queue(queue_name, durable=True)
        # Bind the queue and exchange with the routing key
        await queue.bind(exchange, routing_key=queue_name)
        # Pass the message to the handler
        await queue.consume(handler)
        logger.info(f"Started consuming messages from queue: {queue_name}")
        
        try:
            await asyncio.Future()
        finally:
            await connection.close()
    except Exception as e:
        logger.error(f"Error in consume_messages: {str(e)}")
        raise

async def consume_single_message(queue_name: str,exchange_name: str, message_handler: Callable):
    logger.info("Started single message consumption. Queue name: {queue_name}. Exchange name: {exchange_name}")
    from . import admin
    await wait_for_rabbitmq()
    connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
    channel = await connection.channel()

    # declare exchange
    exchange = await channel.declare_exchange(exchange_name,aio_pika.ExchangeType.DIRECT, durable=True)
    queue = await channel.declare_queue(queue_name, durable=True)

    #Bind queue and exchange
    await queue.bind(exchange, routing_key=queue_name)

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

async def consume_messages_Direct_GEOFENCES(queue_name: str, exchange_name: str, handler):
    await wait_for_rabbitmq()
    
    try:
        connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.DIRECT, durable=True)
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange, routing_key=queue_name)
        await queue.consume(handler)
        logger.info(f"Started consuming messages from queue: {queue_name}")
        # DO NOT AWAIT A FUTURE HERE
    except Exception as e:
        logger.error(f"Error in consume_messages: {str(e)}")
        raise