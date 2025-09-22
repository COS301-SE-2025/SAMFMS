import sys, types, importlib, importlib.util
from dataclasses import dataclass
from datetime import datetime, timedelta
import pytest

class SysModulesSandbox:
    def __enter__(self):
        self._saved = sys.modules.copy()
        _mk("security"); _mk("security.utils")
        _mk("passlib"); _mk("passlib.context")
        _mk("fastapi"); _mk("fastapi.security"); _mk("fastapi.status")
        _mk("config"); _mk("config.settings")

        sys.modules["passlib.context"] = _build_passlib_stub()

        jwt_stub = _build_jwt_stub()
        jose_pkg = types.ModuleType("jose")
        jose_pkg.JWTError = jwt_stub.JWTError
        jose_pkg.jwt = jwt_stub
        sys.modules["jose"] = jose_pkg
        sys.modules["jose.jwt"] = jwt_stub

        sys.modules["fastapi"] = _build_fastapi_stub()
        sys.modules["fastapi.security"] = _build_fastapi_security_stub()
        sys.modules["fastapi.status"] = _build_status_stub()
        sys.modules["config.settings"] = _build_settings_stub()
        return self

    def __exit__(self, *a):
        sys.modules.clear(); sys.modules.update(self._saved)

def _mk(name):
    if name not in sys.modules:
        m = types.ModuleType(name); 
        if "." not in name: m.__path__=[]
        sys.modules[name]=m

def _build_passlib_stub():
    m = types.ModuleType("passlib.context")
    class CryptContext:
        def __init__(self, schemes=None, deprecated=None): pass
        def hash(self, pw:str) -> str: return f"hash:{pw}"
        def verify(self, plain:str, hashed:str) -> bool: return hashed == f"hash:{plain}"
    m.CryptContext = CryptContext
    return m

def _build_jwt_stub():
    m = types.ModuleType("jose.jwt")
    class JWTError(Exception): pass
    _store = {}
    def encode(data:dict, key:str, algorithm:str)->str:
        tok = f"t{len(_store)+1}"
        _store[tok] = dict(data)
        return tok
    def decode(token:str, key:str, algorithms:list|tuple):
        if token not in _store:
            raise JWTError("bad token")
        return dict(_store[token])
    m.JWTError = JWTError
    m.encode = encode; m.decode = decode; m._store = _store
    return m

def _build_fastapi_stub():
    m = types.ModuleType("fastapi")
    class HTTPException(Exception):
        def __init__(self, status_code:int, detail:str, headers:dict|None=None):
            super().__init__(detail); self.status_code=status_code; self.detail=detail; self.headers=headers or {}
    class Depends:
        def __init__(self, dep): self.dep = dep
    m.HTTPException = HTTPException; m.Depends = Depends
    return m

def _build_fastapi_security_stub():
    m = types.ModuleType("fastapi.security")
    @dataclass
    class HTTPAuthorizationCredentials:
        scheme: str
        credentials: str
    class HTTPBearer:
        def __call__(self): 
            return None
    m.HTTPAuthorizationCredentials = HTTPAuthorizationCredentials
    m.HTTPBearer = HTTPBearer
    return m

def _build_status_stub():
    m = types.ModuleType("fastapi.status")
    m.HTTP_401_UNAUTHORIZED = 401
    m.HTTP_403_FORBIDDEN = 403
    return m

def _build_settings_stub():
    m = types.ModuleType("config.settings")
    class _Settings:
        ACCESS_TOKEN_EXPIRE_MINUTES = 15
        REFRESH_TOKEN_EXPIRE_DAYS = 7
        JWT_SECRET_KEY = "secret"
        ALGORITHM = "HS256"
    m.settings = _Settings()
    return m

def import_auth_utils():
    import importlib, importlib.util
    from pathlib import Path

    for name in ("security.utils.auth_utils", "utils.auth_utils", "auth_utils"):
        try:
            if name in sys.modules: del sys.modules[name]
            return importlib.import_module(name)
        except Exception:
            pass

    here = Path(__file__).resolve()
    candidates = []
    for base in [here] + list(here.parents):
        candidates.extend([
            base / "security" / "utils" / "auth_utils.py",
            base / "utils" / "auth_utils.py",
            base.parent / "security" / "utils" / "auth_utils.py",
            base.parent / "utils" / "auth_utils.py",
        ])

    seen = set()
    for c in candidates:
        p = c.resolve()
        if p in seen: continue
        seen.add(p)
        if p.is_file():
            parts = set(p.parts)
            if "security" in parts:
                fqname = "security.utils.auth_utils"
                _mk("security"); _mk("security.utils")
            elif "utils" in parts:
                fqname = "utils.auth_utils"
                _mk("utils")
            else:
                fqname = "auth_utils"
            spec = importlib.util.spec_from_file_location(fqname, str(p))
            if not spec or not spec.loader:
                continue
            mod = importlib.util.module_from_spec(spec)
            sys.modules[fqname] = mod
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            return mod

    raise ImportError("Unable to locate security/utils/auth_utils.py")

