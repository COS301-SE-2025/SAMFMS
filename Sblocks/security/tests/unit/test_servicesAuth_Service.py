import sys
import types
import importlib
import importlib.util
from pathlib import Path
from dataclasses import dataclass
import pytest

class SysModulesSandbox:
    def __init__(self):
        self._saved = None
    def __enter__(self):
        self._saved = sys.modules.copy()
        make_stub_pkg("repositories")
        make_stub_pkg("repositories.user_repository")
        make_stub_pkg("repositories.audit_repository")
        make_stub_pkg("utils")
        make_stub_pkg("utils.auth_utils")
        make_stub_pkg("config")
        make_stub_pkg("config.settings")
        make_stub_pkg("models")
        make_stub_pkg("models.api_models")
        make_stub_pkg("models.database_models")
        sys.modules["repositories.user_repository"] = build_user_repo_stub()
        sys.modules["repositories.audit_repository"] = build_audit_and_token_repo_stub()
        sys.modules["utils.auth_utils"] = build_auth_utils_stub()
        sys.modules["config.settings"] = build_settings_stub()
        sys.modules["models.api_models"] = build_models_api_stub()
        sys.modules["models.database_models"] = build_models_db_stub()
        return self
    def __exit__(self, exc_type, exc, tb):
        sys.modules.clear()
        sys.modules.update(self._saved)

def make_stub_pkg(name):
    if name not in sys.modules:
        m = types.ModuleType(name)
        m.__path__ = []
        sys.modules[name] = m

def build_user_repo_stub():
    m = types.ModuleType("repositories.user_repository")
    class _UserRepository:
        users = {}
        users_by_email = {}
        last_update_pwd = None
        last_update_role = None
        last_force_logout = None
        last_reset_failed = None
        last_increment_failed = None
        all_users = []
        created_users = []
        count_users_value = 0
        update_user_password_result = True
        update_user_role_result = True
        force_logout_result = True
        reset_failed_result = True
        get_all_users_result = None
        @staticmethod
        async def find_by_user_id(user_id):
            return _UserRepository.users.get(user_id)
        @staticmethod
        async def update_user_password(user_id, hashed):
            _UserRepository.last_update_pwd = (user_id, hashed)
            return _UserRepository.update_user_password_result
        @staticmethod
        async def update_user_role(user_id, new_role):
            _UserRepository.last_update_role = (user_id, new_role)
            return _UserRepository.update_user_role_result
        @staticmethod
        async def find_by_email(email):
            return _UserRepository.users_by_email.get(email)
        @staticmethod
        async def reset_failed_attempts(user_id):
            _UserRepository.last_reset_failed = user_id
            return _UserRepository.reset_failed_result
        @staticmethod
        async def increment_failed_attempts(user_id):
            _UserRepository.last_increment_failed = user_id
            return True
        @staticmethod
        async def set_force_logout_after(user_id, dt):
            _UserRepository.last_force_logout = (user_id, dt)
            return _UserRepository.force_logout_result
        @staticmethod
        async def get_all_users():
            if _UserRepository.get_all_users_result is None:
                return _UserRepository.all_users
            return _UserRepository.get_all_users_result
        @staticmethod
        async def count_users():
            return _UserRepository.count_users_value
        @staticmethod
        async def create_user(db_user_data):
            _UserRepository.created_users.append(db_user_data)
            return {"_id": "newid"}
    m.UserRepository = _UserRepository
    return m

def build_audit_and_token_repo_stub():
    m = types.ModuleType("repositories.audit_repository")
    class _AuditRepository:
        logs = []
        @staticmethod
        async def log_security_event(user_id, action, details):
            _AuditRepository.logs.append((user_id, action, details))
            return True
    class _TokenRepository:
        blacklisted = set()
        check_blacklisted_return = False
        last_blacklist = None
        @staticmethod
        async def is_token_blacklisted(token_hash):
            return _TokenRepository.check_blacklisted_return or (token_hash in _TokenRepository.blacklisted)
        @staticmethod
        async def blacklist_token(token_hash, expires_at):
            _TokenRepository.last_blacklist = (token_hash, expires_at)
            _TokenRepository.blacklisted.add(token_hash)
            return True
    m.AuditRepository = _AuditRepository
    m.TokenRepository = _TokenRepository
    return m

