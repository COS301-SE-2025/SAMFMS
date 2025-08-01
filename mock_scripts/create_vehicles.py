#!/usr/bin/env python3
"""
Mock Vehicle Data Generator
Creates realistic vehicle data via Core service API calls
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from config import (
    VEHICLE_TYPES, VEHICLE_MAKES, VEHICLE_MODELS,
    CITIES, STATES, generate_vin, generate_license_plate
)
from api_utils import CoreServiceClient, batch_create_with_delay, log_creation_result, logger


def generate_vehicle_data(count: int = 50) -> List[Dict[str, Any]]:
    """Generate mock vehicle data"""
    vehicles = []
    
    logger.info(f"Generating {count} mock vehicles...")
    
    for i in range(count):
        make = random.choice(VEHICLE_MAKES)
        model = random.choice(VEHICLE_MODELS[make])
        vehicle_type = random.choice(VEHICLE_TYPES)
        
        # Generate realistic year (2015-2024)
        year = random.randint(2015, 2024)
        
        # Generate mileage based on year
        years_old = 2025 - year
        base_mileage = years_old * random.randint(8000, 15000)
        mileage = base_mileage + random.randint(0, 5000)
        
        # Generate location
        city_index = random.randint(0, len(CITIES) - 1)
        city = CITIES[city_index]
        state = STATES[city_index]
        
        vehicle = {
            "vin": generate_vin(),
            "license_plate": generate_license_plate(),
            "make": make,
            "model": model,
            "year": year,
            "vehicle_type": vehicle_type,
            "color": random.choice([
                "White", "Black", "Silver", "Red", "Blue", 
                "Gray", "Green", "Brown", "Yellow", "Orange"
            ]),
            "engine_type": random.choice([
                "gasoline", "diesel", "hybrid", "electric", "flex_fuel"
            ]),
            "fuel_capacity": random.randint(40, 120),  # liters
            "seating_capacity": random.randint(2, 8),
            "current_mileage": mileage,
            "mileage": mileage,  # Try both field names
            "status": random.choice(["active", "active", "active", "maintenance", "inactive"]),
            "purchase_date": (datetime.now() - timedelta(days=years_old * 365 + random.randint(0, 365))).isoformat(),
            "purchase_price": random.randint(15000, 80000),
            "current_value": random.randint(8000, 60000),
            "location": {
                "city": city,
                "state": state,
                "country": "USA"
            },
            "specifications": {
                "transmission": random.choice(["automatic", "manual", "cvt"]),
                "drivetrain": random.choice(["fwd", "rwd", "awd", "4wd"]),
                "engine_size": f"{random.uniform(1.0, 6.0):.1f}L",
                "horsepower": random.randint(150, 400),
                "torque": random.randint(200, 500)
            },
            "insurance": {
                "provider": random.choice([
                    "State Farm", "GEICO", "Progressive", "Allstate", "USAA"
                ]),
                "policy_number": f"POL-{random.randint(100000, 999999)}",
                "expiry_date": (datetime.now() + timedelta(days=random.randint(30, 365))).isoformat()
            },
            "maintenance_notes": f"Regular maintenance vehicle {i+1}. Good condition.",
            "tags": random.sample([
                "fleet", "commercial", "passenger", "cargo", "delivery", 
                "executive", "utility", "backup", "primary"
            ], k=random.randint(1, 3)),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        vehicles.append(vehicle)
        
    logger.info(f"Generated {len(vehicles)} vehicle records")
    return vehicles


async def create_mock_vehicles(count: int = 50):
    """Create mock vehicles via Core service"""
    logger.info("🚗 Starting vehicle creation process...")
    
    # Generate vehicle data
    vehicle_data = generate_vehicle_data(count)
    
    # Create vehicles via Core service
    async with CoreServiceClient() as core_client:
        logger.info("Creating vehicles via Core service...")
        
        results = await batch_create_with_delay(
            core_client.create_vehicle,
            vehicle_data,
            batch_size=5  # 5 vehicles per batch
        )
        
        # Log results
        successful_vehicles = []
        failed_vehicles = []
        
        for i, result in enumerate(results):
            vehicle_name = f"{vehicle_data[i]['make']} {vehicle_data[i]['model']} ({vehicle_data[i]['license_plate']})"
            log_creation_result("vehicle", result, vehicle_name)
            
            if not result.get("error"):
                successful_vehicles.append(result)
            else:
                failed_vehicles.append(result)
        
        logger.info(f"\n📊 Vehicle Creation Summary:")
        logger.info(f"✅ Successfully created: {len(successful_vehicles)} vehicles")
        logger.info(f"❌ Failed to create: {len(failed_vehicles)} vehicles")
        
        if failed_vehicles:
            logger.warning("Failed vehicles - please check Core service logs")
            
        return successful_vehicles


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create mock vehicle data")
    parser.add_argument("--count", type=int, default=50, help="Number of vehicles to create (default: 50)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Creating {args.count} mock vehicles...")
    
    try:
        vehicles = asyncio.run(create_mock_vehicles(args.count))
        logger.info(f"🎉 Vehicle creation process completed! Created {len(vehicles)} vehicles.")
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Error during vehicle creation: {e}")
        raise
