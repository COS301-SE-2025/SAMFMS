import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

import api.exception_handlers as exc_mod


class _RBResp:
    def __init__(self, data): self._d = data
    def model_dump(self, **_): return self._d

class _RB:
    @staticmethod
    def validation_error(message, validation_errors):
        return _RBResp({"success": False, "message": message, "errors": validation_errors})
    @staticmethod
    def error(error, message):
        return _RBResp({"success": False, "error": error, "message": message})

exc_mod.ResponseBuilder = _RB

def _req():
    return Request({"type": "http", "method": "GET", "path": "/x", "headers": []})

@pytest.mark.asyncio
async def test_validation_exception_handler():
    err = RequestValidationError([{"loc": ("query", "a"), "msg": "bad", "type": "type_error"}])
    resp = await exc_mod.validation_exception_handler(_req(), err)
    assert resp.status_code == 422
    body = resp.body.decode()
    assert "Request validation failed" in body
    assert "query -> a" in body

@pytest.mark.asyncio
async def test_http_exception_handler():
    resp = await exc_mod.http_exception_handler(_req(), HTTPException(404, "nope"))
    assert resp.status_code == 404
    assert '"error":"HTTP_404"' in resp.body.decode()

@pytest.mark.asyncio
async def test_starlette_exception_handler():
    resp = await exc_mod.starlette_exception_handler(_req(), StarletteHTTPException(405, "bad"))
    assert resp.status_code == 405
    assert '"error":"HTTP_405"' in resp.body.decode()

@pytest.mark.asyncio
async def test_custom_trip_planning_handlers():
    resp = await exc_mod.trip_planning_exception_handler(_req(), exc_mod.TripNotFoundError("T1"))
    assert resp.status_code == 404
    resp = await exc_mod.trip_planning_exception_handler(_req(), exc_mod.DatabaseConnectionError())
    assert resp.status_code == 503
    resp = await exc_mod.trip_planning_exception_handler(_req(), exc_mod.EventPublishError())
    assert resp.status_code == 502
    resp = await exc_mod.trip_planning_exception_handler(_req(), exc_mod.BusinessLogicError("msg"))
    assert resp.status_code == 400

@pytest.mark.asyncio
async def test_general_exception_handler():
    resp = await exc_mod.general_exception_handler(_req(), Exception("boom"))
    assert resp.status_code == 500

def test_exception_handlers_mapping_keys():
    keys = set(exc_mod.EXCEPTION_HANDLERS.keys())
    assert {RequestValidationError, HTTPException, StarletteHTTPException, exc_mod.TripPlanningException, Exception}.issubset(keys)
