# test_servicesLicense_Service.py
# Small, isolated unit tests for services/license_service.py

import sys
import os
import types
from datetime import datetime, date, timedelta
import pytest

# ---------------------------
# Make project importable anywhere
# ---------------------------
HERE = os.path.abspath(os.path.dirname(__file__))
CANDIDATES = [
    os.path.abspath(os.path.join(HERE, "..", "..")),
    os.path.abspath(os.path.join(HERE, "..")),
    os.getcwd(),
]
for p in CANDIDATES:
    if p not in sys.path:
        sys.path.insert(0, p)

# ---------------------------
# Minimal stubs for imports used by license_service
# ---------------------------
# schemas.entities
if "schemas" not in sys.modules:
    schemas_pkg = types.ModuleType("schemas")
    sys.modules["schemas"] = schemas_pkg
else:
    schemas_pkg = sys.modules["schemas"]

if "schemas.entities" not in sys.modules:
    entities_mod = types.ModuleType("schemas.entities")
    class LicenseRecord: ...
    class LicenseType: ...
    entities_mod.LicenseRecord = LicenseRecord
    entities_mod.LicenseType = LicenseType
    setattr(schemas_pkg, "entities", entities_mod)
    sys.modules["schemas.entities"] = entities_mod

# repositories with LicenseRecordsRepository class
if "repositories" not in sys.modules:
    repos_mod = types.ModuleType("repositories")
    class LicenseRecordsRepository:
        def __init__(self): ...
    repos_mod.LicenseRecordsRepository = LicenseRecordsRepository
    sys.modules["repositories"] = repos_mod

# ---------------------------
# Import target module (force submodule, not the singleton re-export)
# ---------------------------
import importlib
try:
    ls_mod = importlib.import_module("services.license_service")
except Exception:
    ls_mod = importlib.import_module("license_service")

# Prefer class from the module; fallback if a singleton is exposed
if hasattr(ls_mod, "LicenseService"):
    LicenseService = ls_mod.LicenseService
else:
    # If something odd happened and we didn't get the module, use the instance's class
    singleton = getattr(ls_mod, "license_service", None)
    LicenseService = (singleton or ls_mod).__class__


# ---------------------------
# Fake repository used by tests
# ---------------------------
class FakeRepo:
    def __init__(self):
        self.last_create_data = None
        self.create_return = {"id": "new-id"}
        self.get_by_id_return = {"id": "r1"}
        self.update_returns = []
        self.last_update_args = []
        self.delete_return = False
        self.get_by_entity_return = []
        self.get_expiring_soon_return = []
        self.get_expired_licenses_return = []
        self.get_by_license_type_return = []
        self.find_return = []
        self.last_find_args = None
        self.count_queue = []
        self.last_count_queries = []

    async def create(self, data):
        self.last_create_data = dict(data)
        return dict(self.create_return)

    async def get_by_id(self, record_id):
        return dict(self.get_by_id_return) if self.get_by_id_return is not None else None

    async def update(self, record_id, data):
        self.last_update_args.append({"record_id": record_id, "data": dict(data)})
        if self.update_returns:
            return self.update_returns.pop(0)
        return None

    async def delete(self, record_id):
        return bool(self.delete_return)

    async def get_by_entity(self, entity_id, entity_type):
        return list(self.get_by_entity_return)

    async def get_expiring_soon(self, days_ahead):
        return list(self.get_expiring_soon_return)

    async def get_expired_licenses(self):
        return list(self.get_expired_licenses_return)

    async def get_by_license_type(self, license_type):
        return list(self.get_by_license_type_return)

    async def find(self, query=None, skip=0, limit=100, sort=None):
        self.last_find_args = {"query": dict(query or {}), "skip": skip, "limit": limit, "sort": list(sort or [])}
        return list(self.find_return)

    async def count(self, query):
        self.last_count_queries.append(dict(query))
        if self.count_queue:
            return self.count_queue.pop(0)
        return 0


def make_service(repo=None):
    svc = LicenseService()
    if repo is not None:
        svc.repository = repo
    return svc


# ---------------------------
# Tests
# ---------------------------

