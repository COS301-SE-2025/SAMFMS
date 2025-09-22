import sys, os, types, importlib.util, pytest
from datetime import datetime

HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..", "services", "fuel_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "services", "fuel_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "management", "services", "fuel_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "services", "fuel_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "fuel_service.py")),
]

def ensure_mod(name):
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)
    return sys.modules[name]

repositories = ensure_mod("repositories")
repos_pkg = ensure_mod("repositories.repositories")
events = ensure_mod("events")
events_pub = ensure_mod("events.publisher")
schemas = ensure_mod("schemas")
schemas_requests = ensure_mod("schemas.requests")
schemas_entities = ensure_mod("schemas.entities")

# Publisher stub
if not hasattr(events_pub, "event_publisher"):
    class _EP:
        def __init__(self): self.events = []
        async def publish_event(self, event): self.events.append(event)
    events_pub.event_publisher = _EP()

# Schemas stubs (additive; don't clobber if already present)
if not hasattr(schemas_requests, "FuelRecordCreateRequest"):
    class FuelRecordCreateRequest:
        def __init__(self, **data):
            self._data = dict(data)
            for k, v in data.items(): setattr(self, k, v)
        def dict(self): return dict(self._data)
    schemas_requests.FuelRecordCreateRequest = FuelRecordCreateRequest

if not hasattr(schemas_requests, "FuelRecordUpdateRequest"):
    class FuelRecordUpdateRequest:
        def __init__(self, **data):
            self._data = dict(data)
            for k, v in data.items(): setattr(self, k, v)
        def dict(self, exclude_none=False):
            if not exclude_none: return dict(self._data)
            return {k: v for k, v in self._data.items() if v is not None}
    schemas_requests.FuelRecordUpdateRequest = FuelRecordUpdateRequest

if not hasattr(schemas_entities, "FuelRecord"):
    class FuelRecord: ...
    schemas_entities.FuelRecord = FuelRecord

# Repository stubs
class _FuelRepo:
    def __init__(self):
        self.created = []
        self.updated = []
        self.deleted = []
        self.by_id = {}
        self.by_vehicle = {}
        self.by_driver = {}
        self.next_id = "fr1"
        self.raise_on_create = None
        self.raise_on_get = None
        self.raise_on_vehicle = None
        self.raise_on_driver = None
        self.raise_on_update = None
        self.raise_on_delete = None
        self.analytics = {"total_liters": 0, "total_cost": 0}
        self.raise_on_analytics = None
    async def create(self, data):
        if self.raise_on_create: raise self.raise_on_create
        self.created.append(data)
        self.by_id[self.next_id] = {"id": self.next_id, **data}
        rid = self.next_id
        self.next_id = f"fr{int(self.next_id[2:])+1}" if self.next_id.startswith("fr") else "fr2"
        return rid
    async def get_by_id(self, rid):
        if self.raise_on_get: raise self.raise_on_get
        return self.by_id.get(rid)
    async def get_by_vehicle_id(self, vid, days):
        if self.raise_on_vehicle: raise self.raise_on_vehicle
        return list(self.by_vehicle.get((vid, days), []))
    async def get_by_driver_id(self, did, days):
        if self.raise_on_driver: raise self.raise_on_driver
        return list(self.by_driver.get((did, days), []))
    async def update(self, rid, data):
        if self.raise_on_update: raise self.raise_on_update
        self.updated.append((rid, data))
        if rid in self.by_id:
            self.by_id[rid].update(data)
            return True
        return False
    async def delete(self, rid):
        if self.raise_on_delete: raise self.raise_on_delete
        if rid in self.by_id:
            self.by_id.pop(rid)
            self.deleted.append(rid)
            return True
        return False
    async def get_fuel_analytics(self):
        if self.raise_on_analytics: raise self.raise_on_analytics
        return dict(self.analytics)

class _VehicleRepo:
    def __init__(self): self.by_id = {}
    async def get_by_id(self, vid): return self.by_id.get(vid)

class _DriverRepo:
    def __init__(self): self.by_id = {}
    async def get_by_id(self, did): return self.by_id.get(did)

repos_pkg.FuelRecordRepository = _FuelRepo
repos_pkg.VehicleRepository = _VehicleRepo
repos_pkg.DriverRepository = _DriverRepo

