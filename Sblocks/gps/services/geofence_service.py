import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from repositories.database import db_manager
from schemas.entities import Geofence, GeofenceGeometry, GeofenceCenter, GeofenceType, GeofenceStatus, GeofenceCategory
from events.publisher import event_publisher

logger = logging.getLogger(__name__)

class GeofenceService:
    """Service for managing geofences with unified data format and Pydantic V2"""
    
    def __init__(self):
        self.db = db_manager
    
    async def create_geofence(
        self,
        name: str,
        description: Optional[str] = None,
        type: str = "depot",
        status: str = "active",
        geometry: Dict[str, Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: str = "system"
    ) -> Geofence:
        try:
            if not name:
                raise ValueError("Name is required")

            if not geometry:
                raise ValueError("Geometry is required")

            if not isinstance(geometry, dict):
                raise ValueError("Geometry must be a dictionary")

            required_fields = ['type', 'center'] if geometry.get('type') == 'circle' else ['type', 'points']
            for field in required_fields:
                if field not in geometry:
                    raise ValueError(f"Geometry must have '{field}' field")

            # Validate center coordinates or points using Pydantic model
            geometry_obj = GeofenceGeometry(**geometry)

            # Convert unified geometry to MongoDB GeoJSON
            if geometry_obj.type == GeofenceType.CIRCLE:
                geojson_geometry = {
                    "type": "Point",
                    "coordinates": [
                        geometry_obj.center.longitude,
                        geometry_obj.center.latitude
                    ]
                }
                # Store radius in metadata for app logic if needed
                if metadata is None:
                    metadata = {}
                metadata["radius"] = geometry_obj.radius

            elif geometry_obj.type in (GeofenceType.POLYGON, GeofenceType.RECTANGLE):
                # Convert points to GeoJSON Polygon coordinates
                if not geometry_obj.points or len(geometry_obj.points) < 3:
                    raise ValueError("At least 3 points required for polygon/rectangle geometry")

                # GeoJSON polygons require a closed ring: first point == last point
                points_coords = [
                    [pt["longitude"], pt["latitude"]] for pt in geometry_obj.points
                ]
                if points_coords[0] != points_coords[-1]:
                    points_coords.append(points_coords[0])

                geojson_geometry = {
                    "type": "Polygon",
                    "coordinates": [points_coords]
                }
            else:
                raise ValueError(f"Unsupported geometry type: {geometry_obj.type}")

            current_time = datetime.utcnow()

            geofence_data = {
                "name": name,
                "description": description or "",
                "type": GeofenceCategory(type.lower()),
                "status": GeofenceStatus(status.lower()),
                "geometry": geojson_geometry,  # MongoDB GeoJSON here
                "metadata": metadata or {},
                "created_by": created_by,
                "created_at": current_time,
                "updated_at": current_time,
                "is_active": status.lower() == "active"
            }

            logger.info(f"Creating geofence with data: {geofence_data}")

            geofence_model = Geofence(**geofence_data)

            mongo_data = geofence_model.model_dump(exclude={"id"}, by_alias=True)

            result = await self.db.db.geofences.insert_one(mongo_data)

            geofence_model.id = str(result.inserted_id)

            try:
                await event_publisher.publish_geofence_created(
                    geofence_id=str(result.inserted_id),
                    name=name,
                    created_by=created_by
                )
            except Exception as e:
                logger.warning(f"Failed to publish geofence created event: {e}")

            logger.info(f"Geofence created successfully: {name} (ID: {result.inserted_id})")
            return geofence_model

        except Exception as e:
            logger.error(f"Error creating geofence: {e}")
            logger.exception("Full traceback:")
            raise
    
    async def get_geofence_by_id(self, geofence_id: str) -> Optional[Geofence]:
        """Get geofence by ID"""
        try:
            # Convert string ID to ObjectId for MongoDB query
            if len(geofence_id) == 24:  # Standard ObjectId length
                query_id = ObjectId(geofence_id)
            else:
                query_id = geofence_id
            
            doc = await self.db.db.geofences.find_one({"_id": query_id})
            
            if doc:
                # Convert ObjectId to string for Pydantic
                doc["id"] = str(doc.pop("_id"))
                return Geofence(**doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting geofence {geofence_id}: {e}")
            return None
    
    async def get_geofences(
        self,
        is_active: Optional[bool] = None,
        geofence_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Geofence]:
        """Get geofences with optional filters"""
        try:
            query = {}
            
            if is_active is not None:
                query["is_active"] = is_active
            
            if geofence_type:
                query["type"] = geofence_type
            
            cursor = self.db.db.geofences.find(query).skip(offset).limit(limit)
            geofences = []
            
            async for doc in cursor:
                # Convert ObjectId to string
                doc["id"] = str(doc.pop("_id"))
                geofences.append(Geofence(**doc))
            
            return geofences
            
        except Exception as e:
            logger.error(f"Error getting geofences: {e}")
            return []
    
    async def update_geofence(
        self,
        geofence_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        geometry: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Geofence]:
        """Update geofence"""
        try:
            # Build update data
            update_data = {"updated_at": datetime.utcnow()}
            
            if name is not None:
                update_data["name"] = name
            
            if description is not None:
                update_data["description"] = description
            
            if geometry is not None:
                geometry_obj = GeofenceGeometry(**geometry)
                update_data["geometry"] = geometry_obj.model_dump()
            
            if status is not None:
                update_data["status"] = status
                update_data["is_active"] = status.lower() == "active"
            
            if metadata is not None:
                update_data["metadata"] = metadata
            
            # Convert ID
            query_id = ObjectId(geofence_id) if len(geofence_id) == 24 else geofence_id
            
            # Update in database
            result = await self.db.db.geofences.update_one(
                {"_id": query_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_geofence_by_id(geofence_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating geofence {geofence_id}: {e}")
            return None
    
    async def delete_geofence(self, geofence_id: str) -> bool:
        """Delete geofence"""
        try:
            query_id = ObjectId(geofence_id) if len(geofence_id) == 24 else geofence_id
            
            result = await self.db.db.geofences.delete_one({"_id": query_id})
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting geofence {geofence_id}: {e}")
            return False

# Create service instance
geofence_service = GeofenceService()