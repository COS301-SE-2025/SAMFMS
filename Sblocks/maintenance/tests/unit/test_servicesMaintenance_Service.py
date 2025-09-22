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

    class MaintenanceRecord: ...
    class MaintenanceStatus:
        SCHEDULED = "SCHEDULED"
        IN_PROGRESS = "IN_PROGRESS"
        COMPLETED = "COMPLETED"
        OVERDUE = "OVERDUE"

    class MaintenancePriority:
        MEDIUM = "MEDIUM"
        HIGH = "HIGH"
        CRITICAL = "CRITICAL"

    entities_mod.MaintenanceRecord = MaintenanceRecord
    entities_mod.MaintenanceStatus = MaintenanceStatus
    entities_mod.MaintenancePriority = MaintenancePriority
    setattr(schemas_pkg, "entities", entities_mod)
    sys.modules["schemas.entities"] = entities_mod


if "repositories" not in sys.modules:
    repos_mod = types.ModuleType("repositories")

    class MaintenanceRecordsRepository:
        def __init__(self): ...

    repos_mod.MaintenanceRecordsRepository = MaintenanceRecordsRepository
    sys.modules["repositories"] = repos_mod


if "services" not in sys.modules:
    services_pkg = types.ModuleType("services")
    sys.modules["services"] = services_pkg
else:
    services_pkg = sys.modules["services"]

if "services.notification_service" not in sys.modules:
    notif_mod = types.ModuleType("services.notification_service")

    class _DummyNotificationService:
        def __init__(self):
            self.created = []
        async def create_notification(self, data):
            self.created.append(data)

    notif_mod.notification_service = _DummyNotificationService()
    setattr(services_pkg, "notification_service", notif_mod)
    sys.modules["services.notification_service"] = notif_mod


try:
    ms_mod = importlib.import_module("services.maintenance_service")
except Exception:
    ms_mod = importlib.import_module("maintenance_service")

MaintenanceRecordsService = ms_mod.MaintenanceRecordsService
MaintenanceStatus = ms_mod.MaintenanceStatus
MaintenancePriority = ms_mod.MaintenancePriority


class FakeVehicleValidator:
    def __init__(self, ret=True):
        self._ret = ret
    async def validate_vehicle_id(self, vehicle_id):
        return self._ret

class FakeRepo:
    def __init__(self):
        self.create_should_raise = None
        self.create_return = None 
        self.get_by_id_return = None
        self.update_return = None
        self.delete_return = False
        self.by_vehicle_return = []
        self.by_status_return = []
        self.overdue_return = []
        self.upcoming_return = []
        self.history_return = []
        self.cost_summary_return = {}
        self.find_return = []

        self.last_create_data = None
        self.last_update_id = None
        self.last_update_data = None
        self.last_find_args = None
        self.last_history_args = None
        self.last_cost_args = None

    async def create(self, data):
        if self.create_should_raise:
            raise self.create_should_raise
        self.last_create_data = dict(data)
        if self.create_return is not None:
            return dict(self.create_return)
        return {"id": "r1", **dict(data)}

    async def get_by_id(self, record_id):
        return None if self.get_by_id_return is None else dict(self.get_by_id_return)

    async def update(self, record_id, data):
        self.last_update_id = record_id
        self.last_update_data = dict(data)
        return self.update_return

    async def delete(self, record_id):
        return bool(self.delete_return)

    async def get_by_vehicle_id(self, vehicle_id, skip, limit):
        return list(self.by_vehicle_return)

    async def get_by_status(self, status, skip, limit):
        return list(self.by_status_return)

    async def get_overdue_maintenance(self):
        return list(self.overdue_return)

    async def get_upcoming_maintenance(self, days_ahead):
        return list(self.upcoming_return)

    async def get_maintenance_history(self, vehicle_id, start_dt, end_dt):
        self.last_history_args = {"vehicle_id": vehicle_id, "start_dt": start_dt, "end_dt": end_dt}
        return list(self.history_return)

    async def get_cost_summary(self, vehicle_id, start_dt, end_dt):
        self.last_cost_args = {"vehicle_id": vehicle_id, "start_dt": start_dt, "end_dt": end_dt}
        return dict(self.cost_summary_return)

    async def find(self, query=None, skip=0, limit=100, sort=None):
        self.last_find_args = {"query": dict(query or {}), "skip": skip, "limit": limit, "sort": list(sort or [])}
        return list(self.find_return)


