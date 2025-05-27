"""
Geospatial Utilities for GPS Tracking System

Contains functions for distance calculations, geofencing, and spatial operations.
"""

import math
from typing import List, Tuple, Dict, Any
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon
from shapely.ops import transform
import pyproj
from functools import partial

from ..models.location import VehicleLocation, Coordinate
from ..models.geofence import Geofence


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth using Haversine formula
    
    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees
    
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    return c * r


def geodesic_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance using geodesic (more accurate for long distances)
    
    Returns:
        Distance in kilometers
    """
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the bearing from point 1 to point 2
    
    Returns:
        Bearing in degrees (0-360)
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlon = lon2 - lon1
    
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing


def calculate_speed(distance_km: float, time_hours: float) -> float:
    """
    Calculate speed in km/h
    
    Args:
        distance_km: Distance in kilometers
        time_hours: Time in hours
    
    Returns:
        Speed in km/h
    """
    if time_hours <= 0:
        return 0
    return distance_km / time_hours


def is_point_in_circle(
    point_lat: float, 
    point_lon: float, 
    center_lat: float, 
    center_lon: float, 
    radius_km: float
) -> bool:
    """
    Check if a point is within a circular geofence
    
    Args:
        point_lat, point_lon: Point coordinates
        center_lat, center_lon: Circle center coordinates
        radius_km: Circle radius in kilometers
    
    Returns:
        True if point is inside the circle
    """
    distance = haversine_distance(point_lat, point_lon, center_lat, center_lon)
    return distance <= radius_km


def is_point_in_polygon(point_lat: float, point_lon: float, polygon_coords: List[Coordinate]) -> bool:
    """
    Check if a point is within a polygonal geofence
    
    Args:
        point_lat, point_lon: Point coordinates
        polygon_coords: List of polygon coordinates
    
    Returns:
        True if point is inside the polygon
    """
    point = Point(point_lon, point_lat)
    polygon_points = [(coord.longitude, coord.latitude) for coord in polygon_coords]
    polygon = Polygon(polygon_points)
    
    return polygon.contains(point)


def point_to_line_distance(
    point_lat: float, 
    point_lon: float, 
    line_start_lat: float, 
    line_start_lon: float,
    line_end_lat: float, 
    line_end_lon: float
) -> float:
    """
    Calculate the shortest distance from a point to a line segment
    
    Returns:
        Distance in kilometers
    """
    # Convert to UTM for accurate distance calculations
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    
    # Transform coordinates
    point_x, point_y = transformer.transform(point_lon, point_lat)
    line_start_x, line_start_y = transformer.transform(line_start_lon, line_start_lat)
    line_end_x, line_end_y = transformer.transform(line_end_lon, line_end_lat)
    
    # Calculate distance from point to line
    A = point_x - line_start_x
    B = point_y - line_start_y
    C = line_end_x - line_start_x
    D = line_end_y - line_start_y
    
    dot = A * C + B * D
    len_sq = C * C + D * D
    
    if len_sq == 0:
        # Line start and end are the same point
        return math.sqrt(A * A + B * B) / 1000  # Convert to km
    
    param = dot / len_sq
    
    if param < 0:
        xx = line_start_x
        yy = line_start_y
    elif param > 1:
        xx = line_end_x
        yy = line_end_y
    else:
        xx = line_start_x + param * C
        yy = line_start_y + param * D
    
    dx = point_x - xx
    dy = point_y - yy
    
    return math.sqrt(dx * dx + dy * dy) / 1000  # Convert to km


def calculate_route_distance(locations: List[VehicleLocation]) -> float:
    """
    Calculate total distance of a route from a list of locations
    
    Returns:
        Total distance in kilometers
    """
    if len(locations) < 2:
        return 0.0
    
    total_distance = 0.0
    for i in range(1, len(locations)):
        distance = haversine_distance(
            locations[i-1].latitude, locations[i-1].longitude,
            locations[i].latitude, locations[i].longitude
        )
        total_distance += distance
    
    return total_distance


def get_bounding_box(locations: List[VehicleLocation], buffer_km: float = 1.0) -> Dict[str, float]:
    """
    Get bounding box for a list of locations with buffer
    
    Args:
        locations: List of vehicle locations
        buffer_km: Buffer distance in kilometers
    
    Returns:
        Dictionary with min_lat, max_lat, min_lon, max_lon
    """
    if not locations:
        return {"min_lat": 0, "max_lat": 0, "min_lon": 0, "max_lon": 0}
    
    lats = [loc.latitude for loc in locations]
    lons = [loc.longitude for loc in locations]
    
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    # Add buffer (approximate conversion from km to degrees)
    lat_buffer = buffer_km / 111.0  # 1 degree lat ≈ 111 km
    lon_buffer = buffer_km / (111.0 * math.cos(math.radians((min_lat + max_lat) / 2)))
    
    return {
        "min_lat": min_lat - lat_buffer,
        "max_lat": max_lat + lat_buffer,
        "min_lon": min_lon - lon_buffer,
        "max_lon": max_lon + lon_buffer
    }


def calculate_center_point(locations: List[VehicleLocation]) -> Tuple[float, float]:
    """
    Calculate the center point of a list of locations
    
    Returns:
        Tuple of (latitude, longitude)
    """
    if not locations:
        return (0.0, 0.0)
    
    avg_lat = sum(loc.latitude for loc in locations) / len(locations)
    avg_lon = sum(loc.longitude for loc in locations) / len(locations)
    
    return (avg_lat, avg_lon)


def simplify_route(locations: List[VehicleLocation], tolerance_km: float = 0.1) -> List[VehicleLocation]:
    """
    Simplify a route by removing points that are too close together
    
    Args:
        locations: List of locations to simplify
        tolerance_km: Minimum distance between points in kilometers
    
    Returns:
        Simplified list of locations
    """
    if len(locations) <= 2:
        return locations
    
    simplified = [locations[0]]  # Always keep first point
    
    for i in range(1, len(locations) - 1):
        last_kept = simplified[-1]
        current = locations[i]
        
        distance = haversine_distance(
            last_kept.latitude, last_kept.longitude,
            current.latitude, current.longitude
        )
        
        if distance >= tolerance_km:
            simplified.append(current)
    
    simplified.append(locations[-1])  # Always keep last point
    return simplified


def detect_stops(
    locations: List[VehicleLocation], 
    min_stop_duration_minutes: int = 5,
    max_stop_radius_meters: int = 50
) -> List[Dict[str, Any]]:
    """
    Detect stops in a route based on time and location clustering
    
    Args:
        locations: List of locations sorted by timestamp
        min_stop_duration_minutes: Minimum duration to consider a stop
        max_stop_radius_meters: Maximum radius for points to be considered same location
    
    Returns:
        List of stop dictionaries with start_time, end_time, duration, location
    """
    if len(locations) < 2:
        return []
    
    stops = []
    current_stop_start = None
    current_stop_locations = []
    
    for i, location in enumerate(locations):
        if i == 0:
            current_stop_start = location
            current_stop_locations = [location]
            continue
        
        # Check if current location is within stop radius of the first location in current stop
        distance_m = haversine_distance(
            current_stop_start.latitude, current_stop_start.longitude,
            location.latitude, location.longitude
        ) * 1000  # Convert to meters
        
        if distance_m <= max_stop_radius_meters:
            # Still in the same location
            current_stop_locations.append(location)
        else:
            # Moved to a new location, check if previous locations constitute a stop
            if len(current_stop_locations) >= 2:
                duration_minutes = (
                    current_stop_locations[-1].timestamp - current_stop_locations[0].timestamp
                ).total_seconds() / 60
                
                if duration_minutes >= min_stop_duration_minutes:
                    # Calculate center of stop
                    center_lat = sum(loc.latitude for loc in current_stop_locations) / len(current_stop_locations)
                    center_lon = sum(loc.longitude for loc in current_stop_locations) / len(current_stop_locations)
                    
                    stops.append({
                        "start_time": current_stop_locations[0].timestamp,
                        "end_time": current_stop_locations[-1].timestamp,
                        "duration_minutes": duration_minutes,
                        "latitude": center_lat,
                        "longitude": center_lon,
                        "point_count": len(current_stop_locations)
                    })
            
            # Start new potential stop
            current_stop_start = location
            current_stop_locations = [location]
    
    # Check final stop
    if len(current_stop_locations) >= 2:
        duration_minutes = (
            current_stop_locations[-1].timestamp - current_stop_locations[0].timestamp
        ).total_seconds() / 60
        
        if duration_minutes >= min_stop_duration_minutes:
            center_lat = sum(loc.latitude for loc in current_stop_locations) / len(current_stop_locations)
            center_lon = sum(loc.longitude for loc in current_stop_locations) / len(current_stop_locations)
            
            stops.append({
                "start_time": current_stop_locations[0].timestamp,
                "end_time": current_stop_locations[-1].timestamp,
                "duration_minutes": duration_minutes,
                "latitude": center_lat,
                "longitude": center_lon,
                "point_count": len(current_stop_locations)
            })
    
    return stops


def check_geofence_violation(location: VehicleLocation, geofence: Geofence) -> bool:
    """
    Check if a location violates a geofence
    
    Args:
        location: Vehicle location to check
        geofence: Geofence to check against
    
    Returns:
        True if location violates the geofence rules
    """
    if geofence.shape == "circle":
        is_inside = is_point_in_circle(
            location.latitude, location.longitude,
            geofence.center.latitude, geofence.center.longitude,
            geofence.radius
        )
    elif geofence.shape == "polygon":
        is_inside = is_point_in_polygon(
            location.latitude, location.longitude,
            geofence.coordinates
        )
    else:
        return False
    
    # Check violation based on geofence type
    if geofence.fence_type == "inclusion":
        return not is_inside  # Violation if outside inclusion zone
    elif geofence.fence_type == "exclusion":
        return is_inside  # Violation if inside exclusion zone
    
    return False
