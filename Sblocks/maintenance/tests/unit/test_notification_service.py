# SAMFMS/Sblocks/maintenance/tests/unit/test_notification_service.py
import pytest
from datetime import datetime, date, timedelta

from services import notification_service as mod


@pytest.mark.asyncio
async def test_create_notification_validates_and_sets_defaults(mocker):
    svc = mod.NotificationService()
    called = {}
    async def _create(d): called["data"] = d; return {"id": "N1", **d}
    mocker.patch.object(svc.repository, "create", side_effect=_create)

    data = {"title": "T", "message": "M", "notification_type": "maintenance_due"}
    rec = await svc.create_notification(data)
    assert rec["id"] == "N1"
    assert rec["priority"] == mod.MaintenancePriority.MEDIUM
    assert rec["is_sent"] is False and rec["is_read"] is False
    assert called["data"]["recipient_user_ids"] == [] and called["data"]["recipient_roles"] == []


@pytest.mark.asyncio
async def test_create_notification_parses_scheduled_time(mocker):
    svc = mod.NotificationService()
    mocker.patch.object(svc.repository, "create", side_effect=lambda d: d)
    d = await svc.create_notification({"title": "t","message":"m","notification_type":"x","scheduled_send_time": "2024-01-01T00:00:00Z"})
    assert isinstance(d["scheduled_send_time"], datetime)


@pytest.mark.asyncio
async def test_create_notification_missing_field_raises():
    svc = mod.NotificationService()
    with pytest.raises(ValueError):
        await svc.create_notification({"title": "T", "message": "M"})  # missing notification_type


@pytest.mark.asyncio
async def test_send_mark_get_pending_user_notifications_passthrough(mocker):
    svc = mod.NotificationService()
    mocker.patch.object(svc.repository, "mark_as_sent", return_value=None)
    assert await svc.send_notification("N1") is True
    mocker.patch.object(svc.repository, "get_pending_notifications", return_value=[{"id": "N"}])
    assert len(await svc.get_pending_notifications()) == 1
    mocker.patch.object(svc.repository, "get_user_notifications", return_value=[{"id": "N"}])
    assert len(await svc.get_user_notifications("u", True)) == 1
    mocker.patch.object(svc.repository, "mark_as_read", return_value=None)
    assert await svc.mark_notification_read("N1") is True


@pytest.mark.asyncio
async def test_create_maintenance_due_notification_builds_payload(mocker):
    svc = mod.NotificationService()
    mocker.patch.object(svc, "create_notification", return_value={"id": "N"})
    rec = {"vehicle_id": "veh1", "title": "Brake", "priority": mod.MaintenancePriority.HIGH, "scheduled_date": "2025-02-01T10:00:00Z", "id": "R1"}
    res = await svc.create_maintenance_due_notification(rec)
    assert res["id"] == "N"
    svc.create_notification.assert_called_once()
    payload = svc.create_notification.call_args[0][0]
    assert payload["notification_type"] == "maintenance_due" and "Vehicle veh1" in payload["title"]


@pytest.mark.asyncio
async def test_create_license_expiry_notification_priority_threshold(mocker):
    svc = mod.NotificationService()
    mocker.patch.object(svc, "create_notification", return_value={"id": "N"})
    # within 7 days -> HIGH
    lic = {"entity_id": "veh1", "entity_type": "vehicle", "license_type": "roadworthy", "expiry_date": (date.today() + timedelta(days=3)).isoformat(), "id":"L1"}
    await svc.create_license_expiry_notification(lic)
    assert svc.create_notification.call_args[0][0]["priority"] == mod.MaintenancePriority.HIGH
    # >7 days -> MEDIUM
    svc.create_notification.reset_mock()
    lic["expiry_date"] = (date.today() + timedelta(days=30)).isoformat()
    await svc.create_license_expiry_notification(lic)
    assert svc.create_notification.call_args[0][0]["priority"] == mod.MaintenancePriority.MEDIUM


@pytest.mark.asyncio
async def test_create_overdue_and_completed_notifications(mocker):
    svc = mod.NotificationService()
    mocker.patch.object(svc, "create_notification", return_value={"id":"N"})
    m = {"vehicle_id":"v","title":"t","scheduled_date": (datetime.utcnow() - timedelta(days=2)).isoformat(), "id":"R1"}
    await svc.create_overdue_maintenance_notification(m)
    assert svc.create_notification.call_args[0][0]["notification_type"] == "maintenance_overdue"
    svc.create_notification.reset_mock()
    await svc.create_maintenance_completed_notification({"vehicle_id":"v","title":"t","actual_cost": 123.4, "id":"R2"})
    assert svc.create_notification.call_args[0][0]["priority"] == mod.MaintenancePriority.LOW