# Safe import: load fuel_service.py as services.fuel_service
def _load_module():
    if "services" not in sys.modules:
        pkg = types.ModuleType("services"); pkg.__path__ = []; sys.modules["services"] = pkg
    for path in CANDIDATES:
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("services.fuel_service", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["services.fuel_service"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("fuel_service.py not found")
fs_mod = _load_module()
FuelService = fs_mod.FuelService

def make_service():
    svc = FuelService()
    assert isinstance(svc.fuel_repo, _FuelRepo)
    assert isinstance(svc.vehicle_repo, _VehicleRepo)
    assert isinstance(svc.driver_repo, _DriverRepo)
    return svc

# ---- create_fuel_record ----
@pytest.mark.asyncio
async def test_create_fuel_record_vehicle_missing():
    svc = make_service()
    req = schemas_requests.FuelRecordCreateRequest(vehicle_id="V1", driver_id="D1", liters=10, cost=100)
    with pytest.raises(ValueError):
        await svc.create_fuel_record(req, created_by="u")

@pytest.mark.asyncio
async def test_create_fuel_record_driver_missing():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"id": "V1"}
    req = schemas_requests.FuelRecordCreateRequest(vehicle_id="V1", driver_id="D1", liters=10, cost=100)
    with pytest.raises(ValueError):
        await svc.create_fuel_record(req, created_by="u")

@pytest.mark.asyncio
async def test_create_fuel_record_repo_error_propagates():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"id": "V1"}
    svc.driver_repo.by_id["D1"] = {"id": "D1"}
    svc.fuel_repo.raise_on_create = RuntimeError("x")
    req = schemas_requests.FuelRecordCreateRequest(vehicle_id="V1", driver_id="D1", liters=10, cost=100)
    with pytest.raises(RuntimeError):
        await svc.create_fuel_record(req, created_by="u")

@pytest.mark.asyncio
async def test_create_fuel_record_success_publishes_and_returns():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"id": "V1"}
    svc.driver_repo.by_id["D1"] = {"id": "D1"}
    req = schemas_requests.FuelRecordCreateRequest(vehicle_id="V1", driver_id="D1", liters=12.5, cost=250)
    out = await svc.create_fuel_record(req, created_by="u1")
    assert out["id"] == "fr1"
    assert out["created_by"] == "u1"
    assert "created_at" in out
    ep = events_pub.event_publisher
    evt = ep.events[-1]
    assert evt["event_type"] == "fuel_record_created"
    assert evt["vehicle_id"] == "V1" and evt["driver_id"] == "D1"
    assert evt["liters"] == 12.5 and evt["cost"] == 250

# ---- get_fuel_record_by_id / by_vehicle / by_driver ----
@pytest.mark.asyncio
async def test_get_fuel_record_by_id_success_and_error(monkeypatch):
    svc = make_service()
    svc.fuel_repo.by_id["fr1"] = {"id": "fr1", "x": 1}
    assert await svc.get_fuel_record_by_id("fr1") == {"id": "fr1", "x": 1}
    svc.fuel_repo.raise_on_get = RuntimeError("boom")
    with pytest.raises(RuntimeError):
        await svc.get_fuel_record_by_id("fr2")

@pytest.mark.asyncio
async def test_get_fuel_records_by_vehicle_success_and_error():
    svc = make_service()
    svc.fuel_repo.by_vehicle[("V1", 7)] = [{"id": "fr1"}]
    assert await svc.get_fuel_records_by_vehicle("V1", 7) == [{"id": "fr1"}]
    svc.fuel_repo.raise_on_vehicle = RuntimeError("bad")
    with pytest.raises(RuntimeError):
        await svc.get_fuel_records_by_vehicle("V1", 30)

@pytest.mark.asyncio
async def test_get_fuel_records_by_driver_success_and_error():
    svc = make_service()
    svc.fuel_repo.by_driver[("D1", 14)] = [{"id": "fr2"}]
    assert await svc.get_fuel_records_by_driver("D1", 14) == [{"id": "fr2"}]
    svc.fuel_repo.raise_on_driver = RuntimeError("bad")
    with pytest.raises(RuntimeError):
        await svc.get_fuel_records_by_driver("D1", 30)

# ---- update_fuel_record ----
@pytest.mark.asyncio
async def test_update_fuel_record_not_found_and_update_failure():
    svc = make_service()
    req = schemas_requests.FuelRecordUpdateRequest(cost=123)
    with pytest.raises(ValueError):
        await svc.update_fuel_record("fr9", req, "u")
    svc.fuel_repo.by_id["fr1"] = {"id": "fr1", "cost": 10}
    svc.fuel_repo.update = types.MethodType(lambda self, rid, data: False, svc.fuel_repo)  
    with pytest.raises(Exception):
        await svc.update_fuel_record("fr1", req, "u")

