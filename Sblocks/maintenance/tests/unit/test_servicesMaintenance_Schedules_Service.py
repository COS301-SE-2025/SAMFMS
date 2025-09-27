import sys
import os
import types
from datetime import datetime, timedelta, timezone
import pytest
import importlib


HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..")),
    os.path.abspath(os.path.join(HERE, "..")),
    os.getcwd(),
]
for p in CANDIDATES:
    if p not in sys.path:
        sys.path.insert(0, p)

if "schemas" not in sys.modules:
    schemas_pkg = types.ModuleType("schemas")
    sys.modules["schemas"] = schemas_pkg
else:
    schemas_pkg = sys.modules["schemas"]

if "schemas.entities" not in sys.modules:
    entities_mod = types.ModuleType("schemas.entities")
    class MaintenanceStatus:
        SCHEDULED = "SCHEDULED"
    class MaintenancePriority:
        LOW = "LOW"
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"
    entities_mod.MaintenanceStatus = MaintenanceStatus
    entities_mod.MaintenancePriority = MaintenancePriority
    setattr(schemas_pkg, "entities", entities_mod)
    sys.modules["schemas.entities"] = entities_mod


if "repositories" not in sys.modules:
    repos_mod = types.ModuleType("repositories")
    class MaintenanceSchedulesRepository:
        def __init__(self): ...
    repos_mod.MaintenanceSchedulesRepository = MaintenanceSchedulesRepository
    sys.modules["repositories"] = repos_mod


if "services" not in sys.modules:
    services_pkg = types.ModuleType("services")
    sys.modules["services"] = services_pkg
else:
    services_pkg = sys.modules["services"]

if "services.maintenance_service" not in sys.modules:
    ms_mod = types.ModuleType("services.maintenance_service")
    class _DummyMaintenanceRecordsService:
        async def create_maintenance_record(self, data):
            return {"id": "rec-1", **data}
    ms_mod.maintenance_records_service = _DummyMaintenanceRecordsService()
    setattr(services_pkg, "maintenance_service", ms_mod)
    sys.modules["services.maintenance_service"] = ms_mod

try:
    msched_mod = importlib.import_module("services.maintenance_schedules_service")
except Exception:
    msched_mod = importlib.import_module("maintenance_schedules_service")

MaintenanceSchedulesService = msched_mod.MaintenanceSchedulesService

class FakeRepo:
    def __init__(self):
        self.last_create_data = None
        self.create_return = {"id": "sch-1"}
        self.get_by_id_return = {"id": "sch-1"}
        self.update_return = {"id": "sch-1", "updated": True}
        self.delete_return = True
        self.vehicle_schedules = []
        self.active_schedules = []
        self.by_type_schedules = []
        self.calls = []

    async def create(self, data):
        self.calls.append(("create", data))
        self.last_create_data = dict(data)
        return dict(self.create_return)

    async def get_by_id(self, schedule_id):
        self.calls.append(("get_by_id", schedule_id))
        return None if self.get_by_id_return is None else dict(self.get_by_id_return)

    async def update(self, schedule_id, data):
        self.calls.append(("update", schedule_id, data))
        return self.update_return

    async def delete(self, schedule_id):
        self.calls.append(("delete", schedule_id))
        return self.delete_return

    async def get_schedules_for_vehicle(self, vehicle_id):
        self.calls.append(("get_schedules_for_vehicle", vehicle_id))
        return list(self.vehicle_schedules)

    async def get_active_schedules(self):
        self.calls.append(("get_active_schedules",))
        return list(self.active_schedules)

    async def get_schedules_by_type(self, vehicle_type):
        self.calls.append(("get_schedules_by_type", vehicle_type))
        return list(self.by_type_schedules)

def make_service(repo=None):
    svc = MaintenanceSchedulesService()
    if repo is not None:
        svc.repository = repo
    return svc

class FakeVehicleValidator:
    def __init__(self, ret=True):
        self._ret = ret
    async def validate_vehicle_id(self, vehicle_id):
        return self._ret


# ---- create_maintenance_schedule ----

@pytest.mark.asyncio
@pytest.mark.parametrize("missing", ["vehicle_id", "maintenance_type", "scheduled_date", "title"])
async def test_create_missing_required_field_raises(missing, monkeypatch):
    repo = FakeRepo()
    svc = make_service(repo)

    monkeypatch.setattr(msched_mod, "vehicle_validator", FakeVehicleValidator(True))

    payload = {
        "vehicle_id": "V1",
        "maintenance_type": "oil_change",
        "scheduled_date": "2025-01-15T00:00:00Z",
        "title": "Oil"
    }
    payload.pop(missing)

    with pytest.raises(ValueError):
        await svc.create_maintenance_schedule(payload)

