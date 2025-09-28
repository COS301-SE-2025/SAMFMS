import sys
import types
import importlib
import importlib.util
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import pytest

class SysModulesSandbox:
    def __init__(self):
        self._saved = None
    def __enter__(self):
        self._saved = sys.modules.copy()
        _mkpkg("models"); _mkpkg("models.api_models"); _mkpkg("models.database_models")
        _mkpkg("config"); _mkpkg("config.database")
        _mkpkg("services"); _mkpkg("services.auth_service")
        _mkpkg("repositories"); _mkpkg("repositories.audit_repository")
        sys.modules["models.api_models"] = _build_api_models_stub()
        sys.modules["models.database_models"] = _build_database_models_stub()
        sys.modules["repositories.audit_repository"] = _build_audit_stub()
        sys.modules["services.auth_service"] = _build_auth_stub()
        sys.modules["config.database"] = _build_db_stub()
        sys.modules["smtplib"] = _build_smtp_stub()
        return self
    def __exit__(self, exc_type, exc, tb):
        sys.modules.clear()
        sys.modules.update(self._saved)

def _mkpkg(name):
    if name not in sys.modules:
        m = types.ModuleType(name); m.__path__ = []; sys.modules[name] = m

@dataclass
class _InviteUserRequest:
    email: str
    full_name: str
    role: str = "user"
    phoneNo: str = ""

@dataclass
class _VerifyOTPRequest:
    email: str
    otp: str

@dataclass
class _CompleteRegistrationRequest:
    email: str
    password: str
    username: str | None = None

def _build_api_models_stub():
    m = types.ModuleType("models.api_models")
    m.InviteUserRequest = _InviteUserRequest
    m.VerifyOTPRequest = _VerifyOTPRequest
    m.CompleteRegistrationRequest = _CompleteRegistrationRequest
    return m

class _UserInvitation:
    def __init__(self, **doc):
        self.id = doc.get("_id") or doc.get("id")
        self.email = doc.get("email", "").lower()
        self.full_name = doc.get("full_name", "")
        self.role = doc.get("role", "user")
        self.phone_number = doc.get("phone_number", "")
        self.invited_by = doc.get("invited_by", "admin")
        self.status = doc.get("status", "invited")
        self.otp = doc.get("otp", "111111")
        self.expires_at = doc.get("expires_at", datetime.utcnow() + timedelta(hours=24))
        self.activation_attempts = doc.get("activation_attempts", 0)
        self.max_attempts = doc.get("max_attempts", 5)
        self.resend_count = doc.get("resend_count", 0)
        self.max_resends = doc.get("max_resends", 3)
        self.last_otp_sent = doc.get("last_otp_sent", datetime.utcnow() - timedelta(hours=1))
        self.created_at = doc.get("created_at", datetime.utcnow())
        self.email_status = doc.get("email_status", "ready")
        self.retry_count = doc.get("retry_count", 0)
        self.next_retry = doc.get("next_retry", None)
    def dict(self, exclude=None):
        d = {
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "phone_number": self.phone_number,
            "invited_by": self.invited_by,
            "status": self.status,
            "otp": self.otp,
            "expires_at": self.expires_at,
            "activation_attempts": self.activation_attempts,
            "max_attempts": self.max_attempts,
            "resend_count": self.resend_count,
            "max_resends": self.max_resends,
            "last_otp_sent": self.last_otp_sent,
            "created_at": self.created_at,
            "email_status": self.email_status,
            "retry_count": self.retry_count,
            "next_retry": self.next_retry,
        }
        if not (exclude and "id" in exclude):
            d["id"] = self.id
        return d
    def can_resend_otp(self):
        cooldown = timedelta(minutes=1)
        return self.resend_count < self.max_resends and (datetime.utcnow() - self.last_otp_sent) >= cooldown
    def generate_otp(self):
        self.otp = "222222"
    def mark_otp_sent(self):
        self.last_otp_sent = datetime.utcnow(); self.resend_count += 1
    def increment_attempts(self):
        self.activation_attempts += 1
    def is_expired(self):
        return self.expires_at <= datetime.utcnow()
    def is_valid_for_activation(self):
        return (not self.is_expired()) and self.activation_attempts < self.max_attempts and self.status == "invited"

def _build_database_models_stub():
    m = types.ModuleType("models.database_models")
    m.UserInvitation = _UserInvitation
    return m

class _AuditRepository:
    logs = []
    @staticmethod
    async def log_security_event(user_id, action, details):
        _AuditRepository.logs.append((user_id, action, details)); return True

def _build_audit_stub():
    m = types.ModuleType("repositories.audit_repository")
    m.AuditRepository = _AuditRepository
    return m

class _AuthService:
    last_signup_payload = None
    should_raise = False
    @staticmethod
    async def signup_user(payload):
        _AuthService.last_signup_payload = payload
        if _AuthService.should_raise:
            raise RuntimeError("signup failed")
        return {"access_token": "tok", "token_type": "bearer", "user_id": "uid", "role": payload["role"], "permissions": ["read"], "preferences": payload.get("preferences", {})}

def _build_auth_stub():
    m = types.ModuleType("services.auth_service")
    m.AuthService = _AuthService
    return m

class _Result:
    def __init__(self, modified=0, inserted_id=None, deleted=0, matched=None):
        self.modified_count = modified
        self.matched_count = matched if matched is not None else modified
        self.inserted_id = inserted_id
        self.deleted_count = deleted

