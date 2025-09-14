import sys, os, types, importlib.util, pytest
from datetime import datetime

HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..", "services", "notification_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "Sblocks", "maintenance", "services", "notification_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "services", "notification_service.py")),
    os.path.abspath(os.path.join(os.getcwd(), "notification_service.py")),
]

def ensure(name):
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)
    return sys.modules[name]

repositories = ensure("repositories")
repos_pkg = ensure("repositories.repositories")
events = ensure("events")
events_pub = ensure("events.publisher")
schemas = ensure("schemas")
schemas_requests = ensure("schemas.requests")
schemas_entities = ensure("schemas.entities")

class _Priority:
    def __init__(self, v): self.value = v

if not hasattr(schemas_entities, "NotificationStatus"):
    class NotificationStatus:
        UNREAD = "unread"
        READ = "read"
        ARCHIVED = "archived"
    schemas_entities.NotificationStatus = NotificationStatus

if not hasattr(schemas_entities, "NotificationPriority"):
    class NotificationPriority:
        NORMAL = _Priority("normal")
        HIGH = _Priority("high")
    schemas_entities.NotificationPriority = NotificationPriority

if not hasattr(schemas_entities, "Notification"):
    class Notification: ...
    schemas_entities.Notification = Notification

if not hasattr(schemas_requests, "NotificationCreateRequest"):
    class NotificationCreateRequest:
        def __init__(self, **data):
            self._data = dict(data)
            for k, v in data.items(): setattr(self, k, v)
        def dict(self): return dict(self._data)
    schemas_requests.NotificationCreateRequest = NotificationCreateRequest

class _NotificationRepo:
    def __init__(self):
        self.by_id = {}
        self.created = []
        self.updated = []
        self.deleted = []
        self.filters_called = []
        self.next_id = 1
        self.raise_on_create = None
        self.raise_on_update = None
        self.raise_on_delete = None
        self.raise_on_filters = None
        self.raise_on_get = None
    async def create(self, data):
        if self.raise_on_create: raise self.raise_on_create
        nid = f"n{self.next_id}"; self.next_id += 1
        self.by_id[nid] = {"id": nid, **data}
        self.created.append(data)
        return nid
    async def get_by_id(self, nid):
        if self.raise_on_get: raise self.raise_on_get
        return self.by_id.get(nid)
    async def get_by_filters(self, filters):
        if self.raise_on_filters: raise self.raise_on_filters
        self.filters_called.append(filters)
        out = []
        for v in self.by_id.values():
            ok = True
            for k, val in filters.items():
                if v.get(k) != val:
                    ok = False
                    break
            if ok: out.append(v)
        return out
    async def update(self, nid, data):
        if self.raise_on_update: raise self.raise_on_update
        self.updated.append((nid, data))
        if nid in self.by_id:
            self.by_id[nid].update(data)
            return True
        return False
    async def delete(self, nid):
        if self.raise_on_delete: raise self.raise_on_delete
        self.deleted.append(nid)
        self.by_id.pop(nid, None)
        return True

class _DriverRepo:
    def __init__(self): self.by_id = {}
    async def get_by_id(self, did): return self.by_id.get(did)

repos_pkg.NotificationRepository = _NotificationRepo
repos_pkg.DriverRepository = _DriverRepo

def _load_module():
    if "services" not in sys.modules:
        pkg = types.ModuleType("services"); pkg.__path__ = []; sys.modules["services"] = pkg
    for p in CANDIDATES:
        if os.path.exists(p):
            spec = importlib.util.spec_from_file_location("services.notification_service", p)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["services.notification_service"] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("notification_service.py not found")

ns_mod = _load_module()
NotificationService = ns_mod.NotificationService
NotificationStatus = schemas_entities.NotificationStatus
NotificationPriority = schemas_entities.NotificationPriority
NotificationCreateRequest = schemas_requests.NotificationCreateRequest

@pytest.fixture(autouse=True)
def _patch_publisher(monkeypatch):
    pub = getattr(ns_mod, "event_publisher", None)
    captured = []
    if pub is None:
        class _EP:
            async def publish_event(self, evt):
                captured.append(evt)
        pub = _EP()
        setattr(ns_mod, "event_publisher", pub)
    else:
        async def safe_publish(evt):
            captured.append(evt)
        monkeypatch.setattr(pub, "publish_event", safe_publish, raising=True)
    setattr(ns_mod, "_captured_events", captured)
    yield

def make_service():
    svc = NotificationService()
    assert isinstance(svc.notification_repo, _NotificationRepo)
    assert isinstance(svc.driver_repo, _DriverRepo)
    return svc

