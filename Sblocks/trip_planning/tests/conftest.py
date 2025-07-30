import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock
import os
import sys

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database.database import TripPlanningDatabase
from config.settings import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Create a test database instance"""
    test_settings = settings.copy()
    test_settings.DATABASE_NAME = "test_trip_planning_db"
    
    client = AsyncIOMotorClient(test_settings.MONGODB_URL)
    db = client[test_settings.DATABASE_NAME]
    
    # Create test database instance
    test_database = TripPlanningDatabase()
    test_database.db = db
    
    yield test_database
    
    # Cleanup: Drop test database
    await client.drop_database(test_settings.DATABASE_NAME)
    client.close()


@pytest.fixture
async def test_client():
    """Create a test HTTP client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_rabbitmq_publisher():
    """Mock RabbitMQ publisher"""
    publisher = AsyncMock()
    publisher.publish_message = AsyncMock()
    publisher.publish_trip_event = AsyncMock()
    publisher.publish_driver_assignment_event = AsyncMock()
    publisher.publish_notification_event = AsyncMock()
    return publisher


@pytest.fixture
def mock_rabbitmq_consumer():
    """Mock RabbitMQ consumer"""
    consumer = AsyncMock()
    consumer.start_consuming = AsyncMock()
    consumer.stop_consuming = AsyncMock()
    consumer.handle_trip_request = AsyncMock()
    consumer.handle_driver_assignment_request = AsyncMock()
    return consumer


@pytest.fixture
def sample_trip_data():
    """Sample trip data for testing"""
    return {
        "trip_id": "test_trip_001",
        "user_id": "test_user_001",
        "vehicle_id": "test_vehicle_001",
        "origin": {
            "lat": 40.7128,
            "lng": -74.0060,
            "address": "New York, NY"
        },
        "destination": {
            "lat": 34.0522,
            "lng": -118.2437,
            "address": "Los Angeles, CA"
        },
        "waypoints": [],
        "constraints": {
            "avoid_tolls": True,
            "avoid_highways": False,
            "max_duration": 24.0
        },
        "preferences": {
            "vehicle_type": "sedan",
            "fuel_efficiency": True
        },
        "status": "planned",
        "estimated_duration": 40.5,
        "estimated_distance": 2789.6
    }


@pytest.fixture
def sample_driver_data():
    """Sample driver data for testing"""
    return {
        "driver_id": "test_driver_001",
        "user_id": "test_user_002",
        "license_number": "DL123456789",
        "license_expiry": "2025-12-31",
        "vehicle_types": ["sedan", "suv"],
        "max_driving_hours": 10,
        "status": "available",
        "current_location": {
            "lat": 40.7128,
            "lng": -74.0060
        },
        "rating": 4.8,
        "total_trips": 150
    }


@pytest.fixture
def sample_driver_assignment_data():
    """Sample driver assignment data for testing"""
    return {
        "assignment_id": "test_assignment_001",
        "trip_id": "test_trip_001",
        "driver_id": "test_driver_001",
        "assigned_at": "2024-01-15T10:00:00Z",
        "status": "assigned",
        "estimated_pickup_time": "2024-01-15T11:00:00Z"
    }


@pytest.fixture
def sample_notification_data():
    """Sample notification data for testing"""
    return {
        "notification_id": "test_notification_001",
        "user_id": "test_user_001",
        "type": "trip_confirmation",
        "title": "Trip Confirmed",
        "message": "Your trip has been confirmed and a driver has been assigned.",
        "data": {
            "trip_id": "test_trip_001",
            "driver_id": "test_driver_001"
        },
        "channels": ["push", "email"],
        "priority": "high",
        "status": "pending"
    }


@pytest.fixture
def mock_external_services():
    """Mock external service dependencies"""
    services = MagicMock()
    
    # Mock GPS service
    services.gps_service = AsyncMock()
    services.gps_service.calculate_route = AsyncMock(return_value={
        "distance": 2789.6,
        "duration": 40.5,
        "route": []
    })
    services.gps_service.get_current_location = AsyncMock(return_value={
        "lat": 40.7128,
        "lng": -74.0060
    })
    
    # Mock User service
    services.user_service = AsyncMock()
    services.user_service.get_user = AsyncMock(return_value={
        "user_id": "test_user_001",
        "name": "Test User",
        "email": "test@example.com"
    })
    
    # Mock Vehicle service
    services.vehicle_service = AsyncMock()
    services.vehicle_service.get_vehicle = AsyncMock(return_value={
        "vehicle_id": "test_vehicle_001",
        "type": "sedan",
        "status": "available"
    })
    
    return services


class DatabaseTestMixin:
    """Mixin class for database testing utilities"""
    
    async def create_test_trip(self, db, trip_data):
        """Create a test trip in the database"""
        result = await db.trips.insert_one(trip_data)
        return str(result.inserted_id)
    
    async def create_test_driver(self, db, driver_data):
        """Create a test driver in the database"""
        result = await db.drivers.insert_one(driver_data)
        return str(result.inserted_id)
    
    async def create_test_assignment(self, db, assignment_data):
        """Create a test driver assignment in the database"""
        result = await db.driver_assignments.insert_one(assignment_data)
        return str(result.inserted_id)
    
    async def cleanup_test_data(self, db, collections):
        """Clean up test data from specified collections"""
        for collection_name in collections:
            collection = getattr(db, collection_name)
            await collection.delete_many({})


class APITestMixin:
    """Mixin class for API testing utilities"""
    
    async def make_authenticated_request(self, client, method, url, **kwargs):
        """Make an authenticated API request"""
        # Add authentication headers if needed
        headers = kwargs.get('headers', {})
        headers['Authorization'] = 'Bearer test_token'
        kwargs['headers'] = headers
        
        response = await getattr(client, method.lower())(url, **kwargs)
        return response
    
    def assert_success_response(self, response, expected_status=200):
        """Assert that response is successful"""
        assert response.status_code == expected_status
        data = response.json()
        assert data['success'] is True
        return data
    
    def assert_error_response(self, response, expected_status=400):
        """Assert that response contains an error"""
        assert response.status_code == expected_status
        data = response.json()
        assert data['success'] is False
        assert 'error' in data
        return data
