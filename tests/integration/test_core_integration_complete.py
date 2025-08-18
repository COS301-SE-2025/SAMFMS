"""
Comprehensive Core Routes Integration Test
Tests all route integrations with proper mocking and service validation
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any
import logging

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))

logger = logging.getLogger(__name__)

class TestCoreIntegrationComplete:
    """Complete integration tests for all Core routes"""
    
    def test_all_routes_registered(self):
        """Test that all routes are properly registered"""
        try:
            from Core.routes.api import api_router
            
            # Get all routes
            routes = [route.path for route in api_router.routes]
            
            # Check vehicle routes
            vehicle_routes = [r for r in routes if '/vehicles' in r]
            assert len(vehicle_routes) > 0, "No vehicle routes found"
            
            # Check driver routes
            driver_routes = [r for r in routes if '/drivers' in r]
            assert len(driver_routes) > 0, "No driver routes found"
            
            # Check maintenance routes
            maintenance_routes = [r for r in routes if '/maintenance' in r]
            assert len(maintenance_routes) > 0, "No maintenance routes found"
            
            # Check assignments routes
            assignment_routes = [r for r in routes if '/assignments' in r]
            assert len(assignment_routes) > 0, "No assignment routes found"
            
            logger.info("✅ All routes are properly registered")
            
        except Exception as e:
            logger.error(f"❌ Route registration test failed: {e}")
            pytest.fail(f"Route registration failed: {e}")
    
    def test_service_routing_fixed(self):
        """Test that the service routing issue is fixed"""
        try:
            from Core.services.request_router import RequestRouter
            
            router = RequestRouter()
            
            # Test the previously failing vehicle-assignments route
            service = router.get_service_for_endpoint("/api/vehicle-assignments")
            assert service == "management"
            
            # Test the normalized version
            normalized = router.normalize_endpoint("/api/vehicle-assignments")
            assert normalized == "/api/v1/vehicle-assignments"
            
            # Test that the normalized endpoint has a mapping
            normalized_service = router.get_service_for_endpoint(normalized)
            assert normalized_service == "management"
            
            logger.info("✅ Service routing is fixed")
            
        except Exception as e:
            logger.error(f"❌ Service routing test failed: {e}")
            pytest.fail(f"Service routing failed: {e}")
    
    @pytest.mark.asyncio
    async def test_vehicle_routes_integration(self):
        """Test vehicle routes integration with proper mocking"""
        try:
            from Core.routes.api.base import handle_service_request
            from Core.services.core_auth_service import core_auth_service
            from Core.services.request_router import request_router
            
            # Mock dependencies
            mock_credentials = Mock()
            mock_credentials.credentials = "mock_token"
            
            mock_user_context = {"user_id": "test_user", "role": "admin"}
            
            # Mock the auth service
            with patch.object(core_auth_service, 'authorize_request', return_value=mock_user_context):
                # Mock the request router
                with patch.object(request_router, 'route_request', return_value={
                    "status": "success",
                    "data": {
                        "vehicles": [
                            {
                                "id": "vehicle_123",
                                "make": "Toyota",
                                "model": "Camry",
                                "year": 2023,
                                "registration_number": "ABC-123-GP"
                            }
                        ]
                    }
                }) as mock_route:
                    
                    # Test the service request
                    result = await handle_service_request(
                        endpoint="/api/vehicles",
                        method="GET", 
                        data={},
                        credentials=mock_credentials
                    )
                    
                    # Verify the call
                    mock_route.assert_called_once()
                    call_args = mock_route.call_args
                    assert call_args[1]["endpoint"] == "/api/vehicles"
                    assert call_args[1]["method"] == "GET"
                    assert call_args[1]["user_context"] == mock_user_context
                    
                    # Verify the result
                    assert result["status"] == "success"
                    assert "vehicles" in result["data"]
                    
                    logger.info("✅ Vehicle routes integration test passed")
                    
        except Exception as e:
            logger.error(f"❌ Vehicle routes integration test failed: {e}")
            pytest.fail(f"Vehicle routes integration failed: {e}")
    
    @pytest.mark.asyncio
    async def test_driver_routes_integration(self):
        """Test driver routes integration with proper mocking"""
        try:
            from Core.routes.api.base import handle_service_request
            from Core.services.core_auth_service import core_auth_service
            from Core.services.request_router import request_router
            
            # Mock dependencies
            mock_credentials = Mock()
            mock_credentials.credentials = "mock_token"
            
            mock_user_context = {"user_id": "test_user", "role": "admin"}
            
            # Mock the auth service
            with patch.object(core_auth_service, 'authorize_request', return_value=mock_user_context):
                # Mock the request router
                with patch.object(request_router, 'route_request', return_value={
                    "status": "success",
                    "data": {
                        "drivers": [
                            {
                                "id": "driver_123",
                                "employee_id": "EMP001",
                                "first_name": "John",
                                "last_name": "Doe",
                                "email": "john.doe@samfms.com"
                            }
                        ]
                    }
                }) as mock_route:
                    
                    # Test the service request
                    result = await handle_service_request(
                        endpoint="/api/drivers",
                        method="GET", 
                        data={},
                        credentials=mock_credentials
                    )
                    
                    # Verify the call
                    mock_route.assert_called_once()
                    call_args = mock_route.call_args
                    assert call_args[1]["endpoint"] == "/api/drivers"
                    assert call_args[1]["method"] == "GET"
                    assert call_args[1]["user_context"] == mock_user_context
                    
                    # Verify the result
                    assert result["status"] == "success"
                    assert "drivers" in result["data"]
                    
                    logger.info("✅ Driver routes integration test passed")
                    
        except Exception as e:
            logger.error(f"❌ Driver routes integration test failed: {e}")
            pytest.fail(f"Driver routes integration failed: {e}")
    
    @pytest.mark.asyncio
    async def test_maintenance_routes_integration(self):
        """Test maintenance routes integration with proper mocking"""
        try:
            from Core.routes.api.base import handle_service_request
            from Core.services.core_auth_service import core_auth_service
            from Core.services.request_router import request_router
            
            # Mock dependencies
            mock_credentials = Mock()
            mock_credentials.credentials = "mock_token"
            
            mock_user_context = {"user_id": "test_user", "role": "admin"}
            
            # Mock the auth service
            with patch.object(core_auth_service, 'authorize_request', return_value=mock_user_context):
                # Mock the request router
                with patch.object(request_router, 'route_request', return_value={
                    "status": "success",
                    "data": {
                        "maintenance_records": [
                            {
                                "id": "maintenance_123",
                                "vehicle_id": "vehicle_123",
                                "maintenance_type": "regular_service",
                                "description": "Regular 15000km service",
                                "scheduled_date": "2024-01-15"
                            }
                        ]
                    }
                }) as mock_route:
                    
                    # Test the service request
                    result = await handle_service_request(
                        endpoint="/api/maintenance/records",
                        method="GET", 
                        data={},
                        credentials=mock_credentials
                    )
                    
                    # Verify the call
                    mock_route.assert_called_once()
                    call_args = mock_route.call_args
                    assert call_args[1]["endpoint"] == "/api/maintenance/records"
                    assert call_args[1]["method"] == "GET"
                    assert call_args[1]["user_context"] == mock_user_context
                    
                    # Verify the result
                    assert result["status"] == "success"
                    assert "maintenance_records" in result["data"]
                    
                    logger.info("✅ Maintenance routes integration test passed")
                    
        except Exception as e:
            logger.error(f"❌ Maintenance routes integration test failed: {e}")
            pytest.fail(f"Maintenance routes integration failed: {e}")
    
    @pytest.mark.asyncio
    async def test_assignment_routes_integration(self):
        """Test assignment routes integration with proper mocking"""
        try:
            from Core.routes.api.base import handle_service_request
            from Core.services.core_auth_service import core_auth_service
            from Core.services.request_router import request_router
            
            # Mock dependencies
            mock_credentials = Mock()
            mock_credentials.credentials = "mock_token"
            
            mock_user_context = {"user_id": "test_user", "role": "admin"}
            
            # Mock the auth service
            with patch.object(core_auth_service, 'authorize_request', return_value=mock_user_context):
                # Mock the request router
                with patch.object(request_router, 'route_request', return_value={
                    "status": "success",
                    "data": {
                        "assignments": [
                            {
                                "id": "assignment_123",
                                "vehicle_id": "vehicle_123",
                                "driver_id": "driver_123",
                                "status": "active"
                            }
                        ]
                    }
                }) as mock_route:
                    
                    # Test the service request
                    result = await handle_service_request(
                        endpoint="/api/assignments",
                        method="GET", 
                        data={},
                        credentials=mock_credentials
                    )
                    
                    # Verify the call
                    mock_route.assert_called_once()
                    call_args = mock_route.call_args
                    assert call_args[1]["endpoint"] == "/api/assignments"
                    assert call_args[1]["method"] == "GET"
                    assert call_args[1]["user_context"] == mock_user_context
                    
                    # Verify the result
                    assert result["status"] == "success"
                    assert "assignments" in result["data"]
                    
                    logger.info("✅ Assignment routes integration test passed")
                    
        except Exception as e:
            logger.error(f"❌ Assignment routes integration test failed: {e}")
            pytest.fail(f"Assignment routes integration failed: {e}")
    
    @pytest.mark.asyncio
    async def test_create_operations_integration(self):
        """Test create operations for all major resources"""
        try:
            from Core.routes.api.base import handle_service_request
            from Core.services.core_auth_service import core_auth_service
            from Core.services.request_router import request_router
            
            # Mock dependencies
            mock_credentials = Mock()
            mock_credentials.credentials = "mock_token"
            
            mock_user_context = {"user_id": "test_user", "role": "admin"}
            
            # Mock the auth service
            with patch.object(core_auth_service, 'authorize_request', return_value=mock_user_context):
                # Mock the request router
                with patch.object(request_router, 'route_request') as mock_route:
                    
                    # Test vehicle creation
                    mock_route.return_value = {
                        "status": "success",
                        "data": {
                            "id": "vehicle_123",
                            "make": "Toyota",
                            "model": "Camry",
                            "year": 2023,
                            "registration_number": "ABC-123-GP"
                        }
                    }
                    
                    result = await handle_service_request(
                        endpoint="/api/vehicles",
                        method="POST",
                        data={
                            "make": "Toyota",
                            "model": "Camry",
                            "year": 2023,
                            "registration_number": "ABC-123-GP"
                        },
                        credentials=mock_credentials
                    )
                    
                    assert result["status"] == "success"
                    assert result["data"]["id"] == "vehicle_123"
                    
                    # Test driver creation
                    mock_route.return_value = {
                        "status": "success",
                        "data": {
                            "id": "driver_123",
                            "employee_id": "EMP001",
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "john.doe@samfms.com"
                        }
                    }
                    
                    result = await handle_service_request(
                        endpoint="/api/drivers",
                        method="POST",
                        data={
                            "employee_id": "EMP001",
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "john.doe@samfms.com"
                        },
                        credentials=mock_credentials
                    )
                    
                    assert result["status"] == "success"
                    assert result["data"]["id"] == "driver_123"
                    
                    # Test maintenance record creation
                    mock_route.return_value = {
                        "status": "success",
                        "data": {
                            "id": "maintenance_123",
                            "vehicle_id": "vehicle_123",
                            "maintenance_type": "regular_service",
                            "description": "Regular 15000km service",
                            "scheduled_date": "2024-01-15"
                        }
                    }
                    
                    result = await handle_service_request(
                        endpoint="/api/maintenance/records",
                        method="POST",
                        data={
                            "vehicle_id": "vehicle_123",
                            "maintenance_type": "regular_service",
                            "description": "Regular 15000km service",
                            "scheduled_date": "2024-01-15"
                        },
                        credentials=mock_credentials
                    )
                    
                    assert result["status"] == "success"
                    assert result["data"]["id"] == "maintenance_123"
                    
                    logger.info("✅ Create operations integration test passed")
                    
        except Exception as e:
            logger.error(f"❌ Create operations integration test failed: {e}")
            pytest.fail(f"Create operations integration failed: {e}")
    
    def test_all_endpoints_have_service_mapping(self):
        """Test that all endpoints have proper service mappings"""
        try:
            from Core.services.request_router import RequestRouter
            
            router = RequestRouter()
            
            # Test all major endpoints
            test_endpoints = [
                "/api/vehicles",
                "/api/drivers", 
                "/api/assignments",
                "/api/maintenance/records",
                "/api/maintenance/schedules",
                "/api/analytics/dashboard"
            ]
            
            for endpoint in test_endpoints:
                service = router.get_service_for_endpoint(endpoint)
                assert service is not None, f"No service mapping for {endpoint}"
                assert service in ["management", "vehicle_maintenance"], f"Invalid service {service} for {endpoint}"
                
                # Test normalized versions
                normalized = router.normalize_endpoint(endpoint)
                normalized_service = router.get_service_for_endpoint(normalized)
                assert normalized_service == service, f"Normalized endpoint {normalized} has different service"
            
            logger.info("✅ All endpoints have proper service mappings")
            
        except Exception as e:
            logger.error(f"❌ Service mapping test failed: {e}")
            pytest.fail(f"Service mapping failed: {e}")
    
    def test_route_validation_functions(self):
        """Test that route validation functions work properly"""
        try:
            from Core.routes.api.base import validate_required_fields
            from Core.utils.exceptions import ValidationError
            
            # Test successful validation
            data = {"make": "Toyota", "model": "Camry", "year": 2023}
            required_fields = ["make", "model", "year"]
            
            # Should not raise exception
            validate_required_fields(data, required_fields)
            
            # Test failed validation
            incomplete_data = {"make": "Toyota"}
            
            with pytest.raises(ValidationError):
                validate_required_fields(incomplete_data, required_fields)
            
            logger.info("✅ Route validation functions work properly")
            
        except Exception as e:
            logger.error(f"❌ Route validation test failed: {e}")
            pytest.fail(f"Route validation failed: {e}")


class TestServiceHealthChecks:
    """Test service health and connectivity"""
    
    def test_management_service_accessible(self):
        """Test that management service structure is accessible"""
        try:
            import os
            
            # Check if management service exists
            management_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Sblocks', 'management')
            assert os.path.exists(management_path), "Management service not found"
            
            # Check for required files
            main_file = os.path.join(management_path, 'main.py')
            assert os.path.exists(main_file), "Management service main.py not found"
            
            api_dir = os.path.join(management_path, 'api')
            assert os.path.exists(api_dir), "Management service API directory not found"
            
            logger.info("✅ Management service is accessible")
            
        except Exception as e:
            logger.error(f"❌ Management service accessibility test failed: {e}")
            pytest.fail(f"Management service accessibility failed: {e}")
    
    def test_maintenance_service_accessible(self):
        """Test that maintenance service structure is accessible"""
        try:
            import os
            
            # Check if maintenance service exists
            maintenance_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Sblocks', 'maintenance')
            assert os.path.exists(maintenance_path), "Maintenance service not found"
            
            # Check for required files
            main_file = os.path.join(maintenance_path, 'main.py')
            assert os.path.exists(main_file), "Maintenance service main.py not found"
            
            logger.info("✅ Maintenance service is accessible")
            
        except Exception as e:
            logger.error(f"❌ Maintenance service accessibility test failed: {e}")
            pytest.fail(f"Maintenance service accessibility failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
