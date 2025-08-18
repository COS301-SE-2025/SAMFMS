# SAMFMS/Sblocks/maintenance/tests/unit/test_maintenance_schedules_service.py
import pytest
from datetime import datetime, timedelta

from services import maintenance_schedules_service as mod


@pytest.mark.asyncio
async def test_create_schedule_validates_and_sets_defaults(mocker, set_vehicle_validator):
    set_vehicle_validator(True)
    svc = mod.MaintenanceSchedulesService()
    mocker.patch.object(svc.repository, "create", side_effect=lambda d: {"id": "S1", **d})

    data = {
        "vehicle_id": "veh1",
        "maintenance_type": "oil_change",
        "scheduled_date": "2025-01-10T12:00:00Z",
        "title": "Oil Service"
    }
    rec = await svc.create_maintenance_schedule(data)
    assert rec["id"] == "S1"
    assert rec["is_active"] is True
    assert rec["interval_type"] == "mileage"
    assert isinstance(rec["scheduled_date"], datetime)
    assert rec["interval_value"] == svc._get_default_interval("oil_change")


@pytest.mark.asyncio
async def test_create_schedule_rejects_unknown_vehicle(set_vehicle_validator):
    set_vehicle_validator(False)
    svc = mod.MaintenanceSchedulesService()
    with pytest.raises(ValueError):
        await svc.create_maintenance_schedule({
            "vehicle_id": "missing", "maintenance_type": "oil_change",
            "scheduled_date": datetime.utcnow().isoformat(), "title": "Oil"
        })


@pytest.mark.asyncio
async def test_update_schedule_parses_dates_and_calculates_next_due(mocker, set_vehicle_validator):
    set_vehicle_validator(True)
    svc = mod.MaintenanceSchedulesService()
    captured = {}
    async def _update(_id, data):
        captured.update(id=_id, data=data)
        return {"id": _id, **data}
    mocker.patch.object(svc.repository, "update", side_effect=_update)

    await svc.update_maintenance_schedule("S1", {
        "last_service_date": "2024-01-01T00:00:00Z",
        "interval_type": "time",
        "interval_value": 30
    })
    assert "next_due_date" in captured["data"]


@pytest.mark.asyncio
async def test_get_vehicle_schedules_validates_vehicle(mocker, set_vehicle_validator):
    set_vehicle_validator(True)
    svc = mod.MaintenanceSchedulesService()
    mocker.patch.object(svc.repository, "get_schedules_for_vehicle", return_value=[{"id": "S1"}])
    assert (await svc.get_vehicle_maintenance_schedules("veh1"))[0]["id"] == "S1"
    set_vehicle_validator(False)
    with pytest.raises(ValueError):
        await svc.get_vehicle_maintenance_schedules("vehX")


@pytest.mark.asyncio
async def test_get_active_due_and_delete(mocker):
    svc = mod.MaintenanceSchedulesService()
    now = datetime.utcnow()
    # Active schedules to filter
    schedules = [
        {"id": "S1", "is_active": True, "scheduled_date": now - timedelta(days=1)},  # due
        {"id": "S2", "is_active": True, "next_due_date": now + timedelta(days=1)},   # not due
        {"id": "S3", "is_active": False, "scheduled_date": now - timedelta(days=10)} # inactive
    ]
    mocker.patch.object(svc.repository, "get_active_schedules", return_value=schedules)
    due = await svc.get_due_schedules()
    assert [s["id"] for s in due] == ["S1"]

    mocker.patch.object(svc.repository, "delete", return_value=True)
    assert await svc.delete_maintenance_schedule("S1") is True


def test_get_default_interval_has_fallback():
    svc = mod.MaintenanceSchedulesService()
    assert svc._get_default_interval("unknown_type") == 15000