#------------verify_password true/false--------
def test_verify_password_true_and_false():
    with SysModulesSandbox():
        mod = import_auth_utils()
        assert mod.verify_password("pw","hash:pw") is True
        assert mod.verify_password("pw","hash:other") is False

#------------get_password_hash--------
def test_get_password_hash_prefix():
    with SysModulesSandbox():
        mod = import_auth_utils()
        h = mod.get_password_hash("pw")
        assert isinstance(h,str) and h.startswith("hash:")

#------------create_access_token includes_claims--------
def test_create_access_token_contains_exp_and_iat_and_role():
    with SysModulesSandbox():
        mod = import_auth_utils()
        token = mod.create_access_token({"sub":"U1","role":"admin","permissions":["*"]})
        from jose import jwt
        payload = jwt._store[token]
        assert "exp" in payload and "iat" in payload
        assert payload["sub"]=="U1" and payload["role"]=="admin"

#------------create_refresh_token payload--------
def test_create_refresh_token_contains_type_and_sub():
    with SysModulesSandbox():
        mod = import_auth_utils()
        token = mod.create_refresh_token("U2")
        from jose import jwt
        payload = jwt._store[token]
        assert payload["sub"]=="U2" and payload["type"]=="refresh" and "iat" in payload and "exp" in payload

#------------verify_access_token success--------
def test_verify_access_token_success_returns_info():
    with SysModulesSandbox():
        mod = import_auth_utils()
        t = mod.create_access_token({"sub":"U3","role":"user","permissions":["vehicles:read"]})
        info = mod.verify_access_token(t)
        assert info["user_id"]=="U3" and info["role"]=="user" and info["permissions"]==["vehicles:read"] and info["token"]==t

#------------verify_access_token_missing_sub_401--------
def test_verify_access_token_missing_sub_raises_401():
    with SysModulesSandbox():
        mod = import_auth_utils()
        from jose import jwt
        tok = jwt.encode({"role":"user","permissions":[],"iat":datetime.utcnow(),"exp":datetime.utcnow()+timedelta(minutes=5)}, "secret", "HS256")
        with pytest.raises(sys.modules["fastapi"].HTTPException) as ei:
            mod.verify_access_token(tok)
        assert ei.value.status_code == 401

#------------verify_access_token_invalid_token_401--------
def test_verify_access_token_invalid_token_raises_401():
    with SysModulesSandbox():
        mod = import_auth_utils()
        with pytest.raises(sys.modules["fastapi"].HTTPException) as ei:
            mod.verify_access_token("nope")
        assert ei.value.status_code == 401

#------------verify_refresh_token_success--------
def test_verify_refresh_token_success_returns_user_id():
    with SysModulesSandbox():
        mod = import_auth_utils()
        t = mod.create_refresh_token("U4")
        uid = mod.verify_refresh_token(t)
        assert uid == "U4"

#------------verify_refresh_token_wrong_type_401--------
def test_verify_refresh_token_wrong_type_or_missing_sub_raises_401():
    with SysModulesSandbox():
        mod = import_auth_utils()
        from jose import jwt
        t1 = jwt.encode({"sub":"U5","type":"access","iat":datetime.utcnow(),"exp":datetime.utcnow()+timedelta(days=1)}, "secret","HS256")
        t2 = jwt.encode({"type":"refresh","iat":datetime.utcnow(),"exp":datetime.utcnow()+timedelta(days=1)}, "secret","HS256")
        for tok in (t1,t2):
            with pytest.raises(sys.modules["fastapi"].HTTPException) as ei:
                mod.verify_refresh_token(tok)
            assert ei.value.status_code == 401

#------------has_permission all/exact/wildcard/false--------
def test_has_permission_variants():
    with SysModulesSandbox():
        mod = import_auth_utils()
        assert mod.has_permission(["*"], "anything:any")
        assert mod.has_permission(["vehicles:read"], "vehicles:read")
        assert mod.has_permission(["vehicles:*"], "vehicles:delete")
        assert not mod.has_permission(["drivers:read"], "vehicles:read")

#------------require_permission success--------
@pytest.mark.asyncio
async def test_require_permission_success_injects_current_user():
    with SysModulesSandbox():
        mod = import_auth_utils()
        from fastapi.security import HTTPAuthorizationCredentials
        t = mod.create_access_token({"sub":"U6","role":"user","permissions":["reports:read"]})
        @mod.require_permission("reports:read")
        async def ep(credentials: HTTPAuthorizationCredentials, current_user=None):
            return {"ok": True, "user": current_user}
        res = await ep(credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=t))
        assert res["ok"] is True and res["user"]["user_id"] == "U6"

