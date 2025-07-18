"""
Test configuration and fixtures for Maintenance Service tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_maintenance_record():
    """Sample maintenance record for testing"""
    return {
        "id": "test_record_123",
        "vehicle_id": "test_vehicle_456",
        "maintenance_type": "preventive",
        "status": "scheduled",
        "priority": "medium",
        "scheduled_date": datetime.utcnow() + timedelta(days=7),
        "title": "Regular Oil Change",
        "description": "Scheduled oil change and filter replacement",
        "estimated_cost": 75.0,
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_vehicle():
    """Sample vehicle data for testing"""
    return {
        "id": "test_vehicle_456",
        "make": "Toyota",
        "model": "Camry",
        "year": 2020,
        "vin": "1HGBH41JXMN109186",
        "license_plate": "ABC123",
        "mileage": 45000
    }


@pytest.fixture
def sample_vendor():
    """Sample vendor data for testing"""
    return {
        "id": "test_vendor_789",
        "name": "Quality Auto Service",
        "contact_email": "service@qualityauto.com",
        "contact_phone": "+1-555-0123",
        "specialties": ["oil_change", "brake_service", "tire_service"],
        "is_preferred": True,
        "is_active": True
    }


@pytest.fixture
def sample_license_record():
    """Sample license record for testing"""
    return {
        "id": "test_license_101",
        "entity_id": "test_vehicle_456",
        "entity_type": "vehicle",
        "license_type": "vehicle_registration",
        "license_number": "REG123456",
        "issue_date": datetime.utcnow() - timedelta(days=365),
        "expiry_date": datetime.utcnow() + timedelta(days=30),
        "issuing_authority": "Department of Motor Vehicles",
        "is_active": True
    }


@pytest.fixture
def mock_database_manager():
    """Mock database manager for testing"""
    from unittest.mock import AsyncMock, Mock
    
    mock_db = AsyncMock()
    mock_collection = AsyncMock()
    
    # Setup default behavior
    mock_db.get_collection.return_value = mock_collection
    mock_collection.find_one.return_value = None
    mock_collection.find.return_value.to_list.return_value = []
    mock_collection.insert_one.return_value = Mock(inserted_id="test_id")
    mock_collection.update_one.return_value = Mock(modified_count=1)
    mock_collection.delete_one.return_value = Mock(deleted_count=1)
    
    return mock_db


@pytest.fixture
def mock_rabbitmq_consumer():
    """Mock RabbitMQ consumer for testing"""
    from unittest.mock import AsyncMock
    
    mock_consumer = AsyncMock()
    mock_consumer.is_consuming = True
    mock_consumer.start_consuming.return_value = None
    mock_consumer.stop_consuming.return_value = None
    mock_consumer.disconnect.return_value = None
    
    return mock_consumer


# Test utilities
class MockResponse:
    """Mock HTTP response for testing"""
    
    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
    
    async def json(self):
        return self.json_data


class TestDataBuilder:
    """Builder class for creating test data"""
    
    @staticmethod
    def build_maintenance_record(**overrides) -> Dict[str, Any]:
        """Build a maintenance record with optional overrides"""
        base_record = {
            "vehicle_id": "test_vehicle_123",
            "maintenance_type": "preventive",
            "status": "scheduled",
            "priority": "medium",
            "scheduled_date": datetime.utcnow() + timedelta(days=7),
            "title": "Test Maintenance",
            "description": "Test maintenance description",
            "estimated_cost": 100.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        base_record.update(overrides)
        return base_record
    
    @staticmethod
    def build_overdue_maintenance_record(**overrides) -> Dict[str, Any]:
        """Build an overdue maintenance record"""
        overrides.setdefault("scheduled_date", datetime.utcnow() - timedelta(days=5))
        overrides.setdefault("status", "scheduled")
        return TestDataBuilder.build_maintenance_record(**overrides)
    
    @staticmethod
    def build_completed_maintenance_record(**overrides) -> Dict[str, Any]:
        """Build a completed maintenance record"""
        overrides.setdefault("status", "completed")
        overrides.setdefault("actual_completion_date", datetime.utcnow() - timedelta(days=1))
        overrides.setdefault("actual_cost", 120.0)
        overrides.setdefault("labor_cost", 80.0)
        overrides.setdefault("parts_cost", 40.0)
        return TestDataBuilder.build_maintenance_record(**overrides)


# Test constants
TEST_VEHICLE_IDS = ["test_vehicle_1", "test_vehicle_2", "test_vehicle_3"]
TEST_MAINTENANCE_TYPES = ["oil_change", "brake_check", "tire_rotation", "general_service"]
TEST_PRIORITIES = ["low", "medium", "high", "critical"]
TEST_STATUSES = ["scheduled", "in_progress", "completed", "cancelled"]
