""" Simulation service for managing live locations """
import logging
import asyncio
import aiohttp
import time
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta,timezone
from bson import ObjectId
from dataclasses import dataclass
import math

from repositories.database import db_manager, db_manager_gps
from services.trip_service import trip_service
from events.publisher import event_publisher

logger = logging.getLogger(__name__)

current_time = datetime.now(timezone.utc)

@dataclass
class Location:
    latitude: float
    longitude: float
    timestamp: datetime

@dataclass
class Route:
    coordinates: List[Tuple[float, float]]  # List of (lat, lon) pairs
    distance: float  # Total distance in meters
    duration: float  # Total duration in seconds

class VehicleSimulator:
    def __init__(self, trip_id: str, vehicle_id: str, route: Route, speed_kmh: float = 50.0):
        self.trip_id = trip_id
        self.vehicle_id = vehicle_id
        self.route = route
        self.base_speed_kmh = speed_kmh
        self.current_speed_kmh = speed_kmh
        self.speed_ms = speed_kmh / 3.6  # Convert km/h to m/s
        self.current_position = 0  # Current position along the route (0-1)
        self.is_running = False
        self.is_paused = False  # New: Track pause state
        self.start_time = datetime.utcnow()
        self.distance_traveled = 0.0
        self.last_location = None
        
        # Speed variation parameters
        self.min_speed = 40.0  # km/h
        self.max_speed = 140.0  # km/h
        self.speed_change_rate = 0.5  # How quickly speed changes (km/h per update)
        self.target_speed = speed_kmh
        self.speed_change_timer = 0
        self.speed_change_interval = 15  # Change target speed every 15 updates (30 seconds)
        
        # Note: When current_position reaches 1.0 (destination), simulation stops
        # but trip remains active until manually completed by driver
    
    def pause(self):
        """Pause the simulation"""
        self.is_paused = True
        logger.info(f"Paused simulation for trip {self.trip_id}")
    
    def resume(self):
        """Resume the simulation"""
        self.is_paused = False
        logger.info(f"Resumed simulation for trip {self.trip_id}")
    
    def stop(self):
        """Stop the simulation"""
        self.is_running = False
        self.is_paused = False
        logger.info(f"Stopped simulation for trip {self.trip_id}")
    
    def get_distance_traveled(self) -> float:
        """Get distance traveled in meters"""
        return self.distance_traveled

    def get_distance_traveled_km(self) -> float:
        """Get distance traveled in kilometers"""
        return self.distance_traveled / 1000.0
    
    def get_remaining_distance(self) -> float:
        """Get remaining distance in meters"""
        return self.route.distance - self.distance_traveled
    
    def get_progress_percentage(self) -> float:
        """Get trip progress as percentage (0-100)"""
        if self.route.distance == 0:
            return 100.0
        return (self.distance_traveled / self.route.distance) * 100.0
        
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_current_location(self) -> Tuple[float, float]:
        """Get current lat/lon based on position along route"""
        if not self.route.coordinates:
            return self.route.coordinates[0] if self.route.coordinates else (0, 0)
        
        if self.current_position >= 1.0:
            return self.route.coordinates[-1]
        
        # Find which segment we're on
        total_distance = 0
        target_distance = self.current_position * self.route.distance
        
        for i in range(len(self.route.coordinates) - 1):
            start_point = self.route.coordinates[i]
            end_point = self.route.coordinates[i + 1]
            
            segment_distance = self.calculate_distance(
                start_point[0], start_point[1],
                end_point[0], end_point[1]
            )
            
            if total_distance + segment_distance >= target_distance:
                # We're in this segment
                remaining_distance = target_distance - total_distance
                segment_ratio = remaining_distance / segment_distance if segment_distance > 0 else 0
                
                # Interpolate between start and end points
                lat = start_point[0] + (end_point[0] - start_point[0]) * segment_ratio
                lon = start_point[1] + (end_point[1] - start_point[1]) * segment_ratio
                
                return (lat, lon)
            
            total_distance += segment_distance
        
        return self.route.coordinates[-1]
    
    def get_estimated_finish_time(self) -> datetime:
        """Estimate when the trip will finish. Defaults to 50 km/h if speed is missing or invalid."""
        if self.current_position >= 1.0:
            return datetime.utcnow()
        speed_ms = self.speed_ms if self.speed_ms and self.speed_ms > 0 else (50 / 3.6)
        remaining_distance = self.route.distance * (1 - self.current_position)
        remaining_time_sec = remaining_distance / speed_ms
        return datetime.utcnow() + timedelta(seconds=remaining_time_sec)
    
    def update_speed(self):
        """Update current speed with realistic variation"""
        import random
        
        self.speed_change_timer += 1
        
        # Change target speed periodically
        if self.speed_change_timer >= self.speed_change_interval:
            # Choose new target speed with some logic based on route progress
            if self.current_position < 0.1:  # Starting - gradually increase
                self.target_speed = random.uniform(50, 80)
            elif self.current_position > 0.9:  # Near destination - slow down
                self.target_speed = random.uniform(40, 60)
            else:  # Middle of journey - higher speeds on highways
                # Assume highway speeds in middle sections
                highway_probability = 0.7
                if random.random() < highway_probability:
                    self.target_speed = random.uniform(80, 140)
                else:
                    self.target_speed = random.uniform(50, 80)
            
            # Ensure target is within bounds
            self.target_speed = max(self.min_speed, min(self.max_speed, self.target_speed))
            self.speed_change_timer = 0
        
        # Gradually adjust current speed toward target
        speed_diff = self.target_speed - self.current_speed_kmh
        if abs(speed_diff) > self.speed_change_rate:
            if speed_diff > 0:
                self.current_speed_kmh += self.speed_change_rate
            else:
                self.current_speed_kmh -= self.speed_change_rate
        else:
            self.current_speed_kmh = self.target_speed
        
        # Ensure speed stays within bounds
        self.current_speed_kmh = max(self.min_speed, min(self.max_speed, self.current_speed_kmh))
        
        # Update speed_ms for calculations
        self.speed_ms = self.current_speed_kmh / 3.6
    
    async def update_position(self):
        """Update vehicle position and save to database"""
        # Don't update position if paused
        if self.is_paused:
            return True
            
        if self.current_position >= 1.0:
            # Stop simulation but don't complete the trip - let driver complete manually
            self.is_running = False
            logger.info(f"Trip {self.trip_id} simulation reached destination - stopping location updates. Trip remains active for manual completion.")
            return False
        
        # Update speed with realistic variation
        self.update_speed()
        
        # Calculate how far we should have moved in 2 seconds
        distance_moved = self.speed_ms * 2  # 2 seconds
        position_increment = distance_moved / self.route.distance
        
        self.current_position = min(1.0, self.current_position + position_increment)
        
        # Get current lat/lon
        lat, lon = self.get_current_location()

        estimated_finish = self.get_estimated_finish_time()
        
        # Create location document matching the expected format
        current_time = datetime.utcnow()
        location_doc = {
            "vehicle_id": self.vehicle_id,
            "location": {
                "type": "Point",
                "coordinates": [lon, lat]  # GeoJSON format: [longitude, latitude]
            },
            "latitude": lat,
            "longitude": lon,
            "altitude": None,
            "speed": self.current_speed_kmh,  # Use current variable speed
            "heading": self._calculate_heading(),
            "accuracy": None,
            "timestamp": current_time,
            "updated_at": current_time
        }
        
        try:
            # Update current location for the vehicle
            await db_manager_gps.locations.update_one(
                {"vehicle_id": self.vehicle_id},
                {"$set": location_doc},
                upsert=True
            )

            await db_manager.trips.update_one(
                {"_id": ObjectId(self.trip_id)},
                {"$set": {"estimated_end_time": estimated_finish}}
            )

            
        except Exception as e:
            logger.error(f"Failed to update vehicle location: {e}")

        # After updating position, check if this trip needs traffic analysis
        if self.current_position > 0.1 and self.current_position < 0.9:  # Middle of journey
            try:
                # Import here to avoid circular imports
                from services.smart_trip_planning_service import smart_trip_service
                
                # Trigger traffic analysis for this trip (non-blocking)
                asyncio.create_task(smart_trip_service._analyze_route_traffic(self.trip_id,self.vehicle_id))
            except Exception as e:
                logger.warning(f"Failed to trigger traffic analysis: {e}")
        
        return True
    
    async def _complete_trip(self):
        """Move completed trip to trip_history collection"""
        try:
            # Get the original trip document
            trip_doc = await db_manager.trips.find_one({"_id": ObjectId(self.trip_id)})
            
            if not trip_doc:
                logger.error(f"Trip {self.trip_id} not found in trips collection")
                return
            
            # Add completion information
            completion_time = datetime.utcnow()
            trip_doc.update({
                "actual_end_time": completion_time,
                "status": "completed",
                "completion_reason": "completed",
                "moved_to_history_at": completion_time
            })
            
            # Insert into trip_history collection
            await db_manager.trip_history.insert_one(trip_doc)
            logger.info(f"Trip {self.trip_id} moved to trip_history with status 'completed'")
            
            # Remove from active trips collection
            await db_manager.trips.delete_one({"_id": ObjectId(self.trip_id)})
            logger.info(f"Trip {self.trip_id} removed from active trips")
            
            # Clean up vehicle location (optional - you might want to keep last known location)
            # await db_manager_gps.locations.delete_one({"vehicle_id": self.vehicle_id})
            
        except Exception as e:
            logger.error(f"Failed to complete trip {self.trip_id}: {e}")
    
    def _calculate_heading(self) -> float:
        """Calculate current heading based on direction of travel"""
        if len(self.route.coordinates) < 2 or self.current_position >= 1.0:
            return 0.0
        
        # Find current segment
        total_distance = 0
        target_distance = self.current_position * self.route.distance
        
        for i in range(len(self.route.coordinates) - 1):
            start_point = self.route.coordinates[i]
            end_point = self.route.coordinates[i + 1]
            
            segment_distance = self.calculate_distance(
                start_point[0], start_point[1],
                end_point[0], end_point[1]
            )
            
            if total_distance + segment_distance >= target_distance:
                # Calculate bearing from start to end point
                lat1, lon1 = math.radians(start_point[0]), math.radians(start_point[1])
                lat2, lon2 = math.radians(end_point[0]), math.radians(end_point[1])
                
                dlon = lon2 - lon1
                y = math.sin(dlon) * math.cos(lat2)
                x = (math.cos(lat1) * math.sin(lat2) - 
                     math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
                
                bearing = math.atan2(y, x)
                bearing = math.degrees(bearing)
                bearing = (bearing + 360) % 360
                
                return bearing
            
            total_distance += segment_distance
        
        return 0.0

class SimulationService:
    def __init__(self):
        self.active_simulators: Dict[str, VehicleSimulator] = {}
        self.is_running = False
        self.osrm_url = "http://router.project-osrm.org"  # Public OSRM instance
        
    async def get_route(self, start_lat: float, start_lon: float, 
                       end_lat: float, end_lon: float) -> Optional[Route]:
        """Get route from OSRM API"""
        url = f"{self.osrm_url}/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("routes"):
                            route_data = data["routes"][0]
                            
                            # Extract coordinates from geometry
                            coordinates = []
                            if route_data.get("geometry", {}).get("coordinates"):
                                for coord in route_data["geometry"]["coordinates"]:
                                    coordinates.append((coord[1], coord[0]))  # Convert lon,lat to lat,lon
                            
                            return Route(
                                coordinates=coordinates,
                                distance=route_data.get("distance", 0),
                                duration=route_data.get("duration", 0)
                            )
                    else:
                        logger.error(f"OSRM API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to get route from OSRM: {e}")
        
        # Fallback: create simple straight line route
        return Route(
            coordinates=[(start_lat, start_lon), (end_lat, end_lon)],
            distance=self._calculate_straight_line_distance(start_lat, start_lon, end_lat, end_lon),
            duration=0
        )
    
    def _calculate_straight_line_distance(self, lat1: float, lon1: float, 
                                        lat2: float, lon2: float) -> float:
        """Calculate straight line distance as fallback"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    async def get_active_trips(self) -> List[Dict[str, Any]]:
        """Get all trips that have started but not completed"""
        try:
            
            query = {
                "actual_start_time": {"$exists": True, "$ne": None},
                "$or": [
                    {"actual_end_time": {"$exists": False}},
                    {"actual_end_time": None}
                ]
            }
            
            trips_collection = db_manager.trips
            trips = await trips_collection.find(query).to_list(None)
            
            #logger.info(f"Found {len(trips)} active trips")
            return trips
            
        except Exception as e:
            logger.error(f"Failed to get active trips: {e}")
            return []
    
    async def start_trip_simulation(self, trip: Dict[str, Any]):
        """Start simulation for a single trip"""
        trip_id = trip.get("id") or str(trip.get("_id", ""))
        vehicle_id = trip.get("vehicle_id")
        
        if not vehicle_id:
            logger.warning(f"Trip {trip_id} has no vehicle_id")
            return
        
        # Check if trip is already manually completed
        if trip.get("actual_end_time") or trip.get("status") == "completed":
            logger.info(f"Trip {trip_id} is already completed, skipping simulation")
            return
        
        if trip_id in self.active_simulators:
            # Check if the existing simulator has reached the destination
            simulator = self.active_simulators[trip_id]
            if simulator.current_position >= 1.0 and not simulator.is_running:
                logger.info(f"Trip {trip_id} simulation already reached destination, not restarting")
                return
            #logger.info(f"Trip {trip_id} already being simulated")
            return
        
        # First, try to use route_info from the scheduled trip
        route = None
        route_info = trip.get("route_info")
        
        if route_info and route_info.get("coordinates"):
            logger.info(f"Using route_info from scheduled trip {trip_id}")
            
            # Convert coordinates from [lat, lng] to (lat, lon) tuples
            coordinates = []
            for coord in route_info["coordinates"]:
                if len(coord) >= 2:
                    coordinates.append((coord[0], coord[1]))  # [lat, lng] to (lat, lon)
            
            if coordinates:
                route = Route(
                    coordinates=coordinates,
                    distance=route_info.get("distance", 0),
                    duration=route_info.get("duration", 0)
                )
        
        # Fallback to generating route from origin/destination if no route_info
        if not route:
            logger.info(f"No route_info found, generating route for trip {trip_id}")
            
            # Get start coordinates from origin
            origin = trip.get("origin", {})
            origin_location = origin.get("location", {})
            origin_coords = origin_location.get("coordinates", [])
            
            # Get end coordinates from destination
            destination = trip.get("destination", {})
            destination_location = destination.get("location", {})
            destination_coords = destination_location.get("coordinates", [])
            
            if len(origin_coords) < 2 or len(destination_coords) < 2:
                logger.error(f"Trip {trip_id} missing origin or destination coordinates")
                return
            
            # Coordinates are in [longitude, latitude] format (GeoJSON)
            start_lon, start_lat = origin_coords[0], origin_coords[1]
            end_lon, end_lat = destination_coords[0], destination_coords[1]
            
            # Get waypoints if they exist
            waypoints = trip.get("waypoints", [])
            waypoint_coords = []
            for waypoint in waypoints:
                wp_location = waypoint.get("location", {})
                wp_coords = wp_location.get("coordinates", [])
                if len(wp_coords) >= 2:
                    waypoint_coords.append((wp_coords[1], wp_coords[0]))  # Convert to lat, lon
            
            # Get route including waypoints
            route = await self.get_route_with_waypoints(start_lat, start_lon, end_lat, end_lon, waypoint_coords)
        
        if not route:
            logger.error(f"Failed to get route for trip {trip_id}")
            return
        
        # Create and start simulator
        speed = 80.0  # Default starting speed
        simulator = VehicleSimulator(trip_id, vehicle_id, route, speed)
        simulator.is_running = True
        
        self.active_simulators[trip_id] = simulator
        
        logger.info(f"Started simulation for trip {trip_id}, vehicle {vehicle_id} with variable speed (40-140 km/h)")
    
    async def get_route_with_waypoints(self, start_lat: float, start_lon: float, 
                                     end_lat: float, end_lon: float, 
                                     waypoints: List[Tuple[float, float]] = None) -> Optional[Route]:
        """Get route from OSRM API including waypoints"""
        if waypoints is None:
            waypoints = []
        
        # Build coordinates string: start;waypoint1;waypoint2;...;end
        coords = [f"{start_lon},{start_lat}"]
        for wp_lat, wp_lon in waypoints:
            coords.append(f"{wp_lon},{wp_lat}")
        coords.append(f"{end_lon},{end_lat}")
        
        coordinates_str = ";".join(coords)
        url = f"{self.osrm_url}/route/v1/driving/{coordinates_str}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("routes"):
                            route_data = data["routes"][0]
                            
                            # Extract coordinates from geometry
                            coordinates = []
                            if route_data.get("geometry", {}).get("coordinates"):
                                for coord in route_data["geometry"]["coordinates"]:
                                    coordinates.append((coord[1], coord[0]))  # Convert lon,lat to lat,lon
                            
                            return Route(
                                coordinates=coordinates,
                                distance=route_data.get("distance", 0),
                                duration=route_data.get("duration", 0)
                            )
                    else:
                        logger.error(f"OSRM API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to get route from OSRM: {e}")
        
        # Fallback: create simple route through waypoints
        all_points = [(start_lat, start_lon)] + waypoints + [(end_lat, end_lon)]
        total_distance = 0
        for i in range(len(all_points) - 1):
            total_distance += self._calculate_straight_line_distance(
                all_points[i][0], all_points[i][1],
                all_points[i + 1][0], all_points[i + 1][1]
            )
        
        return Route(
            coordinates=all_points,
            distance=total_distance,
            duration=0
        )
    
    async def update_all_simulations(self):
        """Update all active simulations"""
        for trip_id, simulator in self.active_simulators.items():
            if simulator.is_running:
                success = await simulator.update_position()
                if not success:
                    # Simulation stopped (reached destination) but keep simulator to track state
                    logger.info(f"Simulation for trip {trip_id} stopped at destination - awaiting manual completion")
        
        # Note: We don't remove simulators that reached destination to prevent restarting
    
    async def pause_trip_simulation(self, trip_id: str):
        """Pause simulation for a specific trip"""
        if trip_id in self.active_simulators:
            self.active_simulators[trip_id].pause()
            logger.info(f"Paused simulation for trip {trip_id}")
        else:
            logger.warning(f"Cannot pause simulation - trip {trip_id} not found in active simulators")
    
    async def resume_trip_simulation(self, trip_id: str):
        """Resume simulation for a specific trip"""
        if trip_id in self.active_simulators:
            self.active_simulators[trip_id].resume()
            logger.info(f"Resumed simulation for trip {trip_id}")
        else:
            logger.warning(f"Cannot resume simulation - trip {trip_id} not found in active simulators")
    
    async def stop_trip_simulation(self, trip_id: str):
        """Stop and remove simulation for a specific trip"""
        if trip_id in self.active_simulators:
            self.active_simulators[trip_id].stop()
            del self.active_simulators[trip_id]
            logger.info(f"Stopped and removed simulation for trip {trip_id}")
        else:
            logger.warning(f"Cannot stop simulation - trip {trip_id} not found in active simulators")
    
    async def cleanup_completed_trip_simulation(self, trip_id: str):
        """Clean up simulation for a manually completed trip"""
        if trip_id in self.active_simulators:
            del self.active_simulators[trip_id]
            logger.info(f"Cleaned up simulation for manually completed trip {trip_id}")
        else:
            logger.warning(f"Cannot cleanup simulation - trip {trip_id} not found in active simulators")
    
    
    
    async def start_simulation_service(self):
        """Main simulation loop"""
        logger.info("Starting vehicle simulation service")
        self.is_running = True
        
        while self.is_running:
            try:
                # Check for new trips to simulate
                active_trips = await self.get_active_trips()
                
                for trip in active_trips:
                    await self.start_trip_simulation(trip)
                
                # Update all simulations
                await self.update_all_simulations()
                
                # Wait 2 seconds before next update
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    def stop_simulation_service(self):
        """Stop the simulation service"""
        logger.info("Stopping vehicle simulation service")
        self.is_running = False
        self.active_simulators.clear()

# Singleton instance
simulation_service = SimulationService()

# CLI script functionality
async def main():
    """Main function to run as a script"""
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print("Shutting down simulation service...")
        simulation_service.stop_simulation_service()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await simulation_service.start_simulation_service()
    except KeyboardInterrupt:
        print("Simulation service stopped by user")
    except Exception as e:
        logger.error(f"Simulation service failed: {e}")
    finally:
        simulation_service.stop_simulation_service()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the simulation service
    asyncio.run(main())