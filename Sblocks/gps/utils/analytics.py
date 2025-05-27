"""
Analytics Utilities for GPS Tracking System

Contains functions for data analysis, reporting, and metrics calculation.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from collections import defaultdict, Counter

from ..models.location import VehicleLocation
from ..models.geofence import GeofenceEvent
from ..models.route import VehicleRoute
from .geospatial import haversine_distance, detect_stops


def calculate_vehicle_metrics(locations: List[VehicleLocation]) -> Dict[str, Any]:
    """
    Calculate comprehensive metrics for a vehicle's movement
    
    Args:
        locations: List of vehicle locations sorted by timestamp
    
    Returns:
        Dictionary containing various metrics
    """
    if not locations:
        return {}
    
    if len(locations) == 1:
        return {
            "total_distance_km": 0,
            "total_duration_hours": 0,
            "average_speed_kmh": 0,
            "max_speed_kmh": locations[0].speed or 0,
            "stops_count": 0,
            "total_stop_time_minutes": 0
        }
    
    # Basic calculations
    total_distance = 0
    speeds = []
    
    for i in range(1, len(locations)):
        # Distance calculation
        distance = haversine_distance(
            locations[i-1].latitude, locations[i-1].longitude,
            locations[i].latitude, locations[i].longitude
        )
        total_distance += distance
        
        # Speed collection
        if locations[i].speed is not None:
            speeds.append(locations[i].speed)
    
    # Time calculations
    start_time = locations[0].timestamp
    end_time = locations[-1].timestamp
    total_duration_hours = (end_time - start_time).total_seconds() / 3600
    
    # Speed calculations
    avg_speed = total_distance / total_duration_hours if total_duration_hours > 0 else 0
    max_speed = max(speeds) if speeds else 0
    
    # Detect stops
    stops = detect_stops(locations)
    total_stop_time = sum(stop["duration_minutes"] for stop in stops)
    
    return {
        "total_distance_km": round(total_distance, 2),
        "total_duration_hours": round(total_duration_hours, 2),
        "average_speed_kmh": round(avg_speed, 2),
        "max_speed_kmh": max_speed,
        "stops_count": len(stops),
        "total_stop_time_minutes": round(total_stop_time, 2),
        "moving_time_hours": round(total_duration_hours - (total_stop_time / 60), 2),
        "points_count": len(locations),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }


def calculate_fleet_summary(vehicle_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate fleet-wide summary metrics
    
    Args:
        vehicle_metrics: List of vehicle metrics dictionaries
    
    Returns:
        Fleet summary dictionary
    """
    if not vehicle_metrics:
        return {}
    
    # Aggregate totals
    total_distance = sum(m.get("total_distance_km", 0) for m in vehicle_metrics)
    total_duration = sum(m.get("total_duration_hours", 0) for m in vehicle_metrics)
    total_stops = sum(m.get("stops_count", 0) for m in vehicle_metrics)
    total_stop_time = sum(m.get("total_stop_time_minutes", 0) for m in vehicle_metrics)
    
    # Speed statistics
    avg_speeds = [m.get("average_speed_kmh", 0) for m in vehicle_metrics if m.get("average_speed_kmh", 0) > 0]
    max_speeds = [m.get("max_speed_kmh", 0) for m in vehicle_metrics if m.get("max_speed_kmh", 0) > 0]
    
    return {
        "vehicle_count": len(vehicle_metrics),
        "total_distance_km": round(total_distance, 2),
        "total_duration_hours": round(total_duration, 2),
        "average_fleet_speed_kmh": round(statistics.mean(avg_speeds), 2) if avg_speeds else 0,
        "max_fleet_speed_kmh": max(max_speeds) if max_speeds else 0,
        "total_stops": total_stops,
        "total_stop_time_hours": round(total_stop_time / 60, 2),
        "average_distance_per_vehicle": round(total_distance / len(vehicle_metrics), 2),
        "average_duration_per_vehicle": round(total_duration / len(vehicle_metrics), 2)
    }


