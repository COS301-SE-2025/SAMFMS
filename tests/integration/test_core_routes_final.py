"""
Final comprehensive test suite for Core route integration
Tests all routes are properly registered and configured
"""
import pytest
import logging
from unittest.mock import Mock, patch
from fastapi.security import HTTPAuthorizationCredentials

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestCoreRoutesFinal:
    """Final comprehensive test suite for Core routes"""
    
    def test_all_routes_registered(self):
        """Test that all route modules are properly registered"""
        logger.info("🔍 Testing route registration...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            # Import all route modules
            from routes.api.vehicles import router as vehicles_router
            from routes.api.drivers import router as drivers_router
            from routes.api.maintenance import router as maintenance_router
            from routes.api.assignments import router as assignments_router
            
            # Check routers have routes
            assert len(vehicles_router.routes) > 0, "Vehicle router should have routes"
            assert len(drivers_router.routes) > 0, "Driver router should have routes"
            assert len(maintenance_router.routes) > 0, "Maintenance router should have routes"
            assert len(assignments_router.routes) > 0, "Assignment router should have routes"
            
            # Check route paths
            vehicle_paths = [route.path for route in vehicles_router.routes]
            driver_paths = [route.path for route in drivers_router.routes]
            maintenance_paths = [route.path for route in maintenance_router.routes]
            assignment_paths = [route.path for route in assignments_router.routes]
            
            # Vehicle routes should include base API path
            assert "/api/vehicles" in vehicle_paths, "Vehicle base route should exist"
            assert "/api/vehicles/{vehicle_id}" in vehicle_paths, "Vehicle detail route should exist"
            
            # Driver routes should include base API path
            assert "/api/drivers" in driver_paths, "Driver base route should exist"
            assert "/api/drivers/{driver_id}" in driver_paths, "Driver detail route should exist"
            
            # Maintenance routes should include base API path
            assert "/api/maintenance" in maintenance_paths, "Maintenance base route should exist"
            assert "/api/maintenance/{record_id}" in maintenance_paths, "Maintenance detail route should exist"
            
            # Assignment routes should include base API path
            assert "/api/assignments" in assignment_paths, "Assignment base route should exist"
            assert "/api/assignments/{assignment_id}" in assignment_paths, "Assignment detail route should exist"
            
            logger.info("✅ All routes are properly registered")
            
        except ImportError as e:
            pytest.fail(f"Failed to import route modules: {e}")
        except Exception as e:
            pytest.fail(f"Route registration test failed: {e}")
            
    def test_service_routing_complete(self):
        """Test that service routing covers all endpoints"""
        logger.info("🔍 Testing complete service routing...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from services.request_router import RequestRouter
            
            router = RequestRouter()
            
            # Test all major endpoints
            endpoints_to_test = [
                ("/api/vehicles", "management"),
                ("/api/drivers", "management"),
                ("/api/maintenance", "vehicle_maintenance"),
                ("/api/assignments", "management"),
                ("/api/vehicle-assignments", "management"),
                ("/api/analytics", "management"),
                ("/api/v1/vehicles", "management"),
                ("/api/v1/drivers", "management"),
                ("/api/v1/assignments", "management")
            ]
            
            services_found = set()
            for endpoint, expected_service in endpoints_to_test:
                try:
                    service = router.get_service_for_endpoint(endpoint)
                    services_found.add(service)
                    assert service == expected_service, f"Expected {expected_service}, got {service} for {endpoint}"
                    logger.info(f"✅ {endpoint} -> {service}")
                except ValueError as e:
                    pytest.fail(f"No service mapping for {endpoint}: {e}")
                    
            # Verify we found both key services
            assert "management" in services_found, "Management service should be found"
            assert "vehicle_maintenance" in services_found, "Vehicle maintenance service should be found"
            
            logger.info("✅ Service routing is complete")
            
        except Exception as e:
            pytest.fail(f"Service routing test failed: {e}")
            
    def test_routing_patterns_work(self):
        """Test that routing patterns match correctly"""
        logger.info("🔍 Testing routing patterns...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from services.request_router import RequestRouter
            
            router = RequestRouter()
            
            # Test pattern matching works
            test_patterns = [
                ("/api/vehicles/123", "management"),
                ("/api/drivers/456", "management"),
                ("/api/maintenance/789", "vehicle_maintenance"),
                ("/api/assignments/101", "management"),
                ("/api/vehicle-assignments/202", "management"),
                ("/api/analytics/reports", "management"),
                ("/api/v1/vehicles/search", "management"),
                ("/api/v1/drivers/active", "management")
            ]
            
            for endpoint, expected_service in test_patterns:
                try:
                    service = router.get_service_for_endpoint(endpoint)
                    assert service == expected_service, f"Expected {expected_service}, got {service} for {endpoint}"
                    logger.info(f"✅ {endpoint} -> {service}")
                except ValueError as e:
                    pytest.fail(f"Pattern matching failed for {endpoint}: {e}")
                    
            logger.info("✅ Routing patterns work correctly")
            
        except Exception as e:
            pytest.fail(f"Routing pattern test failed: {e}")
            
    def test_endpoint_normalization(self):
        """Test that endpoint normalization works correctly"""
        logger.info("🔍 Testing endpoint normalization...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from services.request_router import RequestRouter
            
            router = RequestRouter()
            
            # Test normalization
            test_cases = [
                ("/api/vehicles", "/api/v1/vehicles"),
                ("/api/drivers", "/api/v1/drivers"),
                ("/api/vehicle-assignments", "/api/v1/vehicle-assignments"),
                ("/api/analytics/reports", "/api/v1/analytics/reports"),
                ("/api/v1/vehicles", "/api/v1/vehicles"),  # Should remain unchanged
                ("/api/maintenance", "/api/maintenance")    # Should remain unchanged
            ]
            
            for original, expected in test_cases:
                normalized = router.normalize_endpoint(original)
                assert normalized == expected, f"Expected {expected}, got {normalized} for {original}"
                logger.info(f"✅ {original} -> {normalized}")
                
            logger.info("✅ Endpoint normalization works correctly")
            
        except Exception as e:
            pytest.fail(f"Endpoint normalization test failed: {e}")
            
    def test_validation_functions(self):
        """Test validation functions work correctly"""
        logger.info("🔍 Testing validation functions...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from routes.api.base import validate_required_fields
            from utils.exceptions import ValidationError
            
            # Test valid data
            valid_data = {"make": "Toyota", "model": "Camry", "year": 2020}
            required_fields = ["make", "model", "year"]
            
            # Should not raise exception
            validate_required_fields(valid_data, required_fields)
            
            # Test invalid data
            invalid_data = {"make": "Toyota"}
            
            with pytest.raises(ValidationError):
                validate_required_fields(invalid_data, required_fields)
                
            logger.info("✅ Validation functions work correctly")
            
        except Exception as e:
            pytest.fail(f"Validation test failed: {e}")
            
    def test_service_discovery(self):
        """Test service discovery configuration"""
        logger.info("🔍 Testing service discovery...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from services.request_router import RequestRouter
            
            router = RequestRouter()
            
            # Get all unique services from routing map
            services = set(router.routing_map.values())
            
            # Expected services should be present
            expected_services = {
                "management",
                "vehicle_maintenance", 
                "gps",
                "trip_planning"
            }
            
            for service in expected_services:
                assert service in services, f"Expected service {service} not found"
                logger.info(f"✅ Service {service} is configured")
                
            logger.info("✅ Service discovery is properly configured")
            
        except Exception as e:
            pytest.fail(f"Service discovery test failed: {e}")
            
    def test_error_handling_structure(self):
        """Test that error handling structures are in place"""
        logger.info("🔍 Testing error handling structures...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            # Test exception imports
            from utils.exceptions import (
                ServiceUnavailableError,
                AuthorizationError,
                ValidationError,
                ServiceTimeoutError
            )
            
            # Test that we can instantiate these exceptions
            errors = [
                ServiceUnavailableError("Test service unavailable"),
                AuthorizationError("Test authorization error"),
                ValidationError("Test validation error"),
                ServiceTimeoutError("Test timeout error")
            ]
            
            for error in errors:
                assert isinstance(error, Exception), f"Error {type(error)} should be an Exception"
                logger.info(f"✅ {type(error).__name__} is properly defined")
                
            logger.info("✅ Error handling structures are in place")
            
        except Exception as e:
            pytest.fail(f"Error handling test failed: {e}")
            
    def test_complete_integration_status(self):
        """Test overall integration status"""
        logger.info("🔍 Testing complete integration status...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            # Test all major components can be imported and instantiated
            from services.request_router import RequestRouter
            from services.core_auth_service import CoreAuthService
            from routes.api.vehicles import router as vehicles_router
            from routes.api.drivers import router as drivers_router
            from routes.api.maintenance import router as maintenance_router
            from routes.api.assignments import router as assignments_router
            
            # Test instantiation
            router = RequestRouter()
            auth_service = CoreAuthService()
            
            # Test routing map completeness
            routing_map = router.routing_map
            assert len(routing_map) > 0, "Routing map should not be empty"
            
            # Test route registration
            all_routers = [vehicles_router, drivers_router, maintenance_router, assignments_router]
            for route_router in all_routers:
                assert len(route_router.routes) > 0, f"Router {route_router} should have routes"
                
            # Count total routes
            total_routes = sum(len(route_router.routes) for route_router in all_routers)
            logger.info(f"Total routes registered: {total_routes}")
            
            # Test service coverage
            services = set(routing_map.values())
            logger.info(f"Services configured: {services}")
            
            assert total_routes > 0, "Should have routes registered"
            assert len(services) > 0, "Should have services configured"
            
            logger.info("✅ Complete integration status is healthy")
            
        except Exception as e:
            pytest.fail(f"Complete integration test failed: {e}")


class TestRouteValidation:
    """Test route validation and structure"""
    
    def test_vehicle_route_structure(self):
        """Test vehicle route structure"""
        logger.info("🔍 Testing vehicle route structure...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from routes.api.vehicles import router as vehicles_router
            
            # Get all routes
            routes = vehicles_router.routes
            paths = [route.path for route in routes]
            methods = [list(route.methods) for route in routes]
            
            # Check for essential vehicle routes
            essential_paths = [
                "/api/vehicles",
                "/api/vehicles/{vehicle_id}"
            ]
            
            for path in essential_paths:
                assert path in paths, f"Essential path {path} not found in vehicle routes"
                logger.info(f"✅ Vehicle route {path} exists")
                
            # Check we have GET and POST methods
            all_methods = [method for method_list in methods for method in method_list]
            assert "GET" in all_methods, "Vehicle routes should have GET method"
            assert "POST" in all_methods, "Vehicle routes should have POST method"
            
            logger.info("✅ Vehicle route structure is correct")
            
        except Exception as e:
            pytest.fail(f"Vehicle route structure test failed: {e}")
            
    def test_driver_route_structure(self):
        """Test driver route structure"""
        logger.info("🔍 Testing driver route structure...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from routes.api.drivers import router as drivers_router
            
            # Get all routes
            routes = drivers_router.routes
            paths = [route.path for route in routes]
            methods = [list(route.methods) for route in routes]
            
            # Check for essential driver routes
            essential_paths = [
                "/api/drivers",
                "/api/drivers/{driver_id}"
            ]
            
            for path in essential_paths:
                assert path in paths, f"Essential path {path} not found in driver routes"
                logger.info(f"✅ Driver route {path} exists")
                
            # Check we have GET and POST methods
            all_methods = [method for method_list in methods for method in method_list]
            assert "GET" in all_methods, "Driver routes should have GET method"
            assert "POST" in all_methods, "Driver routes should have POST method"
            
            logger.info("✅ Driver route structure is correct")
            
        except Exception as e:
            pytest.fail(f"Driver route structure test failed: {e}")
            
    def test_maintenance_route_structure(self):
        """Test maintenance route structure"""
        logger.info("🔍 Testing maintenance route structure...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from routes.api.maintenance import router as maintenance_router
            
            # Get all routes
            routes = maintenance_router.routes
            paths = [route.path for route in routes]
            methods = [list(route.methods) for route in routes]
            
            # Check for essential maintenance routes
            essential_paths = [
                "/api/maintenance",
                "/api/maintenance/{record_id}"
            ]
            
            for path in essential_paths:
                assert path in paths, f"Essential path {path} not found in maintenance routes"
                logger.info(f"✅ Maintenance route {path} exists")
                
            # Check we have GET and POST methods
            all_methods = [method for method_list in methods for method in method_list]
            assert "GET" in all_methods, "Maintenance routes should have GET method"
            assert "POST" in all_methods, "Maintenance routes should have POST method"
            
            logger.info("✅ Maintenance route structure is correct")
            
        except Exception as e:
            pytest.fail(f"Maintenance route structure test failed: {e}")
            
    def test_assignment_route_structure(self):
        """Test assignment route structure"""
        logger.info("🔍 Testing assignment route structure...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from routes.api.assignments import router as assignments_router
            
            # Get all routes
            routes = assignments_router.routes
            paths = [route.path for route in routes]
            methods = [list(route.methods) for route in routes]
            
            # Check for essential assignment routes
            essential_paths = [
                "/api/assignments",
                "/api/assignments/{assignment_id}"
            ]
            
            for path in essential_paths:
                assert path in paths, f"Essential path {path} not found in assignment routes"
                logger.info(f"✅ Assignment route {path} exists")
                
            # Check we have GET and POST methods
            all_methods = [method for method_list in methods for method in method_list]
            assert "GET" in all_methods, "Assignment routes should have GET method"
            assert "POST" in all_methods, "Assignment routes should have POST method"
            
            logger.info("✅ Assignment route structure is correct")
            
        except Exception as e:
            pytest.fail(f"Assignment route structure test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
