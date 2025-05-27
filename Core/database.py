from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://host.docker.internal:27017"
client = AsyncIOMotorClient(MONGO_URI)

db = client.mcore
