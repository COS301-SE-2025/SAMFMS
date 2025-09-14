import sys, os, types, importlib, pytest
from datetime import datetime, timedelta

HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..")),
    os.path.abspath(os.path.join(HERE, "..")),
    os.getcwd(),
]
for p in CANDIDATES:
    if p not in sys.path:
        sys.path.insert(0, p)

if "repositories" not in sys.modules:
    sys.modules["repositories"] = types.ModuleType("repositories")
if not hasattr(sys.modules["repositories"], "__path__"):
    sys.modules["repositories"].__path__ = []
if "repositories.repositories" not in sys.modules:
    sys.modules["repositories.repositories"] = types.ModuleType("repositories.repositories")

if "events" not in sys.modules:
    sys.modules["events"] = types.ModuleType("events")
if not hasattr(sys.modules["events"], "__path__"):
    sys.modules["events"].__path__ = []

if "events.publisher" in sys.modules:
    del sys.modules["events.publisher"]
ep = types.ModuleType("events.publisher")
class _PublisherStub:
    def __init__(self): self.published=[]
    async def publish_event(self, payload): self.published.append(payload)
ep.event_publisher = _PublisherStub()
sys.modules["events.publisher"] = ep

if "schemas" not in sys.modules:
    sys.modules["schemas"] = types.ModuleType("schemas")
if not hasattr(sys.modules["schemas"], "__path__"):
    sys.modules["schemas"].__path__ = []

req_mod = sys.modules.get("schemas.requests")
if req_mod is None:
    req_mod = types.ModuleType("schemas.requests")
    sys.modules["schemas.requests"] = req_mod
class MileageUpdateRequest:
    def __init__(self, vehicle_id:str, driver_id:str, new_mileage:int, reading_date=None, notes=None):
        self.vehicle_id = vehicle_id
        self.driver_id = driver_id
        self.new_mileage = new_mileage
        self.reading_date = reading_date
        self.notes = notes
req_mod.MileageUpdateRequest = MileageUpdateRequest

ent_mod = sys.modules.get("schemas.entities")
if ent_mod is None:
    ent_mod = types.ModuleType("schemas.entities")
    sys.modules["schemas.entities"] = ent_mod
class MileageRecord: pass
ent_mod.MileageRecord = MileageRecord

class _MileageRepo:
    def __init__(self):
        self.created=[]
        self.deleted=[]
        self.by_id={}
        self.by_vehicle={}
        self.by_driver={}
        self.latest={}
        self.last_create_data=None
        self.delete_result=True
    async def create(self, data):
        self.last_create_data = dict(data)
        new_id = f"mr{len(self.created)+1}"
        self.created.append((new_id, dict(data)))
        self.by_id[new_id] = {"_id": new_id, **data}
        return new_id
    async def delete(self, rid):
        self.deleted.append(rid)
        return self.delete_result
    async def get_by_id(self, rid):
        return self.by_id.get(rid)
    async def get_by_vehicle_id(self, vehicle_id, days):
        return list(self.by_vehicle.get((vehicle_id, days), []))
    async def get_by_driver_id(self, driver_id, days):
        return list(self.by_driver.get((driver_id, days), []))
    async def get_latest_mileage(self, vehicle_id):
        return self.latest.get(vehicle_id)

class _VehicleRepo:
    def __init__(self):
        self.by_id={}
        self.update_calls=[]
        self.update_ok=True
    async def get_by_id(self, vid):
        return self.by_id.get(vid)
    async def update(self, vid, data):
        self.update_calls.append((vid, dict(data)))
        if not self.update_ok: return False
        if vid in self.by_id: self.by_id[vid].update(data)
        return True

class _DriverRepo:
    def __init__(self): self.by_id={}
    async def get_by_id(self, did):
        return self.by_id.get(did)

repos_pkg = sys.modules["repositories.repositories"]
repos_pkg.MileageRecordRepository = _MileageRepo
repos_pkg.VehicleRepository = _VehicleRepo
repos_pkg.DriverRepository = _DriverRepo

