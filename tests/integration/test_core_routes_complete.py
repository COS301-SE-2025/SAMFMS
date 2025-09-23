"""
Complete integration tests for Core routes with proper mocking
Tests all routes for proper registration and basic functionality
"""
import pytest
import asyncio
import logging
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestCoreRoutesComplete:
    """Test suite for Core routes integration"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup test environment"""
        self.test_token = "test_token_123"
        self.mock_user_context = {
            "user_id": "test_user_123",
            "organization_id": "test_org_456",
            "role": "admin"
        }
        
    def test_all_routes_exist(self):
        """Test that all expected routes are registered"""
        logger.info("🔍 Testing that all routes are registered...")
        
        # Import here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from routes.api.vehicles import router as vehicles_router
            from routes.api.drivers import router as drivers_router
            from routes.api.maintenance import router as maintenance_router
            from routes.api.assignments import router as assignments_router
            
            # Check that routers have routes
            assert len(.routes) > 0, "Vehicle routes should exist"
            assert len(drivers_router.routes) > 0, "Driver routes should exist"
            assert len(maintenance_router.routes) > 0, "Maintenance routes should exist"
            assert len(assignments_router.routes) > 0, "Assignment routes should exist"
            
            # Check specific route paths
            vehicle_paths = [route.path for route in vehicles_router.routes]
            driver_paths = [route.path for route in drivers_router.routes]
            maintenance_paths = [route.path for route in maintenance_router.routes]
            assignment_paths = [route.path for route in assignments_router.routes]
            
            # Vehicle routes
            assert "/" in vehicle_paths, "Vehicle base route should exist"
            assert "/{vehicle_id}" in vehicle_paths, "Vehicle detail route should exist"
            
            # Driver routes  
            assert "/" in driver_paths, "Driver base route should exist"
            assert "/{driver_id}" in driver_paths, "Driver detail route should exist"
            
            # Maintenance routes
            assert "/" in maintenance_paths, "Maintenance base route should exist"
            assert "/{record_id}" in maintenance_paths, "Maintenance detail route should exist"
            
            # Assignment routes
            assert "/" in assignment_paths, "Assignment base route should exist"
            assert "/{assignment_id}" in assignment_paths, "Assignment detail route should exist"
            
            logger.info("✅ All routes are properly registered")
            
        except ImportError as e:
            pytest.fail(f"Failed to import route modules: {e}")
            
    def test_service_routing_configuration(self):
        """Test that service routing is properly configured"""
        logger.info("🔍 Testing service routing configuration...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from services.request_router import RequestRouter
            
            router = RequestRouter()
            
            # Test key endpoints have service mappings
            test_endpoints = [
                "/api/vehicles",
                "/api/drivers", 
                "/api/maintenance",
                "/api/assignments",
                "/api/vehicle-assignments",
                "/api/v1/vehicles",
                "/api/v1/drivers",
                "/api/v1/assignments"
            ]
            
            for endpoint in test_endpoints:
                try:
                    service = router.get_service_for_endpoint(endpoint)
                    assert service in ["management", "vehicle_maintenance"], f"Unknown service: {service}"
                    logger.info(f"✅ {endpoint} -> {service}")
                except ValueError as e:
                    pytest.fail(f"No service mapping for {endpoint}: {e}")
                    
            logger.info("✅ Service routing is properly configured")
            
        except ImportError as e:
            pytest.fail(f"Failed to import RequestRouter: {e}")
            
    @patch('Core.services.core_auth_service.CoreAuthService.authorize_request')
    @patch('Core.services.request_router.RequestRouter.route_request')
    def test_vehicle_routes_mock(self, mock_route_request, mock_authorize):
        """Test vehicle routes with mocked services"""
        logger.info("🔍 Testing vehicle routes with mocked services...")
        
        # Setup mocks
        mock_authorize.return_value = self.mock_user_context
        mock_route_request.return_value = {
            "status": "success",
            "data": [{"id": "vehicle_123", "make": "Toyota", "model": "Camry"}]
        }
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from routes.api.base import handle_service_request
            
            # Test GET vehicles
            result = asyncio.run(handle_service_request(
                endpoint="/api/vehicles",
                method="GET",
                data={},
                headers={"Authorization": f"Bearer {self.test_token}"}
            ))
            
            assert result["status"] == "success"
            assert "data" in result
            mock_authorize.assert_called_once()
            mock_route_request.assert_called_once()
            
            logger.info("✅ Vehicle routes work with mocked services")
            
        except Exception as e:
            pytest.fail(f"Vehicle routes test failed: {e}")
            
    @patch('Core.services.core_auth_service.CoreAuthService.authorize_request')
    @patch('Core.services.request_router.RequestRouter.route_request')
    def test_driver_routes_mock(self, mock_route_request, mock_authorize):
        """Test driver routes with mocked services"""
        logger.info("🔍 Testing driver routes with mocked services...")
        
        # Setup mocks
        mock_authorize.return_value = self.mock_user_context
        mock_route_request.return_value = {
            "status": "success",
            "data": [{"id": "driver_123", "name": "John Doe", "license_number": "D123456"}]
        }
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from routes.api.base import handle_service_request
            
            # Test GET drivers
            result = asyncio.run(handle_service_request(
                endpoint="/api/drivers",
                method="GET",
                data={},
                headers={"Authorization": f"Bearer {self.test_token}"}
            ))
            
            assert result["status"] == "success"
            assert "data" in result
            mock_authorize.assert_called_once()
            mock_route_request.assert_called_once()
            
            logger.info("✅ Driver routes work with mocked services")
            
        except Exception as e:
            pytest.fail(f"Driver routes test failed: {e}")
            
    @patch('Core.services.core_auth_service.CoreAuthService.authorize_request')
    @patch('Core.services.request_router.RequestRouter.route_request')
    def test_maintenance_routes_mock(self, mock_route_request, mock_authorize):
        """Test maintenance routes with mocked services"""
        logger.info("🔍 Testing maintenance routes with mocked services...")
        
        # Setup mocks
        mock_authorize.return_value = self.mock_user_context
        mock_route_request.return_value = {
            "status": "success",
            "data": [{"id": "maintenance_123", "vehicle_id": "vehicle_123", "type": "oil_change"}]
        }
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from routes.api.base import handle_service_request
            
            # Test GET maintenance
            result = asyncio.run(handle_service_request(
                endpoint="/api/maintenance",
                method="GET",
                data={},
                headers={"Authorization": f"Bearer {self.test_token}"}
            ))
            
            assert result["status"] == "success"
            assert "data" in result
            mock_authorize.assert_called_once()
            mock_route_request.assert_called_once()
            
            logger.info("✅ Maintenance routes work with mocked services")
            
        except Exception as e:
            pytest.fail(f"Maintenance routes test failed: {e}")
            
    @patch('Core.services.core_auth_service.CoreAuthService.authorize_request')
    @patch('Core.services.request_router.RequestRouter.route_request')
    def test_assignment_routes_mock(self, mock_route_request, mock_authorize):
        """Test assignment routes with mocked services"""
        logger.info("🔍 Testing assignment routes with mocked services...")
        
        # Setup mocks
        mock_authorize.return_value = self.mock_user_context
        mock_route_request.return_value = {
            "status": "success",
            "data": [{"id": "assignment_123", "driver_id": "driver_123", "vehicle_id": "vehicle_123"}]
        }
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from routes.api.base import handle_service_request
            
            # Test GET assignments
            result = asyncio.run(handle_service_request(
                endpoint="/api/assignments",
                method="GET",
                data={},
                headers={"Authorization": f"Bearer {self.test_token}"}
            ))
            
            assert result["status"] == "success"
            assert "data" in result
            mock_authorize.assert_called_once()
            mock_route_request.assert_called_once()
            
            logger.info("✅ Assignment routes work with mocked services")
            
        except Exception as e:
            pytest.fail(f"Assignment routes test failed: {e}")
            
    def test_route_validation_functions(self):
        """Test route validation functions"""
        logger.info("🔍 Testing route validation functions...")
        
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
            
            # Test invalid data - should raise ValidationError
            invalid_data = {"make": "Toyota"}  # Missing model and year
            
            with pytest.raises(ValidationError) as exc_info:
                validate_required_fields(invalid_data, required_fields)
                
            assert "Missing required fields: model, year" in str(exc_info.value)
            
            logger.info("✅ Route validation functions work correctly")
            
        except ImportError as e:
            pytest.fail(f"Failed to import validation functions: {e}")
            
    def test_service_health_checks(self):
        """Test service health check functionality"""
        logger.info("🔍 Testing service health checks...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from services.request_router import RequestRouter
            
            router = RequestRouter()
            
            # Test that routing map has expected services
            services = set(router.routing_map.values())
            expected_services = {"management", "vehicle_maintenance", "gps", "trip_planning"}
            
            for service in expected_services:
                assert service in services, f"Expected service {service} not found in routing map"
                
            logger.info("✅ Service health checks passed")
            
        except Exception as e:
            pytest.fail(f"Service health checks failed: {e}")
            
    def test_error_handling(self):
        """Test error handling in routes"""
        logger.info("🔍 Testing error handling...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from routes.api.base import handle_service_request
            from fastapi import HTTPException
            
            # Test without authorization header - should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(handle_service_request(
                    endpoint="/api/vehicles",
                    method="GET",
                    data={},
                    headers={}  # No authorization header
                ))
            
            assert exc_info.value.status_code == 401
            
            logger.info("✅ Error handling works correctly")
            
        except Exception as e:
            pytest.fail(f"Error handling test failed: {e}")
            
    def test_complete_route_coverage(self):
        """Test that all major routes are covered"""
        logger.info("🔍 Testing complete route coverage...")
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))
        
        try:
            from services.request_router import RequestRouter
            
            router = RequestRouter()
            
            # Test all major endpoint patterns
            major_endpoints = [
                "/api/vehicles",
                "/api/drivers",
                "/api/maintenance",
                "/api/assignments",
                "/api/vehicle-assignments",
                "/api/analytics",
                "/api/v1/vehicles",
                "/api/v1/drivers",
                "/api/v1/assignments"
            ]
            
            services_found = set()
            for endpoint in major_endpoints:
                try:
                    service = router.get_service_for_endpoint(endpoint)
                    services_found.add(service)
                    logger.info(f"✅ {endpoint} -> {service}")
                except ValueError:
                    logger.warning(f"⚠️  No service mapping for {endpoint}")
                    
            # Should have found both management and vehicle_maintenance services
            assert "management" in services_found, "Management service should be found"
            assert "vehicle_maintenance" in services_found, "Vehicle maintenance service should be found"
            
            logger.info("✅ Complete route coverage verified")
            
        except Exception as e:
            pytest.fail(f"Route coverage test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
