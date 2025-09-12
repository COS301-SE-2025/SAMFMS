import sys
import os
import types
import asyncio
from datetime import datetime, timedelta, timezone
import pytest

HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..")),
    os.path.abspath(os.path.join(HERE, "..")),
    os.getcwd(),
]
for p in CANDIDATES:
    if p not in sys.path:
        sys.path.insert(0, p)

if "aio_pika" not in sys.modules:
    aio_pika = types.ModuleType("aio_pika")
    class ExchangeType: DIRECT = "direct"
    class DeliveryMode: PERSISTENT = 2
    class Message:
        def __init__(self, body, delivery_mode=None, content_type=None, headers=None):
            self.body = body
            self.delivery_mode = delivery_mode
            self.content_type = content_type
            self.headers = headers
    class _FakeExchange:
        def __init__(self, name):
            self.name = name
            self.published = []
        async def publish(self, message, routing_key):
            self.published.append((message, routing_key))
    class _FakeChannel:
        async def declare_exchange(self, name, _type, durable=True):
            return _FakeExchange(name)
    class _FakeConnection:
        def __init__(self):
            self.is_closed = False
            self._channel = _FakeChannel()
        async def channel(self): return self._channel
        async def close(self): self.is_closed = True
    async def connect_robust(url=None, heartbeat=None, blocked_connection_timeout=None):
        return _FakeConnection()
    aio_pika.ExchangeType = ExchangeType
    aio_pika.DeliveryMode = DeliveryMode
    aio_pika.Message = Message
    aio_pika.connect_robust = connect_robust
    sys.modules["aio_pika"] = aio_pika

if "config" not in sys.modules:
    sys.modules["config"] = types.ModuleType("config")
if "config.rabbitmq_config" not in sys.modules:
    rmod = types.ModuleType("config.rabbitmq_config")
    class RabbitMQConfig:
        EXCHANGE_NAMES = {"requests": "maintenance_requests", "responses": "maintenance_responses"}
        QUEUE_NAMES = {"maintenance": "maintenance.queue"}
        ROUTING_KEYS = {"core_responses": "core.responses"}
        CONNECTION_PARAMS = {"heartbeat": 60, "blocked_connection_timeout": 30}
        REQUEST_TIMEOUTS = {"default_request_timeout": 0.25}
        def get_rabbitmq_url(self): return "amqp://guest:guest@localhost/"
    def json_serializer(obj):
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        raise TypeError
    rmod.RabbitMQConfig = RabbitMQConfig
    rmod.json_serializer = json_serializer
    sys.modules["config.rabbitmq_config"] = rmod

if "schemas" not in sys.modules:
    sys.modules["schemas"] = types.ModuleType("schemas")
if "schemas.responses" not in sys.modules:
    sresp = types.ModuleType("schemas.responses")
    class _Wrap:
        def __init__(self, d): self._d = d
        def model_dump(self): return self._d
    class ResponseBuilder:
        @staticmethod
        def success(data=None, message=""): return _Wrap({"status": "success", "data": data or {}, "message": message})
        @staticmethod
        def error(error="Error", message=""): return _Wrap({"status": "error", "error": error, "message": message})
    sresp.ResponseBuilder = ResponseBuilder
    sys.modules["schemas.responses"] = sresp
if "schemas.error_responses" not in sys.modules:
    serr = types.ModuleType("schemas.error_responses")
    class MaintenanceErrorBuilder:
        @staticmethod
        def internal_error(message="", error_details=None, correlation_id=None):
            return {"error": {"message": message, "details": error_details or {}}, "correlation_id": correlation_id}
    serr.MaintenanceErrorBuilder = MaintenanceErrorBuilder
    sys.modules["schemas.error_responses"] = serr

if "repositories" not in sys.modules:
    sys.modules["repositories"] = types.ModuleType("repositories")
if "repositories.database" not in sys.modules:
    sys.modules["repositories.database"] = types.ModuleType("repositories.database")
if "repositories.database.db_manager" not in sys.modules:
    dbm = types.ModuleType("repositories.database.db_manager")
    class _Admin:
        async def command(self, cmd): return {"ok": 1}
    class _Client:
        def __init__(self): self.admin = _Admin()
    dbm.client = _Client()
    sys.modules["repositories.database.db_manager"] = dbm

