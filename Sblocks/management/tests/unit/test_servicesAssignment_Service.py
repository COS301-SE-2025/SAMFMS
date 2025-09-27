import sys
import os
import types
import importlib
import pytest
from datetime import datetime

HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [

    os.path.abspath(os.path.join(HERE, "..", "..", "services", "assignment_service.py")),

    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "management", "services", "assignment_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "services", "assignment_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "assignment_service.py")),
]

def ensure_pkg(name):
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)
    return sys.modules[name]

repositories = ensure_pkg("repositories")
repos_pkg = ensure_pkg("repositories.repositories")
events = ensure_pkg("events")
events_pub = ensure_pkg("events.publisher")
schemas = ensure_pkg("schemas")
schemas_requests = ensure_pkg("schemas.requests")
schemas_entities = ensure_pkg("schemas.entities")


if not hasattr(events_pub, "event_publisher"):
    class _EP:
        def __init__(self):
            self.events = []
        async def publish_event(self, event):
            self.events.append(event)
    events_pub.event_publisher = _EP()

if not hasattr(schemas_entities, "AssignmentStatus"):
    class AssignmentStatus:
        ACTIVE = "active"
        COMPLETED = "completed"
    schemas_entities.AssignmentStatus = AssignmentStatus
if not hasattr(schemas_entities, "VehicleAssignment"):
    class VehicleAssignment: ...
    schemas_entities.VehicleAssignment = VehicleAssignment

if not hasattr(schemas_requests, "VehicleAssignmentCreateRequest"):
    class VehicleAssignmentCreateRequest:
        def __init__(self, **data):
            self._data = dict(data)
            self.vehicle_id = self._data.get("vehicle_id")
            self.driver_id = self._data.get("driver_id")
            self.assignment_type = self._data.get("assignment_type", "standard")
        def dict(self):
            return dict(self._data)
    schemas_requests.VehicleAssignmentCreateRequest = VehicleAssignmentCreateRequest

if not hasattr(schemas_requests, "VehicleAssignmentUpdateRequest"):
    class VehicleAssignmentUpdateRequest:
        def __init__(self, **data):
            self._data = dict(data)
        def dict(self):
            return dict(self._data)
    schemas_requests.VehicleAssignmentUpdateRequest = VehicleAssignmentUpdateRequest

if not hasattr(schemas_requests, "DriverCreateRequest"):
    class DriverCreateRequest:
        def __init__(self, **kw):
            self._raw = dict(kw)
            for k, v in kw.items():
                setattr(self, k, v)  
        def model_dump(self, exclude_unset=False):
            return dict(self._raw)
    schemas_requests.DriverCreateRequest = DriverCreateRequest

if not hasattr(schemas_requests, "DriverUpdateRequest"):
    class DriverUpdateRequest:
        def __init__(self, **kw):
            self._raw = dict(kw)
            for k, v in kw.items():
                setattr(self, k, v)
        def model_dump(self):
            return dict(self._raw)
    schemas_requests.DriverUpdateRequest = DriverUpdateRequest

class _AssignmentRepoStub:
    def __init__(self):
        self.created = []
        self.updated = []
        self.by_id = {}
        self.by_driver = {}
        self.by_vehicle = {}
        self.active = []
        self.next_id = 1
    async def get_by_driver_id(self, driver_id, status=None):
        lst = list(self.by_driver.get(driver_id, []))
        return [a for a in lst if a.get("status")==status] if status else lst
    async def get_by_vehicle_id(self, vehicle_id, status=None):
        lst = list(self.by_vehicle.get(vehicle_id, []))
        return [a for a in lst if a.get("status")==status] if status else lst
    async def get_by_id(self, assignment_id):
        return self.by_id.get(assignment_id)
    async def create(self, data):
        aid = f"a{self.next_id}"; self.next_id += 1
        created = {"id": aid, **data}
        self.created.append(created)
        self.by_id[aid] = created
        self.by_driver.setdefault(data["driver_id"], []).append(created)
        self.by_vehicle.setdefault(data["vehicle_id"], []).append(created)
        return aid
    async def update(self, assignment_id, data):
        self.updated.append((assignment_id, data))
        if assignment_id in self.by_id:
            self.by_id[assignment_id].update(data)
            return True
        return False
    async def get_active_assignments(self):
        return list(self.active)

