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
