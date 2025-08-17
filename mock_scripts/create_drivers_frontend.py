#!/usr/bin/env python3
"""
Mock Driver Data Generator - Frontend Compatible
Creates drivers using the exact same endpoint and data structure as the frontend
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from config import generate_phone_number, generate_email
from api_utils import CoreServiceClient, batch_create_with_delay, log_creation_result, logger, extract_id_from_response


# Sample names for drivers
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Helen", "Mark", "Sandra", "Donald", "Donna",
    "Steven", "Carol", "Paul", "Ruth", "Andrew", "Sharon", "Joshua", "Michelle",
    "Kenneth", "Laura", "Kevin", "Sarah", "Brian", "Kimberly", "George", "Deborah",
    "Timothy", "Dorothy", "Ronald", "Lisa", "Jason", "Nancy", "Edward", "Karen",
    "Jeffrey", "Betty", "Ryan", "Helen", "Jacob", "Sandra", "Gary", "Donna",
    "Nicholas", "Carol", "Eric", "Ruth", "Jonathan", "Sharon", "Stephen", "Michelle",
    "Larry", "Laura", "Justin", "Sarah", "Scott", "Kimberly", "Brandon", "Deborah",
    "Benjamin", "Dorothy", "Samuel", "Lisa", "Gregory", "Nancy", "Frank", "Karen",
    "Raymond", "Betty", "Alexander", "Helen", "Patrick", "Sandra", "Jack", "Donna",
    "Dennis", "Carol", "Jerry", "Ruth", "Tyler", "Sharon", "Aaron", "Michelle",
    "Jose", "Laura", "Henry", "Sarah", "Adam", "Kimberly", "Douglas", "Deborah",
    "Nathan", "Dorothy", "Peter", "Amy", "Zachary", "Angela", "Kyle", "Ashley",
    "Noah", "Brenda", "Alan", "Emma", "Arthur", "Olivia", "Sean", "Cynthia",
    "Carl", "Marie", "Harold", "Janet", "Jordan", "Catherine", "Roger", "Frances",
    "Keith", "Christine", "Bruce", "Anna", "Wayne", "Samantha", "Louis", "Debra",
    "Ralph", "Rachel", "Roy", "Carolyn", "Eugene", "Virginia", "Philip", "Maria",
    "Billy", "Heather", "Bobby", "Diane", "Mason", "Julie", "Johnny", "Joyce",
    "Clarence", "Victoria", "Ernest", "Kelly", "Martin", "Christina", "Russell", "Joan",
    "Louis", "Evelyn", "Philip", "Lauren", "Willie", "Judith", "Elijah", "Megan",
    "Wayne", "Cheryl", "Mason", "Andrea", "Jesse", "Hannah", "Juan", "Jacqueline",
    "Gabriel", "Martha", "Victor", "Gloria", "Felix", "Teresa", "Oscar", "Sara",
    "Derek", "Janice", "Marcus", "Marie", "Jeremy", "Julia", "Antonio", "Heather",
    "Curtis", "Diane", "Leon", "Carolyn"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza",
    "Ruiz", "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers",
    "Long", "Ross", "Foster", "Jimenez", "Powell", "Jenkins", "Perry", "Russell",
    "Sullivan", "Bell", "Coleman", "Butler", "Henderson", "Barnes", "Gonzales", "Fisher",
    "Vasquez", "Simmons", "Romero", "Jordan", "Patterson", "Alexander", "Hamilton", "Graham",
    "Reynolds", "Griffin", "Wallace", "Moreno", "West", "Cole", "Hayes", "Bryant",
    "Herrera", "Gibson", "Ellis", "Tran", "Medina", "Aguilar", "Stevens", "Murray",
    "Ford", "Castro", "Marshall", "Owen", "Mason", "Harrison", "Hunt", "Banks",
    "Liu", "Knight", "Lane", "Rose", "Gold", "Stone", "Hawkins", "Dunn",
    "Perkins", "Hudson", "Spencer", "Gardner", "Stephens", "Payne", "Pierce", "Berry",
    "Matthews", "Arnold", "Wagner", "Willis", "Ray", "Watkins", "Olson", "Carroll",
    "Duncan", "Snyder", "Hart", "Cunningham", "Bradley", "Lane", "Andrews", "Ruiz",
    "Harper", "Fox", "Riley", "Armstrong", "Carpenter", "Weaver", "Greene", "Lawrence",
    "Elliott", "Chavez", "Sims", "Austin", "Peters", "Kelley", "Franklin", "Lawson",
    "Fields", "Gutierrez", "Ryan", "Schmidt", "Carr", "Vasquez", "Castillo", "Wheeler"
]


def generate_frontend_compatible_drivers(count: int = 30) -> List[Dict[str, Any]]:
    """
    Generate driver data using exact same structure as AddDriverModal.jsx frontend form
    This ensures complete compatibility with the frontend driver creation process
    """
    drivers = []
    used_emails = set()  # Track used emails to ensure uniqueness
    
    logger.info(f"Generating {count} frontend-compatible drivers...")
    
    # Exact license types from AddDriverModal.jsx
    license_types = [
        'A', 'A1', 'B', 'C', 'C1', 'EB', 'EC', 'EC1'
    ]
    
    # Exact departments from AddDriverModal.jsx
    departments = [
        'Operations', 'Logistics', 'Maintenance', 'Administration', 'Security'
    ]
    
    for i in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        
        # Generate unique email
        email = generate_email(first_name, last_name)
        attempt_count = 1
        
        # Ensure email uniqueness
        while email in used_emails and attempt_count < 50:
            if attempt_count <= 10:
                # Try with a number suffix
                email = generate_email(first_name, last_name).replace('@', f'{attempt_count}@')
            else:
                # Try with a different random name combination
                temp_first = random.choice(FIRST_NAMES)
                temp_last = random.choice(LAST_NAMES)
                email = generate_email(temp_first, temp_last)
            attempt_count += 1
        
        # Final fallback if still not unique
        if email in used_emails:
            email = f"{first_name.lower()}.{last_name.lower()}.{random.randint(1000, 9999)}@fleetco.com"
        
        used_emails.add(email)
        
        # Generate realistic dates
        joining_date = datetime.now() - timedelta(days=random.randint(30, 1095))  # 1 month to 3 years ago
        license_expiry = datetime.now() + timedelta(days=random.randint(90, 1095))  # 3 months to 3 years from now
        
        # Generate a security_id (required by Management service)
        import uuid
        security_id = str(uuid.uuid4())
        
        # Create driver data matching frontend AddDriverModal.jsx form exactly
        driver = {
            # Personal Information section
            "full_name": full_name,
            "email": email,
            "phoneNo": generate_phone_number(),  # Note: phoneNo (not phone) to match frontend
            "emergency_contact": generate_phone_number(),  # Optional field
            
            # License Information section  
            "license_number": f"SA{random.randint(1000000000000, 9999999999999)}",  # South African format
            "license_type": random.choice(license_types),  # SA license codes
            "license_expiry": license_expiry.date().isoformat(),  # ISO date format
            
            # Employment Information section
            "department": random.choice(departments),
            "joining_date": joining_date.date().isoformat(),  # ISO date format
            
            # Required by Management service backend (not in frontend form)
            "security_id": security_id,  # Generated UUID for authentication reference
        }
        
        drivers.append(driver)
        
    logger.info(f"Generated {len(drivers)} frontend-compatible driver records")
    logger.info("✅ All drivers use standard password: Password1!")
    return drivers


async def create_frontend_compatible_drivers(count: int = 30):
    """Create drivers using proper two-step process: Core auth first, then Management service"""
    logger.info("🚗 Starting frontend-compatible driver creation...")
    logger.info(f"📋 Creating {count} drivers using proper two-step process")
    logger.info("🔐 All drivers will use password: Password1!")
    
    # Generate base driver data for frontend compatibility
    driver_frontend_data = generate_frontend_compatible_drivers(count)
    
    async with CoreServiceClient() as core_client:
        
        # Step 1: Create users in Core service to get security_user IDs
        logger.info("Step 1: Creating users in Core service for authentication...")
        
        # Convert frontend data to Core service user format
        core_user_data = []
        for driver in driver_frontend_data:
            # Parse full_name into first_name and last_name
            name_parts = driver['full_name'].split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            # Create Core service user record
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
            core_client.create_user,  # Core service endpoint
            core_user_data,
            batch_size=3
        )
        
        # Step 2: Extract user IDs and create Management service driver records
        logger.info("Step 2: Creating driver records in Management service...")
        
        management_driver_data = []
        successful_users = []
        
        for i, (user_result, frontend_data) in enumerate(zip(user_results, driver_frontend_data)):
            if user_result.get("error"):
                logger.error(f"Skipping driver creation for {frontend_data['full_name']} - user creation failed")
                continue
            
            # Debug: Log the actual response structure
            logger.debug(f"User creation response for {frontend_data['full_name']}: {user_result}")
            
            # Extract user ID using the helper function
            user_id = extract_id_from_response(user_result)
            
            logger.debug(f"Extracted user_id for {frontend_data['full_name']}: {user_id}")
            
            if not user_id:
                logger.error(f"Could not extract user ID for {frontend_data['full_name']}. Response keys: {list(user_result.keys())}")
                continue
            
            # Create Management service driver record with security_id
            driver_record = {
                **frontend_data,  # Keep all frontend fields
                "security_id": user_id  # Add the security_id from Core service
            }
            management_driver_data.append(driver_record)
            successful_users.append(user_result)
        
        # Create drivers in Management service
        if management_driver_data:
            results = await batch_create_with_delay(
                core_client.create_driver,  # Management service endpoint
                management_driver_data,
                batch_size=3
            )
        else:
            results = []
        
        # Log results
        successful_drivers = []
        failed_drivers = []
        
        for i, result in enumerate(results):
            driver_name = f"{management_driver_data[i]['full_name']}" if i < len(management_driver_data) else "Unknown"
            log_creation_result("driver", result, driver_name)
            
            if not result.get("error"):
                successful_drivers.append(result)
            else:
                failed_drivers.append(result)
        
        logger.info(f"\n📊 Driver Creation Summary:")
        logger.info(f"👤 Core users created: {len(successful_users)}")
        logger.info(f"🚗 Management drivers created: {len(successful_drivers)}")
        logger.info(f"❌ Failed driver records: {len(failed_drivers)}")
        logger.info(f"🔐 All drivers use password: Password1!")
        
        if failed_drivers:
            logger.warning("Failed drivers - please check Management service logs")
            
        return successful_drivers


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create frontend-compatible mock drivers")
    parser.add_argument("--count", type=int, default=30, help="Number of drivers to create (default: 30)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("🎯 Frontend-Compatible Driver Creation")
    logger.info("=" * 50)
    logger.info("This script creates drivers using the exact same:")
    logger.info("• Data structure as AddDriverModal.jsx")
    logger.info("• API endpoint (/management/drivers)")
    logger.info("• Field names and validation rules")
    logger.info("• Password: Password1! for all drivers")
    logger.info("=" * 50)
    
    try:
        drivers = asyncio.run(create_frontend_compatible_drivers(args.count))
        logger.info(f"🎉 Driver creation process completed! Created {len(drivers)} drivers.")
        logger.info("✅ All drivers are now compatible with frontend expectations!")
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Error during driver creation: {e}")
        raise
