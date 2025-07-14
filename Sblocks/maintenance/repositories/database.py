"""
Database configuration and connection management for Maintenance Service
"""

import logging
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.db_name = os.getenv("MONGODB_DATABASE", "samfms")
        self.connection_string = os.getenv(
            "MONGODB_URL", 
            "mongodb://samfms_mongo_user:MongoPass2025!@mongodb:27017/samfms?authSource=admin"
        )
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.database = self.client[self.db_name]
            
            # Test the connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB database: {self.db_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
            
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
            
    async def get_collection(self, collection_name: str):
        """Get a collection from the database"""
        if self.database is None:
            await self.connect()
        return self.database[collection_name]
        
    async def create_indexes(self):
        """Create database indexes for maintenance collections"""
        try:
            # Maintenance records indexes
            maintenance_collection = await self.get_collection("maintenance_records")
            await maintenance_collection.create_index("vehicle_id")
            await maintenance_collection.create_index("scheduled_date")
            await maintenance_collection.create_index("status")
            await maintenance_collection.create_index("maintenance_type")
            await maintenance_collection.create_index([("vehicle_id", 1), ("scheduled_date", 1)])
            
            # Maintenance schedules indexes
            schedules_collection = await self.get_collection("maintenance_schedules")
            await schedules_collection.create_index("vehicle_id")
            await schedules_collection.create_index("vehicle_type")
            await schedules_collection.create_index("is_active")
            
            # License records indexes
            licenses_collection = await self.get_collection("license_records")
            await licenses_collection.create_index("entity_id")
            await licenses_collection.create_index("entity_type")
            await licenses_collection.create_index("license_type")
            await licenses_collection.create_index("expiry_date")
            await licenses_collection.create_index("is_active")
            await licenses_collection.create_index([("entity_id", 1), ("license_type", 1)])
            
            # Vendors indexes
            vendors_collection = await self.get_collection("maintenance_vendors")
            await vendors_collection.create_index("name")
            await vendors_collection.create_index("is_active")
            await vendors_collection.create_index("is_preferred")
            
            # Notifications indexes
            notifications_collection = await self.get_collection("maintenance_notifications")
            await notifications_collection.create_index("vehicle_id")
            await notifications_collection.create_index("is_sent")
            await notifications_collection.create_index("scheduled_send_time")
            await notifications_collection.create_index("recipient_user_ids")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")
            raise


# Global database manager instance
db_manager = DatabaseManager()
