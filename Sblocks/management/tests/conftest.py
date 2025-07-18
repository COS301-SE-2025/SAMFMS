"""
Test configuration and shared fixtures for Management Service tests
"""
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Generator, AsyncGenerator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from bson import ObjectId

# Mock external dependencies before importing our modules
sys.modules.setdefault("motor", MagicMock())
sys.modules.setdefault("motor.motor_asyncio", MagicMock())
sys.modules.setdefault("pika", MagicMock())
sys.modules.setdefault("aio_pika", MagicMock())
sys.modules.setdefault("redis", MagicMock())


@pytest_asyncio.fixture
def mock_mongodb():
    """Mock MongoDB client and collections"""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    # Configure the mock chain
    mock_client.samfms = mock_db
    mock_db.vehicles = mock_collection
    mock_db.drivers = mock_collection
    mock_db.assignments = mock_collection
    mock_db.usage_logs = mock_collection
    
    # Mock collection methods
    mock_collection.find_one = AsyncMock()
    mock_collection.find = MagicMock(return_value=create_mock_cursor([]))
    mock_collection.insert_one = AsyncMock()
    mock_collection.update_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    mock_collection.count_documents = AsyncMock()
    
    # Mock the update result
    mock_update_result = MagicMock()
    mock_update_result.modified_count = 1
    mock_update_result.matched_count = 1
    mock_collection.update_one.return_value = mock_update_result
    
    # Mock the insert result
    mock_insert_result = MagicMock()
    mock_insert_result.inserted_id = ObjectId()
    mock_collection.insert_one.return_value = mock_insert_result
    
    # Mock the delete result
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1
    mock_collection.delete_one.return_value = mock_delete_result
    
    # Mock collection access by name
    mock_db.__getitem__ = lambda self, key: mock_collection
    
    # Mock the entire database manager
    mock_db_manager = MagicMock()
    mock_db_manager.db = mock_db
    mock_db_manager._db = mock_db  # Mock the private attribute to avoid "not connected" errors
    
    # Patch both the instance and the property
    with patch('repositories.database.db_manager', mock_db_manager), \
         patch('repositories.base.db_manager', mock_db_manager):
        yield mock_db


@pytest_asyncio.fixture
def mock_rabbitmq():
    """Mock RabbitMQ connection and channels"""
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()
    mock_queue = AsyncMock()
    
    mock_connection.channel.return_value = mock_channel
    mock_channel.declare_exchange.return_value = mock_exchange
    mock_channel.declare_queue.return_value = mock_queue
    
    with patch('aio_pika.connect_robust', return_value=mock_connection):
        yield mock_connection


@pytest_asyncio.fixture
def mock_redis():
    """Mock Redis client"""
    mock_redis = AsyncMock()
    
    with patch('redis.asyncio.Redis', return_value=mock_redis):
        yield mock_redis


@pytest_asyncio.fixture
def sample_vehicle_data() -> Dict[str, Any]:
    """Sample vehicle data for testing"""
    return {
        "_id": ObjectId(),
        "registration_number": "TEST123GP",
        "license_plate": "TEST123GP",
        "make": "Toyota",
        "model": "Hilux",
        "year": 2023,
        "type": "pickup",
        "department": "Security",
        "capacity": 5,
        "fuel_type": "diesel",
        "color": "White",
        "vin": "1GTPUEE18J8123456",
        "status": "available",
        "mileage": 15000,
        "created_by": "test_user",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }


@pytest_asyncio.fixture
def sample_driver_data() -> Dict[str, Any]:
    """Sample driver data for testing"""
    return {
        "_id": ObjectId(),
        "employee_id": "EMP001",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@company.com",
        "phone": "+27123456789",
        "license_number": "1234567890",
        "license_class": ["B", "EB"],
        "license_expiry": datetime(2025, 12, 31),
        "status": "active",
        "department": "Security",
        "hire_date": datetime(2020, 1, 15),
        "current_vehicle_id": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }


@pytest_asyncio.fixture
def sample_assignment_data() -> Dict[str, Any]:
    """Sample assignment data for testing"""
    return {
        "_id": ObjectId(),
        "vehicle_id": str(ObjectId()),
        "driver_id": str(ObjectId()),
        "assignment_type": "temporary",
        "status": "active",
        "start_date": datetime.now(timezone.utc),
        "end_date": None,
        "purpose": "Security patrol",
        "route": {"start": "Building A", "end": "Building B"},
        "notes": "Regular patrol duty",
        "created_by": "supervisor",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }


@pytest.fixture
def sample_vehicle_create_request() -> Dict[str, Any]:
    """Sample vehicle creation request data"""
    return {
        "make": "Toyota",
        "model": "Hilux",
        "year": 2023,
        "license_plate": "NEW123GP",
        "vin": "1GTPUEE18J8654321",
        "color": "Blue",
        "fuel_type": "diesel",
        "mileage": 0,
        "type": "pickup",
        "department": "Operations",
        "capacity": 5,
        "status": "available"
    }


@pytest.fixture
def mock_event_publisher():
    """Mock event publisher"""
    with patch('events.publisher.event_publisher') as mock_publisher:
        mock_publisher.publish_vehicle_created = AsyncMock()
        mock_publisher.publish_vehicle_updated = AsyncMock()
        mock_publisher.publish_vehicle_deleted = AsyncMock()
        yield mock_publisher


class MockAsyncIterator:
    """Mock async iterator for MongoDB cursor"""
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item

    async def to_list(self, length=None):
        return self.items[:length] if length else self.items


@pytest_asyncio.fixture
def app() -> FastAPI:
    """FastAPI test app"""
    from main import app
    return app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client"""
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        yield ac


def create_mock_cursor(items):
    """Helper to create mock MongoDB cursor"""
    mock_cursor = MagicMock()
    # Set up the async iterator properly
    async_iter = MockAsyncIterator(items)
    mock_cursor.__aiter__ = MagicMock(return_value=async_iter)
    mock_cursor.to_list = AsyncMock(return_value=items)
    mock_cursor.skip = MagicMock(return_value=mock_cursor)
    mock_cursor.limit = MagicMock(return_value=mock_cursor)
    mock_cursor.sort = MagicMock(return_value=mock_cursor)
    return mock_cursor