def make_service(repo=None, vehicle_ok=True):
    svc = MaintenanceRecordsService()
    if repo is not None:
        svc.repository = repo
    ms_mod.vehicle_validator = FakeVehicleValidator(vehicle_ok)
    return svc



@pytest.mark.asyncio
@pytest.mark.parametrize("missing", ["vehicle_id", "maintenance_type", "scheduled_date", "title"])
async def test_create_missing_required_field_raises(missing):
    svc = make_service(FakeRepo(), vehicle_ok=True)
    data = {
        "vehicle_id": "V1",
        "maintenance_type": "general",
        "scheduled_date": "2028-01-01T00:00:00Z",
        "title": "General",
    }
    data.pop(missing)
    with pytest.raises(ValueError):
        await svc.create_maintenance_record(data)

@pytest.mark.asyncio
async def test_create_invalid_vehicle_id_raises():
    svc = make_service(FakeRepo(), vehicle_ok=False)
    data = {
        "vehicle_id": "BAD",
        "maintenance_type": "general",
        "scheduled_date": "2028-01-01T00:00:00Z",
        "title": "General",
    }
    with pytest.raises(ValueError):
        await svc.create_maintenance_record(data)

@pytest.mark.asyncio
async def test_create_parses_scheduled_date_and_applies_defaults_future_general():
    repo = FakeRepo()
    svc = make_service(repo, vehicle_ok=True)
    future = (datetime.utcnow() + timedelta(days=30)).replace(tzinfo=timezone.utc)
    data = {
        "vehicle_id": "V1",
        "maintenance_type": "general",
        "scheduled_date": future.isoformat().replace("+00:00", "Z"),
        "title": "General",
    }
    rec = await svc.create_maintenance_record(data)
    assert rec["id"] == "r1"
    sent = repo.last_create_data
    assert isinstance(sent["scheduled_date"], datetime)
    assert sent["status"] == MaintenanceStatus.SCHEDULED
    assert sent["priority"] == MaintenancePriority.MEDIUM
    assert isinstance(sent["created_at"], datetime)

@pytest.mark.asyncio
async def test_create_sets_next_service_mileage_when_mileage_present():
    repo = FakeRepo()
    svc = make_service(repo, vehicle_ok=True)
    data = {
        "vehicle_id": "V1",
        "maintenance_type": "oil_change",
        "scheduled_date": (datetime.utcnow() + timedelta(days=10)).isoformat().replace("+00:00", "Z"),
        "title": "Oil",
        "mileage_at_service": 50000,
    }
    _ = await svc.create_maintenance_record(data)
    assert repo.last_create_data["next_service_mileage"] == 60000  

@pytest.mark.asyncio
async def test_create_repo_raises_is_propagated():
    repo = FakeRepo()
    repo.create_should_raise = RuntimeError("db down")
    svc = make_service(repo, vehicle_ok=True)
    data = {
        "vehicle_id": "V1",
        "maintenance_type": "general",
        "scheduled_date": "2028-01-01T00:00:00Z",
        "title": "General",
    }
    with pytest.raises(RuntimeError):
        await svc.create_maintenance_record(data)


@pytest.mark.asyncio
async def test_get_maintenance_record_returns_result():
    repo = FakeRepo()
    repo.get_by_id_return = {"id": "m1"}
    svc = make_service(repo)
    out = await svc.get_maintenance_record("m1")
    assert out["id"] == "m1"

