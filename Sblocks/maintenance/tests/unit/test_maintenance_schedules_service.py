import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from services.maintenance_schedules_service import MaintenanceSchedulesService

@pytest.fixture
def svc():
    return MaintenanceSchedulesService()

@pytest.mark.asyncio
async def test_create_schedule_validates_and_defaults(mocker, svc):
    mocker.object(svc, "repository", AsyncMock(), create=True)
    from utils.vehicle_validator import vehicle_validator
    mocker.object(vehicle_validator, "validate_vehicle_id", new=AsyncMock(return_value=True))
    data = {"vehicle_id":"V1","maintenance_type":"oil_change","scheduled_date":"2025-01-10T00:00:00Z","title":"Oil"}
    svc.repository.create.return_value = {"id":"S1", **data}
    res = await svc.create_maintenance_schedule(data.copy())
    assert res["id"] == "S1"
    args, _ = svc.repository.create.call_args
    called = args[0]
    assert called["is_active"] is True
    assert isinstance(called["scheduled_date"], datetime)
    assert called["interval_type"] in ("mileage", "time")
    assert "interval_value" in called

@pytest.mark.asyncio
async def test_create_schedule_invalid_vehicle_raises(mocker, svc):
    from utils.vehicle_validator import vehicle_validator
    mocker.object(vehicle_validator, "validate_vehicle_id", new=AsyncMock(return_value=False))
    with pytest.raises(ValueError):
        await svc.create_maintenance_schedule({
            "vehicle_id":"X","maintenance_type":"t","scheduled_date":"2025-01-01T00:00:00Z","title":"t"
        })

@pytest.mark.asyncio
async def test_update_schedule_validates_vehicle_when_changed(mocker, svc):
    mocker.object(svc, "repository", AsyncMock(), create=True)
    from utils.vehicle_validator import vehicle_validator
    mocker.object(vehicle_validator, "validate_vehicle_id", new=AsyncMock(return_value=True))
    await svc.update_maintenance_schedule("S1", {"vehicle_id":"V2","last_service_date":"2025-01-01T00:00:00Z"})
    args, _ = svc.repository.update.call_args
    assert isinstance(args[1]["last_service_date"], datetime)

def test_get_default_interval_has_fallback(svc):
    assert svc._get_default_interval("oil_change") > 0
    assert svc._get_default_interval("unknown") == 15000

def test_is_schedule_due_logic(svc):
    now = datetime.utcnow()
    assert svc._is_schedule_due({"is_active": True, "scheduled_date": now - timedelta(days=1)}, now) is True
    assert svc._is_schedule_due({"is_active": True, "next_due_date": now + timedelta(days=1)}, now) is False
    assert svc._is_schedule_due({"is_active": False, "scheduled_date": now - timedelta(days=1)}, now) is False

@pytest.mark.asyncio
async def test_calculate_next_due_time_and_mileage(mocker, svc):
    data = {"interval_type":"time","interval_value":30,"last_service_date":"2025-01-01T00:00:00Z"}
    await svc._calculate_next_due(data)
    assert "next_due_date" in data
    data2 = {"interval_type":"mileage","interval_value":10000,"last_service_mileage":5000}
    await svc._calculate_next_due(data2)
    assert data2["next_due_mileage"] == 15000

@pytest.mark.asyncio
async def test_get_due_schedules_filters_by_due(mocker, svc):
    mocker.object(svc, "repository", AsyncMock(), create=True)
    now = datetime.utcnow()
    svc.repository.get_active_schedules.return_value = [
        {"id":"a","is_active":True,"scheduled_date":now - timedelta(days=1)},
        {"id":"b","is_active":True,"scheduled_date":now + timedelta(days=1)},
    ]
    res = await svc.get_due_schedules()
    assert [s["id"] for s in res] == ["a"]

@pytest.mark.asyncio
async def test_create_record_from_schedule_happy_path(mocker, svc):
    mocker.object(svc, "repository", AsyncMock(), create=True)
    svc.repository.get_by_id = AsyncMock(return_value={
        "id":"S1","vehicle_id":"V1","maintenance_type":"oil_change","scheduled_date": datetime.utcnow()
    })
    # patch global maintenance_records_service
    import services.maintenance_service as ms
    mocker.object(ms, "maintenance_records_service", new=AsyncMock(), create=True)
    ms.maintenance_records_service.create_maintenance_record.return_value = {"id":"R1","vehicle_id":"V1"}
    svc.repository.update.return_value = {"id":"S1"}

    res = await svc.create_record_from_schedule("S1")
    assert res["id"] == "R1"
    svc.repository.update.assert_called_once()
