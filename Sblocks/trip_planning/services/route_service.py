from typing import List, Optional, Dict, Any, Tuple
from bson import ObjectId
from datetime import datetime, timedelta
from ..models.models import Route, RouteOptimization, Location, RouteStatus
from ..database import get_routes_collection
from ..messaging.rabbitmq_client import RabbitMQClient
from ..utils.route_optimization import RouteOptimizer
import math


class RouteService:
    def __init__(self, messaging_client: RabbitMQClient):
        self.messaging_client = messaging_client
        self.routes_collection = get_routes_collection()
        self.route_optimizer = RouteOptimizer()

    async def create_route(self, route_data: Dict[str, Any]) -> Route:
        """Create a new route"""
        # Calculate total distance and estimated duration
        if "waypoints" in route_data and len(route_data["waypoints"]) >= 2:
            total_distance = self._calculate_total_distance(route_data["waypoints"])
            estimated_duration = self._estimate_duration(total_distance)
            
            route_data.update({
                "total_distance": total_distance,
                "estimated_duration": estimated_duration
            })
        
        route = Route(**route_data)
        
        # Insert into database
        result = await self.routes_collection.insert_one(route.dict(by_alias=True))
        route.id = result.inserted_id
        
        # Publish route created event
        await self.messaging_client.publish_event(
            "route.created",
            {
                "route_id": str(route.id),
                "origin": f"{route.origin.latitude},{route.origin.longitude}",
                "destination": f"{route.destination.latitude},{route.destination.longitude}",
                "total_distance": route.total_distance,
                "estimated_duration": route.estimated_duration,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return route

    async def get_route_by_id(self, route_id: str) -> Optional[Route]:
        """Get route by ID"""
        route_data = await self.routes_collection.find_one(
            {"_id": ObjectId(route_id)}
        )
        return Route(**route_data) if route_data else None

    async def get_routes(
        self,
        status: Optional[RouteStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Route]:
        """Get routes with optional filters"""
        query = {}
        
        if status:
            query["status"] = status.value
            
        cursor = self.routes_collection.find(query).skip(skip).limit(limit)
        routes = []
        
        async for route_data in cursor:
            routes.append(Route(**route_data))
            
        return routes

    async def optimize_route(
        self,
        origin: Location,
        destination: Location,
        waypoints: Optional[List[Location]] = None,
        vehicle_type: Optional[str] = None
    ) -> RouteOptimization:
        """Optimize route using external routing service"""
        try:
            # Use route optimizer to get optimized route
            optimization_result = await self.route_optimizer.optimize_route(
                origin=origin,
                destination=destination,
                waypoints=waypoints or [],
                vehicle_type=vehicle_type
            )
            
            return optimization_result
            
        except Exception as e:
            # Fallback to simple route calculation
            waypoints_list = waypoints or []
            all_points = [origin] + waypoints_list + [destination]
            
            total_distance = self._calculate_total_distance(all_points)
            estimated_duration = self._estimate_duration(total_distance)
            
            return RouteOptimization(
                optimized_waypoints=waypoints_list,
                total_distance=total_distance,
                estimated_duration=estimated_duration,
                optimization_method="fallback_calculation"
            )

    async def update_route(self, route_id: str, update_data: Dict[str, Any]) -> Optional[Route]:
        """Update route information"""
        update_data["updated_at"] = datetime.utcnow()
        
        # Recalculate distance and duration if waypoints changed
        if "waypoints" in update_data:
            total_distance = self._calculate_total_distance(update_data["waypoints"])
            estimated_duration = self._estimate_duration(total_distance)
            update_data.update({
                "total_distance": total_distance,
                "estimated_duration": estimated_duration
            })
        
        result = await self.routes_collection.update_one(
            {"_id": ObjectId(route_id)},
            {"$set": update_data}
        )
        
        if result.modified_count:
            updated_route = await self.get_route_by_id(route_id)
            
            # Publish route updated event
            await self.messaging_client.publish_event(
                "route.updated",
                {
                    "route_id": route_id,
                    "updated_fields": list(update_data.keys()),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return updated_route
        return None

    async def update_route_status(self, route_id: str, status: RouteStatus) -> bool:
        """Update route status"""
        result = await self.routes_collection.update_one(
            {"_id": ObjectId(route_id)},
            {
                "$set": {
                    "status": status.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count:
            # Publish status change event
            await self.messaging_client.publish_event(
                "route.status_changed",
                {
                    "route_id": route_id,
                    "new_status": status.value,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
        return False

    async def calculate_route_alternatives(
        self,
        origin: Location,
        destination: Location,
        max_alternatives: int = 3
    ) -> List[RouteOptimization]:
        """Calculate alternative routes"""
        alternatives = []
        
        try:
            # Get multiple route options from optimizer
            optimization_results = await self.route_optimizer.get_route_alternatives(
                origin=origin,
                destination=destination,
                max_alternatives=max_alternatives
            )
            
            alternatives.extend(optimization_results)
            
        except Exception:
            # Fallback: create simple direct route
            direct_distance = self._calculate_distance(origin, destination)
            direct_duration = self._estimate_duration(direct_distance)
            
            alternatives.append(RouteOptimization(
                optimized_waypoints=[],
                total_distance=direct_distance,
                estimated_duration=direct_duration,
                optimization_method="direct_route"
            ))
        
        return alternatives

    async def find_routes_by_area(
        self,
        center_lat: float,
        center_lng: float,
        radius_km: float
    ) -> List[Route]:
        """Find routes within a geographical area"""
        # MongoDB geospatial query for routes within radius
        query = {
            "$or": [
                {
                    "origin": {
                        "$geoWithin": {
                            "$centerSphere": [
                                [center_lng, center_lat],
                                radius_km / 6371  # Earth radius in km
                            ]
                        }
                    }
                },
                {
                    "destination": {
                        "$geoWithin": {
                            "$centerSphere": [
                                [center_lng, center_lat],
                                radius_km / 6371
                            ]
                        }
                    }
                }
            ]
        }
        
        cursor = self.routes_collection.find(query)
        routes = []
        
        async for route_data in cursor:
            routes.append(Route(**route_data))
            
        return routes

    async def get_route_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get route usage analytics"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
            
        pipeline = [
            {
                "$match": {
                    "created_at": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            },
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_distance": {"$avg": "$total_distance"},
                    "avg_duration": {"$avg": "$estimated_duration"},
                    "total_distance": {"$sum": "$total_distance"}
                }
            }
        ]
        
        analytics = {}
        async for result in self.routes_collection.aggregate(pipeline):
            analytics[result["_id"]] = {
                "count": result["count"],
                "average_distance": result["avg_distance"],
                "average_duration": result["avg_duration"],
                "total_distance": result["total_distance"]
            }
            
        return analytics

    def _calculate_distance(self, point1: Location, point2: Location) -> float:
        """Calculate distance between two points using Haversine formula"""
        lat1, lon1 = math.radians(point1.latitude), math.radians(point1.longitude)
        lat2, lon2 = math.radians(point2.latitude), math.radians(point2.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in kilometers
        earth_radius = 6371
        distance = earth_radius * c
        
        return distance

    def _calculate_total_distance(self, waypoints: List[Location]) -> float:
        """Calculate total distance for a route with multiple waypoints"""
        if len(waypoints) < 2:
            return 0.0
            
        total_distance = 0.0
        for i in range(len(waypoints) - 1):
            total_distance += self._calculate_distance(waypoints[i], waypoints[i + 1])
            
        return total_distance

    def _estimate_duration(self, distance_km: float, avg_speed_kmh: float = 50.0) -> int:
        """Estimate duration in minutes based on distance and average speed"""
        if distance_km <= 0:
            return 0
        return int((distance_km / avg_speed_kmh) * 60)

    async def delete_route(self, route_id: str) -> bool:
        """Delete a route"""
        result = await self.routes_collection.update_one(
            {"_id": ObjectId(route_id)},
            {
                "$set": {
                    "status": RouteStatus.INACTIVE.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count:
            await self.messaging_client.publish_event(
                "route.deleted",
                {
                    "route_id": route_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
        return False
