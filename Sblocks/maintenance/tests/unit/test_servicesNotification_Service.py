import sys
import os
import types
from datetime import datetime, timedelta, date
import importlib
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

if "schemas" not in sys.modules:
    sys.modules["schemas"] = types.ModuleType("schemas")
if "schemas.entities" not in sys.modules:
    ents = types.ModuleType("schemas.entities")
    class MaintenancePriority:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    ents.MaintenancePriority = MaintenancePriority
    sys.modules["schemas.entities"] = ents
else:
    if not hasattr(sys.modules["schemas.entities"], "MaintenancePriority"):
        class MaintenancePriority:
            LOW = "low"
            MEDIUM = "medium"
            HIGH = "high"
            CRITICAL = "critical"
        sys.modules["schemas.entities"].MaintenancePriority = MaintenancePriority

if "repositories" not in sys.modules:
    sys.modules["repositories"] = types.ModuleType("repositories")

class _FakeRepo:
    def __init__(self):
        self.created = []
        self.sent = []
        self.read = []
        self.pending = []
        self.by_user = {}
    async def create(self, data):
        doc = dict(data)
        doc.setdefault("id", f"n{len(self.created)+1}")
        self.created.append(doc)
        return doc
    async def mark_as_sent(self, nid):
        self.sent.append(nid)
        return True
    async def get_pending_notifications(self):
        return list(self.pending)
    async def get_user_notifications(self, user_id, unread_only=False):
        return list(self.by_user.get((user_id, unread_only), []))
    async def mark_as_read(self, nid):
        self.read.append(nid)
        return True

try:
    ns_mod = importlib.import_module("services.notification_service")
except Exception:
    ns_mod = importlib.import_module("notification_service")

ns_mod.MaintenanceNotificationsRepository = _FakeRepo

NotificationService = ns_mod.NotificationService
MaintenancePriority = importlib.import_module("schemas.entities").MaintenancePriority

def make_service():
    return NotificationService()

@pytest.mark.asyncio
@pytest.mark.parametrize("missing", ["title", "message", "notification_type"])
async def test_create_missing_required_field_raises(missing):
    svc = make_service()
    data = {"title": "t", "message": "m", "notification_type": "generic"}
    data.pop(missing)
    with pytest.raises(ValueError):
        await svc.create_notification(data)

@pytest.mark.asyncio
async def test_create_defaults_and_parse_scheduled_send_time():
    svc = make_service()
    when = "2030-05-01T12:30:00Z"
    result = await svc.create_notification({
        "title": "T",
        "message": "M",
        "notification_type": "general",
        "scheduled_send_time": when,
    })
    assert result["priority"] == MaintenancePriority.MEDIUM
    assert result["is_sent"] is False
    assert result["is_read"] is False
    assert result["recipient_user_ids"] == []
    assert result["recipient_roles"] == []
    assert isinstance(result["created_at"], datetime)
    assert isinstance(result["scheduled_send_time"], datetime)

@pytest.mark.asyncio
async def test_create_preserves_explicit_values():
    svc = make_service()
    explicit = {
        "title": "A",
        "message": "B",
        "notification_type": "general",
        "priority": MaintenancePriority.HIGH,
        "is_sent": True,
        "is_read": True,
        "recipient_user_ids": ["u1"],
        "recipient_roles": ["r1"],
        "created_at": datetime(2030, 1, 1),
    }
    result = await svc.create_notification(explicit)
    assert result["priority"] == MaintenancePriority.HIGH
    assert result["is_sent"] is True
    assert result["is_read"] is True
    assert result["recipient_user_ids"] == ["u1"]
    assert result["recipient_roles"] == ["r1"]
    assert result["created_at"] == datetime(2030, 1, 1)

@pytest.mark.asyncio
async def test_create_propagates_repo_error(monkeypatch):
    svc = make_service()
    async def boom(data): raise RuntimeError("fail")
    monkeypatch.setattr(svc.repository, "create", boom)
    with pytest.raises(RuntimeError):
        await svc.create_notification({"title": "T", "message": "M", "notification_type": "x"})

@pytest.mark.asyncio
async def test_send_notification_success_and_error(monkeypatch):
    svc = make_service()
    ok = await svc.send_notification("n1")
    assert ok is True and "n1" in svc.repository.sent
    async def boom(_): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "mark_as_sent", boom)
    with pytest.raises(RuntimeError):
        await svc.send_notification("n2")