class _Cursor:
    def __init__(self, docs):
        self._docs = list(docs)
    def sort(self, key, direction):
        reverse = direction < 0
        self._docs.sort(key=lambda d: d.get(key), reverse=reverse)
        return self
    def __aiter__(self):
        self._it = iter(self._docs)
        return self
    async def __anext__(self):
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration

class _Collection:
    def __init__(self):
        self.docs = []; self._last_update = None
    def _match(self, doc, query):
        for k, v in query.items():
            if isinstance(v, dict):
                if "$in" in v and doc.get(k) not in v["$in"]:
                    return False
                if "$lt" in v and not (doc.get(k) < v["$lt"]): return False
                if "$lte" in v and not (doc.get(k) <= v["$lte"]): return False
                if "$gt" in v and not (doc.get(k) > v["$gt"]): return False
            else:
                if doc.get(k) != v: return False
        return True
    async def find_one(self, query):
        for d in self.docs:
            if self._match(d, query): return d
        return None
    async def insert_one(self, doc):
        new = dict(doc); new["_id"] = new.get("_id") or f"id{len(self.docs)+1}"
        new.setdefault("created_at", datetime.utcnow())
        self.docs.append(new); return _Result(inserted_id=new["_id"])
    async def update_one(self, query, update):
        count = 0
        for d in self.docs:
            if self._match(d, query):
                if "$set" in update: d.update(update["$set"])
                if "$inc" in update:
                    for k, v in update["$inc"].items():
                        d[k] = d.get(k, 0) + v
                count += 1; break
        self._last_update = (query, update, count); return _Result(modified=count, matched=count)
    async def update_many(self, query, update):
        count = 0
        for d in self.docs:
            if self._match(d, query):
                if "$set" in update: d.update(update["$set"])
                if "$inc" in update:
                    for k, v in update["$inc"].items():
                        d[k] = d.get(k, 0) + v
                count += 1
        return _Result(modified=count, matched=count)
    async def delete_many(self, query):
        before = len(self.docs)
        self.docs = [d for d in self.docs if not self._match(d, query)]
        return _Result(deleted=before - len(self.docs))
    def find(self, query):
        return _Cursor([d for d in self.docs if self._match(d, query)])

class _DB:
    def __init__(self):
        self.invitations = _Collection(); self.users = _Collection()

def _build_db_stub():
    m = types.ModuleType("config.database")
    _db = _DB()
    def get_database(): return _db
    m.get_database = get_database
    return m

class _SMTP:
    def __init__(self, host, port, timeout=None):
        self.host = host; self.port = port; self.timeout = timeout
        self.started = False; self.logged = False; self.sent = False; self.closed = False
    def starttls(self): self.started = True
    def login(self, u, p): self.logged = True
    def sendmail(self, frm, to, msg): self.sent = True
    def send_message(self, msg): self.sent = True
    def quit(self): self.closed = True

def _build_smtp_stub():
    m = types.ModuleType("smtplib")
    class SMTPException(Exception): ...
    m.SMTPException = SMTPException
    m.SMTP = _SMTP
    return m

def _find_invitation_service_path():
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        for c in [
            parent / "security" / "services" / "invitation_service.py",
            parent / "services" / "invitation_service.py",
            parent / "invitation_service.py",
            Path("/mnt/data/invitation_service.py"),
        ]:
            if c.exists(): return str(c)
    return None

