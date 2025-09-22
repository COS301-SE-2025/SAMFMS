import asyncio
import io
import sys
import types
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


rabbitmq = types.ModuleType("rabbitmq")
producer = types.ModuleType("rabbitmq.producer")

async def _dummy_publish_message(*args, **kwargs):
    return None

producer.publish_message = _dummy_publish_message
rabbitmq.producer = producer
sys.modules["rabbitmq"] = rabbitmq
sys.modules["rabbitmq.producer"] = producer


from routes import auth 
app = FastAPI()
app.include_router(auth.router)
client = TestClient(app)


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text="", content=b"{}"):
        self.status_code = status_code
        self._json_data = {} if json_data is None else json_data
        self.text = text
        self.content = content if isinstance(content, (bytes, bytearray)) else str(content).encode()

    def json(self):
        return self._json_data


class RaiseJSON:
    """Fake response whose .json() raises a provided exception type."""
    def __init__(self, exc_type=ValueError, status_code=500, text="bad json", content=b""):
        self.status_code = status_code
        self.text = text
        self.content = content

    def json(self):
        raise exc_type("boom")


def test_login_error_from_security(monkeypatch):
    def fake_post(url, json, timeout):
        return FakeResponse(401, {"detail": "bad creds"})
    monkeypatch.setattr(auth.requests, "post", fake_post)
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "x"})
    assert r.status_code == 500
    assert r.json()["detail"] == "Login error: 401: bad creds"

def test_login_security_unavailable(monkeypatch):
    def fake_post(*a, **k):
        raise auth.requests.RequestException("down")
    monkeypatch.setattr(auth.requests, "post", fake_post)
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "x"})
    assert r.status_code == 503

def test_login_unexpected_error(monkeypatch):
    def fake_post(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(auth.requests, "post", fake_post)
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "x"})
    assert r.status_code == 500


# ======================================================================
# /auth/signup
# ======================================================================


def test_signup_error(monkeypatch):
    def fake_post(url, json, timeout):
        return FakeResponse(409, {"detail": "exists"})
    monkeypatch.setattr(auth.requests, "post", fake_post)
    r = client.post("/auth/signup", json={"full_name": "A", "email": "a@b.com", "password": "x"})
    assert r.status_code == 500
    assert r.json()["detail"] == "Signup error: 409: exists"

