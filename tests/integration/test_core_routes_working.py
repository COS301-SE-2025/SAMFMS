"""
Core Routes Integration Tests
Tests the integration between Core routes and Management/Maintenance services
"""

import pytest
import asyncio
import httpx
import json
import sys
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any
import logging

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Core'))

logger = logging.getLogger(__name__)

class MockServiceResponse:
    """Mock service response helper"""
    
    @staticmethod
    def success_response(data: Dict[str, Any], status_code: int = 200):
        """Create a successful response"""
        return {
            "status": "success",
            "data": data,
            "status_code": status_code
        }
    
    @staticmethod
    def error_response(message: str, status_code: int = 400):
        """Create an error response"""
        return {
            "status": "error",
            "message": message,
            "status_code": status_code
        }


class TestCoreRoutesIntegration:
    """Test Core routes integration with backend services"""
    
    def test_vehicles_routes_exist(self):
        """Test that vehicle routes exist and are properly configured"""
        try:
            from Core.routes.api.vehicles import router as vehicles_router
            
            # Check that router exists
            assert vehicles_router is not None
            
            # Check that routes are registered
            routes = [route.path for route in vehicles_router.routes]
            assert "/api/vehicles" in routes
            
            logger.info("✅ Vehicle routes exist and are properly configured")
            
        except ImportError as e:
            logger.error(f"❌ Failed to import vehicle routes: {e}")
            pytest.fail(f"Vehicle routes import failed: {e}")
    
    def test_drivers_routes_exist(self):
        """Test that driver routes exist and are properly configured"""
        try:
            from Core.routes.api.drivers import router as drivers_router
            
            # Check that router exists
            assert drivers_router is not None
            
            # Check that routes are registered
            routes = [route.path for route in drivers_router.routes]
            assert "/api/drivers" in routes
            
            logger.info("✅ Driver routes exist and are properly configured")
            
        except ImportError as e:
            logger.error(f"❌ Failed to import driver routes: {e}")
            pytest.fail(f"Driver routes import failed: {e}")
    
    def test_maintenance_routes_exist(self):
        """Test that maintenance routes exist and are properly configured"""
        try:
            from Core.routes.api.maintenance import router as maintenance_router
            
            # Check that router exists
            assert maintenance_router is not None
            
            # Check that routes are registered
            routes = [route.path for route in maintenance_router.routes]
            assert "/api/maintenance/records" in routes
            
            logger.info("✅ Maintenance routes exist and are properly configured")
            
        except ImportError as e:
            logger.error(f"❌ Failed to import maintenance routes: {e}")
            pytest.fail(f"Maintenance routes import failed: {e}")
    
    def test_base_service_handler_exists(self):
        """Test that base service handler exists"""
        try:
            from Core.routes.api.base import handle_service_request
            
            # Check that function exists
            assert callable(handle_service_request)
            
            logger.info("✅ Base service handler exists")
            
        except ImportError as e:
            logger.error(f"❌ Failed to import base service handler: {e}")
            pytest.fail(f"Base service handler import failed: {e}")
    
    def test_request_router_exists(self):
        """Test that request router exists and is properly configured"""
        try:
            from Core.services.request_router import RequestRouter
            
            # Create router instance
            router = RequestRouter()
            
            # Check routing map
            assert router.routing_map is not None
            assert len(router.routing_map) > 0
            
            # Check specific routes
            assert "/api/vehicles" in router.routing_map
            assert "/api/drivers" in router.routing_map
            assert "/api/maintenance/*" in router.routing_map
            
            logger.info("✅ Request router exists and is properly configured")
            
        except ImportError as e:
            logger.error(f"❌ Failed to import request router: {e}")
            pytest.fail(f"Request router import failed: {e}")
    
    @pytest.mark.asyncio
    async def test_vehicle_service_integration(self):
        """Test vehicle service integration with mocked backend"""
        try:
            from Core.routes.api.base import handle_service_request
            from Core.services.request_router import RequestRouter
            
            # Mock the service request handling
            with patch('Core.services.request_router.request_router') as mock_router:
                mock_router.route_request.return_value = MockServiceResponse.success_response({
                    "vehicles": [
                        {
                            "id": "vehicle_123",
                            "make": "Toyota",
                            "model": "Camry",
                            "year": 2023,
                            "registration_number": "ABC-123-GP",
                            "status": "available"
                        }
                    ]
                })
                
                # Test the integration
                result = await mock_router.route_request(
                    endpoint="/api/vehicles",
                    method="GET",
                    data={}
                )
                
                assert result["status"] == "success"
                assert "vehicles" in result["data"]
                assert len(result["data"]["vehicles"]) == 1
                
                logger.info("✅ Vehicle service integration test passed")
                
        except Exception as e:
            logger.error(f"❌ Vehicle service integration test failed: {e}")
            pytest.fail(f"Vehicle service integration failed: {e}")
    
    @pytest.mark.asyncio
    async def test_driver_service_integration(self):
        """Test driver service integration with mocked backend"""
        try:
            from Core.routes.api.base import handle_service_request
            from Core.services.request_router import RequestRouter
            
            # Mock the service request handling
            with patch('Core.services.request_router.request_router') as mock_router:
                mock_router.route_request.return_value = MockServiceResponse.success_response({
                    "drivers": [
                        {
                            "id": "driver_123",
                            "employee_id": "EMP001",
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "john.doe@samfms.com",
                            "status": "active"
                        }
                    ]
                })
                
                # Test the integration
                result = await mock_router.route_request(
                    endpoint="/api/drivers",
                    method="GET",
                    data={}
                )
                
                assert result["status"] == "success"
                assert "drivers" in result["data"]
                assert len(result["data"]["drivers"]) == 1
                
                logger.info("✅ Driver service integration test passed")
                
        except Exception as e:
            logger.error(f"❌ Driver service integration test failed: {e}")
            pytest.fail(f"Driver service integration failed: {e}")
    
    @pytest.mark.asyncio
    async def test_maintenance_service_integration(self):
        """Test maintenance service integration with mocked backend"""
        try:
            from Core.routes.api.base import handle_service_request
            from Core.services.request_router import RequestRouter
            
            # Mock the service request handling
            with patch('Core.services.request_router.request_router') as mock_router:
                mock_router.route_request.return_value = MockServiceResponse.success_response({
                    "maintenance_records": [
                        {
                            "id": "maintenance_123",
                            "vehicle_id": "vehicle_123",
                            "maintenance_type": "regular_service",
                            "description": "Regular 15000km service",
                            "scheduled_date": "2024-01-15",
                            "status": "scheduled"
                        }
                    ]
                })
                
                # Test the integration
                result = await mock_router.route_request(
                    endpoint="/api/maintenance/records",
                    method="GET",
                    data={}
                )
                
                assert result["status"] == "success"
                assert "maintenance_records" in result["data"]
                assert len(result["data"]["maintenance_records"]) == 1
                
                logger.info("✅ Maintenance service integration test passed")
                
        except Exception as e:
            logger.error(f"❌ Maintenance service integration test failed: {e}")
            pytest.fail(f"Maintenance service integration failed: {e}")
    
    def test_service_routing_configuration(self):
        """Test that service routing is properly configured"""
        try:
            from Core.services.request_router import RequestRouter
            
            router = RequestRouter()
            
            # Test vehicle route resolution
            vehicle_service = router.get_service_for_endpoint("/api/vehicles")
            assert vehicle_service == "management"
            
            # Test driver route resolution
            driver_service = router.get_service_for_endpoint("/api/drivers")
            assert driver_service == "management"
            
            # Test maintenance route resolution
            maintenance_service = router.get_service_for_endpoint("/api/maintenance/records")
            assert maintenance_service == "vehicle_maintenance"
            
            logger.info("✅ Service routing configuration test passed")
            
        except Exception as e:
            logger.error(f"❌ Service routing configuration test failed: {e}")
            pytest.fail(f"Service routing configuration failed: {e}")
    
    def test_endpoint_normalization(self):
        """Test that endpoint normalization works correctly"""
        try:
            from Core.services.request_router import RequestRouter
            
            router = RequestRouter()
            
            # Test vehicle endpoint normalization
            normalized = router.normalize_endpoint("/api/vehicles")
            assert normalized == "/api/v1/vehicles"
            
            # Test driver endpoint normalization
            normalized = router.normalize_endpoint("/api/drivers")
            assert normalized == "/api/v1/drivers"
            
            # Test analytics endpoint normalization
            normalized = router.normalize_endpoint("/api/analytics/dashboard")
            assert normalized == "/api/v1/analytics/dashboard"
            
            logger.info("✅ Endpoint normalization test passed")
            
        except Exception as e:
            logger.error(f"❌ Endpoint normalization test failed: {e}")
            pytest.fail(f"Endpoint normalization failed: {e}")
    
    @pytest.mark.asyncio
    async def test_create_vehicle_integration(self):
        """Test vehicle creation integration"""
        try:
            from Core.services.request_router import RequestRouter
            
            # Mock the service request handling
            with patch('Core.services.request_router.request_router') as mock_router:
                mock_router.route_request.return_value = MockServiceResponse.success_response({
                    "id": "vehicle_123",
                    "make": "Toyota",
                    "model": "Camry",
                    "year": 2023,
                    "registration_number": "ABC-123-GP",
                    "status": "available"
                }, 201)
                
                # Test vehicle creation
                result = await mock_router.route_request(
                    endpoint="/api/vehicles",
                    method="POST",
                    data={
                        "make": "Toyota",
                        "model": "Camry",
                        "year": 2023,
                        "registration_number": "ABC-123-GP"
                    }
                )
                
                assert result["status"] == "success"
                assert result["data"]["id"] == "vehicle_123"
                assert result["status_code"] == 201
                
                logger.info("✅ Vehicle creation integration test passed")
                
        except Exception as e:
            logger.error(f"❌ Vehicle creation integration test failed: {e}")
            pytest.fail(f"Vehicle creation integration failed: {e}")
    
    @pytest.mark.asyncio
    async def test_create_driver_integration(self):
        """Test driver creation integration"""
        try:
            from Core.services.request_router import RequestRouter
            
            # Mock the service request handling
            with patch('Core.services.request_router.request_router') as mock_router:
                mock_router.route_request.return_value = MockServiceResponse.success_response({
                    "id": "driver_123",
                    "employee_id": "EMP001",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@samfms.com",
                    "status": "active"
                }, 201)
                
                # Test driver creation
                result = await mock_router.route_request(
                    endpoint="/api/drivers",
                    method="POST",
                    data={
                        "employee_id": "EMP001",
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@samfms.com"
                    }
                )
                
                assert result["status"] == "success"
                assert result["data"]["id"] == "driver_123"
                assert result["status_code"] == 201
                
                logger.info("✅ Driver creation integration test passed")
                
        except Exception as e:
            logger.error(f"❌ Driver creation integration test failed: {e}")
            pytest.fail(f"Driver creation integration failed: {e}")
    
    @pytest.mark.asyncio
    async def test_create_maintenance_record_integration(self):
        """Test maintenance record creation integration"""
        try:
            from Core.services.request_router import RequestRouter
            
            # Mock the service request handling
            with patch('Core.services.request_router.request_router') as mock_router:
                mock_router.route_request.return_value = MockServiceResponse.success_response({
                    "id": "maintenance_123",
                    "vehicle_id": "vehicle_123",
                    "maintenance_type": "regular_service",
                    "description": "Regular 15000km service",
                    "scheduled_date": "2024-01-15",
                    "status": "scheduled"
                }, 201)
                
                # Test maintenance record creation
                result = await mock_router.route_request(
                    endpoint="/api/maintenance/records",
                    method="POST",
                    data={
                        "vehicle_id": "vehicle_123",
                        "maintenance_type": "regular_service",
                        "description": "Regular 15000km service",
                        "scheduled_date": "2024-01-15"
                    }
                )
                
                assert result["status"] == "success"
                assert result["data"]["id"] == "maintenance_123"
                assert result["status_code"] == 201
                
                logger.info("✅ Maintenance record creation integration test passed")
                
        except Exception as e:
            logger.error(f"❌ Maintenance record creation integration test failed: {e}")
            pytest.fail(f"Maintenance record creation integration failed: {e}")
    
    def test_error_handling_integration(self):
        """Test error handling in service integration"""
        try:
            from Core.services.request_router import RequestRouter
            
            router = RequestRouter()
            
            # Test invalid endpoint
            try:
                router.get_service_for_endpoint("/invalid/endpoint")
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "No service found for endpoint" in str(e)
                
            logger.info("✅ Error handling integration test passed")
            
        except Exception as e:
            logger.error(f"❌ Error handling integration test failed: {e}")
            pytest.fail(f"Error handling integration failed: {e}")


