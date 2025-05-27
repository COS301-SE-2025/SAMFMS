from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import asyncio
import logging
from routes import user
from routes import auth
from rabbitmq import producer, consumer, admin
from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(user.router)
app.include_router(auth.router)






@app.on_event("startup")
async def startup_event():
    await admin.broadcast_topics()
    async def safe_consume():
        try:
            await consumer.consume_messages("user_events")
        except Exception as e:
            logger.error(f"Error in consumer: {e}")

    asyncio.create_task(safe_consume())


@app.post("/send/")
async def send_message(data: dict):
    try:
        await producer.publish_message("user_events", data)
        return {"status": "message sent"}
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send message")


#await producer.publish_message("user.created", {"id": 1, "name": "Alice"})




#####################################################################################################################
client = AsyncIOMotorClient("mongodb://host.docker.internal:27017")
db = client.mcore
users_collection = db.users




if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    