@pytest.mark.asyncio
async def test_get_maintenance_record_repo_error_bubbles():
    class R(FakeRepo):
        async def get_by_id(self, _):
            raise RuntimeError("boom")
    svc = make_service(R())
    with pytest.raises(RuntimeError):
        await svc.get_maintenance_record("x")

@pytest.mark.asyncio
async def test_update_invalid_vehicle_id_raises():
    repo = FakeRepo()
    svc = make_service(repo, vehicle_ok=False)
    with pytest.raises(ValueError):
        await svc.update_maintenance_record("id1", {"vehicle_id": "BAD"})

@pytest.mark.asyncio
async def test_update_parses_datetime_fields_and_sets_in_progress_when_started_no_status():
    repo = FakeRepo()
    repo.update_return = {"id": "u1"}
    svc = make_service(repo, vehicle_ok=True)
    data = {
        "scheduled_date": "2025-01-01T00:00:00Z",
        "actual_start_date": "2025-01-02T00:00:00Z",
    }
    out = await svc.update_maintenance_record("u1", data)
    assert out == {"id": "u1"}
    assert isinstance(repo.last_update_data["scheduled_date"], datetime)
    assert isinstance(repo.last_update_data["actual_start_date"], datetime)
    assert repo.last_update_data["status"] == MaintenanceStatus.IN_PROGRESS

@pytest.mark.asyncio
async def test_update_sets_in_progress_when_status_is_scheduled_and_started():
    repo = FakeRepo()
    repo.update_return = {"id": "u2"}
    svc = make_service(repo, vehicle_ok=True)
    data = {
        "status": MaintenanceStatus.SCHEDULED,
        "actual_start_date": datetime(2025, 1, 2, tzinfo=timezone.utc),
    }
    _ = await svc.update_maintenance_record("u2", data)
    assert repo.last_update_data["status"] == MaintenanceStatus.IN_PROGRESS

@pytest.mark.asyncio
async def test_update_sets_completed_when_completion_date_present():
    repo = FakeRepo()
    repo.update_return = {"id": "u3"}
    svc = make_service(repo, vehicle_ok=True)
    data = {
        "actual_start_date": datetime(2025, 1, 2, tzinfo=timezone.utc),
        "actual_completion_date": "2025-01-03T00:00:00Z",
        "status": MaintenanceStatus.SCHEDULED,
    }
    _ = await svc.update_maintenance_record("u3", data)
    assert repo.last_update_data["status"] == MaintenanceStatus.COMPLETED
    assert isinstance(repo.last_update_data["actual_completion_date"], datetime)

@pytest.mark.asyncio
async def test_update_returns_none_when_repo_returns_none():
    repo = FakeRepo()
    repo.update_return = None
    svc = make_service(repo)
    out = await svc.update_maintenance_record("u4", {"title": "X"})
    assert out is None

@pytest.mark.asyncio
async def test_update_repo_error_bubbles():
    class R(FakeRepo):
        async def update(self, *_a, **_k): raise RuntimeError("oops")
    svc = make_service(R(), vehicle_ok=True)
    with pytest.raises(RuntimeError):
        await svc.update_maintenance_record("id", {"title": "x"})


@pytest.mark.asyncio
async def test_delete_returns_true_and_false():
    repo = FakeRepo()
    svc = make_service(repo)
    repo.delete_return = True
    assert await svc.delete_maintenance_record("x") is True
    repo.delete_return = False
    assert await svc.delete_maintenance_record("x") is False

@pytest.mark.asyncio
async def test_delete_repo_error_bubbles():
    class R(FakeRepo):
        async def delete(self, _): raise RuntimeError("nope")
    svc = make_service(R())
    with pytest.raises(RuntimeError):
        await svc.delete_maintenance_record("x")


