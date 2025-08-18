"""
Summary test to validate Core route integration is working
"""
import pytest
import logging

logger = logging.getLogger(__name__)

def test_core_routes_integration_summary():
    """
    Summary test to validate that Core routes are properly integrated
    with Management and Maintenance blocks
    """
    logger.info("🔍 CORE ROUTES INTEGRATION SUMMARY")
    
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
    
    try:
        # 1. Test that all route modules import successfully
        from routes.api.vehicles import router as vehicles_router
        from routes.api.drivers import router as drivers_router
        from routes.api.maintenance import router as maintenance_router
        from routes.api.assignments import router as assignments_router
        logger.info("✅ All route modules imported successfully")
        
        # 2. Test that RequestRouter is properly configured
        from services.request_router import RequestRouter
        router = RequestRouter()
        logger.info("✅ RequestRouter instantiated successfully")
        
        # 3. Test key service mappings
        key_endpoints = [
            ("/api/vehicles", "management", "Vehicle management"),
            ("/api/drivers", "management", "Driver management"), 
            ("/api/maintenance", "vehicle_maintenance", "Maintenance service"),
            ("/api/assignments", "management", "Assignment management")
        ]
        
        for endpoint, expected_service, description in key_endpoints:
            service = router.get_service_for_endpoint(endpoint)
            assert service == expected_service, f"Expected {expected_service}, got {service}"
            logger.info(f"✅ {description}: {endpoint} -> {service}")
            
        # 4. Test route counts
        total_routes = (
            len(vehicles_router.routes) +
            len(drivers_router.routes) +
            len(maintenance_router.routes) +
            len(assignments_router.routes)
        )
        logger.info(f"✅ Total routes registered: {total_routes}")
        
        # 5. Test service coverage
        services = set(router.routing_map.values())
        expected_services = {"management", "vehicle_maintenance", "gps", "trip_planning"}
        assert expected_services.issubset(services), f"Missing services: {expected_services - services}"
        logger.info(f"✅ All expected services are configured: {services}")
        
        # 6. Test pattern matching
        pattern_tests = [
            ("/api/vehicles/123", "management"),
            ("/api/drivers/456", "management"),
            ("/api/maintenance/records/789", "vehicle_maintenance"),
            ("/api/assignments/101", "management")
        ]
        
        for endpoint, expected_service in pattern_tests:
            service = router.get_service_for_endpoint(endpoint)
            assert service == expected_service, f"Pattern matching failed for {endpoint}"
            logger.info(f"✅ Pattern matching works: {endpoint} -> {service}")
            
        logger.info("🎉 CORE ROUTES INTEGRATION SUMMARY: ALL TESTS PASSED!")
        logger.info("📊 Summary:")
        logger.info(f"   - Routes registered: {total_routes}")
        logger.info(f"   - Services configured: {len(services)}")
        logger.info(f"   - Vehicle routes: {len(vehicles_router.routes)}")
        logger.info(f"   - Driver routes: {len(drivers_router.routes)}")
        logger.info(f"   - Maintenance routes: {len(maintenance_router.routes)}")
        logger.info(f"   - Assignment routes: {len(assignments_router.routes)}")
        
    except Exception as e:
        pytest.fail(f"Core routes integration test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
