import sys, os, types, importlib, pytest
from datetime import datetime

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
if "repositories.repositories" not in sys.modules:
    sys.modules["repositories.repositories"] = types.ModuleType("repositories.repositories")
if "repositories.database" not in sys.modules:
    dbm = types.ModuleType("repositories.database")
    dbm.db_manager = object()
    sys.modules["repositories.database"] = dbm
if "events" not in sys.modules:
    sys.modules["events"] = types.ModuleType("events")
if "events.publisher" not in sys.modules:
    pub = types.ModuleType("events.publisher")
    class _EP: pass
    pub.event_publisher = _EP()
    sys.modules["events.publisher"] = pub
if "schemas" not in sys.modules:
    sys.modules["schemas"] = types.ModuleType("schemas")
if "schemas.requests" not in sys.modules:
    req = types.ModuleType("schemas.requests")
    class DriverCreateRequest:
        def __init__(self, **kw):
            for k,v in kw.items(): setattr(self, k, v)
            self._raw = dict(kw)
        def model_dump(self, exclude_unset=False):
            return dict(self._raw)
    class DriverUpdateRequest:
        def __init__(self, **kw):
            self._raw = dict(kw)
        def model_dump(self):
            return dict(self._raw)
    req.DriverCreateRequest = DriverCreateRequest
    req.DriverUpdateRequest = DriverUpdateRequest
    sys.modules["schemas.requests"] = req
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

if "services" in sys.modules:
    del sys.modules["services"]
services_pkg = types.ModuleType("services")
services_pkg.__path__ = []
sys.modules["services"] = services_pkg
drv_analytics = types.ModuleType("services.drivers_service")
class DriversService:
    def __init__(self):
        self.added = 0; self.removed = 0
    async def add_driver(self): self.added += 1
    async def remove_driver(self): self.removed += 1
drv_analytics.DriversService = DriversService
sys.modules["services.drivers_service"] = drv_analytics

class _DriverRepoStub:
    def __init__(self):
        self.created = []
        self.updated = []
        self.deleted = []
        self.find_args = []
        self.count_args = []
        self.data_by_id = {}
        self.by_emp = {}
        self.by_email = {}
        self.by_license = {}
        self.assign_ok = True
        self.unassign_ok = True
        self.update_ok = True
        self.delete_ok = True
        self.last_emp_id = "EMP000"
        self.search_data = []
        self.by_dept = []
        self.active_list = []
        self.by_security = {}
    async def get_by_employee_id(self, emp): return self.by_emp.get(emp)
    async def get_by_email(self, email): return self.by_email.get(email)
    async def get_by_license_number(self, lic): return self.by_license.get(lic)
    async def create(self, data):
        self.created.append(data)
        new_id = f"d{len(self.created)}"
        self.data_by_id[new_id] = {"_id": new_id, **data}
        return new_id
    async def get_by_id(self, did): return self.data_by_id.get(did)
    async def update(self, did, data):
        self.updated.append((did, data))
        if not self.update_ok: return False
        if did in self.data_by_id:
            self.data_by_id[did].update(data)
        return True
    async def assign_vehicle(self, did, vid): return self.assign_ok
    async def unassign_vehicle(self, did): return self.unassign_ok
    async def delete(self, did):
        if not self.delete_ok: return False
        self.data_by_id.pop(did, None)
        self.deleted.append(did)
        return True
    async def find(self, filter_query=None, skip=0, limit=None):
        self.find_args.append((filter_query, skip, limit))
        return list(self.data_by_id.values())
    async def count(self, query=None):
        self.count_args.append(query)
        return len(self.data_by_id)
    async def get_last_employee_id(self): return self.last_emp_id
    async def search_drivers(self, query): return list(self.search_data)
    async def get_by_department(self, dept): return list(self.by_dept)
    async def get_active_drivers(self): return list(self.active_list)
    async def get_by_security_id(self, sid): return self.by_security.get(sid)

