import pytest
from starlette.requests import Request
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

from api import exception_handlers as eh


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload
    def model_dump(self):
        return self._payload

class _RB:
    @staticmethod
    def error(*, error, message, request_id=None):
        return _FakeResp({"error": error, "message": message, "request_id": request_id})
    @staticmethod
    def validation_error(*, message, validation_errors, request_id=None):
        return _FakeResp({"error": "validation_error", "message": message, "details": validation_errors})

def _req():
    return Request({"type": "http", "headers": [(b"x-request-id", b"rid-1")]})



@pytest.mark.asyncio
async def test_database_connection_error_handler_503():
    resp = await eh.database_connection_error_handler(_req(), eh.DatabaseConnectionError("db down"))
    assert resp.status_code == 503
    assert resp.body  # contains our fake payload

@pytest.mark.asyncio
async def test_event_publish_error_handler_202():
    resp = await eh.event_publish_error_handler(_req(), eh.EventPublishError("mq lag"))
    assert resp.status_code == 202

@pytest.mark.asyncio
async def test_business_logic_error_handler_400():
    resp = await eh.business_logic_error_handler(_req(), eh.BusinessLogicError("oops"))
    assert resp.status_code == 400

@pytest.mark.asyncio
async def test_validation_error_handler_422():
    exc = RequestValidationError([{"loc": ("query", "x"), "msg": "field required", "type": "value_error.missing"}])
    resp = await eh.validation_error_handler(_req(), exc)
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_http_exception_handler_echoes_status():
    exc = HTTPException(status_code=404, detail="not found")
    resp = await eh.http_exception_handler(_req(), exc)
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_general_exception_handler_500():
    resp = await eh.general_exception_handler(_req(), RuntimeError("boom"))
    assert resp.status_code == 500
