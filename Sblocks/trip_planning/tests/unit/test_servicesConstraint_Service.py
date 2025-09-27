import os
import sys
import types
import pytest
from unittest.mock import AsyncMock, MagicMock
import importlib.util
from contextlib import contextmanager


@contextmanager
def _sysmodules_snapshot():
    snap = sys.modules.copy()
    try:
        yield
    finally:
        added = set(sys.modules) - set(snap)
        for k in added:
            sys.modules.pop(k, None)
        for k, v in snap.items():
            sys.modules[k] = v

def _load_constraint_service_module():
    try:
        from trip_planning.services.constraint_service import (
            ConstraintService,
            constraint_service as global_constraint_service,
        )
        import trip_planning.services.constraint_service as cs_module
        return ConstraintService, global_constraint_service, cs_module
    except Exception:

        repos_pkg = types.ModuleType("repositories")
        repos_db = types.ModuleType("repositories.database")
        repos_db.db_manager = types.SimpleNamespace()

        schemas_pkg = types.ModuleType("schemas")
        schemas_entities = types.ModuleType("schemas.entities")
        schemas_requests = types.ModuleType("schemas.requests")

        class _TripConstraint: ...
        class _ConstraintType: ...
        class _CreateConstraintRequest: ...
        class _UpdateConstraintRequest: ...

        schemas_entities.TripConstraint = _TripConstraint
        schemas_entities.ConstraintType = _ConstraintType
        schemas_requests.CreateConstraintRequest = _CreateConstraintRequest
        schemas_requests.UpdateConstraintRequest = _UpdateConstraintRequest

        this_dir = os.path.dirname(__file__)
        root = os.path.abspath(os.path.join(this_dir, "..", ".."))
        module_path = os.path.join(root, "services", "constraint_service.py")
        if not os.path.exists(module_path):
            raise ModuleNotFoundError(f"Could not find constraint_service.py at: {module_path}")

        with _sysmodules_snapshot():
            sys.modules.update({
                "repositories": repos_pkg,
                "repositories.database": repos_db,
                "schemas": schemas_pkg,
                "schemas.entities": schemas_entities,
                "schemas.requests": schemas_requests,
            })
            spec = importlib.util.spec_from_file_location(
                "loaded.constraint_service_isolated", module_path
            )
            assert spec and spec.loader
            cs_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cs_module)

        ConstraintService = cs_module.ConstraintService
        global_constraint_service = getattr(cs_module, "constraint_service", None)
        return ConstraintService, global_constraint_service, cs_module

ConstraintService, global_constraint_service, cs_module = _load_constraint_service_module()

class AsyncCursor:
    def __init__(self, docs):
        self._docs = list(docs)
    def sort(self, *_, **__):
        return self
    def __aiter__(self):
        async def gen():
            for d in self._docs:
                yield d
        return gen()

class FakeCollection:
    def __init__(self):
        self.find_one = AsyncMock()
        self.insert_one = AsyncMock()
        self.update_one = AsyncMock()
        self.delete_one = AsyncMock()
        self.find = MagicMock()

class FakeDB:
    def __init__(self):
        self.trips = FakeCollection()
        self.trip_constraints = FakeCollection()

def make_request(type_=None, value=None, priority=None):
    return types.SimpleNamespace(type=type_, value=value, priority=priority)

class DummyUpdateRequest:
    def __init__(self, **kwargs):
        self._values = kwargs
    def dict(self, exclude_unset=False):
        if not exclude_unset:
            return dict(self._values)
        return {k: v for k, v in self._values.items() if v is not None}

class ModelLike:
    def __init__(self, **data):
        self._data = dict(data)
        for k, v in self._data.items():
            setattr(self, k, v)
    def dict(self):
        return dict(self._data)

CT = getattr(cs_module, "ConstraintType", None)
def ct(name: str):
    return getattr(CT, name) if (CT and hasattr(CT, name)) else name.lower()

VALID_TRIP_ID = "507f1f77bcf86cd799439011"
VALID_CONSTRAINT_ID = "64d2e1fa0c1234567890abcd"  

@pytest.fixture
def service():
    svc = ConstraintService()
    svc.db = FakeDB()
    return svc

# ==========
# add_constraint_to_trip
# ==========