if "repositories.repositories" not in sys.modules:
    rrs = types.ModuleType("repositories.repositories")
    class MaintenanceRecordsRepository:
        async def count(self, _q): return 0
        async def find(self, *_a, **_k): return []
    class MaintenanceSchedulesRepository:
        async def count(self, _q): return 0
        async def find(self, *_a, **_k): return []
    rrs.MaintenanceRecordsRepository = MaintenanceRecordsRepository
    rrs.MaintenanceSchedulesRepository = MaintenanceSchedulesRepository
    sys.modules["repositories.repositories"] = rrs

if "services" not in sys.modules:
    sys.modules["services"] = types.ModuleType("services")

def _ensure_service_module(name):
    full = f"services.{name}"
    if full not in sys.modules:
        sys.modules[full] = types.ModuleType(full)
    return sys.modules[full]

msvc = _ensure_service_module("maintenance_service")
class _MaintSvc:
    async def get_overdue_maintenance(self): return []
    async def get_upcoming_maintenance(self, days): return []
    async def get_maintenance_record(self, rid): return None
    async def create_maintenance_record(self, data): return {"id": "newrec", **data}
    async def update_maintenance_record(self, rid, data): return None
    async def delete_maintenance_record(self, rid): return False
    async def search_maintenance_records(self, query, skip=0, limit=100, sort_by="scheduled_date", sort_order="desc"): return []
    async def get_all_maintenance_records(self, skip=0, limit=100): return []
    async def get_maintenance_cost_summary(self, vehicle_id=None, start_date=None, end_date=None): return {"total_cost": 0}
maintenance_records_service = _MaintSvc()
msvc.maintenance_records_service = maintenance_records_service

ssch = _ensure_service_module("maintenance_schedules_service")
class _SchedSvc:
    async def get_due_schedules(self): return []
    async def get_active_schedules(self): return []
    async def get_maintenance_schedule(self, sid): return None
    async def get_vehicle_maintenance_schedules(self, vid): return []
    async def create_maintenance_schedule(self, data): return {"id": "newsched", **data}
    async def update_maintenance_schedule(self, sid, data): return None
    async def delete_maintenance_schedule(self, sid): return False
maintenance_schedules_service = _SchedSvc()
ssch.maintenance_schedules_service = maintenance_schedules_service

lmod = _ensure_service_module("license_service")
class _LicSvc:
    async def get_entity_licenses(self, eid, etype): return []
    async def get_licenses_by_type(self, t): return []
    async def get_all_licenses(self, skip=0, limit=100): return []
    async def get_license_record(self, lid): return None
    async def create_license_record(self, data): return {"id": "newlic", **data}
    async def update_license_record(self, lid, data): return None
    async def delete_license_record(self, lid): return False
license_service = _LicSvc()
lmod.license_service = license_service

amod = _ensure_service_module("analytics_service")
class _AnalyticsSvc:
    async def get_cost_analytics(self, *_a, **_k): return {"time_series": [], "summary": {}}
    async def get_cost_by_month_and_type(self, *_a, **_k): return {}
    async def get_maintenance_records_by_type(self, *_a, **_k): return [{"maintenance_type": "oil_change", "total_cost": 0}]
maintenance_analytics_service = _AnalyticsSvc()
amod.maintenance_analytics_service = maintenance_analytics_service

import importlib
try:
    rc_mod = importlib.import_module("services.request_consumer")
except Exception:
    rc_mod = importlib.import_module("request_consumer")

ServiceRequestConsumer = rc_mod.ServiceRequestConsumer

def make_service(db_ok=True):
    svc = ServiceRequestConsumer()
    async def ok(): return db_ok
    svc._check_database_connectivity = ok
    return svc

def status_str(val):
    return getattr(val, "value", val)

@pytest.mark.asyncio
async def test_health_get_ok():
    svc = make_service()
    out = await svc._handle_health_request("GET", {})
    assert status_str(out["status"]) == "healthy"
    assert out["service"] == "maintenance"

@pytest.mark.asyncio
async def test_health_bad_method_raises():
    svc = make_service()
    with pytest.raises(ValueError):
        await svc._handle_health_request("POST", {})

@pytest.mark.asyncio
async def test_status_get_ok():
    svc = make_service()
    out = await svc._handle_status_request("GET", {})
    assert out["status"] == "operational"
    assert out["service"] == "maintenance"

@pytest.mark.asyncio
async def test_docs_get_ok():
    svc = make_service()
    out = await svc._handle_docs_request("GET", {})
    assert out["openapi_url"] == "/openapi.json"