#------------require_permission_missing_credentials_401--------
@pytest.mark.asyncio
async def test_require_permission_missing_credentials_raises_401():
    with SysModulesSandbox():
        mod = import_auth_utils()
        @mod.require_permission("reports:read")
        async def ep():
            return {"ok":True}
        with pytest.raises(sys.modules["fastapi"].HTTPException) as ei:
            await ep()
        assert ei.value.status_code == 401

#------------require_permission_insufficient_403--------
@pytest.mark.asyncio
async def test_require_permission_insufficient_raises_403():
    with SysModulesSandbox():
        mod = import_auth_utils()
        from fastapi.security import HTTPAuthorizationCredentials
        t = mod.create_access_token({"sub":"U7","role":"user","permissions":["drivers:read"]})
        @mod.require_permission("reports:read")
        async def ep(credentials: HTTPAuthorizationCredentials):
            return {"ok":True}
        with pytest.raises(sys.modules["fastapi"].HTTPException) as ei:
            await ep(credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=t))
        assert ei.value.status_code == 403

#------------require_permission_invalid_token_401--------
@pytest.mark.asyncio
async def test_require_permission_invalid_token_raises_401():
    with SysModulesSandbox():
        mod = import_auth_utils()
        from fastapi.security import HTTPAuthorizationCredentials
        @mod.require_permission("x:y")
        async def ep(credentials: HTTPAuthorizationCredentials):
            return {"ok":True}
        with pytest.raises(sys.modules["fastapi"].HTTPException) as ei:
            await ep(credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="badtoken"))
        assert ei.value.status_code == 401

#------------require_role success--------
@pytest.mark.asyncio
async def test_require_role_success_injects_current_user():
    with SysModulesSandbox():
        mod = import_auth_utils()
        from fastapi.security import HTTPAuthorizationCredentials
        t = mod.create_access_token({"sub":"U8","role":"admin","permissions":["*"]})
        @mod.require_role(["admin","fleet_manager"])
        async def ep(credentials: HTTPAuthorizationCredentials, current_user=None):
            return current_user["role"]
        res = await ep(credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=t))
        assert res == "admin"

#------------require_role_missing_credentials_401--------
@pytest.mark.asyncio
async def test_require_role_missing_credentials_raises_401():
    with SysModulesSandbox():
        mod = import_auth_utils()
        @mod.require_role(["admin"])
        async def ep():
            return True
        with pytest.raises(sys.modules["fastapi"].HTTPException) as ei:
            await ep()
        assert ei.value.status_code == 401

#------------require_role_forbidden_403--------
@pytest.mark.asyncio
async def test_require_role_forbidden_raises_403():
    with SysModulesSandbox():
        mod = import_auth_utils()
        from fastapi.security import HTTPAuthorizationCredentials
        t = mod.create_access_token({"sub":"U9","role":"driver","permissions":["vehicles:read_assigned"]})
        @mod.require_role(["admin","fleet_manager"])
        async def ep(credentials: HTTPAuthorizationCredentials):
            return True
        with pytest.raises(sys.modules["fastapi"].HTTPException) as ei:
            await ep(credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=t))
        assert ei.value.status_code == 403

#------------require_role_invalid_token_401--------
@pytest.mark.asyncio
async def test_require_role_invalid_token_raises_401():
    with SysModulesSandbox():
        mod = import_auth_utils()
        from fastapi.security import HTTPAuthorizationCredentials
        @mod.require_role(["admin"])
        async def ep(credentials: HTTPAuthorizationCredentials):
            return True
        with pytest.raises(sys.modules["fastapi"].HTTPException) as ei:
            await ep(credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials="nope"))
        assert ei.value.status_code == 401

#------------get_current_user returns decoded--------
@pytest.mark.asyncio
async def test_get_current_user_returns_decoded_user():
    with SysModulesSandbox():
        mod = import_auth_utils()
        from fastapi.security import HTTPAuthorizationCredentials
        t = mod.create_access_token({"sub":"U10","role":"user","permissions":[]})
        res = await mod.get_current_user(credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=t))
        assert res["user_id"] == "U10"

#------------get_role_permissions override_and_defaults--------
def test_get_role_permissions_override_and_defaults_and_unknown():
    with SysModulesSandbox():
        mod = import_auth_utils()
        assert mod.get_role_permissions("driver")  # default exists
        assert mod.get_role_permissions("admin")   # "*"
        assert mod.get_role_permissions("x") == []
        assert mod.get_role_permissions("driver", ["custom"]) == ["custom"]

#------------get_rate_limit_key--------
def test_get_rate_limit_key_formats_string():
    with SysModulesSandbox():
        mod = import_auth_utils()
        assert mod.get_rate_limit_key("otp","user1") == "rate_limit:otp:user1"
