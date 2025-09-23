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

            # Normalize everything early
            geom_type = geometry.get("type", "").lower()
            type = type.lower()
            status = status.lower()
            coordinates = geometry.get("coordinates")

            if geom_type not in ["point", "polygon", "rectangle", "circle"]:
                raise ValueError(f"Unsupported geometry type: {geom_type}")

            # Handle Polygon / Rectangle
            if geom_type in ["polygon", "rectangle"]:
                if not coordinates or not isinstance(coordinates, list):
                    raise ValueError("Coordinates must be provided for polygon/rectangle")

                # Handle single-ring polygons
                ring = coordinates[0] if isinstance(coordinates[0][0], list) else coordinates
                if len(ring) < 3:
                    raise ValueError("At least 3 points required for polygon/rectangle geometry")

                # Ensure polygon is closed
                if ring[0] != ring[-1]:
                    ring.append(ring[0])

                coordinates = [ring]  # GeoJSON requires list of linear rings
                geometry = {
                    "type": "Polygon",
                    "coordinates": coordinates
                }

            # Handle Circle (store as point + radius in properties)
            elif geom_type == "circle":
                center = geometry.get("center")
                radius = geometry.get("radius")
                if not center or not radius:
                    raise ValueError("Circle requires center and radius")
                geometry = {
                    "type": "Point",
                    "coordinates": [center["longitude"], center["latitude"]],
                    "properties": {"radius": radius}
                }

            # Handle Point
            elif geom_type == "point":
                if not coordinates or not isinstance(coordinates, list) or len(coordinates) != 2:
                    raise ValueError("Point requires [longitude, latitude]")
                geometry = {
                    "type": "Point",
                    "coordinates": coordinates
                }

            # Prepare MongoDB document
            mongo_data = {
                "name": name,
                "description": description or "",
                "type": type,
                "status": status,
                "geometry": geometry  # Proper GeoJSON structure now
            }

            logger.info(f"Inserting into DB: {self.db.db.name}, Collection: geofences")
            result = await self.db.db.geofences.insert_one(mongo_data)
            logger.info(f"Inserted document ID: {result.inserted_id}")

            # Build Pydantic model for response
            geofence_model = Geofence(**{
                **mongo_data,
                "_id": str(result.inserted_id)  # Convert ObjectId → string
            })

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
                # Convert _id to string
                doc["id"] = str(doc.pop("_id"))

                # Keep geometry exactly as in DB
                if "geometry" not in doc or not isinstance(doc["geometry"], dict):
                    doc["geometry"] = {"type": "Polygon", "coordinates": []}  # Default fallback

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
        """Update geofence with proper GeoJSON transformation and unified format"""
        try:
            update_data = {"updated_at": datetime.utcnow()}

            if name is not None:
                update_data["name"] = name

            if description is not None:
                update_data["description"] = description

            if geometry is not None:
                geo_type = geometry.get("type", "").lower()

                if geo_type == "circle":
                    center = geometry.get("center", {})
                    radius = geometry.get("radius")
                    if not center or radius is None:
                        raise ValueError("Circle geometry requires 'center' and 'radius'")

                    update_data["geometry"] = {
                        "type": "Point",
                        "coordinates": [center.get("longitude"), center.get("latitude")],
                        "properties": {"radius": radius}
                    }

                elif geo_type in ["polygon", "rectangle"]:
                    # Support both "points" format and raw "coordinates"
                    points = geometry.get("points")
                    coordinates = geometry.get("coordinates")

                    if points:
                        coords = [[(p["longitude"], p["latitude"]) for p in points]]
                    elif coordinates:
                        coords = coordinates  # Already in [[lon, lat], [lon, lat]...] format
                    else:
                        raise ValueError("Polygon/Rectangle requires 'points' or 'coordinates' with at least 3 points")

                    # Validate we have at least 3 unique points (excluding closing point)
                    unique_points = set((x, y) for ring in coords for x, y in ring)
                    if len(unique_points) < 3:
                        raise ValueError("Polygon/Rectangle requires at least 3 unique points")

                    # Ensure polygon is closed
                    if coords[0][0] != coords[0][-1]:
                        coords[0].append(coords[0][0])

                    update_data["geometry"] = {
                        "type": "Polygon",
                        "coordinates": coords
                    }


            if status is not None:
                update_data["status"] = status.lower()
                update_data["is_active"] = status.lower() == "active"

            if metadata is not None:
                update_data["metadata"] = metadata

            # Convert ID properly for MongoDB
            query_id = ObjectId(geofence_id) if len(geofence_id) == 24 else geofence_id

            # Perform the update
            result = await self.db.db.geofences.update_one(
                {"_id": query_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                # Retrieve the updated document with proper transformations
                return await self.get_geofence_by_id(geofence_id)

            return None

        except Exception as e:
            logger.error(f"Error updating geofence {geofence_id}: {e}")
            logger.exception("Full traceback:")
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