@pytest.mark.asyncio
async def test_metrics_get_ok():
    svc = make_service()
    out = await svc._handle_metrics_request("GET", {})
    assert out["service"] == "maintenance"

@pytest.mark.asyncio
async def test_records_db_unavailable_returns_error():
    svc = make_service(db_ok=False)
    out = await svc._handle_maintenance_records_request("GET", {"endpoint": "records/overdue"})
    assert status_str(out["status"]) == "error"
    assert out["error"] == "DatabaseUnavailable"

@pytest.mark.asyncio
async def test_records_get_overdue_success():
    svc = make_service()
    async def fake_overdue(): return [{"id": "r1"}, {"id": "r2"}]
    msvc.maintenance_records_service.get_overdue_maintenance = fake_overdue
    out = await svc._handle_maintenance_records_request("GET", {"endpoint": "records/overdue", "data": {}})
    assert status_str(out["status"]) == "success"
    assert out["data"]["filter"] == "overdue"
    assert len(out["data"]["maintenance_records"]) == 2

@pytest.mark.asyncio
async def test_records_get_upcoming_days_variants():
    svc = make_service()
    captured = {"days": None}
    async def fake_upcoming(days):
        captured["days"] = days
        return [{"id": "u"}]
    msvc.maintenance_records_service.get_upcoming_maintenance = fake_upcoming
    out = await svc._handle_maintenance_records_request("GET", {"endpoint": "records/upcoming", "data": {"days": 10}})
    assert captured["days"] == 10 and out["data"]["days_ahead"] == 10
    out = await svc._handle_maintenance_records_request("GET", {"endpoint": "records/upcoming", "data": {"days": -5}})
    assert captured["days"] == 1 and out["data"]["days_ahead"] == 1
    out = await svc._handle_maintenance_records_request("GET", {"endpoint": "records/upcoming", "data": {"days": 999}})
    assert captured["days"] == 365 and out["data"]["days_ahead"] == 365
    out = await svc._handle_maintenance_records_request("GET", {"endpoint": "records/upcoming", "data": {"days": "nope"}})
    assert captured["days"] == 7 and out["data"]["days_ahead"] == 7

@pytest.mark.asyncio
async def test_records_get_by_id_found_and_not_found():
    svc = make_service()
    async def get_one(rec_id): return {"id": rec_id}
    msvc.maintenance_records_service.get_maintenance_record = get_one
    out = await svc._handle_maintenance_records_request("GET", {"endpoint": "records/abc123", "data": {}})
    assert status_str(out["status"]) == "success" and out["data"]["maintenance_record"]["id"] == "abc123"
    async def get_none(rec_id): return None
    msvc.maintenance_records_service.get_maintenance_record = get_none
    out = await svc._handle_maintenance_records_request("GET", {"endpoint": "records/missing", "data": {}})
    assert status_str(out["status"]) == "error" and out["error"] == "NotFound"

@pytest.mark.asyncio
async def test_records_get_list_parses_skip_limit_and_passes_to_search():
    svc = make_service()
    captured = {}
    async def search(query, skip=0, limit=100, sort_by="scheduled_date", sort_order="desc"):
        captured.update({"query": dict(query), "skip": skip, "limit": limit, "sort_by": sort_by, "sort_order": sort_order})
        return [{"id": "x"}]
    msvc.maintenance_records_service.search_maintenance_records = search
    out = await svc._handle_maintenance_records_request("GET", {"endpoint": "records", "data": {"skip": 5, "limit": 3, "sort_by": "priority", "sort_order": "asc"}})
    assert status_str(out["status"]) == "success"
    assert out["data"]["pagination"]["skip"] == 5 and out["data"]["pagination"]["limit"] == 3
    assert captured["skip"] == 5 and captured["limit"] == 3 and captured["sort_by"] == "priority" and captured["sort_order"] == "asc"

@pytest.mark.asyncio
async def test_records_get_list_bad_numbers_fallbacks():
    svc = make_service()
    out = await svc._handle_maintenance_records_request("GET", {"endpoint": "records", "data": {"skip": "x", "limit": "y"}})
    assert status_str(out["status"]) == "success"
    assert out["data"]["pagination"]["skip"] == 0
    assert out["data"]["pagination"]["limit"] == 100

@pytest.mark.asyncio
async def test_records_post_missing_data_error():
    svc = make_service()
    out = await svc._handle_maintenance_records_request("POST", {"endpoint": "records", "data": {}})
    assert status_str(out["status"]) == "error"
    assert out["message"].startswith("Failed to process")

