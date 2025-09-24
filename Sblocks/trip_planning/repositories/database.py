"""
Database configuration and connection management for Trip Planning service
"""
import motor.motor_asyncio
import asyncio
import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Centralized database connection manager for Trip Planning service"""
    
    def __init__(self):
        self._client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self._db = None
        self.mongodb_url = os.getenv(
            "MONGODB_URL",
            "mongodb://samfms_admin:SafeMongoPass2025%21SecureDB%40SAMFMS@mongodb:27017"
        )
        self.database_name = os.getenv("DATABASE_TRIP_PLANNING", "samfms_trip_planning")
        self._loop_id = None
        
    async def connect(self):
        """Establish database connection with optimal settings and error recovery (loop-aware)."""
        import asyncio
        current_loop_id = id(asyncio.get_running_loop())
        if self._client is None or self._loop_id != current_loop_id:
            try:
                if self._client is not None and self._loop_id != current_loop_id:
                    try:
                        logger.warning(f"[DB DEBUG] Loop changed; rebuilding Motor client (old={self._loop_id}, new={current_loop_id})")
                        self._client.close()
                    except Exception as close_err:
                        logger.warning(f"[DB DEBUG] Error closing stale client: {close_err}")
                    self._client = None
                    self._db = None

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

                await self._client.admin.command('ping')
                self._db = self._client[self.database_name]
                self._loop_id = current_loop_id
                logger.warning(f"[DB DEBUG] Connected to MongoDB '{self.database_name}' on loop={self._loop_id} client_id={id(self._client)}")

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

    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            if not self._client:
                return False
            await self._client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_metrics(self) -> dict:
        """Get database metrics"""
        try:
            if self._db is None:
                return {"status": "disconnected"}
            
            # Get collection stats
            collections = ["trips", "trip_constraints", "driver_assignments", 
                          "trip_analytics", "notifications", "notification_preferences",
                          "phone_usage_violations", "speed_violations", "excessive_braking_violations", 
                          "excessive_acceleration_violations", "driver_ping_sessions", "driver_history"]
            
            metrics = {
                "status": "connected",
                "database": self.database_name,
                "collections": {}
            }
            
            for collection_name in collections:
                try:
                    collection = getattr(self, collection_name)
                    count = await collection.count_documents({})
                    metrics["collections"][collection_name] = {"document_count": count}
                except Exception as e:
                    metrics["collections"][collection_name] = {"error": str(e)}
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get database metrics: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Trips collection indexes
            await self.trips.create_index("status")
            await self.trips.create_index("scheduled_start_time")
            await self.trips.create_index("created_by")
            await self.trips.create_index("driver_assignment")
            await self.trips.create_index("vehicle_id")
            await self.trips.create_index([("scheduled_start_time", 1), ("status", 1)])
            
            # Geospatial indexes for location-based queries
            await self.trips.create_index([("origin.location", "2dsphere")])
            await self.trips.create_index([("destination.location", "2dsphere")])
            
            # Trip constraints indexes
            await self.trip_constraints.create_index("trip_id")
            await self.trip_constraints.create_index("type")
            await self.trip_constraints.create_index([("trip_id", 1), ("is_active", 1)])
            
            # Driver assignments indexes
            await self.driver_assignments.create_index("trip_id", unique=True)
            await self.driver_assignments.create_index("driver_id")
            await self.driver_assignments.create_index("assigned_at")
            
            # Trip analytics indexes
            await self.trip_analytics.create_index("trip_id", unique=True)
            await self.trip_analytics.create_index("calculated_at")
            
            # Notifications indexes
            await self.notifications.create_index([("user_id", 1), ("sent_at", -1)])
            await self.notifications.create_index([("user_id", 1), ("is_read", 1)])
            await self.notifications.create_index("type")
            await self.notifications.create_index("trip_id")
            
            # Notification preferences indexes
            await self.notification_preferences.create_index("user_id", unique=True)
            
            # Phone usage violations indexes
            await self.phone_usage_violations.create_index("trip_id")
            await self.phone_usage_violations.create_index("driver_id")
            await self.phone_usage_violations.create_index([("trip_id", 1), ("start_time", -1)])
            await self.phone_usage_violations.create_index("is_active")
            
            # Speed violations indexes
            await self.speed_violations.create_index("trip_id")
            await self.speed_violations.create_index("driver_id")
            await self.speed_violations.create_index([("trip_id", 1), ("time", -1)])
            await self.speed_violations.create_index("time")
            
            # Excessive braking violations indexes
            await self.excessive_braking_violations.create_index("trip_id")
            await self.excessive_braking_violations.create_index("driver_id")
            await self.excessive_braking_violations.create_index([("trip_id", 1), ("time", -1)])
            await self.excessive_braking_violations.create_index("time")
            
            # Excessive acceleration violations indexes
            await self.excessive_acceleration_violations.create_index("trip_id")
            await self.excessive_acceleration_violations.create_index("driver_id")
            await self.excessive_acceleration_violations.create_index([("trip_id", 1), ("time", -1)])
            await self.excessive_acceleration_violations.create_index("time")
            
            # Driver ping sessions indexes
            await self.driver_ping_sessions.create_index("trip_id", unique=True)
            await self.driver_ping_sessions.create_index("driver_id")
            await self.driver_ping_sessions.create_index("is_active")
            await self.driver_ping_sessions.create_index("started_at")
            
            # Driver history indexes
            await self.driver_history.create_index("driver_id", unique=True)
            await self.driver_history.create_index("driver_risk_level")
            await self.driver_history.create_index("driver_safety_score")
            await self.driver_history.create_index("last_updated")
            await self.driver_history.create_index([("driver_safety_score", -1), ("driver_risk_level", 1)])
            
            # Compound indexes for common queries
            await self.trips.create_index([
                ("status", 1), 
                ("scheduled_start_time", 1), 
                ("driver_assignment", 1)
            ])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    @property
    def trips(self):
        """Get trips collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.trips
    
    @property
    def trips_scheduled(self):
        """Get Scheduled trips collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.trips_scheduled

    @property
    def trip_history(self):
        """Get trip history"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.trip_history
    
    @property
    def trip_constraints(self):
        """Get trip constraints collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.trip_constraints
    
    @property
    def driver_assignments(self):
        """Get driver assignments collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.driver_assignments
    
    @property
    def trip_analytics(self):
        """Get trip analytics collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.trip_analytics
    
    @property
    def notifications(self):
        """Get notifications collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.notifications
    
    @property
    def notification_preferences(self):
        """Get notification preferences collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.notification_preferences
    
    @property
    def phone_usage_violations(self):
        """Get phone usage violations collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.phone_usage_violations
    
    @property
    def speed_violations(self):
        """Get speed violations collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.speed_violations
    
    @property
    def excessive_braking_violations(self):
        """Get excessive braking violations collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.excessive_braking_violations
    
    @property
    def excessive_acceleration_violations(self):
        """Get excessive acceleration violations collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.excessive_acceleration_violations
    
    @property
    def driver_ping_sessions(self):
        """Get driver ping sessions collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.driver_ping_sessions
    
    @property
    def driver_history(self):
        """Get driver history collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.driver_history
    
    @property
    def smarttrips(self):
        """Get smart trips collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.smart_trips

    @property
    def route_recommendations(self):
        """Get route recommendations collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.route_recommendations

    
    async def create_trip_with_transaction(self, trip_data: dict, constraints: list = None):
        """Create a trip with constraints in a transaction"""
        async with await self._client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Insert trip
                    trip_result = await self.trips.insert_one(trip_data, session=session)
                    trip_id = str(trip_result.inserted_id)
                    
                    # Insert constraints if provided
                    if constraints:
                        for constraint in constraints:
                            constraint["trip_id"] = trip_id
                        await self.trip_constraints.insert_many(constraints, session=session)
                    
                    await session.commit_transaction()
                    return trip_id
                    
                except Exception as e:
                    await session.abort_transaction()
                    logger.error(f"Transaction failed: {e}")
                    raise
    
    async def delete_trip_with_cleanup(self, trip_id: str):
        """Delete a trip and all related data in a transaction"""
        async with await self._client.start_session() as session:
            async with session.start_transaction():
                try:
                    # Delete trip
                    await self.trips.delete_one({"_id": trip_id}, session=session)
                    
                    # Delete related data
                    await self.trip_constraints.delete_many({"trip_id": trip_id}, session=session)
                    await self.driver_assignments.delete_many({"trip_id": trip_id}, session=session)
                    await self.trip_analytics.delete_many({"trip_id": trip_id}, session=session)
                    
                    # Keep notifications for audit trail, just mark them
                    await self.notifications.update_many(
                        {"trip_id": trip_id},
                        {"$set": {"trip_deleted": True}},
                        session=session
                    )
                    
                    await session.commit_transaction()
                    
                except Exception as e:
                    await session.abort_transaction()
                    logger.error(f"Cleanup transaction failed: {e}")
                    raise


class DatabaseManagerGeo():
    """Centralized database connection manager for Trip Planning: GPS access"""
    def __init__(self):
        self._client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self._db = None
        self.mongodb_url = os.getenv(
            "MONGODB_URL",
            "mongodb://samfms_admin:SafeMongoPass2025%21SecureDB%40SAMFMS@mongodb:27017"
        )
        self.database_name = os.getenv("DATABASE_TRIP_PLANNING_GEO", "samfms_trip_planning_geo")
        # NEW
        self._loop_id = None
    
    async def connect(self):
        """Establish database connection with optimal settings and error recovery (loop-aware)."""
        import asyncio
        current_loop_id = id(asyncio.get_running_loop())
        if self._client is None or self._loop_id != current_loop_id:
            try:
                if self._client is not None and self._loop_id != current_loop_id:
                    try:
                        logger.warning(f"[DB DEBUG] Loop changed; rebuilding Motor client (old={self._loop_id}, new={current_loop_id})")
                        self._client.close()
                    except Exception as close_err:
                        logger.warning(f"[DB DEBUG] Error closing stale client: {close_err}")
                    self._client = None
                    self._db = None

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
                await self._client.admin.command('ping')
                self._db = self._client[self.database_name]
                self._loop_id = current_loop_id
                logger.warning(f"[DB DEBUG] Connected to MongoDB GEO '{self.database_name}' on loop={self._loop_id} client_id={id(self._client)}")

                try:
                    await self._create_indexes()
                except Exception as index_error:
                    logger.warning(f"Failed to create some GEO indexes: {index_error}")

                logger.info(f"Connected to MongoDB GEO: {self.database_name}")

            except Exception as e:
                logger.error(f"Failed to connect to MongoDB GEO: {e}")
                raise
    async def disconnect(self):
        """Safely disconnect from database"""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("Disconnected from MongoDB GPS")
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._client is not None and self._db is not None
    
    @property
    def db(self):
        """Get database GPS instance"""
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
            logger.error(f"Database health check failed GPS: {e}")
            return False
    
    @property
    def locations(self):
        """Get locations collection"""
        if self._db is None:
            raise RuntimeError("Database not connected")
        return self._db.vehicle_locations

class DatabaseManagerManagement():
    """Centralized database connection manager for Trip Planning: Management access"""
    def __init__(self):
        self._client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self._db = None
        self.mongodb_url = os.getenv(
            "MONGODB_URL",
            "mongodb://samfms_admin:SafeMongoPass2025%21SecureDB%40SAMFMS@mongodb:27017"
        )
        self.database_name = os.getenv("DATABASE_TRIP_PLANNING_MANAGEMENT", "samfms_trip_planning_management")
        # NEW
        self._loop_id = None
    
    async def connect(self):
        """Establish database connection with optimal settings and error recovery (loop-aware)."""
        import asyncio
        current_loop_id = id(asyncio.get_running_loop())
        if self._client is None or self._loop_id != current_loop_id:
            try:
                if self._client is not None and self._loop_id != current_loop_id:
                    try:
                        logger.warning(f"[DB DEBUG] Loop changed; rebuilding Motor client (old={self._loop_id}, new={current_loop_id})")
                        self._client.close()
                    except Exception as close_err:
                        logger.warning(f"[DB DEBUG] Error closing stale client: {close_err}")
                    self._client = None
                    self._db = None

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
                await self._client.admin.command('ping')
                self._db = self._client[self.database_name]
                self._loop_id = current_loop_id
                logger.warning(f"[DB DEBUG] Connected to MongoDB MGMT '{self.database_name}' on loop={self._loop_id} client_id={id(self._client)}")

                try:
                    await self._create_indexes()
                except Exception as index_error:
                    logger.warning(f"Failed to create some MGMT indexes: {index_error}")

                logger.info(f"Connected to MongoDB MGMT: {self.database_name}")

            except Exception as e:
                logger.error(f"Failed to connect to MongoDB MGMT: {e}")
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

#class DatabaseManagerSecurity

# Global database manager instance
db_manager = DatabaseManager()
db_manager_gps = DatabaseManagerGeo()
db_manager_management = DatabaseManagerManagement()
