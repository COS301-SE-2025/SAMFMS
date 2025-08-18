import pytest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from services.background_jobs import MaintenanceBackgroundJobs

@pytest.fixture
def jobs():
    return MaintenanceBackgroundJobs()

@pytest.mark.asyncio
async def test_start_background_jobs_creates_tasks(mocker, jobs):
    # stub create_task to return fake task objects
    class FakeTask:
        def cancel(self): ...
    mocker.patch("services.background_jobs.asyncio.create_task", return_value=FakeTask())
    await jobs.start_background_jobs()
    assert jobs.is_running is True
    assert len(jobs.tasks) == 4

@pytest.mark.asyncio
async def test_stop_background_jobs_cancels_and_clears(mocker, jobs):
    class FakeTask:
        cancelled = False
        def cancel(self): self.cancelled = True
    jobs.is_running = True
    jobs.tasks = [FakeTask(), FakeTask()]
    # don't actually sleep
    mocker.patch("services.background_jobs.asyncio.gather", new=AsyncMock(return_value=None))
    await jobs.stop_background_jobs()
    assert jobs.is_running is False
    assert jobs.tasks == []


@pytest.mark.asyncio
async def test_generate_overdue_notification_calls_service(mocker, jobs):
    from unittest.mock import AsyncMock
    import services.notification_service as ns
    from datetime import datetime, timedelta

    mocker.object(ns, "notification_service", new=AsyncMock(), create=True)
    rec = {
        "vehicle_id": "V1",
        "id": "R1",
        "title": "oil change",
        "status": "overdue",
        "scheduled_date": datetime.utcnow() - timedelta(days=10),
    }
    await jobs._generate_overdue_notification(rec)
    ns.notification_service.create_notification.assert_called_once()

@pytest.mark.asyncio
async def test_generate_license_expiry_notification_priority(mocker, jobs):
    from unittest.mock import AsyncMock
    import services.notification_service as ns
    from datetime import datetime, timedelta

    mocker.object(ns, "notification_service", new=AsyncMock(), create=True)
    lic = {
        "entity_id": "V1",
        "id": "L1",
        "license_type": "roadworthy",
        "expiry_date": datetime.utcnow() + timedelta(days=5),
        "is_active": True,
        "advance_notice_days": 30,
    }
    await jobs._generate_license_expiry_notification(lic)
    ns.notification_service.create_notification.assert_called_once()

@pytest.mark.asyncio
async def test_generate_reminder_notification_calls_service(mocker, jobs):
    from unittest.mock import AsyncMock
    import services.notification_service as ns
    from datetime import datetime, timedelta

    mocker.object(ns, "notification_service", new=AsyncMock(), create=True)
    rec = {
        "vehicle_id": "V1",
        "id": "R1",
        "title": "inspection",
        "status": "scheduled",
        "scheduled_date": datetime.utcnow() + timedelta(days=3),
        "is_active": True,
    }
    await jobs._generate_reminder_notification(rec)
    ns.notification_service.create_notification.assert_called_once()