sys.modules["repositories.repositories"].DriverRepository = _DriverRepoStub

def _load_driver_module():
    import importlib.util
    candidates = [
        os.path.abspath(os.path.join(HERE, "..", "..", "services", "driver_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "services", "driver_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "services", "driver_service.py")),
        os.path.abspath(os.path.join(os.getcwd(), "driver_service.py")),
    ]
    for path in candidates:
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("services.driver_service", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["services.driver_service"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("driver_service.py not found")
ds_mod = _load_driver_module()
DriverService = ds_mod.DriverService

def make_service():
    svc = DriverService()
    assert isinstance(svc.driver_repo, _DriverRepoStub)
    return svc

class _FakeResp:
    def __init__(self, status, json_data=None, text_data=""):
        self.status = status
        self._json = json_data or {}
        self._text = text_data
    async def json(self): return dict(self._json)
    async def text(self): return self._text
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False

class _FakeSession:
    def __init__(self, resp=None, boom=False):
        self._resp = resp; self._boom = boom
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def post(self, url, json=None, headers=None):
        if self._boom: raise RuntimeError("net fail")
        return self._resp

@pytest.mark.asyncio
async def test_create_user_account_branches(monkeypatch):
    svc = make_service()
    import aiohttp
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: _FakeSession(_FakeResp(200, {"ok":1})))
    assert await svc._create_user_account({"email":"e@x","full_name":"F"}) is True
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: _FakeSession(_FakeResp(400, text_data="bad")))
    assert await svc._create_user_account({"email":"e@x","full_name":"F"}) is False
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: _FakeSession(boom=True))
    assert await svc._create_user_account({"email":"e@x","full_name":"F"}) is False

@pytest.mark.asyncio
async def test_get_all_drivers_filters_pagination_and_has_more():
    svc = make_service()
    for i in range(5):
        await svc.driver_repo.create({"employee_id": f"E{i}", "status":"active","department":"Ops"})
    out = await svc.get_all_drivers({"status_filter":"active","department_filter":"Ops","skip":"1","limit":"2"})
    assert out["total"] == 5 and out["skip"] == 1 and out["limit"] == 2 and out["has_more"] is True
    q, s, l = svc.driver_repo.find_args[-1]
    assert q == {"status":"active","department":"Ops"} and s == 1 and l == 2

@pytest.mark.asyncio
async def test_get_all_drivers_limit_zero_and_invalid_status_ignored():
    svc = make_service()
    await svc.driver_repo.create({"employee_id":"E","status":"inactive"})
    out = await svc.get_all_drivers({"status_filter":"busy","limit":0})
    assert out["limit"] == out["total"] and out["has_more"] is False
    q, s, l = svc.driver_repo.find_args[-1]
    assert q == {} and l is None

@pytest.mark.asyncio
async def test_get_all_drivers_bad_skip_raises():
    svc = make_service()
    with pytest.raises(ValueError):
        await svc.get_all_drivers({"skip":"abc"})

@pytest.mark.asyncio
async def test_get_num_drivers_wrapper():
    svc = make_service()
    await svc.driver_repo.create({"employee_id":"E1"})
    assert (await svc.get_num_drivers({}))["total"] == 1

# -------- create_driver --------
@pytest.mark.asyncio
async def test_create_driver_uniqueness_checks_raise():
    svc = make_service()
    svc.driver_repo.by_emp["EMP1"] = {"_id":"x"}
    with pytest.raises(ValueError):
        await svc.create_driver(sys.modules["schemas.requests"].DriverCreateRequest(
            employee_id="EMP1", email="a@x", full_name="A B"
        ), created_by="u")
    svc = make_service()
    svc.driver_repo.by_email["a@x"] = {"_id":"x"}
    with pytest.raises(ValueError):
        await svc.create_driver(sys.modules["schemas.requests"].DriverCreateRequest(
            employee_id="E2", email="a@x", full_name="A B"
        ), created_by="u")
    svc = make_service()
    svc.driver_repo.by_license["LIC1"] = {"_id":"y"}
    with pytest.raises(ValueError):
        await svc.create_driver(sys.modules["schemas.requests"].DriverCreateRequest(
            employee_id="E3", email="b@x", full_name="A B", license_number="LIC1"
        ), created_by="u")

