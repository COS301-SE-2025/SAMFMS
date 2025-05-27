# Database configuration for Core Service
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os

class CoreDatabase:
    client: Optional[AsyncIOMotorClient] = None
    database = None

    @classmethod
    async def connect_to_mongo(cls):
        """Create database connection"""
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        cls.client = AsyncIOMotorClient(mongo_url)
        cls.database = cls.client.mcore
        
        # Test connection
        try:
            await cls.client.admin.command('ping')
            print("Successfully connected to MongoDB")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")

    @classmethod
    async def close_mongo_connection(cls):
        """Close database connection"""
        if cls.client:
            cls.client.close()

    @classmethod
    def get_database(cls):
        """Get database instance"""
        return cls.database

    @classmethod
    def get_collection(cls, collection_name: str):
        """Get specific collection"""
        return cls.database[collection_name]

# Convenience functions for collections
def get_users_collection():
    return CoreDatabase.get_collection("users")

# Initialization and cleanup functions
init_database = CoreDatabase.connect_to_mongo
close_database = CoreDatabase.close_mongo_connection