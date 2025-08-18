
from unittest.mock import AsyncMock
import pytest
from datetime import datetime, timedelta, date

from services import notification_service as ns_mod
from services.notification_service import NotificationService


@pytest.fixture
def svc():
    return NotificationService()


@pytest.mark.asyncio
async def test_create_notification_validates_required_fields(svc):
    with pytest.raises(ValueError):
        await svc.create_notification({"title": "t"})  # missing fields


@pytest.mark.asyncio
async def test_create_notification_sets_defaults_and_parses_time(mocker, svc):
    repo = svc.repository
    captured = {}
    async def _create(data):
        captured["data"] = data
        return {"id": "N1", **data}
    mocker.object(repo, "create", _create)

    when = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    doc = await svc.create_notification({
        "title": "T", "message": "M", "notification_type": "maintenance_due",
        "scheduled_send_time": when
    })
    assert doc["id"] == "N1"
    assert captured["data"]["is_read"] is False
    assert isinstance(captured["data"]["scheduled_send_time"], datetime)


@pytest.mark.asyncio
async def test_send_notification_marks_sent(mocker, svc):
    called = {}
    async def _mark(_id): called["id"] = _id
    mocker.object(svc.repository, "mark_as_sent", _mark)
    ok = await svc.send_notification("ABC")
    assert ok is True and called["id"] == "ABC"


@pytest.mark.asyncio
async def test_get_pending_notifications_passthrough(mocker, svc):
    # repo method is awaited -> use AsyncMock (and create=True in case attribute doesn't exist)
    mocker.object(
        svc.repository,
        "get_pending_notifications",
        new=AsyncMock(return_value=[{"id": "n1"}]),
        create=True,
    )
    res = await svc.get_pending_notifications()
    assert res == [{"id": "n1"}]



@pytest.mark.asyncio
async def test_get_user_notifications_passthrough(mocker, svc):
    async def _meth(uid, unread_only): return [{"uid": uid, "unread": unread_only}]
    mocker.object(svc.repository, "get_user_notifications", _meth)
    res = await svc.get_user_notifications("U1", True)
    assert res[0]["uid"] == "U1" and res[0]["unread"] is True


@pytest.mark.asyncio
async def test_mark_notification_read_calls_repo(mocker, svc):
    called = {}
    async def _mark(_id): called["id"] = _id
    mocker.object(svc.repository, "mark_as_read", _mark)
    ok = await svc.mark_notification_read("N9")
    assert ok is True and called["id"] == "N9"


@pytest.mark.asyncio
async def test_create_maintenance_due_notification_builds_payload(mocker, svc):
    created = {}
    async def _create(data):
        created["data"] = data
        return {"id": "X"}
    mocker.object(svc, "create_notification", _create)

    scheduled = datetime.utcnow() + timedelta(days=2)
    await svc.create_maintenance_due_notification({
        "vehicle_id": "V1", "scheduled_date": scheduled, "title": "Oil"
    })
    assert created["data"]["notification_type"] == "maintenance_due"
    assert created["data"]["vehicle_id"] == "V1"


@pytest.mark.asyncio
async def test_create_license_expiry_notification_priority(mocker, svc):
    created = {}
    async def _create(d): created["data"] = d; return {"id": "Y"}
    mocker.object(svc, "create_notification", _create)

    # expires in <=7 days => HIGH
    exp = (date.today() + timedelta(days=3)).isoformat()
    await svc.create_license_expiry_notification({
        "entity_id": "veh1", "entity_type": "vehicle", "license_type": "roadworthy",
        "expiry_date": exp
    })
    assert created["data"]["notification_type"] == "license_expiry"
    assert created["data"]["priority"] == "high"


@pytest.mark.asyncio
async def test_create_overdue_maintenance_notification_sets_critical(mocker, svc):
    created = {}
    async def _create(d): created["data"] = d; return {"id": "Z"}
    mocker.object(svc, "create_notification", _create)

    past = datetime.utcnow() - timedelta(days=5)
    await svc.create_overdue_maintenance_notification({
        "vehicle_id": "V2", "scheduled_date": past, "title": "Brakes"
    })
    assert created["data"]["notification_type"] == "maintenance_overdue"
    assert created["data"]["priority"] == "critical"


@pytest.mark.asyncio
async def test_create_maintenance_completed_notification_sets_low(mocker, svc):
    created = {}
    async def _create(d): created["data"] = d; return {"id": "C"}
    mocker.object(svc, "create_notification", _create)

    await svc.create_maintenance_completed_notification({
        "vehicle_id": "V3", "actual_cost": 123.45
    })
    assert created["data"]["notification_type"] == "maintenance_completed"
    assert created["data"]["priority"] == "low"


@pytest.mark.asyncio
async def test_process_pending_notifications_counts_success(mocker, svc):
    mocker.object(
        svc,
        "get_pending_notifications",
        new=AsyncMock(return_value=[{"id": "a"}, {"id": "b"}]),
        create=True,
    )
    sent = []

    async def _send(notification_id):
        sent.append(notification_id)
        return True

    mocker.object(svc, "send_notification", new=_send, create=True)

    count = await svc.process_pending_notifications()
    assert count == 2 and sent == ["a", "b"]
