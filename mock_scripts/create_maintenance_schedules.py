#!/usr/bin/env python3

"""
Script to create maintenance schedules by r                for schedule in batch:
                    try:
                        response = await client.post("/maintenance/maintenance-schedules", schedule)
                        if response.get('status') == 'success':
                            created_count += 1
                            logger.debug(f"✓ Created maintenance schedule for vehicle {schedule['vehicle_id']}")
                        else:
                            failed_count += 1
                            logger.warning(f"✗ Failed to create maintenance schedule: {response}")
                            
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"✗ Error creating maintenance schedule: {e}")ting vehicle IDs from vehicle_id.txt file.
This ensures realistic maintenance schedules are distributed across available vehicles.
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
from create_maintenance_data import generate_maintenance_schedule_data

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

async def create_maintenance_schedules_from_vehicle_file(vehicle_id_file_path: str, 
                                                       schedule_count: int = 60):
    """Create maintenance schedules using random vehicle IDs from vehicle_id.txt file"""
    logger.info("=== Creating Maintenance Schedules for Random Vehicles ===")
    
    # Load vehicle IDs from file
    all_vehicle_ids = load_vehicle_ids_from_file(vehicle_id_file_path)
    if not all_vehicle_ids:
        logger.error("No vehicle IDs found in vehicle_id.txt file. Exiting.")
        return
    
    logger.info(f"Processing {schedule_count} maintenance schedules from {len(all_vehicle_ids)} available vehicles")
    
    # Initialize API client using context manager
    async with APIClient(CORE_BASE_URL) as client:
        try:
            # Generate maintenance schedules with random vehicle selection
            maintenance_schedules = generate_maintenance_schedule_data(
                all_vehicle_ids,  # Pass all vehicle IDs for random selection
                schedule_count
            )
            
            logger.info(f"Generated {len(maintenance_schedules)} maintenance schedules")
            
            # Create maintenance schedules in batches
            batch_size = 10
            created_count = 0
            failed_count = 0
            
            for i in range(0, len(maintenance_schedules), batch_size):
                batch = maintenance_schedules[i:i + batch_size]
                logger.info(f"Creating batch {i//batch_size + 1}/{(len(maintenance_schedules) + batch_size - 1)//batch_size} ({len(batch)} schedules)")
                
                for schedule in batch:
                    try:
                        response = await client.post("/maintenance/schedules", schedule)
                        if response.get('status_code') in [200, 201]:
                            created_count += 1
                            logger.debug(f"✓ Created maintenance schedule for vehicle {schedule['vehicle_id']}")
                        else:
                            failed_count += 1
                            logger.warning(f"✗ Failed to create maintenance schedule: {response}")
                            
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"✗ Error creating maintenance schedule: {e}")
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            # Summary
            logger.info("=== Maintenance Schedule Creation Summary ===")
            logger.info(f"Total schedules requested: {schedule_count}")
            logger.info(f"Total schedules generated: {len(maintenance_schedules)}")
            logger.info(f"Successfully created: {created_count}")
            logger.info(f"Failed to create: {failed_count}")
            logger.info(f"Success rate: {(created_count/len(maintenance_schedules)*100):.1f}%" if maintenance_schedules else "0%")
            
        except Exception as e:
            logger.error(f"Error in maintenance schedule creation process: {e}")

if __name__ == "__main__":
    # Path to the vehicle_id.txt file
    vehicle_id_file_path = "c:\\Users\\user\\OneDrive\\Documents\\capstone\\repo\\SAMFMS\\mock_scripts\\vehicle_id.txt"
    
    # Check if vehicle_id.txt file exists
    if not Path(vehicle_id_file_path).exists():
        logger.error(f"Vehicle ID file not found: {vehicle_id_file_path}")
        logger.info("Please ensure the vehicle_id.txt file exists and contains vehicle IDs")
        sys.exit(1)
    
    # Run the maintenance schedule creation
    asyncio.run(create_maintenance_schedules_from_vehicle_file(
        vehicle_id_file_path,
        schedule_count=60  # Generate 60 maintenance schedules with random vehicle IDs
    ))
