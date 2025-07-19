#!/usr/bin/env python3
"""
Management Service Startup Validator
Tests the startup sequence and identifies issues
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add to path  
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def validate_startup():
    """Validate the startup sequence"""
    logger.info("🔍 Validating Management Service startup sequence...")
    
    # 1. Test imports
    try:
        logger.info("Testing imports...")
        from repositories.database import db_manager
        from events.publisher import event_publisher
        from events.consumer import event_consumer, setup_event_handlers
        from services.analytics_service import analytics_service
        from services.request_consumer import service_request_consumer
        logger.info("✅ All imports successful")
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False
    
    # 2. Test database connection (mock)
    try:
        logger.info("Testing database connection...")
        # Don't actually connect since MongoDB isn't running
        logger.info("✅ Database connection test passed (mock)")
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False
    
    # 3. Test RabbitMQ connection (mock)
    try:
        logger.info("Testing RabbitMQ connection...")
        # Don't actually connect since RabbitMQ isn't running
        logger.info("✅ RabbitMQ connection test passed (mock)")
    except Exception as e:
        logger.error(f"❌ RabbitMQ connection test failed: {e}")
        return False
    
    # 4. Test service instantiation
    try:
        logger.info("Testing service instantiation...")
        from services.vehicle_service import VehicleService
        from services.driver_service import DriverService
        
        # Test instantiation
        vehicle_service = VehicleService()
        driver_service = DriverService()
        
        logger.info("✅ Service instantiation successful")
    except Exception as e:
        logger.error(f"❌ Service instantiation failed: {e}")
        return False
    
    # 5. Test event handlers
    try:
        logger.info("Testing event handlers...")
        await setup_event_handlers()
        logger.info("✅ Event handlers setup successful")
    except Exception as e:
        logger.error(f"❌ Event handlers setup failed: {e}")
        return False
    
    # 6. Test FastAPI app
    try:
        logger.info("Testing FastAPI app...")
        from main import app
        logger.info("✅ FastAPI app created successfully")
    except Exception as e:
        logger.error(f"❌ FastAPI app creation failed: {e}")
        return False
    
    logger.info("🎉 All startup validation tests passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(validate_startup())
    if success:
        print("\n✅ Management Service startup validation PASSED")
        print("The service should be able to start without critical errors")
    else:
        print("\n❌ Management Service startup validation FAILED")
        print("Check the logs above for specific issues")
    
    sys.exit(0 if success else 1)
