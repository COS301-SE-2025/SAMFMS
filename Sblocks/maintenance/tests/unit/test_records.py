
import pytest
from starlette.requests import Request

from api.routes import maintenance_records as routes
import api.dependencies as deps


# ---------- Helpers ----------

def _make_request(headers=None) -> Request:
    headers = headers or {}
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(k.lower().encode(), str(v).encode()) for k, v in headers.items()],
    }
    return Request(scope)


class _RBObj:
    """Dummy ResponseBuilder return object that supports .model_dump()."""
    def __init__(self, **payload):
        self.payload = payload

    def model_dump(self):
        return self.payload


@pytest.fixture
def rb_success(mocker):
    def _success(**kwargs):
        return _RBObj(**kwargs)
    return mocker.patch("api.routes.maintenance_records.ResponseBuilder.success", side_effect=_success)


@pytest.fixture
def rb_error(mocker):
    def _error(**kwargs):
        return _RBObj(**kwargs)
    return mocker.patch("api.routes.maintenance_records.ResponseBuilder.error", side_effect=_error)


# ---------- POST /records ----------

@pytest.mark.asyncio
async def test_create_maintenance_record_success_sets_audit_fields(mocker, rb_success):
    captured = {}

    async def _create(data):
        captured["data"] = data
        return {"_id": "R1", **data}

    mocker.patch.object(routes.maintenance_records_service, "create_maintenance_record", side_effect=_create)

    class _Req:
        def dict(self):
            return {"vehicle_id": "a" * 24, "status": "open"}

    req = _make_request({"X-Request-ID": "rid-1"})
    res = await routes.create_maintenance_record(
        request=req, maintenance_request=_Req(), user={"user_id": "u1"}, timer=deps.RequestTimer()
    )
    assert res["data"]["_id"] == "R1"
    assert captured["data"]["created_by"] == "u1"
    assert captured["data"]["updated_by"] == "u1"
    assert res["request_id"] == "rid-1"


@pytest.mark.asyncio
async def test_create_maintenance_record_value_error_returns_400(mocker, rb_error):
    mocker.patch.object(routes.maintenance_records_service, "create_maintenance_record", side_effect=ValueError("bad"))

    class _Req:
        def dict(self): return {}

    req = _make_request()
    res = await routes.create_maintenance_record(
        request=req, maintenance_request=_Req(), user={"user_id": "u1"}, timer=deps.RequestTimer()
    )
    assert res["status_code"] == 400


@pytest.mark.asyncio
async def test_create_maintenance_record_exception_returns_500(mocker, rb_error):
    mocker.patch.object(routes.maintenance_records_service, "create_maintenance_record", side_effect=Exception("boom"))

    class _Req:
        def dict(self): return {}

    req = _make_request()
    res = await routes.create_maintenance_record(
        request=req, maintenance_request=_Req(), user={"user_id": "u1"}, timer=deps.RequestTimer()
    )
    assert res["status_code"] == 500


# ---------- GET /records ----------

@pytest.mark.asyncio
async def test_get_maintenance_records_success_returns_model_dump(mocker, rb_success):
    mocker.patch.object(
        routes.maintenance_records_service,
        "search_maintenance_records",
        return_value=[{"_id": "R1"}],
        autospec=True,
    )

    req = _make_request({"X-Request-ID": "list-1"})
    res = await routes.get_maintenance_records(
        request=req,
        vehicle_id=None,
        status=None,
        maintenance_type=None,
        priority=None,
        scheduled_from=None,
        scheduled_to=None,
        vendor_id=None,
        technician_id=None,
        pagination=deps.PaginationParams(page=1, page_size=10),
        current_user={"user_id": "u", "permissions": ["maintenance:read"]},
    )
    assert res["data"] == [{"_id": "R1"}]
    assert res["message"] == "Maintenance records retrieved successfully"
    assert "execution_time_ms" in res


@pytest.mark.asyncio
async def test_get_maintenance_records_invalid_vehicle_id_returns_validation_error(mocker, rb_error):
    # No need to patch service; validator will throw before call.
    req = _make_request()
    res = await routes.get_maintenance_records(
        request=req,
        vehicle_id="too_short",  # triggers validate_object_id ValueError
        status=None,
        maintenance_type=None,
        priority=None,
        scheduled_from=None,
        scheduled_to=None,
        vendor_id=None,
        technician_id=None,
        pagination=deps.PaginationParams(page=1, page_size=10),
        current_user={"user_id": "u", "permissions": ["maintenance:read"]},
    )
    assert res["error"] == "ValidationError"


# ---------- GET /records/{record_id} ----------

@pytest.mark.asyncio
async def test_get_maintenance_record_success(mocker, rb_success):
    mocker.patch.object(
        routes.maintenance_records_service, "get_maintenance_record_by_id", return_value={"_id": "R1"}
    )
    req = _make_request({"X-Request-ID": "rid-2"})
    res = await routes.get_maintenance_record(
        request=req, record_id="a" * 24, current_user={"user_id": "u", "permissions": ["maintenance:read"]}
    )
    assert res["data"]["record"] == {"_id": "R1"}


@pytest.mark.asyncio
async def test_get_maintenance_record_not_found_returns_error(mocker, rb_error):
    mocker.patch.object(routes.maintenance_records_service, "get_maintenance_record_by_id", return_value=None)
    req = _make_request()
    res = await routes.get_maintenance_record(
        request=req, record_id="b" * 24, current_user={"user_id": "u", "permissions": ["maintenance:read"]}
    )
    assert res["error"] == "MaintenanceRecordNotFound"