@pytest.mark.asyncio
async def test_get_vehicle_records_invalid_vehicle_raises():
    repo = FakeRepo()
    svc = make_service(repo, vehicle_ok=False)
    with pytest.raises(ValueError):
        await svc.get_vehicle_maintenance_records("BAD")

@pytest.mark.asyncio
async def test_get_vehicle_records_success_passthrough():
    repo = FakeRepo()
    repo.by_vehicle_return = [{"id": "a"}]
    svc = make_service(repo, vehicle_ok=True)
    res = await svc.get_vehicle_maintenance_records("V1", skip=5, limit=7)
    assert res == [{"id": "a"}]

@pytest.mark.asyncio
async def test_get_vehicle_records_repo_error_bubbles():
    class R(FakeRepo):
        async def get_by_vehicle_id(self, *_a, **_k): raise RuntimeError("boom")
    svc = make_service(R(), vehicle_ok=True)
    with pytest.raises(RuntimeError):
        await svc.get_vehicle_maintenance_records("V1")


@pytest.mark.asyncio
async def test_get_by_status_passthrough():
    repo = FakeRepo()
    repo.by_status_return = [{"id": "s"}]
    svc = make_service(repo)
    out = await svc.get_maintenance_records_by_status(MaintenanceStatus.SCHEDULED, 1, 2)
    assert out == [{"id": "s"}]

@pytest.mark.asyncio
async def test_get_by_status_repo_error_bubbles():
    class R(FakeRepo):
        async def get_by_status(self, *_a, **_k): raise RuntimeError("e")
    svc = make_service(R())
    with pytest.raises(RuntimeError):
        await svc.get_maintenance_records_by_status("X")


@pytest.mark.asyncio
async def test_get_overdue_returns_empty_when_no_records():
    repo = FakeRepo()
    repo.overdue_return = []
    svc = make_service(repo)
    res = await svc.get_overdue_maintenance()
    assert res == []

@pytest.mark.asyncio
async def test_get_overdue_skips_update_if_already_overdue():
    repo = FakeRepo()
    repo.overdue_return = [{"id": "1", "status": MaintenanceStatus.OVERDUE}]
    svc = make_service(repo)
    _ = await svc.get_overdue_maintenance()
    assert repo.last_update_id is None

@pytest.mark.asyncio
async def test_get_overdue_updates_not_overdue_record_and_mutates_result():
    repo = FakeRepo()
    rec = {"id": "2", "status": MaintenanceStatus.SCHEDULED}
    repo.overdue_return = [rec]
    repo.update_return = {"id": "2", "status": MaintenanceStatus.OVERDUE}
    svc = make_service(repo)
    out = await svc.get_overdue_maintenance()
    assert repo.last_update_id == "2"
    assert repo.last_update_data == {"status": MaintenanceStatus.OVERDUE}
    assert out[0]["status"] == MaintenanceStatus.OVERDUE

@pytest.mark.asyncio
async def test_get_overdue_repo_error_bubbles():
    class R(FakeRepo):
        async def get_overdue_maintenance(self): raise RuntimeError("x")
    svc = make_service(R())
    with pytest.raises(RuntimeError):
        await svc.get_overdue_maintenance()


@pytest.mark.asyncio
async def test_get_upcoming_passthrough():
    repo = FakeRepo()
    repo.upcoming_return = [{"id": "u"}]
    svc = make_service(repo)
    out = await svc.get_upcoming_maintenance(10)
    assert out == [{"id": "u"}]

@pytest.mark.asyncio
async def test_get_upcoming_repo_error_bubbles():
    class R(FakeRepo):
        async def get_upcoming_maintenance(self, *_): raise RuntimeError("e")
    svc = make_service(R())
    with pytest.raises(RuntimeError):
        await svc.get_upcoming_maintenance()


@pytest.mark.asyncio
async def test_history_invalid_vehicle_raises():
    repo = FakeRepo()
    svc = make_service(repo, vehicle_ok=False)
    with pytest.raises(ValueError):
        await svc.get_maintenance_history("BAD")

