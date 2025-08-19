import asyncio
import uuid
import pytest
from starlette.requests import Request
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from api import dependencies as deps


def make_request(headers=None):
    scope = {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
    }
    return Request(scope)

@pytest.mark.asyncio
async def test_get_request_id_uses_header():
    req = make_request({"X-Request-ID": "abc-123"})
    rid = await deps.get_request_id(req)
    assert rid == "abc-123"  # explicit header wins

@pytest.mark.asyncio
async def test_get_request_id_generates_uuid():
    rid = await deps.get_request_id(make_request())
    # just validate it's a UUID string
    uuid.UUID(rid)

def test_request_timer_measures_time():
    with deps.RequestTimer() as t:
        pass
    assert t.execution_time_ms is not None
    assert t.execution_time_ms >= 0

@pytest.mark.asyncio
async def test_get_current_user_returns_mock_user():
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token123")
    user = await deps.get_current_user(creds)
    assert user["user_id"]
    assert "gps:read" in user["permissions"]

@pytest.mark.asyncio
async def test_require_permission_allows_when_present():
    checker = deps.require_permission("gps:read")
    user = {"permissions": ["gps:read"], "is_admin": False}
    result = await checker(current_user=user)  # inject directly
    assert result is user

@pytest.mark.asyncio
async def test_require_permission_denies_when_absent():
    checker = deps.require_permission("gps:write")
    user = {"permissions": ["gps:read"], "is_admin": False}
    with pytest.raises(HTTPException) as ei:
        await checker(current_user=user)
    assert ei.value.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_get_optional_user_none_without_auth_header():
    user = await deps.get_optional_user(make_request())
    assert user is None

@pytest.mark.asyncio
async def test_get_optional_user_returns_user_with_header():
    req = make_request({"Authorization": "Bearer whatever"})
    user = await deps.get_optional_user(req)
    assert isinstance(user, dict)
    assert "user_id" in user
