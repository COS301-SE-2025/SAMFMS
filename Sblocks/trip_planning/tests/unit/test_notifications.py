import pytest
from fastapi import HTTPException
import api.routes.notifications as m

class _RBResp:
    def __init__(self, d): self._d = d
    def model_dump(self): return self._d

class RB:
    @staticmethod
    def success(data=None, message=""): return _RBResp({"success": True, "message": message, "data": data})
m.ResponseBuilder = RB  

class _Notif:
    def __init__(self, id="n1", has_oid=False):
        if has_oid:
            self._id = id
        else:
            self.id = id
        self.type = "info"
        self.title = "T"
        self.message = "M"
        self.sent_at = "2024-01-01 00:00:00"
        self.is_read = False
        self.trip_id = None
        self.driver_id = None
        self.data = {}

@pytest.mark.asyncio
async def test_get_notifications_ok(monkeypatch):
    async def _get_user_notifications(user_id, unread_only, limit, skip):
        return ([_Notif("n1"), _Notif("n2", has_oid=True)], 2)
    async def _get_unread_count(user_id): return 1
    monkeypatch.setattr(m.notification_service, "get_user_notifications", _get_user_notifications)
    monkeypatch.setattr(m.notification_service, "get_unread_count", _get_unread_count)

    res = await m.get_notifications(current_user={"user_id":"u1"})
    assert res["data"]["total"] == 2
    assert res["data"]["unread_count"] == 1
    assert len(res["data"]["notifications"]) == 2

@pytest.mark.asyncio
async def test_get_notifications_missing_user():
    with pytest.raises(HTTPException) as e:
        await m.get_notifications(current_user={})
    assert e.value.status_code == 500

class _ReqSend: pass

@pytest.mark.asyncio
async def test_send_notification_ok(monkeypatch):
    async def _send(req): return [_Notif("a"), _Notif("b")]
    monkeypatch.setattr(m.notification_service, "send_notification", _send)
    res = await m.send_notification(_ReqSend(), current_user={"user_id":"u1","role":"admin"})
    assert res["data"]["sent_count"] == 2

@pytest.mark.asyncio
async def test_send_notification_forbidden():
    with pytest.raises(HTTPException) as e:
        await m.send_notification(_ReqSend(), current_user={"user_id":"u1","role":"driver"})
    assert e.value.status_code == 500

@pytest.mark.asyncio
async def test_mark_notification_read_ok(monkeypatch):
    async def _mark(nid, uid): return True
    monkeypatch.setattr(m.notification_service, "mark_notification_read", _mark)
    res = await m.mark_notification_read("n1", current_user={"user_id":"u1"})
    assert res["data"]["marked_read"] is True

@pytest.mark.asyncio
async def test_mark_notification_read_missing_user():
    with pytest.raises(HTTPException) as e:
        await m.mark_notification_read("n1", current_user={})
    assert e.value.status_code == 500

@pytest.mark.asyncio
async def test_get_unread_count_ok(monkeypatch):
    async def _cnt(uid): return 7
    monkeypatch.setattr(m.notification_service, "get_unread_count", _cnt)
    res = await m.get_unread_count(current_user={"user_id":"u1"})
    assert res["data"]["unread_count"] == 7

class _PrefsReq: pass

@pytest.mark.asyncio
async def test_get_notification_preferences_ok(monkeypatch):
    class _Prefs:
        def model_dump(self): return {"email": True}
    async def _get(uid): return _Prefs()
    monkeypatch.setattr(m.notification_service, "get_user_preferences", _get)
    res = await m.get_notification_preferences(current_user={"user_id":"u1"})
    assert res["data"]["email"] is True

@pytest.mark.asyncio
async def test_update_notification_preferences_ok(monkeypatch):
    class _Prefs:
        def model_dump(self): return {"email": False}
    async def _upd(uid, req): return _Prefs()
    monkeypatch.setattr(m.notification_service, "update_user_preferences", _upd)
    res = await m.update_notification_preferences(_PrefsReq(), current_user={"user_id":"u1"})
    assert res["data"]["email"] is False
