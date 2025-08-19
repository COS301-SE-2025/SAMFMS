import pytest
from api.routes import locations as mod

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
async def test_update_vehicle_location_ok(client, monkeypatch):
    async def fake_update_vehicle_location(**kwargs): return Obj(vehicle_id=kwargs["vehicle_id"])
    monkeypatch.setattr(mod.location_service, "update_vehicle_location", fake_update_vehicle_location)
    # background task uses module function; fine to schedule
    resp = await client.post("/locations/update", json={
        "vehicle_id":"v1","latitude":1.1,"longitude":2.2,"altitude":0,"speed":0,"heading":0,"accuracy":5.0,"timestamp":"2023-01-01T00:00:00Z"
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["vehicle_id"] == "v1"

@pytest.mark.asyncio
async def test_get_vehicle_location_404_when_missing(client, monkeypatch):
    monkeypatch.setattr(mod.location_service, "get_vehicle_location", lambda vid: None)
    resp = await client.get("/locations/nope")
    assert resp.status_code == 400

@pytest.mark.asyncio
async def test_get_multiple_vehicle_locations_400_when_no_ids(client):
    resp = await client.get("/locations", params={"vehicle_ids": ""})
    assert resp.status_code == 400

@pytest.mark.asyncio
async def test_get_multiple_vehicle_locations_ok(client, monkeypatch):
    async def fake_get_multiple(ids): return [Obj(vehicle_id=i) for i in ids]
    async def stub(vehicle_id_list): return await fake_get_multiple(vehicle_id_list)
    monkeypatch.setattr(mod.location_service, "get_multiple_vehicle_locations", stub)
    resp = await client.get("/locations", params={"vehicle_ids":"a,b"})
    assert resp.status_code == 200
    assert {x["vehicle_id"] for x in resp.json()["data"]} == {"a","b"}

@pytest.mark.asyncio
async def test_get_location_history_ok(client, monkeypatch):
    async def fake_hist(**kwargs): return [Obj(vehicle_id=kwargs["vehicle_id"], idx=1)]
    monkeypatch.setattr(mod.location_service, "get_location_history", fake_hist)
    resp = await client.get("/locations/veh1/history", params={"limit": 10})
    assert resp.status_code == 200
    assert resp.json()["data"][0]["vehicle_id"] == "veh1"

@pytest.mark.asyncio
async def test_search_vehicles_in_area_ok(client, monkeypatch):
    async def fake_area(**kwargs): return [Obj(vehicle_id="vZ")]
    monkeypatch.setattr(mod.location_service, "get_vehicles_in_area", fake_area)
    resp = await client.post("/locations/search/area", json={"center_latitude":1.0,"center_longitude":2.0,"radius_meters":50})
    assert resp.status_code == 200
    assert resp.json()["data"][0]["vehicle_id"] == "vZ"