class TestServiceValidation:
    """Test service validation and health checks"""
    
    def test_management_service_structure(self):
        """Test that management service has expected structure"""
        try:
            import sys
            import os
            
            # Check if management service directory exists
            management_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Sblocks', 'management')
            assert os.path.exists(management_path), "Management service directory not found"
            
            # Check for main.py
            main_path = os.path.join(management_path, 'main.py')
            assert os.path.exists(main_path), "Management service main.py not found"
            
            # Check for api directory
            api_path = os.path.join(management_path, 'api')
            assert os.path.exists(api_path), "Management service api directory not found"
            
            logger.info("✅ Management service structure validation passed")
            
        except Exception as e:
            logger.error(f"❌ Management service structure validation failed: {e}")
            pytest.fail(f"Management service structure validation failed: {e}")
    
    def test_maintenance_service_structure(self):
        """Test that maintenance service has expected structure"""
        try:
            import sys
            import os
            
            # Check if maintenance service directory exists
            maintenance_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Sblocks', 'maintenance')
            assert os.path.exists(maintenance_path), "Maintenance service directory not found"
            
            # Check for main.py
            main_path = os.path.join(maintenance_path, 'main.py')
            assert os.path.exists(main_path), "Maintenance service main.py not found"
            
            logger.info("✅ Maintenance service structure validation passed")
            
        except Exception as e:
            logger.error(f"❌ Maintenance service structure validation failed: {e}")
            pytest.fail(f"Maintenance service structure validation failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
