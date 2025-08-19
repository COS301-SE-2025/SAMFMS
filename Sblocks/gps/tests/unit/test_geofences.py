import pytest
from api.routes import geofences as mod

class Obj:
    def __init__(self, **d): self.__dict__.update(d)
    def model_dump(self): return dict(self.__dict__)

class RB:
    @staticmethod
    def success(*, data, message, request_id=None, execution_time_ms=None):
        return Obj(success=True, data=data, message=message, request_id=request_id, execution_time_ms=execution_time_ms)
    @staticmethod
    def error(*, error, message, request_id=None):
        return Obj(error=error, message=message, request_id=request_id)




@pytest.mark.asyncio
async def test_create_geofence_ok(client, monkeypatch):
    async def fake_create_geofence(**kwargs): return Obj(id="g1", created_by=kwargs["created_by"])
    monkeypatch.setattr(mod.geofence_service, "create_geofence", fake_create_geofence)
    resp = await client.post("/geofences", json={
        "name":"Home","description":"d","geometry":{"type":"Polygon","coordinates":[]},
        "geofence_type":"polygon","is_active":True,"metadata":{}
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == "g1"


@pytest.mark.asyncio
async def test_get_geofences_sets_created_by_for_non_admin(client, monkeypatch):
    captured = {}
    async def fake_get_geofences(is_active, created_by, limit, offset):
        captured["created_by"] = created_by
        return []
    monkeypatch.setattr(mod.geofence_service, "get_geofences", fake_get_geofences)
    resp = await client.get("/geofences")
    assert resp.status_code == 200
    assert captured["created_by"] == "test-user"  # filled from current_user.user_id

@pytest.mark.asyncio
async def test_update_geofence_404_when_none(client, monkeypatch):
    async def fake_update_geofence(**kwargs): return None
    monkeypatch.setattr(mod.geofence_service, "update_geofence", fake_update_geofence)
    resp = await client.put("/geofences/gx", json={
        "name":"n","description":"d","geometry":{"type":"Polygon","coordinates":[]},
        "is_active":True,"metadata":{}
    })
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_delete_geofence_404_when_false(client, monkeypatch):
    async def fake_delete_geofence(geofence_id): return False
    monkeypatch.setattr(mod.geofence_service, "delete_geofence", fake_delete_geofence)
    resp = await client.delete("/geofences/gx")
    assert resp.status_code == 404