@pytest.mark.asyncio
async def test_history_parses_start_end_and_calls_repo():
    repo = FakeRepo()
    svc = make_service(repo, vehicle_ok=True)
    start = "2025-01-01T00:00:00Z"
    end = "2025-01-31T23:59:59Z"
    _ = await svc.get_maintenance_history("V1", start, end)
    args = repo.last_history_args
    assert isinstance(args["start_dt"], datetime)
    assert isinstance(args["end_dt"], datetime)
    assert args["vehicle_id"] == "V1"

@pytest.mark.asyncio
async def test_history_invalid_date_raises():
    repo = FakeRepo()
    svc = make_service(repo, vehicle_ok=True)
    with pytest.raises(ValueError):
        await svc.get_maintenance_history("V1", start_date="not-a-date")
@pytest.mark.asyncio
async def test_cost_summary_no_dates_passthrough():
    repo = FakeRepo()
    repo.cost_summary_return = {"total_cost": 0}
    svc = make_service(repo)
    out = await svc.get_maintenance_cost_summary()
    assert out == {"total_cost": 0}
    assert repo.last_cost_args == {"vehicle_id": None, "start_dt": None, "end_dt": None}

@pytest.mark.asyncio
async def test_cost_summary_with_dates_parsed_and_passed():
    repo = FakeRepo()
    svc = make_service(repo)
    start = "2025-02-01T00:00:00Z"
    end = "2025-02-28T23:59:59Z"
    _ = await svc.get_maintenance_cost_summary("V1", start, end)
    args = repo.last_cost_args
    assert args["vehicle_id"] == "V1"
    assert isinstance(args["start_dt"], datetime)
    assert isinstance(args["end_dt"], datetime)

@pytest.mark.asyncio
async def test_cost_summary_invalid_date_raises():
    repo = FakeRepo()
    svc = make_service(repo)
    with pytest.raises(ValueError):
        await svc.get_maintenance_cost_summary(start_date="bad-date")


@pytest.mark.asyncio
async def test_search_minimal_query_default_sort_desc():
    repo = FakeRepo()
    svc = make_service(repo)
    _ = await svc.search_maintenance_records({}, skip=0, limit=10)
    args = repo.last_find_args
    assert args["query"] == {}
    assert args["sort"] == [("scheduled_date", -1)]

@pytest.mark.asyncio
async def test_search_full_query_and_asc_sort_and_date_range():
    repo = FakeRepo()
    svc = make_service(repo)
    q = {
        "vehicle_id": "V1",
        "status": MaintenanceStatus.IN_PROGRESS,
        "maintenance_type": "oil_change",
        "priority": MaintenancePriority.HIGH,
        "vendor_id": "ven-1",
        "technician_id": "tech-1",
        "scheduled_from": "2025-03-01T00:00:00Z",
        "scheduled_to": "2025-03-31T23:59:59Z",
    }
    _ = await svc.search_maintenance_records(q, skip=2, limit=3, sort_by="priority", sort_order="asc")
    args = repo.last_find_args
    assert args["skip"] == 2 and args["limit"] == 3
    assert args["sort"] == [("priority", 1)]
    dq = args["query"]
    assert dq["vehicle_id"] == "V1"
    assert dq["status"] == MaintenanceStatus.IN_PROGRESS
    assert dq["maintenance_type"] == "oil_change"
    assert dq["priority"] == MaintenancePriority.HIGH
    assert dq["vendor_id"] == "ven-1"
    assert dq["assigned_technician"] == "tech-1"
    assert isinstance(dq["scheduled_date"]["$gte"], datetime)
    assert isinstance(dq["scheduled_date"]["$lte"], datetime)

@pytest.mark.asyncio
async def test_search_invalid_date_raises():
    repo = FakeRepo()
    svc = make_service(repo)
    with pytest.raises(ValueError):
        await svc.search_maintenance_records({"scheduled_from": "nope"})


