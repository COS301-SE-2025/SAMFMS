"""
Enhanced Database connection and management for Maintenance Service
Includes connection pooling, retry logic, and proper error handling
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
from pymongo import IndexModel, ASCENDING, DESCENDING

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Enhanced database manager with connection pooling and retry logic"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.db_name = os.getenv("DATABASE_NAME", "samfms_maintenance")
        self.connection_string = os.getenv(
            "MONGODB_URL", 
            "mongodb://samfms_admin:SafeMongoPass2025!SecureDB@SAMFMS@mongodb:27017"
        )
        
        # Connection pool settings
        self.max_pool_size = int(os.getenv("MONGODB_MAX_POOL_SIZE", "50"))
        self.min_pool_size = int(os.getenv("MONGODB_MIN_POOL_SIZE", "5"))
        self.server_selection_timeout = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT", "5000"))
        self.connect_timeout = int(os.getenv("MONGODB_CONNECT_TIMEOUT", "10000"))
        
        # Retry settings
        self.max_retries = int(os.getenv("MONGODB_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("MONGODB_RETRY_DELAY", "1.0"))
        
        # Health check
        self.last_health_check = None
        self.health_check_interval = timedelta(minutes=5)
        
    async def connect(self):
        """Connect to MongoDB with retry logic"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempting to connect to MongoDB (attempt {attempt + 1}/{self.max_retries})")
                
                self.client = AsyncIOMotorClient(
                    self.connection_string,
                    maxPoolSize=self.max_pool_size,
                    minPoolSize=self.min_pool_size,
                    serverSelectionTimeoutMS=self.server_selection_timeout,
                    connectTimeoutMS=self.connect_timeout,
                    retryWrites=True,
                    retryReads=True,
                    maxIdleTimeMS=30000,  # 30 seconds
                    waitQueueTimeoutMS=5000,  # 5 seconds
                )
                
                # Test the connection
                await self.client.admin.command('ping')
                
                self.database = self.client[self.db_name]
                logger.info(f"Successfully connected to MongoDB database: {self.db_name}")
                return
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("All connection attempts failed")
                    raise ConnectionError(f"Failed to connect to MongoDB after {self.max_retries} attempts")
            
    async def disconnect(self):
        """Safely disconnect from MongoDB"""
        if self.client:
            try:
                logger.info("Closing MongoDB connection...")
                self.client.close()
                await asyncio.sleep(0.1)
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {e}")
            finally:
                self.client = None
                self.database = None
                
    async def ensure_connection(self):
        """Ensure database connection is healthy"""
        try:
            now = datetime.utcnow()
            if (self.last_health_check is None or 
                now - self.last_health_check > self.health_check_interval):
                
                if self.database is not None:
                    await self.database.command('ping')
                    self.last_health_check = now
                else:
                    raise ConnectionFailure("No database connection")
                    
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            await self.disconnect()
            await self.connect()
            
    async def get_collection(self, collection_name: str):
        """Get a collection with connection validation"""
        await self.ensure_connection()
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
