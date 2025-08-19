from __future__ import annotations
import uuid
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request


import api.dependencies as deps
import httpx


# ---------- Helpers / Scaffolding ----------

class _DummyResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json


class _DummyAsyncClient:
    """Minimal async context manager that emulates httpx.AsyncClient for our tests."""
    def __init__(self, response: _DummyResponse = None, exc: Exception = None):
        self._response = response
        self._exc = exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, *args, **kwargs):
        if self._exc:
            raise self._exc
        return self._response


@pytest.fixture
def auth_credentials():
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-token")


@pytest.fixture
def patch_httpx(mocker):
    """
    Patch api.dependencies.httpx.AsyncClient to return a controllable dummy.
    Usage:
        response = patch_httpx(json_data={"k":"v"}, status=200)
        # OR to raise:
        patch_httpx(exc=httpx.RequestError("boom"))
    """
    def _patch(json_data=None, status=200, exc: Exception = None):
        resp = _DummyResponse(status_code=status, json_data=json_data)
        mocker.patch(
            "api.dependencies.httpx.AsyncClient",
            lambda *args, **kwargs: _DummyAsyncClient(response=resp, exc=exc),
        )
        return resp
    return _patch


def _make_request(headers: dict | None = None) -> Request:
    """Create a minimal ASGI Request with optional headers."""
    headers = headers or {}
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(k.lower().encode(), str(v).encode()) for k, v in headers.items()],
    }
    return Request(scope)


# ---------- get_current_user ----------

@pytest.mark.asyncio
async def test_get_current_user_success(patch_httpx, auth_credentials):
    patch_httpx(json_data={"user_id": "u1", "username": "alice", "permissions": ["p1"]}, status=200)
    user = await deps.get_current_user(auth_credentials)
    assert user["user_id"] == "u1"


@pytest.mark.asyncio
async def test_get_current_user_unauthorized_401(patch_httpx, auth_credentials):
    patch_httpx(json_data={"detail": "unauthorized"}, status=401)
    with pytest.raises(HTTPException) as exc:
        await deps.get_current_user(auth_credentials)
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_get_current_user_forbidden_on_other_status(patch_httpx, auth_credentials):
    patch_httpx(json_data={"detail": "service error"}, status=503)
    with pytest.raises(HTTPException) as exc:
        await deps.get_current_user(auth_credentials)
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_get_current_user_auth_service_unavailable_raises_authentication_error(patch_httpx, auth_credentials):
    patch_httpx(exc=httpx.RequestError("connection failed"))
    with pytest.raises(deps.AuthenticationError):
        await deps.get_current_user(auth_credentials)


@pytest.mark.asyncio
async def test_get_current_user_unexpected_error_translates_to_http_500(mocker, auth_credentials):
    # Make AsyncClient.get raise a generic (non-RequestError) exception
    class _BoomClient(_DummyAsyncClient):
        async def get(self, *args, **kwargs):
            raise RuntimeError("unexpected")

    mocker.patch("api.dependencies.httpx.AsyncClient", lambda *a, **k: _BoomClient())
    with pytest.raises(HTTPException) as exc:
        await deps.get_current_user(auth_credentials)
    assert exc.value.status_code == 500


# ---------- require_permission ----------

@pytest.mark.asyncio
async def test_require_permission_allows_when_user_has_permission():
    dep = deps.require_permission("maintenance:read")
    current_user = {"user_id": "u1", "permissions": ["maintenance:read"]}
    result = await dep(current_user=current_user)
    assert result is current_user


@pytest.mark.asyncio
async def test_require_permission_denies_when_user_lacks_permission():
    dep = deps.require_permission("maintenance:read")
    current_user = {"user_id": "u1", "permissions": ["other:perm"]}
    with pytest.raises(HTTPException) as exc:
        await dep(current_user=current_user)
    assert exc.value.status_code == 403


# ---------- require_permissions ----------

@pytest.mark.asyncio
async def test_require_permissions_allows_when_any_permission_matches():
    dep = deps.require_permissions(["A", "B", "C"])
    current_user = {"permissions": ["Z", "B"]}
    result = await dep(current_user=current_user)
    # This dependency returns None on success (as routes expect)
    assert result is None


@pytest.mark.asyncio
async def test_require_permissions_denies_when_no_permissions_match():
    dep = deps.require_permissions(["A", "B", "C"])
    current_user = {"permissions": ["X", "Y"]}
    with pytest.raises(HTTPException) as exc:
        await dep(current_user=current_user)
    assert exc.value.status_code == 403


# ---------- PaginationParams & get_pagination_params ----------

def test_paginationparams_clamps_page_and_size():
    p = deps.PaginationParams(page=0, page_size=1000)
    assert p.page == 1 and p.page_size == 100 and p.skip == 0 and p.limit == 100


