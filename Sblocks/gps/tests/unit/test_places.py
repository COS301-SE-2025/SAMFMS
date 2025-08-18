import pytest
from api.routes import places as mod

class Obj:
    def __init__(self, **d): self.__dict__.update(d)
    def model_dump(self): return dict(self.__dict__)

class RB:
    @staticmethod
    def success(*, data, message, request_id=None, execution_time_ms=None):
        return Obj(success=True, data=data, message=message, request_id=request_id, execution_time_ms=execution_time_ms)
    @staticmethod
    def error(*, error, message, request_id=None):  # only used via handlers
        return Obj(error=error, message=message, request_id=request_id)


@pytest.fixture(autouse=True)
def patch_response_builder(monkeypatch):
    monkeypatch.setattr(mod, "ResponseBuilder", RB)
    yield


@pytest.mark.asyncio
async def test_create_place_ok(client, monkeypatch):
    async def fake_create_place(**kwargs):
        return Obj(id="p1", user_id=kwargs["user_id"])
    monkeypatch.setattr(mod.places_service, "create_place", fake_create_place)
    resp = await client.post("/places", json={
        "name":"Park","description":"Nice","latitude":1.0,"longitude":2.0,"address":"A","place_type":"park","metadata":{}
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["id"] == "p1"

@pytest.mark.asyncio
async def test_get_place_404_when_missing(client, monkeypatch):
    monkeypatch.setattr(mod.places_service, "get_place", lambda pid: None)
    resp = await client.get("/places/does-not-exist")
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_get_place_forbidden_when_other_users_place(client, monkeypatch):
    async def fake_get_place(pid): return Obj(id=pid, user_id="someone-else")
    monkeypatch.setattr(mod.places_service, "get_place", fake_get_place)
    resp = await client.get("/places/abc")
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_get_user_places_filters_by_current_user(client, monkeypatch):
    captured = {}
    async def fake_get_user_places(user_id, place_type, limit, offset):
        captured["user_id"] = user_id
        return [Obj(id="p1", user_id=user_id)]
    monkeypatch.setattr(mod.places_service, "get_user_places", fake_get_user_places)
    resp = await client.get("/places")
    assert resp.status_code == 200
    assert captured["user_id"] == "test-user"  # from conftest fake_user

@pytest.mark.asyncio
async def test_search_places_ok(client, monkeypatch):
    async def fake_search_places(user_id, search_term, limit): return [Obj(id="p2", user_id=user_id)]
    monkeypatch.setattr(mod.places_service, "search_places", fake_search_places)
    resp = await client.post("/places/search", json={"search_term":"pa","limit":10})
    assert resp.status_code == 200
    assert resp.json()["data"][0]["id"] == "p2"

@pytest.mark.asyncio
async def test_nearby_places_ok(client, monkeypatch):
    async def fake_nearby(**kwargs): return [Obj(id="near1", user_id=kwargs["user_id"])]
    monkeypatch.setattr(mod.places_service, "get_places_near_location", fake_nearby)
    resp = await client.post("/places/nearby", json={"latitude":1.0,"longitude":2.0,"radius_meters":1000,"limit":5})
    assert resp.status_code == 200
    assert resp.json()["data"][0]["id"] == "near1"

@pytest.mark.asyncio
async def test_update_place_404_when_service_returns_none(client, monkeypatch):
    async def fake_update_place(**kwargs): return None
    monkeypatch.setattr(mod.places_service, "update_place", fake_update_place)
    resp = await client.put("/places/xx", json={
        "name":"n","description":"d","latitude":0,"longitude":0,"address":"a","place_type":"p","metadata":{}
    })
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_delete_place_404_when_false(client, monkeypatch):
    async def fake_delete_place(place_id, user_id): return False
    monkeypatch.setattr(mod.places_service, "delete_place", fake_delete_place)
    resp = await client.delete("/places/xx")
    assert resp.status_code == 404
