import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from services.maintenance_service import MaintenanceRecordsService, MaintenanceStatus, MaintenancePriority

@pytest.fixture
def svc():
    return MaintenanceRecordsService()

@pytest.mark.asyncio
async def test_create_record_validates_required_and_defaults(mocker, svc):
    # vehicle ok
    mocker.object(svc, "repository", AsyncMock(), create=True)
    mocker.object(
        svc, "_auto_set_priority", new=AsyncMock(), create=True
    )
    mocker.object(
        svc, "_calculate_next_service_mileage", new=AsyncMock(return_value=12345), create=True
    )
    # vehicle validator returns True
    from utils.vehicle_validator import vehicle_validator
    mocker.object(vehicle_validator, "validate_vehicle_id", new=AsyncMock(return_value=True))
    d = {
        "vehicle_id":"V1","maintenance_type":"oil_change",
        "scheduled_date": datetime.utcnow().isoformat(),
        "title":"Oil change","mileage_at_service":1000
    }
    svc.repository.create.return_value = {"id":"R1", **d}
    res = await svc.create_maintenance_record(d.copy())
    assert res["id"] == "R1"
    args, _ = svc.repository.create.call_args
    called = args[0]
    assert called["status"] == MaintenanceStatus.SCHEDULED
    assert called["priority"] == MaintenancePriority.MEDIUM
    assert called["next_service_mileage"] == 12345

@pytest.mark.asyncio
async def test_create_record_invalid_vehicle_raises(mocker, svc):
    from utils.vehicle_validator import vehicle_validator
    mocker.object(vehicle_validator, "validate_vehicle_id", new=AsyncMock(return_value=False))
    with pytest.raises(ValueError):
        await svc.create_maintenance_record({
            "vehicle_id":"NOPE","maintenance_type":"oil_change",
            "scheduled_date": datetime.utcnow().isoformat(), "title":"t"
        })

@pytest.mark.asyncio
async def test_update_record_sets_status_on_dates(mocker, svc):
    mocker.object(svc, "repository", AsyncMock(), create=True)
    svc.repository.update.return_value = {"id":"R1"}
    # when actual_start_date set and no status, becomes IN_PROGRESS
    await svc.update_maintenance_record("R1", {"actual_start_date": datetime.utcnow().isoformat()})
    args, _ = svc.repository.update.call_args
    assert args[1]["status"] == MaintenanceStatus.IN_PROGRESS
    # when actual_completion_date set, becomes COMPLETED
    await svc.update_maintenance_record("R1", {"actual_completion_date": datetime.utcnow().isoformat()})
    args, _ = svc.repository.update.call_args
    assert args[1]["status"] == MaintenanceStatus.COMPLETED

@pytest.mark.asyncio
async def test_delete_record_bool(mocker, svc):
    mocker.object(svc, "repository", AsyncMock(), create=True)
    svc.repository.delete.return_value = True
    assert await svc.delete_maintenance_record("R1") is True

@pytest.mark.asyncio
async def test_get_vehicle_maintenance_records_validates_vehicle(mocker, svc):
    from utils.vehicle_validator import vehicle_validator
    mocker.object(vehicle_validator, "validate_vehicle_id", new=AsyncMock(return_value=False))
    with pytest.raises(ValueError):
        await svc.get_vehicle_maintenance_records("NOPE")

@pytest.mark.asyncio
async def test_get_maintenance_records_by_status_passthrough(mocker, svc):
    mocker.object(svc, "repository", AsyncMock(), create=True)
    svc.repository.get_by_status.return_value = [{"id":"R1"}]
    res = await svc.get_maintenance_records_by_status("scheduled")
    assert res == [{"id":"R1"}]

