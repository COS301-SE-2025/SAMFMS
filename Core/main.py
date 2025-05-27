from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import asyncio
import logging
from routes import user
from routes import auth
from rabbitmq import producer, consumer
from rabbitmq import admin
from database import db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(user.router)
app.include_router(auth.router)

async def start_rabbitmq_consumer():
    """Start RabbitMQ consumer with error handling"""
    try:
        await consumer.consume_messages("user_events")
    except Exception as e:
        logger.error(f"❌ Failed to start RabbitMQ consumer: {str(e)}")
        # Don't crash the entire application, just log the error

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting application...")
    # Start RabbitMQ consumer in background task
    asyncio.create_task(start_rabbitmq_consumer())
    logger.info("✅ Application startup complete")

@app.post("/send/")
async def send_message(data: dict):
    try:
        await producer.publish_message("user_events", data)
        return {"status": "message sent"}
    except Exception as e:
        logger.error(f"❌ Failed to send message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send message")


#await producer.publish_message("user.created", {"id": 1, "name": "Alice"})




#####################################################################################################################
client = AsyncIOMotorClient("mongodb://host.docker.internal:27017")
db = client.mcore
users_collection = db.users

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)