def analyze_speed_patterns(locations: List[VehicleLocation]) -> Dict[str, Any]:
    """
    Analyze speed patterns and violations
    
    Args:
        locations: List of vehicle locations with speed data
    
    Returns:
        Speed analysis dictionary
    """
    speeds = [loc.speed for loc in locations if loc.speed is not None]
    
    if not speeds:
        return {"error": "No speed data available"}
    
    # Basic statistics
    avg_speed = statistics.mean(speeds)
    median_speed = statistics.median(speeds)
    max_speed = max(speeds)
    min_speed = min(speeds)
    
    # Speed distribution
    speed_ranges = {
        "0-20": len([s for s in speeds if 0 <= s <= 20]),
        "21-40": len([s for s in speeds if 21 <= s <= 40]),
        "41-60": len([s for s in speeds if 41 <= s <= 60]),
        "61-80": len([s for s in speeds if 61 <= s <= 80]),
        "81+": len([s for s in speeds if s > 80])
    }
    
    # Speed violations (assuming 80 km/h speed limit)
    speed_limit = 80
    violations = [s for s in speeds if s > speed_limit]
    violation_percentage = (len(violations) / len(speeds)) * 100 if speeds else 0
    
    return {
        "average_speed": round(avg_speed, 2),
        "median_speed": round(median_speed, 2),
        "max_speed": max_speed,
        "min_speed": min_speed,
        "speed_distribution": speed_ranges,
        "speed_violations": len(violations),
        "violation_percentage": round(violation_percentage, 2),
        "total_data_points": len(speeds)
    }


def analyze_geofence_events(events: List[GeofenceEvent]) -> Dict[str, Any]:
    """
    Analyze geofence events for patterns and violations
    
    Args:
        events: List of geofence events
    
    Returns:
        Geofence analysis dictionary
    """
    if not events:
        return {"total_events": 0}
    
    # Event type distribution
    event_types = Counter(event.event_type for event in events)
    
    # Events by geofence
    geofence_counts = Counter(event.geofence_id for event in events)
    
    # Events by vehicle
    vehicle_counts = Counter(event.vehicle_id for event in events)
    
    # Time-based analysis
    hourly_distribution = defaultdict(int)
    for event in events:
        hour = event.timestamp.hour
        hourly_distribution[hour] += 1
    
    # Recent events (last 24 hours)
    now = datetime.utcnow()
    recent_events = [
        event for event in events 
        if (now - event.timestamp).total_seconds() < 86400
    ]
    
    return {
        "total_events": len(events),
        "event_types": dict(event_types),
        "events_by_geofence": dict(geofence_counts.most_common(10)),
        "events_by_vehicle": dict(vehicle_counts.most_common(10)),
        "hourly_distribution": dict(hourly_distribution),
        "recent_events_24h": len(recent_events),
        "most_active_geofence": geofence_counts.most_common(1)[0] if geofence_counts else None,
        "most_active_vehicle": vehicle_counts.most_common(1)[0] if vehicle_counts else None
    }


def calculate_route_efficiency(route: VehicleRoute) -> Dict[str, Any]:
    """
    Calculate route efficiency metrics
    
    Args:
        route: Vehicle route object
    
    Returns:
        Route efficiency dictionary
    """
    if not route.route_points or len(route.route_points) < 2:
        return {"error": "Insufficient route data"}
    
    # Calculate actual distance traveled
    actual_distance = 0
    for i in range(1, len(route.route_points)):
        actual_distance += haversine_distance(
            route.route_points[i-1].latitude, route.route_points[i-1].longitude,
            route.route_points[i].latitude, route.route_points[i].longitude
        )
    
    # Calculate direct distance (as the crow flies)
    start_point = route.route_points[0]
    end_point = route.route_points[-1]
    direct_distance = haversine_distance(
        start_point.latitude, start_point.longitude,
        end_point.latitude, end_point.longitude
    )
    
    # Efficiency ratio
    efficiency_ratio = direct_distance / actual_distance if actual_distance > 0 else 0
    
    # Time calculations
    total_time = (end_point.timestamp - start_point.timestamp).total_seconds() / 3600
    avg_speed = actual_distance / total_time if total_time > 0 else 0
    
    return {
        "actual_distance_km": round(actual_distance, 2),
        "direct_distance_km": round(direct_distance, 2),
        "efficiency_ratio": round(efficiency_ratio, 3),
        "efficiency_percentage": round(efficiency_ratio * 100, 1),
        "total_time_hours": round(total_time, 2),
        "average_speed_kmh": round(avg_speed, 2),
        "extra_distance_km": round(actual_distance - direct_distance, 2)
    }


def generate_time_series_data(
    locations: List[VehicleLocation], 
    interval_minutes: int = 5
) -> List[Dict[str, Any]]:
    """
    Generate time series data for visualization
    
    Args:
        locations: List of vehicle locations
        interval_minutes: Interval for data points in minutes
    
    Returns:
        List of time series data points
    """
    if not locations:
        return []
    
    locations.sort(key=lambda x: x.timestamp)
    time_series = []
    
    start_time = locations[0].timestamp
    end_time = locations[-1].timestamp
    
    current_time = start_time
    location_index = 0
    
    while current_time <= end_time:
        # Find the closest location to current_time
        while (location_index < len(locations) - 1 and 
               locations[location_index + 1].timestamp <= current_time):
            location_index += 1
        
        location = locations[location_index]
        
        time_series.append({
            "timestamp": current_time.isoformat(),
            "latitude": location.latitude,
            "longitude": location.longitude,
            "speed": location.speed,
            "heading": location.heading,
            "accuracy": location.accuracy
        })
        
        current_time += timedelta(minutes=interval_minutes)
    
    return time_series


