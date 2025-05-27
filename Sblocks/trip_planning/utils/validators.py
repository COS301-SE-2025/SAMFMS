"""Validation utilities for trip planning service"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
from pydantic import ValidationError
from ..models.models import TripStatus, VehicleStatus, DriverStatus


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Validate geographical coordinates"""
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format"""
    # Simple regex for phone validation (adjust based on requirements)
    phone_pattern = r'^[\+]?[1-9]?\d{9,15}$'
    return bool(re.match(phone_pattern, phone.replace(' ', '').replace('-', '')))


def validate_email(email: str) -> bool:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def validate_license_plate(plate: str) -> bool:
    """Validate license plate format"""
    # Basic validation - adjust based on local requirements
    plate_pattern = r'^[A-Z0-9-]{3,10}$'
    return bool(re.match(plate_pattern, plate.upper().replace(' ', '')))


def validate_trip_data(trip_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate trip data and return validation results"""
    errors = []
    warnings = []
    
    # Required fields check
    required_fields = ['origin', 'destination', 'scheduled_start_time']
    for field in required_fields:
        if field not in trip_data or trip_data[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Validate coordinates
    if 'origin' in trip_data and trip_data['origin']:
        origin = trip_data['origin']
        if 'latitude' in origin and 'longitude' in origin:
            if not validate_coordinates(origin['latitude'], origin['longitude']):
                errors.append("Invalid origin coordinates")
        else:
            errors.append("Origin must include latitude and longitude")
    
    if 'destination' in trip_data and trip_data['destination']:
        destination = trip_data['destination']
        if 'latitude' in destination and 'longitude' in destination:
            if not validate_coordinates(destination['latitude'], destination['longitude']):
                errors.append("Invalid destination coordinates")
        else:
            errors.append("Destination must include latitude and longitude")
    
    # Validate time constraints
    if 'scheduled_start_time' in trip_data:
        start_time = trip_data['scheduled_start_time']
        if isinstance(start_time, str):
            try:
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                errors.append("Invalid scheduled_start_time format")
        
        # Check if start time is in the past
        if isinstance(start_time, datetime) and start_time < datetime.utcnow():
            warnings.append("Scheduled start time is in the past")
        
        # Check if start time is too far in the future (e.g., more than 1 year)
        if isinstance(start_time, datetime) and start_time > datetime.utcnow() + timedelta(days=365):
            warnings.append("Scheduled start time is more than 1 year in the future")
    
    # Validate passenger count
    if 'passenger_count' in trip_data:
        passenger_count = trip_data['passenger_count']
        if not isinstance(passenger_count, int) or passenger_count < 1:
            errors.append("Passenger count must be a positive integer")
        elif passenger_count > 50:  # Reasonable upper limit
            warnings.append("Unusually high passenger count")
    
    # Validate trip status
    if 'status' in trip_data:
        status = trip_data['status']
        if isinstance(status, str):
            try:
                TripStatus(status)
            except ValueError:
                errors.append(f"Invalid trip status: {status}")
    
    # Validate distance if provided
    if 'estimated_distance' in trip_data:
        distance = trip_data['estimated_distance']
        if not isinstance(distance, (int, float)) or distance < 0:
            errors.append("Estimated distance must be a positive number")
        elif distance > 10000:  # More than 10,000 km seems unreasonable
            warnings.append("Estimated distance is unusually high")
    
    # Validate duration if provided
    if 'estimated_duration' in trip_data:
        duration = trip_data['estimated_duration']
        if not isinstance(duration, (int, float)) or duration <= 0:
            errors.append("Estimated duration must be a positive number")
        elif duration > 24:  # More than 24 hours
            warnings.append("Estimated duration is more than 24 hours")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_vehicle_data(vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate vehicle data and return validation results"""
    errors = []
    warnings = []
    
    # Required fields check
    required_fields = ['license_plate', 'make', 'model', 'year', 'capacity']
    for field in required_fields:
        if field not in vehicle_data or vehicle_data[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Validate license plate
    if 'license_plate' in vehicle_data:
        if not validate_license_plate(vehicle_data['license_plate']):
            errors.append("Invalid license plate format")
    
    # Validate year
    if 'year' in vehicle_data:
        year = vehicle_data['year']
        current_year = datetime.now().year
        if not isinstance(year, int) or year < 1900 or year > current_year + 1:
            errors.append("Invalid vehicle year")
        elif year < current_year - 30:
            warnings.append("Vehicle is more than 30 years old")
    
    # Validate capacity
    if 'capacity' in vehicle_data:
        capacity = vehicle_data['capacity']
        if not isinstance(capacity, int) or capacity < 1:
            errors.append("Vehicle capacity must be a positive integer")
        elif capacity > 100:
            warnings.append("Unusually high vehicle capacity")
    
    # Validate status
    if 'status' in vehicle_data:
        status = vehicle_data['status']
        if isinstance(status, str):
            try:
                VehicleStatus(status)
            except ValueError:
                errors.append(f"Invalid vehicle status: {status}")
    
    # Validate fuel efficiency if provided
    if 'fuel_efficiency' in vehicle_data:
        efficiency = vehicle_data['fuel_efficiency']
        if not isinstance(efficiency, (int, float)) or efficiency <= 0:
            errors.append("Fuel efficiency must be a positive number")
        elif efficiency > 50:  # More than 50 km/l seems unrealistic
            warnings.append("Unusually high fuel efficiency")
        elif efficiency < 3:  # Less than 3 km/l seems very low
            warnings.append("Very low fuel efficiency")
    
    # Validate mileage if provided
    if 'mileage' in vehicle_data:
        mileage = vehicle_data['mileage']
        if not isinstance(mileage, (int, float)) or mileage < 0:
            errors.append("Mileage must be a non-negative number")
        elif mileage > 1000000:  # More than 1 million km
            warnings.append("Very high mileage")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_driver_data(driver_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate driver data and return validation results"""
    errors = []
    warnings = []
    
    # Required fields check
    required_fields = ['first_name', 'last_name', 'employee_id', 'email', 'phone', 'license']
    for field in required_fields:
        if field not in driver_data or driver_data[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Validate email
    if 'email' in driver_data:
        if not validate_email(driver_data['email']):
            errors.append("Invalid email format")
    
    # Validate phone
    if 'phone' in driver_data:
        if not validate_phone_number(driver_data['phone']):
            errors.append("Invalid phone number format")
    
    # Validate names
    for name_field in ['first_name', 'last_name']:
        if name_field in driver_data:
            name = driver_data[name_field].strip()
            if len(name) < 2:
                errors.append(f"{name_field} must be at least 2 characters long")
            elif len(name) > 50:
                errors.append(f"{name_field} must be less than 50 characters long")
            elif not re.match(r'^[a-zA-Z\s\'-]+$', name):
                errors.append(f"{name_field} contains invalid characters")
    
    # Validate employee ID
    if 'employee_id' in driver_data:
        emp_id = driver_data['employee_id']
        if not re.match(r'^[A-Z0-9-]{3,15}$', emp_id.upper()):
            errors.append("Invalid employee ID format")
    
    # Validate license
    if 'license' in driver_data and driver_data['license']:
        license_data = driver_data['license']
        
        # Check license number
        if 'license_number' in license_data:
            license_num = license_data['license_number']
            if not re.match(r'^[A-Z0-9]{5,20}$', license_num.upper().replace(' ', '')):
                errors.append("Invalid license number format")
        
        # Check expiry date
        if 'expiry_date' in license_data:
            expiry = license_data['expiry_date']
            if isinstance(expiry, str):
                try:
                    expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
                except ValueError:
                    errors.append("Invalid license expiry date format")
            
            if isinstance(expiry, datetime):
                if expiry < datetime.utcnow():
                    errors.append("Driver license has expired")
                elif expiry < datetime.utcnow() + timedelta(days=30):
                    warnings.append("Driver license expires within 30 days")
    
    # Validate status
    if 'status' in driver_data:
        status = driver_data['status']
        if isinstance(status, str):
            try:
                DriverStatus(status)
            except ValueError:
                errors.append(f"Invalid driver status: {status}")
    
    # Validate hire date if provided
    if 'hire_date' in driver_data:
        hire_date = driver_data['hire_date']
        if isinstance(hire_date, str):
            try:
                hire_date = datetime.fromisoformat(hire_date.replace('Z', '+00:00'))
            except ValueError:
                errors.append("Invalid hire date format")
        
        if isinstance(hire_date, datetime):
            if hire_date > datetime.utcnow():
                errors.append("Hire date cannot be in the future")
            elif hire_date < datetime.utcnow() - timedelta(days=365 * 50):  # 50 years ago
                warnings.append("Hire date is more than 50 years ago")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_route_data(route_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate route data and return validation results"""
    errors = []
    warnings = []
    
    # Required fields check
    required_fields = ['name', 'waypoints']
    for field in required_fields:
        if field not in route_data or route_data[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Validate route name
    if 'name' in route_data:
        name = route_data['name'].strip()
        if len(name) < 3:
            errors.append("Route name must be at least 3 characters long")
        elif len(name) > 100:
            errors.append("Route name must be less than 100 characters long")
    
    # Validate waypoints
    if 'waypoints' in route_data:
        waypoints = route_data['waypoints']
        if not isinstance(waypoints, list):
            errors.append("Waypoints must be a list")
        elif len(waypoints) < 2:
            errors.append("Route must have at least 2 waypoints")
        else:
            for i, waypoint in enumerate(waypoints):
                if not isinstance(waypoint, dict):
                    errors.append(f"Waypoint {i+1} must be an object")
                    continue
                
                if 'latitude' not in waypoint or 'longitude' not in waypoint:
                    errors.append(f"Waypoint {i+1} must include latitude and longitude")
                    continue
                
                if not validate_coordinates(waypoint['latitude'], waypoint['longitude']):
                    errors.append(f"Waypoint {i+1} has invalid coordinates")
    
    # Validate distance if provided
    if 'total_distance' in route_data:
        distance = route_data['total_distance']
        if not isinstance(distance, (int, float)) or distance <= 0:
            errors.append("Total distance must be a positive number")
        elif distance > 10000:  # More than 10,000 km
            warnings.append("Route distance is unusually long")
    
    # Validate duration if provided
    if 'estimated_duration' in route_data:
        duration = route_data['estimated_duration']
        if not isinstance(duration, (int, float)) or duration <= 0:
            errors.append("Estimated duration must be a positive number")
        elif duration > 24:  # More than 24 hours
            warnings.append("Route duration is more than 24 hours")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def validate_schedule_data(schedule_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate schedule data and return validation results"""
    errors = []
    warnings = []
    
    # Required fields check
    required_fields = ['trip_id', 'vehicle_id', 'driver_id', 'scheduled_start_time']
    for field in required_fields:
        if field not in schedule_data or schedule_data[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Validate time fields
    time_fields = ['scheduled_start_time', 'scheduled_end_time', 'actual_start_time', 'actual_end_time']
    for field in time_fields:
        if field in schedule_data and schedule_data[field]:
            time_value = schedule_data[field]
            if isinstance(time_value, str):
                try:
                    datetime.fromisoformat(time_value.replace('Z', '+00:00'))
                except ValueError:
                    errors.append(f"Invalid {field} format")
    
    # Validate that end time is after start time
    if ('scheduled_start_time' in schedule_data and 'scheduled_end_time' in schedule_data and
        schedule_data['scheduled_start_time'] and schedule_data['scheduled_end_time']):
        
        try:
            start = schedule_data['scheduled_start_time']
            end = schedule_data['scheduled_end_time']
            
            if isinstance(start, str):
                start = datetime.fromisoformat(start.replace('Z', '+00:00'))
            if isinstance(end, str):
                end = datetime.fromisoformat(end.replace('Z', '+00:00'))
            
            if end <= start:
                errors.append("Scheduled end time must be after start time")
        except (ValueError, TypeError):
            pass  # Already handled by individual field validation
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
