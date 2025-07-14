import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict
import asyncio

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Centralized database connection manager with proper connection pooling"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self._connection_lock = asyncio.Lock()
        self._connected = False
    
    async def connect(self) -> None:
        """Connect to MongoDB with proper connection pooling and error handling"""
        async with self._connection_lock:
            if self._connected and self.client:
                return
            
            try:
                mongo_uri = os.getenv("MONGODB_URL", "mongodb://mongodb_core:27017")
                database_name = os.getenv("DATABASE_NAME", "mcore")
                
                logger.info(f"Connecting to MongoDB: {mongo_uri}")
                
                self.client = AsyncIOMotorClient(
                    mongo_uri,
                    # Connection pool settings
                    maxPoolSize=50,
                    minPoolSize=10,
                    maxIdleTimeMS=30000,
                    # Timeout settings
                    connectTimeoutMS=5000,
                    serverSelectionTimeoutMS=5000,
                    socketTimeoutMS=5000,
                    # Reliability settings
                    retryWrites=True,
                    retryReads=True,
                    # Heartbeat settings
                    heartbeatFrequencyMS=10000
                )
                
                # Test connection
                await self.client.admin.command('ping')
                self.db = self.client[database_name]
                self._connected = True
                
                logger.info("✅ Database connection established successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to connect to database: {e}")
                self._connected = False
                if self.client:
                    self.client.close()
                    self.client = None
                raise
    
    async def disconnect(self) -> None:
        """Gracefully disconnect from MongoDB"""
        async with self._connection_lock:
            if self.client and self._connected:
                try:
                    self.client.close()
                    logger.info("✅ Database connection closed successfully")
                except Exception as e:
                    logger.error(f"❌ Error closing database connection: {e}")
                finally:
                    self.client = None
                    self.db = None
                    self._connected = False
    
    async def health_check(self) -> Dict[str, str]:
        """Check database connection health"""
        try:
            if not self.client or not self._connected:
                return {
                    "status": "unhealthy",
                    "error": "Database not connected"
                }
            
            await self.client.admin.command('ping')
            return {
                "status": "healthy",
                "message": "Database connection is healthy"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy", 
                "error": str(e)
            }
    
    def get_database(self):
        """Get the database instance"""
        if not self._connected or not self.db:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.db

# Global database manager instance
db_manager = DatabaseManager()

# Function to get the database manager instance
async def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    return db_manager

# Backward compatibility
async def get_database():
    """Get the database instance (async version)"""
    if not db_manager._connected:
        await db_manager.connect()
    return db_manager.get_database()

# Legacy sync version for backward compatibility
def get_db_sync():
    """Get the database instance (sync version) - deprecated"""
    logger.warning("get_db_sync is deprecated, use async get_database() instead")
    return db_manager.get_database()

# Export for backward compatibility
db = db_manager
