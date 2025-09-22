# test_servicesBackground_Jobs.py
import sys
import os
import types
import asyncio
from datetime import datetime, timedelta

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

# ----- services stubs so imports succeed anywhere -----
if "services" not in sys.modules:
    services_pkg = types.ModuleType("services")
    sys.modules["services"] = services_pkg
else:
    services_pkg = sys.modules["services"]

def _ensure_submodule(name):
    full = f"services.{name}"
    if full not in sys.modules:
        m = types.ModuleType(full)
        setattr(services_pkg, name, m)
        sys.modules[full] = m
    return sys.modules[full]

_ensure_submodule("maintenance_service")
_ensure_submodule("notification_service")
_ensure_submodule("license_service")

class _DummyMaint:
    async def update_overdue_statuses(self): return []
    async def get_upcoming_maintenance(self, days): return []

class _DummyNotif:
    async def get_pending_notifications(self): return []
    async def send_notification(self, n): ...
    async def get_notifications_for_maintenance(self, _): return []
    async def create_notification(self, data): ...

class _DummyLic:
    async def get_expiring_licenses(self, days_ahead=30): return []

sys.modules["services.maintenance_service"].maintenance_records_service = _DummyMaint()
sys.modules["services.notification_service"].notification_service = _DummyNotif()
sys.modules["services.license_service"].license_service = _DummyLic()

# ----- import target module -----
try:
    from services import background_jobs as bg_mod
except Exception:
    import importlib
    bg_mod = importlib.import_module("background_jobs")

MaintenanceBackgroundJobs = bg_mod.MaintenanceBackgroundJobs


# ----- helpers -----
class DummyTask:
    def __init__(self):
        self._cancelled = False
    def cancel(self):
        self._cancelled = True
    def __repr__(self):
        return f"<DummyTask cancelled={self._cancelled}>"

def patch_sleep_run_once(monkeypatch, job):
    """
    Patch asyncio.sleep so each worker loop runs exactly once.
    Critically, we await the ORIGINAL sleep to avoid recursion.
    """
    orig_sleep = asyncio.sleep

    async def _one(*_a, **_k):
        # flip the guard so the while-loop won't iterate again
        job.is_running = False
        # yield control once
        await orig_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", _one)
    return orig_sleep  # returned in case the test needs it


# ----- tests -----

@pytest.mark.asyncio
async def test_start_background_jobs_creates_four_tasks_and_wont_double_start(monkeypatch):
    job = MaintenanceBackgroundJobs()

    async def _noop(_self): return
    monkeypatch.setattr(MaintenanceBackgroundJobs, "_overdue_status_updater", _noop)
    monkeypatch.setattr(MaintenanceBackgroundJobs, "_notification_sender", _noop)
    monkeypatch.setattr(MaintenanceBackgroundJobs, "_license_expiry_checker", _noop)
    monkeypatch.setattr(MaintenanceBackgroundJobs, "_maintenance_reminder_generator", _noop)

    await job.start_background_jobs()
    assert job.is_running is True
    assert len(job.tasks) == 4

    before_ids = list(map(id, job.tasks))
    await job.start_background_jobs()  # should no-op
    after_ids = list(map(id, job.tasks))
    assert before_ids == after_ids

    await job.stop_background_jobs()


@pytest.mark.asyncio
async def test_stop_background_jobs_cancels_and_clears(monkeypatch):
    job = MaintenanceBackgroundJobs()
    job.is_running = True
    job.tasks = [DummyTask() for _ in range(4)]

    async def _fake_gather(*args, **kwargs): return None
    monkeypatch.setattr(asyncio, "gather", _fake_gather)

    await job.stop_background_jobs()
    assert job.is_running is False
    assert job.tasks == []


@pytest.mark.asyncio
async def test_overdue_status_updater_generates_for_each_updated_record(monkeypatch):
    job = MaintenanceBackgroundJobs()
    job.is_running = True

    class MaintStub:
        async def update_overdue_statuses(self):
            return [
                {"id": "m1", "vehicle_id": "v1", "title": "Oil", "scheduled_date": datetime.utcnow() - timedelta(days=2)},
                {"id": "m2", "vehicle_id": "v2", "title": "Brakes", "scheduled_date": datetime.utcnow() - timedelta(days=1)},
            ]

    calls = []
    async def _gen_overdue(self, record):
        calls.append(record["id"])

    monkeypatch.setattr(bg_mod, "maintenance_records_service", MaintStub())
    monkeypatch.setattr(MaintenanceBackgroundJobs, "_generate_overdue_notification", _gen_overdue)
    patch_sleep_run_once(monkeypatch, job)

    await job._overdue_status_updater()
    assert calls == ["m1", "m2"]


@pytest.mark.asyncio
async def test_overdue_status_updater_handles_no_records(monkeypatch):
    job = MaintenanceBackgroundJobs()
    job.is_running = True

    class MaintStub:
        async def update_overdue_statuses(self): return []

    called = False
    async def _gen_overdue(self, record):
        nonlocal called
        called = True

    monkeypatch.setattr(bg_mod, "maintenance_records_service", MaintStub())
    monkeypatch.setattr(MaintenanceBackgroundJobs, "_generate_overdue_notification", _gen_overdue)
    patch_sleep_run_once(monkeypatch, job)

    await job._overdue_status_updater()
    assert called is False


