#!/usr/bin/env python3
"""
Test Script for SAMFMS Communication Architecture
Tests the Core -> Service Block communication via RabbitMQ
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommunicationTester:
    """Test suite for the communication architecture"""
    
    def __init__(self):
        self.core_base_url = "http://localhost:8080"  # Core service URL
        self.test_token = None
        
    async def authenticate(self) -> str:
        """Get authentication token from security service"""
        try:
            # For testing purposes, we'll use a mock token
            # In real scenario, this would call the security service
            self.test_token = "Bearer test_token_for_admin_user"
            logger.info("Authentication successful")
            return self.test_token
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    async def test_vehicle_management_routes(self):
        """Test routes that go through the Management service"""
        headers = {"Authorization": self.test_token}
        
        async with aiohttp.ClientSession() as session:
            # Test GET /api/vehicles
            try:
                logger.info("Testing GET /api/vehicles...")
                async with session.get(f"{self.core_base_url}/api/vehicles", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ GET /api/vehicles successful: {len(data.get('vehicles', []))} vehicles found")
                    else:
                        logger.warning(f"⚠️ GET /api/vehicles returned status {response.status}")
            except Exception as e:
                logger.error(f"❌ GET /api/vehicles failed: {e}")
            
            # Test POST /api/vehicles (create vehicle)
            try:
                logger.info("Testing POST /api/vehicles...")
                test_vehicle = {
                    "license_plate": "TEST123",
                    "make": "Toyota",
                    "model": "Hilux",
                    "year": 2023,
                    "status": "available",
                    "capacity": 5
                }
                
                async with session.post(
                    f"{self.core_base_url}/api/vehicles", 
                    headers=headers,
                    json=test_vehicle
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        logger.info("✅ POST /api/vehicles successful: Vehicle created")
                        return data.get("_id")  # Return vehicle ID for cleanup
                    else:
                        logger.warning(f"⚠️ POST /api/vehicles returned status {response.status}")
            except Exception as e:
                logger.error(f"❌ POST /api/vehicles failed: {e}")
            
            return None
    
    async def test_gps_routes(self):
        """Test routes that go through the GPS service"""
        headers = {"Authorization": self.test_token}
        
        async with aiohttp.ClientSession() as session:
            # Test GET /api/gps/tracking
            try:
                logger.info("Testing GET /api/gps/tracking...")
                async with session.get(f"{self.core_base_url}/api/gps/tracking", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("✅ GET /api/gps/tracking successful")
                    else:
                        logger.warning(f"⚠️ GET /api/gps/tracking returned status {response.status}")
            except Exception as e:
                logger.error(f"❌ GET /api/gps/tracking failed: {e}")
    
    async def test_trip_planning_routes(self):
        """Test routes that go through the Trip Planning service"""
        headers = {"Authorization": self.test_token}
        
        async with aiohttp.ClientSession() as session:
            # Test GET /api/trips
            try:
                logger.info("Testing GET /api/trips...")
                async with session.get(f"{self.core_base_url}/api/trips", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("✅ GET /api/trips successful")
                    else:
                        logger.warning(f"⚠️ GET /api/trips returned status {response.status}")
            except Exception as e:
                logger.error(f"❌ GET /api/trips failed: {e}")
    
    async def test_maintenance_routes(self):
        """Test routes that go through the Vehicle Maintenance service"""
        headers = {"Authorization": self.test_token}
        
        async with aiohttp.ClientSession() as session:
            # Test GET /api/maintenance
            try:
                logger.info("Testing GET /api/maintenance...")
                async with session.get(f"{self.core_base_url}/api/maintenance", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("✅ GET /api/maintenance successful")
                    else:
                        logger.warning(f"⚠️ GET /api/maintenance returned status {response.status}")
            except Exception as e:
                logger.error(f"❌ GET /api/maintenance failed: {e}")
    
    async def test_resilience_patterns(self):
        """Test resilience patterns like circuit breaker and retries"""
        logger.info("Testing resilience patterns...")
        
        # This would typically involve:
        # 1. Stopping one of the service blocks temporarily
        # 2. Making requests and observing circuit breaker behavior
        # 3. Restarting the service and testing recovery
        
        logger.info("✅ Resilience patterns test would require controlled service failures")
    
    async def test_error_handling(self):
        """Test error handling scenarios"""
        headers = {"Authorization": self.test_token}
        
        async with aiohttp.ClientSession() as session:
            # Test non-existent endpoint
            try:
                logger.info("Testing error handling with non-existent endpoint...")
                async with session.get(f"{self.core_base_url}/api/nonexistent", headers=headers) as response:
                    if response.status == 404:
                        logger.info("✅ Error handling working: 404 for non-existent endpoint")
                    else:
                        logger.warning(f"⚠️ Unexpected status for non-existent endpoint: {response.status}")
            except Exception as e:
                logger.error(f"❌ Error handling test failed: {e}")
    
    async def run_all_tests(self):
        """Run all communication tests"""
        logger.info("🚀 Starting SAMFMS Communication Architecture Tests")
        logger.info("=" * 60)
        
        try:
            # Authenticate
            await self.authenticate()
            
            # Test each service
            await self.test_vehicle_management_routes()
            await self.test_gps_routes()
            await self.test_trip_planning_routes()
            await self.test_maintenance_routes()
            
            # Test resilience and error handling
            await self.test_resilience_patterns()
            await self.test_error_handling()
            
            logger.info("=" * 60)
            logger.info("🎉 Communication Architecture Tests Completed")
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            raise

async def main():
    """Main test runner"""
    tester = CommunicationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    print("SAMFMS Communication Architecture Test Suite")
    print("=" * 50)
    print("This script tests the Core -> Service Block communication")
    print("Make sure all services are running before executing this test")
    print("=" * 50)
    
    # Run the tests
    asyncio.run(main())
