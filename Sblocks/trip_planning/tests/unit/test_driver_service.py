import pytest
from datetime import datetime, timedelta
from types import SimpleNamespace

@pytest.mark.asyncio
async def test_get_all_drivers_paginates(fake_db):
    from services.driver_service import DriverService
    svc = DriverService(); svc.db = fake_db; svc.db_management = fake_db.db_management
    fake_db.db_management.drivers.count_documents = AsyncMock(return_value=3)
    fake_db.db_management.drivers.find.side_effect = lambda *a, **k: _FakeCursor([
        {"_id":"1","name":"A"},{"_id":"2","name":"B"}
    ])
    out = await svc.get_all_drivers(status=None, department=None, skip=0, limit=2)
    assert out["total"] == 3 and out["drivers"][0]["id"] == "1" 

@pytest.mark.asyncio
async def test_get_all_active_drivers_collects_recent(fake_db):
    from services.driver_service import DriverService
    svc = DriverService(); svc.db = fake_db
    fake_db.driver_assignments.find = lambda *a, **k: _FakeCursor(
        [{"driver_id": "d1"}, {"driver_id": "d2"}, {"driver_id": "d1"}]
    )
    ids = await svc._get_all_active_drivers()
    assert sorted(ids) == ["d1","d2"]  
@pytest.mark.asyncio
async def test_find_next_available_time_branches(fake_db):
    from services.driver_service import DriverService
    svc = DriverService(); svc.db = fake_db
    after = datetime.utcnow()
    fake_db.trips.find = lambda *a, **k: _FakeCursor([{"scheduled_end_time": after + timedelta(hours=1)}])    
    t = await svc._find_next_available_time("d", after)
    assert t > after  
    fake_db.trips.find = lambda *a, **k: _FakeCursor([{"scheduled_start_time": after}])
    t2 = await svc._find_next_available_time("d", after)
    assert abs((t2 - (after+timedelta(hours=8))).total_seconds()) < 1  
    fake_db.trips.find = lambda *a, **k: _FakeCursor([])
    t3 = await svc._find_next_available_time("d", after)
    assert t3 == after  

