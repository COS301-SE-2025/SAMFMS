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
        geometry: Dict[str, Any] = None
    ) -> Geofence:
        try:
            if not name:
                raise ValueError("Name is required")
            if not geometry or not isinstance(geometry, dict):
                raise ValueError("Geometry must be provided as a dictionary")

            # Validate using our Pydantic model
            geometry_obj = GeofenceGeometry(**geometry)

            # Build MongoDB GeoJSON format
            if geometry_obj.type == GeofenceType.CIRCLE:
                geojson_geometry = {
                    "type": "Point",
                    "coordinates": [
                        geometry_obj.center.longitude,
                        geometry_obj.center.latitude
                    ],
                    "radius": geometry_obj.radius
                }
            elif geometry_obj.type in (GeofenceType.POLYGON, GeofenceType.RECTANGLE):
                if not geometry_obj.points or len(geometry_obj.points) < 3:
                    raise ValueError("At least 3 points required for polygon/rectangle geometry")

                points_coords = [[pt["longitude"], pt["latitude"]] for pt in geometry_obj.points]
                if points_coords[0] != points_coords[-1]:
                    points_coords.append(points_coords[0])  # Close the polygon

                geojson_geometry = {
                    "type": "Polygon",
                    "coordinates": [points_coords]
                }
            else:
                raise ValueError(f"Unsupported geometry type: {geometry_obj.type}")

            # Combine for Pydantic model (keep both)
            geofence_data = {
                "name": name,
                "description": description or "",
                "type": GeofenceCategory(type.lower()),
                "status": GeofenceStatus(status.lower()),
                "geometry": geometry,               # API-facing structure
                "geojson_geometry": geojson_geometry  # MongoDB storage
            }

            logger.info(f"Creating geofence with data: {geofence_data}")

            # Build Pydantic model
            geofence_model = Geofence(**geofence_data)

            # Dump for MongoDB
            mongo_data = {
                "name": geofence_model.name,
                "description": geofence_model.description,
                "type": geofence_model.type,
                "status": geofence_model.status,
                "geometry": geojson_geometry,  # <-- Use the variable we created earlier
            }



            logger.info(f"Inserting into DB: {self.db.db.name}, Collection: geofences")
            result = await self.db.db.geofences.insert_one(mongo_data)
            logger.info(f"Inserted document ID: {result.inserted_id}")

            geofence_model.id = str(result.inserted_id)

            # Publish event
            try:
                await event_publisher.publish_geofence_created(
                    geofence_id=str(result.inserted_id),
                    name=name
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
    
    # Helper to conver GEOjson from mongodb to expected format
    def _normalize_geometry(self, doc: dict) -> dict:
        geometry = doc.get("geometry", {})
        if geometry.get("type") == "Point":
            # Convert GeoJSON Point back to "circle"
            return {
                "type": "circle",
                "center": {
                    "latitude": geometry["coordinates"][1],
                    "longitude": geometry["coordinates"][0]
                },
                "radius": geometry.get("radius")
            }
        elif geometry.get("type") == "Polygon":
            # Convert GeoJSON Polygon back to "polygon"
            return {
                "type": "polygon",
                "points": [
                    {"latitude": lat, "longitude": lng}
                    for lng, lat in geometry["coordinates"][0]
                ]
            }
        return geometry


    
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
                doc["id"] = str(doc.pop("_id"))
                doc["geometry"] = self._normalize_geometry(doc)
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