@pytest.mark.asyncio
async def test_notification_sender_sends_each_and_continues_on_errors(monkeypatch):
    job = MaintenanceBackgroundJobs()
    job.is_running = True

    class NotifStub:
        def __init__(self):
            self.sent = []
        async def get_pending_notifications(self):
            return [{"id": "n1"}, {"id": "n2"}]
        async def send_notification(self, n):
            if n["id"] == "n2":
                raise RuntimeError("boom")
            self.sent.append(n["id"])

    stub = NotifStub()
    monkeypatch.setattr(bg_mod, "notification_service", stub)
    patch_sleep_run_once(monkeypatch, job)

    await job._notification_sender()
    assert stub.sent == ["n1"]


@pytest.mark.asyncio
async def test_license_expiry_checker_calls_generator(monkeypatch):
    job = MaintenanceBackgroundJobs()
    job.is_running = True

    class LicStub:
        async def get_expiring_licenses(self, days_ahead=30):
            return [{"id": "L1", "entity_id": "e1", "license_type": "registration",
                     "expiry_date": datetime.utcnow() + timedelta(days=5)}]

    seen = []
    async def _gen(self, lic):
        seen.append(lic["id"])

    monkeypatch.setattr(bg_mod, "license_service", LicStub())
    monkeypatch.setattr(MaintenanceBackgroundJobs, "_generate_license_expiry_notification", _gen)
    patch_sleep_run_once(monkeypatch, job)

    await job._license_expiry_checker()
    assert seen == ["L1"]


@pytest.mark.asyncio
async def test_maintenance_reminder_generator_skips_existing_and_creates_new(monkeypatch):
    job = MaintenanceBackgroundJobs()
    job.is_running = True

    class MaintStub:
        async def get_upcoming_maintenance(self, days):
            return [
                {"id": "r1", "vehicle_id": "v1", "title": "Tires", "scheduled_date": datetime.utcnow() + timedelta(days=3)},
                {"id": "r2", "vehicle_id": "v1", "title": "Filters", "scheduled_date": datetime.utcnow() + timedelta(days=5)},
            ]

    class NotifStub:
        def __init__(self):
            self.created = []
        async def get_notifications_for_maintenance(self, rec_id):
            return [{"id": "existing"}] if rec_id == "r1" else []
        async def create_notification(self, data):
            self.created.append(data["maintenance_record_id"])

    nstub = NotifStub()
    monkeypatch.setattr(bg_mod, "maintenance_records_service", MaintStub())
    monkeypatch.setattr(bg_mod, "notification_service", nstub)
    patch_sleep_run_once(monkeypatch, job)

    await job._maintenance_reminder_generator()
    assert nstub.created == ["r2"]


@pytest.mark.asyncio
async def test_generate_overdue_notification_payload_and_call(monkeypatch):
    captured = {}
    class Notif:
        async def create_notification(self, data):
            captured.update(data)

    monkeypatch.setattr(bg_mod, "notification_service", Notif())

    job = MaintenanceBackgroundJobs()
    record = {
        "id": "m99",
        "vehicle_id": "veh-9",
        "title": "Alignment",
        "scheduled_date": datetime.utcnow() - timedelta(days=10),
        "maintenance_type": "alignment",
        "priority": "high",
    }

    await job._generate_overdue_notification(record)
    assert captured["type"] == "overdue_maintenance"
    assert captured["vehicle_id"] == "veh-9"
    assert captured["maintenance_record_id"] == "m99"
    assert "metadata" in captured and "overdue_days" in captured["metadata"]
    assert isinstance(captured["metadata"]["overdue_days"], int)
    assert captured["metadata"]["overdue_days"] >= 0


@pytest.mark.asyncio
async def test_generate_license_expiry_notification_priority_logic(monkeypatch):
    created = []

    class Notif:
        async def create_notification(self, data):
            created.append(data)

    monkeypatch.setattr(bg_mod, "notification_service", Notif())

    job = MaintenanceBackgroundJobs()

    soon = {
        "id": "Lsoon",
        "entity_id": "e1",
        "license_type": "inspection",
        "expiry_date": datetime.utcnow() + timedelta(days=3),
    }
    later = {
        "id": "Llater",
        "entity_id": "e2",
        "license_type": "registration",
        "expiry_date": datetime.utcnow() + timedelta(days=20),
    }

    await job._generate_license_expiry_notification(soon)
    await job._generate_license_expiry_notification(later)

    prios = [created[0]["priority"], created[1]["priority"]]
    assert prios == ["high", "medium"]


@pytest.mark.asyncio
async def test_generate_reminder_notification_payload(monkeypatch):
    captured = {}
    class Notif:
        async def create_notification(self, data):
            captured.update(data)

    monkeypatch.setattr(bg_mod, "notification_service", Notif())

    job = MaintenanceBackgroundJobs()
    record = {
        "id": "r77",
        "vehicle_id": "v7",
        "title": "Cooling System",
        "maintenance_type": "coolant",
        "scheduled_date": datetime.utcnow() + timedelta(days=12),
    }

    await job._generate_reminder_notification(record)
    assert captured["type"] == "maintenance_reminder"
    assert captured["priority"] == "medium"
    assert captured["vehicle_id"] == "v7"
    assert captured["maintenance_record_id"] == "r77"
    assert "scheduled_date" in captured["metadata"]
    assert "days_until_due" in captured["metadata"]