class _VehicleRepoStub:
    def __init__(self):
        self.by_id = {}
        self.updates = []
    async def get_by_id(self, vid):
        return self.by_id.get(vid)
    async def update(self, vid, data):
        self.updates.append((vid, data))
        if vid in self.by_id:
            self.by_id[vid].update(data)
            return True
        return False

class _DriverRepoStub:
    def __init__(self):
        self.by_id = {}
        self.updates = []
    async def get_by_id(self, did):
        return self.by_id.get(did)
    async def update(self, did, data):
        self.updates.append((did, data))
        if did in self.by_id:
            self.by_id[did].update(data)
            return True
        return False

repos_pkg.VehicleAssignmentRepository = _AssignmentRepoStub
repos_pkg.VehicleRepository = _VehicleRepoStub
repos_pkg.DriverRepository = _DriverRepoStub

def _load_assignment_module():
    import importlib.util
    for path in CANDIDATES:
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("services.assignment_service", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["services.assignment_service"] = mod 
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("assignment_service.py not found in expected locations")

assignment_service_module = _load_assignment_module()
VehicleAssignmentService = assignment_service_module.VehicleAssignmentService

def make_service():
    return VehicleAssignmentService()

# ---------------------------------------------------------------------
# Tests (small, branch-by-branch)
# ---------------------------------------------------------------------
@pytest.mark.asyncio
async def test_assign_vehicle_vehicle_not_found():
    svc = make_service()
    req = schemas_requests.VehicleAssignmentCreateRequest(vehicle_id="V1", driver_id="D1", assignment_type="std")
    with pytest.raises(ValueError):
        await svc.assign_vehicle_to_driver(req, created_by="u1")

@pytest.mark.asyncio
async def test_assign_vehicle_vehicle_not_available():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"id":"V1", "status":"assigned"}
    req = schemas_requests.VehicleAssignmentCreateRequest(vehicle_id="V1", driver_id="D1", assignment_type="std")
    with pytest.raises(ValueError):
        await svc.assign_vehicle_to_driver(req, created_by="u1")

@pytest.mark.asyncio
async def test_assign_vehicle_driver_not_found():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"id":"V1", "status":"available"}
    req = schemas_requests.VehicleAssignmentCreateRequest(vehicle_id="V1", driver_id="D1", assignment_type="std")
    with pytest.raises(ValueError):
        await svc.assign_vehicle_to_driver(req, created_by="u1")

@pytest.mark.asyncio
async def test_assign_vehicle_driver_not_active():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"id":"V1", "status":"available"}
    svc.driver_repo.by_id["D1"] = {"id":"D1", "status":"inactive"}
    req = schemas_requests.VehicleAssignmentCreateRequest(vehicle_id="V1", driver_id="D1", assignment_type="std")
    with pytest.raises(ValueError):
        await svc.assign_vehicle_to_driver(req, created_by="u1")

@pytest.mark.asyncio
async def test_assign_vehicle_driver_has_active_assignment():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"id":"V1", "status":"available"}
    svc.driver_repo.by_id["D1"] = {"id":"D1", "status":"active"}
    svc.assignment_repo.by_driver["D1"] = [{"id":"a0","status":"active"}]
    req = schemas_requests.VehicleAssignmentCreateRequest(vehicle_id="V1", driver_id="D1", assignment_type="std")
    with pytest.raises(ValueError):
        await svc.assign_vehicle_to_driver(req, created_by="u1")

@pytest.mark.asyncio
async def test_assign_vehicle_vehicle_has_active_assignment():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"id":"V1", "status":"available"}
    svc.driver_repo.by_id["D1"] = {"id":"D1", "status":"active"}
    svc.assignment_repo.by_driver["D1"] = []
    svc.assignment_repo.by_vehicle["V1"] = [{"id":"a0","status":"active"}]
    req = schemas_requests.VehicleAssignmentCreateRequest(vehicle_id="V1", driver_id="D1", assignment_type="std")
    with pytest.raises(ValueError):
        await svc.assign_vehicle_to_driver(req, created_by="u1")

