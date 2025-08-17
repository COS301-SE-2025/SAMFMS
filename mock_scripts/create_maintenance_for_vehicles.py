#!/usr/bin/env python3

"""
Script to create maintenance records by randomly selecting vehicle IDs from vehicle_id.txt file.
This ensures realistic maintenance records are distributed across available vehicles.
"""

import asyncio
import random
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the mock_scripts directory to the path
sys.path.append(str(Path(__file__).parent))

from api_utils import APIClient, logger
from config import CORE_BASE_URL
from create_maintenance_data import generate_maintenance_record_data

def load_vehicle_ids_from_file(file_path: str) -> List[str]:
    """Load vehicle IDs from vehicle_id.txt file"""
    vehicle_ids = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                vehicle_id = line.strip().strip('"')  # Remove quotes and whitespace
                if vehicle_id:  # Skip empty lines
                    vehicle_ids.append(vehicle_id)
        
        logger.info(f"Loaded {len(vehicle_ids)} vehicle IDs from {file_path}")
        return vehicle_ids
        
    except FileNotFoundError:
        logger.error(f"Vehicle ID file not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading vehicle IDs from file: {e}")
        return []

def select_random_vehicle_ids(all_vehicle_ids: List[str], count: int) -> List[str]:
    """Randomly select vehicle IDs for maintenance records"""
    if count >= len(all_vehicle_ids):
        logger.info(f"Requested {count} vehicles, using all {len(all_vehicle_ids)} available")
        return all_vehicle_ids.copy()
    
    selected = random.sample(all_vehicle_ids, count)
    logger.info(f"Randomly selected {len(selected)} vehicles from {len(all_vehicle_ids)} available")
    return selected

async def get_user_ids(client: APIClient) -> List[str]:
    """Get a list of user IDs for assignment to maintenance records"""
    try:
        response = await client.get("/management/drivers")
        if response.status_code == 200:
            drivers = response.json().get('data', [])
            # Extract security_id from drivers (this is the user ID we need)
            user_ids = [driver.get('security_id') for driver in drivers if driver.get('security_id')]
            logger.info(f"Found {len(user_ids)} user IDs for maintenance assignment")
            return user_ids
        else:
            logger.warning(f"Could not fetch drivers: {response.status_code}")
            return ["system"]  # Fallback to system assignment
    except Exception as e:
        logger.error(f"Error fetching user IDs: {e}")
        return ["system"]

async def create_maintenance_records_from_vehicle_file(vehicle_id_file_path: str, 
                                                     record_count: int = 100):
    """Create maintenance records using random vehicle IDs from vehicle_id.txt file"""
    logger.info("=== Creating Maintenance Records for Random Vehicles ===")
    
    # Load vehicle IDs from file
    all_vehicle_ids = load_vehicle_ids_from_file(vehicle_id_file_path)
    if not all_vehicle_ids:
        logger.error("No vehicle IDs found in vehicle_id.txt file. Exiting.")
        return
    
    logger.info(f"Processing {record_count} maintenance records from {len(all_vehicle_ids)} available vehicles")
    
    # Initialize API client using context manager
    async with APIClient(CORE_BASE_URL) as client:
        try:
            # Get user IDs for assignment
            user_ids = await get_user_ids(client)
            
            # Generate maintenance records with random vehicle selection
            maintenance_records = generate_maintenance_record_data(
                all_vehicle_ids,  # Pass all vehicle IDs for random selection
                user_ids,
                record_count
            )
            
            logger.info(f"Generated {len(maintenance_records)} maintenance records")
            
            # Create maintenance records in batches
            batch_size = 10
            created_count = 0
            failed_count = 0
            
            for i in range(0, len(maintenance_records), batch_size):
                batch = maintenance_records[i:i + batch_size]
                logger.info(f"Creating batch {i//batch_size + 1}/{(len(maintenance_records) + batch_size - 1)//batch_size} ({len(batch)} records)")
                
                for record in batch:
                    try:
                        response = await client.post("/maintenance/maintenance-records", record)
                        if response.get('status') == 'success':
                            created_count += 1
                            logger.debug(f"✓ Created maintenance record for vehicle {record['vehicle_id']}")
                        else:
                            failed_count += 1
                            logger.warning(f"✗ Failed to create maintenance record: {response}")
                            
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"✗ Error creating maintenance record: {e}")
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            # Summary
            logger.info("=== Maintenance Record Creation Summary ===")
            logger.info(f"Total records requested: {record_count}")
            logger.info(f"Total records generated: {len(maintenance_records)}")
            logger.info(f"Successfully created: {created_count}")
            logger.info(f"Failed to create: {failed_count}")
            logger.info(f"Success rate: {(created_count/len(maintenance_records)*100):.1f}%" if maintenance_records else "0%")
            
        except Exception as e:
            logger.error(f"Error in maintenance record creation process: {e}")

if __name__ == "__main__":
    # Path to the vehicle_id.txt file
    vehicle_id_file_path = "c:\\Users\\user\\OneDrive\\Documents\\capstone\\repo\\SAMFMS\\mock_scripts\\vehicle_id.txt"
    
    # Check if vehicle_id.txt file exists
    if not Path(vehicle_id_file_path).exists():
        logger.error(f"Vehicle ID file not found: {vehicle_id_file_path}")
        logger.info("Please ensure the vehicle_id.txt file exists and contains vehicle IDs")
        sys.exit(1)
    
    # Run the maintenance record creation
    asyncio.run(create_maintenance_records_from_vehicle_file(
        vehicle_id_file_path,
        record_count=100  # Generate 100 maintenance records with random vehicle IDs
    ))
