import uuid
import pika
import json
import asyncio
from typing import Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)

class AsyncRPCClient:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.futures: Dict[str, asyncio.Future] = {}

        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER", "samfms_rabbit"),
            os.getenv("RABBITMQ_PASSWORD", "samfms_rabbit123")
        )
        parameters = pika.ConnectionParameters(
            host='rabbitmq',
            credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        # Declare a temporary reply queue
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self._on_response,
            auto_ack=True
        )

    def _on_response(self, ch, method, props, body):
        correlation_id = props.correlation_id
        if correlation_id in self.futures:
            future = self.futures.pop(correlation_id)
            self.loop.call_soon_threadsafe(future.set_result, json.loads(body))

    def send_request(self, exchange: str, routing_key: str, message: Dict[str, Any]) -> asyncio.Future:
        correlation_id = str(uuid.uuid4())
        future = self.loop.create_future()
        self.futures[correlation_id] = future

        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=correlation_id,
                delivery_mode=2,
                content_type='application/json'
            ),
            body=json.dumps(message)
        )

        return future

    def start(self):
        # Run the consumer in a separate thread
        import threading
        def run():
            while True:
                try:
                    self.connection.process_data_events(time_limit=1)
                except Exception as e:
                    logger.error(f"Error in RPC client loop: {e}")
        threading.Thread(target=run, daemon=True).start()

    def close(self):
        self.connection.close()


class AsyncRPCServer:
    def __init__(self, queue_name: str, exchange: str, routing_key: str, handler: Callable):
        self.queue_name = queue_name
        self.exchange = exchange
        self.routing_key = routing_key
        self.handler = handler

        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER", "samfms_rabbit"),
            os.getenv("RABBITMQ_PASSWORD", "samfms_rabbit123")
        )
        parameters = pika.ConnectionParameters(
            host='rabbitmq',
            credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=routing_key)

    def _on_request(self, ch, method, props, body):
        try:
            request_data = json.loads(body)
            logger.info(f"Received request on {self.queue_name}: {request_data}")
            response = self.handler(request_data)

            ch.basic_publish(
                exchange='',
                routing_key=props.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=props.correlation_id,
                    delivery_mode=2,
                    content_type='application/json'
                ),
                body=json.dumps(response)
            )
        except Exception as e:
            logger.error(f"Failed to process request: {e}")
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def start(self):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self._on_request)
        logger.info(f"RPC Server started for queue: {self.queue_name}")
        self.channel.start_consuming()
