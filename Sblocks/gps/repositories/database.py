"""
Database configuration and connection management for GPS service
"""
import motor.motor_asyncio
import asyncio
import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Centralized database connection manager for GPS service"""
    
    def __init__(self):
        self._client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self._db = None
        self.mongodb_url = os.getenv(
            "MONGODB_URL", 
            "mongodb://samfms_admin:SafeMongoPass2025%21SecureDB%40SAMFMS@mongodb:27017"
        )
        self.database_name = os.getenv("DATABASE_NAME", "samfms_gps")
        
    async def connect(self):
        """Establish database connection with optimal settings and error recovery"""
        if self._client is None:
            try:
                # Connection with optimized settings
                self._client = motor.motor_asyncio.AsyncIOMotorClient(
                    self.mongodb_url,
                    maxPoolSize=50,
                    minPoolSize=10,
                    maxIdleTimeMS=30000,
                    waitQueueTimeoutMS=5000,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=20000,
                    retryWrites=True,
                    w="majority"
                )
                
                # Test connection
                await self._client.admin.command('ping')
                self._db = self._client[self.database_name]
                
                # Create indexes with error handling
                try:
                    await self._create_indexes()
                except Exception as index_error:
                    logger.warning(f"Failed to create some indexes: {index_error}")
                
                logger.info(f"Connected to MongoDB: {self.database_name}")
                
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
                
    async def disconnect(self):
        """Safely disconnect from database"""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("Disconnected from MongoDB")
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._client is not None and self._db is not None
    
    @property
    def db(self):
        """Get database instance"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db
    
    async def _create_indexes(self):
        """Create necessary indexes for GPS collections"""
        try:
            # Vehicle locations collection indexes
            locations_collection = self._db.vehicle_locations
            await locations_collection.create_index([
                ("vehicle_id", 1),
                ("timestamp", -1)
            ])
            await locations_collection.create_index([
                ("location", "2dsphere")
            ])
            await locations_collection.create_index([
                ("timestamp", -1)
            ])
            await locations_collection.create_index([
                ("vehicle_id", 1),
                ("created_at", -1)
            ])
            
            # Location history collection indexes
            history_collection = self._db.location_history
            await history_collection.create_index([
                ("vehicle_id", 1),
                ("timestamp", -1)
            ])
            await history_collection.create_index([
                ("location", "2dsphere")
            ])
            await history_collection.create_index([
                ("timestamp", 1)  # For TTL and cleanup
            ])
            
            # Geofences collection indexes
            geofences_collection = self._db.geofences
            await geofences_collection.create_index([
                ("name", 1)
            ])
            await geofences_collection.create_index([
                ("geometry", "2dsphere")
            ])
            await geofences_collection.create_index([
                ("created_by", 1)
            ])
            await geofences_collection.create_index([
                ("is_active", 1)
            ])
            
            # Geofence events collection indexes
            geofence_events_collection = self._db.geofence_events
            await geofence_events_collection.create_index([
                ("vehicle_id", 1),
                ("timestamp", -1)
            ])
            await geofence_events_collection.create_index([
                ("geofence_id", 1),
                ("timestamp", -1)
            ])
            await geofence_events_collection.create_index([
                ("event_type", 1),
                ("timestamp", -1)
            ])
            
            # Places collection indexes
            places_collection = self._db.places
            await places_collection.create_index([
                ("user_id", 1),
                ("name", 1)
            ])
            await places_collection.create_index([
                ("location", "2dsphere")
            ])
            await places_collection.create_index([
                ("created_by", 1)
            ])
            
            # Tracking sessions collection indexes
            tracking_sessions_collection = self._db.tracking_sessions
            await tracking_sessions_collection.create_index([
                ("vehicle_id", 1),
                ("is_active", 1)
            ])
            await tracking_sessions_collection.create_index([
                ("started_at", -1)
            ])
            await tracking_sessions_collection.create_index([
                ("user_id", 1),
                ("started_at", -1)
            ])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Perform database health check"""
        try:
            if self._client is None:
                return False
            await self._client.admin.command('ping')
            return True
        except Exception:
            return False


# Global database manager instance
db_manager = DatabaseManager()
