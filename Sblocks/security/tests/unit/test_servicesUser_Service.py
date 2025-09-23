import sys
import types
import importlib
import importlib.util
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
import pytest

class SysModulesSandbox:
    def __init__(self):
        self._saved = None
    def __enter__(self):
        self._saved = sys.modules.copy()
        _mkpkg("repositories"); _mkpkg("repositories.user_repository"); _mkpkg("repositories.audit_repository")
        _mkpkg("models"); _mkpkg("models.database_models"); _mkpkg("models.api_models")
        _mkpkg("utils"); _mkpkg("utils.auth_utils"); _mkpkg("security"); _mkpkg("security.services")
        sys.modules["repositories.user_repository"] = _build_user_repo_stub()
        sys.modules["repositories.audit_repository"] = _build_audit_repo_stub()
        sys.modules["models.database_models"] = _build_db_models_stub()
        sys.modules["models.api_models"] = _build_api_models_stub()
        sys.modules["utils.auth_utils"] = _build_auth_utils_stub()
        return self
    def __exit__(self, exc_type, exc, tb):
        sys.modules.clear()
        sys.modules.update(self._saved)

def _mkpkg(name):
    if name not in sys.modules:
        m = types.ModuleType(name); m.__path__ = []; sys.modules[name] = m

# -------------------- stubs --------------------

class _UserRepository:
    users: Dict[str, Dict[str, Any]] = {}
    by_email: Dict[str, str] = {}
    last_update_args: List[Any] = []
    last_delete: Optional[str] = None

    @classmethod
    async def get_all_users(cls) -> List[Dict[str, Any]]:
        return [dict(v) for v in cls.users.values()]

    @classmethod
    async def find_by_user_id(cls, user_id: str) -> Optional[Dict[str, Any]]:
        v = cls.users.get(user_id)
        return dict(v) if v else None

    @classmethod
    async def find_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        uid = cls.by_email.get(email)
        return dict(cls.users[uid]) if uid else None

    @classmethod
    async def update_user(cls, user_id: str, updates: Dict[str, Any]) -> bool:
        if user_id not in cls.users:
            return False
        cls.users[user_id].update(updates)
        cls.last_update_args.append((user_id, dict(updates)))
        return True

    @classmethod
    async def delete_user(cls, user_id: str) -> bool:
        cls.last_delete = user_id
        if user_id in cls.users:
            email = cls.users[user_id].get("email")
            if email in cls.by_email:
                del cls.by_email[email]
            del cls.users[user_id]
            return True
        return False

    @classmethod
    async def create_user(cls, doc: Dict[str, Any]) -> Any:
        uid = doc.get("user_id")
        cls.users[uid] = dict(doc)
        email = doc.get("email")
        if email: cls.by_email[email] = uid
        return {"inserted_id": uid}

def _build_user_repo_stub():
    m = types.ModuleType("repositories.user_repository")
    m.UserRepository = _UserRepository
    return m

class _AuditRepository:
    logs: List[tuple] = []
    @staticmethod
    async def log_security_event(user_id: str, action: str, details: Dict[str, Any]):
        _AuditRepository.logs.append((user_id, action, details))
        return True

def _build_audit_repo_stub():
    m = types.ModuleType("repositories.audit_repository")
    m.AuditRepository = _AuditRepository
    return m

@dataclass
class _SecurityUser:
    user_id: str
    email: str
    phone: str
    password_hash: str
    role: str
    is_active: bool
    permissions: List[str]
    approved: bool
    full_name: str
    id: Optional[str] = None
    def model_dump(self, exclude: set | None = None):
        d = {
            "user_id": self.user_id, "email": self.email, "phone": self.phone,
            "password_hash": self.password_hash, "role": self.role,
            "is_active": self.is_active, "permissions": list(self.permissions),
            "approved": self.approved, "full_name": self.full_name
        }
        if not (exclude and "id" in exclude):
            d["id"] = self.id
        return d

@dataclass
class _UserCreatedMessage:
    user_id: str
    full_name: str
    phoneNo: str
    details: Dict[str, Any]
    preferences: Dict[str, Any]

@dataclass
class _UserUpdatedMessage:
    user_id: str
    fields: List[str]

@dataclass
class _UserDeletedMessage:
    user_id: str

def _build_db_models_stub():
    m = types.ModuleType("models.database_models")
    m.SecurityUser = _SecurityUser
    m.UserCreatedMessage = _UserCreatedMessage
    m.UserUpdatedMessage = _UserUpdatedMessage
    m.UserDeletedMessage = _UserDeletedMessage
    return m