@pytest.mark.asyncio
async def test_get_overdue_maintenance_updates_status(mocker, svc):
    mocker.object(svc, "repository", AsyncMock(), create=True)
    svc.repository.get_overdue_maintenance.return_value = [
        {"id":"R1","status":"scheduled"},
        {"id":"R2","status":"overdue"},
    ]
    svc.repository.update.return_value = {"id":"R1","status":"overdue"}
    res = await svc.get_overdue_maintenance()
    assert res[0]["status"] == MaintenanceStatus.OVERDUE
    assert res[1]["status"] == "overdue"
    svc.repository.update.assert_called_once()

@pytest.mark.asyncio
async def test_get_maintenance_history_parses_dates_and_validates_vehicle(mocker, svc):
    from utils.vehicle_validator import vehicle_validator
    mocker.object(vehicle_validator, "validate_vehicle_id", new=AsyncMock(return_value=True))
    mocker.object(svc, "repository", AsyncMock(), create=True)
    await svc.get_maintenance_history("V1", "2025-01-01T00:00:00Z", "2025-02-01T00:00:00Z")
    args, _ = svc.repository.get_maintenance_history.call_args
    assert args[1].isoformat().startswith("2025-01-01")
    assert args[2].isoformat().startswith("2025-02-01")

@pytest.mark.asyncio
async def test_get_maintenance_cost_summary_parses_dates(mocker, svc):
    mocker.object(svc, "repository", AsyncMock(), create=True)
    await svc.get_maintenance_cost_summary(start_date="2025-01-01T00:00:00Z", end_date="2025-01-31T00:00:00Z")
    args, _ = svc.repository.get_cost_summary.call_args
    assert args[1].isoformat().startswith("2025-01-01")
    assert args[2].isoformat().startswith("2025-01-31")

@pytest.mark.asyncio
async def test_search_maintenance_records_builds_query_and_sort(mocker, svc):
    mocker.object(svc, "repository", AsyncMock(), create=True)
    q = {"vehicle_id":"V1","status":"scheduled","scheduled_from":"2025-01-01T00:00:00Z"}
    await svc.search_maintenance_records(q, skip=2, limit=5, sort_by="scheduled_date", sort_order="asc")
    args, _ = svc.repository.find.call_args
    assert args[0]["vehicle_id"] == "V1"
    assert "$gte" in args[0]["scheduled_date"]
    assert args[3] == [("scheduled_date", 1)]

@pytest.mark.asyncio
async def test_calculate_next_service_mileage_intervals(mocker, svc):
    # default and specific types
    assert await svc._calculate_next_service_mileage("V1","oil_change",1000) == 11000
    assert await svc._calculate_next_service_mileage("V1","unknown",1000) == 16000

@pytest.mark.asyncio
async def test_calculate_maintenance_costs_sums_fields(mocker, svc):
    mocker.object(svc, "repository", AsyncMock(), create=True)
    svc.repository.find.return_value = [
        {"actual_cost": 100, "labor_cost": 60, "parts_cost": 40, "maintenance_type":"t1",
         "actual_completion_date": datetime(2025,1,1)},
        {"actual_cost": 50, "labor_cost": 20, "parts_cost": 30, "maintenance_type":"t1",
         "actual_completion_date": datetime(2025,1,2)},
    ]
    res = await svc.calculate_maintenance_costs()
    assert res["total_cost"] == 150
    assert res["labor_cost"] == 80
    assert res["parts_cost"] == 70
    assert res["average_cost"] == 75
    assert res["cost_by_type"]["t1"] == 150
    assert "2025-01" in res["cost_by_month"]

@pytest.mark.asyncio
async def test_update_overdue_statuses_updates_each(mocker, svc):
    mocker.object(svc, "repository", AsyncMock(), create=True)
    svc.repository.find.return_value = [{"_id":"a"}, {"_id":"b"}]
    svc.repository.update.side_effect = [{"id":"a"}, {"id":"b"}]
    res = await svc.update_overdue_statuses()
    assert [r["id"] for r in res] == ["a","b"]
    assert svc.repository.update.call_count == 2