@pytest.mark.asyncio
async def test_add_constraint_trip_not_found_raises(service):
    service.db.trips.find_one.return_value = None
    req = make_request(ct("AVOID_TOLLS"), None, 5)
    with pytest.raises(ValueError):
        await service.add_constraint_to_trip(VALID_TRIP_ID, req)

@pytest.mark.asyncio
async def test_add_constraint_happy_path_simple_flag(service):
    service.db.trips.find_one.return_value = {"_id": VALID_TRIP_ID}
    service.db.trip_constraints.insert_one.return_value = types.SimpleNamespace(
        inserted_id=VALID_CONSTRAINT_ID
    )
    service.db.trips.update_one.return_value = types.SimpleNamespace(modified_count=1)

    req = make_request(ct("AVOID_TOLLS"), None, 5)
    out = await service.add_constraint_to_trip(VALID_TRIP_ID, req)
    data = out if isinstance(out, dict) else out.dict()
    assert data["trip_id"] == VALID_TRIP_ID
    assert data["priority"] == 5
    assert str(data.get("_id") or data.get("id"))

    service.db.trip_constraints.insert_one.assert_called_once()
    service.db.trips.update_one.assert_called_once()

@pytest.mark.asyncio
async def test_add_constraint_avoid_area_missing_radius_raises(service):
    service.db.trips.find_one.return_value = {"_id": "ok"}
    req = make_request(ct("AVOID_AREA"), {"center": {"coordinates": [0, 0]}}, 3)
    with pytest.raises(ValueError):
        await service.add_constraint_to_trip(VALID_TRIP_ID, req)

@pytest.mark.asyncio
async def test_add_constraint_avoid_area_bad_center_raises(service):
    service.db.trips.find_one.return_value = {"_id": "ok"}
    req = make_request(ct("AVOID_AREA"), {"center": "not-a-dict", "radius": 10}, 3)
    with pytest.raises(ValueError):
        await service.add_constraint_to_trip(VALID_TRIP_ID, req)

@pytest.mark.asyncio
async def test_add_constraint_avoid_area_non_positive_radius_raises(service):
    service.db.trips.find_one.return_value = {"_id": "ok"}
    req = make_request(ct("AVOID_AREA"), {"center": {"coordinates": [0, 0]}, "radius": 0}, 3)
    with pytest.raises(ValueError):
        await service.add_constraint_to_trip(VALID_TRIP_ID, req)

@pytest.mark.asyncio
async def test_add_constraint_preferred_route_missing_waypoints_allows_empty(service):
    service.db.trips.find_one.return_value = {"_id": "ok"}
    service.db.trip_constraints.insert_one.return_value = types.SimpleNamespace(
        inserted_id=VALID_CONSTRAINT_ID
    )
    service.db.trips.update_one.return_value = types.SimpleNamespace(modified_count=1)
    req = make_request(ct("PREFERRED_ROUTE"), {}, 1)
    out = await service.add_constraint_to_trip(VALID_TRIP_ID, req)
    assert out  

# ==========
# get_trip_constraints
# ==========

@pytest.mark.asyncio
async def test_get_trip_constraints_returns_list(service):
    docs = [
        {"_id": VALID_CONSTRAINT_ID, "trip_id": "T", "type": ct("AVOID_TOLLS"), "priority": 1, "is_active": True, "value": None},
        {"_id": "64d2e1fa0c1234567890abce", "trip_id": "T", "type": ct("FASTEST_ROUTE"), "priority": 2, "is_active": True, "value": None},
    ]
    service.db.trip_constraints.find.return_value = AsyncCursor(docs)
    out = await service.get_trip_constraints("T")
    assert isinstance(out, list) and len(out) == 2

@pytest.mark.asyncio
async def test_get_trip_constraints_find_raises(service):
    def boom(*_, **__):
        raise RuntimeError("DB broken")
    service.db.trip_constraints.find.side_effect = boom
    with pytest.raises(RuntimeError):
        await service.get_trip_constraints("T")

# ==========
# get_constraint_by_id
# ==========

@pytest.mark.asyncio
async def test_get_constraint_by_id_found(service):
    service.db.trip_constraints.find_one.return_value = {
        "_id": VALID_CONSTRAINT_ID, "trip_id": "T", "type": ct("AVOID_FERRIES"),
        "value": None, "priority": 2, "is_active": True
    }
    out = await service.get_constraint_by_id(VALID_CONSTRAINT_ID)
    assert out is not None