@pytest.mark.asyncio
async def test_records_post_success():
    svc = make_service()
    async def create(d): return {"id": "n1", **d}
    msvc.maintenance_records_service.create_maintenance_record = create
    out = await svc._handle_maintenance_records_request("POST", {"endpoint": "records", "data": {"vehicle_id": "V"}})
    assert status_str(out["status"]) == "success" and out["data"]["maintenance_record"]["id"] == "n1"

@pytest.mark.asyncio
async def test_records_put_missing_id_or_data_error():
    svc = make_service()
    out = await svc._handle_maintenance_records_request("PUT", {"endpoint": "records", "data": {"x": 1}})
    assert status_str(out["status"]) == "error"
    out = await svc._handle_maintenance_records_request("PUT", {"endpoint": "records/abc", "data": {}})
    assert status_str(out["status"]) == "error"

@pytest.mark.asyncio
async def test_records_put_found_and_not_found():
    svc = make_service()
    async def upd(_id, d): return {"id": _id, **d}
    msvc.maintenance_records_service.update_maintenance_record = upd
    out = await svc._handle_maintenance_records_request("PUT", {"endpoint": "records/r1", "data": {"title": "T"}})
    assert status_str(out["status"]) == "success"
    async def upd_none(_id, d): return None
    msvc.maintenance_records_service.update_maintenance_record = upd_none
    out = await svc._handle_maintenance_records_request("PUT", {"endpoint": "records/r2", "data": {"title": "T"}})
    assert status_str(out["status"]) == "error" and out["error"] == "NotFound"

@pytest.mark.asyncio
async def test_records_delete_missing_id_true_false():
    svc = make_service()
    out = await svc._handle_maintenance_records_request("DELETE", {"endpoint": "records", "data": {}})
    assert status_str(out["status"]) == "error"
    async def del_true(_id): return True
    async def del_false(_id): return False
    msvc.maintenance_records_service.delete_maintenance_record = del_true
    out = await svc._handle_maintenance_records_request("DELETE", {"endpoint": "records/r3", "data": {}})
    assert status_str(out["status"]) == "success" and out["data"]["deleted"] is True
    msvc.maintenance_records_service.delete_maintenance_record = del_false
    out = await svc._handle_maintenance_records_request("DELETE", {"endpoint": "records/r4", "data": {}})
    assert status_str(out["status"]) == "error" and out["error"] == "NotFound"

@pytest.mark.asyncio
async def test_schedules_db_unavailable():
    svc = make_service(db_ok=False)
    out = await svc._handle_schedules_request("GET", {"endpoint": "schedules/active"})
    assert status_str(out["status"]) == "error" and out["error"] == "DatabaseUnavailable"

@pytest.mark.asyncio
async def test_schedules_get_upcoming_and_active():
    svc = make_service()
    async def due(): return [{"id": "s1"}]
    async def active(): return [{"id": "a1"}]
    ssch.maintenance_schedules_service.get_due_schedules = due
    ssch.maintenance_schedules_service.get_active_schedules = active
    out = await svc._handle_schedules_request("GET", {"endpoint": "schedules/upcoming", "data": {}})
    assert status_str(out["status"]) == "success" and out["data"]["total"] == 1
    out = await svc._handle_schedules_request("GET", {"endpoint": "schedules/active", "data": {}})
    assert status_str(out["status"]) == "success" and out["data"]["schedules"][0]["id"] == "a1"

@pytest.mark.asyncio
async def test_schedules_get_by_id_found_not_found():
    svc = make_service()
    async def get_one(_id): return {"id": _id}
    async def get_none(_id): return None
    ssch.maintenance_schedules_service.get_maintenance_schedule = get_one
    out = await svc._handle_schedules_request("GET", {"endpoint": "schedules/xyz", "data": {}})
    assert status_str(out["status"]) == "success" and out["data"]["schedule"]["id"] == "xyz"
    ssch.maintenance_schedules_service.get_maintenance_schedule = get_none
    out = await svc._handle_schedules_request("GET", {"endpoint": "schedules/none", "data": {}})
    assert status_str(out["status"]) == "error" and out["error"] == "NotFound"

