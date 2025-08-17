#!/usr/bin/env python3
"""
Mock Maintenance Data Generator
Creates realistic maintenance records, licenses, and schedules via API calls
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from config import (
    MAINTENANCE_TYPES, LICENSE_TYPES,
    random_date_in_range, future_date_in_range
)
from api_utils import (
    CoreServiceClient, MaintenanceServiceClient, 
    batch_create_with_delay, log_creation_result, logger,
    extract_id_from_response
)


def generate_maintenance_record_data_for_all_vehicles(vehicle_ids: List[str], user_ids: List[str], 
                                                    min_records_per_vehicle: int = 1,
                                                    max_records_per_vehicle: int = 3) -> List[Dict[str, Any]]:
    """Generate maintenance records ensuring each vehicle gets at least min_records_per_vehicle records"""
    records = []
    
    logger.info(f"Generating maintenance records for {len(vehicle_ids)} vehicles...")
    logger.info(f"Each vehicle will get {min_records_per_vehicle}-{max_records_per_vehicle} maintenance records")
    
    for vehicle_id in vehicle_ids:
        # Determine how many records this vehicle should get
        num_records = random.randint(min_records_per_vehicle, max_records_per_vehicle)
        
        for j in range(num_records):
            record = generate_single_maintenance_record(vehicle_id, user_ids)
            records.append(record)
    
    logger.info(f"Generated {len(records)} maintenance records total")
    return records


def generate_single_maintenance_record(vehicle_id: str, user_ids: List[str]) -> Dict[str, Any]:
    """Generate a single maintenance record for a specific vehicle"""
    assigned_to = random.choice(user_ids) if user_ids else "system"
    maintenance_type = random.choice(MAINTENANCE_TYPES)
    
    # Determine if this is past, current, or future maintenance
    maintenance_timing = random.choices(
        ["past", "current", "future"],
        weights=[60, 20, 20]  # 60% past, 20% current, 20% future
    )[0]
    
    if maintenance_timing == "past":
        scheduled_date = random_date_in_range(365, 30)  # 30 days to 1 year ago
        completed_date = scheduled_date + timedelta(days=random.randint(0, 7))
        status = random.choice(["completed", "completed", "overdue"])
    elif maintenance_timing == "current":
        scheduled_date = random_date_in_range(30, 0)  # Last 30 days
        # Always provide completed_date, even for current/in-progress items
        completed_date = scheduled_date + timedelta(days=random.randint(0, 5))
        status = random.choice(["scheduled", "in_progress", "overdue"])
    else:  # future
        scheduled_date = future_date_in_range(1, 180)  # Next 6 months
        # Even for future items, simulate as if they have a projected completion
        completed_date = scheduled_date + timedelta(days=random.randint(0, 3))
        status = "scheduled"
    
    # Generate cost based on maintenance type
    cost_ranges = {
        "oil_change": (50, 150),
        "tire_rotation": (30, 80),
        "brake_inspection": (100, 300),
        "transmission_service": (200, 800),
        "air_filter_replacement": (20, 60),
        "battery_check": (50, 200),
        "coolant_flush": (100, 250),
        "tune_up": (200, 500),
        "alignment": (80, 200),
        "inspection": (50, 150),
        "engine_diagnostic": (150, 400),
        "suspension_check": (100, 600)
    }
    
    min_cost, max_cost = cost_ranges.get(maintenance_type, (100, 500))
    estimated_cost = random.randint(min_cost, max_cost)
    # Always provide actual_cost - for completed items use slight variation, 
    # for others use estimated cost as baseline
    if status == "completed":
        actual_cost = estimated_cost + random.randint(-50, 100)
    else:
        # For non-completed items, use estimated cost with small variation
        actual_cost = estimated_cost + random.randint(-20, 50)
    
    record = {
        "vehicle_id": vehicle_id,
        "maintenance_type": maintenance_type,
        "title": maintenance_type.replace("_", " ").title(),
        "description": f"Routine {maintenance_type.replace('_', ' ')} maintenance for vehicle",
        "scheduled_date": scheduled_date.isoformat(),
        "completed_date": completed_date.isoformat() if completed_date else None,
        "status": status,
        "priority": random.choice(["low", "medium", "high"]),
        "estimated_cost": estimated_cost,
        "actual_cost": actual_cost,
        "mileage_at_service": random.randint(10000, 150000),
        "next_service_mileage": random.randint(15000, 160000),
        "assigned_to": assigned_to,
        "vendor": {
            "name": random.choice([
                "QuickLube Plus", "AutoCare Express", "Fleet Maintenance Co",
                "ProService Motors", "Reliable Auto", "TechCare Automotive"
            ]),
            "contact": f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
            "address": f"{random.randint(100, 9999)} Service Dr, Auto City, AC {random.randint(10000, 99999)}"
        },
        "parts_used": [
            {
                "part_name": random.choice(["Oil Filter", "Air Filter", "Brake Pads", "Spark Plugs", "Belts"]),
                "part_number": f"P{random.randint(100000, 999999)}",
                "quantity": random.randint(1, 4),
                "cost": random.randint(10, 200)
            }
        ] if status in ["completed", "in_progress"] else [],
        "labor_hours": random.uniform(0.5, 8.0),  # Always provide labor hours
        "notes": f"Maintenance {'performed' if status == 'completed' else 'scheduled'} for {maintenance_type}. Vehicle in good condition.",
        "attachments": [],
        "warranty_period": random.randint(30, 365),  # Always provide warranty period
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return record


def generate_maintenance_record_data(vehicle_ids: List[str], user_ids: List[str], 
                                   count: int = 100) -> List[Dict[str, Any]]:
    """Generate mock maintenance record data (original function for backwards compatibility)"""
    records = []
    
    logger.info(f"Generating {count} maintenance records for {len(vehicle_ids)} vehicles...")
    
    for i in range(count):
        vehicle_id = random.choice(vehicle_ids)
        record = generate_single_maintenance_record(vehicle_id, user_ids)
        records.append(record)
        
        # Determine if this is past, current, or future maintenance
        
    logger.info(f"Generated {len(records)} maintenance records")
    return records


def generate_license_record_data(vehicle_ids: List[str], driver_ids: List[str], 
                               count: int = 80) -> List[Dict[str, Any]]:
    """Generate mock license record data"""
    licenses = []
    
    logger.info(f"Generating {count} license records...")
    
    # Split between vehicle and driver licenses
    vehicle_license_count = int(count * 0.7)  # 70% vehicle licenses
    driver_license_count = count - vehicle_license_count
    
    # Vehicle licenses
    for i in range(vehicle_license_count):
        vehicle_id = random.choice(vehicle_ids)
        license_type = random.choice([
            "vehicle_registration", "inspection_certificate", 
            "insurance_certificate", "emissions_certificate"
        ])
        
        issue_date = random_date_in_range(365, 30)
        expiry_date = future_date_in_range(30, 730)  # 1 month to 2 years from now
        
        license = {
            "entity_id": vehicle_id,
            "entity_type": "vehicle",
            "license_type": license_type,
            "license_number": f"{license_type.upper()[:3]}-{random.randint(100000, 999999)}",
            "title": f"{license_type.replace('_', ' ').title()}",
            "issue_date": issue_date.date().isoformat(),
            "expiry_date": expiry_date.date().isoformat(),
            "issuing_authority": random.choice([
                "Department of Motor Vehicles", "State Transportation Authority",
                "Environmental Protection Agency", "Federal Motor Carrier Safety Administration"
            ]),
            "description": f"Official {license_type.replace('_', ' ')} documentation",
            "is_active": True,
            "advance_notice_days": random.choice([30, 60, 90]),
            "cost": random.randint(50, 500),
            "renewal_required": True,
            "compliance_status": "compliant",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        licenses.append(license)
    
    # Driver licenses
    for i in range(driver_license_count):
        driver_id = random.choice(driver_ids) if driver_ids else f"driver_{i}"
        license_type = random.choice([
            "class_a_cdl", "class_b_cdl", "class_c_regular",
            "commercial_permit", "hazmat_endorsement"
        ])
        
        issue_date = random_date_in_range(1095, 365)  # 1-3 years ago
        expiry_date = future_date_in_range(365, 1825)  # 1-5 years from now
        
        license = {
            "entity_id": driver_id,
            "entity_type": "driver",
            "license_type": license_type,
            "license_number": f"DL{random.randint(100000000, 999999999)}",
            "title": f"{license_type.replace('_', ' ').title()}",
            "issue_date": issue_date.date().isoformat(),
            "expiry_date": expiry_date.date().isoformat(),
            "issuing_authority": "Department of Motor Vehicles",
            "description": f"Commercial driver {license_type.replace('_', ' ')} license",
            "is_active": True,
            "advance_notice_days": 60,
            "cost": random.randint(100, 300),
            "renewal_required": True,
            "compliance_status": "compliant",
            "restrictions": random.choice([
                [], ["corrective_lenses"], ["daylight_only"], ["no_passengers"]
            ]),
            "endorsements": random.sample([
                "passenger", "school_bus", "hazmat", "motorcycle", "air_brakes"
            ], k=random.randint(0, 2)),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        licenses.append(license)
    
    logger.info(f"Generated {len(licenses)} license records ({vehicle_license_count} vehicle, {driver_license_count} driver)")
    return licenses


def generate_maintenance_schedule_data(vehicle_ids: List[str], 
                                     count: int = 60) -> List[Dict[str, Any]]:
    """Generate mock maintenance schedule data"""
    schedules = []
    
    logger.info(f"Generating {count} maintenance schedules...")
    
    for i in range(count):
        vehicle_id = random.choice(vehicle_ids)
        maintenance_type = random.choice(MAINTENANCE_TYPES)
        
        # Initialize all variables
        interval_type = random.choice(["mileage", "time"])
        interval_value = None
        last_service_date = None
        last_service_mileage = None
        next_due_date = None
        next_due_mileage = None
        
        # Set interval values based on type
        if interval_type == "mileage":
            interval_value = random.choice([3000, 5000, 7500, 10000, 15000, 30000])
            last_service_mileage = random.randint(10000, 50000)
            next_due_mileage = last_service_mileage + interval_value
        else:  # time
            interval_value = random.choice([30, 60, 90, 180, 365])  # days
            last_service_date = random_date_in_range(interval_value, 30)
            next_due_date = last_service_date + timedelta(days=interval_value)
        
        # Calculate scheduled_date - the actual date for the next maintenance
        if next_due_date:
            scheduled_date = next_due_date
        else:
            # For mileage-based, estimate based on average driving
            days_to_mileage = max(30, (next_due_mileage - last_service_mileage) // 50)  # ~50 miles/day
            scheduled_date = datetime.now() + timedelta(days=days_to_mileage)
        
        schedule = {
            "vehicle_id": vehicle_id,
            "maintenance_type": maintenance_type,
            "title": f"Recurring {maintenance_type.replace('_', ' ').title()}",
            "description": f"Scheduled {maintenance_type.replace('_', ' ')} maintenance",
            "scheduled_date": scheduled_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "interval_type": interval_type,
            "interval_value": interval_value,
            "last_service_date": last_service_date.strftime("%Y-%m-%dT%H:%M:%S") if last_service_date else None,
            "last_service_mileage": last_service_mileage,
            "next_due_date": next_due_date.strftime("%Y-%m-%dT%H:%M:%S") if next_due_date else None,
            "next_due_mileage": next_due_mileage,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        schedules.append(schedule)
    
    logger.info(f"Generated {len(schedules)} maintenance schedules")
    return schedules


async def get_existing_entities():
    """Get existing vehicles and users from Core service"""
    vehicle_ids = []
    user_ids = []
    driver_ids = []
    
    try:
        async with CoreServiceClient() as core_client:
            # Get vehicles
            vehicles_response = await core_client.get_vehicles({"limit": 1000})
            
            # Handle different response formats
            if isinstance(vehicles_response, list):
                # Direct list response
                vehicle_ids = [extract_id_from_response({"data": v}) for v in vehicles_response]
                vehicle_ids = [vid for vid in vehicle_ids if vid]  # Filter out None values
            elif isinstance(vehicles_response, dict) and not vehicles_response.get("error"):
                # Check for nested structure: response.data.data.vehicles
                vehicles_data = vehicles_response.get("data", {})
                if isinstance(vehicles_data, dict) and "data" in vehicles_data:
                    inner_data = vehicles_data["data"]
                    if "vehicles" in inner_data:
                        vehicle_ids = [extract_id_from_response({"data": v}) for v in inner_data["vehicles"]]
                        vehicle_ids = [vid for vid in vehicle_ids if vid]  # Filter out None values
                # Fallback to direct vehicles in data
                elif "vehicles" in vehicles_data:
                    vehicle_ids = [extract_id_from_response({"data": v}) for v in vehicles_data["vehicles"]]
                    vehicle_ids = [vid for vid in vehicle_ids if vid]  # Filter out None values
            
            # Get users
            users_response = await core_client.get_users({"limit": 1000})
            
            # Handle different response formats
            if isinstance(users_response, list):
                # Direct list response
                for user in users_response:
                    user_id = extract_id_from_response({"data": user})
                    if user_id:
                        user_ids.append(user_id)
                        if user.get("role") == "driver":
                            driver_ids.append(user_id)
            elif isinstance(users_response, dict) and not users_response.get("error"):
                # Check for nested structure: response.data.data.users
                users_data = users_response.get("data", {})
                if isinstance(users_data, dict) and "data" in users_data:
                    inner_data = users_data["data"]
                    if "users" in inner_data:
                        for user in inner_data["users"]:
                            user_id = extract_id_from_response({"data": user})
                            if user_id:
                                user_ids.append(user_id)
                                if user.get("role") == "driver":
                                    driver_ids.append(user_id)
                # Fallback to direct users in data
                elif "users" in users_data:
                    for user in users_data["users"]:
                        user_id = extract_id_from_response({"data": user})
                        if user_id:
                            user_ids.append(user_id)
                            if user.get("role") == "driver":
                                driver_ids.append(user_id)
                                
    except Exception as e:
        logger.warning(f"Error fetching existing entities: {e}")
    
    logger.info(f"Found {len(vehicle_ids)} vehicles, {len(user_ids)} users ({len(driver_ids)} drivers)")
    return vehicle_ids, user_ids, driver_ids


async def create_mock_maintenance_data(records_count: int = 100, 
                                     licenses_count: int = 80,
                                     schedules_count: int = 60):
    """Create mock maintenance data via API calls"""
    logger.info("🔧 Starting maintenance data creation process...")
    
    # Get existing entities
    vehicle_ids, user_ids, driver_ids = await get_existing_entities()
    
    if not vehicle_ids:
        logger.error("No vehicles found! Please create vehicles first using create_vehicles.py")
        return
    
    if not user_ids:
        logger.warning("No users found! Some maintenance data may be incomplete.")
    
    # Generate maintenance data
    maintenance_records = generate_maintenance_record_data(vehicle_ids, user_ids, records_count)
    license_records = generate_license_record_data(vehicle_ids, driver_ids, licenses_count)
    maintenance_schedules = generate_maintenance_schedule_data(vehicle_ids, schedules_count)
    
    results = {
        "maintenance_records": [],
        "license_records": [],
        "maintenance_schedules": []
    }
    
    # Create maintenance data via Maintenance service
    async with MaintenanceServiceClient() as maintenance_client:
        # Create maintenance records
        logger.info("Creating maintenance records...")
        maintenance_results = await batch_create_with_delay(
            maintenance_client.create_maintenance_record,
            maintenance_records,
            batch_size=4
        )
        
        successful_records = 0
        for i, result in enumerate(maintenance_results):
            record_name = f"{maintenance_records[i]['maintenance_type']} - {maintenance_records[i]['vehicle_id'][:8]}"
            log_creation_result("maintenance record", result, record_name)
            if not result.get("error"):
                successful_records += 1
                results["maintenance_records"].append(result)
        
        # Create license records
        logger.info("Creating license records...")
        license_results = await batch_create_with_delay(
            maintenance_client.create_license_record,
            license_records,
            batch_size=4
        )
        
        successful_licenses = 0
        for i, result in enumerate(license_results):
            license_name = f"{license_records[i]['license_type']} - {license_records[i]['entity_id'][:8]}"
            log_creation_result("license record", result, license_name)
            if not result.get("error"):
                successful_licenses += 1
                results["license_records"].append(result)
        
        # Create maintenance schedules
        logger.info("Creating maintenance schedules...")
        schedule_results = await batch_create_with_delay(
            maintenance_client.create_maintenance_schedule,
            maintenance_schedules,
            batch_size=4
        )
        
        successful_schedules = 0
        for i, result in enumerate(schedule_results):
            schedule_name = f"{maintenance_schedules[i]['maintenance_type']} - {maintenance_schedules[i]['vehicle_id'][:8]}"
            log_creation_result("maintenance schedule", result, schedule_name)
            if not result.get("error"):
                successful_schedules += 1
                results["maintenance_schedules"].append(result)
    
    # Summary
    logger.info(f"\n📊 Maintenance Data Creation Summary:")
    logger.info(f"✅ Maintenance Records: {successful_records}/{len(maintenance_records)}")
    logger.info(f"✅ License Records: {successful_licenses}/{len(license_records)}")
    logger.info(f"✅ Maintenance Schedules: {successful_schedules}/{len(maintenance_schedules)}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create mock maintenance data")
    parser.add_argument("--records", type=int, default=100, help="Number of maintenance records (default: 100)")
    parser.add_argument("--licenses", type=int, default=80, help="Number of license records (default: 80)")
    parser.add_argument("--schedules", type=int, default=60, help="Number of maintenance schedules (default: 60)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Creating {args.records} maintenance records, {args.licenses} licenses, {args.schedules} schedules...")
    
    try:
        results = asyncio.run(create_mock_maintenance_data(args.records, args.licenses, args.schedules))
        if results:
            total_created = len(results["maintenance_records"]) + len(results["license_records"]) + len(results["maintenance_schedules"])
            logger.info(f"🎉 Maintenance data creation completed! Created {total_created} total records.")
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Error during maintenance data creation: {e}")
        raise
