import aio_pika
import asyncio
import json

RABBITMQ_URL = "amqp://guest:guest@localhost/"

async def broadcast_topics():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    exchange = await channel.declare_exchange("fanout_exchange", aio_pika.ExchangeType.FANOUT)

    topics = {
        "exchange": "topic_exchange",
        "topics": ["user.created", "user.updated", "order.created", "order.updated"]
    }

    while True:
        await exchange.publish(
            aio_pika.Message(body=json.dumps(topics).encode()),
            routing_key=""  
        )

        print("📤 Broadcasted topics to fanout exchange:", topics)
        await asyncio.sleep(30)

asyncio.run(broadcast_topics())