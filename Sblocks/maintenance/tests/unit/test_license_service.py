import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock
from services.license_service import LicenseService

@pytest.fixture
def svc():
    return LicenseService()

@pytest.mark.asyncio
async def test_create_license_record_success_sets_defaults_and_parses_dates(mocker, svc):
    mock_repo = AsyncMock()
    svc.repository = mock_repo
    payload = {
        "entity_id": "V1", "entity_type": "vehicle",
        "license_type": "roadworthy", "license_number": "ABC123",
        "title": "Roadworthy", "issue_date": "2025-01-01", "expiry_date": "2026-01-01",
        "issuing_authority": "DMV"
    }
    mock_repo.create.return_value = {"id": "L1", **payload}
    res = await svc.create_license_record(payload.copy())
    assert res["id"] == "L1"
    # dates parsed
    args, _ = mock_repo.create.call_args
    called = args[0]
    assert isinstance(called["issue_date"], date)
    assert isinstance(called["expiry_date"], date)
    # default flags
    assert called["is_active"] is True
    assert called["advance_notice_days"] == 30
    assert isinstance(called["created_at"], datetime)

@pytest.mark.asyncio
async def test_create_license_record_missing_field_raises(mocker, svc):
    with pytest.raises(ValueError):
        await svc.create_license_record({"entity_type": "vehicle"})  # missing many

@pytest.mark.asyncio
async def test_create_license_record_invalid_entity_type_raises(mocker, svc):
    payload = {
        "entity_id": "X", "entity_type": "foo",
        "license_type": "roadworthy", "license_number": "A",
        "title": "t", "issue_date": "2025-01-01", "expiry_date": "2026-01-01",
        "issuing_authority": "DMV"
    }
    with pytest.raises(ValueError):
        await svc.create_license_record(payload)

@pytest.mark.asyncio
async def test_get_license_record_passthrough(mocker, svc):
    svc.repository = AsyncMock()
    svc.repository.get_by_id.return_value = {"id": "L1"}
    res = await svc.get_license_record("L1")
    assert res["id"] == "L1"

@pytest.mark.asyncio
async def test_update_license_record_parses_dates(mocker, svc):
    svc.repository = AsyncMock()
    svc.repository.update.return_value = {"id": "L1", "expiry_date": date(2026,1,1)}
    res = await svc.update_license_record("L1", {"expiry_date": "2026-01-01"})
    assert res["id"] == "L1"
    args, _ = svc.repository.update.call_args
    assert isinstance(args[1]["expiry_date"], date)

@pytest.mark.asyncio
async def test_delete_license_record_bool(mocker, svc):
    svc.repository = AsyncMock()
    svc.repository.delete.return_value = True
    assert await svc.delete_license_record("L1") is True

@pytest.mark.asyncio
async def test_get_entity_licenses_invalid_type_raises(mocker, svc):
    with pytest.raises(ValueError):
        await svc.get_entity_licenses("X", "company")

@pytest.mark.asyncio
async def test_get_entity_licenses_ok(mocker, svc):
    svc.repository = AsyncMock()
    svc.repository.get_by_entity.return_value = [{"id":"L1"}]
    res = await svc.get_entity_licenses("V1","vehicle")
    assert res == [{"id":"L1"}]

@pytest.mark.asyncio
async def test_get_expiring_and_expired_passthrough(mocker, svc):
    svc.repository = AsyncMock()
    svc.repository.get_expiring_soon.return_value = [{"id":"L1"}]
    svc.repository.get_expired_licenses.return_value = [{"id":"L2"}]
    assert await svc.get_expiring_licenses(30) == [{"id":"L1"}]
    assert await svc.get_expired_licenses() == [{"id":"L2"}]

@pytest.mark.asyncio
async def test_get_licenses_by_type_passthrough(mocker, svc):
    svc.repository = AsyncMock()
    svc.repository.get_by_license_type.return_value = [{"id":"L3"}]
    assert await svc.get_licenses_by_type("roadworthy") == [{"id":"L3"}]

@pytest.mark.asyncio
async def test_get_all_licenses_calls_find_with_sort(mocker, svc):
    svc.repository = AsyncMock()
    await svc.get_all_licenses(skip=5, limit=10)
    _, kwargs = svc.repository.find.call_args
    assert kwargs["skip"] == 5 and kwargs["limit"] == 10
    assert kwargs["sort"] == [("expiry_date", 1)]

@pytest.mark.asyncio
async def test_renew_license_sets_dates_and_cost(mocker, svc):
    svc.repository = AsyncMock()
    svc.repository.update.return_value = {"id": "L1", "expiry_date": date(2027,1,1)}
    res = await svc.renew_license("L1", "2027-01-01", renewal_cost=123.4)
    assert res["id"] == "L1"
    args, _ = svc.repository.update.call_args
    assert args[1]["renewal_cost"] == 123.4
    assert isinstance(args[1]["renewal_date"], date)

@pytest.mark.asyncio
async def test_deactivate_license_sets_flag(mocker, svc):
    svc.repository = AsyncMock()
    await svc.deactivate_license("L1")
    args, _ = svc.repository.update.call_args
    assert args[1] == {"is_active": False}

@pytest.mark.asyncio
async def test_search_licenses_builds_query_and_sort(mocker, svc):
    svc.repository = AsyncMock()
    q = {"entity_id":"V1","is_active":True,"expiring_within_days":15}
    await svc.search_licenses(q, skip=2, limit=3, sort_by="license_type", sort_order="desc")
    args, _ = svc.repository.find.call_args
    assert args[0]["entity_id"] == "V1"
    assert "$lte" in args[0]["expiry_date"]  # expiring_within_days mapped
    assert args[3] == [("license_type",-1)]

@pytest.mark.asyncio
async def test_get_total_count_builds_query(mocker, svc):
    svc.repository = AsyncMock()
    q = {"entity_type":"vehicle","license_type":"roadworthy"}
    await svc.get_total_count(q)
    svc.repository.count.assert_called_once()
    (db_query,), _ = svc.repository.count.call_args
    assert db_query["entity_type"] == "vehicle"
    assert db_query["license_type"] == "roadworthy"

@pytest.mark.asyncio
async def test_get_license_summary_counts(mocker, svc):
    svc.repository = AsyncMock()
    svc.repository.count.side_effect = [10, 7, 3, 2]  # total, active, expiring, expired
    res = await svc.get_license_summary(entity_id="V1", entity_type="vehicle")
    assert res == {
        "total_licenses": 10, "active_licenses": 7,
        "inactive_licenses": 3, "expiring_soon": 3, "expired": 2
    }
