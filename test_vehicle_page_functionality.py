#!/usr/bin/env python3
"""
Vehicle Page Functionality Test for SAMFMS
Tests the complete vehicle management flow through Core -> RabbitMQ -> Management Service
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VehiclePageTester:
    """Test suite for vehicle page functionality"""
    
    def __init__(self):
        self.core_base_url = "http://localhost:8080"  # Core service URL
        self.test_token = None
        self.created_vehicle_id = None
        
    async def authenticate(self) -> str:
        """Get authentication token"""
        try:
            # For testing purposes, use a mock token
            # In real scenario, this would authenticate with security service
            self.test_token = "Bearer test_token_admin_user"
            logger.info("✅ Authentication successful")
            return self.test_token
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise
    
    async def test_get_vehicles(self) -> bool:
        """Test GET /api/vehicles - Vehicle list functionality"""
        try:
            headers = {"Authorization": self.test_token}
            
            async with aiohttp.ClientSession() as session:
                logger.info("🔍 Testing GET /api/vehicles...")
                
                async with session.get(f"{self.core_base_url}/api/vehicles", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        vehicle_count = len(data.get('vehicles', []))
                        logger.info(f"✅ GET /api/vehicles successful: {vehicle_count} vehicles found")
                        return True
                    else:
                        logger.warning(f"⚠️ GET /api/vehicles returned status {response.status}")
                        error_text = await response.text()
                        logger.warning(f"Error details: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ GET /api/vehicles failed: {e}")
            return False
    
    async def test_create_vehicle(self) -> bool:
        """Test POST /api/vehicles - Add vehicle functionality"""
        try:
            headers = {"Authorization": self.test_token}
            
            test_vehicle = {
                "make": "Toyota",
                "model": "Hilux Test",
                "year": 2023,
                "license_plate": f"TEST{datetime.now().strftime('%M%S')}",
                "vin": f"TEST123456789{datetime.now().strftime('%M%S')}",
                "color": "White",
                "fuel_type": "Diesel",
                "mileage": 0,
                "status": "available",
                "department": "Fleet Management",
                "fuel_efficiency": "8.5L/100km"
            }
            
            async with aiohttp.ClientSession() as session:
                logger.info("🔍 Testing POST /api/vehicles...")
                
                async with session.post(
                    f"{self.core_base_url}/api/vehicles", 
                    headers=headers,
                    json=test_vehicle
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        self.created_vehicle_id = data.get("_id")
                        logger.info(f"✅ POST /api/vehicles successful: Vehicle created with ID {self.created_vehicle_id}")
                        return True
                    else:
                        logger.warning(f"⚠️ POST /api/vehicles returned status {response.status}")
                        error_text = await response.text()
                        logger.warning(f"Error details: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ POST /api/vehicles failed: {e}")
            return False
    
    async def test_get_single_vehicle(self) -> bool:
        """Test GET /api/vehicles/{id} - Vehicle details functionality"""
        if not self.created_vehicle_id:
            logger.warning("⚠️ No vehicle ID available for single vehicle test")
            return False
            
        try:
            headers = {"Authorization": self.test_token}
            
            async with aiohttp.ClientSession() as session:
                logger.info(f"🔍 Testing GET /api/vehicles/{self.created_vehicle_id}...")
                
                async with session.get(
                    f"{self.core_base_url}/api/vehicles/{self.created_vehicle_id}", 
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ GET /api/vehicles/{self.created_vehicle_id} successful: Retrieved vehicle details")
                        return True
                    else:
                        logger.warning(f"⚠️ GET /api/vehicles/{self.created_vehicle_id} returned status {response.status}")
                        error_text = await response.text()
                        logger.warning(f"Error details: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ GET /api/vehicles/{self.created_vehicle_id} failed: {e}")
            return False
    
    async def test_update_vehicle(self) -> bool:
        """Test PUT /api/vehicles/{id} - Edit vehicle functionality"""
        if not self.created_vehicle_id:
            logger.warning("⚠️ No vehicle ID available for update test")
            return False
            
        try:
            headers = {"Authorization": self.test_token}
            
            update_data = {
                "mileage": 1500,
                "status": "in_use",
                "notes": "Updated via API test"
            }
            
            async with aiohttp.ClientSession() as session:
                logger.info(f"🔍 Testing PUT /api/vehicles/{self.created_vehicle_id}...")
                
                async with session.put(
                    f"{self.core_base_url}/api/vehicles/{self.created_vehicle_id}", 
                    headers=headers,
                    json=update_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ PUT /api/vehicles/{self.created_vehicle_id} successful: Vehicle updated")
                        return True
                    else:
                        logger.warning(f"⚠️ PUT /api/vehicles/{self.created_vehicle_id} returned status {response.status}")
                        error_text = await response.text()
                        logger.warning(f"Error details: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ PUT /api/vehicles/{self.created_vehicle_id} failed: {e}")
            return False
    
    async def test_search_vehicles(self) -> bool:
        """Test GET /api/vehicles/search/{query} - Vehicle search functionality"""
        try:
            headers = {"Authorization": self.test_token}
            search_query = "Toyota"
            
            async with aiohttp.ClientSession() as session:
                logger.info(f"🔍 Testing GET /api/vehicles/search/{search_query}...")
                
                async with session.get(
                    f"{self.core_base_url}/api/vehicles/search/{search_query}", 
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result_count = len(data.get('vehicles', []))
                        logger.info(f"✅ GET /api/vehicles/search/{search_query} successful: {result_count} vehicles found")
                        return True
                    else:
                        logger.warning(f"⚠️ GET /api/vehicles/search/{search_query} returned status {response.status}")
                        error_text = await response.text()
                        logger.warning(f"Error details: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ GET /api/vehicles/search failed: {e}")
            return False
    
    async def test_delete_vehicle(self) -> bool:
        """Test DELETE /api/vehicles/{id} - Delete vehicle functionality"""
        if not self.created_vehicle_id:
            logger.warning("⚠️ No vehicle ID available for delete test")
            return False
            
        try:
            headers = {"Authorization": self.test_token}
            
            async with aiohttp.ClientSession() as session:
                logger.info(f"🔍 Testing DELETE /api/vehicles/{self.created_vehicle_id}...")
                
                async with session.delete(
                    f"{self.core_base_url}/api/vehicles/{self.created_vehicle_id}", 
                    headers=headers
                ) as response:
                    if response.status in [200, 204]:
                        logger.info(f"✅ DELETE /api/vehicles/{self.created_vehicle_id} successful: Vehicle deleted")
                        return True
                    else:
                        logger.warning(f"⚠️ DELETE /api/vehicles/{self.created_vehicle_id} returned status {response.status}")
                        error_text = await response.text()
                        logger.warning(f"Error details: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ DELETE /api/vehicles/{self.created_vehicle_id} failed: {e}")
            return False
    
    async def test_vehicle_assignments(self) -> bool:
        """Test vehicle assignment endpoints"""
        try:
            headers = {"Authorization": self.test_token}
            
            async with aiohttp.ClientSession() as session:
                logger.info("🔍 Testing GET /api/vehicle-assignments...")
                
                async with session.get(f"{self.core_base_url}/api/vehicle-assignments", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        assignment_count = len(data.get('assignments', []))
                        logger.info(f"✅ GET /api/vehicle-assignments successful: {assignment_count} assignments found")
                        return True
                    else:
                        logger.warning(f"⚠️ GET /api/vehicle-assignments returned status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ GET /api/vehicle-assignments failed: {e}")
            return False
    
    async def test_vehicle_usage(self) -> bool:
        """Test vehicle usage endpoints"""
        try:
            headers = {"Authorization": self.test_token}
            
            async with aiohttp.ClientSession() as session:
                logger.info("🔍 Testing GET /api/vehicle-usage...")
                
                async with session.get(f"{self.core_base_url}/api/vehicle-usage", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        usage_count = len(data.get('usage_records', []))
                        logger.info(f"✅ GET /api/vehicle-usage successful: {usage_count} usage records found")
                        return True
                    else:
                        logger.warning(f"⚠️ GET /api/vehicle-usage returned status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ GET /api/vehicle-usage failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run complete vehicle page functionality test suite"""
        logger.info("🚀 Starting Vehicle Page Functionality Tests")
        logger.info("=" * 70)
        
        test_results = []
        
        try:
            # Authenticate
            await self.authenticate()
            
            # Test vehicle CRUD operations
            test_results.append(("GET Vehicles", await self.test_get_vehicles()))
            test_results.append(("CREATE Vehicle", await self.test_create_vehicle()))
            test_results.append(("GET Single Vehicle", await self.test_get_single_vehicle()))
            test_results.append(("UPDATE Vehicle", await self.test_update_vehicle()))
            test_results.append(("SEARCH Vehicles", await self.test_search_vehicles()))
            test_results.append(("DELETE Vehicle", await self.test_delete_vehicle()))
            
            # Test related endpoints
            test_results.append(("Vehicle Assignments", await self.test_vehicle_assignments()))
            test_results.append(("Vehicle Usage", await self.test_vehicle_usage()))
            
            # Summary
            logger.info("=" * 70)
            logger.info("📊 Test Results Summary:")
            passed_tests = 0
            total_tests = len(test_results)
            
            for test_name, result in test_results:
                status = "✅ PASSED" if result else "❌ FAILED"
                logger.info(f"  {test_name:<25} {status}")
                if result:
                    passed_tests += 1
            
            logger.info("=" * 70)
            logger.info(f"🎯 Tests Passed: {passed_tests}/{total_tests}")
            
            if passed_tests == total_tests:
                logger.info("🎉 All Vehicle Page Functionality Tests PASSED!")
                logger.info("✅ Frontend -> Core -> RabbitMQ -> Management Service communication is working!")
            else:
                logger.warning(f"⚠️ {total_tests - passed_tests} tests failed. Check the logs above for details.")
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            raise

async def main():
    """Main test runner"""
    tester = VehiclePageTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    print("SAMFMS Vehicle Page Functionality Test Suite")
    print("=" * 60)
    print("This script tests the complete vehicle management functionality")
    print("including frontend API -> Core -> RabbitMQ -> Management Service")
    print("Make sure all services are running before executing this test")
    print("=" * 60)
    
    # Run the tests
    asyncio.run(main())
