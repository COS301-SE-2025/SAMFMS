
import motor.motor_asyncio
import asyncio
import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    
    
    def __init__(self):
        self._client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self._db = None
        self.mongodb_url = os.getenv(
            "MONGODB_URL", 
            "mongodb://samfms_admin:SafeMongoPass2025%21SecureDB%40SAMFMS@mongodb:27017"
        )
        self.database_name = os.getenv("DATABASE_NAME", "samfms_management")
        
    async def connect(self):
        
        if self._client is None:
            try:
                
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
                
                
                try:
                    await self._create_indexes()
                except Exception as index_error:
                    logger.error(f"Index creation failed, but continuing: {index_error}")
                    
                
                logger.info(f"Connected to MongoDB: {self.database_name}")
                
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
    
    async def disconnect(self):
        
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("Disconnected from MongoDB")
    
    @property
    def db(self):
        
        if self._db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._db
    
    @property
    def client(self):
        
        if self._client is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._client
    
    async def _create_indexes(self):
        
        try:
            db = self.db
            
            
            async def create_index_safe(collection, index_spec, **options):
                try:
                    await collection.create_index(index_spec, **options)
                except Exception as e:
                    if "already exists" in str(e) and "different options" in str(e):
                        
                        try:
                            index_name = None
                            if isinstance(index_spec, str):
                                index_name = f"{index_spec}_1"
                            elif isinstance(index_spec, list):
                                index_name = "_".join([f"{field}_{direction}" for field, direction in index_spec])
                            
                            if index_name:
                                logger.warning(f"Dropping existing index {index_name} and recreating")
                                await collection.drop_index(index_name)
                                await collection.create_index(index_spec, **options)
                        except Exception as drop_error:
                            logger.warning(f"Could not recreate index {index_spec}: {drop_error}")
                    else:
                        logger.warning(f"Could not create index {index_spec}: {e}")
            
            
            await create_index_safe(db.vehicle_assignments, "vehicle_id")
            await create_index_safe(db.vehicle_assignments, "driver_id")
            await create_index_safe(db.vehicle_assignments, "status")
            await create_index_safe(db.vehicle_assignments, "assignment_type")
            await create_index_safe(db.vehicle_assignments, [("vehicle_id", 1), ("status", 1)])
            await create_index_safe(db.vehicle_assignments, [("driver_id", 1), ("status", 1)])
            await create_index_safe(db.vehicle_assignments, "created_at")
            
            
            await create_index_safe(db.vehicle_usage_logs, "vehicle_id")
            await create_index_safe(db.vehicle_usage_logs, "driver_id")
            await create_index_safe(db.vehicle_usage_logs, "assignment_id")
            await create_index_safe(db.vehicle_usage_logs, "trip_start")
            await create_index_safe(db.vehicle_usage_logs, [("vehicle_id", 1), ("trip_start", -1)])
            await create_index_safe(db.vehicle_usage_logs, [("driver_id", 1), ("trip_start", -1)])
            
            
            await create_index_safe(db.drivers, "employee_id", unique=True)
            await create_index_safe(db.drivers, "user_id", sparse=True)
            await create_index_safe(db.drivers, "email", unique=True)
            await create_index_safe(db.drivers, "license_number", unique=True)
            await create_index_safe(db.drivers, "status")
            await create_index_safe(db.drivers, "department")
            await create_index_safe(db.drivers, "current_vehicle_id", sparse=True)
            
            
            await create_index_safe(db.analytics_snapshots, "metric_type")
            await create_index_safe(db.analytics_snapshots, "generated_at")
            await create_index_safe(db.analytics_snapshots, "expires_at")
            await create_index_safe(db.analytics_snapshots, [("metric_type", 1), ("generated_at", -1)])
            
            
            await create_index_safe(db.audit_logs, "entity_type")
            await create_index_safe(db.audit_logs, "entity_id")
            await create_index_safe(db.audit_logs, "user_id")
            await create_index_safe(db.audit_logs, "timestamp")
            await create_index_safe(db.audit_logs, [("entity_type", 1), ("entity_id", 1)])
            
            
            await create_index_safe(db.analytics_snapshots, "expires_at", expireAfterSeconds=0)
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")
            
            logger.warning("Continuing service startup despite index creation issues")
    
    async def health_check(self) -> bool:
        
        try:
            await self._client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False



db_manager = DatabaseManager()



async def get_database():
    
    return db_manager.db


async def test_database_connection():
    
    return await db_manager.health_check()



def get_assignments_collection():
    
    return db_manager.db.vehicle_assignments


def get_usage_logs_collection():
    
    return db_manager.db.vehicle_usage_logs


def get_drivers_collection():
    
    return db_manager.db.drivers


def get_analytics_collection():
    
    return db_manager.db.analytics_snapshots


def get_audit_logs_collection():
    
    return db_manager.db.audit_logs
