import aio_pika
import json
import admin

async def publish_message(event_type: str, message: dict):
    connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
    channel = await connection.channel()

    exchange = await channel.declare_exchange("fanout_exchange", aio_pika.ExchangeType.FANOUT)


    queue = await channel.declare_queue(event_type, durable=True)
    await channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(message).encode()),
        routing_key=""
    )

    print(f"Message published message to fanout exchange: {event_type} -> {message}")
    await connection.close()
