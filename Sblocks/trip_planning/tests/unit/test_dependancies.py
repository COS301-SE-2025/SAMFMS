import pytest
from fastapi import HTTPException


import api.dependencies as deps


@pytest.mark.asyncio
async def test_get_current_user_ok():
    user = await deps.get_current_user("Bearer anytoken")
    assert user == "user_123"


@pytest.mark.asyncio
async def test_get_current_user_missing_header():
    with pytest.raises(HTTPException) as e:
        await deps.get_current_user(None)
    assert e.value.status_code == 401
    assert "Authorization header required" in e.value.detail


@pytest.mark.asyncio
async def test_get_current_user_bad_format():
    with pytest.raises(HTTPException) as e:
        await deps.get_current_user("Basic abc")
    assert e.value.status_code == 401
    assert "Invalid authorization format" in e.value.detail


@pytest.mark.asyncio
async def test_get_current_user_secure_ok():
    ctx = await deps.get_current_user_secure("Bearer x")
    assert ctx["user_id"] == "user_123"
    assert "permissions" in ctx


@pytest.mark.asyncio
async def test_get_current_user_secure_missing_header():
    with pytest.raises(HTTPException):
        await deps.get_current_user_secure(None)


@pytest.mark.asyncio
async def test_validate_trip_access_404(monkeypatch):
    async def _get_by_id(_):
        return None
    monkeypatch.setattr(deps.trip_service, "get_trip_by_id", _get_by_id)
    with pytest.raises(HTTPException) as e:
        await deps.validate_trip_access("t1", current_user="u1")
    assert e.value.status_code == 404


class _DriverAssign:
    def __init__(self, driver_id): self.driver_id = driver_id

class _TripStub:
    def __init__(self, created_by="creator", driver_id=None):
        self.created_by = created_by
        self.driver_assignment = _DriverAssign(driver_id) if driver_id else None

@pytest.mark.asyncio
async def test_validate_trip_access_ok_creator(monkeypatch):
    async def _get_by_id(_): return _TripStub(created_by="u1")
    monkeypatch.setattr(deps.trip_service, "get_trip_by_id", _get_by_id)
    trip = await deps.validate_trip_access("t1", current_user="u1")
    assert isinstance(trip, _TripStub)

@pytest.mark.asyncio
async def test_validate_trip_access_ok_assigned_driver(monkeypatch):
    async def _get_by_id(_): return _TripStub(created_by="other", driver_id="u2")
    monkeypatch.setattr(deps.trip_service, "get_trip_by_id", _get_by_id)
    trip = await deps.validate_trip_access("t1", current_user="u2")
    assert isinstance(trip, _TripStub)

@pytest.mark.asyncio
async def test_validate_trip_access_forbidden(monkeypatch):
    async def _get_by_id(_): return _TripStub(created_by="someone", driver_id="driverX")
    monkeypatch.setattr(deps.trip_service, "get_trip_by_id", _get_by_id)
    with pytest.raises(HTTPException) as e:
        await deps.validate_trip_access("t1", current_user="stranger")
    assert e.value.status_code == 403


def test_get_pagination_params_ok():
    assert deps.get_pagination_params(0, 50) == {"skip": 0, "limit": 50}


def test_get_pagination_params_bad_skip():
    with pytest.raises(HTTPException) as e:
        deps.get_pagination_params(-1, 10)
    assert e.value.status_code == 400


def test_get_pagination_params_bad_limit_low():
    with pytest.raises(HTTPException) as e:
        deps.get_pagination_params(0, 0)
    assert e.value.status_code == 400


def test_get_pagination_params_bad_limit_high():
    with pytest.raises(HTTPException) as e:
        deps.get_pagination_params(0, 1001)
    assert e.value.status_code == 400