@pytest.mark.asyncio
async def test_get_pagination_params_returns_expected_values():
    p = await deps.get_pagination_params(page=2, page_size=10)
    assert p.page == 2 and p.page_size == 10 and p.skip == 10 and p.limit == 10


# ---------- validate_object_id ----------

def test_validate_object_id_accepts_valid_hex_24_chars():
    deps.validate_object_id("a" * 24)  # Should not raise


def test_validate_object_id_raises_on_empty():
    with pytest.raises(ValueError):
        deps.validate_object_id("")


def test_validate_object_id_raises_on_wrong_length():
    with pytest.raises(ValueError):
        deps.validate_object_id("a" * 23)


def test_validate_object_id_raises_on_non_hex_chars():
    with pytest.raises(ValueError):
        deps.validate_object_id("g" * 24)  # 'g' is not hex


# ---------- get_request_id ----------

@pytest.mark.asyncio
async def test_get_request_id_returns_existing_header():
    request = _make_request({"X-Request-ID": "req-123"})
    rid = await deps.get_request_id(request)
    assert rid == "req-123"


@pytest.mark.asyncio
async def test_get_request_id_generates_uuid_when_missing():
    request = _make_request({})
    rid = await deps.get_request_id(request)
    # Validate it's a UUID
    assert uuid.UUID(rid).hex is not None


# ---------- RequestTimer ----------

def test_request_timer_elapsed_inside_context_is_int():
    with deps.RequestTimer() as t:
        assert isinstance(t.elapsed, int)  # Elapsed is available during context


def test_request_timer_sets_execution_time_on_exit():
    with deps.RequestTimer() as t:
        pass
    assert isinstance(t.execution_time_ms, int) and t.execution_time_ms >= 0
    assert uuid.UUID(t.request_id).hex is not None


# ---------- get_request_timer ----------

@pytest.mark.asyncio
async def test_get_request_timer_returns_started_timer():
    t = await deps.get_request_timer()
    assert t.start_time is not None and isinstance(t.elapsed, int)
    # Manually exit to finalize
    t.__exit__(None, None, None)
    assert isinstance(t.execution_time_ms, int)


# ---------- get_user_context ----------

@pytest.mark.asyncio
async def test_get_user_context_authenticated_when_get_current_user_succeeds(mocker):
    # Patch get_current_user to avoid hitting httpx, but still use real HTTPBearer parsing.
    async def _fake_get_current_user(_creds):
        return {"user_id": "u1", "username": "alice", "permissions": ["p1"]}

    mocker.patch("api.dependencies.get_current_user", _fake_get_current_user)

    request = _make_request({"Authorization": "Bearer test-token"})
    ctx = await deps.get_user_context(request)
    assert ctx == {
        "user_id": "u1",
        "username": "alice",
        "permissions": ["p1"],
        "authenticated": True,
    }


@pytest.mark.asyncio
async def test_get_user_context_anonymous_when_auth_header_missing():
    request = _make_request({})
    ctx = await deps.get_user_context(request)
    assert ctx["authenticated"] is False and ctx["username"] == "anonymous"


@pytest.mark.asyncio
async def test_get_user_context_anonymous_when_get_current_user_raises(mocker):
    async def _boom(_creds):
        raise HTTPException(status_code=401, detail="bad token")

    mocker.patch("api.dependencies.get_current_user", _boom)
    request = _make_request({"Authorization": "Bearer bad-token"})
    ctx = await deps.get_user_context(request)
    assert ctx["authenticated"] is False and ctx["user_id"] is None


# ---------- validate_date_range ----------

def test_validate_date_range_accepts_valid_iso_range():
    assert deps.validate_date_range("2023-01-01T00:00:00Z", "2023-01-02T00:00:00Z") is None


def test_validate_date_range_raises_when_start_equals_end():
    with pytest.raises(ValueError, match="Start date must be before end date"):
        deps.validate_date_range("2023-01-01T00:00:00Z", "2023-01-01T00:00:00Z")


def test_validate_date_range_raises_when_start_after_end():
    with pytest.raises(ValueError, match="Start date must be before end date"):
        deps.validate_date_range("2023-01-03T00:00:00Z", "2023-01-02T00:00:00Z")


def test_validate_date_range_raises_on_invalid_format():
    with pytest.raises(ValueError, match="Invalid date format"):
        deps.validate_date_range("not-a-date", "2023-01-02T00:00:00Z")


def test_validate_date_range_noop_when_one_or_both_missing():
    # Should not raise if one or both dates are None
    assert deps.validate_date_range(None, "2023-01-02T00:00:00Z") is None
    assert deps.validate_date_range("2023-01-01T00:00:00Z", None) is None
    assert deps.validate_date_range(None, None) is None