@pytest.mark.asyncio
async def test_get_constraint_by_id_not_found(service):
    service.db.trip_constraints.find_one.return_value = None
    out = await service.get_constraint_by_id("64d2e1fa0c1234567890abcf") 
    assert out is None

# ==========
# update_constraint
# ==========

@pytest.mark.asyncio
async def test_update_constraint_not_found_returns_none(service, monkeypatch):
    monkeypatch.setattr(service, "get_constraint_by_id", AsyncMock(return_value=None))
    req = DummyUpdateRequest(name="anything")
    assert await service.update_constraint(VALID_CONSTRAINT_ID, req) is None

@pytest.mark.asyncio
async def test_update_constraint_modified_count_zero_returns_none(service, monkeypatch):
    existing = ModelLike(_id=VALID_CONSTRAINT_ID, trip_id="T", type=ct("AVOID_AREA"),
                         value={"center": {"coordinates":[0,0]}, "radius": 5},
                         priority=3, is_active=True)
    monkeypatch.setattr(service, "get_constraint_by_id", AsyncMock(return_value=existing))
    service.db.trip_constraints.update_one.return_value = types.SimpleNamespace(modified_count=0)

    req = DummyUpdateRequest(value={"center": {"coordinates":[1,1]}, "radius": 10})
    assert await service.update_constraint(VALID_CONSTRAINT_ID, req) is None

@pytest.mark.asyncio
async def test_update_constraint_success(service, monkeypatch):
    existing = ModelLike(_id=VALID_CONSTRAINT_ID, trip_id="T", type=ct("PREFERRED_ROUTE"),
                         value={"waypoints": ["A"]}, priority=3, is_active=True)
    updated  = {"_id": VALID_CONSTRAINT_ID, "trip_id": "T", "type": ct("PREFERRED_ROUTE"),
                "value": {"waypoints": ["A","B"]}, "priority": 3, "is_active": True}

    get_mock = AsyncMock(side_effect=[existing, updated]) 
    monkeypatch.setattr(service, "get_constraint_by_id", get_mock)
    service.db.trip_constraints.update_one.return_value = types.SimpleNamespace(modified_count=1)
    upd_trip = AsyncMock()
    monkeypatch.setattr(service, "_update_trip_constraints", upd_trip)

    req = DummyUpdateRequest(value={"waypoints": ["A","B"]})
    out = await service.update_constraint(VALID_CONSTRAINT_ID, req)
    data = out if isinstance(out, dict) else getattr(out, "model_dump", lambda: out)()
    if not isinstance(data, dict):
        data = out.dict() if hasattr(out, "dict") else {}
    assert (data.get("value") or {}).get("waypoints") == ["A","B"]
    upd_trip.assert_awaited_once_with("T")

@pytest.mark.asyncio
async def test_update_constraint_validation_error_raises(service, monkeypatch):
    existing = ModelLike(_id=VALID_CONSTRAINT_ID, trip_id="T", type=ct("PREFERRED_ROUTE"),
                         value={"waypoints": ["A"]}, priority=3, is_active=True)
    monkeypatch.setattr(service, "get_constraint_by_id", AsyncMock(return_value=existing))
    def force_raise(_type, _value):
        raise ValueError("requires waypoints list")
    monkeypatch.setattr(service, "_validate_constraint_value", force_raise)
    bad_req = DummyUpdateRequest(value={"waypoints": "not-a-list"})
    with pytest.raises(ValueError):
        await service.update_constraint(VALID_CONSTRAINT_ID, bad_req)

# ==========
# remove_constraint
# ==========

@pytest.mark.asyncio
async def test_remove_constraint_not_found_returns_false(service, monkeypatch):
    monkeypatch.setattr(service, "get_constraint_by_id", AsyncMock(return_value=None))
    assert await service.remove_constraint(VALID_CONSTRAINT_ID) is False

@pytest.mark.asyncio
async def test_remove_constraint_deleted_count_zero_returns_false(service, monkeypatch):
    c = ModelLike(_id=VALID_CONSTRAINT_ID, trip_id="T", type=ct("AVOID_TOLLS"),
                  value=None, priority=1, is_active=True)
    monkeypatch.setattr(service, "get_constraint_by_id", AsyncMock(return_value=c))
    service.db.trip_constraints.delete_one.return_value = types.SimpleNamespace(deleted_count=0)
    assert await service.remove_constraint(VALID_CONSTRAINT_ID) is False

