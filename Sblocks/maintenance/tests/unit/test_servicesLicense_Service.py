import sys
import os
import types
from datetime import datetime, date, timedelta
import importlib
import pytest

HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..")),
    os.path.abspath(os.path.join(HERE, "..")),
    os.getcwd(),
]
for p in CANDIDATES:
    if p not in sys.path:
        sys.path.insert(0, p)

if "schemas" not in sys.modules:
    sys.modules["schemas"] = types.ModuleType("schemas")
if "schemas.entities" not in sys.modules:
    ents = types.ModuleType("schemas.entities")
    class LicenseRecord: ...
    class LicenseType: ...
    ents.LicenseRecord = LicenseRecord
    ents.LicenseType = LicenseType
    sys.modules["schemas.entities"] = ents
else:
    se = sys.modules["schemas.entities"]
    if not hasattr(se, "LicenseRecord"):
        class LicenseRecord: ...
        se.LicenseRecord = LicenseRecord
    if not hasattr(se, "LicenseType"):
        class LicenseType: ...
        se.LicenseType = LicenseType

if "repositories" not in sys.modules:
    sys.modules["repositories"] = types.ModuleType("repositories")

class _RepoStub:
    def __init__(self):
        self.created = []
        self.updated = []
        self.deleted = []
        self.find_calls = []
        self.count_calls = []
        self.count_queue = []  
    async def create(self, data):
        self.created.append(data)
        return {"id": f"lic{len(self.created)}", **data}
    async def get_by_id(self, rid):
        return {"id": rid, "stub": True} if rid == "found" else None
    async def update(self, rid, data):
        self.updated.append((rid, data))
        return {"id": rid, **data} if rid != "missing" else None
    async def delete(self, rid):
        self.deleted.append(rid)
        return rid != "missing"
    async def get_by_entity(self, eid, etype):
        return [{"id": "e1", "entity_id": eid, "entity_type": etype}]
    async def get_expiring_soon(self, days):
        return [{"id": "ex1", "days": days}]
    async def get_expired_licenses(self):
        return [{"id": "expired"}]
    async def get_by_license_type(self, lt):
        return [{"id": "t1", "license_type": lt}]
    async def find(self, query=None, skip=0, limit=100, sort=None):
        self.find_calls.append((query, skip, limit, sort))
        return [{"id": "f1", "query": query, "skip": skip, "limit": limit, "sort": sort}]
    async def count(self, query=None):
        self.count_calls.append(query)
        if self.count_queue:
            return self.count_queue.pop(0)
        return 0

try:
    ls_mod = importlib.import_module("services.license_service")
except Exception:
    ls_mod = importlib.import_module("license_service")

ls_mod.LicenseRecordsRepository = _RepoStub
LicenseService = ls_mod.LicenseService

def make_service():
    return LicenseService()

# -------------------- create_license_record --------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("missing", [
    "entity_id","entity_type","license_type","license_number","title","issue_date","expiry_date","issuing_authority"
])
async def test_create_missing_required_field_raises(missing):
    svc = make_service()
    data = {
        "entity_id":"V1","entity_type":"vehicle","license_type":"roadworthy","license_number":"ABC",
        "title":"Roadworthy","issue_date":"2025-01-01","expiry_date":"2026-01-01","issuing_authority":"Dept"
    }
    data.pop(missing)
    with pytest.raises(ValueError):
        await svc.create_license_record(data)

@pytest.mark.asyncio
async def test_create_invalid_entity_type_raises():
    svc = make_service()
    data = {
        "entity_id":"X","entity_type":"fleet","license_type":"roadworthy","license_number":"L1",
        "title":"T","issue_date":"2025-01-01","expiry_date":"2026-01-01","issuing_authority":"Dept"
    }
    with pytest.raises(ValueError):
        await svc.create_license_record(data)

@pytest.mark.asyncio
async def test_create_parses_dates_and_sets_defaults():
    svc = make_service()
    out = await svc.create_license_record({
        "entity_id":"V1","entity_type":"vehicle","license_type":"roadworthy","license_number":"L1",
        "title":"T","issue_date":"2025-01-01","expiry_date":"2026-01-01","renewal_date":"2025-06-01",
        "issuing_authority":"Dept"
    })
    assert isinstance(out["issue_date"], date)
    assert isinstance(out["expiry_date"], date)
    assert isinstance(out["renewal_date"], date)
    assert out["is_active"] is True
    assert out["advance_notice_days"] == 30
    assert isinstance(out["created_at"], datetime)

