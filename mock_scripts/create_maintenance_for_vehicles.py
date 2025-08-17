#!/usr/bin/env python3

"""
Script to create maintenance records for specific vehicles from JSON file.
This ensures every vehicle in the database has at least one maintenance record.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the mock_scripts directory to the path
sys.path.append(str(Path(__file__).parent))

from api_utils import APIClient, logger
from config import CORE_BASE_URL
from create_maintenance_data import generate_maintenance_record_data_for_all_vehicles

def extract_vehicle_ids_from_json(json_file_path: str) -> List[str]:
    """Extract vehicle IDs from the JSON export file"""
    vehicle_ids = []
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # If it's a list of vehicles
                for vehicle in data:
                    if '_id' in vehicle:
                        if isinstance(vehicle['_id'], dict) and '$oid' in vehicle['_id']:
                            # MongoDB ObjectId format: {"_id": {"$oid": "..."}}
                            vehicle_ids.append(vehicle['_id']['$oid'])
                        elif isinstance(vehicle['_id'], str):
                            # String format: {"_id": "..."}
                            vehicle_ids.append(vehicle['_id'])
            elif isinstance(data, dict):
                # If it's a single vehicle
                if '_id' in data:
                    if isinstance(data['_id'], dict) and '$oid' in data['_id']:
                        vehicle_ids.append(data['_id']['$oid'])
                    elif isinstance(data['_id'], str):
                        vehicle_ids.append(data['_id'])
        
        logger.info(f"Extracted {len(vehicle_ids)} vehicle IDs from JSON file")
        return vehicle_ids
        
    except FileNotFoundError:
        logger.error(f"JSON file not found: {json_file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file: {e}")
        return []
    except Exception as e:
        logger.error(f"Error reading vehicle IDs: {e}")
        return []

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

async def create_maintenance_records_from_json(json_file_path: str, 
                                             min_records_per_vehicle: int = 1,
                                             max_records_per_vehicle: int = 3):
    """Create maintenance records for all vehicles in the JSON file"""
    logger.info("=== Creating Maintenance Records for Specific Vehicles ===")
    
    # Extract vehicle IDs from JSON
    vehicle_ids = extract_vehicle_ids_from_json(json_file_path)
    if not vehicle_ids:
        logger.error("No vehicle IDs found in JSON file. Exiting.")
        return
    
    logger.info(f"Processing {len(vehicle_ids)} vehicles")
    logger.info(f"Each vehicle will get {min_records_per_vehicle}-{max_records_per_vehicle} maintenance records")
    
    # Initialize API client
    client = APIClient(CORE_BASE_URL)
    
    try:
        # Authenticate
        auth_success = await client.authenticate()
        if not auth_success:
            logger.error("Authentication failed")
            return
        
        # Get user IDs for assignment
        user_ids = await get_user_ids(client)
        
        # Generate maintenance records for all vehicles
        maintenance_records = generate_maintenance_record_data_for_all_vehicles(
            vehicle_ids, 
            user_ids,
            min_records_per_vehicle,
            max_records_per_vehicle
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
                    if response.status_code in [200, 201]:
                        created_count += 1
                        logger.debug(f"✓ Created maintenance record for vehicle {record['vehicle_id']}")
                    else:
                        failed_count += 1
                        logger.warning(f"✗ Failed to create maintenance record: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"✗ Error creating maintenance record: {e}")
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        # Summary
        logger.info("=== Maintenance Record Creation Summary ===")
        logger.info(f"Total vehicles processed: {len(vehicle_ids)}")
        logger.info(f"Total records generated: {len(maintenance_records)}")
        logger.info(f"Successfully created: {created_count}")
        logger.info(f"Failed to create: {failed_count}")
        logger.info(f"Success rate: {(created_count/len(maintenance_records)*100):.1f}%" if maintenance_records else "0%")
        
    except Exception as e:
        logger.error(f"Error in maintenance record creation process: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    # Path to the JSON file with vehicles
    json_file_path = "c:\\Users\\user\\OneDrive\\Documents\\capstone\\repo\\SAMFMS\\mock_scripts\\samfms_management.vehicles.json"
    
    # Check if JSON file exists
    if not Path(json_file_path).exists():
        logger.error(f"JSON file not found: {json_file_path}")
        logger.info("Please ensure the JSON file exists and contains vehicle data")
        sys.exit(1)
    
    # Run the maintenance record creation
    asyncio.run(create_maintenance_records_from_json(
        json_file_path,
        min_records_per_vehicle=1,  # At least 1 record per vehicle
        max_records_per_vehicle=3   # Up to 3 records per vehicle
    ))
