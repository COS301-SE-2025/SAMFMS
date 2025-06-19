from fastapi import FastAPI
import redis
import pika
import logging
import asyncio
import json
import aio_pika

from rabbitmq.consumer import consume_messages_Direct, consume_messages_FanOut
from rabbitmq.admin import create_exchange
from rabbitmq.producer import publish_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GPS Data Service", version="1.0.0")

# Initialize Redis connection
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Initialize RabbitMQ connection
def get_rabbitmq_connection():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbitmq', 
                                    credentials=pika.PlainCredentials('guest', 'guest'))
        )
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        return None

@app.on_event("startup")
async def startup_event():
    logger.info("GPS Data Service starting up...")
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
    
    # Test RabbitMQ connection
    connection = get_rabbitmq_connection()
    if connection:
        logger.info("RabbitMQ connection successful")
        connection.close()
    
    # # Start the RabbitMQ consumer for db
    asyncio.create_task(consume_messages_Direct("gps_db_requests",handle_direct_request))

@app.get("/")
def read_root():
    return {"message": "Hello from GPS Data Service", "service": "gps_data"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "gps_data"}


#############################################################
# Herrie code for message queue
async def handle_direct_request(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        logger.info(f"Received message: {data}")
#############################################################
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
