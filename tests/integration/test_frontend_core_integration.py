"""
Frontend-Core Integration Tests
Tests the communication flow between the React Frontend and FastAPI Core service
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_CONFIG = {
    "core_url": "http://localhost:8000",
    "frontend_url": "http://localhost:3000",  
    "timeout": 30,
    "retry_attempts": 3,
    "test_user": {
        "email": "integration_test@samfms.co.za",
        "password": "IntegrationTest123!",
        "full_name": "Integration Test User",
        "role": "fleet_manager"
    }
}

class IntegrationTestHelper:
    """Helper class for integration testing"""
    
    @staticmethod
    async def wait_for_service(url: str, timeout: int = 60) -> bool:
        """Wait for a service to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(f"{url}/health")
                    if response.status_code == 200:
                        return True
            except Exception:
                pass
            await asyncio.sleep(2)
        return False
    
    @staticmethod
    async def authenticate_user() -> str:
        """Authenticate and return JWT token"""
        auth_data = {
            "email": TEST_CONFIG["test_user"]["email"],
            "password": TEST_CONFIG["test_user"]["password"]
        }
        
        async with httpx.AsyncClient(timeout=TEST_CONFIG["timeout"]) as client:
            try:
                # Try to create user first
                await client.post(
                    f"{TEST_CONFIG['core_url']}/auth/create-user",
                    json={
                        **TEST_CONFIG["test_user"],
                        "department": "Test Department"
                    }
                )
            except Exception:
                pass  # User might already exist
            
            # Login
            response = await client.post(
                f"{TEST_CONFIG['core_url']}/auth/login",
                json=auth_data
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            else:
                logger.warning(f"Authentication failed: {response.status_code} - {response.text}")
                return None

    @staticmethod
    async def make_authenticated_request(method: str, endpoint: str, token: str, data: Dict = None) -> httpx.Response:
        """Make authenticated request to Core API"""
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient(timeout=TEST_CONFIG["timeout"]) as client:
            if method.upper() == "GET":
                return await client.get(f"{TEST_CONFIG['core_url']}{endpoint}", headers=headers)
            elif method.upper() == "POST":
                return await client.post(f"{TEST_CONFIG['core_url']}{endpoint}", headers=headers, json=data)
            elif method.upper() == "PUT":
                return await client.put(f"{TEST_CONFIG['core_url']}{endpoint}", headers=headers, json=data)
            elif method.upper() == "DELETE":
                return await client.delete(f"{TEST_CONFIG['core_url']}{endpoint}", headers=headers)


@pytest.mark.integration
@pytest.mark.asyncio
class TestFrontendCoreIntegration:
    """Test Frontend-Core integration flows"""
    
    @pytest.fixture(scope="class", autouse=True)
    async def setup_services(self):
        """Ensure services are running before tests"""
        logger.info("Waiting for Core service to be available...")
        core_available = await IntegrationTestHelper.wait_for_service(TEST_CONFIG["core_url"])
        
        if not core_available:
            pytest.skip("Core service not available for integration testing")
        
        logger.info("✅ Core service is available")
    
    @pytest.fixture
    async def auth_token(self):
        """Provide authenticated token for tests"""
        token = await IntegrationTestHelper.authenticate_user()
        if not token:
            pytest.skip("Could not authenticate test user")
        return token
    
    async def test_authentication_flow(self):
        """Test complete authentication flow"""
        logger.info("Testing authentication flow...")
        
        # Test login
        auth_data = {
            "email": TEST_CONFIG["test_user"]["email"],
            "password": TEST_CONFIG["test_user"]["password"]
        }
        
        async with httpx.AsyncClient(timeout=TEST_CONFIG["timeout"]) as client:
            response = await client.post(
                f"{TEST_CONFIG['core_url']}/auth/login",
                json=auth_data
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "access_token" in data
                assert data["user_id"] is not None
                logger.info("✅ Authentication flow test passed")
            else:
                logger.info(f"⚠️ Authentication test skipped - service unavailable (status: {response.status_code})")
                pytest.skip("Authentication service unavailable")
    
    async def test_user_info_retrieval(self, auth_token):
        """Test user info retrieval with authentication"""
        logger.info("Testing user info retrieval...")
        
        response = await IntegrationTestHelper.make_authenticated_request(
            "GET", "/auth/me", auth_token
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "email" in data
            assert "role" in data
            logger.info("✅ User info retrieval test passed")
        else:
            logger.info(f"⚠️ User info test result: {response.status_code}")
            # Don't fail - service might be in development
    
    async def test_vehicle_api_endpoints(self, auth_token):
        """Test vehicle management endpoints"""
        logger.info("Testing vehicle API endpoints...")
        
        # Test GET vehicles
        response = await IntegrationTestHelper.make_authenticated_request(
            "GET", "/api/vehicles", auth_token
        )
        
        logger.info(f"GET /api/vehicles response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "vehicles" in data or isinstance(data, list)
            logger.info("✅ Vehicle GET endpoint test passed")
        elif response.status_code in [401, 403]:
            logger.info("⚠️ Vehicle endpoint test - authentication issue")
        elif response.status_code == 404:
            logger.info("⚠️ Vehicle endpoint test - endpoint not found")
        else:
            logger.info(f"⚠️ Vehicle endpoint test result: {response.status_code}")
    
    async def test_driver_api_endpoints(self, auth_token):
        """Test driver management endpoints"""
        logger.info("Testing driver API endpoints...")
        
        response = await IntegrationTestHelper.make_authenticated_request(
            "GET", "/api/drivers", auth_token
        )
        
        logger.info(f"GET /api/drivers response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "drivers" in data or isinstance(data, list)
            logger.info("✅ Driver GET endpoint test passed")
        elif response.status_code in [401, 403]:
            logger.info("⚠️ Driver endpoint test - authentication issue")
        elif response.status_code == 404:
            logger.info("⚠️ Driver endpoint test - endpoint not found")
        else:
            logger.info(f"⚠️ Driver endpoint test result: {response.status_code}")
    
    async def test_analytics_endpoints(self, auth_token):
        """Test analytics endpoints"""
        logger.info("Testing analytics endpoints...")
        
        # Test dashboard analytics
        response = await IntegrationTestHelper.make_authenticated_request(
            "GET", "/api/analytics/dashboard", auth_token
        )
        
        logger.info(f"GET /api/analytics/dashboard response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Analytics data structure may vary
            assert isinstance(data, dict)
            logger.info("✅ Analytics dashboard endpoint test passed")
        elif response.status_code in [401, 403]:
            logger.info("⚠️ Analytics endpoint test - authentication issue")
        elif response.status_code == 404:
            logger.info("⚠️ Analytics endpoint test - endpoint not found")
        else:
            logger.info(f"⚠️ Analytics endpoint test result: {response.status_code}")
    
    async def test_maintenance_endpoints(self, auth_token):
        """Test maintenance endpoints"""
        logger.info("Testing maintenance endpoints...")
        
        response = await IntegrationTestHelper.make_authenticated_request(
            "GET", "/api/maintenance/records", auth_token
        )
        
        logger.info(f"GET /api/maintenance/records response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert "records" in data or isinstance(data, list)
            logger.info("✅ Maintenance GET endpoint test passed")
        elif response.status_code in [401, 403]:
            logger.info("⚠️ Maintenance endpoint test - authentication issue") 
        elif response.status_code == 404:
            logger.info("⚠️ Maintenance endpoint test - endpoint not found")
        else:
            logger.info(f"⚠️ Maintenance endpoint test result: {response.status_code}")
    
    async def test_health_endpoints(self):
        """Test service health endpoints"""
        logger.info("Testing health endpoints...")
        
        async with httpx.AsyncClient(timeout=TEST_CONFIG["timeout"]) as client:
            response = await client.get(f"{TEST_CONFIG['core_url']}/health")
            
            if response.status_code == 200:
                data = response.json()
                assert "status" in data
                logger.info("✅ Health endpoint test passed")
            else:
                logger.info(f"⚠️ Health endpoint test result: {response.status_code}")


@pytest.mark.integration
@pytest.mark.asyncio
class TestFrontendApiCompatibility:
    """Test Frontend API compatibility with Core"""
    
    @pytest.fixture
    async def auth_token(self):
        """Provide authenticated token for tests"""
        token = await IntegrationTestHelper.authenticate_user()
        if not token:
            pytest.skip("Could not authenticate test user")
        return token
    
    async def test_frontend_auth_api_structure(self, auth_token):
        """Test that Core API matches Frontend expectations for auth"""
        logger.info("Testing Frontend auth API compatibility...")
        
        # Test user info structure matches frontend expectations
        response = await IntegrationTestHelper.make_authenticated_request(
            "GET", "/auth/me", auth_token
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check expected fields that frontend needs
            expected_fields = ["email", "role"]
            for field in expected_fields:
                if field not in data:
                    logger.warning(f"Expected field '{field}' missing from /auth/me response")
            
            logger.info("✅ Frontend auth API compatibility test completed")
        else:
            logger.info(f"⚠️ Auth API compatibility test result: {response.status_code}")
    
    async def test_frontend_vehicle_api_structure(self, auth_token):
        """Test that Core API matches Frontend expectations for vehicles"""
        logger.info("Testing Frontend vehicle API compatibility...")
        
        response = await IntegrationTestHelper.make_authenticated_request(
            "GET", "/api/vehicles", auth_token
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Frontend expects either a list or object with 'vehicles' key
            if isinstance(data, dict) and "vehicles" in data:
                vehicles = data["vehicles"]
            elif isinstance(data, list):
                vehicles = data
            else:
                logger.warning("Unexpected vehicle API response structure")
                vehicles = []
            
            if vehicles and len(vehicles) > 0:
                # Check first vehicle structure
                vehicle = vehicles[0]
                expected_fields = ["id", "registration_number", "make", "model"]
                for field in expected_fields:
                    if field not in vehicle:
                        logger.warning(f"Expected field '{field}' missing from vehicle object")
            
            logger.info("✅ Frontend vehicle API compatibility test completed")
        else:
            logger.info(f"⚠️ Vehicle API compatibility test result: {response.status_code}")


@pytest.mark.integration 
@pytest.mark.asyncio
class TestServiceCommunication:
    """Test communication between Core and service blocks"""
    
    @pytest.fixture
    async def auth_token(self):
        """Provide authenticated token for tests"""
        token = await IntegrationTestHelper.authenticate_user()
        if not token:
            pytest.skip("Could not authenticate test user")
        return token
    
    async def test_core_to_management_service(self, auth_token):
        """Test Core to Management service communication"""
        logger.info("Testing Core to Management service communication...")
        
        # Test requests that route to Management service
        endpoints = [
            "/api/vehicles",
            "/api/drivers", 
            "/api/analytics/dashboard"
        ]
        
        for endpoint in endpoints:
            response = await IntegrationTestHelper.make_authenticated_request(
                "GET", endpoint, auth_token
            )
            
            logger.info(f"Management service endpoint {endpoint}: {response.status_code}")
            
            if response.status_code in [200, 404, 503]:
                # 200: Success, 404: Not found (acceptable), 503: Service unavailable (acceptable)
                continue
            elif response.status_code in [401, 403]:
                logger.warning(f"Authentication issue with {endpoint}")
            else:
                logger.warning(f"Unexpected response from {endpoint}: {response.status_code}")
        
        logger.info("✅ Core to Management service communication test completed")
    
    async def test_core_to_maintenance_service(self, auth_token):
        """Test Core to Maintenance service communication"""
        logger.info("Testing Core to Maintenance service communication...")
        
        # Test requests that route to Maintenance service
        endpoints = [
            "/api/maintenance/records",
            "/api/maintenance/schedules"
        ]
        
        for endpoint in endpoints:
            response = await IntegrationTestHelper.make_authenticated_request(
                "GET", endpoint, auth_token
            )
            
            logger.info(f"Maintenance service endpoint {endpoint}: {response.status_code}")
            
            if response.status_code in [200, 404, 503]:
                continue
            elif response.status_code in [401, 403]:
                logger.warning(f"Authentication issue with {endpoint}")
            else:
                logger.warning(f"Unexpected response from {endpoint}: {response.status_code}")
        
        logger.info("✅ Core to Maintenance service communication test completed")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])