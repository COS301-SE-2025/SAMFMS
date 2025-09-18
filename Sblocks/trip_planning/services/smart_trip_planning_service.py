import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
import asyncio
import traceback
import aiohttp
from math import radians, sin, cos, sqrt, atan2
from bson import ObjectId
from flexpolyline import decode

from schemas.entities import ScheduledTrip, RouteInfo, RouteBounds, TripStatus, VehicleLocation, SmartTrip, TrafficCondition, RouteRecommendation, TrafficType, Trip
from schemas.requests import CreateTripRequest, UpdateTripRequest
from repositories.database import db_manager, db_manager_gps, db_manager_management
from services.trip_service import trip_service
from services.vehicle_service import vehicle_service
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

    async def _generate_route_recommendation(
        self,
        trip: Trip,
        traffic_condition: TrafficCondition
    ) -> Optional[RouteRecommendation]:
        """Generate a route recommendation if traffic conditions warrant it."""
        try:
            # 1. Validate traffic condition severity and ratio
            if not traffic_condition or traffic_condition.traffic_ratio < (1 + HIGH_TRAFFIC_THRESHOLD):
                return None  # Traffic not bad enough for rerouting

            if traffic_condition.severity not in [TrafficType.HEAVY, TrafficType.SEVERE]:
                return None  # Only heavy or severe traffic triggers reroute

            # 2. Extract vehicle ID
            vehicle_id = trip.vehicle_id
            if not vehicle_id:
                logger.warning(f"No vehicle_id for trip {trip.id}")
                return None

            # 3. Get current vehicle location
            current_location = await self._get_current_trip_location(vehicle_id)
            if not current_location:
                logger.warning(f"No current location for vehicle {vehicle_id}")
                return None
            current_lat, current_lng = current_location

            # 4. Get destination coordinates safely
            if not trip.destination or not trip.destination.location or not trip.destination.location.coordinates:
                logger.warning(f"Destination coordinates missing for trip {trip.id}")
                return None

            dest_coords = trip.destination.location.coordinates
            if len(dest_coords) < 2:
                logger.warning(f"Invalid destination coordinates for trip {trip.id}: {dest_coords}")
                return None
            dest_lng, dest_lat = dest_coords[0], dest_coords[1]

            # 5. Fetch alternative routes
            alternative_routes = await self._get_alternative_routes_mapbox(
                None, None, dest_lat, dest_lng, current_lat, current_lng
            )
            logger.info(f"Generated {len(alternative_routes)} alternative routes")
            if not alternative_routes:
                return None

            # 6. Evaluate alternative routes
            best_route = None
            best_savings = 0
            current_route_info = trip.route_info.dict() if trip.route_info else None
            current_duration = traffic_condition.current_duration

            for alt_route in alternative_routes:
                # Get live traffic for this alternative
                alt_traffic = await self._get_tomtom_traffic(current_lat, current_lng, dest_lat, dest_lng)
                alt_duration = alt_route["duration"] + alt_traffic.get("live_traffic_delay", 0)
                time_savings = current_duration - alt_duration

                # Skip if route too similar
                if current_route_info and current_route_info.get("coordinates"):
                    similarity = self._calculate_route_similarity(
                        current_route_info["coordinates"],
                        alt_route["coordinates"]
                    )
                    if similarity > (1 - ROUTE_DEVIATION_THRESHOLD):
                        logger.info("Alternative route to similiar, skipping route")
                        continue

                # Select best route if savings significant
                if time_savings > best_savings and time_savings >= MINIMUM_TIME_SAVINGS:
                    best_savings = time_savings
                    best_route = alt_route
                    best_route["traffic_info"] = alt_traffic

            if not best_route or best_savings < MINIMUM_TIME_SAVINGS:
                return None

            # 7. Build route recommendation object
            confidence = min(0.95, 0.6 + (best_savings / 1800))  # Higher confidence for bigger savings
            reason = (
                f"Heavy traffic detected on current route ({traffic_condition.severity}). "
                f"Alternative route saves {int(best_savings / 60)} minutes and avoids congestion."
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
                reason=reason,
                created_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(
                f"Error generating route recommendation for trip {getattr(trip, 'id', 'unknown')}: {e}\n"
                f"{traceback.format_exc()}"
            )
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
                        
                        # Generate route recommendation
                        recommendation = await self._generate_route_recommendation(trip, traffic_condition)
                        
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
                    
                logger.info(f"[SmartTripService.create_smart_trip] Best driver assignment: {best_driver_id}")
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