@pytest.mark.asyncio
async def test_create_preserves_explicit_defaults():
    svc = make_service()
    out = await svc.create_license_record({
        "entity_id":"D1","entity_type":"driver","license_type":"permit","license_number":"P1",
        "title":"Permit","issue_date":"2025-01-01","expiry_date":"2026-01-01",
        "issuing_authority":"Dept","is_active":False,"advance_notice_days":10,"created_at":datetime(2030,1,1)
    })
    assert out["is_active"] is False
    assert out["advance_notice_days"] == 10
    assert out["created_at"] == datetime(2030,1,1)

@pytest.mark.asyncio
async def test_create_propagates_repo_error(monkeypatch):
    svc = make_service()
    async def boom(data): raise RuntimeError("fail")
    monkeypatch.setattr(svc.repository, "create", boom)
    with pytest.raises(RuntimeError):
        await svc.create_license_record({
            "entity_id":"V1","entity_type":"vehicle","license_type":"roadworthy","license_number":"L1",
            "title":"T","issue_date":"2025-01-01","expiry_date":"2026-01-01","issuing_authority":"Dept"
        })

# -------------------- get_license_record --------------------

@pytest.mark.asyncio
async def test_get_license_record_found_none_and_error(monkeypatch):
    svc = make_service()
    rec = await svc.get_license_record("found")
    assert rec and rec["id"] == "found"
    rec2 = await svc.get_license_record("missing")
    assert rec2 is None
    async def boom(_): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "get_by_id", boom)
    with pytest.raises(RuntimeError):
        await svc.get_license_record("any")

# -------------------- update_license_record --------------------

@pytest.mark.asyncio
async def test_update_parses_dates_and_returns_record(monkeypatch):
    svc = make_service()
    rec = await svc.update_license_record("rec1", {
        "issue_date":"2025-01-01","expiry_date":"2026-01-01","renewal_date":"2025-06-01","title":"New"
    })
    assert rec["id"] == "rec1"
    assert isinstance(rec["issue_date"], date)
    assert isinstance(rec["expiry_date"], date)
    assert isinstance(rec["renewal_date"], date)

@pytest.mark.asyncio
async def test_update_not_found_and_error(monkeypatch):
    svc = make_service()
    out = await svc.update_license_record("missing", {"title":"X"})
    assert out is None
    async def boom(rid, data): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "update", boom)
    with pytest.raises(RuntimeError):
        await svc.update_license_record("rec2", {"title":"Y"})

# -------------------- delete --------------------

@pytest.mark.asyncio
async def test_delete_true_false_and_error(monkeypatch):
    svc = make_service()
    assert await svc.delete_license_record("rec1") is True
    assert await svc.delete_license_record("missing") is False
    async def boom(_): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "delete", boom)
    with pytest.raises(RuntimeError):
        await svc.delete_license_record("rec2")

# -------------------- entity, expiring, expired, by_type --------------------

@pytest.mark.asyncio
async def test_get_entity_licenses_valid_and_invalid():
    svc = make_service()
    out = await svc.get_entity_licenses("V1", "vehicle")
    assert out and out[0]["entity_type"] == "vehicle"
    with pytest.raises(ValueError):
        await svc.get_entity_licenses("V1", "fleet")

@pytest.mark.asyncio
async def test_get_expiring_licenses_success_and_error(monkeypatch):
    svc = make_service()
    out = await svc.get_expiring_licenses(15)
    assert out and out[0]["days"] == 15
    async def boom(_): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "get_expiring_soon", boom)
    with pytest.raises(RuntimeError):
        await svc.get_expiring_licenses(5)

@pytest.mark.asyncio
async def test_get_expired_licenses_success_and_error(monkeypatch):
    svc = make_service()
    out = await svc.get_expired_licenses()
    assert out and out[0]["id"] == "expired"
    async def boom(): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "get_expired_licenses", boom)
    with pytest.raises(RuntimeError):
        await svc.get_expired_licenses()

@pytest.mark.asyncio
async def test_get_licenses_by_type_success_and_error(monkeypatch):
    svc = make_service()
    out = await svc.get_licenses_by_type("roadworthy")
    assert out and out[0]["license_type"] == "roadworthy"
    async def boom(_): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "get_by_license_type", boom)
    with pytest.raises(RuntimeError):
        await svc.get_licenses_by_type("x")

# -------------------- get_all_licenses --------------------