@dataclass
class _CreateUserRequest:
    full_name: str
    email: str
    password: str
    role: str = "user"
    phoneNo: str = ""
    details: Optional[Dict[str, Any]] = field(default_factory=dict)
    def dict(self): return {
        "full_name": self.full_name, "email": self.email, "password": self.password,
        "role": self.role, "phoneNo": self.phoneNo, "details": self.details
    }

def _build_api_models_stub():
    m = types.ModuleType("models.api_models")
    m.CreateUserRequest = _CreateUserRequest
    return m

class _AuthUtils:
    ROLES = {
        "admin": {"permissions": ["all"]},
        "user": {"permissions": ["read"]},
        "viewer": {"permissions": ["view"]},
    }
    @staticmethod
    def get_role_permissions(role: str, custom_permissions: Optional[List[str]] = None):
        if custom_permissions is not None:
            return list(custom_permissions)
        base = _AuthUtils.ROLES.get(role, {"permissions": []})["permissions"]
        return list(base)
    @staticmethod
    def get_password_hash(pw: str) -> str:
        return f"hash:{pw}"
    @staticmethod
    def verify_password(plain: str, pw_hash: str) -> bool:
        return pw_hash == f"hash:{plain}"

def _build_auth_utils_stub():
    m = types.ModuleType("utils.auth_utils")
    m.ROLES = _AuthUtils.ROLES
    m.get_role_permissions = _AuthUtils.get_role_permissions
    m.get_password_hash = _AuthUtils.get_password_hash
    m.verify_password = _AuthUtils.verify_password
    return m

# -------------------- loader --------------------

def _find_user_service_path():
    from pathlib import Path
    start = Path(__file__).resolve()
    candidates = []

    # Walk up and try common layouts relative to each ancestor
    for base in [start] + list(start.parents):
        candidates.extend([
            base / "security" / "services" / "user_service.py",
            base / "services" / "user_service.py",
            base.parent / "security" / "services" / "user_service.py",
            base.parent / "services" / "user_service.py",
        ])

    # Deduplicate while preserving order
    seen = set()
    uniq = []
    for c in candidates:
        cp = c.resolve()
        if cp not in seen:
            seen.add(cp)
            uniq.append(cp)

    for c in uniq:
        if c.is_file():
            return str(c)

    # As a very last resort, try the uploaded path (may not exist locally)
    fallback = "/mnt/data/user_service.py"
    if Path(fallback).exists():
        return fallback
    return None


