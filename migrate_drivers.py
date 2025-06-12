#!/usr/bin/env python3
"""
Driver Management Migration Script
==================================

This script migrates driver management functionality from the Core service 
to the Management Sblock service for better architectural organization.

Migration Steps:
1. Connect to both Core and Management databases
2. Copy driver data from Core to Management
3. Validate data integrity
4. Update any existing vehicle assignments
5. Clean up old driver data (optional)

Author: SAMFMS Development Team
Date: May 30, 2025
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configurations
CORE_DB_URL = os.getenv("CORE_MONGODB_URL", "mongodb://host.docker.internal:27017")
MANAGEMENT_DB_URL = os.getenv("MANAGEMENT_MONGODB_URL", "mongodb://host.docker.internal:27017")

CORE_DB_NAME = "samfms_core"
MANAGEMENT_DB_NAME = "management_db"


class DriverMigrator:
    def __init__(self):
        self.core_client = None
        self.management_client = None
        self.core_db = None
        self.management_db = None
        
    async def connect_databases(self):
        """Connect to both databases"""
        try:
            # Connect to Core database
            self.core_client = AsyncIOMotorClient(CORE_DB_URL)
            self.core_db = self.core_client[CORE_DB_NAME]
            await self.core_client.admin.command('ping')
            logger.info("✅ Connected to Core database")
            
            # Connect to Management database
            self.management_client = AsyncIOMotorClient(MANAGEMENT_DB_URL)
            self.management_db = self.management_client[MANAGEMENT_DB_NAME]
            await self.management_client.admin.command('ping')
            logger.info("✅ Connected to Management database")
            
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def check_existing_data(self):
        """Check for existing driver data in both databases"""
        try:
            # Check Core database
            core_drivers = await self.core_db.drivers.count_documents({})
            logger.info(f"📊 Found {core_drivers} drivers in Core database")
            
            # Check Management database
            management_drivers = await self.management_db.drivers.count_documents({})
            logger.info(f"📊 Found {management_drivers} drivers in Management database")
            
            return core_drivers, management_drivers
        except Exception as e:
            logger.error(f"❌ Failed to check existing data: {e}")
            return 0, 0
    
    async def migrate_drivers(self, dry_run=True):
        """Migrate driver data from Core to Management database"""
        try:
            migrated_count = 0
            errors = []
            
            # Get all drivers from Core database
            async for driver in self.core_db.drivers.find({}):
                try:
                    # Transform driver data for Management database
                    transformed_driver = await self.transform_driver_data(driver)
                    
                    if not dry_run:
                        # Check if driver already exists in Management database
                        existing = await self.management_db.drivers.find_one({
                            "employee_id": transformed_driver.get("employee_id")
                        })
                        
                        if existing:
                            logger.warning(f"⚠️  Driver {transformed_driver['employee_id']} already exists, skipping")
                            continue
                        
                        # Insert into Management database
                        await self.management_db.drivers.insert_one(transformed_driver)
                        logger.info(f"✅ Migrated driver: {transformed_driver['employee_id']}")
                    else:
                        logger.info(f"🔍 [DRY RUN] Would migrate driver: {transformed_driver.get('employee_id', 'Unknown')}")
                    
                    migrated_count += 1
                    
                except Exception as e:
                    error_msg = f"Failed to migrate driver {driver.get('employee_id', 'Unknown')}: {e}"
                    errors.append(error_msg)
                    logger.error(f"❌ {error_msg}")
            
            logger.info(f"📈 Migration completed: {migrated_count} drivers processed")
            if errors:
                logger.warning(f"⚠️  {len(errors)} errors occurred during migration")
                for error in errors:
                    logger.warning(f"   - {error}")
            
            return migrated_count, errors
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return 0, [str(e)]
    
    async def transform_driver_data(self, core_driver):
        """Transform driver data from Core format to Management format"""
        # Remove Core-specific fields and ensure Management format
        transformed = {
            "employee_id": core_driver.get("employee_id"),
            "user_id": str(core_driver.get("user_id", "")),
            "license_number": core_driver.get("license_number"),
            "license_class": core_driver.get("license_class", ["B"]),  # Default to class B
            "license_expiry": core_driver.get("license_expiry"),
            "phone_number": core_driver.get("phone_number"),
            "emergency_contact": core_driver.get("emergency_contact"),
            "emergency_phone": core_driver.get("emergency_phone"),
            "department": core_driver.get("department"),
            "hire_date": core_driver.get("hire_date"),
            "status": core_driver.get("status", "active"),
            "medical_certificate_expiry": core_driver.get("medical_certificate_expiry"),
            "prdp_certificate": core_driver.get("prdp_certificate", False),
            "driving_record_points": core_driver.get("driving_record_points", 0),
            "current_vehicle_id": core_driver.get("current_vehicle_id"),
            "authorized_vehicle_types": core_driver.get("authorized_vehicle_types", []),
            "performance_rating": core_driver.get("performance_rating"),
            "notes": core_driver.get("notes"),
            "created_at": core_driver.get("created_at", datetime.utcnow()),
            "updated_at": datetime.utcnow()
        }
        
        # Remove None values
        return {k: v for k, v in transformed.items() if v is not None}
    
    async def create_indexes(self):
        """Create necessary indexes in Management database"""
        try:
            await self.management_db.drivers.create_index("employee_id", unique=True)
            await self.management_db.drivers.create_index("license_number", unique=True)
            await self.management_db.drivers.create_index("user_id")
            await self.management_db.drivers.create_index("status")
            await self.management_db.drivers.create_index("department")
            await self.management_db.drivers.create_index("current_vehicle_id")
            logger.info("✅ Created driver indexes in Management database")
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")
    
    async def validate_migration(self):
        """Validate the migration was successful"""
        try:
            # Count drivers in both databases
            core_count = await self.core_db.drivers.count_documents({})
            management_count = await self.management_db.drivers.count_documents({})
            
            logger.info(f"📊 Validation Results:")
            logger.info(f"   Core database: {core_count} drivers")
            logger.info(f"   Management database: {management_count} drivers")
            
            # Sample validation - check a few random drivers
            sample_drivers = []
            async for driver in self.management_db.drivers.find({}).limit(3):
                sample_drivers.append(driver)
            
            for driver in sample_drivers:
                logger.info(f"✅ Sample driver: {driver.get('employee_id')} - {driver.get('status')}")
            
            return core_count, management_count
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return 0, 0
    
    async def close_connections(self):
        """Close database connections"""
        if self.core_client:
            self.core_client.close()
        if self.management_client:
            self.management_client.close()
        logger.info("🔌 Database connections closed")


async def main():
    """Main migration function"""
    migrator = DriverMigrator()
    
    try:
        # Connect to databases
        if not await migrator.connect_databases():
            return
        
        # Check existing data
        core_count, management_count = await migrator.check_existing_data()
        
        if core_count == 0:
            logger.info("ℹ️  No drivers found in Core database - nothing to migrate")
            return
        
        if management_count > 0:
            response = input(f"⚠️  Management database already has {management_count} drivers. Continue? (y/n): ")
            if response.lower() != 'y':
                logger.info("Migration cancelled by user")
                return
        
        # Ask for migration mode
        print("\\n🚀 Driver Migration Options:")
        print("1. Dry run (show what would be migrated)")
        print("2. Actual migration")
        choice = input("Enter choice (1 or 2): ")
        
        dry_run = choice != "2"
        
        # Create indexes first
        await migrator.create_indexes()
        
        # Perform migration
        logger.info(f"🔄 Starting migration ({'DRY RUN' if dry_run else 'ACTUAL MIGRATION'})...")
        migrated_count, errors = await migrator.migrate_drivers(dry_run=dry_run)
        
        if not dry_run and migrated_count > 0:
            # Validate migration
            await migrator.validate_migration()
            
            # Ask about cleanup
            if len(errors) == 0:
                cleanup = input("\\n🧹 Migration successful! Remove driver data from Core database? (y/n): ")
                if cleanup.lower() == 'y':
                    deleted = await migrator.core_db.drivers.delete_many({})
                    logger.info(f"🗑️  Removed {deleted.deleted_count} drivers from Core database")
        
        logger.info("🎉 Migration process completed!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
    finally:
        await migrator.close_connections()


if __name__ == "__main__":
    print("="*60)
    print("🚛 SAMFMS Driver Management Migration")
    print("="*60)
    print("Moving driver management from Core to Management Sblock")
    print("for better architectural organization.\\n")
    
    asyncio.run(main())