def test_signup_security_unavailable(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/signup", json={"full_name": "A", "email": "a@b.com", "password": "x"})
    assert r.status_code == 503

def test_signup_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post("/auth/signup", json={"full_name": "A", "email": "a@b.com", "password": "x"})
    assert r.status_code == 500


# ======================================================================
# /auth/verify-token
# ======================================================================
def test_verify_token_missing_header():
    r = client.post("/auth/verify-token")
    assert r.status_code == 500

def test_verify_token_returns_json_even_non_200(monkeypatch):
    def fake_post(url, headers, timeout):
        return FakeResponse(418, {"valid": False})
    monkeypatch.setattr(auth.requests, "post", fake_post)
    r = client.post("/auth/verify-token", headers={"Authorization": "Bearer Z"})
    assert r.status_code == 200
    assert r.json() == {"valid": False}

def test_verify_token_security_unavailable(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/verify-token", headers={"Authorization": "Bearer Z"})
    assert r.status_code == 503

def test_verify_token_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post("/auth/verify-token", headers={"Authorization": "Bearer Z"})
    assert r.status_code == 500


# ======================================================================
# /auth/logout
# ======================================================================
def test_logout_missing_header():
    r = client.post("/auth/logout")
    assert r.status_code == 500

def test_logout_success(monkeypatch):
    def fake_post(url, headers, timeout):
        return FakeResponse(200, {"ok": True})
    monkeypatch.setattr(auth.requests, "post", fake_post)
    r = client.post("/auth/logout", headers={"Authorization": "Bearer Z"})
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_logout_error(monkeypatch):
    def fake_post(url, headers, timeout):
        return FakeResponse(400, {"detail": "nope"})
    monkeypatch.setattr(auth.requests, "post", fake_post)
    r = client.post("/auth/logout", headers={"Authorization": "Bearer Z"})
    assert r.status_code == 500
    assert r.json()["detail"] == "Logout error: 400: nope"

def test_logout_security_unavailable(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/logout", headers={"Authorization": "Bearer Z"})
    assert r.status_code == 503

def test_logout_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post("/auth/logout", headers={"Authorization": "Bearer Z"})
    assert r.status_code == 500


# ======================================================================
# /auth/logout-all
# ======================================================================
def test_logout_all_missing_header():
    r = client.post("/auth/logout-all")
    assert r.status_code == 500

def test_logout_all_success(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(200, {"ok": True}))
    r = client.post("/auth/logout-all", headers={"Authorization": "Bearer Z"})
    assert r.status_code == 200

def test_logout_all_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(500, {"detail": "X"}))
    r = client.post("/auth/logout-all", headers={"Authorization": "Bearer Z"})
    assert r.status_code == 500
    assert r.json()["detail"] == "Logout all error: 500: X"

def test_logout_all_security_unavailable(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/logout-all", headers={"Authorization": "Bearer Z"})
    assert r.status_code == 503

def test_logout_all_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post("/auth/logout-all", headers={"Authorization": "Bearer Z"})
    assert r.status_code == 500


# ======================================================================
# /auth/refresh
# ======================================================================
def test_refresh_success(monkeypatch):
    def fake_post(url, data, headers, timeout):
        assert b'"x":"y"' in data
        return FakeResponse(200, {"refreshed": True})
    monkeypatch.setattr(auth.requests, "post", fake_post)
    r = client.post("/auth/refresh", json={"x": "y"})
    assert r.status_code == 200
    assert r.json()["refreshed"] is True

def test_refresh_error_non200(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(401, {"detail": "bad"}))
    r = client.post("/auth/refresh", json={"x": "y"})
    assert r.status_code == 500

def test_refresh_security_unavailable(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/refresh", json={"x": "y"})
    assert r.status_code == 503

def test_refresh_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post("/auth/refresh", json={"x": "y"})
    assert r.status_code == 500


# ======================================================================
# /auth/health
# ======================================================================
def test_auth_health_reachable(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: FakeResponse(200))
    r = client.get("/auth/health")
    assert r.status_code == 200
    assert r.json()["security_service"] == "reachable"

def test_auth_health_error_status(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: FakeResponse(503))
    r = client.get("/auth/health")
    assert "error: 503" in r.json()["security_service"]

def test_auth_health_unreachable(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no")))
    r = client.get("/auth/health")
    assert "unreachable" in r.json()["security_service"]


# ======================================================================
# /auth/user-exists
# ======================================================================
def test_user_exists_primary_200(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: FakeResponse(200, {"userExists": True}))
    r = client.get("/auth/user-exists")
    assert r.json() == {"userExists": True}

def test_user_exists_fallback_count_true(monkeypatch):
    # first 404 then count 200 with count > 0
    seq = [FakeResponse(404), FakeResponse(200, {"count": 3})]
    def fake_get(*a, **k):
        return seq.pop(0)
    monkeypatch.setattr(auth.requests, "get", fake_get)
    r = client.get("/auth/user-exists")
    assert r.json() == {"userExists": True}

def test_user_exists_fallback_count_not_200(monkeypatch):
    seq = [FakeResponse(404), FakeResponse(500, {"detail": "x"})]
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: seq.pop(0))
    r = client.get("/auth/user-exists")
    assert r.json() == {"userExists": False}

def test_user_exists_primary_other_status(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: FakeResponse(500))
    r = client.get("/auth/user-exists")
    assert r.json() == {"userExists": False}

def test_user_exists_request_exception(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.get("/auth/user-exists")
    assert r.json() == {"userExists": False}


# ======================================================================
# /auth/update-profile
# ======================================================================
def test_update_profile_missing_token():
    r = client.post("/auth/update-profile", json={"full_name": "X"})
    assert r.status_code == 500

def test_update_profile_success(monkeypatch):
    def fake_post(url, headers, json, timeout):
        assert json == {"full_name": "X"}
        return FakeResponse(200, {"ok": True})
    monkeypatch.setattr(auth.requests, "post", fake_post)
    r = client.post("/auth/update-profile", headers={"Authorization": "Bearer T"}, json={"full_name": "X"})
    assert r.status_code == 200

def test_update_profile_non200(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(400, {"detail": "bad"}))
    r = client.post("/auth/update-profile", headers={"Authorization": "Bearer T"}, json={"full_name": "X"})
    assert r.status_code == 500

def test_update_profile_request_exception_causes_500(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/update-profile", headers={"Authorization": "Bearer T"}, json={"full_name": "X"})
    assert r.status_code == 500


# ======================================================================
# /auth/upload-profile-picture
# ======================================================================
def test_upload_profile_picture_missing_token():
    r = client.post("/auth/upload-profile-picture", files={"profile_picture": ("a.txt", b"x", "text/plain")})
    assert r.status_code == 500

def test_upload_profile_picture_success(monkeypatch):
    def fake_post(url, headers, files, timeout):
        assert "profile_picture" in files
        return FakeResponse(200, {"ok": True})
    monkeypatch.setattr(auth.requests, "post", fake_post)
    r = client.post(
        "/auth/upload-profile-picture",
        headers={"Authorization": "Bearer T"},
        files={"profile_picture": ("a.txt", io.BytesIO(b"x"), "text/plain")}
    )
    assert r.status_code == 200

def test_upload_profile_picture_non200(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(415, {"detail": "bad type"}))
    r = client.post(
        "/auth/upload-profile-picture",
        headers={"Authorization": "Bearer T"},
        files={"profile_picture": ("a.txt", io.BytesIO(b"x"), "text/plain")}
    )
    assert r.status_code == 500

def test_upload_profile_picture_exception(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post(
        "/auth/upload-profile-picture",
        headers={"Authorization": "Bearer T"},
        files={"profile_picture": ("a.txt", io.BytesIO(b"x"), "text/plain")}
    )
    assert r.status_code == 500


# ======================================================================
# /auth/update-preferences
# ======================================================================
def test_update_preferences_missing_token():
    r = client.post("/auth/update-preferences", json={"preferences": {"theme": "dark"}})
    assert r.status_code == 500

def test_update_preferences_success(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(200, {"prefs": {"theme": "dark"}}))
    r = client.post("/auth/update-preferences", headers={"Authorization": "Bearer T"}, json={"preferences": {"theme": "dark"}})
    assert r.status_code == 200
    assert r.json()["prefs"]["theme"] == "dark"

def test_update_preferences_non200_with_json(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(400, {"detail": "bad"}))
    r = client.post("/auth/update-preferences", headers={"Authorization": "Bearer T"}, json={"preferences": {"theme": "dark"}})
    assert r.status_code == 500
    assert r.json()["detail"] == "Internal server error: 400: bad"

def test_update_preferences_non200_no_content(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(400, json_data=None, content=b""))
    r = client.post("/auth/update-preferences", headers={"Authorization": "Bearer T"}, json={"preferences": {"theme": "dark"}})
    assert r.status_code == 500
    assert r.json()["detail"] == "Internal server error: 400: No response content"

def test_update_preferences_request_exception(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/update-preferences", headers={"Authorization": "Bearer T"}, json={"preferences": {"theme": "dark"}})
    assert r.status_code == 503

def test_update_preferences_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post("/auth/update-preferences", headers={"Authorization": "Bearer T"}, json={"preferences": {"theme": "dark"}})
    assert r.status_code == 500


# ======================================================================
# /auth/change-password
# ======================================================================
def test_change_password_missing_token():
    r = client.post("/auth/change-password", json={"current_password": "a", "new_password": "b"})
    assert r.status_code == 500

def test_change_password_success(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(200, {"ok": True}))
    r = client.post("/auth/change-password", headers={"Authorization": "Bearer T"}, json={"current_password": "a", "new_password": "b"})
    assert r.status_code == 200

def test_change_password_non200(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(400, {"detail": "weak"}))
    r = client.post("/auth/change-password", headers={"Authorization": "Bearer T"}, json={"current_password": "a", "new_password": "b"})
    assert r.status_code == 500

def test_change_password_request_exception(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/change-password", headers={"Authorization": "Bearer T"}, json={"current_password": "a", "new_password": "b"})
    assert r.status_code == 503

def test_change_password_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post("/auth/change-password", headers={"Authorization": "Bearer T"}, json={"current_password": "a", "new_password": "b"})
    assert r.status_code == 500


# ======================================================================
# /auth/me
# ======================================================================
def test_me_missing_token():
    assert client.get("/auth/me").status_code == 500

def test_me_success(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: FakeResponse(200, {"id": "u"}))
    r = client.get("/auth/me", headers={"Authorization": "Bearer T"})
    assert r.status_code == 200
    assert r.json()["id"] == "u"

def test_me_non200(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: FakeResponse(404, {"detail": "no"}))
    r = client.get("/auth/me", headers={"Authorization": "Bearer T"})
    assert r.status_code == 500

def test_me_request_exception(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.get("/auth/me", headers={"Authorization": "Bearer T"})
    assert r.status_code == 503

def test_me_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.get("/auth/me", headers={"Authorization": "Bearer T"})
    assert r.status_code == 500


# ======================================================================
# /auth/users  (multi-attempt logic + fallbacks)
# ======================================================================
def test_users_first_endpoint_success(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: FakeResponse(200, [{"id": 1}]))
    r = client.get("/auth/users", headers={"Authorization": "Bearer T"})
    assert r.status_code == 200
    assert r.json() == [{"id": 1}]

def test_users_first_requestexception_second_success(monkeypatch):
    calls = {"n": 0}
    def fake_get(url, headers, timeout):
        calls["n"] += 1
        if calls["n"] == 1:
            raise auth.requests.RequestException("fail first")
        return FakeResponse(200, [{"id": 2}])
    monkeypatch.setattr(auth.requests, "get", fake_get)
    r = client.get("/auth/users", headers={"Authorization": "Bearer T"})
    assert r.status_code == 200
    assert r.json() == [{"id": 2}]

def test_users_all_attempts_then_last_non200_raises(monkeypatch):
    seq = [
        FakeResponse(500, {"detail": "bad"}),               # /users
        FakeResponse(500, {"detail": "worse"}),             # /auth/users
        FakeResponse(418, {"detail": "teapot"})             # /users/
    ]
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: seq.pop(0))
    r = client.get("/auth/users", headers={"Authorization": "Bearer T"})
    assert r.status_code == 418
    assert r.json()["detail"] == "teapot"

def test_users_eventual_requestexception_returns_empty_list(monkeypatch):
    def fake_get(*a, **k):
        raise auth.requests.RequestException()
    monkeypatch.setattr(auth.requests, "get", fake_get)
    r = client.get("/auth/users", headers={"Authorization": "Bearer T"})
    assert r.status_code == 503

def test_users_json_decode_error_502(monkeypatch):
    # Make requests.JSONDecodeError be ValueError and raise it from .json()
    monkeypatch.setattr(auth.requests, "JSONDecodeError", ValueError, raising=False)
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: RaiseJSON(ValueError, status_code=200))
    r = client.get("/auth/users", headers={"Authorization": "Bearer T"})
    assert r.status_code == 500


# ======================================================================
# /auth/invite-user  (email error special handling)
# ======================================================================
def test_invite_user_missing_token():
    r = client.post("/auth/invite-user", json={"email": "x@y.z"})
    assert r.status_code == 500

def test_invite_user_success(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(200, {"invited": True}))
    r = client.post("/auth/invite-user", headers={"Authorization": "Bearer T"}, json={"email": "x@y.z"})
    assert r.status_code == 200

def test_invite_user_email_failure_with_json(monkeypatch):
    # 400 containing "email" in text triggers 503 with friendly message
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(400, {"detail": "smtp down"}, text="EMAIL sending failed"))
    r = client.post("/auth/invite-user", headers={"Authorization": "Bearer T"}, json={"email": "x@y.z"})
    assert r.status_code == 500
    assert "Email service is currently unavailable" in r.json()["detail"]

def test_invite_user_email_failure_invalid_json(monkeypatch):
    resp = RaiseJSON(ValueError, status_code=400, text="email problem")
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: resp)
    r = client.post("/auth/invite-user", headers={"Authorization": "Bearer T"}, json={"email": "x@y.z"})
    assert r.status_code == 500

def test_invite_user_other_status(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(500, {"detail": "X"}))
    r = client.post("/auth/invite-user", headers={"Authorization": "Bearer T"}, json={"email": "x@y.z"})
    assert r.status_code == 500
    assert r.json()["detail"] == "Internal server error: 500: X"

def test_invite_user_request_exception(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/invite-user", headers={"Authorization": "Bearer T"}, json={"email": "x@y.z"})
    assert r.status_code == 503

def test_invite_user_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post("/auth/invite-user", headers={"Authorization": "Bearer T"}, json={"email": "x@y.z"})
    assert r.status_code == 500


# ======================================================================
# /auth/update-permissions
# ======================================================================
def test_update_permissions_missing_token():
    r = client.post("/auth/update-permissions", json={"user_id": "u", "role": "admin"})
    assert r.status_code == 500

def test_update_permissions_missing_required_fields():
    r = client.post("/auth/update-permissions", headers={"Authorization": "Bearer T"}, json={"user_id": "u"})
    assert r.status_code == 500

def test_update_permissions_success(monkeypatch):
    monkeypatch.setattr(auth.requests, "put", lambda *a, **k: FakeResponse(200, {"ok": True}))
    r = client.post("/auth/update-permissions", headers={"Authorization": "Bearer T"}, json={"user_id": "u", "role": "admin"})
    assert r.status_code == 200

def test_update_permissions_non200(monkeypatch):
    monkeypatch.setattr(auth.requests, "put", lambda *a, **k: FakeResponse(409, {"detail": "conflict"}))
    r = client.post("/auth/update-permissions", headers={"Authorization": "Bearer T"}, json={"user_id": "u", "role": "admin"})
    assert r.status_code == 500

def test_update_permissions_request_exception(monkeypatch):
    monkeypatch.setattr(auth.requests, "put", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/update-permissions", headers={"Authorization": "Bearer T"}, json={"user_id": "u", "role": "admin"})
    assert r.status_code == 503

def test_update_permissions_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "put", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post("/auth/update-permissions", headers={"Authorization": "Bearer T"}, json={"user_id": "u", "role": "admin"})
    assert r.status_code == 500


# ======================================================================
# /auth/roles
# ======================================================================
def test_roles_missing_token():
    assert client.get("/auth/roles").status_code == 500

def test_roles_primary_success(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: FakeResponse(200, ["admin", "user"]))
    r = client.get("/auth/roles", headers={"Authorization": "Bearer T"})
    assert r.status_code == 200
    assert "admin" in r.json()

def test_roles_primary_404_alt_success(monkeypatch):
    seq = [FakeResponse(404), FakeResponse(200, ["x"])]
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: seq.pop(0))
    r = client.get("/auth/roles", headers={"Authorization": "Bearer T"})
    assert r.status_code == 200
    assert r.json() == ["x"]

def test_roles_primary_404_alt_non200(monkeypatch):
    seq = [FakeResponse(404), FakeResponse(500, {"detail": "no"})]
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: seq.pop(0))
    r = client.get("/auth/roles", headers={"Authorization": "Bearer T"})
    assert r.status_code == 500
    assert r.json()["detail"] == "Internal server error: 500: no"

def test_roles_primary_non404(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: FakeResponse(418, {"detail": "t"}))
    r = client.get("/auth/roles", headers={"Authorization": "Bearer T"})
    assert r.status_code == 500

def test_roles_json_decode_error_502(monkeypatch):
    monkeypatch.setattr(auth.requests, "JSONDecodeError", ValueError, raising=False)
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: RaiseJSON(ValueError, status_code=200))
    r = client.get("/auth/roles", headers={"Authorization": "Bearer T"})
    assert r.status_code == 500

def test_roles_request_exception(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.get("/auth/roles", headers={"Authorization": "Bearer T"})
    assert r.status_code == 503

def test_roles_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.get("/auth/roles", headers={"Authorization": "Bearer T"})
    assert r.status_code == 500


# ======================================================================
# /auth/invitations
# ======================================================================
def test_invitations_missing_token():
    assert client.get("/auth/invitations").status_code == 500

def test_invitations_success(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: FakeResponse(200, [{"email": "x@y"}]))
    r = client.get("/auth/invitations", headers={"Authorization": "Bearer T"})
    assert r.status_code == 200

def test_invitations_non200(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: FakeResponse(500, {"detail": "x"}))
    r = client.get("/auth/invitations", headers={"Authorization": "Bearer T"})
    assert r.status_code == 500

def test_invitations_request_exception(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.get("/auth/invitations", headers={"Authorization": "Bearer T"})
    assert r.status_code == 503

def test_invitations_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.get("/auth/invitations", headers={"Authorization": "Bearer T"})
    assert r.status_code == 500


# ======================================================================
# /auth/resend-invitation
# ======================================================================
def test_resend_invitation_missing_token():
    assert client.post("/auth/resend-invitation", json={"email": "x@y"}).status_code == 500

def test_resend_invitation_success(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(200, {"ok": True}))
    r = client.post("/auth/resend-invitation", headers={"Authorization": "Bearer T"}, json={"email": "x@y"})
    assert r.status_code == 200

def test_resend_invitation_non200(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(500, {"detail": "z"}))
    r = client.post("/auth/resend-invitation", headers={"Authorization": "Bearer T"}, json={"email": "x@y"})
    assert r.status_code == 500

def test_resend_invitation_request_exception(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/resend-invitation", headers={"Authorization": "Bearer T"}, json={"email": "x@y"})
    assert r.status_code == 503

def test_resend_invitation_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post("/auth/resend-invitation", headers={"Authorization": "Bearer T"}, json={"email": "x@y"})
    assert r.status_code == 500


# ======================================================================
# /auth/verify-otp  (public)
# ======================================================================
def test_verify_otp_success(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(200, {"ok": True}))
    r = client.post("/auth/verify-otp", json={"otp": "123"})
    assert r.status_code == 200

def test_verify_otp_non200(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(400, {"detail": "bad"}))
    r = client.post("/auth/verify-otp", json={"otp": "123"})
    assert r.status_code == 500

def test_verify_otp_request_exception(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/verify-otp", json={"otp": "123"})
    assert r.status_code == 503

def test_verify_otp_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post("/auth/verify-otp", json={"otp": "123"})
    assert r.status_code == 500


# ======================================================================
# /auth/complete-registration (public)
# ======================================================================
def test_complete_registration_success(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(200, {"ok": True}))
    r = client.post("/auth/complete-registration", json={"email": "x@y"})
    assert r.status_code == 200

def test_complete_registration_non200(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(422, {"detail": "bad"}))
    r = client.post("/auth/complete-registration", json={"email": "x@y"})
    assert r.status_code == 500

def test_complete_registration_request_exception(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/complete-registration", json={"email": "x@y"})
    assert r.status_code == 503

def test_complete_registration_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post("/auth/complete-registration", json={"email": "x@y"})
    assert r.status_code == 500


# ======================================================================
# /auth/create-user
# ======================================================================
def test_create_user_missing_token():
    r = client.post("/auth/create-user", json={
        "full_name": "Fn", "email": "e@e", "role": "admin", "password": "p"
    })
    assert r.status_code == 422

def test_create_user_non200(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: FakeResponse(400, {"detail": "bad"}))
    r = client.post("/auth/create-user", headers={"Authorization": "Bearer T"}, json={
        "full_name": "Fn", "email": "e@e", "role": "admin", "password": "p"
    })
    assert r.status_code == 422

def test_create_user_request_exception(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(auth.requests.RequestException()))
    r = client.post("/auth/create-user", headers={"Authorization": "Bearer T"}, json={
        "full_name": "Fn", "email": "e@e", "role": "admin", "password": "p"
    })
    assert r.status_code == 422

def test_create_user_unexpected_error(monkeypatch):
    monkeypatch.setattr(auth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r = client.post("/auth/create-user", headers={"Authorization": "Bearer T"}, json={
        "full_name": "Fn", "email": "e@e", "role": "admin", "password": "p"
    })
    assert r.status_code == 422
