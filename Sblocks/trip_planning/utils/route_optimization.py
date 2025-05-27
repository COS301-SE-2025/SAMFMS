"""Route optimization utilities"""

from typing import List, Dict, Tuple, Optional
import math
from datetime import datetime, timedelta
import asyncio


class RouteOptimizer:
    """Route optimization and pathfinding utilities"""
    
    def __init__(self):
        self.earth_radius_km = 6371.0
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Calculate differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return self.earth_radius_km * c
    
    def calculate_travel_time(self, distance_km: float, avg_speed_kmh: float = 50.0) -> float:
        """Calculate estimated travel time in hours"""
        return distance_km / avg_speed_kmh
    
    def optimize_route_order(self, waypoints: List[Dict[str, float]], start_point: Optional[Dict[str, float]] = None) -> List[int]:
        """
        Optimize the order of waypoints using nearest neighbor algorithm
        Returns list of indices representing the optimized order
        """
        if not waypoints:
            return []
        
        if len(waypoints) <= 2:
            return list(range(len(waypoints)))
        
        # If no start point specified, use first waypoint
        if not start_point:
            start_point = waypoints[0]
            remaining_indices = list(range(1, len(waypoints)))
            optimized_order = [0]
        else:
            remaining_indices = list(range(len(waypoints)))
            optimized_order = []
        
        current_point = start_point
        
        while remaining_indices:
            # Find nearest unvisited waypoint
            nearest_index = None
            min_distance = float('inf')
            
            for idx in remaining_indices:
                waypoint = waypoints[idx]
                distance = self.calculate_distance(
                    current_point['latitude'], current_point['longitude'],
                    waypoint['latitude'], waypoint['longitude']
                )
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_index = idx
            
            # Add nearest waypoint to optimized order
            optimized_order.append(nearest_index)
            remaining_indices.remove(nearest_index)
            current_point = waypoints[nearest_index]
        
        return optimized_order
    
    def calculate_route_metrics(self, waypoints: List[Dict[str, float]], optimized_order: List[int]) -> Dict[str, float]:
        """Calculate total distance and time for optimized route"""
        if len(optimized_order) < 2:
            return {"total_distance": 0.0, "total_time": 0.0}
        
        total_distance = 0.0
        
        for i in range(len(optimized_order) - 1):
            current_idx = optimized_order[i]
            next_idx = optimized_order[i + 1]
            
            current_point = waypoints[current_idx]
            next_point = waypoints[next_idx]
            
            distance = self.calculate_distance(
                current_point['latitude'], current_point['longitude'],
                next_point['latitude'], next_point['longitude']
            )
            total_distance += distance
        
        total_time = self.calculate_travel_time(total_distance)
        
        return {
            "total_distance": total_distance,
            "total_time": total_time
        }
    
    def find_optimal_depot_location(self, frequent_destinations: List[Dict[str, float]]) -> Dict[str, float]:
        """Find optimal depot location based on frequent destinations"""
        if not frequent_destinations:
            return {"latitude": 0.0, "longitude": 0.0}
        
        # Calculate centroid as a simple optimization
        avg_lat = sum(dest['latitude'] for dest in frequent_destinations) / len(frequent_destinations)
        avg_lon = sum(dest['longitude'] for dest in frequent_destinations) / len(frequent_destinations)
        
        return {
            "latitude": avg_lat,
            "longitude": avg_lon
        }
    
    def estimate_fuel_consumption(self, distance_km: float, vehicle_efficiency_km_per_liter: float = 12.0) -> float:
        """Estimate fuel consumption for a route"""
        return distance_km / vehicle_efficiency_km_per_liter
    
    def calculate_route_cost(
        self, 
        distance_km: float, 
        time_hours: float, 
        fuel_cost_per_liter: float = 1.5,
        driver_cost_per_hour: float = 15.0,
        vehicle_efficiency: float = 12.0
    ) -> Dict[str, float]:
        """Calculate total cost for a route"""
        fuel_consumption = self.estimate_fuel_consumption(distance_km, vehicle_efficiency)
        fuel_cost = fuel_consumption * fuel_cost_per_liter
        driver_cost = time_hours * driver_cost_per_hour
        total_cost = fuel_cost + driver_cost
        
        return {
            "fuel_cost": fuel_cost,
            "driver_cost": driver_cost,
            "total_cost": total_cost,
            "fuel_consumption_liters": fuel_consumption
        }
    
    def check_route_feasibility(
        self, 
        total_distance: float, 
        vehicle_max_range: float,
        total_time: float,
        max_working_hours: float = 8.0
    ) -> Dict[str, bool]:
        """Check if route is feasible within vehicle and driver constraints"""
        return {
            "distance_feasible": total_distance <= vehicle_max_range,
            "time_feasible": total_time <= max_working_hours,
            "overall_feasible": (
                total_distance <= vehicle_max_range and 
                total_time <= max_working_hours
            )
        }
    
    async def get_traffic_adjusted_time(
        self, 
        base_time_hours: float, 
        departure_time: datetime,
        traffic_api_client=None
    ) -> float:
        """
        Get traffic-adjusted travel time
        This is a placeholder for integration with traffic APIs
        """
        # Simple traffic multiplier based on time of day
        hour = departure_time.hour
        
        # Rush hour traffic (7-9 AM, 5-7 PM)
        if (7 <= hour <= 9) or (17 <= hour <= 19):
            traffic_multiplier = 1.5
        # Moderate traffic (6-7 AM, 9-11 AM, 3-5 PM, 7-8 PM)
        elif (6 <= hour <= 7) or (9 <= hour <= 11) or (15 <= hour <= 17) or (19 <= hour <= 20):
            traffic_multiplier = 1.2
        # Light traffic
        else:
            traffic_multiplier = 1.0
        
        return base_time_hours * traffic_multiplier
