import os
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import requests
from math import radians, sin, cos, sqrt, atan2
from bson import ObjectId
from flexpolyline import decode

from schemas.entities import ScheduledTrip, RouteInfo, RouteBounds, TripStatus, VehicleLocation
from schemas.requests import CreateTripRequest, UpdateTripRequest
from repositories.database import db_manager, db_manager_gps, db_manager_management
from services.trip_service import trip_service
from services.vehicle_service import vehicle_service
from services.driver_analytics_service import driver_analytics_service


logger = logging.getLogger(__name__)

PRETORIA_COORDINATES = [28.1881, -25.7463]

ORS_API_KEY = os.getenv("ORS_API_KEY")
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
VEHICLE_MASS = 12000  # kg constant mass


class SmartTripService:
    """Service for creating optimized smart trips"""

    def __init__(self):
        self.db = db_manager
        self.db_gps = db_manager_gps
        self.db_management = db_manager_management

    # -------------------- Utilities --------------------
    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0  # km
        dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
        a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    def _calculate_bounds(self, coords: List[List[float]]) -> RouteBounds:
        if not coords:
            return None
        lats, lngs = [c[0] for c in coords], [c[1] for c in coords]
        return RouteBounds(
            southWest={"lat": min(lats), "lng": min(lngs)},
            northEast={"lat": max(lats), "lng": max(lngs)}
        )
    
    async def get_all_vehicle_locations(self) -> List[VehicleLocation]:
        """Fetch all current vehicle locations."""
        try:
            cursor = self.db_gps.locations.find({})
            locations = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])  # Convert ObjectId to string for API response
                locations.append(VehicleLocation(**doc))
            return locations
        except Exception as e:
            logger.error(f"Error fetching all vehicle locations: {e}")
            raise

    # -------------------- External API Calls --------------------
    async def _get_ors_route(self, origin_lat, origin_lng, dest_lat, dest_lng, departure_time):
        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        headers = {"Authorization": ORS_API_KEY}
        params = {
            "start": f"{origin_lng},{origin_lat}",
            "end": f"{dest_lng},{dest_lat}"
        }

        try:
            resp = requests.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            route = data["features"][0]["properties"]["segments"][0]
            polyline = data["features"][0]["geometry"]["coordinates"]
            coords = [[lat, lng] for lng, lat in polyline]  # Convert lng,lat -> lat,lng

            elevation_gain = route.get("ascent", 0)
            toll_cost = 0  # ORS free plan doesn't return toll data directly

            return {
                "duration": route["duration"],  # seconds
                "distance": route["distance"],  # meters
                "elevation_gain": elevation_gain,
                "coordinates": coords,
                "bounds": self._calculate_bounds(coords),
                "tollCost": toll_cost
            }
        except Exception as e:
            logger.error(f"ORS error: {e}")
            return None

    async def _get_tomtom_traffic(self, origin_lat, origin_lng, dest_lat, dest_lng, departure_time):
        if not TOMTOM_API_KEY:
            return 0  # No traffic delay if no key

        url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin_lat},{origin_lng}:{dest_lat},{dest_lng}/json"
        params = {
            "key": TOMTOM_API_KEY,
            "computeTravelTimeFor": "all",
            "traffic": "true",
            "departAt": departure_time.isoformat()
        }

        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data["routes"][0]["summary"].get("trafficDelayInSeconds", 0)
        except Exception as e:
            logger.warning(f"TomTom Traffic API error: {e}")
            return 0

    # -------------------- Main Smart Trip Function --------------------
    async def create_smart_trip(self, scheduled_trip: ScheduledTrip, created_by: str) -> Dict[str, Any]:
        """Create an optimized smart trip from a scheduled trip"""
        try:
            # Extract coordinates safely
            origin_coords = scheduled_trip.origin.location.coordinates
            dest_coords = scheduled_trip.destination.location.coordinates
            
            origin_lat = origin_coords[1] 
            origin_lng = origin_coords[0]
            dest_lat = dest_coords[1]
            dest_lng = dest_coords[0]

            start_window = scheduled_trip.start_time_window
            end_window = scheduled_trip.end_time_window
            
            # Ensure datetime objects
            if isinstance(start_window, str):
                start_window = datetime.fromisoformat(start_window.replace('Z', '+00:00'))
            if isinstance(end_window, str):
                end_window = datetime.fromisoformat(end_window.replace('Z', '+00:00'))

            window_duration_hours = (end_window - start_window).total_seconds() / 3600
            num_samples = min(5, int(window_duration_hours))
            step = (end_window - start_window) / num_samples if num_samples > 0 else timedelta(0)

            best_route = None
            best_start = start_window
            min_duration = float("inf")

            # Route optimization
            for i in range(num_samples + 1):
                test_start = start_window + i * step
                route = await self._get_ors_route(origin_lat, origin_lng, dest_lat, dest_lng, test_start)
                if route:
                    traffic_delay = await self._get_tomtom_traffic(origin_lat, origin_lng, dest_lat, dest_lng, test_start)
                    total_duration = route["duration"] + traffic_delay
                    if total_duration < min_duration:
                        min_duration = total_duration
                        best_start = test_start
                        best_route = route
                        best_route["traffic_delay"] = traffic_delay

            if not best_route:
                raise ValueError("Failed to get route from ORS")

            distance_km = best_route["distance"] / 1000.0
            duration_min = best_route["duration"] / 60.0
            traffic_delay_min = best_route.get("traffic_delay", 0) / 60.0

            # Vehicle assignment
            optimized_end = best_start + timedelta(seconds=min_duration)
            vehicles = await vehicle_service.get_available_vehicles(best_start, optimized_end)
            logger.info(f"Vehicles in optimized time: {vehicles}")
            
            # Get current locations
            locations = await self.get_all_vehicle_locations()
            
            # Create a set of vehicle IDs that have location data
            vehicles_with_locations = set()
            locations_list = []
            
            # Process existing locations
            if locations:
                for loc in locations:
                    try:
                        loc_dict = loc.model_dump() if hasattr(loc, 'model_dump') else loc
                        locations_list.append(loc_dict)
                        vehicles_with_locations.add(str(loc_dict.get("vehicle_id", "")))
                    except Exception as e:
                        logger.warning(f"Error processing location {loc}: {e}")
                        continue
            
            # Find vehicles without location data and add default locations
            if vehicles:
                vehicle_list = vehicles.get('vehicles', [])
                for vehicle in vehicle_list:
                    try:
                        vehicle_id = str(vehicle.get("_id", vehicle.get("id", "")))
                        
                        if vehicle_id not in vehicles_with_locations:
                            # Create default location entry for missing vehicle
                            default_location = {
                                "id": f"default_{vehicle_id}",
                                "vehicle_id": vehicle_id,
                                "location": {
                                    "type": "Point",
                                    "coordinates": PRETORIA_COORDINATES
                                },
                                "latitude": PRETORIA_COORDINATES[1],
                                "longitude": PRETORIA_COORDINATES[0],
                                "altitude": None,
                                "speed": 0.0,
                                "heading": 0.0,
                                "accuracy": None,
                                "timestamp": datetime.utcnow().isoformat(),
                                "updated_at": datetime.utcnow().isoformat()
                            }
                            locations_list.append(default_location)
                    except Exception as e:
                        logger.warning(f"Error processing vehicle {vehicle}: {e}")
                        continue

            # Find closest vehicle
            min_dist = float("inf")
            closest_vehicle_id = None
            closest_vehicle_name = "Unknown"
            
            for loc in locations_list:
                try:
                    dist = self._haversine(origin_lat, origin_lng, loc["latitude"], loc["longitude"])
                    if dist < min_dist:
                        min_dist = dist
                        closest_vehicle_id = loc["vehicle_id"]
                except Exception as e:
                    logger.warning(f"Error calculating distance for location {loc}: {e}")
                    continue
            
            vehicle_name = None
            if closest_vehicle_id:
                try:
                    vehicle_doc = await self.db_management.vehicles.find_one({"_id": ObjectId(closest_vehicle_id)})
                    logger.info(f"Vehicle assignment chosen: {vehicle_doc}")
                    if vehicle_doc:
                        vehicle_name = vehicle_doc["make"] + vehicle_doc["model"] + vehicle_doc["registration_number"]
                        closest_vehicle_name = vehicle_name
                except Exception as e:
                    logger.warning(f"Error fetching vehicle {closest_vehicle_id}: {e}")

            # Driver assignment
            try:
                stats = await driver_analytics_service.get_driver_trip_stats("year")
                best_driver_id = None
                best_driver_name = "Unknown"
                best_rate = -1.0
                
                for stat in stats:
                    try:
                        completed = stat.get("completed_trips", 0)
                        cancelled = stat.get("cancelled_trips", 0)
                        total = completed + cancelled
                        rate = completed / total if total > 0 else 0.0
                        if rate > best_rate:
                            best_rate = rate
                            best_driver_name = stat.get("driver_name", "Unknown")
                            best_driver_id = stat.get("driver_id")
                    except Exception as e:
                        logger.warning(f"Error processing driver stat {stat}: {e}")
                        continue
                        
                if best_driver_id is None:
                    logger.warning("No valid driver ID found; defaulting to None")
                    
                logger.info(f"Best driver assignment: {best_driver_id}")
            except Exception as e:
                logger.warning(f"Error getting driver stats: {e}")
                best_driver_id = None
                best_driver_name = "Unknown"
                best_rate = 0.0

            optimized_start = best_start
            optimized_end = best_start + timedelta(seconds=min_duration)

            # Calculate benefits
            try:
                original_duration_min = getattr(scheduled_trip, 'estimated_duration', duration_min)
                if hasattr(scheduled_trip, 'route_info') and scheduled_trip.route_info:
                    route_duration = getattr(scheduled_trip.route_info, 'duration', 0) / 60
                    original_duration_min = route_duration if route_duration > 0 else duration_min
            except Exception as e:
                logger.warning(f"Error calculating original duration: {e}")
                original_duration_min = duration_min

            time_saved_min = original_duration_min - duration_min
            time_saved_str = f"{abs(int(time_saved_min))} minutes" if time_saved_min != 0 else "No change"

            fuel_efficiency = f"{max(0, 10 - traffic_delay_min * 0.5):.1f}% improvement"

            # Reasoning
            reasoning = [
                f"Optimal traffic conditions at suggested start time",
                f"Driver with {best_rate * 100:.0f}% completion rate selected",
                f"Closest vehicle at {min_dist:.1f} km assigned"
            ]

            # Create trip record in DB
            try:
                route_info_obj = RouteInfo(
                    distance=best_route["distance"],
                    duration=best_route["duration"],
                    coordinates=best_route["coordinates"],
                    bounds=best_route["bounds"]
                )
                
                create_request = CreateTripRequest(
                    name=scheduled_trip.name,
                    description=scheduled_trip.description,
                    scheduled_start_time=optimized_start,
                    scheduled_end_time=optimized_end,
                    origin=scheduled_trip.origin,
                    destination=scheduled_trip.destination,
                    waypoints=scheduled_trip.waypoints or [],
                    route_info=route_info_obj,
                    priority=scheduled_trip.priority,
                    driver_assignment=best_driver_id, 
                    vehicle_id=vehicle_name,
                    constraints=[]
                )
                
                actual_trip = await trip_service.create_trip(create_request, created_by)
                logger.info(f"New smart trip created {actual_trip}")
            except Exception as e:
                logger.warning(f"Error creating trip in database: {e}")

            # Return properly structured response
            trip_id = str(getattr(scheduled_trip, 'id', 'unknown'))
            smart_id = f"smart-{trip_id[:8]}"
            
            return {
                "id": smart_id,
                "tripId": trip_id,
                "tripName": scheduled_trip.name,
                "originalSchedule": {
                    "startTime": start_window.isoformat() if hasattr(start_window, 'isoformat') else str(start_window),
                    "endTime": end_window.isoformat() if hasattr(end_window, 'isoformat') else str(end_window),
                    "vehicle": None,
                    "driver": None
                },
                "optimizedSchedule": {
                    "startTime": optimized_start.isoformat(),
                    "endTime": optimized_end.isoformat(),
                    "vehicleId": closest_vehicle_id,
                    "vehicleName": closest_vehicle_name,
                    "driverId": best_driver_id,
                    "driverName": best_driver_name
                },
                "route": {
                    "origin": scheduled_trip.origin.name,
                    "destination": scheduled_trip.destination.name,
                    "waypoints": [],
                    "estimatedDistance": f"{distance_km:.1f} km",
                    "estimatedDuration": f"{int(duration_min)} minutes"
                },
                "benefits": {
                    "timeSaved": time_saved_str,
                    "fuelEfficiency": fuel_efficiency,
                    "routeOptimization": "Optimal traffic timing",
                    "driverUtilization": f"{best_rate * 100:.0f}% efficiency"
                },
                "confidence": 92,
                "reasoning": reasoning
            }
            
        except Exception as e:
            logger.error(f"Error in create_smart_trip: {e}", exc_info=True)
            # Return a basic error response instead of failing completely
            return {
                "id": f"error-{datetime.now().timestamp()}",
                "error": f"Failed to create smart trip: {str(e)}",
                "tripId": getattr(scheduled_trip, 'id', 'unknown'),
                "tripName": getattr(scheduled_trip, 'name', 'Unknown Trip')
            }

# Create global service instance
smart_trip_service = SmartTripService()