@pytest.mark.asyncio
async def test_create_invalid_vehicle_id_raises(monkeypatch):
    repo = FakeRepo()
    svc = make_service(repo)
    monkeypatch.setattr(msched_mod, "vehicle_validator", FakeVehicleValidator(False))

    payload = {
        "vehicle_id": "NOPE",
        "maintenance_type": "oil_change",
        "scheduled_date": "2025-01-15T00:00:00Z",
        "title": "Oil Change",
    }
    with pytest.raises(ValueError):
        await svc.create_maintenance_schedule(payload)

@pytest.mark.asyncio
async def test_create_sets_defaults_parses_date_and_interval_default(monkeypatch):
    repo = FakeRepo()
    svc = make_service(repo)
    monkeypatch.setattr(msched_mod, "vehicle_validator", FakeVehicleValidator(True))

    payload = {
        "vehicle_id": "V1",
        "maintenance_type": "oil_change",
        "scheduled_date": "2025-01-15T00:00:00Z",
        "title": "Oil",
    }
    created = await svc.create_maintenance_schedule(payload)
    assert created["id"] == "sch-1"

    sent = repo.last_create_data
    assert sent["is_active"] is True
    assert isinstance(sent["created_at"], datetime)
    assert isinstance(sent["scheduled_date"], datetime)
    assert sent["interval_type"] == "mileage"
    assert sent["interval_value"] == svc._get_default_interval("oil_change")

@pytest.mark.asyncio
async def test_create_respects_provided_interval_fields(monkeypatch):
    repo = FakeRepo()
    svc = make_service(repo)
    monkeypatch.setattr(msched_mod, "vehicle_validator", FakeVehicleValidator(True))

    payload = {
        "vehicle_id": "V1",
        "maintenance_type": "brake_service",
        "scheduled_date": datetime(2025, 2, 1, tzinfo=timezone.utc),
        "title": "Brakes",
        "interval_type": "time",
        "interval_value": 60,
        "is_active": False,
        "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
    }
    _ = await svc.create_maintenance_schedule(payload)
    sent = repo.last_create_data
    assert sent["interval_type"] == "time"
    assert sent["interval_value"] == 60
    assert sent["is_active"] is False
    assert sent["created_at"] == datetime(2025, 1, 1, tzinfo=timezone.utc)

# ---- get_maintenance_schedule ----

@pytest.mark.asyncio
async def test_get_maintenance_schedule_returns_record():
    repo = FakeRepo()
    repo.get_by_id_return = {"id": "sch-42"}
    svc = make_service(repo)
    res = await svc.get_maintenance_schedule("sch-42")
    assert res["id"] == "sch-42"


@pytest.mark.asyncio
async def test_update_rejects_invalid_vehicle_id(monkeypatch):
    repo = FakeRepo()
    svc = make_service(repo)
    monkeypatch.setattr(msched_mod, "vehicle_validator", FakeVehicleValidator(False))

    with pytest.raises(ValueError):
        await svc.update_maintenance_schedule("sch-1", {"vehicle_id": "NOPE"})