def _load_mileage_module():
    import importlib.util
    candidates = [
        os.path.abspath(os.path.join(HERE, "..", "..", "services", "mileage_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "services", "mileage_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "services", "mileage_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "mileage_service.py")),
    ]
    for path in candidates:
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("services.mileage_service", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["services.mileage_service"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("mileage_service.py not found")

ms_mod = _load_mileage_module()
MileageService = ms_mod.MileageService
publisher = importlib.import_module("events.publisher").event_publisher

def make_service():
    svc = MileageService()
    assert isinstance(svc.mileage_repo, _MileageRepo)
    assert isinstance(svc.vehicle_repo, _VehicleRepo)
    assert isinstance(svc.driver_repo, _DriverRepo)
    return svc

@pytest.mark.asyncio
async def test_update_vehicle_mileage_vehicle_not_found():
    svc = make_service()
    svc.driver_repo.by_id["D1"] = {"_id":"D1"}
    req = MileageUpdateRequest(vehicle_id="V1", driver_id="D1", new_mileage=100)
    with pytest.raises(ValueError):
        await svc.update_vehicle_mileage(req, "u")

@pytest.mark.asyncio
async def test_update_vehicle_mileage_driver_not_found():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"_id":"V1", "mileage": 10}
    req = MileageUpdateRequest(vehicle_id="V1", driver_id="D1", new_mileage=100)
    with pytest.raises(ValueError):
        await svc.update_vehicle_mileage(req, "u")

@pytest.mark.asyncio
async def test_update_vehicle_mileage_new_mileage_not_greater():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"_id":"V1", "mileage": 100}
    svc.driver_repo.by_id["D1"] = {"_id":"D1"}
    req = MileageUpdateRequest(vehicle_id="V1", driver_id="D1", new_mileage=100)
    with pytest.raises(ValueError):
        await svc.update_vehicle_mileage(req, "u")

@pytest.mark.asyncio
async def test_update_vehicle_mileage_success_default_reading_date_and_event():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"_id":"V1", "mileage": 50}
    svc.driver_repo.by_id["D1"] = {"_id":"D1"}
    req = MileageUpdateRequest(vehicle_id="V1", driver_id="D1", new_mileage=120)
    rid = await svc.update_vehicle_mileage(req, "alice")
    assert rid["_id"].startswith("mr")
    created = svc.mileage_repo.last_create_data
    assert created["previous_mileage"] == 50 and created["new_mileage"] == 120 and created["mileage_difference"] == 70
    assert created["reading_date"] is not None and created["created_by"] == "alice"
    assert publisher.published and publisher.published[-1]["event_type"] == "vehicle_mileage_updated"

@pytest.mark.asyncio
async def test_update_vehicle_mileage_success_with_provided_reading_date():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"_id":"V1", "mileage": 10}
    svc.driver_repo.by_id["D1"] = {"_id":"D1"}
    rd = datetime(2030,1,1,9,0,0)
    req = MileageUpdateRequest(vehicle_id="V1", driver_id="D1", new_mileage=20, reading_date=rd, notes="n")
    _ = await svc.update_vehicle_mileage(req, "u")
    assert svc.mileage_repo.last_create_data["reading_date"] == rd

@pytest.mark.asyncio
async def test_update_vehicle_mileage_vehicle_update_fails_rolls_back_and_raises():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"_id":"V1", "mileage": 1}
    svc.driver_repo.by_id["D1"] = {"_id":"D1"}
    svc.vehicle_repo.update_ok = False
    req = MileageUpdateRequest(vehicle_id="V1", driver_id="D1", new_mileage=2)
    with pytest.raises(Exception):
        await svc.update_vehicle_mileage(req, "u")
    assert svc.mileage_repo.deleted

@pytest.mark.asyncio
async def test_update_vehicle_mileage_publish_event_raises():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"_id":"V1", "mileage": 1}
    svc.driver_repo.by_id["D1"] = {"_id":"D1"}
    async def boom(payload): raise RuntimeError("publish fail")
    publisher.published.clear()
    publisher.publish_event = boom
    req = MileageUpdateRequest(vehicle_id="V1", driver_id="D1", new_mileage=3)
    with pytest.raises(RuntimeError):
        await svc.update_vehicle_mileage(req, "u")
    assert not svc.mileage_repo.by_id[svc.mileage_repo.created[-1][0]] is None

@pytest.mark.asyncio
async def test_get_records_by_vehicle_success_and_error(monkeypatch):
    svc = make_service()
    svc.mileage_repo.by_vehicle[("V1", 7)] = [{"_id":"mr1"}]
    ok = await svc.get_mileage_records_by_vehicle("V1", 7)
    assert ok == [{"_id":"mr1"}]
    async def boom(v, d): raise RuntimeError("x")
    monkeypatch.setattr(svc.mileage_repo, "get_by_vehicle_id", boom)
    with pytest.raises(RuntimeError):
        await svc.get_mileage_records_by_vehicle("V1", 7)

@pytest.mark.asyncio
async def test_get_records_by_driver_success_and_error(monkeypatch):
    svc = make_service()
    svc.mileage_repo.by_driver[("D1", 30)] = [{"_id":"mr1"}]
    ok = await svc.get_mileage_records_by_driver("D1", 30)
    assert ok == [{"_id":"mr1"}]
    async def boom(v, d): raise RuntimeError("x")
    monkeypatch.setattr(svc.mileage_repo, "get_by_driver_id", boom)
    with pytest.raises(RuntimeError):
        await svc.get_mileage_records_by_driver("D1", 7)

