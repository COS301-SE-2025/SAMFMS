import os
from fastapi import FastAPI
import redis
import pika
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Micro Frontend Service", version="1.0.0")

# Initialize Redis connection
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Initialize RabbitMQ connection
def get_rabbitmq_connection():
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='rabbitmq', 
                                    credentials=pika.PlainCredentials(
                                        os.getenv('RABBITMQ_USER', 'samfms_rabbit'),
                                        os.getenv('RABBITMQ_PASSWORD', 'samfms_rabbit123')
                                    ))
        )
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        return None

@app.on_event("startup")
async def startup_event():
    logger.info("Micro Frontend Service starting up...")
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

@app.get("/")
def read_root():
    return {"message": "Hello from Micro Frontend Service", "service": "micro_frontend"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "micro_frontend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
