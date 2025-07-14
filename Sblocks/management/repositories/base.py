"""
Base repository class with common database operations
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TypeVar, Generic
from bson import ObjectId
from datetime import datetime
import logging

from .database import db_manager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
    
    @property
    def collection(self):
        """Get collection instance"""
        return db_manager.db[self.collection_name]
    
    async def create(self, entity: Dict[str, Any]) -> str:
        """Create new entity"""
        try:
            entity["created_at"] = datetime.utcnow()
            entity["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(entity)
            logger.info(f"Created entity in {self.collection_name}: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create entity in {self.collection_name}: {e}")
            raise
    
    async def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by ID"""
        try:
            if not ObjectId.is_valid(entity_id):
                return None
                
            entity = await self.collection.find_one({"_id": ObjectId(entity_id)})
            if entity:
                entity["_id"] = str(entity["_id"])
            return entity
            
        except Exception as e:
            logger.error(f"Failed to get entity {entity_id} from {self.collection_name}: {e}")
            raise
    
    async def update(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """Update entity"""
        try:
            if not ObjectId.is_valid(entity_id):
                return False
                
            updates["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(entity_id)},
                {"$set": updates}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated entity {entity_id} in {self.collection_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update entity {entity_id} in {self.collection_name}: {e}")
            raise
    
    async def delete(self, entity_id: str) -> bool:
        """Delete entity"""
        try:
            if not ObjectId.is_valid(entity_id):
                return False
                
            result = await self.collection.delete_one({"_id": ObjectId(entity_id)})
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted entity {entity_id} from {self.collection_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete entity {entity_id} from {self.collection_name}: {e}")
            raise
    
    async def find(
        self, 
        filter_query: Dict[str, Any] = None, 
        skip: int = 0, 
        limit: int = 100,
        sort: List[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Find entities with pagination"""
        try:
            filter_query = filter_query or {}
            
            cursor = self.collection.find(filter_query)
            
            if sort:
                cursor = cursor.sort(sort)
            
            cursor = cursor.skip(skip).limit(limit)
            
            entities = []
            async for entity in cursor:
                entity["_id"] = str(entity["_id"])
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Failed to find entities in {self.collection_name}: {e}")
            raise
    
    async def count(self, filter_query: Dict[str, Any] = None) -> int:
        """Count entities matching filter"""
        try:
            filter_query = filter_query or {}
            return await self.collection.count_documents(filter_query)
            
        except Exception as e:
            logger.error(f"Failed to count entities in {self.collection_name}: {e}")
            raise
    
    async def aggregate(self, pipeline: List[Dict[str, Any]], limit: int = 1000) -> List[Dict[str, Any]]:
        """Execute aggregation pipeline"""
        try:
            cursor = self.collection.aggregate(pipeline)
            results = await cursor.to_list(length=limit)
            
            # Convert ObjectIds to strings
            for result in results:
                if "_id" in result and isinstance(result["_id"], ObjectId):
                    result["_id"] = str(result["_id"])
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to execute aggregation in {self.collection_name}: {e}")
            raise
    
    async def find_one(self, filter_query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single entity"""
        try:
            entity = await self.collection.find_one(filter_query)
            if entity:
                entity["_id"] = str(entity["_id"])
            return entity
            
        except Exception as e:
            logger.error(f"Failed to find one entity in {self.collection_name}: {e}")
            raise
    
    async def update_many(self, filter_query: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """Update multiple entities"""
        try:
            updates["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_many(
                filter_query,
                {"$set": updates}
            )
            
            logger.info(f"Updated {result.modified_count} entities in {self.collection_name}")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Failed to update many entities in {self.collection_name}: {e}")
            raise
    
    async def delete_many(self, filter_query: Dict[str, Any]) -> int:
        """Delete multiple entities"""
        try:
            result = await self.collection.delete_many(filter_query)
            
            logger.info(f"Deleted {result.deleted_count} entities from {self.collection_name}")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete many entities from {self.collection_name}: {e}")
            raise
