import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
import asyncio
import traceback
import aiohttp
import math
import random
from math import radians, sin, cos, sqrt, atan2
from bson import ObjectId
from flexpolyline import decode

from schemas.entities import ScheduledTrip, RouteInfo, RouteBounds, TripStatus, VehicleLocation, SmartTrip, TrafficCondition, RouteRecommendation, TrafficType, Trip, TripPriority
from schemas.requests import CreateTripRequest, UpdateTripRequest, DriverAvailabilityRequest
from repositories.database import db_manager, db_manager_gps, db_manager_management
from services.trip_service import trip_service
from services.vehicle_service import vehicle_service
from services.notification_service import notification_service
from services.driver_service import driver_service
from services.driver_analytics_service import driver_analytics_service


logger = logging.getLogger(__name__)

PRETORIA_COORDINATES = [28.1881, -25.7463]

ORS_API_KEY = os.getenv("ORS_API_KEY")
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY")
VEHICLE_MASS = 12000  # kg constant mass

# Traffic monitoring configuration
TRAFFIC_CHECK_INTERVAL = 300  # Check traffic every 5 minutes
HIGH_TRAFFIC_THRESHOLD = 0.3  # 30% increase in travel time indicates high traffic
MINIMUM_TIME_SAVINGS = 600  # Only recommend if saves at least 10 minutes
ROUTE_DEVIATION_THRESHOLD = 0.5  # Only recommend if new route is significantly different


