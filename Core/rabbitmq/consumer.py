import aio_pika
import asyncio
import json
import admin

async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        print("Message Received:", data)

async def consume_messages(queue_name: str):
    connection = await aio_pika.connect_robust(admin.RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue(queue_name, durable=True)
    await queue.consume(handle_message)