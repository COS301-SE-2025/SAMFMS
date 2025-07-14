"""
Base repository class for Maintenance Service
"""

import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from .database import db_manager

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository with common CRUD operations"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        
    async def get_collection(self):
        """Get the MongoDB collection"""
        return await db_manager.get_collection(self.collection_name)
        
    def _prepare_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare document for MongoDB insertion"""
        doc = data.copy()
        
        # Handle datetime objects
        for key, value in doc.items():
            if isinstance(value, datetime):
                doc[key] = value
                
        return doc
        
    def _process_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process MongoDB result for API response"""
        if result and "_id" in result:
            result["id"] = str(result["_id"])
            if "id" not in result or result["id"] != str(result["_id"]):
                # Only remove _id if we successfully created the id field
                del result["_id"]
        return result
        
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document"""
        try:
            collection = await self.get_collection()
            doc = self._prepare_document(data)
            
            result = await collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            
            return self._process_result(doc)
            
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error in {self.collection_name}: {e}")
            raise ValueError("Document with this identifier already exists")
        except Exception as e:
            logger.error(f"Error creating document in {self.collection_name}: {e}")
            raise
            
    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            collection = await self.get_collection()
            
            # Handle both ObjectId and string IDs
            query_id = ObjectId(doc_id) if ObjectId.is_valid(doc_id) else doc_id
            result = await collection.find_one({"_id": query_id})
            
            return self._process_result(result) if result else None
            
        except Exception as e:
            logger.error(f"Error fetching document from {self.collection_name}: {e}")
            raise
            
    async def update(self, doc_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update document by ID"""
        try:
            collection = await self.get_collection()
            
            # Prepare update data
            update_doc = self._prepare_document(data)
            update_doc["updated_at"] = datetime.utcnow()
            
            query_id = ObjectId(doc_id) if ObjectId.is_valid(doc_id) else doc_id
            result = await collection.find_one_and_update(
                {"_id": query_id},
                {"$set": update_doc},
                return_document=True
            )
            
            return self._process_result(result) if result else None
            
        except Exception as e:
            logger.error(f"Error updating document in {self.collection_name}: {e}")
            raise
            
    async def delete(self, doc_id: str) -> bool:
        """Delete document by ID"""
        try:
            collection = await self.get_collection()
            
            query_id = ObjectId(doc_id) if ObjectId.is_valid(doc_id) else doc_id
            result = await collection.delete_one({"_id": query_id})
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting document from {self.collection_name}: {e}")
            raise
            
    async def find(self, 
                   query: Dict[str, Any] = None, 
                   skip: int = 0, 
                   limit: int = 100,
                   sort: List[tuple] = None) -> List[Dict[str, Any]]:
        """Find documents with query, pagination, and sorting"""
        try:
            collection = await self.get_collection()
            
            cursor = collection.find(query or {})
            
            if sort:
                cursor = cursor.sort(sort)
            if skip > 0:
                cursor = cursor.skip(skip)
            if limit > 0:
                cursor = cursor.limit(limit)
                
            results = await cursor.to_list(length=limit)
            return [self._process_result(doc) for doc in results]
            
        except Exception as e:
            logger.error(f"Error finding documents in {self.collection_name}: {e}")
            raise
            
    async def count(self, query: Dict[str, Any] = None) -> int:
        """Count documents matching query"""
        try:
            collection = await self.get_collection()
            return await collection.count_documents(query or {})
            
        except Exception as e:
            logger.error(f"Error counting documents in {self.collection_name}: {e}")
            raise
            
    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute aggregation pipeline"""
        try:
            collection = await self.get_collection()
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            return [self._process_result(doc) for doc in results]
            
        except Exception as e:
            logger.error(f"Error executing aggregation in {self.collection_name}: {e}")
            raise