@pytest.mark.asyncio
async def test_create_notification_invalid_recipient_raises():
    svc = make_service()
    req = NotificationCreateRequest(title="t", message="m", notification_type="x", recipient_id="D1", priority=None)
    with pytest.raises(ValueError):
        await svc.create_notification(req, "u")

@pytest.mark.asyncio
async def test_create_notification_success_and_event_priority_default():
    svc = make_service()
    svc.driver_repo.by_id["D1"] = {"id": "D1"}
    req = NotificationCreateRequest(title="t", message="m", notification_type="x", recipient_id="D1", priority=None)
    out = await svc.create_notification(req, "u1")
    assert out["id"].startswith("n")
    assert out["status"] == NotificationStatus.UNREAD
    assert out["created_by"] == "u1"
    evt = ns_mod._captured_events[-1]
    assert evt["event_type"] == "notification_created"
    assert evt["recipient_id"] == "D1"
    assert evt["priority"] == NotificationPriority.NORMAL.value

@pytest.mark.asyncio
async def test_create_notification_repo_error_propagates():
    svc = make_service()
    svc.driver_repo.by_id["D1"] = {"id": "D1"}
    svc.notification_repo.raise_on_create = RuntimeError("x")
    req = NotificationCreateRequest(title="t", message="m", notification_type="x", recipient_id="D1", priority=NotificationPriority.HIGH)
    with pytest.raises(RuntimeError):
        await svc.create_notification(req, "u")

@pytest.mark.asyncio
async def test_get_notifications_by_recipient_success_and_error():
    svc = make_service()
    nid = await svc.notification_repo.create({"recipient_id":"R","status":NotificationStatus.UNREAD,"title":"a","created_by":"x","created_at":"1"})
    out = await svc.get_notifications_by_recipient("R", NotificationStatus.UNREAD)
    assert out and out[0]["id"] == nid
    svc.notification_repo.raise_on_filters = RuntimeError("bad")
    with pytest.raises(RuntimeError):
        await svc.get_notifications_by_recipient("R")

@pytest.mark.asyncio
async def test_get_broadcast_notifications_success_and_error():
    svc = make_service()
    nid = await svc.notification_repo.create({"recipient_id":None,"status":NotificationStatus.UNREAD,"title":"b","created_by":"x","created_at":"1"})
    out = await svc.get_broadcast_notifications()
    assert any(n["id"] == nid for n in out)
    svc.notification_repo.raise_on_filters = RuntimeError("bad")
    with pytest.raises(RuntimeError):
        await svc.get_broadcast_notifications()

@pytest.mark.asyncio
async def test_mark_notification_as_read_not_found_and_permission_denied():
    svc = make_service()
    with pytest.raises(ValueError):
        await svc.mark_notification_as_read("n9", "U1")
    nid = await svc.notification_repo.create({"recipient_id":"U2","status":NotificationStatus.UNREAD,"title":"t","created_by":"x","created_at":"1"})
    with pytest.raises(ValueError):
        await svc.mark_notification_as_read(nid, "U1")

@pytest.mark.asyncio
async def test_mark_notification_as_read_broadcast_allows_and_publishes():
    svc = make_service()
    nid = await svc.notification_repo.create({"recipient_id":None,"status":NotificationStatus.UNREAD,"title":"t","created_by":"x","created_at":"1"})
    out = await svc.mark_notification_as_read(nid, "U1")
    assert out["status"] == NotificationStatus.READ
    evt = ns_mod._captured_events[-1]
    assert evt["event_type"] == "notification_read" and evt["notification_id"] == nid

@pytest.mark.asyncio
async def test_archive_notification_branches():
    svc = make_service()
    with pytest.raises(ValueError):
        await svc.archive_notification("n9", "U1")
    nid = await svc.notification_repo.create({"recipient_id":"U2","status":NotificationStatus.UNREAD,"title":"t","created_by":"x","created_at":"1"})
    with pytest.raises(ValueError):
        await svc.archive_notification(nid, "U1")
    svc.notification_repo.by_id[nid]["recipient_id"] = "U1"
    out = await svc.archive_notification(nid, "U1")
    assert out["status"] == NotificationStatus.ARCHIVED
    evt = ns_mod._captured_events[-1]
    assert evt["event_type"] == "notification_archived" and evt["notification_id"] == nid

@pytest.mark.asyncio
async def test_delete_notification_not_found_and_success_even_if_not_creator():
    svc = make_service()
    with pytest.raises(ValueError):
        await svc.delete_notification("n9", "U1")
    nid = await svc.notification_repo.create({"recipient_id":"U2","status":NotificationStatus.UNREAD,"title":"t","created_by":"OTHER","created_at":"1"})
    before = len(ns_mod._captured_events)
    ok = await svc.delete_notification(nid, "U1")
    assert ok is True
    assert len(ns_mod._captured_events) == before + 1
    evt = ns_mod._captured_events[-1]
    assert evt["event_type"] == "notification_deleted" and evt["notification_id"] == nid

