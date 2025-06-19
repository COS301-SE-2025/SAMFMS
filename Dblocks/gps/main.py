from fastapi import FastAPI
import redis
import pika
import logging
import asyncio

from rabbitmq.consumer import consume_messages
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
    asyncio.create_task(consume_messages("db_requests"))

@app.get("/")
def read_root():
    return {"message": "Hello from GPS Data Service", "service": "gps_data"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "gps_data"}


# message queue code
def get_latest_gps(vehicle_id):
    # Replace with real DB logic
    return {"vehicle_id": vehicle_id, "lat": -25.0, "lon": 28.0, "timestamp": 1234567890}

def handle_db_request(message):
    logger.info("Message received: " + message)
    vehicle_id = message["vehicle_id"]
    reply_to = message["reply_to"]
    gps_data = get_latest_gps(vehicle_id)
    publish_message(reply_to, gps_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
