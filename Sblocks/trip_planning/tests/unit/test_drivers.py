import pytest
from fastapi import HTTPException
import api.routes.drivers as m


class RB:
    @staticmethod
    def success(data=None, message=""): return {"success": True, "message": message, "data": data}
m.ResponseBuilder = RB  

class _AssignReq: 
    def __init__(self, driver_id="d1"): self.driver_id = driver_id

class _Assignment:
    def __init__(self, id="a1"): self.id = id
    def dict(self): return {"id": self.id}

class _Trip: pass 


@pytest.mark.asyncio
async def test_get_all_drivers_ok(monkeypatch):
    async def _get_all_drivers(**kwargs):
        return {"drivers": [{"id":"d1"}], "total": 1}
    monkeypatch.setattr(m.driver_service, "get_all_drivers", _get_all_drivers)

    res = await m.get_all_drivers(current_user="u1")
    assert res["success"] is True
    assert res["data"]["drivers"][0]["id"] == "d1"


@pytest.mark.asyncio
async def test_assign_driver_ok(monkeypatch):
    async def _assign(trip_id, request, current_user):
        return _Assignment("a123")
    monkeypatch.setattr(m.driver_service, "assign_driver_to_trip", _assign)

    res = await m.assign_driver_to_trip("t1", _AssignReq("d9"), current_user="u1", trip=_Trip())
    assert res["data"]["assignment"]["id"] == "a123"


@pytest.mark.asyncio
async def test_assign_driver_value_error(monkeypatch):
    async def _assign(*_): raise ValueError("nope")
    monkeypatch.setattr(m.driver_service, "assign_driver_to_trip", _assign)
    with pytest.raises(HTTPException) as e:
        await m.assign_driver_to_trip("t1", _AssignReq(), current_user="u1", trip=_Trip())
    assert e.value.status_code == 400


@pytest.mark.asyncio
async def test_unassign_driver_ok(monkeypatch):
    async def _unassign(*_): return True
    monkeypatch.setattr(m.driver_service, "unassign_driver_from_trip", _unassign)
    res = await m.unassign_driver_from_trip("t1", current_user="u1", trip=_Trip())
    assert res["success"] is True


@pytest.mark.asyncio
async def test_unassign_driver_not_found(monkeypatch):
    async def _unassign(*_): return False
    monkeypatch.setattr(m.driver_service, "unassign_driver_from_trip", _unassign)
    with pytest.raises(HTTPException) as e:
        await m.unassign_driver_from_trip("t1", current_user="u1", trip=_Trip())
    assert e.value.status_code == 500


class _AvailReq:  # schemas.requests.DriverAvailabilityRequest stub
    def __init__(self, driver_ids, start_time, end_time):
        self.driver_ids = driver_ids; self.start_time = start_time; self.end_time = end_time

@pytest.mark.asyncio
async def test_check_driver_availability_ok(monkeypatch):
    async def _get_avail(req): return [{"driver_id": "d1", "slots": []}]
    monkeypatch.setattr(m.driver_service, "get_driver_availability", _get_avail)

    from datetime import datetime, timedelta
    now = datetime.utcnow()
    res = await m.check_driver_availability(
        start_time=now, end_time=now + timedelta(hours=1), driver_ids=["d1"], current_user="u1"
    )
    assert res["data"]["availability"][0]["driver_id"] == "d1"


@pytest.mark.asyncio
async def test_check_driver_availability_bad_time():
    from datetime import datetime
    now = datetime.utcnow()
    with pytest.raises(HTTPException) as e:
        await m.check_driver_availability(start_time=now, end_time=now, current_user="u1")
    assert e.value.status_code == 500


class _Assign:
    def __init__(self, id="a"): self._id = id
    def dict(self): return {"id": self._id}

@pytest.mark.asyncio
async def test_get_driver_assignments_ok(monkeypatch):
    async def _get(driver_id, active_only=True): return [_Assign("x")]
    monkeypatch.setattr(m.driver_service, "get_driver_assignments", _get)
    res = await m.get_driver_assignments("d1", current_user="u1")
    assert res["data"]["assignments"][0]["id"] == "x"


@pytest.mark.asyncio
async def test_get_all_assignments_ok(monkeypatch):
    async def _get(driver_id=None, trip_id=None, active_only=True): return [_Assign("y")]
    monkeypatch.setattr(m.driver_service, "get_driver_assignments", _get)
    res = await m.get_all_assignments(current_user="u1")
    assert res["data"]["assignments"][0]["id"] == "y"