@pytest.mark.asyncio
async def test_remove_constraint_success(service, monkeypatch):
    c = ModelLike(_id=VALID_CONSTRAINT_ID, trip_id="T", type=ct("AVOID_TOLLS"),
                  value=None, priority=1, is_active=True)
    monkeypatch.setattr(service, "get_constraint_by_id", AsyncMock(return_value=c))
    service.db.trip_constraints.delete_one.return_value = types.SimpleNamespace(deleted_count=1)
    upd_trip = AsyncMock()
    monkeypatch.setattr(service, "_update_trip_constraints", upd_trip)
    assert await service.remove_constraint(VALID_CONSTRAINT_ID) is True
    upd_trip.assert_awaited_once_with("T")

# ==========
# get_active_constraints_for_trip
# ==========

@pytest.mark.asyncio
async def test_get_active_constraints_for_trip_returns_list(service):
    docs = [
        {"_id": "64d2e1fa0c1234567890abce", "trip_id": "T", "type": ct("FASTEST_ROUTE"), "priority": 7, "is_active": True, "value": None},
        {"_id": "64d2e1fa0c1234567890abcf", "trip_id": "T", "type": ct("AVOID_FERRIES"), "priority": 2, "is_active": True, "value": None},
    ]
    service.db.trip_constraints.find.return_value = AsyncCursor(docs)
    out = await service.get_active_constraints_for_trip("T")
    assert isinstance(out, list) and len(out) == 2

# ==========
# apply_constraints_to_route
# ==========

@pytest.mark.asyncio
async def test_apply_constraints_to_route_combines_all(service, monkeypatch):
    fake_constraints = [
        ModelLike(id="64d2e1fa0c1234567890abce", trip_id="T", type=ct("SHORTEST_ROUTE"),
                  value=None, priority=6, is_active=True)
    ]
    monkeypatch.setattr(service, "get_active_constraints_for_trip", AsyncMock(return_value=fake_constraints))
    base = {"foo": "bar"}
    out = await service.apply_constraints_to_route("T", base)
    assert isinstance(out, dict)
    assert base == {"foo": "bar"}  

# ==========
# _update_trip_constraints
# ==========

@pytest.mark.asyncio
async def test_update_trip_constraints_normal(service, monkeypatch):
    items = [
        ModelLike(_id="64d2e1fa0c1234567890abca", trip_id=VALID_TRIP_ID, type=ct("AVOID_TOLLS"), value=None, priority=1, is_active=True),
        ModelLike(_id="64d2e1fa0c1234567890abcb", trip_id=VALID_TRIP_ID, type=ct("FUEL_EFFICIENT"), value=None, priority=4, is_active=True),
    ]
    monkeypatch.setattr(service, "get_trip_constraints", AsyncMock(return_value=items))
    service.db.trips.update_one.return_value = types.SimpleNamespace(modified_count=1)

    await service._update_trip_constraints(VALID_TRIP_ID)
    call = service.db.trips.update_one.await_args
    assert call is not None
    update_doc = call.args[1] if len(call.args) >= 2 else call.kwargs.get("update", {})
    body = update_doc.get("$set", update_doc)
    assert "constraints" in body
    ids = [c.get("id") or c.get("_id") for c in body["constraints"]]
    assert ids == ["64d2e1fa0c1234567890abca", "64d2e1fa0c1234567890abcb"]

@pytest.mark.asyncio
async def test_update_trip_constraints_swallows_errors(service, monkeypatch):
    monkeypatch.setattr(service, "get_trip_constraints", AsyncMock(side_effect=RuntimeError("boom")))
    await service._update_trip_constraints(VALID_TRIP_ID)

# ==========
# get_constraint_templates
# ==========

@pytest.mark.asyncio
async def test_get_constraint_templates_has_expected_types(service):
    out = await service.get_constraint_templates()
    def norm(t):
        return t.value if hasattr(t, "value") else t
    got = {norm(tpl["type"]) for tpl in out}
    expected = {
        "avoid_tolls", "avoid_highways", "fastest_route",
        "shortest_route", "fuel_efficient", "avoid_ferries"
    }
    assert expected.issubset(got)
