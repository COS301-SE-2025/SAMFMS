from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from routes import user
from routes import auth
from rabbitmq import producer, consumer
from rabbitmq import admin
from rabbitmq import producer, consumer


from database import db

app = FastAPI()

app.include_router(user.router)
app.include_router(auth.router)

admin.broadcast_topics()


@app.lifespan("startup")
async def startup_event():
    import asyncio
    asyncio.create_task(consumer.consume_messages("user_events"))

@app.post("/send/")
async def send_message(data: dict):
    await producer.publish_message("user_events", data)
    return {"status": "message sent"}


#await producer.publish_message("user.created", {"id": 1, "name": "Alice"})




#####################################################################################################################
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.mcore
users_collection = db.users

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)