@pytest.mark.asyncio
async def test_schedules_get_list_by_vehicle_or_default():
    svc = make_service()
    async def by_vehicle(_vid): return [{"id": "v1"}]
    async def active(): return [{"id": "a1"}]
    ssch.maintenance_schedules_service.get_vehicle_maintenance_schedules = by_vehicle
    ssch.maintenance_schedules_service.get_active_schedules = active
    out = await svc._handle_schedules_request("GET", {"endpoint": "schedules", "data": {"vehicle_id": "V"}})
    assert status_str(out["status"]) == "success" and out["data"]["filters"]["vehicle_id"] == "V"
    out = await svc._handle_schedules_request("GET", {"endpoint": "schedules", "data": {}})
    assert status_str(out["status"]) == "success" and out["data"]["schedules"][0]["id"] == "a1"

@pytest.mark.asyncio
async def test_schedules_post_put_delete_paths():
    svc = make_service()
    async def create(d): return {"id": "ns", **d}
    async def update(i, d): return {"id": i, **d}
    async def update_none(i, d): return None
    async def delete_true(i): return True
    async def delete_false(i): return False
    ssch.maintenance_schedules_service.create_maintenance_schedule = create
    ssch.maintenance_schedules_service.update_maintenance_schedule = update
    ssch.maintenance_schedules_service.delete_maintenance_schedule = delete_true
    out = await svc._handle_schedules_request("POST", {"endpoint": "schedules", "data": {"title": "T"}})
    assert status_str(out["status"]) == "success"
    out = await svc._handle_schedules_request("PUT", {"endpoint": "schedules/s1", "data": {"x": 1}})
    assert status_str(out["status"]) == "success"
    ssch.maintenance_schedules_service.update_maintenance_schedule = update_none
    out = await svc._handle_schedules_request("PUT", {"endpoint": "schedules/s2", "data": {"x": 1}})
    assert status_str(out["status"]) == "error" and out["error"] == "NotFound"
    ssch.maintenance_schedules_service.delete_maintenance_schedule = delete_false
    out = await svc._handle_schedules_request("DELETE", {"endpoint": "schedules/s3", "data": {}})
    assert status_str(out["status"]) == "error" and out["error"] == "NotFound"

@pytest.mark.asyncio
async def test_license_db_unavailable():
    svc = make_service(db_ok=False)
    out = await svc._handle_license_request("GET", {"endpoint": "licenses", "data": {}})
    assert status_str(out["status"]) == "error" and out["error"] == "DatabaseUnavailable"

@pytest.mark.asyncio
async def test_license_get_listing_all_type_vehicle_and_fallback():
    svc = make_service()
    async def all_licenses(skip=0, limit=100):
        return [{"id": "l1", "license_type": "roadworthy", "entity_id": "V", "expiry_date": datetime.now().date() + timedelta(days=60), "is_active": True}]
    lmod.license_service.get_all_licenses = all_licenses
    out = await svc._handle_license_request("GET", {"endpoint": "licenses", "data": {"skip": 0, "limit": 10}})
    assert status_str(out["status"]) == "success" and out["data"]["total"] == 1
    async def by_type(t):
        return [{"id": "l2", "license_type": t, "entity_id": "V", "expiry_date": datetime.now().date() + timedelta(days=10), "is_active": True}]
    lmod.license_service.get_licenses_by_type = by_type
    out = await svc._handle_license_request("GET", {"endpoint": "licenses", "data": {"type": "inspections"}})
    assert status_str(out["status"]) == "success" and out["data"]["summary"]["expiring_soon"] >= 0
    async def by_vehicle(eid, etype):
        return [{"id": "l3", "entity_id": eid, "license_type": "permits", "expiry_date": datetime.now().date() - timedelta(days=2), "is_active": True}]
    lmod.license_service.get_entity_licenses = by_vehicle
    out = await svc._handle_license_request("GET", {"endpoint": "licenses", "data": {"vehicle_id": "V9"}})
    assert status_str(out["status"]) == "success" and out["data"]["summary"]["expired"] >= 0
    async def boom(*_a, **_k): raise RuntimeError("x")
    lmod.license_service.get_all_licenses = boom
    out = await svc._handle_license_request("GET", {"endpoint": "licenses", "data": {}})
    assert status_str(out["status"]) == "success" and out["data"]["total"] == 0 and out["data"]["summary"]["compliance_rate"] == 100

