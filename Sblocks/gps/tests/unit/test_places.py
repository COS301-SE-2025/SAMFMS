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

@pytest.mark.asyncio
async def test_create_place_ok(monkeypatch):
    # Patch the actual import site used by the service
    import events.publisher as pub_mod
    from unittest.mock import AsyncMock
    from bson import ObjectId
    from services.places_service import places_service

    # Patch publisher at the real import site
    publish_mock = AsyncMock()
    monkeypatch.setattr(pub_mod.event_publisher, "publish_place_created", publish_mock)

    # Minimal fake DB manager + collection used by create_place()
    class _InsertRes:
        def __init__(self, _id): self.inserted_id = _id

    class _PlacesCol:
        async def insert_one(self, doc):
            # sanity: service writes GeoJSON Point with [lng, lat]
            assert doc["location"]["type"] == "Point"
            assert doc["location"]["coordinates"] == [18.4, -33.9]
            return _InsertRes(ObjectId())

    class _FakeDBMgr:
        def __init__(self):
            self.db = type("X", (), {})()
            self.db.places = _PlacesCol()
        def is_connected(self):
            return True

    # Inject fake DB manager so no real I/O happens
    monkeypatch.setattr(places_service, "db", _FakeDBMgr(), raising=False)

    # Act
    place = await places_service.create_place(
        user_id="u1",
        name="Cafe",
        description=None,
        latitude=-33.9,
        longitude=18.4,
        address="A",
        place_type="custom",
    )

    # Assert on the dumped dict to avoid 'LocationPoint' indexing issues
    data = place.model_dump()
    assert data["name"] == "Cafe"
    assert data["location"]["coordinates"] == [18.4, -33.9]
    publish_mock.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_place_404_when_missing(client, monkeypatch):
    monkeypatch.setattr(mod.places_service, "get_place", lambda pid: None)
    resp = await client.get("/places/does-not-exist")
    assert resp.status_code == 400

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
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_delete_place_404_when_false(client, monkeypatch):
    async def fake_delete_place(place_id, user_id): return False
    monkeypatch.setattr(mod.places_service, "delete_place", fake_delete_place)
    resp = await client.delete("/places/xx")
    assert resp.status_code == 404