@pytest.mark.asyncio
async def test_create_license_record_success_parses_dates_and_sets_defaults():
    repo = FakeRepo()
    svc = make_service(repo)

    payload = {
        "entity_id": "veh-1",
        "entity_type": "vehicle",
        "license_type": "registration",
        "license_number": "ABC123",
        "title": "Vehicle Registration",
        "issue_date": "2025-01-01",
        "expiry_date": "2025-12-31",
        "issuing_authority": "DMV",
    }

    rec = await svc.create_license_record(payload)
    assert rec["id"] == "new-id"

    sent = repo.last_create_data
    assert isinstance(sent["issue_date"], date)
    assert isinstance(sent["expiry_date"], date)
    assert sent["is_active"] is True
    assert sent["advance_notice_days"] == 30
    assert isinstance(sent["created_at"], datetime)


@pytest.mark.asyncio
async def test_create_license_record_missing_required_field_raises():
    repo = FakeRepo()
    svc = make_service(repo)
    with pytest.raises(ValueError):
        await svc.create_license_record({
            "entity_type": "vehicle",
            "license_type": "registration",
            "license_number": "X",
            "title": "T",
            "issue_date": "2025-01-01",
            "expiry_date": "2025-12-31",
            "issuing_authority": "DMV",
        })


@pytest.mark.asyncio
async def test_create_license_record_invalid_entity_type_raises():
    repo = FakeRepo()
    svc = make_service(repo)
    bad = {
        "entity_id": "id1",
        "entity_type": "fleet",
        "license_type": "registration",
        "license_number": "X",
        "title": "T",
        "issue_date": "2025-01-01",
        "expiry_date": "2025-12-31",
        "issuing_authority": "DMV",
    }
    with pytest.raises(ValueError):
        await svc.create_license_record(bad)


@pytest.mark.asyncio
async def test_get_license_record_pass_through():
    repo = FakeRepo()
    repo.get_by_id_return = {"id": "abc"}
    svc = make_service(repo)
    res = await svc.get_license_record("abc")
    assert res["id"] == "abc"


@pytest.mark.asyncio
async def test_update_license_record_parses_dates_and_returns_record():
    repo = FakeRepo()
    repo.update_returns = [{"id": "u1"}]
    svc = make_service(repo)

    res = await svc.update_license_record("u1", {
        "issue_date": "2025-02-02",
        "renewal_date": "2025-02-03",
    })
    assert res["id"] == "u1"
    sent = repo.last_update_args[-1]["data"]
    assert isinstance(sent["issue_date"], date)
    assert isinstance(sent["renewal_date"], date)


@pytest.mark.asyncio
async def test_update_license_record_returns_none_when_not_found():
    repo = FakeRepo()
    repo.update_returns = [None]
    svc = make_service(repo)
    assert await svc.update_license_record("nope", {"title": "X"}) is None


@pytest.mark.asyncio
async def test_delete_license_record_true_and_false():
    repo = FakeRepo()
    svc = make_service(repo)
    repo.delete_return = True
    assert await svc.delete_license_record("x") is True
    repo.delete_return = False
    assert await svc.delete_license_record("x") is False


@pytest.mark.asyncio
async def test_get_entity_licenses_valid_and_invalid_type():
    repo = FakeRepo()
    svc = make_service(repo)
    repo.get_by_entity_return = [{"id": "L1"}]
    ok = await svc.get_entity_licenses("veh-1", "vehicle")
    assert ok == [{"id": "L1"}]
    with pytest.raises(ValueError):
        await svc.get_entity_licenses("veh-1", "fleet")


@pytest.mark.asyncio
async def test_expiring_expired_and_by_type_passthroughs():
    repo = FakeRepo()
    svc = make_service(repo)
    repo.get_expiring_soon_return = [{"id": "E1"}]
    repo.get_expired_licenses_return = [{"id": "EX1"}]
    repo.get_by_license_type_return = [{"id": "T1"}]
    assert await svc.get_expiring_licenses(15) == [{"id": "E1"}]
    assert await svc.get_expired_licenses() == [{"id": "EX1"}]
    assert await svc.get_licenses_by_type("registration") == [{"id": "T1"}]


@pytest.mark.asyncio
async def test_get_all_licenses_builds_fixed_query_and_sort():
    repo = FakeRepo()
    svc = make_service(repo)
    repo.find_return = [{"id": "A1"}]
    res = await svc.get_all_licenses(skip=5, limit=7)
    assert res == [{"id": "A1"}]
    args = repo.last_find_args
    assert args["query"] == {"is_active": True}
    assert args["skip"] == 5 and args["limit"] == 7
    assert args["sort"] == [("expiry_date", 1)]


