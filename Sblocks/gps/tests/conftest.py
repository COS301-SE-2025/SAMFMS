"""
Test configuration for GPS service
"""
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from repositories.database import DatabaseManager


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Create test database fixture"""
    # Use test database
    db_manager = DatabaseManager()
    db_manager.database_name = "test_samfms_gps"
    
    await db_manager.connect()
    
    yield db_manager
    
    # Cleanup
    await db_manager._client.drop_database("test_samfms_gps")
    await db_manager.disconnect()


@pytest.fixture
async def sample_vehicle_location():
    """Sample vehicle location data"""
    return {
        "vehicle_id": "test_vehicle_001",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "altitude": 10.0,
        "speed": 35.0,
        "heading": 90.0,
        "accuracy": 5.0
    }


@pytest.fixture
async def sample_geofence():
    """Sample geofence data"""
    return {
        "name": "Test Geofence",
        "description": "A test geofence",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-74.010, 40.710],
                [-74.000, 40.710],
                [-74.000, 40.720],
                [-74.010, 40.720],
                [-74.010, 40.710]
            ]]
        },
        "geofence_type": "polygon",
        "is_active": True,
        "created_by": "test_user"
    }


@pytest.fixture
async def sample_place():
    """Sample place data"""
    return {
        "user_id": "test_user",
        "name": "Test Place",
        "description": "A test place",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "address": "123 Test St, New York, NY",
        "place_type": "custom"
    }