@pytest.mark.asyncio
async def test_assign_vehicle_success_updates_and_event():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"id":"V1", "status":"available"}
    svc.driver_repo.by_id["D1"] = {"id":"D1", "status":"active"}
    svc.assignment_repo.by_driver["D1"] = []
    svc.assignment_repo.by_vehicle["V1"] = []
    req = schemas_requests.VehicleAssignmentCreateRequest(vehicle_id="V1", driver_id="D1", assignment_type="std")
    out = await svc.assign_vehicle_to_driver(req, created_by="u1")
    assert out["id"].startswith("a")
    assert svc.vehicle_repo.updates[-1][0] == "V1"
    assert svc.vehicle_repo.updates[-1][1]["status"] == "assigned"
    assert svc.driver_repo.updates[-1][0] == "D1"
    assert svc.driver_repo.updates[-1][1]["current_vehicle_id"] == "V1"
    ep = events_pub.event_publisher
    assert ep.events[-1]["event_type"] == "vehicle_assigned"
    assert ep.events[-1]["vehicle_id"] == "V1"
    assert ep.events[-1]["driver_id"] == "D1"

@pytest.mark.asyncio
async def test_unassign_vehicle_assignment_not_found():
    svc = make_service()
    with pytest.raises(ValueError):
        await svc.unassign_vehicle_from_driver("a999", updated_by="u2")

@pytest.mark.asyncio
async def test_unassign_vehicle_not_active():
    svc = make_service()
    svc.assignment_repo.by_id["a1"] = {"id":"a1","status":"completed","vehicle_id":"V1","driver_id":"D1"}
    with pytest.raises(ValueError):
        await svc.unassign_vehicle_from_driver("a1", updated_by="u2")

@pytest.mark.asyncio
async def test_unassign_vehicle_success_no_end_mileage_and_with_end_mileage():
    svc = make_service()
    svc.assignment_repo.by_id["a2"] = {"id":"a2","status":"active","vehicle_id":"V1","driver_id":"D1"}
    svc.vehicle_repo.by_id["V1"] = {"id":"V1","status":"assigned"}
    svc.driver_repo.by_id["D1"] = {"id":"D1","current_vehicle_id":"V1"}
    out = await svc.unassign_vehicle_from_driver("a2", updated_by="u2")
    assert out["status"] == "completed"
    assert svc.vehicle_repo.by_id["V1"]["status"] == "available"
    assert svc.driver_repo.by_id["D1"]["current_vehicle_id"] is None
    ep = events_pub.event_publisher
    assert ep.events[-1]["event_type"] == "vehicle_unassigned"
    svc.assignment_repo.by_id["a3"] = {"id":"a3","status":"active","vehicle_id":"V1","driver_id":"D1"}
    out2 = await svc.unassign_vehicle_from_driver("a3", updated_by="u3", end_mileage=12345)
    assert svc.assignment_repo.by_id["a3"]["end_mileage"] == 12345

@pytest.mark.asyncio
async def test_get_driver_current_assignment_first_or_none():
    svc = make_service()
    svc.assignment_repo.by_driver["D1"] = [{"id":"a1","status":"active"},{"id":"a0","status":"active"}]
    got = await svc.get_driver_current_assignment("D1")
    assert got["id"] == "a1"
    svc.assignment_repo.by_driver["D2"] = []
    assert await svc.get_driver_current_assignment("D2") is None

@pytest.mark.asyncio
async def test_get_vehicle_current_assignment_first_or_none():
    svc = make_service()
    svc.assignment_repo.by_vehicle["V1"] = [{"id":"a1","status":"active"}]
    got = await svc.get_vehicle_current_assignment("V1")
    assert got["id"] == "a1"
    svc.assignment_repo.by_vehicle["V2"] = []
    assert await svc.get_vehicle_current_assignment("V2") is None