@pytest.mark.asyncio
async def test_renew_license_with_and_without_cost_sets_renewal_date():
    repo = FakeRepo()
    svc = make_service(repo)
    today = date.today()
    repo.update_returns = [{"id": "R1"}, {"id": "R2"}]
    res1 = await svc.renew_license("R1", "2026-03-10", renewal_cost=99.5)
    sent1 = repo.last_update_args[-1]["data"]
    assert res1["id"] == "R1"
    assert sent1["expiry_date"] == date(2026, 3, 10)
    assert sent1["renewal_date"] == today
    assert sent1["renewal_cost"] == 99.5
    res2 = await svc.renew_license("R2", "2027-01-01")
    sent2 = repo.last_update_args[-1]["data"]
    assert res2["id"] == "R2"
    assert sent2["expiry_date"] == date(2027, 1, 1)
    assert sent2["renewal_date"] == today
    assert "renewal_cost" not in sent2


@pytest.mark.asyncio
async def test_deactivate_license_sets_flag_false():
    repo = FakeRepo()
    repo.update_returns = [{"id": "D1"}]
    svc = make_service(repo)
    res = await svc.deactivate_license("D1")
    sent = repo.last_update_args[-1]["data"]
    assert res["id"] == "D1"
    assert sent == {"is_active": False}


@pytest.mark.asyncio
async def test_search_licenses_builds_query_and_sort_desc():
    repo = FakeRepo()
    svc = make_service(repo)
    future_days = 45
    q = {
        "entity_id": "veh-1",
        "entity_type": "vehicle",
        "license_type": "registration",
        "is_active": True,
        "expiring_within_days": future_days,
    }
    _ = await svc.search_licenses(q, skip=2, limit=3, sort_by="license_number", sort_order="desc")
    args = repo.last_find_args
    assert args["skip"] == 2 and args["limit"] == 3
    assert args["sort"] == [("license_number", -1)]
    expected_future = date.today() + timedelta(days=future_days)
    assert args["query"]["entity_id"] == "veh-1"
    assert args["query"]["entity_type"] == "vehicle"
    assert args["query"]["license_type"] == "registration"
    assert args["query"]["is_active"] is True
    assert args["query"]["expiry_date"]["$lte"] == expected_future


@pytest.mark.asyncio
async def test_search_licenses_minimal_defaults():
    repo = FakeRepo()
    svc = make_service(repo)
    _ = await svc.search_licenses({}, skip=0, limit=10)
    args = repo.last_find_args
    assert args["query"] == {}
    assert args["sort"] == [("expiry_date", 1)]


@pytest.mark.asyncio
async def test_get_total_count_builds_query_with_expiring_within_days():
    repo = FakeRepo()
    svc = make_service(repo)
    repo.count_queue = [5]
    q = {"is_active": True, "expiring_within_days": 10}
    total = await svc.get_total_count(q)
    assert total == 5
    sent_query = repo.last_count_queries[-1]
    assert sent_query["is_active"] is True
    assert sent_query["expiry_date"]["$lte"] == date.today() + timedelta(days=10)


@pytest.mark.asyncio
async def test_get_license_summary_counts_and_computed_fields():
    repo = FakeRepo()
    svc = make_service(repo)
    repo.count_queue = [20, 16, 4, 3]
    summary = await svc.get_license_summary(entity_id="veh-1", entity_type="vehicle")
    assert summary["total_licenses"] == 20
    assert summary["active_licenses"] == 16
    assert summary["inactive_licenses"] == 4
    assert summary["expiring_soon"] == 4
    assert summary["expired"] == 3
    q_total, q_active, q_expiring, q_expired = repo.last_count_queries[-4:]
    assert q_total == {"entity_id": "veh-1", "entity_type": "vehicle"}
    assert q_active == {"entity_id": "veh-1", "entity_type": "vehicle", "is_active": True}
    assert q_expiring["is_active"] is True and "$lte" in q_expiring["expiry_date"]
    assert q_expired["is_active"] is True and "$lt" in q_expired["expiry_date"]
