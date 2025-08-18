#!/usr/bin/env python3
"""
Management Service Health Check and Diagnostic Tool
This script validates the management service configuration and identifies issues
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_management_service():
    """Test management service components"""
    results = {}
    
    # Test database connection
    try:
        from repositories.database import db_manager
        await db_manager.connect()
        results["database"] = "✅ Connected"
        await db_manager.disconnect()
    except Exception as e:
        results["database"] = f"❌ Failed: {e}"
    
    # Test repository imports
    try:
        from repositories.repositories import (
            VehicleRepository, 
            DriverRepository, 
            VehicleAssignmentRepository,
            AnalyticsRepository
        )
        results["repositories"] = "✅ All repositories imported"
    except Exception as e:
        results["repositories"] = f"❌ Failed: {e}"
    
    # Test service imports
    try:
        from services.vehicle_service import VehicleService
        from services.driver_service import DriverService
        from services.analytics_service import AnalyticsService
        results["services"] = "✅ All services imported"
    except Exception as e:
        results["services"] = f"❌ Failed: {e}"
    
    # Test event system
    try:
        from events.consumer import EventConsumer
        from events.publisher import EventPublisher
        consumer = EventConsumer()
        publisher = EventPublisher()
        results["events"] = "✅ Event system imported"
    except Exception as e:
        results["events"] = f"❌ Failed: {e}"
    
    # Test main app
    try:
        from main import app
        results["main_app"] = "✅ Main app imported"
    except Exception as e:
        results["main_app"] = f"❌ Failed: {e}"
    
    # Display results
    print("\n" + "="*50)
    print("Management Service Health Check Results")
    print("="*50)
    
    for component, status in results.items():
        print(f"{component}: {status}")
    
    print("="*50)
    
    # Check for critical failures
    failures = [k for k, v in results.items() if v.startswith("❌")]
    if failures:
        print(f"\n❌ Critical failures in: {', '.join(failures)}")
        return False
    else:
        print("\n✅ All components passed!")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_management_service())
    sys.exit(0 if success else 1)
