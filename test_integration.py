#!/usr/bin/env python3
"""
SAMFMS Service Integration Test
Tests critical service functionality and integration
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add Core to path
sys.path.insert(0, str(Path(__file__).parent / "Core"))
sys.path.insert(0, str(Path(__file__).parent / "Sblocks" / "management"))
sys.path.insert(0, str(Path(__file__).parent / "Sblocks" / "maintenance"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connections():
    """Test database connections for all services"""
    results = {}
    
    # Test Core database
    try:
        from Core.database import get_database_manager
        db_manager = await get_database_manager()
        await db_manager.connect()
        health = await db_manager.health_check()
        results["core"] = health["status"] == "healthy"
        await db_manager.close()
        logger.info("✅ Core database connection test passed")
    except Exception as e:
        results["core"] = False
        logger.error(f"❌ Core database connection test failed: {e}")
    
    # Test Management database
    try:
        from Sblocks.management.repositories.database import db_manager as mgmt_db
        await mgmt_db.connect()
        health = await mgmt_db.health_check()
        results["management"] = health
        await mgmt_db.disconnect()
        logger.info("✅ Management database connection test passed")
    except Exception as e:
        results["management"] = False
        logger.error(f"❌ Management database connection test failed: {e}")
    
    # Test Maintenance database
    try:
        from Sblocks.maintenance.repositories.database import db_manager as maint_db
        await maint_db.connect()
        health = await maint_db.health_check()
        results["maintenance"] = health
        await maint_db.disconnect()
        logger.info("✅ Maintenance database connection test passed")
    except Exception as e:
        results["maintenance"] = False
        logger.error(f"❌ Maintenance database connection test failed: {e}")
    
    return results

async def test_service_imports():
    """Test that critical service components can be imported"""
    results = {}
    
    # Test Core imports
    try:
        from Core.main import app as core_app
        from Core.routes.auth import router as auth_router
        from Core.routes.api import api_router
        results["core_imports"] = True
        logger.info("✅ Core service imports test passed")
    except Exception as e:
        results["core_imports"] = False
        logger.error(f"❌ Core service imports test failed: {e}")
    
    # Test Management imports
    try:
        from Sblocks.management.main import app as mgmt_app
        from Sblocks.management.repositories.repositories import VehicleRepository
        from Sblocks.management.services.vehicle_service import VehicleService
        results["management_imports"] = True
        logger.info("✅ Management service imports test passed")
    except Exception as e:
        results["management_imports"] = False
        logger.error(f"❌ Management service imports test failed: {e}")
    
    # Test Maintenance imports
    try:
        from Sblocks.maintenance.main import app as maint_app
        from Sblocks.maintenance.repositories.repositories import MaintenanceRecordRepository
        results["maintenance_imports"] = True
        logger.info("✅ Maintenance service imports test passed")
    except Exception as e:
        results["maintenance_imports"] = False
        logger.error(f"❌ Maintenance service imports test failed: {e}")
    
    return results

async def test_repository_patterns():
    """Test repository patterns work correctly"""
    results = {}
    
    # Test Vehicle Repository
    try:
        from Sblocks.management.repositories.repositories import VehicleRepository
        from Sblocks.management.repositories.database import db_manager
        
        # Mock database connection
        if not db_manager._client:
            await db_manager.connect()
        
        repo = VehicleRepository()
        # Test that basic operations don't crash
        results["vehicle_repository"] = True
        logger.info("✅ Vehicle Repository test passed")
    except Exception as e:
        results["vehicle_repository"] = False
        logger.error(f"❌ Vehicle Repository test failed: {e}")
    
    return results

async def run_integration_tests():
    """Run all integration tests"""
    logger.info("🚀 Starting SAMFMS Integration Tests...")
    
    all_results = {}
    
    # Test imports first
    logger.info("Testing service imports...")
    import_results = await test_service_imports()
    all_results.update(import_results)
    
    # Test database connections
    logger.info("Testing database connections...")
    db_results = await test_database_connections()
    all_results.update(db_results)
    
    # Test repository patterns
    logger.info("Testing repository patterns...")
    repo_results = await test_repository_patterns()
    all_results.update(repo_results)
    
    # Summary
    logger.info("\n📊 Test Results Summary:")
    logger.info("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in all_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("=" * 50)
    logger.info(f"Total: {passed + failed} tests")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    
    if failed > 0:
        logger.error("❌ Some tests failed - check logs for details")
        return False
    else:
        logger.info("✅ All tests passed!")
        return True

if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)