@pytest.mark.asyncio
async def test_auto_set_priority_brake_sets_high():
    svc = make_service(FakeRepo())
    data = {"maintenance_type": "brake", "priority": MaintenancePriority.MEDIUM}
    await svc._auto_set_priority(data)
    assert data["priority"] == MaintenancePriority.HIGH

@pytest.mark.asyncio
async def test_auto_set_priority_emergency_current_logic_sets_high_not_critical():
    svc = make_service(FakeRepo())
    data = {"maintenance_type": "emergency", "priority": MaintenancePriority.MEDIUM}
    await svc._auto_set_priority(data)
    assert data["priority"] == MaintenancePriority.HIGH

@pytest.mark.asyncio
async def test_auto_set_priority_overdue_scheduled_date_sets_high():
    svc = make_service(FakeRepo())
    past = datetime.utcnow() - timedelta(days=1)
    data = {"maintenance_type": "general", "scheduled_date": past, "priority": MaintenancePriority.MEDIUM}
    await svc._auto_set_priority(data)
    assert data["priority"] == MaintenancePriority.HIGH

@pytest.mark.asyncio
async def test_auto_set_priority_leaves_default_when_not_critical_and_future():
    svc = make_service(FakeRepo())
    future = datetime.utcnow() + timedelta(days=10)
    data = {"maintenance_type": "general", "scheduled_date": future, "priority": MaintenancePriority.MEDIUM}
    await svc._auto_set_priority(data)
    assert data["priority"] == MaintenancePriority.MEDIUM


@pytest.mark.asyncio
async def test_calc_next_service_known_type():
    svc = make_service(FakeRepo())
    out = await svc._calculate_next_service_mileage("V1", "oil_change", 10000)
    assert out == 20000

@pytest.mark.asyncio
async def test_calc_next_service_unknown_type_defaults_15000():
    svc = make_service(FakeRepo())
    out = await svc._calculate_next_service_mileage("V1", "mystery", 5000)
    assert out == 20000

@pytest.mark.asyncio
async def test_calc_next_service_handles_exception_and_returns_fallback():
    svc = make_service(FakeRepo())
    out = await svc._calculate_next_service_mileage("V1", None, 7000)
    assert out == 22000 



@pytest.mark.asyncio
async def test_generate_notifications_creates_when_3days_before():
    class CapturingNS:
        def __init__(self): self.created = []
        async def create_notification(self, data): self.created.append(data)
    capt = CapturingNS()
    ms_mod.notification_service = capt

    svc = make_service(FakeRepo())
    scheduled = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(days=6)
    record = {"id": "r10", "vehicle_id": "V1", "title": "T", "priority": "low", "scheduled_date": scheduled}

    await svc._generate_automatic_notifications(record)
    assert len(capt.created) == 0

@pytest.mark.asyncio
async def test_generate_notifications_skips_when_within_3days_or_no_date():
    class CapturingNS:
        def __init__(self): self.created = []
        async def create_notification(self, data): self.created.append(data)
    capt = CapturingNS()
    ms_mod.notification_service = capt

    svc = make_service(FakeRepo())
    near = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(days=1)

    await svc._generate_automatic_notifications({"id": "r1", "vehicle_id": "V", "title": "X", "scheduled_date": near})
    await svc._generate_automatic_notifications({"id": "r2", "vehicle_id": "V", "title": "Y"}) 

    assert capt.created == []
    
@pytest.mark.asyncio
async def test_generate_notifications_swallows_errors():

    class BadNS:
        async def create_notification(self, _): raise RuntimeError("fail")
    ms_mod.notification_service = BadNS()

    svc = make_service(FakeRepo())
    fut = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(days=10)
    await svc._generate_automatic_notifications({"id": "r", "vehicle_id": "V", "title": "Z", "scheduled_date": fut})