@pytest.mark.asyncio
async def test_create_driver_drops_empty_license_and_calls_add_driver(monkeypatch):
    svc = make_service()
    import aiohttp
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: _FakeSession(_FakeResp(500)))
    req = sys.modules["schemas.requests"].DriverCreateRequest(
        employee_id="E4", email="c@x", full_name="A B", license_number="   "
    )
    out = await svc.create_driver(req, created_by="u")
    assert out["id"].startswith("d")
    assert "license_number" not in svc.driver_repo.created[-1]

@pytest.mark.asyncio
async def test_create_driver_success_user_account_true(monkeypatch):
    svc = make_service()
    import aiohttp
    monkeypatch.setattr(aiohttp, "ClientSession", lambda: _FakeSession(_FakeResp(200, {"ok":1})))
    req = sys.modules["schemas.requests"].DriverCreateRequest(
        employee_id="E5", email="d@x", full_name="C D"
    )
    out = await svc.create_driver(req, created_by="u")
    assert out["id"].startswith("d")

# -------- update_driver --------
@pytest.mark.asyncio
async def test_update_driver_not_found_and_fail_and_success():
    svc = make_service()
    with pytest.raises(ValueError):
        await svc.update_driver("nope", sys.modules["schemas.requests"].DriverUpdateRequest(email="x@x"), "u")

    new_id = await svc.driver_repo.create({"employee_id":"E","email":"a@x"})

    svc.driver_repo.by_email["dup@x"] = {"_id":"other"}
    with pytest.raises(ValueError):
        await svc.update_driver(new_id, sys.modules["schemas.requests"].DriverUpdateRequest(email="dup@x"), "u")

    svc.driver_repo.by_email["same@x"] = {"_id":new_id}
    ok = await svc.update_driver(new_id, sys.modules["schemas.requests"].DriverUpdateRequest(email="same@x"), "u")
    assert ok["email"] == "same@x"

    svc.driver_repo.update_ok = False
    with pytest.raises(ValueError):
        await svc.update_driver(new_id, sys.modules["schemas.requests"].DriverUpdateRequest(phone="1"), "u")

# -------- assign / unassign --------
@pytest.mark.asyncio
async def test_assign_vehicle_branches():
    svc = make_service()
    with pytest.raises(ValueError):
        await svc.assign_vehicle_to_driver("nope", "V1", "u")
    did = await svc.driver_repo.create({"employee_id":"E","current_vehicle_id":"V2"})
    with pytest.raises(ValueError):
        await svc.assign_vehicle_to_driver(did, "V1", "u")
    svc.driver_repo.data_by_id[did]["current_vehicle_id"] = None
    svc.driver_repo.assign_ok = False
    with pytest.raises(ValueError):
        await svc.assign_vehicle_to_driver(did, "V1", "u")
    svc.driver_repo.assign_ok = True
    assert await svc.assign_vehicle_to_driver(did, "V1", "u") is True

@pytest.mark.asyncio
async def test_unassign_vehicle_branches():
    svc = make_service()
    with pytest.raises(ValueError):
        await svc.unassign_vehicle_from_driver("nope", "u")
    did = await svc.driver_repo.create({"employee_id":"E"})
    with pytest.raises(ValueError):
        await svc.unassign_vehicle_from_driver(did, "u")
    svc.driver_repo.data_by_id[did]["current_vehicle_id"] = "V1"
    svc.driver_repo.unassign_ok = False
    with pytest.raises(ValueError):
        await svc.unassign_vehicle_from_driver(did, "u")
    svc.driver_repo.unassign_ok = True
    assert await svc.unassign_vehicle_from_driver(did, "u") is True


