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

# ---- packages & stubs (ensure parent modules behave like packages)
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
    
ep = types.ModuleType("events.publisher")

class _PublisherStub:
    def __init__(self):
        self.created = []
        self.updated = []
        self.deleted = []
    async def publish_vehicle_created(self, vehicle, user):
        self.created.append((vehicle, user))
    async def publish_vehicle_updated(self, vehicle, user, changes=None):
        self.updated.append((vehicle, user, changes or {}))
    async def publish_vehicle_deleted(self, vehicle, user):
        self.deleted.append((vehicle, user))

ep.event_publisher = _PublisherStub()
sys.modules["events.publisher"] = ep

if "schemas" not in sys.modules:
    sys.modules["schemas"] = types.ModuleType("schemas")
if not hasattr(sys.modules["schemas"], "__path__"):
    sys.modules["schemas"].__path__ = []

# >>> HARDENED: always attach classes to schemas.requests, even if it exists
req_mod = sys.modules.get("schemas.requests")
if req_mod is None:
    req_mod = types.ModuleType("schemas.requests")
    sys.modules["schemas.requests"] = req_mod

class VehicleCreateRequest:
    def __init__(self, **kw):
        # assign into backing store (won't hit properties)
        self._raw = dict(kw)
        for k, v in kw.items():
            setattr(self, k, v)  # ok because we implement setters below
    def model_dump(self): return dict(self._raw)

    @property
    def registration_number(self): return self._raw.get("registration_number")
    @registration_number.setter
    def registration_number(self, value): self._raw["registration_number"] = value

    @property
    def license_plate(self): return self._raw.get("license_plate")
    @license_plate.setter
    def license_plate(self, value): self._raw["license_plate"] = value

class VehicleUpdateRequest:
    def __init__(self, **kw): self._raw = dict(kw)
    def model_dump(self): return dict(self._raw)

req_mod.VehicleCreateRequest = VehicleCreateRequest
req_mod.VehicleUpdateRequest = VehicleUpdateRequest

if "schemas.responses" not in sys.modules:
    rmod = types.ModuleType("schemas.responses")
    class _Wrap:
        def __init__(self, d): self._d = d
        def model_dump(self): return self._d
    class ResponseBuilder:
        @staticmethod
        def success(data=None, message=""): return _Wrap({"status":"success","data":data,"message":message})
        @staticmethod
        def error(error="Error", message=""): return _Wrap({"status":"error","error":error,"message":message})
    rmod.ResponseBuilder = ResponseBuilder
    sys.modules["schemas.responses"] = rmod

# ---- repository stubs
class _VehicleRepoStub:
    def __init__(self):
        self._by_id = {}
        self._reg_map = {}
        self.find_calls = []
        self.count_calls = []
        self.get_by_reg_calls = []
        self.create_calls = []
        self.update_calls = []
        self.delete_calls = []
        self.count_value = 0
        self.find_result = []
        self.get_by_reg_result = None
        self.create_ok_id = "veh1"
        self.update_ok = True
        self.delete_ok = True
    async def find(self, filter_query=None, skip=0, limit=None, sort=None):
        self.find_calls.append((filter_query, skip, limit, sort))
        return list(self.find_result)
    async def count(self, query=None):
        self.count_calls.append(query)
        return self.count_value
    async def get_by_registration_number(self, reg):
        self.get_by_reg_calls.append(reg)
        return self.get_by_reg_result or self._reg_map.get(reg)
    async def create(self, data):
        self.create_calls.append(data)
        vid = self.create_ok_id
        self._by_id[vid] = {"_id": vid, **data}
        self._reg_map[data["registration_number"]] = self._by_id[vid]
        return vid
    async def get_by_id(self, vid):
        return self._by_id.get(vid)
    async def update(self, vid, data):
        self.update_calls.append((vid, data))
        if not self.update_ok: return False
        if vid in self._by_id: self._by_id[vid].update(data)
        return True
    async def delete(self, vid):
        self.delete_calls.append(vid)
        if not self.delete_ok: return False
        return bool(self._by_id.pop(vid, None))

class _AssignRepoStub:
    def __init__(self):
        self._by_vehicle = {}
        self.calls = []
    async def get_by_vehicle_id(self, vehicle_id, status=None):
        self.calls.append((vehicle_id, status))
        data = self._by_vehicle.get(vehicle_id, [])
        if status=="active":
            return [a for a in data if a.get("status")=="active"]
        return data

class _UsageRepoStub:
    def __init__(self):
        self.find_calls = []
        self.logs = []
    async def find(self, filter_query=None, sort=None):
        self.find_calls.append((filter_query, sort))
        return list(self.logs)