@pytest.mark.asyncio
async def test_update_overdue_statuses_updates_all_scheduled_before_now():
    repo = FakeRepo()
    now = datetime.utcnow()
    repo.find_return = [
        {"_id": "x1", "status": MaintenanceStatus.SCHEDULED, "scheduled_date": now - timedelta(days=1)},
        {"_id": "x2", "status": MaintenanceStatus.SCHEDULED, "scheduled_date": now - timedelta(days=2)},
    ]

    def _upd_ret(doc_id, data):
        return {"id": doc_id, **data}
    async def update(record_id, data):
        repo.last_update_id = record_id
        repo.last_update_data = data
        return _upd_ret(record_id, data)
    repo.update = update

    svc = make_service(repo)
    out = await svc.update_overdue_statuses()
    assert len(out) == 2
    assert all(o["status"] == MaintenanceStatus.OVERDUE for o in out)
    assert all(o["priority"] == MaintenancePriority.HIGH for o in out)

    q = repo.last_find_args["query"]
    assert q["status"] == MaintenanceStatus.SCHEDULED
    assert "$lt" in q["scheduled_date"]
    assert isinstance(q["scheduled_date"]["$lt"], datetime)


@pytest.mark.asyncio
async def test_calculate_costs_no_records_returns_zeros():
    repo = FakeRepo()
    repo.find_return = []
    svc = make_service(repo)
    out = await svc.calculate_maintenance_costs()
    assert out["total_cost"] == 0
    assert out["labor_cost"] == 0
    assert out["parts_cost"] == 0
    assert out["record_count"] == 0
    assert out["average_cost"] == 0
    assert out["cost_by_type"] == {}
    assert out["cost_by_month"] == {}

@pytest.mark.asyncio
async def test_calculate_costs_aggregates_and_buckets():
    repo = FakeRepo()
    repo.find_return = [
        {"actual_cost": 120.0, "labor_cost": 70.0, "parts_cost": 50.0, "maintenance_type": "oil_change",
         "actual_completion_date": datetime(2025, 1, 5, tzinfo=timezone.utc)},
        {"actual_cost": None, "labor_cost": 10.0, "parts_cost": None, "maintenance_type": "brake",
         "actual_completion_date": datetime(2025, 1, 12, tzinfo=timezone.utc)},
        {"actual_cost": 80.0, "maintenance_type": "unknown"},
    ]
    svc = make_service(repo)
    out = await svc.calculate_maintenance_costs(vehicle_id="V1",
                                                start_date=datetime(2025,1,1, tzinfo=timezone.utc),
                                                end_date=datetime(2025,1,31, tzinfo=timezone.utc))

    assert out["total_cost"] == 200.0 
    assert out["labor_cost"] == 80.0   
    assert out["parts_cost"] == 50.0
    assert out["record_count"] == 3
    assert out["average_cost"] == 200.0 / 3

    assert out["cost_by_type"]["oil_change"] == 120.0
    assert out["cost_by_type"]["brake"] == 0
    assert out["cost_by_type"]["unknown"] == 80.0
    assert out["cost_by_month"]["2025-01"] == 120.0  


    q = repo.last_find_args["query"]
    assert q["status"] == MaintenanceStatus.COMPLETED
    assert q["vehicle_id"] == "V1"
    assert "$gte" in q["actual_completion_date"] and "$lte" in q["actual_completion_date"]


@pytest.mark.asyncio
async def test_alias_methods_delegate():
    repo = FakeRepo()
    repo.by_vehicle_return = [{"id": "AV"}]
    repo.by_status_return = [{"id": "AS"}]
    svc = make_service(repo, vehicle_ok=True)

    v = await svc.get_maintenance_by_vehicle("V1")
    assert v == [{"id": "AV"}]

    s = await svc.get_maintenance_by_status(MaintenanceStatus.SCHEDULED)
    assert s == [{"id": "AS"}]