@pytest.mark.asyncio
async def test_get_pending_notifications_success_and_error(monkeypatch):
    svc = make_service()
    svc.repository.pending = [{"id": "a"}, {"id": "b"}]
    out = await svc.get_pending_notifications()
    assert [n["id"] for n in out] == ["a", "b"]
    async def boom(): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "get_pending_notifications", boom)
    with pytest.raises(RuntimeError):
        await svc.get_pending_notifications()

@pytest.mark.asyncio
async def test_get_user_notifications_variants_and_error(monkeypatch):
    svc = make_service()
    svc.repository.by_user[("u1", False)] = [{"id": "x"}]
    svc.repository.by_user[("u1", True)] = [{"id": "y"}]
    out1 = await svc.get_user_notifications("u1", False)
    out2 = await svc.get_user_notifications("u1", True)
    assert out1[0]["id"] == "x" and out2[0]["id"] == "y"
    async def boom(uid, unread_only=False): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "get_user_notifications", boom)
    with pytest.raises(RuntimeError):
        await svc.get_user_notifications("u2", True)

@pytest.mark.asyncio
async def test_mark_notification_read_success_and_error(monkeypatch):
    svc = make_service()
    ok = await svc.mark_notification_read("n9")
    assert ok is True and "n9" in svc.repository.read
    async def boom(_): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "mark_as_read", boom)
    with pytest.raises(RuntimeError):
        await svc.mark_notification_read("n10")

@pytest.mark.asyncio
async def test_create_maintenance_due_notification_defaults_and_parse(monkeypatch):
    svc = make_service()
    async def capture(data): return {"id": "z", **data}
    monkeypatch.setattr(svc, "create_notification", capture)
    rec = {"id": "r1", "vehicle_id": "V1", "title": "Oil", "scheduled_date": "2030-05-02T08:15:00"}
    out = await svc.create_maintenance_due_notification(rec)
    assert out["notification_type"] == "maintenance_due"
    assert out["title"] == "Maintenance Due - Vehicle V1"
    assert "scheduled for 2030-05-02 08:15" in out["message"]
    assert out["priority"] == MaintenancePriority.MEDIUM
    assert out["recipient_roles"] == ["fleet_manager", "maintenance_supervisor"]

@pytest.mark.asyncio
async def test_create_maintenance_due_notification_respects_priority(monkeypatch):
    svc = make_service()
    async def passthru(data): return data
    monkeypatch.setattr(svc, "create_notification", passthru)
    rec = {"id": "r2", "vehicle_id": "V2", "title": "Brakes", "scheduled_date": datetime(2030, 1, 1, 9, 0, 0), "priority": MaintenancePriority.HIGH}
    out = await svc.create_maintenance_due_notification(rec)
    assert out["priority"] == MaintenancePriority.HIGH

@pytest.mark.asyncio
async def test_create_maintenance_due_notification_bad_date_raises(monkeypatch):
    svc = make_service()
    async def passthru(data): return data
    monkeypatch.setattr(svc, "create_notification", passthru)
    rec = {"id": "r3", "vehicle_id": "V3", "title": "X", "scheduled_date": None}
    with pytest.raises(Exception):
        await svc.create_maintenance_due_notification(rec)

@pytest.mark.asyncio
async def test_create_license_expiry_notification_high_vs_medium_and_vehicle_id(monkeypatch):
    svc = make_service()
    async def passthru(data): return data
    monkeypatch.setattr(svc, "create_notification", passthru)
    soon = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
    later = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")
    rec_soon = {"id": "L1", "entity_id": "V9", "entity_type": "vehicle", "license_type": "roadworthy", "expiry_date": soon}
    rec_later = {"id": "L2", "entity_id": "D1", "entity_type": "driver", "license_type": "permit", "expiry_date": later}
    out1 = await svc.create_license_expiry_notification(rec_soon)
    out2 = await svc.create_license_expiry_notification(rec_later)
    assert out1["priority"] == MaintenancePriority.HIGH and out1["vehicle_id"] == "V9"
    assert out2["priority"] == MaintenancePriority.MEDIUM and out2["vehicle_id"] is None
    assert "expires in" in out1["message"]