@pytest.mark.asyncio
async def test_license_get_single_found_notfound_and_error():
    svc = make_service()
    async def get_one(lid):
        return {"id": lid, "entity_id": "V", "license_type": "roadworthy", "expiry_date": datetime.now().date() + timedelta(days=1), "is_active": True}
    async def get_none(lid): return None
    lmod.license_service.get_license_record = get_one
    out = await svc._handle_license_request("GET", {"endpoint": "licenses/item", "data": {"license_id": "L1"}})
    assert status_str(out["status"]) == "success" and out["data"]["license"]["id"] == "L1"
    lmod.license_service.get_license_record = get_none
    out = await svc._handle_license_request("GET", {"endpoint": "licenses/item", "data": {"license_id": "L2"}})
    assert status_str(out["status"]) == "error" and out["error"] == "NotFound"
    async def boom(lid): raise RuntimeError("X")
    lmod.license_service.get_license_record = boom
    out = await svc._handle_license_request("GET", {"endpoint": "licenses/item", "data": {"license_id": "L3"}})
    assert status_str(out["status"]) == "error" and out["error"] == "FetchError"

@pytest.mark.asyncio
async def test_license_post_validation_success_and_error():
    svc = make_service()
    out = await svc._handle_license_request("POST", {"endpoint": "licenses", "data": {"vehicle_id": "V"}})
    assert status_str(out["status"]) == "error" and out["message"].startswith("Required field")
    async def create(d): return {"id": "NL", **d}
    lmod.license_service.create_license_record = create
    data = {"license_type": "roadworthy", "vehicle_id": "V", "license_number": "123", "issue_date": "2025-01-01", "expiry_date": "2025-12-31"}
    out = await svc._handle_license_request("POST", {"endpoint": "licenses", "data": data})
    assert status_str(out["status"]) == "success" and out["data"]["license"]["id"] == "NL"
    async def boom(d): raise RuntimeError("fail")
    lmod.license_service.create_license_record = boom
    out = await svc._handle_license_request("POST", {"endpoint": "licenses", "data": data})
    assert status_str(out["status"]) == "error" and out["error"] == "CreationError"

@pytest.mark.asyncio
async def test_license_put_delete_flows():
    svc = make_service()
    out = await svc._handle_license_request("PUT", {"endpoint": "licenses", "data": {"updates": {"x": 1}}})
    assert status_str(out["status"]) == "error" and out["message"].startswith("License ID is required")
    async def upd(lid, u): return {"id": lid, **u}
    lmod.license_service.update_license_record = upd
    out = await svc._handle_license_request("PUT", {"endpoint": "licenses", "data": {"license_id": "L1", "updates": {"x": 1}}})
    assert status_str(out["status"]) == "success"
    async def upd_none(lid, u): return None
    lmod.license_service.update_license_record = upd_none
    out = await svc._handle_license_request("PUT", {"endpoint": "licenses", "data": {"license_id": "L2", "updates": {"x": 1}}})
    assert status_str(out["status"]) == "error" and out["error"] == "NotFound"
    async def upd_err(lid, u): raise RuntimeError("e")
    lmod.license_service.update_license_record = upd_err
    out = await svc._handle_license_request("PUT", {"endpoint": "licenses", "data": {"license_id": "L3", "updates": {"x": 1}}})
    assert status_str(out["status"]) == "error" and out["error"] == "UpdateError"
    out = await svc._handle_license_request("DELETE", {"endpoint": "licenses", "data": {}})
    assert status_str(out["status"]) == "error" and out["message"].startswith("License ID is required")
    async def del_true(lid): return True
    async def del_false(lid): return False
    lmod.license_service.delete_license_record = del_true
    out = await svc._handle_license_request("DELETE", {"endpoint": "licenses", "data": {"license_id": "L4"}})
    assert status_str(out["status"]) == "success" and out["data"]["deleted"] is True
    lmod.license_service.delete_license_record = del_false
    out = await svc._handle_license_request("DELETE", {"endpoint": "licenses", "data": {"license_id": "L5"}})
    assert status_str(out["status"]) == "error" and out["error"] == "NotFound"
    async def del_err(lid): raise RuntimeError("e")
    lmod.license_service.delete_license_record = del_err
    out = await svc._handle_license_request("DELETE", {"endpoint": "licenses", "data": {"license_id": "L6"}})
    assert status_str(out["status"]) == "error" and out["error"] == "DeletionError"

@pytest.mark.asyncio
async def test_analytics_db_unavailable():
    svc = make_service(db_ok=False)
    out = await svc._handle_analytics_request("GET", {"endpoint": "analytics/dashboard", "data": {}})
    assert status_str(out["status"]) == "error" and out["error"] == "DatabaseUnavailable"

