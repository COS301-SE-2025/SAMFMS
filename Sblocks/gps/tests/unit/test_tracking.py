import pytest
from api.routes import tracking as mod

class Obj:
    def __init__(self, **d): self.__dict__.update(d)
    def model_dump(self): return dict(self.__dict__)

class RB:
    @staticmethod
    def success(*, data, message, request_id=None, execution_time_ms=None):
        return Obj(success=True, data=data, message=message, request_id=request_id, execution_time_ms=execution_time_ms)


@pytest.mark.asyncio
async def test_start_tracking_session_ok(client, monkeypatch):
    async def fake_start_tracking_session(**kwargs): return Obj(id="s1", vehicle_id=kwargs["vehicle_id"])
    monkeypatch.setattr(mod.location_service, "start_tracking_session", fake_start_tracking_session)
    resp = await client.post("/tracking/sessions", json={"vehicle_id": "veh-1"})
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == "s1"

@pytest.mark.asyncio
async def test_end_tracking_session_404_when_false(client, monkeypatch):
    async def fake_end_tracking_session(session_id): return False
    monkeypatch.setattr(mod.location_service, "end_tracking_session", fake_end_tracking_session)
    resp = await client.delete("/tracking/sessions/does-not-exist")
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_get_active_tracking_sessions_defaults_user_id(client, monkeypatch):
    captured = {}
    async def fake_get_active(user_id):
        captured["user_id"] = user_id
        return [Obj(id="s1")]
    monkeypatch.setattr(mod.location_service, "get_active_tracking_sessions", fake_get_active)
    resp = await client.get("/tracking/sessions")
    assert resp.status_code == 200
    assert captured["user_id"] == "test-user"  # auto-filled for non-admin
