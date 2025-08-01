#!/usr/bin/env python3
"""
Mock User Data Generator
Creates realistic user data (drivers and fleet managers) via Core service API calls
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from config import (
    CITIES, STATES, DRIVER_LICENSES,
    generate_phone_number, generate_email
)
from api_utils import CoreServiceClient, batch_create_with_delay, log_creation_result, logger


# Sample names for users
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Helen", "Mark", "Sandra", "Donald", "Donna",
    "Steven", "Carol", "Paul", "Ruth", "Andrew", "Sharon", "Joshua", "Michelle"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"
]


def generate_driver_data(count: int = 30) -> List[Dict[str, Any]]:
    """Generate mock driver data"""
    drivers = []
    
    logger.info(f"Generating {count} mock drivers...")
    
    for i in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        # Generate realistic age (21-65 for drivers)
        age = random.randint(21, 65)
        birth_date = datetime.now() - timedelta(days=age * 365 + random.randint(0, 365))
        
        # Generate hire date (1-10 years ago)
        hire_date = datetime.now() - timedelta(days=random.randint(365, 3650))
        
        # Generate location
        city_index = random.randint(0, len(CITIES) - 1)
        city = CITIES[city_index]
        state = STATES[city_index]
        
        driver = {
            "username": f"{first_name.lower()}.{last_name.lower()}.{random.randint(100, 999)}",
            "email": generate_email(first_name, last_name),
            "password": "Password1!",  # Standard password for all mock users
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "role": "driver",
            "phone": generate_phone_number(),
            "date_of_birth": birth_date.date().isoformat(),
            "hire_date": hire_date.date().isoformat(),
            "status": random.choice(["active", "active", "active", "inactive"]),
            "address": {
                "street": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Elm', 'Cedar', 'Maple'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr', 'Rd'])}",
                "city": city,
                "state": state,
                "zip_code": f"{random.randint(10000, 99999)}",
                "country": "USA"
            },
            "emergency_contact": {
                "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "relationship": random.choice(["spouse", "parent", "sibling", "friend"]),
                "phone": generate_phone_number()
            },
            "driver_info": {
                "license_number": f"DL{random.randint(100000000, 999999999)}",
                "license_class": random.choice(DRIVER_LICENSES),
                "license_expiry": (datetime.now() + timedelta(days=random.randint(30, 1095))).date().isoformat(),
                "years_experience": min(age - 16, random.randint(2, 30)),
                "clean_record": random.choice([True, True, True, False]),  # 75% clean records
                "certifications": random.sample([
                    "defensive_driving", "hazmat", "passenger_transport", 
                    "commercial_vehicle", "safety_training", "first_aid"
                ], k=random.randint(1, 3))
            },
            "employment": {
                "employee_id": f"EMP{random.randint(10000, 99999)}",
                "department": random.choice(["transportation", "delivery", "logistics", "field_services"]),
                "shift": random.choice(["day", "night", "rotating"]),
                "salary": random.randint(35000, 75000),
                "benefits_eligible": True
            },
            "preferences": {
                "preferred_vehicle_types": random.sample(["sedan", "suv", "truck", "van"], k=random.randint(1, 2)),
                "max_shift_hours": random.choice([8, 10, 12]),
                "weekend_availability": random.choice([True, False]),
                "travel_radius": random.randint(25, 100)  # miles
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        drivers.append(driver)
        
    logger.info(f"Generated {len(drivers)} driver records")
    return drivers


def generate_fleet_manager_data(count: int = 10) -> List[Dict[str, Any]]:
    """Generate mock fleet manager data"""
    managers = []
    
    logger.info(f"Generating {count} mock fleet managers...")
    
    for i in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        # Generate realistic age (25-60 for managers)
        age = random.randint(25, 60)
        birth_date = datetime.now() - timedelta(days=age * 365 + random.randint(0, 365))
        
        # Generate hire date (2-15 years ago)
        hire_date = datetime.now() - timedelta(days=random.randint(730, 5475))
        
        # Generate location
        city_index = random.randint(0, len(CITIES) - 1)
        city = CITIES[city_index]
        state = STATES[city_index]
        
        manager = {
            "username": f"{first_name.lower()}.{last_name.lower()}.mgr{random.randint(10, 99)}",
            "email": generate_email(first_name, last_name, "management.samfms.com"),
            "password": "Password1!",  # Standard password for all mock users
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "role": "fleet_manager",
            "phone": generate_phone_number(),
            "date_of_birth": birth_date.date().isoformat(),
            "hire_date": hire_date.date().isoformat(),
            "status": "active",
            "address": {
                "street": f"{random.randint(100, 9999)} {random.choice(['Executive', 'Corporate', 'Business', 'Professional'])} {random.choice(['Dr', 'Blvd', 'Way', 'Circle'])}",
                "city": city,
                "state": state,
                "zip_code": f"{random.randint(10000, 99999)}",
                "country": "USA"
            },
            "emergency_contact": {
                "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "relationship": random.choice(["spouse", "parent", "sibling"]),
                "phone": generate_phone_number()
            },
            "management_info": {
                "employee_id": f"MGR{random.randint(1000, 9999)}",
                "department": "fleet_management",
                "team_size": random.randint(5, 25),
                "responsibilities": random.sample([
                    "vehicle_allocation", "maintenance_scheduling", "driver_management",
                    "cost_optimization", "compliance_monitoring", "route_planning",
                    "safety_oversight", "vendor_management", "reporting"
                ], k=random.randint(3, 6)),
                "certifications": random.sample([
                    "fleet_management", "transportation_management", "safety_compliance",
                    "project_management", "lean_six_sigma", "leadership"
                ], k=random.randint(2, 4))
            },
            "employment": {
                "salary": random.randint(60000, 120000),
                "bonus_eligible": True,
                "stock_options": random.choice([True, False]),
                "benefits_tier": "premium"
            },
            "permissions": {
                "vehicle_management": True,
                "driver_management": True,
                "maintenance_oversight": True,
                "reporting_access": True,
                "budget_authority": random.randint(10000, 100000),
                "approval_levels": random.sample([
                    "vehicle_purchase", "maintenance_approval", "driver_hiring",
                    "route_changes", "vendor_contracts"
                ], k=random.randint(2, 4))
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        managers.append(manager)
        
    logger.info(f"Generated {len(managers)} fleet manager records")
    return managers


async def create_mock_users(drivers_count: int = 30, managers_count: int = 10):
    """Create mock users via Core service"""
    logger.info("👥 Starting user creation process...")
    
    # Generate user data
    driver_data = generate_driver_data(drivers_count)
    manager_data = generate_fleet_manager_data(managers_count)
    
    all_users = driver_data + manager_data
    
    # Create users via Core service
    async with CoreServiceClient() as core_client:
        logger.info("Creating users via Core service...")
        
        results = await batch_create_with_delay(
            core_client.create_user,
            all_users,
            batch_size=3  # 3 users per batch to be gentle
        )
        
        # Log results
        successful_users = []
        failed_users = []
        successful_drivers = 0
        successful_managers = 0
        
        for i, result in enumerate(results):
            user_name = f"{all_users[i]['first_name']} {all_users[i]['last_name']} ({all_users[i]['role']})"
            log_creation_result("user", result, user_name)
            
            if not result.get("error"):
                successful_users.append(result)
                if all_users[i]['role'] == 'driver':
                    successful_drivers += 1
                else:
                    successful_managers += 1
            else:
                failed_users.append(result)
        
        logger.info(f"\n📊 User Creation Summary:")
        logger.info(f"✅ Successfully created: {len(successful_users)} users")
        logger.info(f"   - Drivers: {successful_drivers}")
        logger.info(f"   - Fleet Managers: {successful_managers}")
        logger.info(f"❌ Failed to create: {len(failed_users)} users")
        
        if failed_users:
            logger.warning("Failed users - please check Core service logs")
            
        return successful_users


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create mock user data")
    parser.add_argument("--drivers", type=int, default=30, help="Number of drivers to create (default: 30)")
    parser.add_argument("--managers", type=int, default=10, help="Number of fleet managers to create (default: 10)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Creating {args.drivers} drivers and {args.managers} fleet managers...")
    
    try:
        users = asyncio.run(create_mock_users(args.drivers, args.managers))
        logger.info(f"🎉 User creation process completed! Created {len(users)} users.")
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Error during user creation: {e}")
        raise
