import pytest

from api.routes import notifications as routes


# ---------- Helpers ----------

class _Timer:
    request_id = "req-1"

    @property
    def elapsed(self):
        return 42


@pytest.fixture
def fake_timer():
    return _Timer()


@pytest.fixture
def rb_success(mocker):
    """Patch ResponseBuilder.success to return a simple dict of the payload."""
    def _success(**kwargs):
        return kwargs
    return mocker.patch("api.routes.notifications.ResponseBuilder.success", side_effect=_success)


@pytest.fixture
def rb_error(mocker):
    def _error(**kwargs):
        return kwargs
    return mocker.patch("api.routes.notifications.ResponseBuilder.error", side_effect=_error)


# ---------- /notifications/pending ----------

@pytest.mark.asyncio
async def test_get_pending_notifications_success(mocker, rb_success, fake_timer):
    mocker.patch.object(
        routes.notification_service,
        "get_pending_notifications",
        return_value=[{"_id": "n1"}, {"_id": "n2"}],
        autospec=True,
    )
    res = await routes.get_pending_notifications(user={"user_id": "u"}, timer=fake_timer)
    assert res["data"] == [{"_id": "n1"}, {"_id": "n2"}]
    assert res["metadata"]["total"] == 2
    assert res["message"] == "Pending notifications retrieved successfully"


@pytest.mark.asyncio
async def test_get_pending_notifications_error(mocker, rb_error, fake_timer):
    mocker.patch.object(
        routes.notification_service,
        "get_pending_notifications",
        side_effect=Exception("boom"),
        autospec=True,
    )
    res = await routes.get_pending_notifications(user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 500


# ---------- /notifications/user/{user_id} ----------

@pytest.mark.asyncio
async def test_get_user_notifications_success_all(mocker, rb_success, fake_timer):
    mocker.patch.object(
        routes.notification_service,
        "get_user_notifications",
        return_value=[{"_id": "n1"}],
        autospec=True,
    )
    user_id = "a" * 24
    res = await routes.get_user_notifications(
        user_id=user_id, unread_only=False, user={"user_id": "u"}, timer=fake_timer
    )
    assert res["data"] == [{"_id": "n1"}]
    assert res["metadata"]["user_id"] == user_id
    assert res["message"] == f"Notifications for user {user_id} retrieved successfully"


@pytest.mark.asyncio
async def test_get_user_notifications_success_unread_only(mocker, rb_success, fake_timer):
    mocker.patch.object(
        routes.notification_service,
        "get_user_notifications",
        return_value=[{"_id": "n1"}],
        autospec=True,
    )
    user_id = "b" * 24
    res = await routes.get_user_notifications(
        user_id=user_id, unread_only=True, user={"user_id": "u"}, timer=fake_timer
    )
    assert res["metadata"]["unread_only"] is True
    assert res["message"] == f"Unread notifications for user {user_id} retrieved successfully"


@pytest.mark.asyncio
async def test_get_user_notifications_error(mocker, rb_error, fake_timer):
    mocker.patch.object(
        routes.notification_service,
        "get_user_notifications",
        side_effect=Exception("boom"),
        autospec=True,
    )
    res = await routes.get_user_notifications(
        user_id="c" * 24, unread_only=False, user={"user_id": "u"}, timer=fake_timer
    )
    assert res["status_code"] == 500


# ---------- /notifications/process ----------

@pytest.mark.asyncio
async def test_process_pending_notifications_success(mocker, rb_success, fake_timer):
    mocker.patch.object(
        routes.notification_service,
        "process_pending_notifications",
        return_value=5,
        autospec=True,
    )
    res = await routes.process_pending_notifications(user={"user_id": "u"}, timer=fake_timer)
    assert res["data"] == {"sent_count": 5}
    assert "Processed and sent 5 notifications" in res["message"]


@pytest.mark.asyncio
async def test_process_pending_notifications_error(mocker, rb_error, fake_timer):
    mocker.patch.object(
        routes.notification_service,
        "process_pending_notifications",
        side_effect=Exception("boom"),
        autospec=True,
    )
    res = await routes.process_pending_notifications(user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 500


# ---------- /notifications/{id}/read ----------

@pytest.mark.asyncio
async def test_mark_notification_read_success(mocker, rb_success, fake_timer):
    mocker.patch.object(
        routes.notification_service,
        "mark_notification_read",
        return_value=True,
        autospec=True,
    )
    res = await routes.mark_notification_read(notification_id="d" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert res["message"] == "Notification marked as read"


@pytest.mark.asyncio
async def test_mark_notification_read_not_found(mocker, rb_error, fake_timer):
    mocker.patch.object(
        routes.notification_service,
        "mark_notification_read",
        return_value=False,
        autospec=True,
    )
    res = await routes.mark_notification_read(notification_id="e" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 404


@pytest.mark.asyncio
async def test_mark_notification_read_error(mocker, rb_error, fake_timer):
    mocker.patch.object(
        routes.notification_service,
        "mark_notification_read",
        side_effect=Exception("boom"),
        autospec=True,
    )
    res = await routes.mark_notification_read(notification_id="f" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 500


# ---------- /notifications/{id}/send ----------

@pytest.mark.asyncio
async def test_send_notification_success(mocker, rb_success, fake_timer):
    mocker.patch.object(
        routes.notification_service,
        "send_notification",
        return_value=True,
        autospec=True,
    )
    res = await routes.send_notification(notification_id="1" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert res["message"] == "Notification sent successfully"


@pytest.mark.asyncio
async def test_send_notification_not_found(mocker, rb_error, fake_timer):
    mocker.patch.object(
        routes.notification_service,
        "send_notification",
        return_value=False,
        autospec=True,
    )
    res = await routes.send_notification(notification_id="2" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 404


@pytest.mark.asyncio
async def test_send_notification_error(mocker, rb_error, fake_timer):
    mocker.patch.object(
        routes.notification_service,
        "send_notification",
        side_effect=Exception("boom"),
        autospec=True,
    )
    res = await routes.send_notification(notification_id="3" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 500
