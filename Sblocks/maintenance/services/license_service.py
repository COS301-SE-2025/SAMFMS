"""
License Management Service
Handles business logic for license and certification tracking
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta

from schemas.entities import LicenseRecord, LicenseType
from repositories import LicenseRecordsRepository

logger = logging.getLogger(__name__)


class LicenseService:
    """Service for license and certification management"""
    
    def __init__(self):
        self.repository = LicenseRecordsRepository()
        
    async def create_license_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new license record"""
        try:
            # Validate required fields
            required_fields = ["entity_id", "entity_type", "license_type", "license_number", 
                             "title", "issue_date", "expiry_date", "issuing_authority"]
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Required field '{field}' is missing")
            
            # Validate entity type
            if data["entity_type"] not in ["vehicle", "driver"]:
                raise ValueError("Entity type must be 'vehicle' or 'driver'")
            
            # Parse dates if they're strings
            date_fields = ["issue_date", "expiry_date", "renewal_date"]
            for field in date_fields:
                if field in data and isinstance(data[field], str):
                    data[field] = datetime.strptime(data[field], "%Y-%m-%d").date()
            
            # Set default values
            if "is_active" not in data:
                data["is_active"] = True
            if "advance_notice_days" not in data:
                data["advance_notice_days"] = 30
            if "created_at" not in data:
                data["created_at"] = datetime.utcnow()
                
            record = await self.repository.create(data)
            logger.info(f"Created license record {record['id']} for {data['entity_type']} {data['entity_id']}")
            
            return record
            
        except Exception as e:
            logger.error(f"Error creating license record: {e}")
            raise
            
    async def get_license_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a license record by ID"""
        try:
            return await self.repository.get_by_id(record_id)
        except Exception as e:
            logger.error(f"Error fetching license record {record_id}: {e}")
            raise
            
    async def update_license_record(self, record_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a license record"""
        try:
            # Parse dates if they're strings
            date_fields = ["issue_date", "expiry_date", "renewal_date"]
            for field in date_fields:
                if field in data and isinstance(data[field], str):
                    data[field] = datetime.strptime(data[field], "%Y-%m-%d").date()
                    
            record = await self.repository.update(record_id, data)
            if record:
                logger.info(f"Updated license record {record_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Error updating license record {record_id}: {e}")
            raise
            
    async def delete_license_record(self, record_id: str) -> bool:
        """Delete a license record"""
        try:
            success = await self.repository.delete(record_id)
            if success:
                logger.info(f"Deleted license record {record_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting license record {record_id}: {e}")
            raise
            
    async def get_entity_licenses(self, entity_id: str, entity_type: str) -> List[Dict[str, Any]]:
        """Get all licenses for an entity"""
        try:
            if entity_type not in ["vehicle", "driver"]:
                raise ValueError("Entity type must be 'vehicle' or 'driver'")
                
            return await self.repository.get_by_entity(entity_id, entity_type)
        except Exception as e:
            logger.error(f"Error fetching licenses for {entity_type} {entity_id}: {e}")
            raise
            
    async def get_expiring_licenses(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get licenses expiring in the next X days"""
        try:
            return await self.repository.get_expiring_soon(days_ahead)
        except Exception as e:
            logger.error(f"Error fetching expiring licenses: {e}")
            raise
            
    async def get_expired_licenses(self) -> List[Dict[str, Any]]:
        """Get expired licenses"""
        try:
            return await self.repository.get_expired_licenses()
        except Exception as e:
            logger.error(f"Error fetching expired licenses: {e}")
            raise
            
    async def get_licenses_by_type(self, license_type: str) -> List[Dict[str, Any]]:
        """Get licenses by type"""
        try:
            return await self.repository.get_by_license_type(license_type)
        except Exception as e:
            logger.error(f"Error fetching licenses by type {license_type}: {e}")
            raise
            
    async def get_all_licenses(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all licenses with pagination"""
        try:
            return await self.repository.find(
                query={"is_active": True},
                skip=skip,
                limit=limit,
                sort=[("expiry_date", 1)]
            )
        except Exception as e:
            logger.error(f"Error fetching all licenses: {e}")
            raise
            
    async def renew_license(self, record_id: str, new_expiry_date: str, 
                           renewal_cost: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Renew a license"""
        try:
            # Parse the new expiry date
            new_expiry = datetime.strptime(new_expiry_date, "%Y-%m-%d").date()
            
            update_data = {
                "expiry_date": new_expiry,
                "renewal_date": date.today()
            }
            
            if renewal_cost is not None:
                update_data["renewal_cost"] = renewal_cost
                
            record = await self.repository.update(record_id, update_data)
            if record:
                logger.info(f"Renewed license record {record_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Error renewing license record {record_id}: {e}")
            raise
            
    async def deactivate_license(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Deactivate a license"""
        try:
            record = await self.repository.update(record_id, {"is_active": False})
            if record:
                logger.info(f"Deactivated license record {record_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Error deactivating license record {record_id}: {e}")
            raise
            
    async def search_licenses(self, 
                            query: Dict[str, Any],
                            skip: int = 0,
                            limit: int = 100,
                            sort_by: str = "expiry_date",
                            sort_order: str = "asc") -> List[Dict[str, Any]]:
        """Search license records with complex filters"""
        try:
            # Build MongoDB query from search parameters
            db_query = {}
            
            if "entity_id" in query:
                db_query["entity_id"] = query["entity_id"]
            if "entity_type" in query:
                db_query["entity_type"] = query["entity_type"]
            if "license_type" in query:
                db_query["license_type"] = query["license_type"]
            if "is_active" in query:
                db_query["is_active"] = query["is_active"]
                
            # Expiry date range
            if "expiring_within_days" in query:
                future_date = date.today() + timedelta(days=query["expiring_within_days"])
                db_query["expiry_date"] = {"$lte": future_date}
                
            # Sorting
            sort_direction = 1 if sort_order == "asc" else -1
            sort = [(sort_by, sort_direction)]
            
            return await self.repository.find(db_query, skip, limit, sort)
            
        except Exception as e:
            logger.error(f"Error searching license records: {e}")
            raise
            
    async def get_license_summary(self, entity_id: Optional[str] = None,
                                entity_type: Optional[str] = None) -> Dict[str, Any]:
        """Get license summary statistics"""
        try:
            query = {}
            if entity_id:
                query["entity_id"] = entity_id
            if entity_type:
                query["entity_type"] = entity_type
                
            # Get counts for different status
            total_licenses = await self.repository.count(query)
            
            active_query = query.copy()
            active_query["is_active"] = True
            active_licenses = await self.repository.count(active_query)
            
            # Expiring soon (30 days)
            future_date = date.today() + timedelta(days=30)
            expiring_query = query.copy()
            expiring_query.update({
                "is_active": True,
                "expiry_date": {"$lte": future_date}
            })
            expiring_licenses = await self.repository.count(expiring_query)
            
            # Expired
            expired_query = query.copy()
            expired_query.update({
                "is_active": True,
                "expiry_date": {"$lt": date.today()}
            })
            expired_licenses = await self.repository.count(expired_query)
            
            return {
                "total_licenses": total_licenses,
                "active_licenses": active_licenses,
                "inactive_licenses": total_licenses - active_licenses,
                "expiring_soon": expiring_licenses,
                "expired": expired_licenses
            }
            
        except Exception as e:
            logger.error(f"Error getting license summary: {e}")
            raise


# Global service instance
license_service = LicenseService()