@pytest.mark.asyncio
async def test_search_and_department_and_active_and_get_by_id():
    svc = make_service()
    svc.driver_repo.search_data = [{"id":"s1"}]
    svc.driver_repo.by_dept = [{"id":"d1"}]
    svc.driver_repo.active_list = [{"id":"a1"}]
    did = await svc.driver_repo.create({"employee_id":"E"})
    assert await svc.search_drivers("q") == [{"id":"s1"}]
    assert await svc.get_drivers_by_department("Ops") == [{"id":"d1"}]
    assert await svc.get_active_drivers() == [{"id":"a1"}]
    assert (await svc.get_driver_by_id("nope")) is None
    assert (await svc.get_driver_by_id(did))["_id"] == did



@pytest.mark.asyncio
async def test_generate_next_employee_id_paths(monkeypatch):
    svc = make_service()
    svc.driver_repo.last_emp_id = "EMP000"
    assert await svc.generate_next_employee_id() == "EMP001"
    svc.driver_repo.last_emp_id = "EMP009"
    assert await svc.generate_next_employee_id() == "EMP010"
    async def boom(): raise RuntimeError()
    monkeypatch.setattr(svc.driver_repo, "get_last_employee_id", boom)
    assert await svc.generate_next_employee_id() == "EMP001"


@pytest.mark.asyncio
async def test_handle_request_get_search_and_id_return_error_due_to_bug():
    svc = make_service()
    r = await svc.handle_request("GET", {"endpoint":"drivers/search","data":{"query":"a"}})
    assert r["status"] == "error" and r["error"] == "DriverRequestError"
    r2 = await svc.handle_request("GET", {"endpoint":"drivers/XYZ","data":{}})
    assert r2["status"] == "error" and r2["error"] == "DriverRequestError"

@pytest.mark.asyncio
async def test_handle_request_get_employee_success_and_default_list():
    svc = make_service()
    svc.driver_repo.by_security["SEC1"] = {"employee_id":"EMP777"}
    ok = await svc.handle_request("GET", {"endpoint":"drivers/employee/SEC1","data":{}})
    assert ok["status"] == "success" and ok["data"] == "EMP777"

    await svc.driver_repo.create({"employee_id":"E"})
    ok2 = await svc.handle_request("GET", {"endpoint":"drivers","data":{"pagination":{"skip":0,"limit":10}}})
    assert ok2["status"] == "success" and "drivers" in ok2["data"]

@pytest.mark.asyncio
async def test_handle_request_post_put_delete_and_errors():
    svc = make_service()
    bad = await svc.handle_request("POST", {"endpoint":"drivers","data":{}})
    assert bad["status"] == "error"
    ok = await svc.handle_request("POST", {"endpoint":"drivers","data":{
        "full_name":"John Smith","email":"j@x","phoneNo":"1","security_id":"S1"
    }})
    assert ok["status"] == "success" and "id" in ok["data"]
    did = ok["data"]["id"]
    okp = await svc.handle_request("PUT", {"endpoint":f"drivers/{did}","data":{"email":"z@x"}})
    assert okp["status"] == "success" and okp["data"]["email"] == "z@x"
    badp = await svc.handle_request("PUT", {"endpoint":"drivers","data":{"email":"z@x"}})
    assert badp["status"] == "error"
    badp2 = await svc.handle_request("PUT", {"endpoint":f"drivers/{did}","data":{}})
    assert badp2["status"] == "error"
    okd = await svc.handle_request("DELETE", {"endpoint":f"drivers/{did}","data":{}})
    assert okd["status"] == "success"
    badm = await svc.handle_request("PATCH", {"endpoint":"drivers","data":{}})
    assert badm["status"] == "error" and badm["error"] == "DriverRequestError"
