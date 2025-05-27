import aio_pika
import json
import logging
from . import admin

logger = logging.getLogger(__name__)

async def publish_message(event_type: str, message: dict):
    try:
        connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
        channel = await connection.channel()

        exchange = await channel.declare_exchange("fanout_exchange", aio_pika.ExchangeType.FANOUT)

        queue = await channel.declare_queue(event_type, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=event_type
        )

        logger.info(f"📤 Published message to queue: {event_type} -> {message}")
        await connection.close()
        
    except Exception as e:
        logger.error(f"❌ Failed to publish message: {str(e)}")
        raise
