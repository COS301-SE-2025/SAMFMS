#!/usr/bin/env python3
"""
Comprehensive Test Suite for SAMFMS Maintenance Service
Tests all functionality end-to-end
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys
import os

# Configuration
BASE_URL = "http://localhost:21007"
CORE_URL = "http://localhost:21004"
TEST_VEHICLE_ID = "test_vehicle_001"
TEST_USER_TOKEN = "your_jwt_token_here"  # Replace with actual token

# Test data
MAINTENANCE_RECORD_DATA = {
    "vehicle_id": TEST_VEHICLE_ID,
    "maintenance_type": "preventive",
    "title": "Test Oil Change",
    "description": "Test maintenance record for oil change",
    "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z",
    "priority": "medium",
    "estimated_cost": 250.00,
    "estimated_duration": 2,
    "assigned_technician": "test_tech_001",
    "technician_name": "Test Technician",
    "mileage_at_service": 50000
}

LICENSE_RECORD_DATA = {
    "entity_id": TEST_VEHICLE_ID,
    "entity_type": "vehicle",
    "license_type": "vehicle_registration",
    "license_number": "TEST-123-456",
    "issue_date": "2025-01-01T00:00:00Z",
    "expiry_date": "2026-01-01T00:00:00Z",
    "issuing_authority": "Test Department of Transport",
    "cost": 500.00
}

class MaintenanceServiceTester:
    def __init__(self):
        self.session = None
        self.headers = {
            "Authorization": f"Bearer {TEST_USER_TOKEN}",
            "Content-Type": "application/json"
        }
        self.test_results = []
        self.created_records = []
        
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession()
        print("🔧 Starting Maintenance Service Tests")
        print("=" * 50)
        
    async def cleanup(self):
        """Cleanup test data and session"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created maintenance records
        for record_id in self.created_records:
            try:
                await self.delete_maintenance_record(record_id)
                print(f"✅ Deleted maintenance record: {record_id}")
            except Exception as e:
                print(f"⚠️ Failed to delete record {record_id}: {e}")
                
        if self.session:
            await self.session.close()
            
    async def run_test(self, test_name: str, test_func, *args, **kwargs):
        """Run individual test with error handling"""
        try:
            print(f"\n🧪 Running: {test_name}")
            result = await test_func(*args, **kwargs)
            print(f"✅ PASSED: {test_name}")
            self.test_results.append({"test": test_name, "status": "PASSED", "result": result})
            return result
        except Exception as e:
            print(f"❌ FAILED: {test_name} - {str(e)}")
            self.test_results.append({"test": test_name, "status": "FAILED", "error": str(e)})
            return None
            
    # Health Check Tests
    async def test_service_health(self):
        """Test service health endpoint"""
        async with self.session.get(f"{BASE_URL}/health") as response:
            assert response.status == 200
            data = await response.json()
            assert data["service"] == "maintenance"
            assert data["status"] in ["healthy", "degraded"]
            return data
            
    async def test_service_metrics(self):
        """Test service metrics endpoint"""
        async with self.session.get(f"{BASE_URL}/metrics") as response:
            assert response.status == 200
            data = await response.json()
            assert "uptime_seconds" in data
            return data
            
    # Maintenance Records Tests
    async def test_create_maintenance_record(self):
        """Test creating a maintenance record"""
        async with self.session.post(
            f"{BASE_URL}/maintenance/records/",
            headers=self.headers,
            json=MAINTENANCE_RECORD_DATA
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            assert "data" in data
            record_id = data["data"]["id"]
            self.created_records.append(record_id)
            return data["data"]
            
    async def test_get_maintenance_records(self):
        """Test retrieving maintenance records"""
        async with self.session.get(
            f"{BASE_URL}/maintenance/records/",
            headers=self.headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            assert "data" in data
            assert isinstance(data["data"], list)
            return data
            
    async def test_get_maintenance_record_by_id(self, record_id: str):
        """Test retrieving specific maintenance record"""
        async with self.session.get(
            f"{BASE_URL}/maintenance/records/{record_id}",
            headers=self.headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            assert data["data"]["id"] == record_id
            return data["data"]
            
    async def test_update_maintenance_record(self, record_id: str):
        """Test updating a maintenance record"""
        update_data = {
            "status": "in_progress",
            "actual_start_date": datetime.utcnow().isoformat() + "Z",
            "notes": "Started maintenance work"
        }
        
        async with self.session.put(
            f"{BASE_URL}/maintenance/records/{record_id}",
            headers=self.headers,
            json=update_data
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "in_progress"
            return data["data"]
            
    async def delete_maintenance_record(self, record_id: str):
        """Delete a maintenance record"""
        async with self.session.delete(
            f"{BASE_URL}/maintenance/records/{record_id}",
            headers=self.headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            return data
            
    async def test_get_vehicle_maintenance_records(self):
        """Test retrieving maintenance records for a vehicle"""
        async with self.session.get(
            f"{BASE_URL}/maintenance/records/vehicle/{TEST_VEHICLE_ID}",
            headers=self.headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            return data
            
    async def test_get_overdue_maintenance(self):
        """Test retrieving overdue maintenance"""
        async with self.session.get(
            f"{BASE_URL}/maintenance/records/status/overdue",
            headers=self.headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            return data
            
    async def test_get_upcoming_maintenance(self):
        """Test retrieving upcoming maintenance"""
        async with self.session.get(
            f"{BASE_URL}/maintenance/records/status/upcoming?days=30",
            headers=self.headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            return data
            
    # License Management Tests
    async def test_create_license_record(self):
        """Test creating a license record"""
        async with self.session.post(
            f"{BASE_URL}/maintenance/licenses/",
            headers=self.headers,
            json=LICENSE_RECORD_DATA
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            return data["data"]
            
    async def test_get_license_records(self):
        """Test retrieving license records"""
        async with self.session.get(
            f"{BASE_URL}/maintenance/licenses/",
            headers=self.headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            return data
            
    # Analytics Tests
    async def test_maintenance_dashboard(self):
        """Test maintenance dashboard analytics"""
        async with self.session.get(
            f"{BASE_URL}/maintenance/analytics/dashboard",
            headers=self.headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            assert "data" in data
            return data["data"]
            
    async def test_cost_analytics(self):
        """Test cost analytics"""
        async with self.session.get(
            f"{BASE_URL}/maintenance/analytics/costs",
            headers=self.headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            return data["data"]
            
    async def test_maintenance_trends(self):
        """Test maintenance trends"""
        async with self.session.get(
            f"{BASE_URL}/maintenance/analytics/trends?days=90",
            headers=self.headers
        ) as response:
            assert response.status == 200
            data = await response.json()
            assert data["success"] is True
            return data["data"]
            
    # Core Service Integration Tests
    async def test_core_service_proxy(self):
        """Test Core service proxy integration"""
        async with self.session.get(
            f"{CORE_URL}/api/maintenance",
            headers=self.headers
        ) as response:
            # Should work through Core's proxy
            assert response.status == 200
            data = await response.json()
            return data
            
    # Load and Performance Tests
    async def test_concurrent_requests(self):
        """Test concurrent request handling"""
        tasks = []
        for i in range(10):
            task = self.session.get(
                f"{BASE_URL}/maintenance/records/",
                headers=self.headers
            )
            tasks.append(task)
            
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = 0
        for response in responses:
            if hasattr(response, 'status') and response.status == 200:
                success_count += 1
                response.close()
                
        assert success_count >= 8  # Allow for some failures
        return {"total_requests": 10, "successful": success_count}
        
    # Data Validation Tests
    async def test_invalid_maintenance_data(self):
        """Test validation with invalid data"""
        invalid_data = {
            "vehicle_id": "",  # Invalid: empty
            "maintenance_type": "invalid_type",  # Invalid: not in enum
            "scheduled_date": "invalid_date",  # Invalid: bad format
            "estimated_cost": -100  # Invalid: negative cost
        }
        
        async with self.session.post(
            f"{BASE_URL}/maintenance/records/",
            headers=self.headers,
            json=invalid_data
        ) as response:
            assert response.status == 422  # Validation error
            data = await response.json()
            assert data["success"] is False
            return data
            
    async def run_all_tests(self):
        """Run the complete test suite"""
        await self.setup()
        
        try:
            # Basic health tests
            await self.run_test("Service Health Check", self.test_service_health)
            await self.run_test("Service Metrics", self.test_service_metrics)
            
            # Maintenance record CRUD tests
            record = await self.run_test("Create Maintenance Record", self.test_create_maintenance_record)
            if record:
                record_id = record["id"]
                await self.run_test("Get Maintenance Record by ID", self.test_get_maintenance_record_by_id, record_id)
                await self.run_test("Update Maintenance Record", self.test_update_maintenance_record, record_id)
                
            await self.run_test("Get All Maintenance Records", self.test_get_maintenance_records)
            await self.run_test("Get Vehicle Maintenance Records", self.test_get_vehicle_maintenance_records)
            await self.run_test("Get Overdue Maintenance", self.test_get_overdue_maintenance)
            await self.run_test("Get Upcoming Maintenance", self.test_get_upcoming_maintenance)
            
            # License management tests
            await self.run_test("Create License Record", self.test_create_license_record)
            await self.run_test("Get License Records", self.test_get_license_records)
            
            # Analytics tests
            await self.run_test("Maintenance Dashboard", self.test_maintenance_dashboard)
            await self.run_test("Cost Analytics", self.test_cost_analytics)
            await self.run_test("Maintenance Trends", self.test_maintenance_trends)
            
            # Integration tests
            await self.run_test("Core Service Proxy", self.test_core_service_proxy)
            
            # Performance tests
            await self.run_test("Concurrent Requests", self.test_concurrent_requests)
            
            # Validation tests
            await self.run_test("Invalid Data Validation", self.test_invalid_maintenance_data)
            
        finally:
            await self.cleanup()
            
        # Print test summary
        self.print_test_summary()
        
    def print_test_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 50)
        print("🏁 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASSED")
        failed = sum(1 for result in self.test_results if result["status"] == "FAILED")
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAILED":
                    print(f"  - {result['test']}: {result['error']}")
                    
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"  {status_icon} {result['test']}")

async def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Maintenance Service Test Suite")
        print("Usage: python test_maintenance_service.py")
        print("Make sure the maintenance service is running on localhost:21007")
        return
        
    tester = MaintenanceServiceTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
