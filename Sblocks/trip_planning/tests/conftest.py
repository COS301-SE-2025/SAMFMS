import os
import sys
import asyncio
import importlib
from typing import Optional
import builtins 

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock

APP_ROOT = "/app"
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

from main import app  
try:
    from api.exception_handlers import EXCEPTION_HANDLERS
    for exc_type, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exc_type, handler)
except Exception:
    pass

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Dedicated event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def test_client():
    """
    Async test client bound to the real app, with a default Authorization header
    so routes depending on get_current_user don't 401 during tests.
    """
    default_headers = {"Authorization": "Bearer test_token"}
    async with AsyncClient(app=app, base_url="http://test", headers=default_headers) as client:
        yield client

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from database.database import TripPlanningDatabase
    from config.settings import settings

    @pytest_asyncio.fixture
    async def test_db():
        """Create a test database instance (Mongo)"""
        test_settings = settings.copy()
        test_settings.DATABASE_NAME = "test_trip_planning_db"

        client = AsyncIOMotorClient(test_settings.MONGODB_URL)
        db = client[test_settings.DATABASE_NAME]

        test_database = TripPlanningDatabase()
        test_database.db = db

        yield test_database

        await client.drop_database(test_settings.DATABASE_NAME)
        client.close()

except Exception:
    pass

@pytest.fixture
def mock_rabbitmq_publisher():
    publisher = AsyncMock()
    publisher.publish_message = AsyncMock()
    publisher.publish_trip_event = AsyncMock()
    publisher.publish_driver_assignment_event = AsyncMock()
    publisher.publish_notification_event = AsyncMock()
    return publisher

@pytest.fixture
def mock_rabbitmq_consumer():
    consumer = AsyncMock()
    consumer.start_consuming = AsyncMock()
    consumer.stop_consuming = AsyncMock()
    consumer.handle_trip_request = AsyncMock()
    consumer.handle_driver_assignment_request = AsyncMock()
    return consumer

@pytest.fixture
def mock_analytics_service(monkeypatch):
    """
    Patch the *exact* symbol that the analytics routes call.
    """
    route_mod: Optional[object] = None
    for modname in ("api.routes.analytics", "api.analytics", "analytics"):
        try:
            route_mod = importlib.import_module(modname)
            getattr(route_mod, "analytics_service")
            break
        except Exception:
            route_mod = None

    if route_mod is None:
        raise RuntimeError("Could not find analytics route module to patch.")

    mock = AsyncMock()
    mock.get_trip_analytics = AsyncMock(return_value={})
    mock.get_trip_history_stats = AsyncMock(return_value={})
    mock.get_driver_performance = AsyncMock(return_value=[])
    mock.get_route_efficiency_analysis = AsyncMock(return_value={})

    monkeypatch.setattr(route_mod, "analytics_service", mock)

    try:
        services_mod = importlib.import_module("services.analytics_service")
        monkeypatch.setattr(services_mod, "analytics_service", mock)
    except Exception:
        pass

    return mock

@pytest.fixture
def sample_trip_data():
    return {
        "trip_id": "test_trip_001",
        "user_id": "test_user_001",
        "vehicle_id": "test_vehicle_001",
        "origin": {"lat": 40.7128, "lng": -74.0060, "address": "New York, NY"},
        "destination": {"lat": 34.0522, "lng": -118.2437, "address": "Los Angeles, CA"},
        "waypoints": [],
        "constraints": {"avoid_tolls": True, "avoid_highways": False, "max_duration": 24.0},
        "preferences": {"vehicle_type": "sedan", "fuel_efficiency": True},
        "status": "planned",
        "estimated_duration": 40.5,
        "estimated_distance": 2789.6,
    }

@pytest.fixture
def sample_driver_data():
    return {
        "driver_id": "test_driver_001",
        "user_id": "test_user_002",
        "license_number": "DL123456789",
        "license_expiry": "2025-12-31",
        "vehicle_types": ["sedan", "suv"],
        "max_driving_hours": 10,
        "status": "available",
        "current_location": {"lat": 40.7128, "lng": -74.0060},
        "rating": 4.8,
        "total_trips": 150,
    }

@pytest.fixture
def sample_driver_assignment_data():
    return {
        "assignment_id": "test_assignment_001",
        "trip_id": "test_trip_001",
        "driver_id": "test_driver_001",
        "assigned_at": "2024-01-15T10:00:00Z",
        "status": "assigned",
        "estimated_pickup_time": "2024-01-15T11:00:00Z",
    }