@pytest.mark.asyncio
async def test_analytics_dashboard_success():
    svc = make_service()
    import repositories.repositories as rrs
    class MR(rrs.MaintenanceRecordsRepository):
        async def count(self, q): return 3
        async def find(self, query=None, skip=0, limit=10, sort=None): return [{"id": "r", "created_at": datetime.now(timezone.utc)}]
    class MS(rrs.MaintenanceSchedulesRepository):
        async def count(self, q): return 2
    rrs.MaintenanceRecordsRepository = MR
    rrs.MaintenanceSchedulesRepository = MS
    out = await svc._handle_analytics_request("GET", {"endpoint": "analytics/dashboard", "data": {}})
    assert status_str(out["status"]) == "success"
    assert "analytics" in out["data"]

@pytest.mark.asyncio
async def test_analytics_dashboard_fallback_on_error():
    svc = make_service()
    import repositories.repositories as rrs
    class MR(rrs.MaintenanceRecordsRepository):
        async def count(self, q): raise RuntimeError("boom")
    rrs.MaintenanceRecordsRepository = MR
    out = await svc._handle_analytics_request("GET", {"endpoint": "analytics/dashboard", "data": {}})
    assert status_str(out["status"]) == "success" and "analytics" in out["data"]


@pytest.mark.asyncio
async def test_analytics_general_success_and_fallback():
    svc = make_service()
    out = await svc._handle_analytics_request("GET", {"endpoint": "analytics", "data": {}})
    assert status_str(out["status"]) == "success" and "analytics" in out["data"]
    import repositories.repositories as rrs
    class MS(rrs.MaintenanceSchedulesRepository):
        async def find(self, *_a, **_k): raise RuntimeError("e")
    rrs.MaintenanceSchedulesRepository = MS
    out = await svc._handle_analytics_request("GET", {"endpoint": "analytics", "data": {}})
    assert status_str(out["status"]) == "success" and "analytics" in out["data"]

@pytest.mark.asyncio
async def test_notifications_db_unavailable():
    svc = make_service(db_ok=False)
    out = await svc._handle_notification_request("GET", {"endpoint": "notifications", "data": {}})
    assert status_str(out["status"]) == "error" and out["error"] == "DatabaseUnavailable"

@pytest.mark.asyncio
async def test_notifications_compose_and_filters_and_pagination():
    svc = make_service()
    async def overdue():
        return [{"id": "o1", "vehicle_id": "V1", "maintenance_type": "oil_change", "due_date": datetime.now().isoformat()}]
    async def upcoming(_days):
        return [{"id": "u1", "vehicle_id": "V2", "maintenance_type": "brake"}]
    async def cost_summary(): return {"total_cost": 5000, "average_cost": 100}
    msvc.maintenance_records_service.get_overdue_maintenance = overdue
    msvc.maintenance_records_service.get_upcoming_maintenance = upcoming
    msvc.maintenance_records_service.get_maintenance_cost_summary = cost_summary
    out = await svc._handle_notification_request("GET", {"endpoint": "notifications", "data": {"skip": 0, "limit": 10}})
    assert status_str(out["status"]) == "success" and out["data"]["total"] >= 1
    out = await svc._handle_notification_request("GET", {"endpoint": "notifications", "data": {"type": "maintenance_upcoming", "skip": 0, "limit": 10}})
    assert all(n["type"] == "maintenance_upcoming" for n in out["data"]["notifications"])

@pytest.mark.asyncio
async def test_notifications_high_cost_alert_and_exception_fallback():
    svc = make_service()
    async def cost_summary(): return {"total_cost": 20001, "average_cost": 100}
    async def overdue(): return []
    async def upcoming(_): return []
    msvc.maintenance_records_service.get_overdue_maintenance = overdue
    msvc.maintenance_records_service.get_upcoming_maintenance = upcoming
    msvc.maintenance_records_service.get_maintenance_cost_summary = cost_summary
    out = await svc._handle_notification_request("GET", {"endpoint": "notifications", "data": {"skip": 0, "limit": 10}})
    assert any(n["type"] == "cost_alert" for n in out["data"]["notifications"])
    async def boom(): raise RuntimeError("e")
    msvc.maintenance_records_service.get_overdue_maintenance = boom
    out = await svc._handle_notification_request("GET", {"endpoint": "notifications", "data": {"skip": 0, "limit": 10}})
    assert status_str(out["status"]) == "success" and out["data"]["total"] == 0