@pytest.mark.asyncio
async def test_get_assignments_lists_success_and_errors(monkeypatch):
    svc = make_service()
    svc.assignment_repo.by_driver["D1"] = [{"id":"a1"}]
    assert await svc.get_assignments_by_driver("D1") == [{"id":"a1"}]
    svc.assignment_repo.by_vehicle["V1"] = [{"id":"b1"}]
    assert await svc.get_assignments_by_vehicle("V1") == [{"id":"b1"}]
    async def boom(*a, **k): raise RuntimeError("x")
    monkeypatch.setattr(svc.assignment_repo, "get_by_driver_id", boom)
    with pytest.raises(RuntimeError):
        await svc.get_assignments_by_driver("D1")
    monkeypatch.setattr(svc.assignment_repo, "get_by_vehicle_id", boom)
    with pytest.raises(RuntimeError):
        await svc.get_assignments_by_vehicle("V1")

@pytest.mark.asyncio
async def test_get_all_active_assignments_success_and_error(monkeypatch):
    svc = make_service()
    svc.assignment_repo.active = [{"id":"a"}]
    assert await svc.get_all_active_assignments() == [{"id":"a"}]
    async def boom(): raise RuntimeError("x")
    monkeypatch.setattr(svc.assignment_repo, "get_active_assignments", boom)
    with pytest.raises(RuntimeError):
        await svc.get_all_active_assignments()

@pytest.mark.asyncio
async def test_handle_request_get_driver_current_and_vehicle_current_and_active():
    svc = make_service()
    svc.assignment_repo.by_driver["D1"] = [{"id":"a1","status":"active"}]
    r1 = await svc.handle_request("GET", {"endpoint":"assignments/driver/D1/current","data":{}})
    assert r1["success"] is True and r1["data"]["id"] == "a1"
    svc.assignment_repo.by_vehicle["V1"] = [{"id":"v1","status":"active"}]
    r2 = await svc.handle_request("GET", {"endpoint":"assignments/vehicle/V1/current","data":{}})
    assert r2["success"] is True and r2["data"]["id"] == "v1"
    svc.assignment_repo.active = [{"id":"a"}]
    r3 = await svc.handle_request("GET", {"endpoint":"assignments/active","data":{}})
    assert r3["success"] is True and r3["data"] == [{"id":"a"}]

@pytest.mark.asyncio
async def test_handle_request_get_driver_and_vehicle_lists():
    svc = make_service()
    svc.assignment_repo.by_driver["DX"] = [{"id":"x"}]
    r1 = await svc.handle_request("GET", {"endpoint":"assignments/driver/DX","data":{}})
    assert r1["success"] is True and r1["data"] == [{"id":"x"}]
    svc.assignment_repo.by_vehicle["VX"] = [{"id":"y"}]
    r2 = await svc.handle_request("GET", {"endpoint":"assignments/vehicle/VX","data":{}})
    assert r2["success"] is True and r2["data"] == [{"id":"y"}]

@pytest.mark.asyncio
async def test_handle_request_post_and_delete_success():
    svc = make_service()
    svc.vehicle_repo.by_id["V1"] = {"id":"V1","status":"available"}
    svc.driver_repo.by_id["D1"] = {"id":"D1","status":"active"}
    r = await svc.handle_request("POST", {"endpoint":"assignments","user_id":"u1","data":{
        "vehicle_id":"V1","driver_id":"D1","assignment_type":"std"
    }})
    assert r["success"] is True and "id" in r["data"]
    aid = r["data"]["id"]
    r2 = await svc.handle_request("DELETE", {"endpoint":f"assignments/{aid}","user_id":"u2","data":{"end_mileage": 5000}})
    assert r2["success"] is True and r2["data"]["status"] == "completed"

@pytest.mark.asyncio
async def test_handle_request_unsupported_and_internal_error(monkeypatch):
    svc = make_service()
    r = await svc.handle_request("GET", {"endpoint":"assignments/unknown","data":{}})
    assert r["success"] is False and "Unsupported" in r["error"]
    async def boom(*a, **k): raise RuntimeError("boom")
    monkeypatch.setattr(svc, "assign_vehicle_to_driver", boom)
    r2 = await svc.handle_request("POST", {"endpoint":"assignments","user_id":"u","data":{}})
    assert r2["success"] is False and "boom" in r2["error"]
