# SAMFMS/Sblocks/maintenance/tests/unit/test_license_service.py
import pytest
from datetime import datetime, date, timedelta

from services import license_service as mod



@pytest.mark.asyncio
async def test_create_license_record_validates_required_and_defaults(mocker):
    svc = mod.LicenseService()
    created = {}
    mocker.patch.object(svc.repository, "create", side_effect=lambda d: {"id": "L1", **d})

    data = {
        "entity_id": "veh1", "entity_type": "vehicle", "license_type": "roadworthy",
        "license_number": "ABC123", "title": "Roadworthy", "issue_date": "2024-01-01",
        "expiry_date": "2025-01-01", "issuing_authority": "DMV"
    }
    rec = await svc.create_license_record(data)
    assert rec["id"] == "L1"
    assert isinstance(rec["issue_date"], date) and isinstance(rec["expiry_date"], date)
    assert rec["is_active"] is True and rec["advance_notice_days"] == 30


@pytest.mark.asyncio
async def test_create_license_record_rejects_bad_entity_type():
    svc = mod.LicenseService()
    bad = {
        "entity_id": "x", "entity_type": "truck", "license_type": "roadworthy",
        "license_number": "1", "title": "t", "issue_date": "2024-01-01",
        "expiry_date": "2024-12-31", "issuing_authority": "A"
    }
    with pytest.raises(ValueError):
        await svc.create_license_record(bad)


@pytest.mark.asyncio
async def test_get_update_delete_pass_through(mocker):
    svc = mod.LicenseService()
    mocker.patch.object(svc.repository, "get_by_id", return_value={"id": "L1"})
    assert (await svc.get_license_record("L1"))["id"] == "L1"

    mocker.patch.object(svc.repository, "update", return_value={"id": "L1", "title": "New"})
    upd = await svc.update_license_record("L1", {"issue_date": "2024-02-01"})
    assert isinstance(upd["id"], str)

    mocker.patch.object(svc.repository, "delete", return_value=True)
    assert await svc.delete_license_record("L1") is True


@pytest.mark.asyncio
async def test_get_entity_licenses_validates_type(mocker):
    svc = mod.LicenseService()
    mocker.patch.object(svc.repository, "get_by_entity", return_value=[{"id": "L1"}])
    res = await svc.get_entity_licenses("veh1", "vehicle")
    assert res and res[0]["id"] == "L1"
    with pytest.raises(ValueError):
        await svc.get_entity_licenses("veh1", "fleet")


@pytest.mark.asyncio
async def test_get_expiring_and_expired(mocker):
    svc = mod.LicenseService()
    mocker.patch.object(svc.repository, "get_expiring_soon", return_value=[1, 2])
    mocker.patch.object(svc.repository, "get_expired_licenses", return_value=[3])
    assert len(await svc.get_expiring_licenses(30)) == 2
    assert len(await svc.get_expired_licenses()) == 1


@pytest.mark.asyncio
async def test_get_licenses_by_type(mocker):
    svc = mod.LicenseService()
    mocker.patch.object(svc.repository, "get_by_license_type", return_value=[{"id": "L1"}])
    assert (await svc.get_licenses_by_type("roadworthy"))[0]["id"] == "L1"


@pytest.mark.asyncio
async def test_get_all_licenses_applies_default_sort(mocker):
    svc = mod.LicenseService()
    called = {}
    async def _find(query, skip, limit, sort):
        called.update(query=query, skip=skip, limit=limit, sort=sort)
        return []
    mocker.patch.object(svc.repository, "find", side_effect=_find)
    await svc.get_all_licenses(skip=5, limit=10)
    assert called["query"]["is_active"] is True
    assert called["sort"][0][0] == "expiry_date"


@pytest.mark.asyncio
async def test_renew_license_parses_date_and_sets_optional_cost(mocker):
    svc = mod.LicenseService()
    payload = {}
    mocker.patch.object(svc.repository, "update", side_effect=lambda _id, d: {"id": _id, **d})
    rec = await svc.renew_license("L1", "2025-06-01", renewal_cost=123.45)
    assert rec["expiry_date"].isoformat() == "2025-06-01"
    assert rec["renewal_cost"] == 123.45
    assert isinstance(rec["renewal_date"], date)


@pytest.mark.asyncio
async def test_search_licenses_builds_query_and_sort(mocker):
    svc = mod.LicenseService()
    captured = {}
    async def _find(q, skip, limit, sort):
        captured["q"], captured["skip"], captured["limit"], captured["sort"] = q, skip, limit, sort
        return []
    mocker.patch.object(svc.repository, "find", side_effect=_find)

    await svc.search_licenses(
        {"entity_id": "veh1", "entity_type": "vehicle", "license_type": "roadworthy", "is_active": True, "expiring_within_days": 15},
        skip=2, limit=5, sort_by="issue_date", sort_order="desc"
    )
    assert "expiry_date" in captured["q"]
    assert captured["sort"][0] == ("issue_date", -1)


@pytest.mark.asyncio
async def test_get_total_count_builds_query(mocker):
    svc = mod.LicenseService()
    captured = {}
    mocker.patch.object(svc.repository, "count", side_effect=lambda q: 99 if "expiry_date" in q else 0)
    total = await svc.get_total_count({"is_active": True, "expiring_within_days": 30})
    assert total == 99


@pytest.mark.asyncio
async def test_get_license_summary_combines_counts(mocker):
    svc = mod.LicenseService()
    # count: total, active, expiring soon, expired
    mocker.patch.object(svc.repository, "count", side_effect=[10, 8, 3, 1])
    s = await svc.get_license_summary(entity_id="veh1", entity_type="vehicle")
    assert s["total_licenses"] == 10
    assert s["inactive_licenses"] == 2