def import_user_module():
    import importlib.util
    from pathlib import Path

    # Try normal imports first (if the project is already on sys.path)
    for name in ("security.services.user_service", "services.user_service"):
        try:
            if name in sys.modules:
                del sys.modules[name]
            return importlib.import_module(name)
        except Exception:
            pass

    # Path-based import
    path = _find_user_service_path()
    if not path:
        raise ImportError("Unable to locate user_service.py")

    p = Path(path)
    parts = set(p.parts)

    # Decide a stable qualified name that matches the path
    if "security" in parts:
        fqname = "security.services.user_service"
        # Ensure packages exist so the module can be registered under this name
        _mkpkg("security")
        _mkpkg("security.services")
    elif "services" in parts:
        fqname = "services.user_service"
        _mkpkg("services")
    else:
        fqname = "user_service"

    spec = importlib.util.spec_from_file_location(fqname, path)
    if not spec or not spec.loader:
        raise ImportError(f"Unable to load spec for {fqname} at {path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[fqname] = mod
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod

#------------get_all_users happy--------
@pytest.mark.asyncio
async def test_get_all_users_happy_sanitizes_and_defaults():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        UserRepository.users.clear(); UserRepository.by_email.clear()
        UserRepository.users["u1"] = {
            "user_id":"u1","email":"a@x.com","password_hash":"hash:pw","_id":"X",
            "preferences":{}
        }
        UserRepository.users["u2"] = {
            "user_id":"u2","email":"b@x.com","password_hash":"hash:pw2","_id":"Y"
        }
        users = await mod.UserService.get_all_users()
        assert isinstance(users, list) and len(users)==2
        for u in users:
            assert "password_hash" not in u
            assert "_id" not in u
            assert u["id"] == u["user_id"]
            assert "preferences" in u and isinstance(u["preferences"], dict)

#------------get_all_users error--------
@pytest.mark.asyncio
async def test_get_all_users_error_raises():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        async def boom(): raise RuntimeError("db")
        UserRepository.get_all_users = boom  # type: ignore
        with pytest.raises(RuntimeError):
            await mod.UserService.get_all_users()

#------------get_user_by_id found--------
@pytest.mark.asyncio
async def test_get_user_by_id_found_sanitized_defaults():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        UserRepository.users["u9"] = {
            "user_id":"u9","email":"c@x.com","password_hash":"hash:pw","_id":"Z"
        }
        u = await mod.UserService.get_user_by_id("u9")
        assert u["id"] == "u9"
        assert "password_hash" not in u and "_id" not in u
        assert "preferences" in u and isinstance(u["preferences"], dict)

#------------get_user_by_id missing--------
@pytest.mark.asyncio
async def test_get_user_by_id_not_found_is_none():
    with SysModulesSandbox():
        mod = import_user_module()
        u = await mod.UserService.get_user_by_id("none")
        assert u is None

#------------update_user_permissions role path--------
@pytest.mark.asyncio
async def test_update_user_permissions_with_role_updates_and_audits():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        from repositories.audit_repository import AuditRepository
        UserRepository.users["ux"] = {"user_id":"ux","email":"x@x.com"}
        ok = await mod.UserService.update_user_permissions("ux", role="user")
        assert ok is True
        assert UserRepository.users["ux"]["role"] == "user"
        assert "permissions" in UserRepository.users["ux"]
        assert any(a=="permissions_updated" for _,a,_ in AuditRepository.logs)

#------------update_user_permissions custom only--------
@pytest.mark.asyncio
async def test_update_user_permissions_custom_only_updates():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        from repositories.audit_repository import AuditRepository
        UserRepository.users["uy"] = {"user_id":"uy","email":"y@x.com"}
        ok = await mod.UserService.update_user_permissions("uy", custom_permissions=["read","x"])
        assert ok is True
        assert UserRepository.users["uy"]["permissions"] == ["read","x"]
        assert any(a=="permissions_updated" for _,a,_ in AuditRepository.logs)

#------------update_user_permissions no updates--------
@pytest.mark.asyncio
async def test_update_user_permissions_no_updates_returns_false():
    with SysModulesSandbox():
        mod = import_user_module()
        ok = await mod.UserService.update_user_permissions("none")
        assert ok is False

#------------update_user_permissions error--------
@pytest.mark.asyncio
async def test_update_user_permissions_error_raises():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        async def boom(uid, up): raise RuntimeError("u")
        UserRepository.update_user = boom  # type: ignore
        with pytest.raises(RuntimeError):
            await mod.UserService.update_user_permissions("u1", role="user")

#------------update_user_profile filters and audits--------
@pytest.mark.asyncio
async def test_update_user_profile_filters_sensitive_and_audits():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        from repositories.audit_repository import AuditRepository

        async def _reset_update(uid, updates):
            if uid not in UserRepository.users:
                return False
            UserRepository.users[uid].update(updates)
            UserRepository.last_update_args.append((uid, dict(updates)))
            return True
        UserRepository.update_user = _reset_update  # ensure not overridden by earlier tests

        UserRepository.users["u1"] = {"user_id":"u1","email":"a@x.com"}
        ok = await mod.UserService.update_user_profile("u1", {
            "password_hash":"xxx","_id":"Z","user_id":"u1","full_name":"New"
        })
        assert ok is True
        assert UserRepository.users["u1"]["full_name"] == "New"
        assert any(a=="profile_updated" for _,a,_ in AuditRepository.logs)

#------------update_user_profile no safe fields--------
@pytest.mark.asyncio
async def test_update_user_profile_no_safe_fields_false():
    with SysModulesSandbox():
        mod = import_user_module()
        ok = await mod.UserService.update_user_profile("u1", {"password_hash":"x","_id":"1","user_id":"u"})
        assert ok is False

#------------update_user_preferences success--------
@pytest.mark.asyncio
async def test_update_user_preferences_success_filters_and_audits():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        from repositories.audit_repository import AuditRepository

        async def _reset_update(uid, updates):
            if uid not in UserRepository.users:
                return False
            UserRepository.users[uid].update(updates)
            UserRepository.last_update_args.append((uid, dict(updates)))
            return True
        UserRepository.update_user = _reset_update  # ensure not overridden

        UserRepository.users["u2"] = {"user_id":"u2","email":"b@x.com"}
        prefs = {"theme":"dark","unknown":"x","two_factor":"true"}
        ok = await mod.UserService.update_user_preferences("u2", prefs)
        assert ok is True
        assert UserRepository.users["u2"]["preferences"] == {"theme":"dark","two_factor":"true"}
        assert any(a=="preferences_updated" for _,a,_ in AuditRepository.logs)

#------------update_user_preferences repo false--------
@pytest.mark.asyncio
async def test_update_user_preferences_repo_false():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        async def nope(uid, up): return False
        UserRepository.update_user = nope  # type: ignore
        ok = await mod.UserService.update_user_preferences("u2", {"theme":"dark"})
        assert ok is False

#------------update_user_preferences empty returns False--------
@pytest.mark.asyncio
async def test_update_user_preferences_empty_returns_false():
    with SysModulesSandbox():
        mod = import_user_module()
        ok = await mod.UserService.update_user_preferences("u2", {"not_allowed":"x"})
        assert ok is False

#------------delete_user success--------
@pytest.mark.asyncio
async def test_delete_user_success_audits():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        from repositories.audit_repository import AuditRepository
        UserRepository.users["u3"] = {"user_id":"u3","email":"c@x.com"}; UserRepository.by_email["c@x.com"]="u3"
        ok = await mod.UserService.delete_user("u3","admin")
        assert ok is True
        assert any(a=="user_deleted" for _,a,_ in AuditRepository.logs)

#------------delete_user failure--------
@pytest.mark.asyncio
async def test_delete_user_failure_returns_false_no_audit():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.audit_repository import AuditRepository
        pre = len(AuditRepository.logs)
        ok = await mod.UserService.delete_user("missing","admin")
        assert ok is False
        assert len(AuditRepository.logs) == pre

#------------change_user_password user missing--------
@pytest.mark.asyncio
async def test_change_user_password_user_missing_raises():
    with SysModulesSandbox():
        mod = import_user_module()
        with pytest.raises(ValueError):
            await mod.UserService.change_user_password("none","old","new")

#------------change_user_password wrong current--------
@pytest.mark.asyncio
async def test_change_user_password_wrong_current_raises():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        UserRepository.users["u4"] = {"user_id":"u4","email":"d@x.com","password_hash":"hash:secret"}
        with pytest.raises(ValueError):
            await mod.UserService.change_user_password("u4","bad","newpw")

#------------change_user_password success--------
@pytest.mark.asyncio
async def test_change_user_password_success_updates_and_audits():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        from repositories.audit_repository import AuditRepository

        async def _reset_update(uid, updates):
            if uid not in UserRepository.users:
                return False
            UserRepository.users[uid].update(updates)
            UserRepository.last_update_args.append((uid, dict(updates)))
            return True
        UserRepository.update_user = _reset_update  # ensure not overridden

        UserRepository.users["u5"] = {"user_id":"u5","email":"e@x.com","password_hash":"hash:oldpw"}
        ok = await mod.UserService.change_user_password("u5","oldpw","newpw")
        assert ok is True
        assert UserRepository.users["u5"]["password_hash"] == "hash:newpw"
        assert any(a=="password_changed" for _,a,_ in AuditRepository.logs)

#------------change_user_password repo false--------
@pytest.mark.asyncio
async def test_change_user_password_repo_false_no_audit():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        from repositories.audit_repository import AuditRepository
        UserRepository.users["u6"] = {"user_id":"u6","email":"f@x.com","password_hash":"hash:pw1"}
        async def nope(uid, up): return False
        UserRepository.update_user = nope  # type: ignore
        pre = len(AuditRepository.logs)
        ok = await mod.UserService.change_user_password("u6","pw1","pw2")
        assert ok is False
        assert len(AuditRepository.logs) == pre

#------------toggle_user_status success but function raises (bug)--------
@pytest.mark.asyncio
async def test_toggle_user_status_success_logs_then_raises():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        from repositories.audit_repository import AuditRepository

        async def _force_true(uid, updates):
            if uid not in UserRepository.users:
                UserRepository.users[uid] = {"user_id": uid}
            UserRepository.users[uid].update(updates)
            return True
        UserRepository.update_user = _force_true  

        UserRepository.users["u7"] = {"user_id":"u7","email":"g@x.com"}
        result = await mod.UserService.toggle_user_status("u7", True, "admin")
        assert result is True
 
#------------toggle_user_status failure still raises and no audit--------
@pytest.mark.asyncio
async def test_toggle_user_status_update_false_raises_no_audit():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        from repositories.audit_repository import AuditRepository

        async def _force_false(uid, updates):
            return False
        UserRepository.update_user = _force_false  # type: ignore

        pre = len(AuditRepository.logs)
        result = await mod.UserService.toggle_user_status("missing", False, "admin")
        assert result is False
        assert len(AuditRepository.logs) == pre
#------------create_user_manually missing data--------
@pytest.mark.asyncio
async def test_create_user_manually_missing_data_raises():
    with SysModulesSandbox():
        mod = import_user_module()
        with pytest.raises(ValueError):
            await mod.UserService.create_user_manually(None, "creator")  # type: ignore

#------------create_user_manually existing email--------
@pytest.mark.asyncio
async def test_create_user_manually_existing_email_raises():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        from models.api_models import CreateUserRequest
        UserRepository.users["uid0"] = {"user_id":"uid0","email":"x@x.com","password_hash":"hash:pw"}
        UserRepository.by_email["x@x.com"]="uid0"
        req = CreateUserRequest(full_name="X", email="x@x.com", password="pw", role="user")
        with pytest.raises(ValueError):
            await mod.UserService.create_user_manually(req, "creator")

#------------create_user_manually happy--------
@pytest.mark.asyncio
async def test_create_user_manually_happy_path(monkeypatch):
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        from repositories.audit_repository import AuditRepository
        from models.api_models import CreateUserRequest
        fixed = uuid.UUID("00000000-0000-0000-0000-000000000001")
        monkeypatch.setattr(uuid, "uuid4", lambda: fixed)
        req = CreateUserRequest(full_name="Y", email="y@x.com", password="pw", role="user", phoneNo="1")
        result = await mod.UserService.create_user_manually(req, "creator1")
        assert result["email"] == "y@x.com"
        assert result["role"] == "user"
        assert "preferences" in result and isinstance(result["preferences"], dict)
        uid = result["user_id"]
        assert UserRepository.users[uid]["password_hash"] == "hash:pw"
        assert any(a=="manual_user_created" for _,a,_ in AuditRepository.logs)

#------------create_user_manually repo error--------
@pytest.mark.asyncio
async def test_create_user_manually_repo_error_raises(monkeypatch):
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        from models.api_models import CreateUserRequest
        fixed = uuid.UUID("00000000-0000-0000-0000-000000000002")
        monkeypatch.setattr(uuid, "uuid4", lambda: fixed)
        async def boom(doc): raise RuntimeError("db")
        UserRepository.create_user = boom  # type: ignore
        req = CreateUserRequest(full_name="Z", email="z@x.com", password="pw", role="admin", phoneNo="2")
        with pytest.raises(RuntimeError):
            await mod.UserService.create_user_manually(req, "creator2")

@pytest.mark.asyncio
async def test_get_user_by_id_error_raises():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        async def boom(uid): raise RuntimeError("x")
        UserRepository.find_by_user_id = boom  # type: ignore
        with pytest.raises(RuntimeError):
            await mod.UserService.get_user_by_id("u1")


@pytest.mark.asyncio
async def test_update_user_permissions_get_role_permissions_raises():
    with SysModulesSandbox():
        mod = import_user_module()
        from utils import auth_utils
        def raise_gp(role, custom_permissions=None):
            raise RuntimeError("gp")
        auth_utils.get_role_permissions = raise_gp  # type: ignore
        with pytest.raises(RuntimeError):
            await mod.UserService.update_user_permissions("u1", role="admin")


@pytest.mark.asyncio
async def test_update_user_profile_exception_raises():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        UserRepository.users["u1"] = {"user_id":"u1","email":"a@x.com"}
        async def boom(uid, updates): raise RuntimeError("u")
        UserRepository.update_user = boom  # type: ignore
        with pytest.raises(RuntimeError):
            await mod.UserService.update_user_profile("u1", {"full_name":"New"})


@pytest.mark.asyncio
async def test_update_user_preferences_exception_raises():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        UserRepository.users["u2"] = {"user_id":"u2","email":"b@x.com"}
        async def boom(uid, updates): raise RuntimeError("p")
        UserRepository.update_user = boom  # type: ignore
        with pytest.raises(RuntimeError):
            await mod.UserService.update_user_preferences("u2", {"theme":"dark"})


@pytest.mark.asyncio
async def test_delete_user_exception_raises():
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.user_repository import UserRepository
        async def boom(uid): raise RuntimeError("d")
        UserRepository.delete_user = boom  # type: ignore
        with pytest.raises(RuntimeError):
            await mod.UserService.delete_user("u9","admin")


@pytest.mark.asyncio
async def test_create_user_manually_audit_error_raises(monkeypatch):
    with SysModulesSandbox():
        mod = import_user_module()
        from repositories.audit_repository import AuditRepository
        from models.api_models import CreateUserRequest
        import uuid as _uuid
        monkeypatch.setattr(_uuid, "uuid4", lambda: _uuid.UUID("00000000-0000-0000-0000-0000000000aa"))
        async def boom(*a, **k): raise RuntimeError("audit")
        AuditRepository.log_security_event = boom  # type: ignore
        req = CreateUserRequest(full_name="N", email="n@x.com", password="pw", role="user")
        with pytest.raises(RuntimeError):
            await mod.UserService.create_user_manually(req, "creator")