@pytest.mark.asyncio
async def test_get_maintenance_record_invalid_id_returns_validation_error(mocker, rb_error):
    req = _make_request()
    res = await routes.get_maintenance_record(
        request=req, record_id="invalid", current_user={"user_id": "u", "permissions": ["maintenance:read"]}
    )
    assert res["error"] == "ValidationError"


# ---------- PUT /records/{record_id} ----------

@pytest.mark.asyncio
async def test_update_maintenance_record_no_data_returns_validation_error(mocker, rb_error):
    class _Req:
        def dict(self, exclude_unset=False):
            return {}

    req = _make_request()
    res = await routes.update_maintenance_record(
        request=req,
        updates=_Req(),
        record_id="a" * 24,
        current_user={"user_id": "u", "permissions": ["maintenance:update"]},
    )
    assert res["error"] == "ValidationError"
    assert res["message"] == "No update data provided"


@pytest.mark.asyncio
async def test_update_maintenance_record_success(mocker, rb_success):
    async def _update(record_id, data, updated_by):
        return {"_id": record_id, **data, "updated_by": updated_by}

    mocker.patch.object(routes.maintenance_records_service, "update_maintenance_record", side_effect=_update)

    class _Req:
        def dict(self, exclude_unset=False):
            return {"status": "closed"}

    req = _make_request()
    res = await routes.update_maintenance_record(
        request=req,
        updates=_Req(),
        record_id="b" * 24,
        current_user={"user_id": "u2", "permissions": ["maintenance:update"]},
    )
    assert res["data"]["record"]["updated_by"] == "u2"
    assert res["data"]["record"]["status"] == "closed"


@pytest.mark.asyncio
async def test_update_maintenance_record_not_found_returns_error(mocker, rb_error):
    mocker.patch.object(routes.maintenance_records_service, "update_maintenance_record", return_value=None)

    class _Req:
        def dict(self, exclude_unset=False):
            return {"status": "closed"}

    req = _make_request()
    res = await routes.update_maintenance_record(
        request=req,
        updates=_Req(),
        record_id="c" * 24,
        current_user={"user_id": "u", "permissions": ["maintenance:update"]},
    )
    assert res["error"] == "MaintenanceRecordNotFound"


# ---------- DELETE /records/{record_id} ----------

@pytest.mark.asyncio
async def test_delete_maintenance_record_success(mocker, rb_success):
    mocker.patch.object(routes.maintenance_records_service, "delete_maintenance_record", return_value=True)
    req = _make_request()
    res = await routes.delete_maintenance_record(
        request=req, record_id="a" * 24, current_user={"user_id": "u", "permissions": ["maintenance:delete"]}
    )
    assert res["data"]["record_id"] == "a" * 24
    assert "deleted successfully" in res["message"]


@pytest.mark.asyncio
async def test_delete_maintenance_record_not_found(mocker, rb_error):
    mocker.patch.object(routes.maintenance_records_service, "delete_maintenance_record", return_value=False)
    req = _make_request()
    res = await routes.delete_maintenance_record(
        request=req, record_id="b" * 24, current_user={"user_id": "u", "permissions": ["maintenance:delete"]}
    )
    assert res["error"] == "MaintenanceRecordNotFound"


# ---------- GET /records/vehicle/{vehicle_id} ----------

@pytest.mark.asyncio
async def test_get_vehicle_maintenance_records_success(mocker, rb_success):
    mocker.patch.object(routes.maintenance_records_service, "search_maintenance_records", return_value=[{"_id": "R1"}])
    req = _make_request()
    res = await routes.get_vehicle_maintenance_records(
        request=req,
        vehicle_id="a" * 24,
        status="open",
        pagination=deps.PaginationParams(page=1, page_size=10),
        current_user={"user_id": "u", "permissions": ["maintenance:read"]},
    )
    assert res["message"] == "Vehicle maintenance records retrieved successfully"
    assert res["data"] == [{"_id": "R1"}]


@pytest.mark.asyncio
async def test_get_vehicle_maintenance_records_invalid_vehicle_id(mocker, rb_error):
    req = _make_request()
    res = await routes.get_vehicle_maintenance_records(
        request=req,
        vehicle_id="short",
        status=None,
        pagination=deps.PaginationParams(page=1, page_size=10),
        current_user={"user_id": "u", "permissions": ["maintenance:read"]},
    )
    assert res["error"] == "ValidationError"


# ---------- GET /records/search ----------

@pytest.mark.asyncio
async def test_search_maintenance_records_success(mocker, rb_success):
    mocker.patch.object(
        routes.maintenance_records_service, "search_maintenance_records_text", return_value=[{"_id": "R1"}]
    )
    req = _make_request()
    res = await routes.search_maintenance_records(
        request=req, q="filter", pagination=deps.PaginationParams(page=1, page_size=5),
        current_user={"user_id": "u", "permissions": ["maintenance:read"]},
    )
    assert res["message"] == "Maintenance records search completed successfully"
    assert res["data"] == [{"_id": "R1"}]


@pytest.mark.asyncio
async def test_search_maintenance_records_error(mocker, rb_error):
    mocker.patch.object(
        routes.maintenance_records_service, "search_maintenance_records_text", side_effect=Exception("boom")
    )
    req = _make_request()
    res = await routes.search_maintenance_records(
        request=req, q="filter", pagination=deps.PaginationParams(page=1, page_size=5),
        current_user={"user_id": "u", "permissions": ["maintenance:read"]},
    )
    assert res["error"] == "MaintenanceRecordSearchError"