@pytest.mark.asyncio
async def test_get_all_licenses_calls_find_and_error(monkeypatch):
    svc = make_service()
    out = await svc.get_all_licenses(skip=5, limit=7)
    assert out and out[0]["skip"] == 5 and out[0]["limit"] == 7
    q, s, l, sort = svc.repository.find_calls[-1]
    assert q == {"is_active": True}
    assert sort == [("expiry_date", 1)]
    async def boom(query, skip, limit, sort): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "find", boom)
    with pytest.raises(RuntimeError):
        await svc.get_all_licenses()

# -------------------- renew_license --------------------

@pytest.mark.asyncio
async def test_renew_license_with_and_without_cost_and_not_found_and_error(monkeypatch):
    svc = make_service()
    out = await svc.renew_license("rec1", "2030-12-31", renewal_cost=123.45)
    assert out["id"] == "rec1" and out["renewal_cost"] == 123.45
    assert out["expiry_date"] == date(2030,12,31)
    assert out["renewal_date"] == date.today()
    out2 = await svc.renew_license("missing", "2031-01-01")
    assert out2 is None
    async def boom(rid, data): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "update", boom)
    with pytest.raises(RuntimeError):
        await svc.renew_license("rec2", "2031-02-01")

# -------------------- deactivate_license --------------------

@pytest.mark.asyncio
async def test_deactivate_license_found_not_found_and_error(monkeypatch):
    svc = make_service()
    out = await svc.deactivate_license("rec1")
    assert out["id"] == "rec1" and out["is_active"] is False
    out2 = await svc.deactivate_license("missing")
    assert out2 is None
    async def boom(rid, data): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "update", boom)
    with pytest.raises(RuntimeError):
        await svc.deactivate_license("rec3")

# -------------------- search_licenses --------------------

@pytest.mark.asyncio
async def test_search_licenses_build_query_and_sort_asc_desc(monkeypatch):
    svc = make_service()
    q = {
        "entity_id":"V1","entity_type":"vehicle","license_type":"roadworthy","is_active":True,
        "expiring_within_days": 10
    }
    out = await svc.search_licenses(q, skip=2, limit=3, sort_by="license_number", sort_order="asc")
    q1, s1, l1, sort1 = svc.repository.find_calls[-1]
    assert q1["entity_id"] == "V1" and q1["entity_type"] == "vehicle"
    assert q1["license_type"] == "roadworthy" and q1["is_active"] is True
    assert "$lte" in q1["expiry_date"]
    assert s1 == 2 and l1 == 3 and sort1 == [("license_number", 1)]
    out2 = await svc.search_licenses({"entity_id":"D1"}, sort_by="expiry_date", sort_order="desc")
    q2, s2, l2, sort2 = svc.repository.find_calls[-1]
    assert q2 == {"entity_id":"D1"}
    assert sort2 == [("expiry_date", -1)]

@pytest.mark.asyncio
async def test_search_licenses_error_propagates(monkeypatch):
    svc = make_service()
    async def boom(query, skip, limit, sort): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "find", boom)
    with pytest.raises(RuntimeError):
        await svc.search_licenses({"entity_id":"V1"})

# -------------------- get_total_count --------------------

@pytest.mark.asyncio
async def test_get_total_count_builds_query_and_error(monkeypatch):
    svc = make_service()
    q = {"entity_type":"driver","expiring_within_days":5,"is_active":True}
    cnt = await svc.get_total_count(q)
    assert isinstance(cnt, int)
    built = svc.repository.count_calls[-1]
    assert built["entity_type"] == "driver" and built["is_active"] is True
    assert "$lte" in built["expiry_date"]
    async def boom(query): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "count", boom)
    with pytest.raises(RuntimeError):
        await svc.get_total_count({"entity_id":"X"})

# -------------------- get_license_summary --------------------

@pytest.mark.asyncio
async def test_get_license_summary_sequence_and_error(monkeypatch):
    svc = make_service()
    svc.repository.count_queue = [10, 7, 3, 2]  
    out = await svc.get_license_summary(entity_id="V1", entity_type="vehicle")
    assert out == {
        "total_licenses": 10,
        "active_licenses": 7,
        "inactive_licenses": 3,
        "expiring_soon": 3,
        "expired": 2
    }
    async def boom(query): raise RuntimeError("x")
    monkeypatch.setattr(svc.repository, "count", boom)
    with pytest.raises(RuntimeError):
        await svc.get_license_summary()