def calculate_dwell_time(
    locations: List[VehicleLocation], 
    geofence_center_lat: float,
    geofence_center_lon: float,
    geofence_radius_km: float
) -> Dict[str, Any]:
    """
    Calculate how long a vehicle dwelled in a geofenced area
    
    Args:
        locations: List of vehicle locations
        geofence_center_lat: Geofence center latitude
        geofence_center_lon: Geofence center longitude
        geofence_radius_km: Geofence radius in kilometers
    
    Returns:
        Dwell time analysis
    """
    if not locations:
        return {"total_dwell_time_minutes": 0, "visits": []}
    
    visits = []
    current_visit_start = None
    in_geofence = False
    
    for location in locations:
        distance = haversine_distance(
            location.latitude, location.longitude,
            geofence_center_lat, geofence_center_lon
        )
        
        is_inside = distance <= geofence_radius_km
        
        if is_inside and not in_geofence:
            # Entered geofence
            current_visit_start = location.timestamp
            in_geofence = True
        elif not is_inside and in_geofence:
            # Exited geofence
            if current_visit_start:
                visit_duration = (location.timestamp - current_visit_start).total_seconds() / 60
                visits.append({
                    "start_time": current_visit_start.isoformat(),
                    "end_time": location.timestamp.isoformat(),
                    "duration_minutes": round(visit_duration, 2)
                })
            in_geofence = False
    
    # Handle case where vehicle is still in geofence at end
    if in_geofence and current_visit_start and locations:
        visit_duration = (locations[-1].timestamp - current_visit_start).total_seconds() / 60
        visits.append({
            "start_time": current_visit_start.isoformat(),
            "end_time": locations[-1].timestamp.isoformat(),
            "duration_minutes": round(visit_duration, 2)
        })
    
    total_dwell_time = sum(visit["duration_minutes"] for visit in visits)
    
    return {
        "total_dwell_time_minutes": round(total_dwell_time, 2),
        "visit_count": len(visits),
        "visits": visits,
        "average_visit_duration": round(total_dwell_time / len(visits), 2) if visits else 0
    }


def detect_anomalies(locations: List[VehicleLocation]) -> List[Dict[str, Any]]:
    """
    Detect anomalies in vehicle movement patterns
    
    Args:
        locations: List of vehicle locations
    
    Returns:
        List of detected anomalies
    """
    if len(locations) < 3:
        return []
    
    anomalies = []
    
    # Speed anomalies
    speeds = [loc.speed for loc in locations if loc.speed is not None]
    if speeds:
        avg_speed = statistics.mean(speeds)
        speed_threshold = avg_speed * 2  # 2x average speed
        
        for i, location in enumerate(locations):
            if location.speed and location.speed > speed_threshold:
                anomalies.append({
                    "type": "speed_anomaly",
                    "timestamp": location.timestamp.isoformat(),
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "speed": location.speed,
                    "threshold": speed_threshold,
                    "description": f"Speed {location.speed} km/h exceeds threshold {speed_threshold:.1f} km/h"
                })
    
    # Location jump anomalies (unrealistic distance covered in short time)
    for i in range(1, len(locations)):
        prev_loc = locations[i-1]
        curr_loc = locations[i]
        
        distance = haversine_distance(
            prev_loc.latitude, prev_loc.longitude,
            curr_loc.latitude, curr_loc.longitude
        )
        
        time_diff = (curr_loc.timestamp - prev_loc.timestamp).total_seconds() / 3600
        
        if time_diff > 0:
            implied_speed = distance / time_diff
            
            # Flag if implied speed > 200 km/h (unrealistic for ground vehicles)
            if implied_speed > 200:
                anomalies.append({
                    "type": "location_jump",
                    "timestamp": curr_loc.timestamp.isoformat(),
                    "latitude": curr_loc.latitude,
                    "longitude": curr_loc.longitude,
                    "distance_km": round(distance, 2),
                    "time_diff_hours": round(time_diff, 3),
                    "implied_speed": round(implied_speed, 1),
                    "description": f"Unrealistic movement: {distance:.1f}km in {time_diff*3600:.0f}s"
                })
    
    return anomalies