@pytest.mark.asyncio
async def test_create_license_expiry_notification_bad_date_raises(monkeypatch):
    svc = make_service()
    async def passthru(data): return data
    monkeypatch.setattr(svc, "create_notification", passthru)
    rec = {"id": "L3", "entity_id": "X", "entity_type": "vehicle", "license_type": "roadworthy", "expiry_date": "bad"}
    with pytest.raises(Exception):
        await svc.create_license_expiry_notification(rec)

@pytest.mark.asyncio
async def test_create_overdue_maintenance_notification_string_and_datetime(monkeypatch):
    svc = make_service()
    async def passthru(data): return data
    monkeypatch.setattr(svc, "create_notification", passthru)
    fixed_now = datetime(2030, 1, 10, 12, 0, 0)
    class FixedDT(datetime):
        @classmethod
        def utcnow(cls): return fixed_now
    import types as _types
    patched_datetime = _types.SimpleNamespace(
        utcnow=FixedDT.utcnow,
        fromisoformat=datetime.fromisoformat,
        __name__="datetime"
    )
    import types as _t
    patched_datetime = _t.SimpleNamespace(utcnow=FixedDT.utcnow, fromisoformat=datetime.fromisoformat)
    import builtins
    setattr(ns_mod, "datetime", patched_datetime)  # patch module's datetime usage (utcnow/fromisoformat)
    rec_str = {"id": "r4", "vehicle_id": "V4", "title": "T", "scheduled_date": "2030-01-07T12:00:00"}
    out1 = await svc.create_overdue_maintenance_notification(rec_str)
    assert out1["priority"] == MaintenancePriority.CRITICAL and "overdue" in out1["message"]
    setattr(ns_mod, "datetime", patched_datetime)
    class Dummy: pass
    setattr(ns_mod, "datetime", types.SimpleNamespace(utcnow=FixedDT.utcnow, fromisoformat=datetime.fromisoformat))
    rec_dt = {"id": "r5", "vehicle_id": "V5", "title": "T", "scheduled_date": datetime(2030, 1, 8, 12, 0, 0)}
    out2 = await svc.create_overdue_maintenance_notification(rec_dt)
    assert out2["priority"] == MaintenancePriority.CRITICAL and "overdue" in out2["message"]
    setattr(ns_mod, "datetime", importlib.import_module("datetime"))

@pytest.mark.asyncio
async def test_create_overdue_maintenance_notification_bad_date_raises(monkeypatch):
    svc = make_service()
    async def passthru(data): return data
    monkeypatch.setattr(svc, "create_notification", passthru)
    rec = {"id": "r6", "vehicle_id": "V6", "title": "T", "scheduled_date": None}
    with pytest.raises(Exception):
        await svc.create_overdue_maintenance_notification(rec)

@pytest.mark.asyncio
async def test_create_maintenance_completed_notification_defaults_and_cost(monkeypatch):
    svc = make_service()
    async def passthru(data): return data
    monkeypatch.setattr(svc, "create_notification", passthru)
    out1 = await svc.create_maintenance_completed_notification({"id": "r7", "vehicle_id": "V7", "title": "T"})
    out2 = await svc.create_maintenance_completed_notification({"id": "r8", "vehicle_id": "V8", "title": "T", "actual_cost": 123.4})
    assert out1["priority"] == MaintenancePriority.LOW and "$0.00" in out1["message"]
    assert out2["priority"] == MaintenancePriority.LOW and "$123.40" in out2["message"]
    assert out1["recipient_roles"] == ["fleet_manager"]

@pytest.mark.asyncio
async def test_process_pending_notifications_counts_and_continues(monkeypatch):
    svc = make_service()
    svc.repository.pending = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    sent = []
    async def good(nid): sent.append(nid); return True
    async def bad(nid): raise RuntimeError("x")
    calls = {"i": 0}
    async def mark(nid):
        calls["i"] += 1
        return await (good if calls["i"] != 2 else bad)(nid)
    monkeypatch.setattr(svc, "send_notification", mark)
    count = await svc.process_pending_notifications()
    assert count == 2 and sent == ["a", "c"]

@pytest.mark.asyncio
async def test_process_pending_notifications_no_pending_and_repo_error(monkeypatch):
    svc = make_service()
    svc.repository.pending = []
    assert await svc.process_pending_notifications() == 0
    async def boom(): raise RuntimeError("fail")
    monkeypatch.setattr(svc, "get_pending_notifications", boom)
    with pytest.raises(RuntimeError):
        await svc.process_pending_notifications()
