"""
Configuration for mock data scripts
"""

import os
from datetime import datetime, timedelta
import random

# Core service configuration
CORE_BASE_URL = os.getenv("CORE_SERVICE_URL", "http://localhost:21004")
MAINTENANCE_BASE_URL = os.getenv("MAINTENANCE_SERVICE_URL", "http://localhost:21004")

# Rate limiting configuration
REQUESTS_PER_MINUTE = 120  # 2 requests per second (0.5 seconds per request)
DELAY_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE  # 0.5 seconds between requests

# Authentication credentials
LOGIN_EMAIL = os.getenv("SAMFMS_LOGIN_EMAIL", "mvanheerdentuks@gmail.com")
LOGIN_PASSWORD = os.getenv("SAMFMS_LOGIN_PASSWORD", "Password2@")  # Will prompt if not set

# Default headers for requests (token will be added after login)
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "SAMFMS-MockDataGenerator/1.0"
}

# Mock data configurations
VEHICLE_TYPES = [
    "sedan", "suv", "truck", "van", "pickup_truck", 
    "bus", "motorcycle", "delivery_van", "semi_truck"
]

VEHICLE_MAKES = [
    "Toyota", "Ford", "Chevrolet", "Honda", "Nissan", 
    "Mercedes-Benz", "BMW", "Audi", "Volkswagen", "Hyundai"
]

VEHICLE_MODELS = {
    "Toyota": ["Camry", "Corolla", "RAV4", "Prius", "Tacoma"],
    "Ford": ["F-150", "Explorer", "Escape", "Mustang", "Transit"],
    "Chevrolet": ["Silverado", "Equinox", "Malibu", "Tahoe", "Express"],
    "Honda": ["Civic", "Accord", "CR-V", "Pilot", "Ridgeline"],
    "Nissan": ["Altima", "Sentra", "Rogue", "Pathfinder", "Titan"],
    "Mercedes-Benz": ["C-Class", "E-Class", "GLC", "Sprinter", "Actros"],
    "BMW": ["3 Series", "X3", "X5", "5 Series", "X1"],
    "Audi": ["A4", "Q5", "A6", "Q7", "A3"],
    "Volkswagen": ["Jetta", "Passat", "Tiguan", "Atlas", "Crafter"],
    "Hyundai": ["Elantra", "Sonata", "Tucson", "Santa Fe", "H-1"]
}

MAINTENANCE_TYPES = [
    "oil_change", "tire_rotation", "brake_inspection", "transmission_service",
    "air_filter_replacement", "battery_check", "coolant_flush", "tune_up",
    "alignment", "inspection", "engine_diagnostic", "suspension_check"
]

LICENSE_TYPES = [
    "vehicle_registration", "inspection_certificate", "insurance_certificate",
    "emissions_certificate", "commercial_permit", "safety_certificate"
]

DRIVER_LICENSES = [
    "class_a_cdl", "class_b_cdl", "class_c_regular", "motorcycle_license",
    "commercial_permit", "hazmat_endorsement", "passenger_endorsement"
]

# Location data
CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"
]

STATES = [
    "NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA", "TX", "CA"
]

# Utility functions
def generate_vin():
    """Generate a realistic VIN number"""
    chars = "ABCDEFGHJKLMNPRSTUVWXYZ1234567890"
    return ''.join(random.choices(chars, k=17))

def generate_license_plate():
    """Generate a realistic license plate"""
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    numbers = "0123456789"
    formats = [
        f"{random.choice(letters)}{random.choice(letters)}{random.choice(letters)}-{random.randint(1000, 9999)}",
        f"{random.randint(100, 999)}-{random.choice(letters)}{random.choice(letters)}{random.choice(letters)}",
        f"{random.choice(letters)}{random.randint(100, 999)}{random.choice(letters)}{random.choice(letters)}"
    ]
    return random.choice(formats)

def generate_phone_number():
    """Generate a realistic phone number"""
    return f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"

def random_date_in_range(start_days_ago, end_days_ago=0):
    """Generate a random date within a range"""
    start_date = datetime.now() - timedelta(days=start_days_ago)
    end_date = datetime.now() - timedelta(days=end_days_ago)
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between + 1)
    return start_date + timedelta(days=random_days)

def future_date_in_range(start_days_ahead, end_days_ahead):
    """Generate a random future date within a range"""
    start_date = datetime.now() + timedelta(days=start_days_ahead)
    end_date = datetime.now() + timedelta(days=end_days_ahead)
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between + 1)
    return start_date + timedelta(days=random_days)

def generate_email(first_name, last_name, domain="samfms.com"):
    """Generate an email address"""
    return f"{first_name.lower()}.{last_name.lower()}@{domain}"