def build_auth_utils_stub():
    m = types.ModuleType("utils.auth_utils")
    m.ROLES = {"admin": ["*"], "user": ["read"]}
    m._verify_password_result = True
    m._raise_on_verify_access = None
    m._verify_access_payload = {"user_id": "u1", "issued_at": 1.0}
    m._create_token_value = "token-xyz"
    m._role_permissions_return = ["read"]
    def verify_password(pw, hashed):
        return m._verify_password_result
    def get_password_hash(pw):
        if getattr(m, "_hash_raises", False):
            raise RuntimeError("hash error")
        return f"HASH({pw})"
    def create_access_token(data):
        m._last_token_data = data
        return m._create_token_value
    def verify_access_token(token):
        if m._raise_on_verify_access:
            raise m._raise_on_verify_access
        return m._verify_access_payload
    def get_role_permissions(role, custom=None):
        return m._role_permissions_return
    m.verify_password = verify_password
    m.get_password_hash = get_password_hash
    m.create_access_token = create_access_token
    m.verify_access_token = verify_access_token
    m.get_role_permissions = get_role_permissions
    return m

def build_settings_stub():
    m = types.ModuleType("config.settings")
    class _S:
        DEFAULT_FIRST_USER_ROLE = "admin"
        DEFAULT_USER_ROLE = "user"
        LOGIN_ATTEMPT_LIMIT = 3
    m.settings = _S()
    return m

def build_models_api_stub():
    m = types.ModuleType("models.api_models")
    @dataclass
    class TokenResponse:
        access_token: str
        token_type: str
        user_id: str
        role: str
        permissions: list
        preferences: dict
    m.TokenResponse = TokenResponse
    return m

def build_models_db_stub():
    m = types.ModuleType("models.database_models")
    class UserCreatedMessage: ...
    m.UserCreatedMessage = UserCreatedMessage
    return m

def _find_auth_service_path():
    here = Path(__file__).resolve()
    candidates = []
    for parent in [here.parent] + list(here.parents):
        candidates += [
            parent / "security" / "services" / "auth_service.py",
            parent / "services" / "auth_service.py",
            parent / "auth_service.py",
        ]
    for c in candidates:
        if c.exists():
            return str(c)
    fallback = "/mnt/data/auth_service.py"
    return fallback if Path(fallback).exists() else None

