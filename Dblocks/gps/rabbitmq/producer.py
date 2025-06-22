import aio_pika
import json
import logging
from . import admin

logger = logging.getLogger(__name__)

async def publish_message(
    exchange_name: str,
    exchange_type: aio_pika.ExchangeType,
    message: dict,
    routing_key: str = ""
):
    """
    Publishes a message to a specified exchange.

    Args:
        exchange_name (str): The name of the exchange to publish to.
        exchange_type (aio_pika.ExchangeType): eg. aio_pika.ExchangeType.FANOUT
        message (dict): The message to publish.
        routing_key (str): The routing key (ignored for fanout exchanges).
    """
    try:
        connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
        channel = await connection.channel()

        exchange = await channel.declare_exchange(exchange_name, exchange_type, durable=True)

        await exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=routing_key
        )

        logger.info(f"Published message to {exchange_type} exchange '{exchange_name}': {message}")
    except Exception as e:
        logger.error(f"Failed to publish message to exchange '{exchange_name}': {str(e)}")

        raise
    finally:
        await connection.close()