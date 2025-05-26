from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
from routes import user


from database import db

app = FastAPI()
app.include_router(user.router)


client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.mcore
users_collection = db.users

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)