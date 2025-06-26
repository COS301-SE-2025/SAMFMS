from fastapi import FastAPI
import redis
import pika
import logging
import asyncio
import json
import aio_pika
import os

from rabbitmq.consumer import consume_messages_Direct, consume_messages_FanOut
from rabbitmq.admin import create_exchange
from rabbitmq.producer import publish_message

#DBLock functions
from database import get_gps_location_by_device_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GPS Data Service", version="1.0.0")

# Initialize Redis connection using environment variables
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# Initialize RabbitMQ connection using environment variables
def get_rabbitmq_connection():
    try:
        rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        rabbitmq_username = os.getenv("RABBITMQ_USERNAME", "guest")
        rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "guest")
        
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=rabbitmq_host, 
                credentials=pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
            )
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
# FUnction to handle requests from the GPS SBlock
async def handle_direct_request(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        logger.info(f"Received message: {data}")

        operation = data.get("operation")
        data_type = data.get("type")
        parameters = data.get("parameters")

        if operation == "retrieve":
            device_id = parameters.get("device_id")
            location = await get_gps_location_by_device_id(device_id)
            logger.info(f"Location from DB: {location}")
        elif operation == "ADD":
            device_id = parameters.get("device_id")


        #await respond_GPSBlock("Here is the DBLock response")

# Function to respond to request from GPS SBlock
async def respond_GPSBlock(message: str):
    logger.info("Entered the respond_GPSBlock function")
    await publish_message(
        "gps_responses_Direct",
        aio_pika.ExchangeType.DIRECT,
        {"message": f"Message From GPS DBlock to GPS SBlock test : {message}"},
        routing_key="gps_responses_Direct"
    )
#############################################################
    

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("GPS_DBLOCK_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