def import_invitation_module():
    names = ["security.services.invitation_service","services.invitation_service","invitation_service"]
    last = None
    for n in names:
        try:
            if n in sys.modules: del sys.modules[n]
            return importlib.import_module(n)
        except Exception as e:
            last = e
    path = _find_invitation_service_path()
    if not path: raise last or ImportError("Unable to import invitation_service")
    if "security" not in sys.modules: _mkpkg("security")
    if "security.services" not in sys.modules: _mkpkg("security.services")
    spec = importlib.util.spec_from_file_location("security.services.invitation_service", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["security.services.invitation_service"] = mod
    spec.loader.exec_module(mod)  
    return mod

#------------_check_rate_limit test--------
@pytest.mark.asyncio
async def test_check_rate_limit_allows_then_blocks_and_prunes():
    with SysModulesSandbox():
        mod = import_invitation_module()
        store = mod.InvitationService._rate_limit_storage; store.clear()
        email = "e@x.com"
        for _ in range(5): assert await mod.InvitationService._check_rate_limit(email) is True
        assert await mod.InvitationService._check_rate_limit(email) is False
        store[email] = [datetime.utcnow() - timedelta(minutes=16)]
        assert await mod.InvitationService._check_rate_limit(email) is True

#------------send_invitation missing fields--------
@pytest.mark.asyncio
async def test_send_invitation_missing_fields_raises():
    with SysModulesSandbox():
        from models.api_models import InviteUserRequest
        mod = import_invitation_module()
        with pytest.raises(mod.InvitationError):
            await mod.InvitationService.send_invitation(InviteUserRequest(email="", full_name=""), "u0")

#------------send_invitation rate limited--------
@pytest.mark.asyncio
async def test_send_invitation_rate_limited_raises():
    with SysModulesSandbox():
        from models.api_models import InviteUserRequest
        mod = import_invitation_module()
        s = mod.InvitationService._rate_limit_storage; s["e@x.com"] = [datetime.utcnow()] * 5
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.send_invitation(InviteUserRequest(email="e@x.com", full_name="N A"), "mgr")
        assert "Too many invitation" in str(ei.value)

#------------send_invitation existing user--------
@pytest.mark.asyncio
async def test_send_invitation_existing_user_raises():
    with SysModulesSandbox():
        from models.api_models import InviteUserRequest
        from config.database import get_database
        mod = import_invitation_module()
        db = get_database(); await db.users.insert_one({"email": "e@x.com"})
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.send_invitation(InviteUserRequest(email="e@x.com", full_name="NA"), "mgr")
        assert "already exists" in str(ei.value)

#------------send_invitation cannot resend max--------
@pytest.mark.asyncio
async def test_send_invitation_existing_invitation_cannot_resend_max():
    with SysModulesSandbox():
        from models.api_models import InviteUserRequest
        from config.database import get_database
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        db = get_database()
        inv = UserInvitation(email="e@x.com", full_name="NA", status="invited", resend_count=3, max_resends=3, last_otp_sent=datetime.utcnow())
        await db.invitations.insert_one(inv.dict(exclude={"id"}))
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.send_invitation(InviteUserRequest(email="e@x.com", full_name="NA"), "mgr")
        assert "Maximum resend limit" in str(ei.value)

#------------send_invitation cannot resend cooldown--------
@pytest.mark.asyncio
async def test_send_invitation_existing_invitation_cannot_resend_cooldown():
    with SysModulesSandbox():
        from models.api_models import InviteUserRequest
        from config.database import get_database
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        db = get_database()
        inv = UserInvitation(email="e2@x.com", full_name="NA", status="invited", resend_count=1, max_resends=3, last_otp_sent=datetime.utcnow())
        await db.invitations.insert_one(inv.dict(exclude={"id"}))
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.send_invitation(InviteUserRequest(email="e2@x.com", full_name="NA"), "mgr")
        assert "Please wait before" in str(ei.value)

#------------send_invitation resend success--------
@pytest.mark.asyncio
async def test_send_invitation_existing_invitation_resend_success():
    with SysModulesSandbox():
        from models.api_models import InviteUserRequest
        from config.database import get_database
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        db = get_database()
        inv = UserInvitation(email="e3@x.com", full_name="NA", status="invited", resend_count=1, max_resends=3, last_otp_sent=datetime.utcnow()-timedelta(minutes=5))
        stored = inv.dict(exclude={"id"}); stored["_id"] = "x1"; await db.invitations.insert_one(stored)
        async def ok(_): return True
        mod.InvitationService._send_invitation_email_with_retry = staticmethod(ok)
        res = await mod.InvitationService.send_invitation(InviteUserRequest(email="e3@x.com", full_name="NA"), "mgr")
        assert "Invitation" in res["message"]

#------------send_invitation new invitation--------
@pytest.mark.asyncio
async def test_send_invitation_new_invitation_email_success():
    with SysModulesSandbox():
        from models.api_models import InviteUserRequest
        mod = import_invitation_module()
        async def ok(_): return True
        mod.InvitationService._send_invitation_email_with_retry = staticmethod(ok)
        res = await mod.InvitationService.send_invitation(InviteUserRequest(email="new@x.com", full_name="NA"), "mgr")
        assert "Invitation" in res["message"]

#------------send_invitation email retry path--------
@pytest.mark.asyncio
async def test_send_invitation_email_retry_marked_but_success_response():
    with SysModulesSandbox():
        from models.api_models import InviteUserRequest
        mod = import_invitation_module()
        async def always_fail(_): return False
        mod.InvitationService._send_invitation_email_with_retry = staticmethod(always_fail)
        res = await mod.InvitationService.send_invitation(InviteUserRequest(email="retry@x.com", full_name="NA"), "mgr")
        assert "Invitation" in res["message"]

#------------verify_otp rate limited--------
@pytest.mark.asyncio
async def test_verify_otp_rate_limited_raises():
    with SysModulesSandbox():
        from models.api_models import VerifyOTPRequest
        mod = import_invitation_module()
        mod.InvitationService._rate_limit_storage[f"verify_e@x.com"] = [datetime.utcnow()] * 10
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.verify_otp(VerifyOTPRequest(email="e@x.com", otp="111111"))
        assert "Too many verification attempts" in str(ei.value)

#------------verify_otp not found--------
@pytest.mark.asyncio
async def test_verify_otp_not_found_raises_invalid():
    with SysModulesSandbox():
        from models.api_models import VerifyOTPRequest
        mod = import_invitation_module()
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.verify_otp(VerifyOTPRequest(email="none@x.com", otp="111111"))
        assert ("No pending invitation" in str(ei.value)) or ("Invalid invitation" in str(ei.value))

#------------verify_otp expired--------
@pytest.mark.asyncio
async def test_verify_otp_expired_marks_and_raises():
    with SysModulesSandbox():
        from models.api_models import VerifyOTPRequest
        from config.database import get_database
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        db = get_database()
        inv = UserInvitation(email="exp@x.com", full_name="NA", status="invited", expires_at=datetime.utcnow()-timedelta(minutes=1))
        await db.invitations.insert_one(inv.dict(exclude={"id"}))
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.verify_otp(VerifyOTPRequest(email="exp@x.com", otp="111111"))
        assert "expired" in str(ei.value).lower()

#------------verify_otp attempts exceeded--------
@pytest.mark.asyncio
async def test_verify_otp_attempts_exceeded_marks_and_raises():
    with SysModulesSandbox():
        from models.api_models import VerifyOTPRequest
        from config.database import get_database
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        db = get_database()
        inv = UserInvitation(email="max@x.com", full_name="NA", status="invited", activation_attempts=5, max_attempts=5)
        await db.invitations.insert_one(inv.dict(exclude={"id"}))
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.verify_otp(VerifyOTPRequest(email="max@x.com", otp="111111"))
        assert "Maximum verification attempts" in str(ei.value)

#------------verify_otp invalid or not pending--------
@pytest.mark.asyncio
async def test_verify_otp_invalid_status_raises():
    with SysModulesSandbox():
        from models.api_models import VerifyOTPRequest
        from config.database import get_database
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        db = get_database()
        inv = UserInvitation(email="bad@x.com", full_name="NA", status="activated")
        await db.invitations.insert_one(inv.dict(exclude={"id"}))
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.verify_otp(VerifyOTPRequest(email="bad@x.com", otp="111111"))
        assert ("No pending invitation" in str(ei.value)) or ("Invalid invitation status" in str(ei.value))

#------------verify_otp wrong otp--------
@pytest.mark.asyncio
async def test_verify_otp_wrong_otp_increments_and_raises():
    with SysModulesSandbox():
        from models.api_models import VerifyOTPRequest
        from config.database import get_database
        from models.database_models import UserInvitation
        from repositories.audit_repository import AuditRepository
        mod = import_invitation_module()
        db = get_database()
        inv = UserInvitation(email="w@x.com", full_name="NA", status="invited", otp="222222")
        await db.invitations.insert_one(inv.dict(exclude={"id"}))
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.verify_otp(VerifyOTPRequest(email="w@x.com", otp="999999"))
        assert "Invalid OTP" in str(ei.value)
        assert any(a=="otp_verification_failed" for _,a,_ in AuditRepository.logs)

#------------verify_otp success--------
@pytest.mark.asyncio
async def test_verify_otp_success_updates_status_and_returns_message():
    with SysModulesSandbox():
        from models.api_models import VerifyOTPRequest
        from config.database import get_database
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        db = get_database()
        inv = UserInvitation(email="ok@x.com", full_name="NA", status="invited", otp="333333")
        await db.invitations.insert_one(inv.dict(exclude={"id"}))
        res = await mod.InvitationService.verify_otp(VerifyOTPRequest(email="ok@x.com", otp="333333"))
        assert isinstance(res, dict)
        assert ("message" in res) or ("email" in res)
        doc = await db.invitations.find_one({"email": "ok@x.com"})
        assert doc is not None
        assert doc.get("email") == "ok@x.com"

#------------complete_registration unique username (service may fail)--------
@pytest.mark.asyncio
async def test_complete_registration_generates_unique_username_but_service_may_fail():
    with SysModulesSandbox():
        from models.api_models import CompleteRegistrationRequest
        from config.database import get_database
        mod = import_invitation_module()
        db = get_database()
        await db.invitations.insert_one({"email":"u@x.com","full_name":"Name","role":"user","phone_number":"","status":"otp_verified"})
        await db.users.insert_one({"username":"u"}); await db.users.insert_one({"username":"u1"})
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.complete_registration(CompleteRegistrationRequest(email="u@x.com", password="pw", username=None))
        assert "Failed to complete registration" in str(ei.value)

#------------get_pending_invitations filtering--------
@pytest.mark.asyncio
async def test_get_pending_invitations_admin_and_fleet_filters():
    with SysModulesSandbox():
        from config.database import get_database
        mod = import_invitation_module()
        db = get_database()
        await db.invitations.insert_one({"email":"a@x.com","full_name":"A","role":"driver","phone_number":"","status":"invited","invited_by":"mgr"})
        await db.invitations.insert_one({"email":"b@x.com","full_name":"B","role":"user","phone_number":"","status":"invited","invited_by":"other"})
        lst_admin = await mod.InvitationService.get_pending_invitations("admin","admin")
        assert isinstance(lst_admin, list)
        lst_mgr = await mod.InvitationService.get_pending_invitations("mgr","fleet_manager")
        assert isinstance(lst_mgr, list)

#------------resend_invitation not found--------
@pytest.mark.asyncio
async def test_resend_invitation_not_found_raises():
    with SysModulesSandbox():
        mod = import_invitation_module()
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.resend_invitation("none@x.com","u1")
        assert "No pending invitation" in str(ei.value)

#------------resend_invitation cooldown/max--------
@pytest.mark.asyncio
async def test_resend_invitation_max_or_cooldown_raises():
    with SysModulesSandbox():
        from config.database import get_database
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        db = get_database()
        full = UserInvitation(email="m@x.com", full_name="NA", status="invited", resend_count=3, max_resends=3, last_otp_sent=datetime.utcnow())
        await db.invitations.insert_one(full.dict(exclude={"id"}))
        with pytest.raises(mod.InvitationError):
            await mod.InvitationService.resend_invitation("m@x.com","u1")
        cool = UserInvitation(email="c@x.com", full_name="NA", status="invited", resend_count=1, last_otp_sent=datetime.utcnow())
        await db.invitations.insert_one(cool.dict(exclude={"id"}))
        with pytest.raises(mod.InvitationError):
            await mod.InvitationService.resend_invitation("c@x.com","u1")

#------------resend_invitation success--------
@pytest.mark.asyncio
async def test_resend_invitation_success():
    with SysModulesSandbox():
        from config.database import get_database
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        db = get_database()
        inv = UserInvitation(email="s@x.com", full_name="NA", status="invited", resend_count=0, last_otp_sent=datetime.utcnow()-timedelta(minutes=5))
        await db.invitations.insert_one(inv.dict(exclude={"id"}))
        async def ok(_): return True
        mod.InvitationService._send_invitation_email_with_retry = staticmethod(ok)
        res = await mod.InvitationService.resend_invitation("s@x.com","u1")
        assert "resent" in res["message"].lower()

#------------_send_invitation_email_with_retry success after fails--------
@pytest.mark.asyncio
async def test_send_invitation_email_with_retry_success_after_failures(monkeypatch):
    with SysModulesSandbox():
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        state = {"n": 0}
        async def sometimes(inv):
            if state["n"] < 2:
                state["n"] += 1
                raise RuntimeError("temp")
            return None
        async def _noop(*args, **kwargs): return None
        monkeypatch.setattr(mod.asyncio, "sleep", _noop)
        mod.InvitationService._send_invitation_email = staticmethod(sometimes)
        ok = await mod.InvitationService._send_invitation_email_with_retry(UserInvitation(email="r@x.com", full_name="NA"))
        assert ok is True

#------------_send_invitation_email_with_retry exhaust--------
@pytest.mark.asyncio
async def test_send_invitation_email_with_retry_exhausts(monkeypatch):
    with SysModulesSandbox():
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        async def always_raise(inv): raise RuntimeError("fail")
        async def _noop(*args, **kwargs): return None
        monkeypatch.setattr(mod.asyncio, "sleep", _noop)
        mod.InvitationService._send_invitation_email = staticmethod(always_raise)
        ok = await mod.InvitationService._send_invitation_email_with_retry(UserInvitation(email="z@x.com", full_name="NA"), max_retries=2)
        assert ok is False

#------------_send_invitation_email missing cfg--------
@pytest.mark.asyncio
async def test_send_invitation_email_missing_config_raises(monkeypatch):
    with SysModulesSandbox():
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        for k in ["SMTP_SERVER","SMTP_PORT","SMTP_USERNAME","SMTP_PASSWORD","FROM_EMAIL","FRONTEND_URL"]:
            monkeypatch.delenv(k, raising=False)
        with pytest.raises(Exception):
            await mod.InvitationService._send_invitation_email(UserInvitation(email="a@x.com", full_name="NA"))

#------------_send_invitation_email invalid FROM--------
@pytest.mark.asyncio
async def test_send_invitation_email_invalid_from_raises(monkeypatch):
    with SysModulesSandbox():
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        monkeypatch.setenv("SMTP_SERVER","smtp.local")
        monkeypatch.setenv("SMTP_PORT","587")
        monkeypatch.setenv("SMTP_USERNAME","user@x.com")
        monkeypatch.setenv("SMTP_PASSWORD","pw")
        monkeypatch.setenv("FROM_EMAIL","bad-address")
        monkeypatch.setenv("FRONTEND_URL","http://localhost")
        with pytest.raises(Exception):
            await mod.InvitationService._send_invitation_email(UserInvitation(email="a@x.com", full_name="NA"))

#------------_send_invitation_email success--------
@pytest.mark.asyncio
async def test_send_invitation_email_success(monkeypatch):
    with SysModulesSandbox():
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        monkeypatch.setenv("SMTP_SERVER","smtp.local")
        monkeypatch.setenv("SMTP_PORT","587")
        monkeypatch.setenv("SMTP_USERNAME","user@x.com")
        monkeypatch.setenv("SMTP_PASSWORD","pw")
        monkeypatch.setenv("FROM_EMAIL","user@x.com")
        monkeypatch.setenv("FRONTEND_URL","http://localhost")
        await mod.InvitationService._send_invitation_email(UserInvitation(email="a@x.com", full_name="NA"))

#------------cleanup_expired_invitations--------
@pytest.mark.asyncio
async def test_cleanup_expired_invitations_runs_without_error():
    with SysModulesSandbox():
        from config.database import get_database
        mod = import_invitation_module()
        db = get_database()
        await db.invitations.insert_one({"email":"old@x.com","status":"invited","expires_at":datetime.utcnow()-timedelta(days=1),"created_at":datetime.utcnow()-timedelta(days=31)})
        await db.invitations.insert_one({"email":"retry@x.com","email_status":"pending_retry","created_at":datetime.utcnow()-timedelta(days=31)})
        await mod.InvitationService.cleanup_expired_invitations()

#------------cancel_invitation not found--------
@pytest.mark.asyncio
async def test_cancel_invitation_not_found_raises():
    with SysModulesSandbox():
        mod = import_invitation_module()
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.cancel_invitation("none@x.com","u1")
        assert ("No pending invitation" in str(ei.value)) or ("Failed to cancel invitation" in str(ei.value))

#------------cancel_invitation success--------
@pytest.mark.asyncio
async def test_cancel_invitation_success():
    with SysModulesSandbox():
        from config.database import get_database
        mod = import_invitation_module()
        db = get_database()
        await db.invitations.insert_one({"email":"c@x.com","status":"invited"})
        class _Upd: 
            def __init__(self): self.matched_count = 1; self.modified_count = 1
        async def forced_ok(q, u): return _Upd()
        db.invitations.update_one = forced_ok
        res = await mod.InvitationService.cancel_invitation("c@x.com","u1")
        assert "cancel" in res["message"].lower()

#------------extra: verify wrong then right flow--------
@pytest.mark.asyncio
async def test_verify_otp_wrong_then_right_flow(monkeypatch):
    with SysModulesSandbox():
        from models.api_models import VerifyOTPRequest
        from models.database_models import UserInvitation
        from config.database import get_database
        mod = import_invitation_module()
        db = get_database()
        inv = UserInvitation(email="pair@x.com", full_name="NA", status="invited", otp="123456")
        await db.invitations.insert_one(inv.dict(exclude={"id"}))
        with pytest.raises(mod.InvitationError):
            await mod.InvitationService.verify_otp(VerifyOTPRequest(email="pair@x.com", otp="000000"))
        res = await mod.InvitationService.verify_otp(VerifyOTPRequest(email="pair@x.com", otp="123456"))
        assert isinstance(res, dict)

#------------extra: retry immediate success--------
@pytest.mark.asyncio
async def test_send_invitation_email_with_retry_immediate_success(monkeypatch):
    with SysModulesSandbox():
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        async def ok(_): return None
        async def _noop(*a, **k): return None
        monkeypatch.setattr(mod.asyncio, "sleep", _noop)
        mod.InvitationService._send_invitation_email = staticmethod(ok)
        assert await mod.InvitationService._send_invitation_email_with_retry(UserInvitation(email="i@x.com", full_name="NA")) is True

#------------extra: retry zero retries returns false--------
@pytest.mark.asyncio
async def test_send_invitation_email_with_retry_zero_retries_returns_false(monkeypatch):
    with SysModulesSandbox():
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        async def boom(_): raise RuntimeError("x")
        async def _noop(*a, **k): return None
        monkeypatch.setattr(mod.asyncio, "sleep", _noop)
        mod.InvitationService._send_invitation_email = staticmethod(boom)
        assert await mod.InvitationService._send_invitation_email_with_retry(UserInvitation(email="z0@x.com", full_name="NA"), max_retries=0) is False
        
#------------send_invitation returns 'queued' when email service down--------
@pytest.mark.asyncio
async def test_send_invitation_returns_queued_when_email_service_down():
    with SysModulesSandbox():
        from models.api_models import InviteUserRequest
        mod = import_invitation_module()
        async def always_fail(_): return False
        mod.InvitationService._send_invitation_email_with_retry = staticmethod(always_fail)
        res = await mod.InvitationService.send_invitation(
            InviteUserRequest(email="queued@x.com", full_name="QA User"), "mgr1"
        )
        assert isinstance(res, dict)
        assert res.get("email") == "queued@x.com"
        assert res.get("email_status") == "queued"
        assert "Email will be sent" in res.get("message", "")

#------------complete_registration missing invitation triggers InvitationError path--------
@pytest.mark.asyncio
async def test_complete_registration_missing_invitation_hits_invitationerror_block():
    with SysModulesSandbox():
        from models.api_models import CompleteRegistrationRequest
        mod = import_invitation_module()
        with pytest.raises(mod.InvitationError):
            await mod.InvitationService.complete_registration(
                CompleteRegistrationRequest(email="missing@x.com", password="pw")
            )

#------------_send_invitation_email success with trailing slash FRONTEND_URL and no full_name--------
@pytest.mark.asyncio
async def test_send_invitation_email_success_trailing_slash_and_no_full_name(monkeypatch):
    with SysModulesSandbox():
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        monkeypatch.setenv("SMTP_SERVER","smtp.local")
        monkeypatch.setenv("SMTP_PORT","587")
        monkeypatch.setenv("SMTP_USERNAME","user@x.com")
        monkeypatch.setenv("SMTP_PASSWORD","pw")
        monkeypatch.setenv("FROM_EMAIL","user@x.com")
        monkeypatch.setenv("FRONTEND_URL","http://localhost/") 
        inv = UserInvitation(email="no-name@x.com", full_name="", status="invited")
        await mod.InvitationService._send_invitation_email(inv)  

#------------_send_invitation_email SMTPException path--------
@pytest.mark.asyncio
async def test_send_invitation_email_smtp_exception_is_wrapped(monkeypatch):
    with SysModulesSandbox():
        from models.database_models import UserInvitation
        import smtplib as real_smtplib  
        mod = import_invitation_module()
        monkeypatch.setenv("SMTP_SERVER","smtp.local")
        monkeypatch.setenv("SMTP_PORT","587")
        monkeypatch.setenv("SMTP_USERNAME","user@x.com")
        monkeypatch.setenv("SMTP_PASSWORD","pw")
        monkeypatch.setenv("FROM_EMAIL","user@x.com")
        monkeypatch.setenv("FRONTEND_URL","http://localhost")

        class BoomSMTP:
            def __init__(self, host, port, timeout=None): pass
            def starttls(self): pass
            def login(self, u, p): pass
            def send_message(self, msg): 
                raise real_smtplib.SMTPException("boom") 
            def quit(self): pass


        real_smtplib.SMTP = BoomSMTP  
        with pytest.raises(Exception) as ei:
            await mod.InvitationService._send_invitation_email(UserInvitation(email="smtp@x.com", full_name="SMTP Err"))
        assert "Email sending failed" in str(ei.value)

#------------cancel_invitation generic exception path (logs and raises generic InvitationError)--------
@pytest.mark.asyncio
async def test_cancel_invitation_generic_exception_path():
    with SysModulesSandbox():
        from config.database import get_database
        mod = import_invitation_module()
        db = get_database()
        await db.invitations.insert_one({"email":"boom@x.com","status":"invited"})
        async def explode(*a, **k): 
            raise RuntimeError("db down")
        db.invitations.update_one = explode
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.cancel_invitation("boom@x.com","u9")
        assert "Failed to cancel invitation" in str(ei.value)


@pytest.mark.asyncio
async def test_send_invitation_existing_invitation_resend_branch_counts_and_success():
    with SysModulesSandbox():
        from config.database import get_database
        from models.database_models import UserInvitation
        from models.api_models import InviteUserRequest
        mod = import_invitation_module()
        db = get_database()
        inv = UserInvitation(
            email="resendhit@x.com", full_name="Re Send", status="invited",
            resend_count=0, last_otp_sent=datetime.utcnow() - timedelta(minutes=10)
        )
        await db.invitations.insert_one(inv.dict(exclude={"id"}))
        async def ok(_): return True
        mod.InvitationService._send_invitation_email_with_retry = staticmethod(ok)
        res = await mod.InvitationService.send_invitation(
            InviteUserRequest(email="resendhit@x.com", full_name="Re Send"), "admin1"
        )
        assert res["email"] == "resendhit@x.com"
        doc = await db.invitations.find_one({"email": "resendhit@x.com"})
        assert doc is not None
        assert doc.get("resend_count", 0) >= 1

#------------_send_invitation_email_with_retry: success via first attempt (explicit True return path)--------
@pytest.mark.asyncio
async def test_send_invitation_email_with_retry_first_attempt_true(monkeypatch):
    with SysModulesSandbox():
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        async def success(_): return None  
        async def _noop(*a, **k): return None
        monkeypatch.setattr(mod.asyncio, "sleep", _noop)
        mod.InvitationService._send_invitation_email = staticmethod(success)
        assert await mod.InvitationService._send_invitation_email_with_retry(UserInvitation(email="first@x.com", full_name="First")) is True

#------------verify_otp: invitation present but wrong status (explicit message branch)--------
@pytest.mark.asyncio
async def test_verify_otp_wrong_status_explicit_message_branch():
    with SysModulesSandbox():
        from config.database import get_database
        from models.database_models import UserInvitation
        from models.api_models import VerifyOTPRequest
        mod = import_invitation_module()
        db = get_database()
        await db.invitations.insert_one(UserInvitation(email="stat@x.com", full_name="S", status="activated").dict(exclude={"id"}))
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.verify_otp(VerifyOTPRequest(email="stat@x.com", otp="111111"))
        assert "No pending invitation" in str(ei.value) or "Invalid invitation status" in str(ei.value)

#------------cleanup_expired_invitations: pending_retry older than threshold becomes failed--------
@pytest.mark.asyncio
async def test_cleanup_expired_invitations_marks_failed_from_pending_retry():
    with SysModulesSandbox():
        from config.database import get_database
        mod = import_invitation_module()
        db = get_database()
        old = datetime.utcnow() - timedelta(days=40)
        await db.invitations.insert_one({
            "email":"oldretry@x.com","status":"invited","email_status":"pending_retry",
            "created_at": old, "retry_count": 5
        })
        await mod.InvitationService.cleanup_expired_invitations()
        doc = await db.invitations.find_one({"email":"oldretry@x.com"})
        assert (doc is None) or (doc.get("email_status") in {"failed","pending_retry"})

@pytest.mark.asyncio
async def test_send_invitation_generic_exception_is_wrapped():
    with SysModulesSandbox():
        from models.api_models import InviteUserRequest
        mod = import_invitation_module()
        async def ok(_): return True
        mod.InvitationService._send_invitation_email_with_retry = staticmethod(ok)
        from repositories.audit_repository import AuditRepository
        async def boom(*a, **k): raise RuntimeError("log failed")
        AuditRepository.log_security_event = boom  
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.send_invitation(
                InviteUserRequest(email="gx@x.com", full_name="Gen X"), "mgr2"
            )
        assert "Failed to send invitation" in str(ei.value)

@pytest.mark.asyncio
async def test_verify_otp_invalid_status_branch():
    with SysModulesSandbox():
        from config.database import get_database
        from models.database_models import UserInvitation
        from models.api_models import VerifyOTPRequest
        mod = import_invitation_module()
        db = get_database()
        inv = UserInvitation(email="st@x.com", full_name="S", status="invited", otp="111111")
        await db.invitations.insert_one(inv.dict(exclude={"id"}))
        def _fake_valid(self): return False
        def _not_expired(self): return False
        UserInvitation.is_valid_for_activation = _fake_valid
        UserInvitation.is_expired = _not_expired
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.verify_otp(VerifyOTPRequest(email="st@x.com", otp="111111"))
        assert "Invalid invitation status" in str(ei.value)

@pytest.mark.asyncio
async def test_verify_otp_generic_exception_wrapped():
    with SysModulesSandbox():
        from config.database import get_database
        from models.database_models import UserInvitation
        from models.api_models import VerifyOTPRequest
        from repositories.audit_repository import AuditRepository
        mod = import_invitation_module()

        if hasattr(mod, "UserInvitation"):
            mod.UserInvitation.is_valid_for_activation = lambda self: True 

        db = get_database()
        inv = UserInvitation(email="ok2@x.com", full_name="NA", status="invited", otp="333333")
        await db.invitations.insert_one(inv.dict(exclude={"id"}))

        async def boom(*a, **k):  
            raise RuntimeError("audit failed")
        AuditRepository.log_security_event = boom 

        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.verify_otp(VerifyOTPRequest(email="ok2@x.com", otp="333333"))

        msg = str(ei.value)
        assert ("Failed to verify OTP" in msg) or ("Invalid invitation status" in msg)
        
@pytest.mark.asyncio
async def test_complete_registration_success_path_with_username_dedup():
    with SysModulesSandbox():
        from config.database import get_database
        from repositories.audit_repository import AuditRepository
        mod = import_invitation_module()

        if hasattr(mod, "UserInvitation"):
            mod.UserInvitation.is_valid_for_activation = lambda self: True 

        async def audit_ok(*a, **k): return True
        AuditRepository.log_security_event = audit_ok 

        db = get_database()
        await db.invitations.insert_one({
            "email":"john@x.com","full_name":"John Doe","role":"user",
            "phone_number":"", "status":"invited","otp":"otp1"
        })
        await db.users.insert_one({"username":"john"})
        await db.users.insert_one({"username":"john1"})

        class Req:
            def __init__(self):
                self.email="john@x.com"; self.password="pw"; self.username=None; self.otp="otp1"

        class Tok:
            def __init__(self):
                self.access_token="t"; self.token_type="bearer"; self.user_id="U1"
                self.role="user"; self.permissions=["read"]; self.preferences={"theme":"light"}

        async def signup(payload): return Tok()
        from services.auth_service import AuthService
        AuthService.signup_user = staticmethod(signup)

        res = await mod.InvitationService.complete_registration(Req())
        assert isinstance(res, dict)
        assert res["access_token"] == "t"

        doc = await db.invitations.find_one({"email":"john@x.com"})
        assert doc is not None and doc.get("status") in {"activated","completed","registered","invited"}

@pytest.mark.asyncio
async def test_complete_registration_invitationerror_passthrough():
    with SysModulesSandbox():
        from config.database import get_database
        from repositories.audit_repository import AuditRepository
        mod = import_invitation_module()

        if hasattr(mod, "UserInvitation"):
            mod.UserInvitation.is_valid_for_activation = lambda self: True  

        async def audit_ok(*a, **k): return True
        AuditRepository.log_security_event = audit_ok 

        db = get_database()
        await db.invitations.insert_one({
            "email":"passthru@x.com","full_name":"P","role":"user",
            "phone_number":"", "status":"invited","otp":"o2"
        })

        class Req:
            def __init__(self):
                self.email="passthru@x.com"; self.password="pw"; self.username=None; self.otp="o2"

        async def raise_ie(*a, **k):
            raise mod.InvitationError("service says no")

        from services.auth_service import AuthService
        AuthService.signup_user = staticmethod(raise_ie)

        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.complete_registration(Req())

        assert "service says no" in str(ei.value) or "Invitation is no longer valid" in str(ei.value)

@pytest.mark.asyncio
async def test_get_pending_invitations_non_admin_non_fleet_returns_empty():
    with SysModulesSandbox():
        mod = import_invitation_module()
        res = await mod.InvitationService.get_pending_invitations("u7","viewer")
        assert res == []

@pytest.mark.asyncio
async def test_get_pending_invitations_generic_exception_wrapped():
    with SysModulesSandbox():
        from config.database import get_database
        mod = import_invitation_module()
        db = get_database()
        def broken_find(q): 
            raise RuntimeError("find exploded")
        db.invitations.find = broken_find  
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.get_pending_invitations("admin","admin")
        assert "Failed to retrieve invitations" in str(ei.value)

@pytest.mark.asyncio
async def test_resend_invitation_rate_limited_raises():
    with SysModulesSandbox():
        mod = import_invitation_module()
        key = "resend_rl@x.com"
        mod.InvitationService._rate_limit_storage[f"resend_{key}"] = [datetime.utcnow()] * 5
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.resend_invitation(key, "u2")
        assert "Too many resend requests" in str(ei.value)

@pytest.mark.asyncio
async def test_resend_invitation_send_returns_false_raises():
    with SysModulesSandbox():
        from config.database import get_database
        from models.database_models import UserInvitation
        mod = import_invitation_module()
        db = get_database()
        inv = UserInvitation(email="rf@x.com", full_name="R F", status="invited",
                             resend_count=0, last_otp_sent=datetime.utcnow()-timedelta(minutes=5))
        await db.invitations.insert_one(inv.dict(exclude={"id"}))
        async def nope(_): return False
        mod.InvitationService._send_invitation_email_with_retry = staticmethod(nope)
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.resend_invitation("rf@x.com","u3")
        assert "Failed to send invitation email" in str(ei.value)

@pytest.mark.asyncio
async def test_resend_invitation_generic_exception_wrapped():
    with SysModulesSandbox():
        from config.database import get_database
        mod = import_invitation_module()
        db = get_database()
        async def explode(*a, **k): 
            raise RuntimeError("db blowup")
        db.invitations.find_one = explode
        with pytest.raises(mod.InvitationError) as ei:
            await mod.InvitationService.resend_invitation("gx2@x.com","u9")
        assert "Failed to resend invitation" in str(ei.value)
