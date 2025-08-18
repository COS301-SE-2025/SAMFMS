#!/usr/bin/env python3
"""
Master Mock Data Generator
Orchestrates the creation of all mock data in the correct order
"""

import asyncio
import sys
import time
from datetime import datetime

from api_utils import logger


async def run_script_module(module_name: str, function_name: str, *args, **kwargs):
    """Dynamically import and run a script module"""
    try:
        logger.info(f"🚀 Starting {module_name}...")
        start_time = time.time()
        
        # Dynamic import
        module = __import__(module_name)
        func = getattr(module, function_name)
        
        # Run the function
        result = await func(*args, **kwargs)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ {module_name} completed in {elapsed:.2f} seconds")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in {module_name}: {e}")
        raise


async def create_all_mock_data(
    vehicles_count: int = 50,
    drivers_count: int = 50, 
    managers_count: int = 10,
    maintenance_records_count: int = 100,
    licenses_count: int = 80,
    schedules_count: int = 60
):
    """Create all mock data in the correct order"""
    
    logger.info("🎬 Starting complete mock data generation process...")
    logger.info("🔐 Authentication will be handled automatically...")
    logger.info("=" * 60)
    
    total_start_time = time.time()
    results = {}
    
    try:
        # Step 1: Create vehicles (foundation for maintenance data)
        logger.info("STEP 1: Creating Vehicles")
        logger.info("-" * 30)
        vehicles = await run_script_module(
            "create_vehicles", 
            "create_mock_vehicles", 
            vehicles_count
        )
        results["vehicles"] = vehicles
        
        # Pause between major steps
        logger.info("Pausing between steps...")
        await asyncio.sleep(5)
        
        # Step 2: Create users (drivers and fleet managers)
        logger.info("\nSTEP 2: Creating Users")
        logger.info("-" * 30)
        users = await run_script_module(
            "create_users", 
            "create_mock_users", 
            drivers_count, 
            managers_count
        )
        results["users"] = users
        
        # Pause between major steps
        logger.info("Pausing between steps...")
        await asyncio.sleep(5)
        
        # Step 3: Create maintenance data (depends on vehicles and users)
        logger.info("\nSTEP 3: Creating Maintenance Data")
        logger.info("-" * 30)
        maintenance_data = await run_script_module(
            "create_maintenance_data", 
            "create_mock_maintenance_data",
            maintenance_records_count,
            licenses_count,
            schedules_count
        )
        results["maintenance_data"] = maintenance_data
        
    except Exception as e:
        logger.error(f"❌ Mock data generation failed: {e}")
        if "Authentication failed" in str(e):
            logger.error("💡 Please check your login credentials in config.py or environment variables")
            logger.error("   - Set SAMFMS_LOGIN_EMAIL and SAMFMS_LOGIN_PASSWORD environment variables")
            logger.error("   - Or ensure the default email in config.py is correct")
        return None
    
    # Final summary
    total_elapsed = time.time() - total_start_time
    logger.info("\n" + "=" * 60)
    logger.info("🏁 MOCK DATA GENERATION COMPLETE!")
    logger.info("=" * 60)
    
    # Count successful creations
    vehicles_created = len(results.get("vehicles", []))
    users_created = len(results.get("users", []))
    
    maintenance_results = results.get("maintenance_data", {})
    records_created = len(maintenance_results.get("maintenance_records", []))
    licenses_created = len(maintenance_results.get("license_records", []))
    schedules_created = len(maintenance_results.get("maintenance_schedules", []))
    
    logger.info(f"📊 FINAL SUMMARY:")
    logger.info(f"   🚗 Vehicles Created: {vehicles_created}")
    logger.info(f"   👥 Users Created: {users_created}")
    logger.info(f"   🔧 Maintenance Records: {records_created}")
    logger.info(f"   📄 License Records: {licenses_created}")
    logger.info(f"   📅 Maintenance Schedules: {schedules_created}")
    logger.info(f"   ⏱️  Total Time: {total_elapsed:.2f} seconds")
    
    total_items = vehicles_created + users_created + records_created + licenses_created + schedules_created
    logger.info(f"   🎯 Total Items Created: {total_items}")
    
    # Success rate
    total_attempted = vehicles_count + drivers_count + managers_count + maintenance_records_count + licenses_count + schedules_count
    success_rate = (total_items / total_attempted) * 100 if total_attempted > 0 else 0
    logger.info(f"   📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        logger.info("🎉 EXCELLENT! Most data created successfully.")
    elif success_rate >= 60:
        logger.info("✅ GOOD! Majority of data created successfully.")
    else:
        logger.warning("⚠️  Some issues encountered. Check logs for details.")
    
    logger.info("\n💡 Next steps:")
    logger.info("   1. Check the Core and Maintenance service logs")
    logger.info("   2. Verify data in the web interface")
    logger.info("   3. Test API endpoints with the new data")
    
    return results


async def quick_test():
    """Create a small set of test data quickly"""
    logger.info("🧪 Running quick test with minimal data...")
    
    return await create_all_mock_data(
        vehicles_count=5,
        drivers_count=3,
        managers_count=2,
        maintenance_records_count=10,
        licenses_count=8,
        schedules_count=5
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create complete mock data set for SAMFMS")
    parser.add_argument("--vehicles", type=int, default=50, help="Number of vehicles (default: 50)")
    parser.add_argument("--drivers", type=int, default=50, help="Number of drivers (default: 50)")
    parser.add_argument("--managers", type=int, default=10, help="Number of fleet managers (default: 10)")
    parser.add_argument("--records", type=int, default=100, help="Number of maintenance records (default: 100)")
    parser.add_argument("--licenses", type=int, default=80, help="Number of license records (default: 80)")
    parser.add_argument("--schedules", type=int, default=60, help="Number of maintenance schedules (default: 60)")
    parser.add_argument("--quick", action="store_true", help="Run quick test with minimal data")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        if args.quick:
            results = asyncio.run(quick_test())
        else:
            results = asyncio.run(create_all_mock_data(
                args.vehicles, args.drivers, args.managers,
                args.records, args.licenses, args.schedules
            ))
        
        if results:
            logger.info("🎊 Mock data generation process completed successfully!")
        else:
            logger.error("❌ Mock data generation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