@pytest.mark.asyncio
async def test_update_fuel_record_success_publishes_and_returns():
    svc = make_service()
    svc.fuel_repo.by_id["fr1"] = {"id": "fr1", "cost": 10}
    req = schemas_requests.FuelRecordUpdateRequest(cost=123, note=None)
    out = await svc.update_fuel_record("fr1", req, "u2")
    assert out["cost"] == 123
    ep = events_pub.event_publisher
    evt = ep.events[-1]
    assert evt["event_type"] == "fuel_record_updated" and evt["fuel_record_id"] == "fr1"


# ---- get_fuel_analytics ----
@pytest.mark.asyncio
async def test_get_fuel_analytics_success_and_error():
    svc = make_service()
    svc.fuel_repo.analytics = {"total_liters": 123, "total_cost": 456}
    out = await svc.get_fuel_analytics()
    assert out["fuel_analytics"] == {"total_liters": 123, "total_cost": 456}
    assert "generated_at" in out
    svc.fuel_repo.raise_on_analytics = RuntimeError("nope")
    with pytest.raises(RuntimeError):
        await svc.get_fuel_analytics()

# ---- handle_request routing ----
@pytest.mark.asyncio
async def test_handle_request_get_vehicle_driver_record_and_notfound():
    svc = make_service()
    svc.fuel_repo.by_vehicle[("V1", 7)] = [{"id": "fr1"}]
    r1 = await svc.handle_request("GET", {"endpoint": "fuel/vehicle/V1/records", "data": {"days": 7}})
    assert r1["success"] is True and r1["data"] == [{"id": "fr1"}]
    svc.fuel_repo.by_driver[("D1", 30)] = [{"id": "fr2"}]
    r2 = await svc.handle_request("GET", {"endpoint": "fuel/driver/D1/records", "data": {}})
    assert r2["success"] is True and r2["data"] == [{"id": "fr2"}]
    svc.fuel_repo.by_id["fr3"] = {"id": "fr3", "cost": 10}
    r3 = await svc.handle_request("GET", {"endpoint": "fuel/records/fr3", "data": {}})
    assert r3["success"] is True and r3["data"]["id"] == "fr3"
    r4 = await svc.handle_request("GET", {"endpoint": "fuel/records/unknown", "data": {}})
    assert r4["success"] is False and "not found" in r4["error"].lower()

@pytest.mark.asyncio
async def test_handle_request_get_analytics_and_post_put_delete_success():
    svc = make_service()
    svc.fuel_repo.analytics = {"total_liters": 1}
    ga = await svc.handle_request("GET", {"endpoint": "fuel/analytics", "data": {}})
    assert ga["success"] is True and "fuel_analytics" in ga["data"]
    svc.vehicle_repo.by_id["V1"] = {"id": "V1"}
    svc.driver_repo.by_id["D1"] = {"id": "D1"}
    post = await svc.handle_request("POST", {"endpoint": "fuel/records", "user_id": "u", "data": {"vehicle_id": "V1", "driver_id": "D1", "liters": 5, "cost": 50}})
    assert post["success"] is True and "id" in post["data"]
    rid = post["data"]["id"]
    put = await svc.handle_request("PUT", {"endpoint": f"fuel/records/{rid}", "user_id": "u2", "data": {"cost": 60}})
    assert put["success"] is True and put["data"]["cost"] == 60
    dele = await svc.handle_request("DELETE", {"endpoint": f"fuel/records/{rid}", "user_id": "u3", "data": {}})
    assert dele["success"] is True and "deleted successfully" in dele["message"].lower()

@pytest.mark.asyncio
async def test_handle_request_unsupported_and_exception(monkeypatch):
    svc = make_service()
    bad = await svc.handle_request("GET", {"endpoint": "fuel/unknown", "data": {}})
    assert bad["success"] is False and "unsupported" in bad["error"].lower()
    async def boom(*a, **k): raise RuntimeError("explode")
    monkeypatch.setattr(svc, "create_fuel_record", boom)
    err = await svc.handle_request("POST", {"endpoint": "fuel/records", "user_id": "u", "data": {"vehicle_id": "V1", "driver_id": "D1"}})
    assert err["success"] is False and "explode" in err["error"]