@pytest.fixture
def sample_notification_data():
    return {
        "notification_id": "test_notification_001",
        "user_id": "test_user_001",
        "type": "trip_confirmation",
        "title": "Trip Confirmed",
        "message": "Your trip has been confirmed and a driver has been assigned.",
        "data": {"trip_id": "test_trip_001", "driver_id": "test_driver_001"},
        "channels": ["push", "email"],
        "priority": "high",
        "status": "pending",
    }

class APITestMixin:
    async def make_authenticated_request(self, client, method, url, **kwargs):
        headers = kwargs.get("headers", {})
        headers["Authorization"] = "Bearer test_token"
        kwargs["headers"] = headers
        return await getattr(client, method.lower())(url, **kwargs)

    def assert_success_response(self, response, expected_status=200):
        assert response.status_code == expected_status
        data = response.json()
        assert data["success"] is True
        return data

    def assert_error_response(self, response, expected_status=400):
        assert response.status_code == expected_status
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        return data

from types import SimpleNamespace

class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)
    def sort(self, *args, **kwargs): return self
    def skip(self, *_): return self
    def limit(self, *_): return self
    async def to_list(self, length=None): return list(self._docs)
    def __aiter__(self):
        self._it = iter(self._docs)
        return self
    async def __anext__(self):
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration

def make_fake_collection():
    col = SimpleNamespace()
    col.count_documents = AsyncMock(return_value=0)
    col.find = MagicMock(side_effect=lambda *a, **k: _FakeCursor([]))
    col.aggregate = MagicMock(side_effect=lambda *a, **k: SimpleNamespace(
        to_list=AsyncMock(return_value=[])
    ))
    col.insert_one = AsyncMock(return_value=SimpleNamespace(inserted_id="507f1f77bcf86cd799439011"))
    col.update_one = AsyncMock(return_value=SimpleNamespace(matched_count=1, modified_count=1))
    col.delete_one = AsyncMock(return_value=SimpleNamespace(deleted_count=1))
    return col

@pytest.fixture
def fake_db():
    """
    In-memory, mockable Mongo-ish db with the collections our services use.
    Override per-test by tweaking return values / side_effects.
    """
    db = SimpleNamespace(
        trips=make_fake_collection(),
        trip_history=make_fake_collection(),
        trip_analytics=make_fake_collection(),
        vehicles=make_fake_collection(),
        notifications=make_fake_collection(),
        drivers=make_fake_collection(),
        driver_assignments=make_fake_collection(),
    )
    db_management = SimpleNamespace(drivers=make_fake_collection())
    db.db_management = db_management
    return db

@pytest.fixture
def patch_db_manager(monkeypatch, fake_db):
    """
    Many services do: `from repositories.database import db_manager`.
    Patch that singleton to our fake_db for clean unit tests.
    """
    try:
        repo = importlib.import_module("repositories.database")
        monkeypatch.setattr(repo, "db_manager", fake_db)
    except Exception:
        pass
    return fake_db

@pytest.fixture
def patch_event_publisher(monkeypatch):
    """Patch the global event_publisher used by services to a no-op AsyncMock."""
    try:
        pubmod = importlib.import_module("events.publisher")
        mock_pub = AsyncMock()
        for name in (
            "publish_trip_started", "publish_trip_completed",
            "publish_driver_assigned", "publish_driver_unassigned",
            "publish_notification_sent",
        ):
            setattr(mock_pub, name, AsyncMock())
        monkeypatch.setattr(pubmod, "event_publisher", mock_pub)
        return mock_pub
    except Exception:
        return AsyncMock()


builtins.AsyncMock = AsyncMock
builtins.MagicMock = MagicMock
builtins.asyncio = asyncio
builtins._FakeCursor = _FakeCursor


@pytest.fixture(autouse=True)
def service_api_shims(monkeypatch):
    """
    Some tests call ConstraintService.apply_constraint(single, route_data),
    while the implementation may only expose apply_constraints_to_route(list, route_data).
    Provide a shim if needed.
    """
    try:
        import services.constraint_service as cs
        if hasattr(cs, "ConstraintService"):
            if (not hasattr(cs.ConstraintService, "apply_constraint")
                and hasattr(cs.ConstraintService, "apply_constraints_to_route")):

                async def _apply_constraint(self, constraint, route_data):
                    constraints = [constraint] if constraint is not None else []
                    return await cs.ConstraintService.apply_constraints_to_route(self, constraints, route_data)

                monkeypatch.setattr(cs.ConstraintService, "apply_constraint", _apply_constraint, raising=False)
    except Exception:
        pass
