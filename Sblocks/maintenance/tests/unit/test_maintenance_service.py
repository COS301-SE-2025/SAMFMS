# SAMFMS/Sblocks/maintenance/tests/unit/test_maintenance_service.py
import pytest
from datetime import datetime, timedelta

from services import maintenance_service as mod



@pytest.mark.asyncio
async def test_create_maintenance_record_validates_and_sets_defaults(mocker, set_vehicle_validator):
    set_vehicle_validator(True)
    svc = mod.MaintenanceRecordsService()

    async def _create(data): return {"id": "R1", **data}
    mocker.patch.object(svc.repository, "create", side_effect=_create)
    # Avoid side effects in notifications
    mocker.patch("services.notification_service.notification_service.create_notification", return_value={"id": "N1"})

    data = {
        "vehicle_id": "veh1",
        "maintenance_type": "brake",
        "scheduled_date": datetime.utcnow().isoformat() + "Z",
        "title": "Brake check",
        "mileage_at_service": 10000
    }
    rec = await svc.create_maintenance_record(data)
    assert rec["id"] == "R1"
    # 'brake' => HIGH per service logic
    assert rec["priority"] == mod.MaintenancePriority.HIGH
    assert "next_service_mileage" in rec and rec["next_service_mileage"] > 10000


@pytest.mark.asyncio
async def test_create_maintenance_record_invalid_vehicle_raises(set_vehicle_validator):
    set_vehicle_validator(False)
    svc = mod.MaintenanceRecordsService()
    with pytest.raises(ValueError):
        await svc.create_maintenance_record({
            "vehicle_id": "vehX", "maintenance_type": "oil_change",
            "scheduled_date": datetime.utcnow().isoformat(), "title": "Oil"
        })


@pytest.mark.asyncio
async def test_update_maintenance_record_status_transitions(mocker, set_vehicle_validator):
    set_vehicle_validator(True)
    svc = mod.MaintenanceRecordsService()

    # Track what was sent to update
    captured = {}
    async def _update(_id, data):
        captured.update(id=_id, data=data)
        return {"id": _id, **data}
    mocker.patch.object(svc.repository, "update", side_effect=_update)

    # Start date -> IN_PROGRESS
    await svc.update_maintenance_record("R1", {"actual_start_date": datetime.utcnow().isoformat() + "Z"})
    assert captured["data"]["status"] == mod.MaintenanceStatus.IN_PROGRESS

    # Completion date -> COMPLETED
    await svc.update_maintenance_record("R1", {"actual_completion_date": datetime.utcnow().isoformat() + "Z"})
    assert captured["data"]["status"] == mod.MaintenanceStatus.COMPLETED


@pytest.mark.asyncio
async def test_delete_maintenance_record_passthrough(mocker):
    svc = mod.MaintenanceRecordsService()
    mocker.patch.object(svc.repository, "delete", return_value=True)
    assert await svc.delete_maintenance_record("R1") is True


@pytest.mark.asyncio
async def test_get_vehicle_maintenance_records_validates_vehicle(mocker, set_vehicle_validator):
    set_vehicle_validator(True)
    svc = mod.MaintenanceRecordsService()
    mocker.patch.object(svc.repository, "get_by_vehicle_id", return_value=[{"id": "R1"}])
    res = await svc.get_vehicle_maintenance_records("veh1", skip=1, limit=5)
    assert res and res[0]["id"] == "R1"

    set_vehicle_validator(False)
    with pytest.raises(ValueError):
        await svc.get_vehicle_maintenance_records("vehX")


@pytest.mark.asyncio
async def test_get_overdue_maintenance_updates_status(mocker):
    svc = mod.MaintenanceRecordsService()
    overdue = [{"id": "R1", "status": mod.MaintenanceStatus.SCHEDULED}]
    mocker.patch.object(svc.repository, "get_overdue_maintenance", return_value=overdue)
    mocker.patch.object(svc.repository, "update", return_value={"id": "R1", "status": mod.MaintenanceStatus.OVERDUE})
    res = await svc.get_overdue_maintenance()
    assert res[0]["status"] == mod.MaintenanceStatus.OVERDUE


