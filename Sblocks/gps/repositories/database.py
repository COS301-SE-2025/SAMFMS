"""
Database configuration and connection management for GPS service with analytics support
"""
import motor.motor_asyncio
import asyncio
import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Centralized database connection manager for GPS service with analytics support"""
    
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

    @property
    def vehicle_locations(self):
        """Get locations collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.vehicle_locations
    
    async def _create_indexes(self):
        """Create necessary indexes for GPS collections including analytics support"""
        try:
            # Vehicle locations collection indexes (enhanced for analytics)
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
            # New indexes for analytics
            await locations_collection.create_index([
                ("vehicle_id", 1),
                ("date", 1)  # For daily analytics
            ])
            await locations_collection.create_index([
                ("vehicle_id", 1),
                ("engine_status", 1),
                ("timestamp", 1)  # For idle time calculations
            ])
            
            # Location history collection indexes (enhanced for analytics)
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
            # New indexes for analytics
            await history_collection.create_index([
                ("vehicle_id", 1),
                ("date", 1)  # For daily analytics
            ])
            await history_collection.create_index([
                ("vehicle_id", 1),
                ("movement_status", 1),
                ("timestamp", 1)  # For movement analysis
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
            
            # Tracking sessions collection indexes (enhanced for analytics)
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
            # New indexes for analytics
            await tracking_sessions_collection.create_index([
                ("vehicle_id", 1),
                ("date", 1)  # For daily session analytics
            ])
            await tracking_sessions_collection.create_index([
                ("ended_at", -1)  # For completed sessions
            ])
            
            # NEW: Vehicle analytics collection for pre-computed daily summaries
            analytics_collection = self._db.vehicle_analytics
            await analytics_collection.create_index([
                ("vehicle_id", 1),
                ("date", 1)
            ], unique=True)  # One record per vehicle per day
            await analytics_collection.create_index([
                ("date", -1)
            ])
            await analytics_collection.create_index([
                ("vehicle_id", 1),
                ("date", -1)
            ])
            
            # NEW: Fuel events collection for tracking fuel changes
            fuel_events_collection = self._db.fuel_events
            await fuel_events_collection.create_index([
                ("vehicle_id", 1),
                ("timestamp", -1)
            ])
            await fuel_events_collection.create_index([
                ("vehicle_id", 1),
                ("date", 1)
            ])
            await fuel_events_collection.create_index([
                ("event_type", 1),  # "refuel", "consumption"
                ("timestamp", -1)
            ])
            
            logger.info("Database indexes created successfully with analytics support")
            
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

    # NEW: Analytics helper methods
    async def get_daily_analytics(self, vehicle_id: str = None, date: str = None):
        """Get pre-computed daily analytics for vehicles"""
        try:
            collection = self._db.vehicle_analytics
            
            # Build query
            query = {}
            if vehicle_id:
                query["vehicle_id"] = vehicle_id
            if date:
                query["date"] = date
            
            cursor = collection.find(query).sort("date", -1)
            return await cursor.to_list(length=None)
            
        except Exception as e:
            logger.error(f"Error fetching daily analytics: {e}")
            raise
    
    async def get_vehicle_tracking_data(self, vehicle_id: str, start_date: str, end_date: str):
        """Get tracking data for analytics calculations"""
        try:
            collection = self._db.vehicle_locations
            
            query = {
                "vehicle_id": vehicle_id,
                "timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            cursor = collection.find(query).sort("timestamp", 1)
            return await cursor.to_list(length=None)
            
        except Exception as e:
            logger.error(f"Error fetching tracking data: {e}")
            raise
    
    async def store_daily_analytics(self, analytics_data: dict):
        """Store or update daily analytics summary"""
        try:
            collection = self._db.vehicle_analytics
            
            # Upsert daily analytics
            await collection.replace_one(
                {
                    "vehicle_id": analytics_data["vehicle_id"],
                    "date": analytics_data["date"]
                },
                analytics_data,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error storing daily analytics: {e}")
            raise

class DatabaseManagerManagement():
    """Centralized database connection manager for Trip Planning: Management access"""
    def __init__(self):
        self._client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self._db = None
        self.mongodb_url = os.getenv(
            "MONGODB_URL",
            "mongodb://samfms_admin:SafeMongoPass2025%21SecureDB%40SAMFMS@mongodb:27017"
        )
        self.database_name = os.getenv("DATABASE_MANAGEMENT","samfms_management")
    
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

                logger.info(f"Connected to MongoDB Management: {self.database_name}")
            
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB Management: {e}")
                raise
    async def disconnect(self):
        """Safely disconnect from database"""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("Disconnected from MongoDB Management")
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._client is not None and self._db is not None
    
    @property
    def db(self):
        """Get database Management instance"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db

    async def health_check(self) -> bool:
        """Check database health"""
        try:
            if not self._client:
                return False
            await self._client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database health check failed Management: {e}")
            return False
    
    @property
    def drivers(self):
        """Get drivers collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.drivers
    
    @property
    def vehicles(self):
        """Get vehicles collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.vehicles
    
    @property
    def vehicle_assignments(self):
        """Get vehicle_assignments collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.vehicle_assignments

# Global database manager instance
db_manager = DatabaseManager()
db_manager_management = DatabaseManagerManagement()