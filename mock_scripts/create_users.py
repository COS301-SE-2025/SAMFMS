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
    """Generate mock driver data using the same structure as frontend"""
    drivers = []
    
    logger.info(f"Generating {count} mock drivers...")
    
    # Frontend license types from AddDriverModal.jsx
    license_types = [
        'A', 'A1', 'B', 'C', 'C1', 'EB', 'EC', 'EC1'
    ]
    
    # Frontend departments from AddDriverModal.jsx
    departments = [
        'Operations', 'Logistics', 'Maintenance', 'Administration', 'Security'
    ]
    
    for i in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        
        # Generate realistic dates
        joining_date = datetime.now() - timedelta(days=random.randint(30, 1095))
        license_expiry = datetime.now() + timedelta(days=random.randint(30, 1095))
        
        # Generate security_id required by Management service
        import uuid
        security_id = str(uuid.uuid4())
        
        # Create driver data matching frontend structure exactly
        driver = {
            # Frontend form fields only - matching AddDriverModal.jsx exactly
            "full_name": full_name,
            "email": generate_email(first_name, last_name),
            "phoneNo": generate_phone_number(),
            "emergency_contact": generate_phone_number(),
            "license_number": f"SA{random.randint(1000000000000, 9999999999999)}",  # SA format
            "license_type": random.choice(license_types),
            "license_expiry": license_expiry.date().isoformat(),
            "department": random.choice(departments),
            "joining_date": joining_date.date().isoformat(),
            # Required by Management service backend
            "security_id": security_id,
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
    """Create mock users and drivers via appropriate service endpoints with proper security_id linking"""
    logger.info("👥 Starting user creation process...")
    
    # Generate user data
    driver_data = generate_driver_data(drivers_count)
    manager_data = generate_fleet_manager_data(managers_count)
    
    # Create users via appropriate endpoints
    async with CoreServiceClient() as core_client:
        
        # Create drivers using two-step process: Core auth first, then Management service
        if drivers_count > 0:
            logger.info(f"Creating {len(driver_data)} drivers via two-step process...")
            
            # Step 1: Create users in Core service for authentication
            logger.info("Step 1: Creating driver users in Core service...")
            core_user_data = []
            for driver in driver_data:
                # Parse full_name into first_name and last_name
                name_parts = driver['full_name'].split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                user_data = {
                    "username": f"{first_name.lower()}.{last_name.lower()}.{random.randint(100, 999)}",
                    "email": driver['email'],
                    "password": "Password1!",
                    "first_name": first_name,
                    "last_name": last_name,
                    "full_name": driver['full_name'],
                    "role": "driver",
                    "phone": driver['phoneNo'],
                    "status": "active"
                }
                core_user_data.append(user_data)
            
            # Create users in Core service
            user_results = await batch_create_with_delay(
                core_client.create_user,
                core_user_data,
                batch_size=3
            )
            
            # Step 2: Create Management service driver records with security_id
            logger.info("Step 2: Creating driver records in Management service...")
            management_driver_data = []
            successful_driver_users = []
            
            for i, (user_result, driver_frontend) in enumerate(zip(user_results, driver_data)):
                if user_result.get("error"):
                    continue
                
                # Extract user ID from Core service response
                user_id = None
                if "data" in user_result and "id" in user_result["data"]:
                    user_id = user_result["data"]["id"]
                elif "id" in user_result:
                    user_id = user_result["id"]
                elif "user" in user_result and "id" in user_result["user"]:
                    user_id = user_result["user"]["id"]
                
                if user_id:
                    driver_record = {
                        **driver_frontend,
                        "security_id": user_id
                    }
                    management_driver_data.append(driver_record)
                    successful_driver_users.append(user_result)
            
            # Create drivers in Management service
            if management_driver_data:
                driver_results = await batch_create_with_delay(
                    core_client.create_driver,
                    management_driver_data,
                    batch_size=3
                )
            else:
                driver_results = []
        else:
            driver_results = []
            successful_driver_users = []
        
        # Create fleet managers using Core service (they use different structure)
        if managers_count > 0:
            logger.info(f"Creating {len(manager_data)} fleet managers via Core service...")
            manager_results = await batch_create_with_delay(
                core_client.create_user,  # Managers still use Core service
                manager_data,
                batch_size=3
            )
        else:
            manager_results = []
        
        # Combine results for logging
        all_results = driver_results + manager_results
        all_user_data = management_driver_data + manager_data if drivers_count > 0 else manager_data
        
        # Log results
        successful_users = []
        failed_users = []
        successful_drivers = 0
        successful_managers = 0
        
        for i, result in enumerate(all_results):
            if i < len(driver_results):
                user_name = f"{management_driver_data[i]['full_name']} (driver)" if i < len(management_driver_data) else "Unknown driver"
                user_type = "driver"
            else:
                manager_index = i - len(driver_results)
                user_name = f"{manager_data[manager_index]['first_name']} {manager_data[manager_index]['last_name']} (fleet_manager)" if manager_index < len(manager_data) else "Unknown manager"
                user_type = "fleet_manager"
            
            log_creation_result("user", result, user_name)
            
            if not result.get("error"):
                successful_users.append(result)
                if user_type == 'driver':
                    successful_drivers += 1
                else:
                    successful_managers += 1
            else:
                failed_users.append(result)
        
        logger.info(f"\n📊 User Creation Summary:")
        logger.info(f"👤 Core users created: {len(successful_driver_users) + successful_managers}")
        logger.info(f"✅ Successfully created: {len(successful_users)} total records")
        logger.info(f"   - Drivers: {successful_drivers}")
        logger.info(f"   - Fleet Managers: {successful_managers}")
        logger.info(f"❌ Failed to create: {len(failed_users)} records")
        logger.info(f"🔐 All users use password: Password1!")
        
        if failed_users:
            logger.warning("Failed users - please check service logs")
            
        return successful_users
        
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
