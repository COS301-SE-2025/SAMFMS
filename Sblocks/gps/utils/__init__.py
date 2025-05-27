"""
GPS Utilities Package

Contains utility functions for geospatial calculations and analytics.
"""

from .geospatial import (
    haversine_distance,
    geodesic_distance,
    calculate_bearing,
    calculate_speed,
    is_point_in_circle,
    is_point_in_polygon,
    point_to_line_distance,
    calculate_route_distance,
    get_bounding_box,
    calculate_center_point,
    simplify_route,
    detect_stops,
    check_geofence_violation
)

from .analytics import (
    calculate_vehicle_metrics,
    calculate_fleet_summary,
    analyze_speed_patterns,
    analyze_geofence_events,
    calculate_route_efficiency,
    generate_time_series_data,
    calculate_dwell_time,
    detect_anomalies
)

__all__ = [
    # Geospatial utilities
    "haversine_distance",
    "geodesic_distance", 
    "calculate_bearing",
    "calculate_speed",
    "is_point_in_circle",
    "is_point_in_polygon",
    "point_to_line_distance",
    "calculate_route_distance",
    "get_bounding_box",
    "calculate_center_point",
    "simplify_route",
    "detect_stops",
    "check_geofence_violation",
    
    # Analytics utilities
    "calculate_vehicle_metrics",
    "calculate_fleet_summary",
    "analyze_speed_patterns",
    "analyze_geofence_events",
    "calculate_route_efficiency",
    "generate_time_series_data",
    "calculate_dwell_time",
    "detect_anomalies"
]
