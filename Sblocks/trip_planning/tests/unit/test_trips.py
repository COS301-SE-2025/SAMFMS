import pytest
from fastapi import HTTPException
import api.routes.trips as m


class RB:
    @staticmethod
    def success(data=None, message=""): return {"success": True, "message": message, "data": data}
    @staticmethod
    def paginated(items, total, skip, limit, message=""):
        return {"success": True, "message": message, "items": items, "total": total, "skip": skip, "limit": limit}
m.ResponseBuilder = RB  


class _ReqCreate: pass
class _ReqUpdate: pass
class _ReqFilter: pass
class _ReqOptimize:
    def __init__(self): self.optimization_type="fastest"; self.avoid_traffic=True; self.real_time=False
class _ReqProgress:
    class _Loc:
        def dict(self): return {"lat":1.0,"lng":2.0}
    def __init__(self):
        self.current_location = self._Loc()
        self.status = "in_progress"
        self.estimated_arrival = None

class _Way:
    def dict(self): return {"x": 1}

class _DriverAssign:
    def __init__(self, driver_id): self.driver_id = driver_id
    def dict(self): return {"driver_id": self.driver_id}

class _Trip:
    def __init__(self, id="t1", created_by="u", driver_id=None):
        self.id=id; self.created_by=created_by
        self.origin=type("O",(),{"dict":lambda s: {"o":1}})()
        self.destination=type("D",(),{"dict":lambda s: {"d":1}})()
        self.waypoints=[_Way()]
        self.estimated_duration=120
        self.estimated_distance=100.0
        self.status="planned"
        self.scheduled_start_time=None
        self.actual_start_time=None
        self.actual_end_time=None
        self.driver_assignment=_DriverAssign(driver_id) if driver_id else None
        self.vehicle_id="veh1"
    def dict(self): return {"id": self.id}

# ----- Tests -----
@pytest.mark.asyncio
async def test_create_trip_ok(monkeypatch):
    async def _create(req, user): return _Trip("t9")
    monkeypatch.setattr(m.trip_service, "create_trip", _create)
    res = await m.create_trip(_ReqCreate(), current_user="u1")
    assert res["data"]["trip"]["id"] == "t9"

@pytest.mark.asyncio
async def test_create_trip_value_error(monkeypatch):
    async def _create(*_): raise ValueError("bad")
    monkeypatch.setattr(m.trip_service, "create_trip", _create)
    with pytest.raises(HTTPException) as e:
        await m.create_trip(_ReqCreate(), current_user="u1")
    assert e.value.status_code == 400

@pytest.mark.asyncio
async def test_create_trip_internal_error(monkeypatch):
    async def _create(*_): raise RuntimeError("boom")
    monkeypatch.setattr(m.trip_service, "create_trip", _create)
    with pytest.raises(HTTPException) as e:
        await m.create_trip(_ReqCreate(), current_user="u1")
    assert e.value.status_code == 500

class _TripObj:
    def __init__(self, i): self._i=i
    def dict(self): return {"id": self._i}

@pytest.mark.asyncio
async def test_list_trips_ok(monkeypatch):
    async def _list(filter_req): return ([_TripObj("t1"), _TripObj("t2")], 2)
    monkeypatch.setattr(m.trip_service, "list_trips", _list)
    res = await m.list_trips(
        status=None,
        priority=None,
        driver_id=None,
        vehicle_id=None,
        start_date=None,
        end_date=None,
        skip=0,
        limit=50,
        sort_by="scheduled_start_time",
        sort_order="asc",
        current_user="u1",
    )
    assert res["total"] == 2 and len(res["items"]) == 2

@pytest.mark.asyncio
async def test_get_trip_ok():
    res = await m.get_trip("t1", current_user="u1", trip=_Trip("t1"))
    assert res["data"]["trip"]["id"] == "t1"

@pytest.mark.asyncio
async def test_update_trip_ok(monkeypatch):
    async def _update(tid, req, user): return _Trip("t2")
    monkeypatch.setattr(m.trip_service, "update_trip", _update)
    res = await m.update_trip("t1", _ReqUpdate(), current_user="u1", trip=_Trip("t1"))
    assert res["data"]["trip"]["id"] == "t2"

@pytest.mark.asyncio
async def test_update_trip_not_found(monkeypatch):
    async def _update(*_): return None
    monkeypatch.setattr(m.trip_service, "update_trip", _update)
    with pytest.raises(HTTPException) as e:
        await m.update_trip("t1", _ReqUpdate(), current_user="u1", trip=_Trip("t1"))
    assert e.value.status_code == 500