@pytest.mark.asyncio
async def test_get_maintenance_history_parses_dates_and_calls_repo(mocker, set_vehicle_validator):
    set_vehicle_validator(True)
    svc = mod.MaintenanceRecordsService()
    called = {}
    async def _get_hist(vehicle_id, start, end):
        called.update(vehicle_id=vehicle_id, start=start, end=end); return []
    mocker.patch.object(svc.repository, "get_maintenance_history", side_effect=_get_hist)
    await svc.get_maintenance_history("veh1", start_date="2024-01-01T00:00:00Z", end_date="2024-02-01T00:00:00Z")
    assert called["start"].isoformat().startswith("2024-01-01")
    assert called["end"].isoformat().startswith("2024-02-01")


@pytest.mark.asyncio
async def test_get_maintenance_cost_summary_parses_dates(mocker):
    svc = mod.MaintenanceRecordsService()
    called = {}
    mocker.patch.object(svc.repository, "get_cost_summary", side_effect=lambda v, s, e: {"ok": True, "v": v, "s": s, "e": e})
    res = await svc.get_maintenance_cost_summary("veh1", "2024-01-01T00:00:00Z", "2024-01-31T00:00:00Z")
    assert res["v"] == "veh1" and res["s"].isoformat().startswith("2024-01-01")


@pytest.mark.asyncio
async def test_search_maintenance_records_builds_query_and_sort(mocker):
    svc = mod.MaintenanceRecordsService()
    captured = {}
    async def _find(q, skip, limit, sort):
        captured.update(q=q, skip=skip, limit=limit, sort=sort); return []
    mocker.patch.object(svc.repository, "find", side_effect=_find)
    await svc.search_maintenance_records(
        {"vehicle_id": "veh1", "status": "open", "maintenance_type": "oil_change", "priority": "high",
         "vendor_id": "v1", "technician_id": "t1", "scheduled_from": "2024-01-01T00:00:00Z", "scheduled_to": "2024-01-31T00:00:00Z"},
        skip=0, limit=10, sort_by="scheduled_date", sort_order="asc"
    )
    assert "scheduled_date" in captured["q"]
    assert captured["sort"][0] == ("scheduled_date", 1)


@pytest.mark.asyncio
async def test_generate_automatic_notifications_only_future_dates(mocker):
    svc = mod.MaintenanceRecordsService()
    # Past scheduled date -> no create_notification
    past = {"vehicle_id": "v", "title": "T", "scheduled_date": datetime.utcnow() - timedelta(days=1)}
    cn = mocker.patch("services.notification_service.notification_service.create_notification", return_value={"id": "N"})
    await svc._generate_automatic_notifications(past)
    assert cn.call_count == 0
    # Future (>=3 days) -> create
    future = {"vehicle_id": "v", "title": "T", "scheduled_date": datetime.utcnow() + timedelta(days=10)}
    await svc._generate_automatic_notifications(future)
    assert cn.call_count == 1


@pytest.mark.asyncio
async def test_calculate_maintenance_costs_summarizes_records(mocker):
    svc = mod.MaintenanceRecordsService()
    recs = [
        {"actual_cost": 100, "labor_cost": 40, "parts_cost": 60, "maintenance_type": "oil_change",
         "actual_completion_date": datetime(2024, 1, 15)},
        {"actual_cost": 50, "labor_cost": 10, "parts_cost": 40, "maintenance_type": "inspection",
         "actual_completion_date": datetime(2024, 1, 31)},
    ]
    mocker.patch.object(svc.repository, "find", return_value=recs)
    res = await svc.calculate_maintenance_costs()
    assert res["total_cost"] == 150 and res["record_count"] == 2
    assert res["cost_by_type"]["oil_change"] == 100
    assert res["cost_by_month"]["2024-01"] == 150


@pytest.mark.asyncio
async def test_alias_methods_delegate(mocker):
    svc = mod.MaintenanceRecordsService()
    mocker.patch.object(svc, "get_vehicle_maintenance_records", return_value=[{"id": "R"}])
    assert (await svc.get_maintenance_by_vehicle("veh"))[0]["id"] == "R"
    mocker.patch.object(svc, "get_maintenance_records_by_status", return_value=[{"id": "R"}])
    assert (await svc.get_maintenance_by_status("open"))[0]["id"] == "R"