@pytest.mark.asyncio
async def test_get_latest_mileage_success_and_error(monkeypatch):
    svc = make_service()
    svc.mileage_repo.latest["V1"] = {"mileage": 123}
    assert await svc.get_latest_mileage("V1") == {"mileage": 123}
    async def boom(v): raise RuntimeError("x")
    monkeypatch.setattr(svc.mileage_repo, "get_latest_mileage", boom)
    with pytest.raises(RuntimeError):
        await svc.get_latest_mileage("V1")

@pytest.mark.asyncio
async def test_validate_mileage_update_all_branches(monkeypatch):
    svc = make_service()
    out1 = await svc.validate_mileage_update("NOPE", 10)
    assert out1["valid"] is False and out1["reason"] == "Vehicle not found"
    svc.vehicle_repo.by_id["V1"] = {"_id":"V1", "mileage": 100}
    out2 = await svc.validate_mileage_update("V1", 90)
    assert out2["valid"] is False and "90" in out2["reason"]
    out3 = await svc.validate_mileage_update("V1", 150)
    assert out3["valid"] is True and out3["difference"] == 50
    async def boom(_): raise RuntimeError("fail")
    monkeypatch.setattr(svc.vehicle_repo, "get_by_id", boom)
    out4 = await svc.validate_mileage_update("V1", 1)
    assert out4["valid"] is False and "fail" in out4["reason"]

@pytest.mark.asyncio
async def test_handle_request_get_current_and_error(monkeypatch):
    svc = make_service()
    async def cur(v): return 555
    setattr(svc, "get_current_vehicle_mileage", cur)
    r = await svc.handle_request("GET", {"endpoint":"mileage/current/vehicle/V1","data":{}})
    assert r["success"] is True and r["data"]["vehicle_id"] == "V1" and r["data"]["current_mileage"] == 555
    r2 = await svc.handle_request("GET", {"endpoint":"mileage/current/vehicle","data":{}})
    assert r2["success"] is False and "error" in r2

@pytest.mark.asyncio
async def test_handle_request_get_history_driver_and_record_by_id(monkeypatch):
    svc = make_service()
    async def hist(v, d): return [{"_id":"mr1"}]
    setattr(svc, "get_mileage_history", hist)
    r = await svc.handle_request("GET", {"endpoint":"mileage/history/vehicle/V1","data":{"days":7}})
    assert r["success"] is True and r["data"][0]["_id"] == "mr1"
    svc.mileage_repo.by_id["mrX"] = {"_id":"mrX", "x":1}
    r2 = await svc.handle_request("GET", {"endpoint":"mileage/records/driver/D1","data":{"days":14}})
    assert r2["success"] is True and isinstance(r2["data"], list)
    r3 = await svc.handle_request("GET", {"endpoint":"mileage/records/mrX","data":{}})
    assert r3["success"] is True and r3["data"]["_id"] == "mrX"
    r4 = await svc.handle_request("GET", {"endpoint":"mileage/records/missing","data":{}})
    assert r4["success"] is False and r4["error"] == "Mileage record not found"

@pytest.mark.asyncio
async def test_handle_request_post_update_and_delete_and_unsupported(monkeypatch):
    svc = make_service()
    async def upd(req, uid): return {"_id":"mrY","ok":1}
    monkeypatch.setattr(svc, "update_vehicle_mileage", upd)
    r = await svc.handle_request("POST", {"endpoint":"mileage/update","data":{"vehicle_id":"V1","driver_id":"D1","new_mileage":10},"user_id":"u"})
    assert r["success"] is True and r["data"]["_id"] == "mrY"
    svc.mileage_repo.by_id["mrZ"] = {"_id":"mrZ"}
    svc.mileage_repo.delete_result = True
    d1 = await svc.handle_request("DELETE", {"endpoint":"mileage/records/mrZ","data":{}})
    assert d1["success"] is True
    svc.mileage_repo.delete_result = False
    d2 = await svc.handle_request("DELETE", {"endpoint":"mileage/records/mrZ","data":{}})
    assert d2["success"] is False
    bad = await svc.handle_request("PATCH", {"endpoint":"x","data":{}})
    assert bad["success"] is False and "error" in bad
    bad2 = await svc.handle_request("GET", {"endpoint":"weird/path","data":{}})
    assert bad2["success"] is False and "Unsupported" in bad2["error"]