@pytest.mark.asyncio
async def test_delete_trip_ok(monkeypatch):
    async def _delete(*_): return True
    monkeypatch.setattr(m.trip_service, "delete_trip", _delete)
    res = await m.delete_trip("t1", current_user="u1", trip=_Trip("t1"))
    assert res["success"] is True

@pytest.mark.asyncio
async def test_delete_trip_not_found(monkeypatch):
    async def _delete(*_): return False
    monkeypatch.setattr(m.trip_service, "delete_trip", _delete)
    with pytest.raises(HTTPException) as e:
        await m.delete_trip("t1", current_user="u1", trip=_Trip("t1"))
    assert e.value.status_code == 500

@pytest.mark.asyncio
async def test_start_trip_ok(monkeypatch):
    async def _start(*_): return _Trip("tS")
    monkeypatch.setattr(m.trip_service, "start_trip", _start)
    res = await m.start_trip("t1", current_user="u1", trip=_Trip("t1"))
    assert res["data"]["trip"]["id"] == "tS"

@pytest.mark.asyncio
async def test_start_trip_not_found(monkeypatch):
    async def _start(*_): return None
    monkeypatch.setattr(m.trip_service, "start_trip", _start)
    with pytest.raises(HTTPException) as e:
        await m.start_trip("t1", current_user="u1", trip=_Trip("t1"))
    assert e.value.status_code == 500

@pytest.mark.asyncio
async def test_complete_trip_ok(monkeypatch):
    async def _complete(*_): return _Trip("tC")
    monkeypatch.setattr(m.trip_service, "complete_trip", _complete)
    res = await m.complete_trip("t1", current_user="u1", trip=_Trip("t1"))
    assert res["data"]["trip"]["id"] == "tC"

@pytest.mark.asyncio
async def test_complete_trip_not_found(monkeypatch):
    async def _complete(*_): return None
    monkeypatch.setattr(m.trip_service, "complete_trip", _complete)
    with pytest.raises(HTTPException):
        await m.complete_trip("t1", current_user="u1", trip=_Trip("t1"))

@pytest.mark.asyncio
async def test_optimize_route_ok(monkeypatch):
    async def _get_constraints(tid): return [{"k":"v"}]
    async def _apply(tid, route): return {"applied": True, "input": route}
    monkeypatch.setattr(m.constraint_service, "get_active_constraints_for_trip", _get_constraints)
    monkeypatch.setattr(m.constraint_service, "apply_constraints_to_route", _apply)
    res = await m.optimize_trip_route("t1", _ReqOptimize(), current_user="u1", trip=_Trip("t1"))
    assert res["data"]["trip_id"] == "t1"
    assert "optimized_route" in res["data"]

@pytest.mark.asyncio
async def test_update_trip_progress_ok():
    res = await m.update_trip_progress("t1", _ReqProgress(), current_user="u1", trip=_Trip("t1"))
    assert res["data"]["trip_id"] == "t1"
    assert res["data"]["status"] == "in_progress"

@pytest.mark.asyncio
async def test_get_trip_status_ok():
    trip = _Trip("t1", driver_id="d1")
    res = await m.get_trip_status("t1", current_user="u1", trip=trip)
    assert res["data"]["trip_id"] == "t1"
    assert res["data"]["driver_assignment"]["driver_id"] == "d1"

@pytest.mark.asyncio
async def test_get_upcoming_trips_ok(monkeypatch):
    async def _get(driver_id, limit): return [_Trip("A"), _Trip("B")]
    monkeypatch.setattr(m.trip_service, "get_upcoming_trips", _get)
    res = await m.get_upcoming_trips("d1", current_user="u1")
    assert res["data"]["count"] == 2

@pytest.mark.asyncio
async def test_get_recent_trips_ok(monkeypatch):
    async def _get(driver_id, limit, days): return [_Trip("R")]
    monkeypatch.setattr(m.trip_service, "get_recent_trips", _get)
    res = await m.get_recent_trips("d1", current_user="u1")
    assert res["data"]["count"] == 1

@pytest.mark.asyncio
async def test_get_all_recent_trips_ok(monkeypatch):
    async def _get(limit, days): return [_Trip("R1"), _Trip("R2")]
    monkeypatch.setattr(m.trip_service, "get_all_recent_trips", _get)
    res = await m.get_all_recent_trips(current_user="u1")
    assert res["data"]["count"] == 2