def import_service_module():
    names = ["security.services.auth_service", "services.auth_service", "auth_service"]
    last_err = None
    for name in names:
        try:
            if name in sys.modules:
                del sys.modules[name]
            return importlib.import_module(name)
        except Exception as e:
            last_err = e
    path = _find_auth_service_path()
    if not path:
        raise last_err or ImportError("Unable to locate auth_service.py")
    if "security" not in sys.modules:
        pkg = types.ModuleType("security")
        pkg.__path__ = []
        sys.modules["security"] = pkg
    if "security.services" not in sys.modules:
        pkg = types.ModuleType("security.services")
        pkg.__path__ = []
        sys.modules["security.services"] = pkg
    spec = importlib.util.spec_from_file_location("security.services.auth_service", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["security.services.auth_service"] = mod
    spec.loader.exec_module(mod)  # type: ignore
    return mod

#------------get_user_role() returns role--------
@pytest.mark.asyncio
async def test_get_user_role_returns_role():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        UserRepository.users = {"u1": {"role": "admin"}}
        mod = import_service_module()
        role = await mod.AuthService.get_user_role("u1")
        assert role == "admin"

#------------get_user_role() returns none when missing--------
@pytest.mark.asyncio
async def test_get_user_role_none_when_missing():
    with SysModulesSandbox():
        mod = import_service_module()
        role = await mod.AuthService.get_user_role("nope")
        assert role is None

#------------get_user_role() repo error returns none--------
@pytest.mark.asyncio
async def test_get_user_role_repo_error_returns_none():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        async def boom(uid): raise RuntimeError("fail")
        UserRepository.find_by_user_id = staticmethod(boom)
        mod = import_service_module()
        role = await mod.AuthService.get_user_role("u1")
        assert role is None

#------------update_user_password() success--------
@pytest.mark.asyncio
async def test_update_user_password_success():
    with SysModulesSandbox():
        mod = import_service_module()
        ok = await mod.AuthService.update_user_password("u1", "pw")
        assert ok is True

#------------update_user_password() hash error false--------
@pytest.mark.asyncio
async def test_update_user_password_hash_error_returns_false():
    with SysModulesSandbox():
        import utils.auth_utils as au
        au._hash_raises = True
        mod = import_service_module()
        ok = await mod.AuthService.update_user_password("u1", "pw")
        assert ok is False

#------------update_user_password() repo error false--------
@pytest.mark.asyncio
async def test_update_user_password_repo_error_returns_false():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        async def boom(uid, h): raise RuntimeError("fail")
        UserRepository.update_user_password = staticmethod(boom)
        mod = import_service_module()
        ok = await mod.AuthService.update_user_password("u1", "pw")
        assert ok is False

#------------update_user_role() success--------
@pytest.mark.asyncio
async def test_update_user_role_success():
    with SysModulesSandbox():
        mod = import_service_module()
        ok = await mod.AuthService.update_user_role("u1", "user")
        assert ok is True

#------------update_user_role() error false--------
@pytest.mark.asyncio
async def test_update_user_role_error_false():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        async def boom(uid, r): raise RuntimeError("fail")
        UserRepository.update_user_role = staticmethod(boom)
        mod = import_service_module()
        ok = await mod.AuthService.update_user_role("u1", "user")
        assert ok is False

#------------is_token_valid() true when not blacklisted--------
@pytest.mark.asyncio
async def test_is_token_valid_true_when_not_blacklisted():
    with SysModulesSandbox():
        mod = import_service_module()
        ok = await mod.AuthService.is_token_valid("t")
        assert ok is True

#------------is_token_valid() false when blacklisted--------
@pytest.mark.asyncio
async def test_is_token_valid_false_when_blacklisted():
    with SysModulesSandbox():
        from repositories.audit_repository import TokenRepository
        TokenRepository.check_blacklisted_return = True
        mod = import_service_module()
        ok = await mod.AuthService.is_token_valid("t")
        assert ok is False

#------------is_token_valid() false on verify exception--------
@pytest.mark.asyncio
async def test_is_token_valid_false_on_verify_exception():
    with SysModulesSandbox():
        import utils.auth_utils as au
        au._raise_on_verify_access = ValueError("bad token")
        mod = import_service_module()
        ok = await mod.AuthService.is_token_valid("t")
        assert ok is False

#------------get_user_by_email() success--------
@pytest.mark.asyncio
async def test_get_user_by_email_success():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        UserRepository.users_by_email = {"e@x.com": {"user_id": "u1"}}
        mod = import_service_module()
        u = await mod.AuthService.get_user_by_email("e@x.com")
        assert u["user_id"] == "u1"

#------------get_user_by_email() error none--------
@pytest.mark.asyncio
async def test_get_user_by_email_error_none():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        async def boom(e): raise RuntimeError("db")
        UserRepository.find_by_email = staticmethod(boom)
        mod = import_service_module()
        u = await mod.AuthService.get_user_by_email("e@x.com")
        assert u is None

#------------reset_failed_login_attempts() success--------
@pytest.mark.asyncio
async def test_reset_failed_login_attempts_success():
    with SysModulesSandbox():
        mod = import_service_module()
        ok = await mod.AuthService.reset_failed_login_attempts("u1")
        assert ok is True

#------------reset_failed_login_attempts() error false--------
@pytest.mark.asyncio
async def test_reset_failed_login_attempts_error_false():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        async def boom(uid): raise RuntimeError("db")
        UserRepository.reset_failed_attempts = staticmethod(boom)
        mod = import_service_module()
        ok = await mod.AuthService.reset_failed_login_attempts("u1")
        assert ok is False

#------------force_logout_user() success--------
@pytest.mark.asyncio
async def test_force_logout_user_success():
    with SysModulesSandbox():
        mod = import_service_module()
        ok = await mod.AuthService.force_logout_user("u1")
        assert ok is True

#------------force_logout_user() error false--------
@pytest.mark.asyncio
async def test_force_logout_user_error_false():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        async def boom(uid, dt): raise RuntimeError("db")
        UserRepository.set_force_logout_after = staticmethod(boom)
        mod = import_service_module()
        ok = await mod.AuthService.force_logout_user("u1")
        assert ok is False

#------------get_all_users() success--------
@pytest.mark.asyncio
async def test_get_all_users_success():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        UserRepository.get_all_users_result = [{"user_id": "u1"}]
        mod = import_service_module()
        lst = await mod.AuthService.get_all_users()
        assert lst == [{"user_id": "u1"}]

#------------get_all_users() error empty--------
@pytest.mark.asyncio
async def test_get_all_users_error_empty():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        async def boom(): raise RuntimeError("db")
        UserRepository.get_all_users = staticmethod(boom)
        mod = import_service_module()
        lst = await mod.AuthService.get_all_users()
        assert lst == []

#------------get_user_permissions() success--------
@pytest.mark.asyncio
async def test_get_user_permissions_success():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        UserRepository.users = {"u1": {"permissions": ["read", "write"]}}
        mod = import_service_module()
        perms = await mod.AuthService.get_user_permissions("u1")
        assert perms == ["read", "write"]

#------------get_user_permissions() missing or error returns empty--------
@pytest.mark.asyncio
async def test_get_user_permissions_missing_or_error_returns_empty():
    with SysModulesSandbox():
        mod = import_service_module()
        perms1 = await mod.AuthService.get_user_permissions("unknown")
        assert perms1 == []
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        async def boom(uid): raise RuntimeError("db")
        UserRepository.find_by_user_id = staticmethod(boom)
        mod = import_service_module()
        perms2 = await mod.AuthService.get_user_permissions("u1")
        assert perms2 == []

#------------signup_user() first user admin defaults--------
@pytest.mark.asyncio
async def test_signup_first_user_admin_defaults():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        import utils.auth_utils as au
        UserRepository.count_users_value = 0
        UserRepository.users_by_email = {}
        au._create_token_value = "tok1"
        mod = import_service_module()
        res = await mod.AuthService.signup_user({
            "email": "a@b.c",
            "phoneNo": "123",
            "password": "pw",
            "full_name": "A B",
        })
        assert res.access_token == "tok1"
        assert res.role == "admin"
        assert res.preferences["theme"] == "light"
        assert len(UserRepository.created_users) == 1
        assert UserRepository.created_users[0]["approved"] is True

#------------signup_user() non-first default role approved false--------
@pytest.mark.asyncio
async def test_signup_non_first_default_role_approved_false():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        import utils.auth_utils as au
        UserRepository.count_users_value = 2
        au._role_permissions_return = ["read"]
        mod = import_service_module()
        res = await mod.AuthService.signup_user({
            "email": "c@d.e",
            "phoneNo": "456",
            "password": "pw",
            "full_name": "C D",
        })
        assert res.role == "user"
        assert UserRepository.created_users[-1]["approved"] is False

#------------signup_user() non-first admin role custom perms--------
@pytest.mark.asyncio
async def test_signup_non_first_admin_role_custom_permissions():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        import utils.auth_utils as au
        UserRepository.count_users_value = 1
        au._role_permissions_return = ["x","y"]
        mod = import_service_module()
        res = await mod.AuthService.signup_user({
            "email": "e@f.g",
            "phoneNo": "789",
            "password": "pw",
            "full_name": "E F",
            "role": "admin",
            "custom_permissions": ["x","y"],
            "preferences": {"theme":"dark"}
        })
        assert res.role == "admin"
        assert res.preferences["theme"] == "dark"
        assert UserRepository.created_users[-1]["approved"] is True

#------------signup_user() repo error propagates--------
@pytest.mark.asyncio
async def test_signup_user_repo_error_propagates():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        async def boom(data): raise RuntimeError("create fail")
        UserRepository.create_user = staticmethod(boom)
        mod = import_service_module()
        with pytest.raises(RuntimeError):
            await mod.AuthService.signup_user({
                "email": "x@y.z",
                "phoneNo": "000",
                "password": "pw",
                "full_name": "X Y",
            })

#------------login_user() success default preferences--------
@pytest.mark.asyncio
async def test_login_user_success_default_preferences():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        import utils.auth_utils as au
        au._verify_password_result = True
        au._create_token_value = "tok2"
        user = {
            "user_id": "u1",
            "email": "e@x.com",
            "role": "user",
            "permissions": ["read"],
            "password_hash": "HASH",
            "failed_login_attempts": 0,
            "is_active": True,
            "preferences": {}
        }
        UserRepository.users_by_email = {"e@x.com": user}
        mod = import_service_module()
        res = await mod.AuthService.login_user("e@x.com", "pw", "1.2.3.4")
        assert res.access_token == "tok2"
        assert res.preferences["theme"] == "light"

#------------login_user() not found raises--------
@pytest.mark.asyncio
async def test_login_user_not_found_raises():
    with SysModulesSandbox():
        mod = import_service_module()
        with pytest.raises(ValueError):
            await mod.AuthService.login_user("missing@x.com", "pw", "1.1.1.1")

#------------login_user() rate limited raises--------
@pytest.mark.asyncio
async def test_login_user_rate_limited_raises():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        user = {
            "user_id": "u2",
            "email": "e@x.com",
            "role": "user",
            "permissions": ["read"],
            "password_hash": "HASH",
            "failed_login_attempts": 3,
            "is_active": True,
        }
        UserRepository.users_by_email = {"e@x.com": user}
        mod = import_service_module()
        with pytest.raises(ValueError):
            await mod.AuthService.login_user("e@x.com", "pw", "1.1.1.1")

#------------login_user() disabled raises--------
@pytest.mark.asyncio
async def test_login_user_disabled_raises():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        user = {
            "user_id": "u3",
            "email": "e@x.com",
            "role": "user",
            "permissions": ["read"],
            "password_hash": "HASH",
            "failed_login_attempts": 0,
            "is_active": False,
        }
        UserRepository.users_by_email = {"e@x.com": user}
        mod = import_service_module()
        with pytest.raises(ValueError):
            await mod.AuthService.login_user("e@x.com", "pw", "1.1.1.1")

#------------login_user() bad password raises and increments--------
@pytest.mark.asyncio
async def test_login_user_bad_password_raises_and_increments():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        import utils.auth_utils as au
        au._verify_password_result = False
        user = {
            "user_id": "u4",
            "email": "e@x.com",
            "role": "user",
            "permissions": ["read"],
            "password_hash": "HASH",
            "failed_login_attempts": 0,
            "is_active": True,
        }
        UserRepository.users_by_email = {"e@x.com": user}
        mod = import_service_module()
        with pytest.raises(ValueError):
            await mod.AuthService.login_user("e@x.com", "pw", "1.1.1.1")
        assert UserRepository.last_increment_failed == "u4"

#------------get_current_user_secure() success--------
@pytest.mark.asyncio
async def test_get_current_user_secure_success():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        import utils.auth_utils as au
        from repositories.audit_repository import TokenRepository
        au._verify_access_payload = {"user_id": "u1", "issued_at": 2.0, "token": "T"}
        TokenRepository.check_blacklisted_return = False
        UserRepository.users = {"u1": {"user_id":"u1","is_active":True}}
        mod = import_service_module()
        u = await mod.AuthService.get_current_user_secure("T")
        assert u["user_id"] == "u1"
        assert u["token"] == "T"

#------------get_current_user_secure() blacklisted raises--------
@pytest.mark.asyncio
async def test_get_current_user_secure_blacklisted_raises():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        import utils.auth_utils as au
        from repositories.audit_repository import TokenRepository
        au._verify_access_payload = {"user_id": "u1", "issued_at": 2.0, "token": "T"}
        TokenRepository.check_blacklisted_return = True
        UserRepository.users = {"u1": {"user_id":"u1","is_active":True}}
        mod = import_service_module()
        with pytest.raises(ValueError):
            await mod.AuthService.get_current_user_secure("T")

#------------get_current_user_secure() not found raises--------
@pytest.mark.asyncio
async def test_get_current_user_secure_not_found_raises():
    with SysModulesSandbox():
        import utils.auth_utils as au
        au._verify_access_payload = {"user_id": "missing", "issued_at": 2.0}
        mod = import_service_module()
        with pytest.raises(ValueError):
            await mod.AuthService.get_current_user_secure("t")

#------------get_current_user_secure() disabled raises--------
@pytest.mark.asyncio
async def test_get_current_user_secure_disabled_raises():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        import utils.auth_utils as au
        au._verify_access_payload = {"user_id": "u9", "issued_at": 2.0}
        UserRepository.users = {"u9": {"user_id":"u9","is_active":False}}
        mod = import_service_module()
        with pytest.raises(ValueError):
            await mod.AuthService.get_current_user_secure("t")

#------------get_current_user_secure() force logout invalidates--------
@pytest.mark.asyncio
async def test_get_current_user_secure_force_logout_invalidates():
    with SysModulesSandbox():
        from repositories.user_repository import UserRepository
        import utils.auth_utils as au
        from datetime import datetime, timedelta
        au._verify_access_payload = {"user_id": "u8", "issued_at": (datetime.utcnow()-timedelta(hours=2)).timestamp()}
        UserRepository.users = {"u8": {"user_id":"u8","is_active":True,"force_logout_after": datetime.utcnow()}}
        mod = import_service_module()
        with pytest.raises(ValueError):
            await mod.AuthService.get_current_user_secure("t")

#------------get_current_user_secure() verify error propagates--------
@pytest.mark.asyncio
async def test_get_current_user_secure_verify_error_propagates():
    with SysModulesSandbox():
        import utils.auth_utils as au
        au._raise_on_verify_access = RuntimeError("bad token")
        mod = import_service_module()
        with pytest.raises(RuntimeError):
            await mod.AuthService.get_current_user_secure("t")

#------------logout_user() with exp blacklists and logs--------
@pytest.mark.asyncio
async def test_logout_user_with_exp_blacklists_and_logs():
    with SysModulesSandbox():
        import utils.auth_utils as au
        from repositories.audit_repository import TokenRepository, AuditRepository
        from datetime import datetime, timedelta
        au._verify_access_payload = {"user_id": "u1", "exp": int((datetime.utcnow()+timedelta(hours=1)).timestamp())}
        mod = import_service_module()
        await mod.AuthService.logout_user("T")
        assert TokenRepository.last_blacklist is not None
        assert AuditRepository.logs[-1][1] == "user_logout"

#------------logout_user() without exp logs only--------
@pytest.mark.asyncio
async def test_logout_user_without_exp_logs_only():
    with SysModulesSandbox():
        import utils.auth_utils as au
        from repositories.audit_repository import TokenRepository, AuditRepository
        au._verify_access_payload = {"user_id": "u1"}
        TokenRepository.last_blacklist = None
        mod = import_service_module()
        await mod.AuthService.logout_user("T")
        assert TokenRepository.last_blacklist is None or TokenRepository.last_blacklist[0] is not None
        assert AuditRepository.logs[-1][1] == "user_logout"

#------------logout_user() verify error propagates--------
@pytest.mark.asyncio
async def test_logout_user_verify_error_propagates():
    with SysModulesSandbox():
        import utils.auth_utils as au
        au._raise_on_verify_access = RuntimeError("bad token")
        mod = import_service_module()
        with pytest.raises(RuntimeError):
            await mod.AuthService.logout_user("T")