@pytest.mark.asyncio
async def test_notifications_post_and_put_and_unsupported():
    svc = make_service()
    out = await svc._handle_notification_request("POST", {"endpoint": "notifications", "data": {}})
    assert status_str(out["status"]) == "error"
    out = await svc._handle_notification_request("POST", {"endpoint": "notifications", "data": {"notification_id": "N1", "action": "mark_read"}})
    assert status_str(out["status"]) == "success" and out["data"]["notification_id"] == "N1"
    out = await svc._handle_notification_request("PUT", {"endpoint": "notifications", "data": {"user_id": "U1", "preferences": {"email": True}}})
    assert status_str(out["status"]) == "success" and out["data"]["user_id"] == "U1"

@pytest.mark.asyncio
async def test_vendors_db_unavailable():
    svc = make_service(db_ok=False)
    out = await svc._handle_vendor_request("GET", {"endpoint": "vendors", "data": {}})
    assert status_str(out["status"]) == "error" and out["error"] == "DatabaseUnavailable"

@pytest.mark.asyncio
async def test_vendors_listing_success_and_filters_and_fallback():
    svc = make_service()
    async def all_records(skip=0, limit=100):
        return [{"maintenance_type": "oil_change", "cost": 100}, {"maintenance_type": "brake_service", "cost": 200}]
    msvc.maintenance_records_service.get_all_maintenance_records = all_records
    out = await svc._handle_vendor_request("GET", {"endpoint": "vendors", "data": {"skip": 0, "limit": 5}})
    assert status_str(out["status"]) == "success" and out["data"]["total"] >= 1
    out = await svc._handle_vendor_request("GET", {"endpoint": "vendors", "data": {"type": "maintenance_service", "status": "active", "skip": 0, "limit": 5}})
    assert status_str(out["status"]) == "success" and out["data"]["total"] >= 1
    async def boom(skip=0, limit=100): raise RuntimeError("e")
    msvc.maintenance_records_service.get_all_maintenance_records = boom
    out = await svc._handle_vendor_request("GET", {"endpoint": "vendors", "data": {}})
    assert status_str(out["status"]) == "success" and out["data"]["total"] == 0

@pytest.mark.asyncio
async def test_vendor_single_and_post_put_delete():
    svc = make_service()
    out = await svc._handle_vendor_request("GET", {"endpoint": "vendors/item", "data": {"vendor_id": "vendor_1"}})
    assert status_str(out["status"]) == "success" and out["data"]["vendor"]["id"] == "vendor_1"
    out = await svc._handle_vendor_request("GET", {"endpoint": "vendors/item", "data": {}})
    assert status_str(out["status"]) == "error"
    out = await svc._handle_vendor_request("POST", {"endpoint": "vendors", "data": {"name": "ACME"}})
    assert status_str(out["status"]) == "success" and out["data"]["vendor"]["id"].startswith("vendor_")
    out = await svc._handle_vendor_request("PUT", {"endpoint": "vendors", "data": {"vendor_id": "vendor_1", "updates": {"rating": 5}}})
    assert status_str(out["status"]) == "success" and out["data"]["vendor"]["id"] == "vendor_1"
    out = await svc._handle_vendor_request("DELETE", {"endpoint": "vendors", "data": {"vendor_id": "vendor_1"}})
    assert status_str(out["status"]) == "success" and out["data"]["deleted"] is True

@pytest.mark.asyncio
async def test_handle_request_handler_exception_still_sends_error(monkeypatch):
    svc = make_service()
    sent = {"payload": None}
    async def fake_send(cid, payload): sent["payload"] = (cid, payload)
    monkeypatch.setattr(svc, "_send_response", fake_send)
    async def passthrough(coro, timeout): return await coro
    monkeypatch.setattr(asyncio, "wait_for", passthrough)
    async def boom(*_a, **_k): raise RuntimeError("kaboom")
    monkeypatch.setattr(svc, "_route_request", boom)
    class Msg:
        def __init__(self):
            self.body = b'{"correlation_id":"REQ1","method":"GET","endpoint":"health","user_context":{}}'
        class _Ctx:
            async def __aenter__(self): return self
            async def __aexit__(self, *exc): return False
        def process(self, requeue=False): return self._Ctx()
    await svc.handle_request(Msg())
    assert sent["payload"][0] == "REQ1"
    assert "error" in sent["payload"][1]