class SmartTripService:
    """Service for creating optimized smart trips with traffic monitoring"""

    def __init__(self):
        self.db = db_manager
        self.db_gps = db_manager_gps
        self.db_management = db_manager_management
        self.active_traffic_monitoring = False
        self.route_recommendations: Dict[str, RouteRecommendation] = {}
        self.last_traffic_check: Dict[str, datetime] = {}

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

    def _calculate_route_similarity(self, route1_coords: List[List[float]], 
                                route2_coords: List[List[float]]) -> float:
        """Calculate similarity between two routes (0-1, where 1 is identical)"""
        if not route1_coords or not route2_coords:
            return 0.0
        
        # Increase sample size for better comparison
        sample_size = min(20, len(route1_coords), len(route2_coords))  # Increased from 10
        
        # Handle different route lengths better
        route1_step = max(1, len(route1_coords) // sample_size)
        route2_step = max(1, len(route2_coords) // sample_size)
        
        route1_samples = [route1_coords[i * route1_step] for i in range(sample_size)]
        route2_samples = [route2_coords[i * route2_step] for i in range(sample_size)]
        
        # Calculate average distance between corresponding points
        total_distance = 0
        for i in range(min(len(route1_samples), len(route2_samples))):
            distance = self._haversine(
                route1_samples[i][0], route1_samples[i][1],
                route2_samples[i][0], route2_samples[i][1]
            )
            total_distance += distance
        
        avg_distance = total_distance / sample_size
        # Make similarity calculation more lenient (increased from 5.0 to 10.0)
        similarity = max(0, 1 - (avg_distance / 10.0))
        
        logger.debug(f"Route similarity: avg_distance={avg_distance:.2f}km, similarity={similarity:.2f}")
        return similarity
    
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
    async def _get_ors_route(self, origin_lat, origin_lng, dest_lat, dest_lng, departure_time=None):
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
    
    async def _get_alternative_routes_mapbox(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        current_location_lat: float = None,
        current_location_lng: float = None
    ) -> List[dict]:
        """
        Get multiple alternative routes using Mapbox Directions API with traffic awareness.
        Returns a list of routes with distance, duration, and coordinates.
        """
        try:
            # Starting point: current location or origin
            if current_location_lat and current_location_lng:
                start_lat, start_lng = current_location_lat, current_location_lng
            else:
                start_lat, start_lng = origin_lat, origin_lng

            # Build the request URL
            coordinates = f"{start_lng},{start_lat};{dest_lng},{dest_lat}"
            url = f"https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{coordinates}"

            params = {
                "alternatives": "true",          # Request alternative routes
                "geometries": "geojson",         # Return coordinates in GeoJSON format
                "overview": "full",              # Full route geometry
                "steps": "false",                 # We only need the full route, not step-by-step
                "access_token": MAPBOX_API_KEY
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as resp:
                    resp.raise_for_status()
                    data = await resp.json()

            routes = []
            for i, route in enumerate(data.get("routes", [])):
                try:
                    coords = route["geometry"]["coordinates"]
                    coords_latlng = [[lat, lng] for lng, lat in coords]  # Convert order

                    route_data = {
                        "duration": route["duration"],  # seconds
                        "distance": route["distance"],  # meters
                        "coordinates": coords_latlng,
                        "bounds": self._calculate_bounds(coords_latlng),
                        "tollCost": 0,
                        "route_index": i
                    }
                    routes.append(route_data)
                    logger.info(f"Mapbox Route {i}: {route_data['distance']/1000:.1f}km, {route_data['duration']/60:.1f}min")

                except Exception as e:
                    logger.warning(f"Error processing Mapbox route {i}: {e}")
                    continue

            logger.info(f"Mapbox returned {len(routes)} alternative routes")
            return routes

        except Exception as e:
            logger.error(f"Error getting Mapbox alternative routes: {e}")
            return []

    async def _get_alternative_routes(self, origin_lat, origin_lng, dest_lat, dest_lng, 
                                    current_location_lat=None, current_location_lng=None):
        """Get multiple alternative routes, optionally from current location"""
        if current_location_lat and current_location_lng:
            start_lat, start_lng = current_location_lat, current_location_lng
        else:
            start_lat, start_lng = origin_lat, origin_lng

        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        headers = {"Authorization": ORS_API_KEY}
        
        # Updated parameters for better alternative route generation
        params = {
            "start": f"{start_lng},{start_lat}",
            "end": f"{dest_lng},{dest_lat}",
            "alternative_routes": "3",  # Maximum is 3 for ORS
            "radiuses": "1000",  # Increased from 1000 to 5000 for more flexibility
            "continue_straight": "false",  # Allow route deviation
            #"avoid_features": "",  # Don't avoid anything initially
        }

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            logger.info(f"ORS returned {len(data.get('features', []))} route features")
            
            routes = []
            for i, feature in enumerate(data.get("features", [])):
                try:
                    route = feature["properties"]["segments"][0]
                    polyline = feature["geometry"]["coordinates"]
                    coords = [[lat, lng] for lng, lat in polyline]
                    
                    route_data = {
                        "duration": route["duration"],
                        "distance": route["distance"],
                        "coordinates": coords,
                        "bounds": self._calculate_bounds(coords),
                        "elevation_gain": route.get("ascent", 0),
                        "tollCost": 0,
                        "route_index": i  # Add index for debugging
                    }
                    routes.append(route_data)
                    logger.info(f"Route {i}: {route_data['distance']/1000:.1f}km, {route_data['duration']/60:.1f}min")
                    
                except Exception as e:
                    logger.warning(f"Error processing route feature {i}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(routes)} alternative routes")
            return routes
            
        except Exception as e:
            logger.error(f"Error getting alternative routes: {e}")
            return []
    
    async def _get_tomtom_traffic_test_mode(self):
        base_duration = 3600  # 1 hour base travel time
        return {
            "live_traffic_delay": base_duration * 1.5,  # 150% delay
            "historical_traffic_delay": base_duration * 0.2,
            "traffic_ratio": 2.5,  # Heavy traffic
            "no_traffic_duration": base_duration,
            "live_traffic_duration": base_duration * 2.5
        }

    async def _get_tomtom_traffic(self, origin_lat, origin_lng, dest_lat, dest_lng, departure_time=None):
        if not TOMTOM_API_KEY:
            return 0  # No traffic delay if no key

        url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin_lat},{origin_lng}:{dest_lat},{dest_lng}/json"
        params = {
            "key": TOMTOM_API_KEY,
            "computeTravelTimeFor": "all",
            "traffic": "true"
        }
        
        if departure_time:
            params["departAt"] = departure_time.isoformat()

        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            summary = data["routes"][0]["summary"]
            logger.info(f"Traffic summary {summary}")
            live_traffic_time = summary.get("liveTrafficIncidentsTravelTimeInSeconds", 0)
            historical_traffic_time = summary.get("historicalTrafficTravelTimeInSeconds", 0)
            no_traffic_time = summary.get("noTrafficTravelTimeInSeconds", 0)
            
            return {
                "live_traffic_delay": live_traffic_time - no_traffic_time,
                "historical_traffic_delay": historical_traffic_time - no_traffic_time,
                "traffic_ratio": live_traffic_time / no_traffic_time if no_traffic_time > 0 else 1.0,
                "no_traffic_duration": no_traffic_time,
                "live_traffic_duration": live_traffic_time
            }
        except Exception as e:
            logger.warning(f"TomTom Traffic API error: {e}")
            return {"live_traffic_delay": 0, "historical_traffic_delay": 0, "traffic_ratio": 1.0}
        
    
    def _is_reasonable_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> bool:
        """Check if distance between two points is reasonable for routing"""
        distance_km = self._haversine(lat1, lng1, lat2, lng2)
        return 5 <= distance_km <= 2000  # Between 5km and 2000km
    
    def _generate_intermediate_waypoints(
        self,
        current_lat: float,
        current_lng: float,
        dest_lat: float,
        dest_lng: float,
        num_waypoints: int = 3
    ) -> List[Tuple[float, float]]:
        """Generate intermediate waypoints along the route for better alternatives"""
        
        waypoints = []
        total_distance = self._haversine(current_lat, current_lng, dest_lat, dest_lng)
        
        # For very long routes (>500km), use fewer, more strategic waypoints
        if total_distance > 500:
            num_waypoints = min(2, num_waypoints)
            deviation_factor = 0.05  # Smaller deviation for long routes
        else:
            deviation_factor = 0.15  # Larger deviation for shorter routes
        
        logger.info(f"Route distance: {total_distance:.1f}km, using {num_waypoints} waypoints with {deviation_factor*100:.1f}% deviation")
        
        # Generate waypoints at regular intervals along the route
        for i in range(1, num_waypoints + 1):
            progress = i / (num_waypoints + 1)  # 0.25, 0.5, 0.75 for 3 waypoints
            
            # Base waypoint along the direct line
            base_lat = current_lat + (dest_lat - current_lat) * progress
            base_lng = current_lng + (dest_lng - current_lng) * progress
            
            # Create perpendicular offset for route deviation
            bearing = math.atan2(dest_lng - current_lng, dest_lat - current_lat)
            perp_bearing = bearing + math.pi / 2  # 90 degrees offset
            
            # Multiple deviation strategies
            strategies = [
                (deviation_factor, "right"),
                (-deviation_factor, "left"),
                (deviation_factor * 0.5, "slight_right"),
                (-deviation_factor * 0.5, "slight_left")
            ]
            
            for deviation, direction in strategies[:2]:  # Only use 2 main strategies to avoid too many requests
                offset_distance = total_distance * abs(deviation)
                
                # Convert offset to lat/lng (approximation)
                lat_offset = math.cos(perp_bearing) * offset_distance / 111.0  # Rough conversion
                lng_offset = math.sin(perp_bearing) * offset_distance / (111.0 * math.cos(math.radians(base_lat)))
                
                waypoint_lat = base_lat + lat_offset * (1 if deviation > 0 else -1)
                waypoint_lng = base_lng + lng_offset * (1 if deviation > 0 else -1)
                
                # Validate the waypoint
                if (self._is_reasonable_distance(current_lat, current_lng, waypoint_lat, waypoint_lng) and 
                    self._is_reasonable_distance(waypoint_lat, waypoint_lng, dest_lat, dest_lng)):
                    waypoints.append((waypoint_lat, waypoint_lng, f"intermediate_{direction}_{i}"))
        
        return waypoints
    
    def _generate_major_city_waypoints(
        self,
        current_lat: float,
        current_lng: float,
        dest_lat: float,
        dest_lng: float
    ) -> List[Tuple[float, float]]:
        """Generate waypoints through major cities/towns that might provide alternative routes"""
        
        # Major South African cities and towns (lat, lng, name)
        major_cities = [
            (-26.2041, 28.0473, "johannesburg"),    # Johannesburg
            (-25.7479, 28.2293, "pretoria"),        # Pretoria  
            (-29.8587, 31.0218, "durban"),          # Durban
            (-33.9249, 18.4241, "cape_town"),       # Cape Town
            (-26.1596, 27.9467, "soweto"),          # Soweto
            (-29.1216, 26.2147, "bloemfontein"),    # Bloemfontein
            (-28.7282, 24.7499, "kimberley"),       # Kimberley
            (-25.8740, 24.6768, "rustenburg"),      # Rustenburg
            (-26.7056, 27.1007, "potchefstroom"),   # Potchefstroom
        ]
        
        waypoints = []
        route_distance = self._haversine(current_lat, current_lng, dest_lat, dest_lng)
        
        for city_lat, city_lng, city_name in major_cities:
            # Check if city is reasonably positioned for a detour
            dist_to_city = self._haversine(current_lat, current_lng, city_lat, city_lng)
            city_to_dest = self._haversine(city_lat, city_lng, dest_lat, dest_lng)
            
            # Only consider cities that don't add too much extra distance
            total_via_city = dist_to_city + city_to_dest
            detour_ratio = total_via_city / route_distance
            
            if 1.1 <= detour_ratio <= 1.8:  # 10% to 80% detour acceptable
                waypoints.append((city_lat, city_lng, f"via_{city_name}"))
                logger.info(f"Added city waypoint: {city_name} (detour ratio: {detour_ratio:.2f})")
        
        return waypoints[:3]  # Limit to 3 city waypoints
    
    async def _get_route_via_waypoint_safe(
        self,
        start_lat: float, start_lng: float,
        waypoint_lat: float, waypoint_lng: float,
        dest_lat: float, dest_lng: float,
        waypoint_name: str = "waypoint"
    ) -> Optional[dict]:
        """Safely get route via waypoint with better error handling"""
        
        try:
            logger.info(f"Attempting route via {waypoint_name}: {waypoint_lat:.4f}, {waypoint_lng:.4f}")
            
            # Validate distances first
            dist1 = self._haversine(start_lat, start_lng, waypoint_lat, waypoint_lng)
            dist2 = self._haversine(waypoint_lat, waypoint_lng, dest_lat, dest_lng)
            
            if dist1 < 5 or dist2 < 5:  # Too close
                logger.warning(f"Waypoint {waypoint_name} too close to start or destination")
                return None
            
            if dist1 > 1000 or dist2 > 1000:  # Too far for intermediate waypoint
                logger.warning(f"Waypoint {waypoint_name} too far from route")
                return None
            
            # Try to get both legs of the route
            leg1 = await self._get_ors_route(start_lat, start_lng, waypoint_lat, waypoint_lng)
            if not leg1:
                logger.warning(f"Failed to get route to waypoint {waypoint_name}")
                return None
            
            leg2 = await self._get_ors_route(waypoint_lat, waypoint_lng, dest_lat, dest_lng)
            if not leg2:
                logger.warning(f"Failed to get route from waypoint {waypoint_name} to destination")
                return None
            
            # Combine routes
            combined_coords = leg1["coordinates"] + leg2["coordinates"][1:]
            total_distance = leg1["distance"] + leg2["distance"]
            total_duration = leg1["duration"] + leg2["duration"]
            
            route = {
                "duration": total_duration,
                "distance": total_distance,
                "coordinates": combined_coords,
                "bounds": self._calculate_bounds(combined_coords),
                "waypoint": (waypoint_lat, waypoint_lng),
                "waypoint_name": waypoint_name,
                "elevation_gain": leg1.get("elevation_gain", 0) + leg2.get("elevation_gain", 0),
                "tollCost": 0
            }
            
            logger.info(f"Successfully created route via {waypoint_name}: "
                       f"{total_distance/1000:.1f}km, {total_duration/60:.1f}min")
            return route
            
        except Exception as e:
            logger.warning(f"Error getting route via waypoint {waypoint_name}: {e}")
            return None
    
    async def _generate_improved_alternative_routes(
        self,
        current_lat: float,
        current_lng: float,
        dest_lat: float,
        dest_lng: float,
        num_routes: int = 5
    ) -> List[dict]:
        """Generate improved alternative routes with better waypoint strategies"""
        
        logger.info(f"Generating improved alternative routes from ({current_lat:.4f}, {current_lng:.4f}) "
                   f"to ({dest_lat:.4f}, {dest_lng:.4f})")
        
        alternative_routes = []
        
        # 1. Get standard API routes first
        try:
            mapbox_routes = await self._get_alternative_routes_mapbox(
                None, None, dest_lat, dest_lng, current_lat, current_lng
            )
            
            # Only add routes that are actually different and reasonable
            for i, route in enumerate(mapbox_routes[:2]):
                if route.get("distance", 0) > 1000:  # At least 1km
                    route["route_type"] = f"mapbox_standard_{i}"
                    route["route_index"] = len(alternative_routes)
                    alternative_routes.append(route)
                    
        except Exception as e:
            logger.warning(f"Error getting Mapbox routes: {e}")
        
        # 2. Try ORS alternative routes as backup
        try:
            ors_routes = await self._get_alternative_routes(
                None, None, dest_lat, dest_lng, current_lat, current_lng
            )
            
            for i, route in enumerate(ors_routes[:2]):
                if route.get("distance", 0) > 1000 and len(alternative_routes) < 3:
                    route["route_type"] = f"ors_standard_{i}"
                    route["route_index"] = len(alternative_routes)
                    alternative_routes.append(route)
                    
        except Exception as e:
            logger.warning(f"Error getting ORS routes: {e}")
        
        # 3. Generate strategic waypoint routes only if we need more
        if len(alternative_routes) < num_routes:
            logger.info(f"Need more routes, generating waypoint-based alternatives")
            
            # Generate intermediate waypoints
            intermediate_waypoints = self._generate_intermediate_waypoints(
                current_lat, current_lng, dest_lat, dest_lng, 3
            )
            
            # Generate city waypoints for longer routes
            route_distance = self._haversine(current_lat, current_lng, dest_lat, dest_lng)
            if route_distance > 100:  # Only for routes longer than 100km
                city_waypoints = self._generate_major_city_waypoints(
                    current_lat, current_lng, dest_lat, dest_lng
                )
                intermediate_waypoints.extend(city_waypoints)
            
            logger.info(f"Generated {len(intermediate_waypoints)} strategic waypoints")
            
            # Try each waypoint, but limit API calls
            for waypoint_lat, waypoint_lng, waypoint_name in intermediate_waypoints[:5]:
                if len(alternative_routes) >= num_routes:
                    break
                
                waypoint_route = await self._get_route_via_waypoint_safe(
                    current_lat, current_lng,
                    waypoint_lat, waypoint_lng,
                    dest_lat, dest_lng,
                    waypoint_name
                )
                
                if waypoint_route:
                    waypoint_route["route_type"] = f"waypoint_{waypoint_name}"
                    waypoint_route["route_index"] = len(alternative_routes)
                    alternative_routes.append(waypoint_route)
        
        logger.info(f"Generated {len(alternative_routes)} total alternative routes")
        
        # Sort routes by duration to prioritize faster routes
        if alternative_routes:
            alternative_routes.sort(key=lambda r: r.get("duration", float('inf')))
        
        return alternative_routes

    # -------------------- Traffic Monitoring Functions --------------------
    async def _get_current_trip_location(self, vehicle_id: str) -> Optional[Tuple[float, float]]:
        """Get current location of a vehicle on an active trip"""
        try:
            location = await self.db_gps.locations.find_one({"vehicle_id": vehicle_id})
            if location:
                return (location["latitude"], location["longitude"])
            return None
        except Exception as e:
            logger.error(f"Error getting current location for vehicle {vehicle_id}: {e}")
            return None

    async def _analyze_route_traffic(self, trip_id, vehicle_id) -> TrafficCondition:
        """Analyze traffic conditions for a specific trip's route"""
        try:
            # vehicle_id, trip 
            if not vehicle_id:
                return None

            # Get current vehicle location
            current_location = await self._get_current_trip_location(vehicle_id)
            if not current_location:
                return None

            # Get destination coordinates
            destination =  await trip_service.get_trip_destination(trip_id)
            dest_location = destination["location"]
            dest_coords = dest_location["coordinates"]
            
            if len(dest_coords) < 2:
                return None

            dest_lat = dest_coords[1]
            dest_lng = dest_coords[0]
            current_lat, current_lng = current_location

            # Get traffic information for current location to destination
            traffic_info = await self._get_tomtom_traffic_test_mode()
            #(
            #    current_lat, current_lng, dest_lat, dest_lng
            #)

            traffic_ratio = traffic_info.get("traffic_ratio", 1.0)
            
            # Determine traffic severity
            if traffic_ratio >= 2.0:
                severity = "severe"
            elif traffic_ratio >= 1.5:
                severity = "heavy"
            elif traffic_ratio >= 1.3:
                severity = "moderate"
            else:
                severity = "light"

            return TrafficCondition(
                segment_id=f"{trip_id}-current-to-dest",
                current_duration=traffic_info.get("live_traffic_duration", 0),
                free_flow_duration=traffic_info.get("no_traffic_duration", 0),
                traffic_ratio=traffic_ratio,
                severity=severity,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"Error analyzing traffic for trip {trip_id}: {e}")
            return None

    async def get_improved_alternative_routes(
        self,
        origin_lat: float, origin_lng: float,
        dest_lat: float, dest_lng: float,
        current_location_lat: float = None,
        current_location_lng: float = None,
        num_routes: int = 5
    ) -> List[dict]:
        """Get improved alternative routes with better waypoint logic"""
        
        start_lat = current_location_lat if current_location_lat else origin_lat
        start_lng = current_location_lng if current_location_lng else origin_lng
        
        alternative_routes = await self._generate_improved_alternative_routes(
            start_lat, start_lng, dest_lat, dest_lng, num_routes
        )
        
        return alternative_routes


    # Updated enhanced route recommendation method
    async def generate_improved_route_recommendation(
        self,
        trip: Trip,
        traffic_condition: TrafficCondition
    ) -> Optional[RouteRecommendation]:
        """Generate route recommendation with improved alternative route logic"""
        try:

            vehicle_id = trip.vehicle_id
            if not vehicle_id:
                logger.warning(f"No vehicle_id for trip {trip.id}")
                return None

            current_location = await self._get_current_trip_location(vehicle_id)
            if not current_location:
                logger.warning(f"No current location for vehicle {vehicle_id}")
                return None
            current_lat, current_lng = current_location

            if not trip.destination or not trip.destination.location or not trip.destination.location.coordinates:
                logger.warning(f"Destination coordinates missing for trip {trip.id}")
                return None

            dest_coords = trip.destination.location.coordinates
            if len(dest_coords) < 2:
                logger.warning(f"Invalid destination coordinates for trip {trip.id}: {dest_coords}")
                return None
            dest_lng, dest_lat = dest_coords[0], dest_coords[1]

            # Use improved route generation
#            alternative_routes = await self.get_improved_alternative_routes(
#               None, None, dest_lat, dest_lng, current_lat, current_lng, num_routes=5
#            )

            alternative_routes = await self._generate_improved_alternative_routes(
                current_lat,current_lng,dest_lat,dest_lng, num_routes=5
            )
            
            logger.info(f"Generated {len(alternative_routes)} improved alternative routes")
            if not alternative_routes:
                return None

            # Evaluate routes with better logic
            best_route = None
            best_savings = 0
            current_route_info = trip.route_info.dict() if trip.route_info else None
            current_duration = traffic_condition.current_duration
            
            # Be more lenient with minimum time savings for severe traffic
            min_savings = MINIMUM_TIME_SAVINGS * 0.3 if traffic_condition.severity == TrafficType.SEVERE else MINIMUM_TIME_SAVINGS * 0.5

            for alt_route in alternative_routes:
                # Get traffic info for this route
                alt_traffic = await self._get_tomtom_traffic(current_lat, current_lng, dest_lat, dest_lng)
                alt_duration = alt_route["duration"] + alt_traffic.get("live_traffic_delay", 0)
                time_savings = current_duration - alt_duration

                # Adjusted similarity checking
                route_type = alt_route.get("route_type", "standard")
                similarity_threshold = 0.7  # More lenient threshold
                
                if "waypoint" in route_type:
                    similarity_threshold = 0.85  # Even more lenient for waypoint routes

                # Check route similarity
                passes_similarity = True
                if current_route_info and current_route_info.get("coordinates"):
                    similarity = self._calculate_route_similarity(
                        current_route_info["coordinates"],
                        alt_route["coordinates"]
                    )
                    logger.info(f"Route {alt_route.get('route_index', 0)} ({route_type}): "
                            f"similarity={similarity:.2f}, threshold={similarity_threshold:.2f}, "
                            f"saves {int(time_savings/60)}min")
                    
                    if similarity > similarity_threshold:
                        logger.info(f"Route too similar, skipping")
                        passes_similarity = False
                else:
                    logger.info(f"No current route to compare, accepting route {route_type}")

                # Select best route with more lenient criteria
                if (passes_similarity and 
                    time_savings > best_savings and 
                    time_savings >= min_savings):
                    
                    best_savings = time_savings
                    best_route = alt_route
                    best_route["traffic_info"] = alt_traffic
                    logger.info(f"New best route: {route_type}, saves {int(time_savings/60)} minutes")

            if not best_route:
                logger.info(f"No suitable alternative found after evaluating {len(alternative_routes)} routes")
                return None

            # Build recommendation
            confidence = min(0.95, 0.6 + (best_savings / 1800))
            route_type = best_route.get("route_type", "alternative")
            waypoint_info = ""
            
            if best_route.get("waypoint_name"):
                waypoint_info = f" via {best_route['waypoint_name']}"
            
            reason = (
                f"Severe traffic detected ({traffic_condition.severity}). "
                f"Alternative route{waypoint_info} saves {int(best_savings / 60)} minutes "
                f"using {route_type} routing strategy."
            )

            recommended_route_info = RouteInfo(
                distance=best_route["distance"],
                duration=best_route["duration"],
                coordinates=best_route["coordinates"],
                bounds=best_route.get("bounds")
            )

            return RouteRecommendation(
                trip_id=str(trip.id),
                vehicle_id=vehicle_id,
                current_route=RouteInfo(**current_route_info) if current_route_info else None,
                recommended_route=recommended_route_info,
                time_savings=best_savings,
                traffic_avoided=traffic_condition.severity,
                confidence=confidence,
                reason=reason
            )

        except Exception as e:
            logger.error(f"Error in improved route recommendation for trip {getattr(trip, 'id', 'unknown')}: {e}")
            return None
        
    async def monitor_traffic_and_recommend_routes(self):
        """Main traffic monitoring function that generates route recommendations"""
        try:
            logger.info("Starting traffic monitoring cycle")
            
            active_trips = await trip_service.get_active_trips()
            logger.info(f"Monitoring {len(active_trips)} active trips for traffic conditions")
            
            recommendations_generated = 0
            
            for trip in active_trips:
                try:
                    trip_id = trip.id
                    
                    # Update last check time
                    self.last_traffic_check[trip_id] = datetime.utcnow()
                    
                    # Analyze traffic conditions
                    traffic_condition = await self._analyze_route_traffic(trip_id,trip.vehicle_id)
                    
                    if traffic_condition and traffic_condition.severity in [TrafficType.HEAVY, TrafficType.SEVERE]:
                        logger.info(f"High traffic detected for trip {trip_id}: {traffic_condition.severity}")
                        # Make notification to fleet manager about high traffic
                        asyncio.create_task(notification_service.notify_high_traffic(trip,traffic_condition.severity))
                        # Generate route recommendation
                        recommendation = await self.generate_improved_route_recommendation(trip, traffic_condition)
                        
                        if recommendation:
                            # Store recommendation
                            self.route_recommendations[trip_id] = recommendation
                            recommendations_generated += 1
                            
                            logger.info(f"Route recommendation generated for trip {trip_id}: "
                                      f"saves {int(recommendation.time_savings / 60)} minutes")
                            
                            # Optionally, publish event or store in database
                            await trip_service._store_route_recommendation(recommendation)
                    
                except Exception as e:
                    logger.error(f"Error processing trip {trip.id} in traffic monitoring: {e}")
                    continue
            
            logger.info(f"Traffic monitoring cycle complete. Generated {recommendations_generated} recommendations")
            
        except Exception as e:
            logger.error(f"Error in traffic monitoring cycle: {e}")

    async def start_traffic_monitoring(self):
        """Start the traffic monitoring service"""
        logger.info("Starting traffic monitoring service")
        self.active_traffic_monitoring = True
        
        while self.active_traffic_monitoring:
            try:
                await self.monitor_traffic_and_recommend_routes()
                await asyncio.sleep(TRAFFIC_CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Error in traffic monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry on error

    def stop_traffic_monitoring(self):
        """Stop the traffic monitoring service"""
        logger.info("Stopping traffic monitoring service")
        self.active_traffic_monitoring = False

    # -------------------- Original Smart Trip Creation Functions --------------------
    async def create_smart_trip(self, scheduled_trip: ScheduledTrip, created_by: str) -> SmartTrip:
        """Create an optimized smart trip from a scheduled trip"""
        try:
            logger.info(f"[SmartTripService.create_smart_trip] Creating smart trip from scheduled trip ID={scheduled_trip.id}")
            
            # Extract coordinates safely
            origin_coords = scheduled_trip.origin.location.coordinates
            dest_coords = scheduled_trip.destination.location.coordinates
            
            origin_lat = origin_coords[1] 
            origin_lng = origin_coords[0]
            dest_lat = dest_coords[1]
            dest_lng = dest_coords[0]

            # Use the correct attribute names from ScheduledTrip
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
            logger.info(f"[SmartTripService.create_smart_trip] Optimizing route with {num_samples} samples")
            for i in range(num_samples + 1):
                test_start = start_window + i * step
                route = await self._get_ors_route(origin_lat, origin_lng, dest_lat, dest_lng, test_start)
                if route:
                    traffic_delay = await self._get_tomtom_traffic(origin_lat, origin_lng, dest_lat, dest_lng, test_start)
                    total_duration = route["duration"] + traffic_delay.get("live_traffic_delay", 0)
                    if total_duration < min_duration:
                        min_duration = total_duration
                        best_start = test_start
                        best_route = route
                        best_route["traffic_delay"] = traffic_delay.get("live_traffic_delay", 0)

            if not best_route:
                raise ValueError("Failed to get route from ORS")

            distance_km = best_route["distance"] / 1000.0
            duration_min = best_route["duration"] / 60.0
            traffic_delay_min = best_route.get("traffic_delay", 0) / 60.0

            # Vehicle assignment
            optimized_end = best_start + timedelta(seconds=min_duration)
            vehicles = await vehicle_service.get_available_vehicles(best_start, optimized_end)
            logger.info(f"[SmartTripService.create_smart_trip] Found {len(vehicles.get('vehicles', [])) if vehicles else 0} available vehicles")
            
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
                    logger.info(f"[SmartTripService.create_smart_trip] Vehicle assignment chosen: {vehicle_doc}")
                    if vehicle_doc:
                        vehicle_name = vehicle_doc["make"] + vehicle_doc["model"] + vehicle_doc["registration_number"]
                        closest_vehicle_name = vehicle_name
                except Exception as e:
                    logger.warning(f"Error fetching vehicle {closest_vehicle_id}: {e}")

            optimized_start = best_start

            # Driver assignment
            try:
                best_rate = None
                if scheduled_trip.priority == TripPriority.HIGH or scheduled_trip.priority == TripPriority.URGENT:
                    stats = await driver_analytics_service.get_driver_trip_stats("year")
                    
                    # Calculate completion rates for all drivers and sort them
                    driver_performance = []
                    
                    for stat in stats:
                        try:
                            completed = stat.get("completed_trips", 0)
                            cancelled = stat.get("cancelled_trips", 0)
                            total = completed + cancelled
                            rate = completed / total if total > 0 else 0.0
                            
                            driver_performance.append({
                                "driver_id": stat.get("driver_id"),
                                "driver_name": stat.get("driver_name", "Unknown"),
                                "completion_rate": rate
                            })
                        except Exception as e:
                            logger.warning(f"Error processing driver stat {stat}: {e}")
                            continue
                    
                    # Sort by completion rate (descending) and get top 5
                    driver_performance.sort(key=lambda x: x["completion_rate"], reverse=True)
                    top_5_drivers = driver_performance[:5]
                    


                    # Filter for available drivers among top 5
                    available_top_drivers = []
                    for driver in top_5_drivers:
                        try:

                            if driver["driver_id"] and await driver_service.check_driver_availability(driver["driver_id"], optimized_start, optimized_end):
                                available_top_drivers.append(driver)
                        except Exception as e:
                            logger.warning(f"Error checking availability for driver {driver['driver_id']}: {e}")
                            continue
                    
                    # Randomly select from available top performers
                    if available_top_drivers:
                        selected_driver = random.choice(available_top_drivers)
                        best_driver_id = selected_driver["driver_id"]
                        best_driver_name = selected_driver["driver_name"]
                        best_rate = selected_driver["completion_rate"]
                        logger.info(f"Selected top performer: {best_driver_name} )")
                    else:
                        best_driver_id = None
                        best_driver_name = "Unknown"
                        logger.warning("No available drivers found among top 5 performers; defaulting to None")

                else:
                    # For non-urgent/non-high priority trips, get all available drivers
                    logger.info("Entered normal schedule trip recommendations")
                    drivers = await driver_service.get_all_drivers() 
                    available_drivers = []
                    
                    for driver in drivers["drivers"]:
                        try:
                            if await driver_service.check_driver_availability(driver["employee_id"], optimized_start, optimized_end):
                                available_drivers.append(driver)
                        except Exception as e:
                            logger.warning("Error checking availability for driver ")
                            continue
                    logger.info(f"{len(available_drivers)} available for normal/low priority trips")
                    
                    # Randomly select from all available drivers
                    if available_drivers:
                        selected_driver = random.choice(available_drivers)
                        logger.info(f"Selected driver info: {selected_driver}")
                        best_driver_id = selected_driver["employee_id"]
                        best_driver_name = f"{selected_driver['first_name']} {selected_driver['last_name']}".strip()
                                
                        # workout rate:
                        specific_stats = await driver_analytics_service.get_driver_trip_stats_by_id(best_driver_id, "year")
                        completed = specific_stats["completed_trips"]
                        cancelled = specific_stats["cancelled_trips"]
                        total = completed + cancelled
                        best_rate = completed / total if total > 0 else 0.0
                        logger.info(f"Randomly selected driver: {best_driver_name}")
                    else:
                        best_driver_id = None
                        best_driver_name = "Unknown"
                        logger.warning("No available drivers found; defaulting to None")
                        return None

                logger.info(f"[SmartTripService.create_smart_trip] Best driver assignment: {best_driver_id}")
                
            except Exception as e:
                logger.warning(f"Error getting driver stats: {e}")
                best_driver_id = None
                best_driver_name = "Unknown"
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

            route_info_obj = RouteInfo(
                distance=best_route["distance"],
                duration=best_route["duration"],
                coordinates=best_route["coordinates"],
                bounds=best_route["bounds"]
            )
            
            # Return properly structured response
            trip_id = str(getattr(scheduled_trip, 'id', 'unknown'))
            smart_id = f"smart-{trip_id[:8]}"

            from schemas.requests import CreateSmartTripRequest
            create_request = CreateSmartTripRequest(
                smart_id=smart_id,
                trip_id=trip_id,
                trip_name=scheduled_trip.name,
                description=scheduled_trip.description,

                original_start_time=start_window,
                original_end_time=end_window,

                optimized_start_time=optimized_start,
                optimized_end_time=optimized_end,
                vehicle_id=closest_vehicle_id,
                vehicle_name=closest_vehicle_name,
                driver_id=best_driver_id,
                driver_name=best_driver_name,
                priority=scheduled_trip.priority,

                origin=scheduled_trip.origin,
                destination=scheduled_trip.destination,
                waypoints=scheduled_trip.waypoints or [],
                estimated_distance=distance_km,
                estimated_duration=duration_min,
                route_info=route_info_obj,

                time_saved=time_saved_str,
                fuel_efficiency=fuel_efficiency,
                route_optimisation="Optimal traffic timing",
                driver_utilisation=f"{best_rate * 100:.0f}% efficiency",
                confidence="92",
                reasoning=reasoning
            )

            try:
                # Call the database service method to create the smart trip
                actual_trip = await trip_service.create_smart_trip(create_request, created_by)
                logger.info(f"[SmartTripService.create_smart_trip] New smart trip created: {actual_trip.id}")
                return actual_trip
            except Exception as e:
                logger.error(f"Error creating trip in database: {e}")
                raise
                
        except Exception as e:
            logger.error(f"[SmartTripService.create_smart_trip] Error in create_smart_trip: {e}", exc_info=True)
            raise


# Create global service instance
smart_trip_service = SmartTripService()