repos_pkg = sys.modules["repositories.repositories"]
repos_pkg.VehicleRepository = _VehicleRepoStub
repos_pkg.VehicleAssignmentRepository = _AssignRepoStub
repos_pkg.VehicleUsageLogRepository = _UsageRepoStub

# ---- safe-load vehicle_service
def _load_vehicle_module():
    import importlib.util
    if "services" in sys.modules:
        del sys.modules["services"]
    spkg = types.ModuleType("services")
    spkg.__path__ = []
    sys.modules["services"] = spkg
    candidates = [
        os.path.abspath(os.path.join(HERE, "..", "..", "services", "vehicle_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "services", "vehicle_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "services", "vehicle_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "vehicle_service.py")),
    ]
    for path in candidates:
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("services.vehicle_service", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["services.vehicle_service"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("vehicle_service.py not found")

vs_mod = _load_vehicle_module()
VehicleService = vs_mod.VehicleService
publisher = importlib.import_module("events.publisher").event_publisher

def make_service():
    svc = VehicleService()
    assert isinstance(svc.vehicle_repo, _VehicleRepoStub)
    assert isinstance(svc.assignment_repo, _AssignRepoStub)
    return svc

# ---------------- get_vehicles ----------------
@pytest.mark.asyncio
async def test_get_vehicles_filters_and_pagination_and_iso_conversion():
    svc = make_service()
    dt = datetime(2030, 1, 1, 12, 0, 0)
    svc.vehicle_repo.find_result = [{"_id":"veh1","registration_number":"REG1","created_at": dt, "other": "x"}]
    svc.vehicle_repo.count_value = 21
    out = await svc.get_vehicles("Ops","active","truck", {"skip": 10, "limit": 5})
    q, s, l, sort = svc.vehicle_repo.find_calls[-1]
    assert q == {"department":"Ops","status":"active","type":"truck"} and s==10 and l==5
    assert sort == [("registration_number",1)]
    assert out["vehicles"][0]["created_at"] == dt.isoformat()
    assert out["pagination"] == {"total":21,"page":3,"page_size":5,"total_pages":5}

@pytest.mark.asyncio
async def test_get_vehicles_default_pagination_and_repo_error(monkeypatch):
    svc = make_service()
    svc.vehicle_repo.find_result = []
    svc.vehicle_repo.count_value = 0
    out = await svc.get_vehicles()
    assert out["pagination"]["page"] == 1 and out["pagination"]["page_size"] == 50
    async def boom(**kw): raise RuntimeError("x")
    monkeypatch.setattr(svc.vehicle_repo, "find", boom)
    with pytest.raises(RuntimeError):
        await svc.get_vehicles()

# ---------------- get_num_vehicles ----------------
@pytest.mark.asyncio
async def test_get_num_vehicles_wraps_get_vehicles(monkeypatch):
    svc = make_service()
    async def fake_get(*a, **k): return {"vehicles":[1,2,3], "pagination":{}}
    monkeypatch.setattr(svc, "get_vehicles", fake_get)
    out = await svc.get_num_vehicles()
    assert out == {"Total vehicles": 3}

# ---------------- create_vehicle ----------------
@pytest.mark.asyncio
async def test_create_vehicle_missing_ids_and_duplicate_reg_raises(monkeypatch):
    svc = make_service()
    VC = req_mod.VehicleCreateRequest
    with pytest.raises(ValueError):
        await svc.create_vehicle(VC(), created_by="u")
    svc.vehicle_repo.get_by_reg_result = {"_id":"exists"}
    with pytest.raises(ValueError):
        await svc.create_vehicle(VC(registration_number="REG1"), created_by="u")

@pytest.mark.asyncio
async def test_create_vehicle_happy_path_fill_defaults_and_publish():
    svc = make_service()
    VC = req_mod.VehicleCreateRequest
    now_before = datetime.utcnow()
    req = VC(license_plate="ABC123", make="Ford")
    svc.vehicle_repo.create_ok_id = "vehX"
    res = await svc.create_vehicle(req, "alice")
    assert (res.get("id") == "vehX") or (res.get("_id") == "vehX")

    stored = svc.vehicle_repo._by_id["vehX"]
    assert stored["registration_number"] == "ABC123" and stored["license_plate"] == "ABC123"
    assert stored["status"] == "available"
    assert stored["created_by"] == "alice"

    # created_at / updated_at may be ISO strings after transform; parse if needed
    def _parse_dt(v):
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # allow `Z` suffix or plain ISO
            s = v.replace("Z", "+00:00") if v.endswith("Z") else v
            return datetime.fromisoformat(s)
        raise AssertionError(f"unexpected datetime type: {type(v)}")

    created_dt = _parse_dt(stored["created_at"])
    updated_dt = _parse_dt(stored["updated_at"])
    assert updated_dt >= created_dt

    # event was published
    assert publisher.created and publisher.created[-1][0]["_id"] == "vehX"

# ---------------- get_vehicle_by_id ----------------
@pytest.mark.asyncio
async def test_get_vehicle_by_id_ok_and_error(monkeypatch):
    svc = make_service()
    svc.vehicle_repo._by_id["veh1"] = {"_id":"veh1"}
    assert await svc.get_vehicle_by_id("veh1") == {"_id":"veh1"}
    async def boom(_): raise RuntimeError("x")
    monkeypatch.setattr(svc.vehicle_repo, "get_by_id", boom)
    with pytest.raises(RuntimeError):
        await svc.get_vehicle_by_id("veh2")

# ---------------- update_vehicle ----------------
@pytest.mark.asyncio
async def test_update_vehicle_not_found_clash_fail_and_success_with_changes(monkeypatch):
    svc = make_service()
    VU = req_mod.VehicleUpdateRequest
    with pytest.raises(ValueError):
        await svc.update_vehicle("nope", VU(status="active"), "u")
    svc.vehicle_repo._by_id["veh1"] = {"_id":"veh1","registration_number":"REG1","status":"available"}
    svc.vehicle_repo._reg_map["REG2"] = {"_id":"someoneelse"}
    with pytest.raises(ValueError):
        await svc.update_vehicle("veh1", VU(registration_number="REG2"), "u")
    svc.vehicle_repo.update_ok = False
    with pytest.raises(ValueError):
        await svc.update_vehicle("veh1", VU(status="available"), "u")
    svc.vehicle_repo.update_ok = True
    publisher.updated.clear()
    out = await svc.update_vehicle("veh1", VU(status="active"), "bob")
    assert out["status"] == "active"
    assert publisher.updated and "status" in publisher.updated[-1][2]
    publisher.updated.clear()
    _ = await svc.update_vehicle("veh1", VU(status="active"), "bob")
    assert len(publisher.updated) in (0, 1)

# ---------------- delete_vehicle ----------------
@pytest.mark.asyncio
async def test_delete_vehicle_not_found_active_assignments_fail_and_success():
    svc = make_service()
    with pytest.raises(ValueError):
        await svc.delete_vehicle("nope", "u")
    svc.vehicle_repo._by_id["veh1"] = {"_id":"veh1"}
    svc.assignment_repo._by_vehicle["veh1"] = [{"status":"active"}]
    with pytest.raises(ValueError):
        await svc.delete_vehicle("veh1", "u")
    svc.assignment_repo._by_vehicle["veh1"] = []
    svc.vehicle_repo.delete_ok = False
    assert await svc.delete_vehicle("veh1", "u") is False
    svc.vehicle_repo._by_id["veh2"] = {"_id":"veh2"}
    svc.vehicle_repo.delete_ok = True
    publisher.deleted.clear()
    assert await svc.delete_vehicle("veh2", "u") is True
    assert publisher.deleted and publisher.deleted[-1][0]["_id"] == "veh2"

# ---------------- search_vehicles ----------------
@pytest.mark.asyncio
async def test_search_vehicles_default_pagination_and_filter_shape():
    svc = make_service()
    svc.vehicle_repo.find_result = [{"_id":"veh1"},{"_id":"veh2"}]
    svc.vehicle_repo.count_value = 2
    out = await svc.search_vehicles("Fo")
    q, s, l, sort = svc.vehicle_repo.find_calls[-1]
    assert s == 0 and l == 1000 and sort == [("registration_number",1)]
    assert "$or" in q and any("make" in cond for cond in q["$or"])
    assert out["pagination"]["total"] == 2 and out["pagination"]["total_pages"] == 1

# ---------------- get_vehicle_assignments ----------------
@pytest.mark.asyncio
async def test_get_vehicle_assignments_ok_and_error(monkeypatch):
    svc = make_service()
    svc.assignment_repo._by_vehicle["veh1"] = [{"id":"a1"}]
    assert await svc.get_vehicle_assignments("veh1") == [{"id":"a1"}]
    async def boom(*a, **k): raise RuntimeError("x")
    monkeypatch.setattr(svc.assignment_repo, "get_by_vehicle_id", boom)
    with pytest.raises(RuntimeError):
        await svc.get_vehicle_assignments("veh1")

# ---------------- get_vehicle_usage_stats ----------------
@pytest.mark.asyncio
async def test_get_vehicle_usage_stats_date_range_no_logs_and_logs_slicing(monkeypatch):
    svc = make_service()
    usage_repo = repos_pkg.VehicleUsageLogRepository()
    usage_repo.logs = []
    def fake_vulr(): return usage_repo
    if not hasattr(sys.modules["repositories"], "__path__"):
        sys.modules["repositories"].__path__ = []
    monkeypatch.setattr(importlib.import_module("repositories.repositories"), "VehicleUsageLogRepository", fake_vulr)
    out = await svc.get_vehicle_usage_stats("veh1", "2030-01-01T00:00:00", "2030-01-31T23:59:59")
    f, sort = usage_repo.find_calls[-1]
    assert "created_at" in f and "$gte" in f["created_at"] and "$lte" in f["created_at"]
    assert out["trip_count"] == 0 and out["avg_distance_per_trip"] == 0 and out["fuel_efficiency"] == 0
    usage_repo.logs = [{"distance":1,"fuel_consumed":0,"created_at":datetime.utcnow()} for _ in range(12)]
    out2 = await svc.get_vehicle_usage_stats("veh1")
    assert out2["trip_count"] == 12 and len(out2["usage_logs"]) == 10 and out2["fuel_efficiency"] == 0

# ---------------- handle_request ----------------
@pytest.mark.asyncio
async def test_handle_request_get_variants_and_total_message():
    svc = make_service()
    svc.vehicle_repo._by_id["veh1"] = {"_id":"veh1"}
    svc.vehicle_repo.find_result = [{"_id":"veh1"}]
    svc.vehicle_repo.count_value = 1
    r1 = await svc.handle_request("GET", {"endpoint":"vehicles/search","data":{"query":"v"}})
    assert r1["status"] == "success" and "vehicles" in r1["data"]
    r2 = await svc.handle_request("GET", {"endpoint":"vehicles/veh1","data":{}})
    assert r2["status"] == "success" and r2["data"]["id"] == "veh1"
    r3 = await svc.handle_request("GET", {"endpoint":"vehicles-total","data":{}})
    assert r3["status"] == "success" and "penis" in r3["message"]
    r4 = await svc.handle_request("GET", {"endpoint":"vehicles","data":{}})
    assert r4["status"] == "success" and "vehicles" in r4["data"]

@pytest.mark.asyncio
async def test_handle_request_post_put_delete_and_edge_cases():
    svc = make_service()
    r0 = await svc.handle_request("POST", {"endpoint":"vehicles","data":{}})
    assert r0["status"] == "error" and r0["error"] == "VehicleRequestError"
    r1 = await svc.handle_request("POST", {"endpoint":"vehicles/assign-driver","data":{"driver":"d","vehicle":"v"}})
    assert r1 is None
    r2 = await svc.handle_request("POST", {"endpoint":"vehicles","data":{"license_plate":"PLT"}})
    assert r2["status"] == "success" and r2["data"]["id"]
    vid = r2["data"]["id"]
    r3 = await svc.handle_request("PUT", {"endpoint":"vehicles","data":{"status":"active"}})
    assert r3["status"] == "error"
    r4 = await svc.handle_request("PUT", {"endpoint":f"vehicles/{vid}","data":{}})
    assert r4["status"] == "error"
    r5 = await svc.handle_request("PUT", {"endpoint":f"vehicles/{vid}","data":{"status":"active"}})
    assert r5["status"] == "success" and r5["data"]["status"] == "active"
    r6 = await svc.handle_request("DELETE", {"endpoint":"vehicles","data":{}})
    assert r6["status"] == "error"
    r7 = await svc.handle_request("DELETE", {"endpoint":f"vehicles/{vid}","data":{}})
    assert r7["status"] == "success" and isinstance(r7["data"], bool)

@pytest.mark.asyncio
async def test_handle_request_unsupported_method_returns_error():
    svc = make_service()
    r = await svc.handle_request("PATCH", {"endpoint":"vehicles","data":{}})
    assert r["status"] == "error" and r["error"] == "VehicleRequestError"

def test_transform_vehicle_data_variants():
    svc = make_service()
    assert svc._transform_vehicle_data(None) is None
    v = {"_id":"x","a":1}
    out = svc._transform_vehicle_data(v)
    assert out["id"] == "x" and "_id" not in out
    lst = {"vehicles":[{"_id":"a"},{"_id":"b"}]}
    out2 = svc._transform_vehicle_data(lst)
    assert out2["vehicles"][0]["id"] == "a"
    lst2 = [{"_id":"c"}]
    out3 = svc._transform_vehicle_data(lst2)
    assert out3[0]["id"] == "c"