@pytest.mark.asyncio
async def test_get_unread_count_success_and_error(monkeypatch):
    svc = make_service()
    await svc.notification_repo.create({"recipient_id":"R","status":NotificationStatus.UNREAD,"title":"1","created_by":"x","created_at":"1"})
    await svc.notification_repo.create({"recipient_id":"R","status":NotificationStatus.UNREAD,"title":"2","created_by":"x","created_at":"2"})
    assert await svc.get_unread_count_by_recipient("R") == 2
    async def boom(*a, **k): raise RuntimeError("x")
    monkeypatch.setattr(svc, "get_notifications_by_recipient", boom)
    with pytest.raises(RuntimeError):
        await svc.get_unread_count_by_recipient("R")

@pytest.mark.asyncio
async def test_create_system_maintenance_assignment_notifications():
    svc = make_service()
    out1 = await svc.create_system_notification("Title","Msg", NotificationPriority.HIGH)
    assert out1["title"] == "Title"
    svc.driver_repo.by_id["D1"] = {"id":"D1"}
    out2 = await svc.create_maintenance_notification("V1","D1","Fix me")
    assert out2["recipient_id"] == "D1"
    out3 = await svc.create_assignment_notification("D1","V9","shift")
    assert "assigned to vehicle V9" in out3["message"]

@pytest.mark.asyncio
async def test_create_system_notification_error_propagates(monkeypatch):
    svc = make_service()
    async def boom(req, who): raise RuntimeError("nope")
    monkeypatch.setattr(svc, "create_notification", boom)
    with pytest.raises(RuntimeError):
        await svc.create_system_notification("T","M", NotificationPriority.NORMAL)

@pytest.mark.asyncio
async def test_handle_request_get_routes():
    svc = make_service()
    svc.driver_repo.by_id["D1"] = {"id":"D1"}
    await svc.notification_repo.create({"recipient_id":"U1","status":NotificationStatus.UNREAD,"title":"1","created_by":"x","created_at":"2025-01-02T00:00:00"})
    await svc.notification_repo.create({"recipient_id":None,"status":NotificationStatus.UNREAD,"title":"2","created_by":"x","created_at":"2025-01-03T00:00:00"})
    r1 = await svc.handle_request("GET", {"endpoint":"notifications/recipient/U1/unread-count","data":{}})
    assert r1["success"] is True and r1["data"]["unread_count"] >= 0
    r2 = await svc.handle_request("GET", {"endpoint":"notifications/recipient/U1","data":{"status": NotificationStatus.UNREAD}})
    assert r2["success"] is True and all(n["recipient_id"]=="U1" for n in r2["data"])
    r3 = await svc.handle_request("GET", {"endpoint":"notifications/broadcast","data":{}})
    assert r3["success"] is True and all(n["recipient_id"] is None for n in r3["data"])
    r4 = await svc.handle_request("GET", {"endpoint":"notifications/my-notifications","data":{},"user_id":"U1"})
    assert r4["success"] is True and len(r4["data"]) >= 2
    assert r4["data"][0]["created_at"] >= r4["data"][1]["created_at"]


@pytest.mark.asyncio
async def test_handle_request_put_read_and_archive_and_delete():
    svc = make_service()
    nid = await svc.notification_repo.create({"recipient_id":"U1","status":NotificationStatus.UNREAD,"title":"1","created_by":"U1","created_at":"1"})
    r = await svc.handle_request("PUT", {"endpoint":f"notifications/{nid}/read","user_id":"U1","data":{}})
    assert r["success"] is True and r["data"]["status"] == NotificationStatus.READ
    a = await svc.handle_request("PUT", {"endpoint":f"notifications/{nid}/archive","user_id":"U1","data":{}})
    assert a["success"] is True and a["data"]["status"] == NotificationStatus.ARCHIVED
    d = await svc.handle_request("DELETE", {"endpoint":f"notifications/{nid}","user_id":"U1","data":{}})
    assert d["success"] is True and "deleted successfully" in d["message"].lower()

@pytest.mark.asyncio
async def test_handle_request_unsupported_and_exception(monkeypatch):
    svc = make_service()
    bad = await svc.handle_request("GET", {"endpoint":"notifications/unknown","data":{}})
    assert bad["success"] is False and "unsupported" in bad["error"].lower()
    async def boom(*a, **k): raise RuntimeError("explode")
    monkeypatch.setattr(svc, "create_system_notification", boom)
    err = await svc.handle_request("POST", {"endpoint":"notifications/system","data":{"title":"t","message":"m"}})
    assert err["success"] is False and "explode" in err["error"]