@pytest.mark.asyncio
async def test_update_parses_datetimes_and_triggers_calculate_next_due(monkeypatch):
    repo = FakeRepo()
    svc = make_service(repo)
    monkeypatch.setattr(msched_mod, "vehicle_validator", FakeVehicleValidator(True))

    called = {"flag": False}
    async def _calc(data):
        called["flag"] = True
        data["next_due_date"] = datetime(2025, 3, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(svc, "_calculate_next_due", _calc)

    data = {
        "scheduled_date": "2025-02-01T00:00:00Z",
        "last_service_date": "2025-01-01T00:00:00Z",
        "next_due_date": "2025-02-15T00:00:00Z",
        "interval_type": "time",
    }
    out = await svc.update_maintenance_schedule("sch-1", data)
    assert out == repo.update_return
    _, _, sent = repo.calls[-1]
    assert isinstance(sent["scheduled_date"], datetime)
    assert isinstance(sent["last_service_date"], datetime)
    assert isinstance(sent["next_due_date"], datetime)
    assert called["flag"] is True

@pytest.mark.asyncio
async def test_update_returns_none_when_repo_returns_none():
    repo = FakeRepo()
    repo.update_return = None
    svc = make_service(repo)
    out = await svc.update_maintenance_schedule("sch-1", {"title": "X"})
    assert out is None

# ---- delete_maintenance_schedule ----

@pytest.mark.asyncio
async def test_delete_maintenance_schedule_true_and_false():
    repo = FakeRepo()
    svc = make_service(repo)

    repo.delete_return = True
    assert await svc.delete_maintenance_schedule("sch-1") is True

    repo.delete_return = False
    assert await svc.delete_maintenance_schedule("sch-1") is False

# ---- get_vehicle_maintenance_schedules ----

@pytest.mark.asyncio
async def test_get_vehicle_schedules_invalid_vehicle_id_raises(monkeypatch):
    repo = FakeRepo()
    svc = make_service(repo)
    monkeypatch.setattr(msched_mod, "vehicle_validator", FakeVehicleValidator(False))
    with pytest.raises(ValueError):
        await svc.get_vehicle_maintenance_schedules("NOPE")

@pytest.mark.asyncio
async def test_get_vehicle_schedules_success(monkeypatch):
    repo = FakeRepo()
    repo.vehicle_schedules = [{"id": "s1"}, {"id": "s2"}]
    svc = make_service(repo)
    monkeypatch.setattr(msched_mod, "vehicle_validator", FakeVehicleValidator(True))
    res = await svc.get_vehicle_maintenance_schedules("V1")
    assert res == [{"id": "s1"}, {"id": "s2"}]

# ---- get_active_schedules / get_schedules_by_type ----

@pytest.mark.asyncio
async def test_get_active_schedules_passthrough():
    repo = FakeRepo()
    repo.active_schedules = [{"id": "a1"}]
    svc = make_service(repo)
    res = await svc.get_active_schedules()
    assert res == [{"id": "a1"}]

@pytest.mark.asyncio
async def test_get_schedules_by_type_passthrough():
    repo = FakeRepo()
    repo.by_type_schedules = [{"id": "t1"}]
    svc = make_service(repo)
    res = await svc.get_schedules_by_type("truck")
    assert res == [{"id": "t1"}]

# ---- get_due_schedules ----

@pytest.mark.asyncio
async def test_get_due_schedules_filters_using_is_schedule_due():
    repo = FakeRepo()
    now = datetime.utcnow().replace(tzinfo=None)
    repo.active_schedules = [
        {"id": "A", "is_active": True, "next_due_date": now - timedelta(days=1)},
        {"id": "B", "is_active": True, "scheduled_date": now - timedelta(hours=1)},
        {"id": "C", "is_active": True, "next_due_date": now + timedelta(days=1)},
        {"id": "D", "is_active": False, "scheduled_date": now - timedelta(days=5)},
    ]
    svc = make_service(repo)
    due = await svc.get_due_schedules()
    ids = [d["id"] for d in due]
    assert set(ids) == {"A", "B"}

# ---- _is_schedule_due (all branches) ----

def test_is_schedule_due_inactive_returns_false():
    svc = make_service(FakeRepo())
    now = datetime.utcnow()
    assert svc._is_schedule_due({"is_active": False, "next_due_date": now - timedelta(days=1)}, now) is False

def test_is_schedule_due_next_due_date_past_true():
    svc = make_service(FakeRepo())
    now = datetime.utcnow()
    assert svc._is_schedule_due({"is_active": True, "next_due_date": now - timedelta(seconds=1)}, now) is True

def test_is_schedule_due_next_due_date_future_false():
    svc = make_service(FakeRepo())
    now = datetime.utcnow()
    assert svc._is_schedule_due({"is_active": True, "next_due_date": now + timedelta(seconds=1)}, now) is False

def test_is_schedule_due_uses_scheduled_date_past_true_when_no_next_due():
    svc = make_service(FakeRepo())
    now = datetime.utcnow()
    assert svc._is_schedule_due({"is_active": True, "scheduled_date": now - timedelta(minutes=1)}, now) is True

def test_is_schedule_due_scheduled_date_future_false():
    svc = make_service(FakeRepo())
    now = datetime.utcnow()
    assert svc._is_schedule_due({"is_active": True, "scheduled_date": now + timedelta(minutes=1)}, now) is False

def test_is_schedule_due_non_datetime_fields_returns_false():
    svc = make_service(FakeRepo())
    now = datetime.utcnow()
    assert svc._is_schedule_due({"is_active": True, "next_due_date": "2025-01-01"}, now) is False

# ---- create_record_from_schedule ----

@pytest.mark.asyncio
async def test_create_record_from_schedule_not_found_raises(monkeypatch):
    repo = FakeRepo()
    repo.get_by_id_return = None
    svc = make_service(repo)
    with pytest.raises(ValueError):
        await svc.create_record_from_schedule("missing-id")

@pytest.mark.asyncio
async def test_create_record_from_schedule_uses_next_due_date_if_present(monkeypatch):
    repo = FakeRepo()
    svc = make_service(repo)

    nd = datetime(2026, 1, 1, tzinfo=timezone.utc)
    repo.get_by_id_return = {
        "id": "sch-1",
        "vehicle_id": "V9",
        "maintenance_type": "oil_change",
        "title": "Oil",
        "description": "desc",
        "scheduled_date": datetime(2025, 12, 31, tzinfo=timezone.utc),
        "next_due_date": nd,
    }

    import services.maintenance_service as mm
    captured = {}
    class CapturingMRS:
        async def create_maintenance_record(self, data):
            captured.update(data)
            return {"id": "rec-99", **data}
    mm.maintenance_records_service = CapturingMRS()

    updated = {}
    async def fake_update(_sid, data):
        updated.update(data)
        return {"id": "sch-1", **data}
    monkeypatch.setattr(svc, "update_maintenance_schedule", fake_update)

    rec = await svc.create_record_from_schedule("sch-1")
    assert rec["id"] == "rec-99"
    assert captured["status"] == msched_mod.MaintenanceStatus.SCHEDULED
    assert captured["priority"] == msched_mod.MaintenancePriority.MEDIUM
    assert captured["scheduled_date"] == nd
    assert "last_executed" in updated and isinstance(updated["last_executed"], datetime)
    assert updated["last_record_id"] == "rec-99"

@pytest.mark.asyncio
async def test_create_record_from_schedule_falls_back_to_scheduled_date(monkeypatch):
    repo = FakeRepo()
    svc = make_service(repo)

    sd = datetime(2026, 2, 1, tzinfo=timezone.utc)
    repo.get_by_id_return = {
        "id": "sch-2",
        "vehicle_id": "V1",
        "maintenance_type": "brake_service",
        "title": "Brakes",
        "scheduled_date": sd,
    }

    import services.maintenance_service as mm
    captured = {}
    class CapturingMRS:
        async def create_maintenance_record(self, data):
            captured.update(data)
            return {"id": "rec-1", **data}
    mm.maintenance_records_service = CapturingMRS()

    async def fake_update(*_a, **_k):
        return None
    monkeypatch.setattr(svc, "update_maintenance_schedule", fake_update)

    rec = await svc.create_record_from_schedule("sch-2")
    assert rec["id"] == "rec-1"
    assert captured["scheduled_date"] == sd

# ---- _get_default_interval ----

def test_get_default_interval_known_type():
    svc = make_service(FakeRepo())
    # Should not raise; ensure it returns an int
    assert isinstance(svc._get_default_interval("oil_change"), int)

def test_get_default_interval_unknown_type_defaults_15000():
    svc = make_service(FakeRepo())
    assert svc._get_default_interval("mystery_service") == 15000

# ---- _calculate_next_due (all branches) ----

@pytest.mark.asyncio
async def test_calculate_next_due_time_interval_parses_str_date_and_sets_next_due():
    svc = make_service(FakeRepo())
    data = {"interval_type": "time", "interval_value": 30, "last_service_date": "2025-01-01T00:00:00Z"}
    await svc._calculate_next_due(data)
    assert "next_due_date" in data
    assert isinstance(data["next_due_date"], datetime)

@pytest.mark.asyncio
async def test_calculate_next_due_mileage_sets_next_due_mileage():
    svc = make_service(FakeRepo())
    data = {"interval_type": "mileage", "interval_value": 10000, "last_service_mileage": 45000}
    await svc._calculate_next_due(data)
    assert data["next_due_mileage"] == 55000

@pytest.mark.asyncio
async def test_calculate_next_due_both_sets_both_when_present():
    svc = make_service(FakeRepo())
    data = {"interval_type": "both", "interval_value": 90,
            "last_service_date": "2025-01-02T00:00:00Z", "last_service_mileage": 10000}
    await svc._calculate_next_due(data)
    assert isinstance(data.get("next_due_date"), datetime)
    assert data.get("next_due_mileage") == 10000 + 90

@pytest.mark.asyncio
async def test_calculate_next_due_handles_bad_date_string_without_raising():
    svc = make_service(FakeRepo())
    data = {"interval_type": "time", "interval_value": 30, "last_service_date": "not-a-date"}
    await svc._calculate_next_due(data)
    assert "next_due_date" not in data
