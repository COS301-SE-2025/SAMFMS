from datetime import date
import pytest

from api.routes import licenses as routes


# ---------- Helpers ----------

class _Timer:
    request_id = "req-lic"
    @property
    def elapsed(self):
        return 9


@pytest.fixture
def fake_timer():
    return _Timer()


@pytest.fixture
def rb_success(mocker):
    def _success(**kwargs):
        return kwargs
    return mocker.patch("api.routes.licenses.ResponseBuilder.success", side_effect=_success)


@pytest.fixture
def rb_error(mocker):
    def _error(**kwargs):
        return kwargs
    return mocker.patch("api.routes.licenses.ResponseBuilder.error", side_effect=_error)


# ---------- /licenses/ (POST) ----------

@pytest.mark.asyncio
async def test_create_license_record_adds_created_updated_by(mocker, rb_success, fake_timer):
    recorded = {}
    async def _create(data):
        recorded["data"] = data
        return {"_id": "L1", **data}

    mocker.patch.object(routes.license_service, "create_license_record", side_effect=_create)

    class _Req:
        def dict(self):
            return {"license_type": "roadworthy", "entity_id": "veh1"}

    res = await routes.create_license_record(request=_Req(), user={"user_id": "u1"}, timer=fake_timer)
    assert res["data"]["_id"] == "L1"
    assert recorded["data"]["created_by"] == "u1"
    assert recorded["data"]["updated_by"] == "u1"


@pytest.mark.asyncio
async def test_create_license_record_value_error_returns_400(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "create_license_record", side_effect=ValueError("bad"))
    class _Req: 
        def dict(self): 
            return {}
    res = await routes.create_license_record(request=_Req(), user={"user_id": "u1"}, timer=fake_timer)
    assert res["status_code"] == 400


@pytest.mark.asyncio
async def test_create_license_record_exception_returns_500(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "create_license_record", side_effect=Exception("boom"))
    class _Req: 
        def dict(self): 
            return {}
    res = await routes.create_license_record(request=_Req(), user={"user_id": "u1"}, timer=fake_timer)
    assert res["status_code"] == 500


# ---------- /licenses/ (GET) ----------

@pytest.mark.asyncio
async def test_get_license_records_builds_summary_and_has_more(mocker, rb_success, fake_timer):
    mocker.patch.object(routes.license_service, "search_licenses", return_value=[{"_id": "L1"}, {"_id": "L2"}])
    mocker.patch.object(routes.license_service, "get_total_count", return_value=5)
    mocker.patch.object(
        routes.license_service,
        "get_license_summary",
        return_value={"expired": 1, "expiring_soon": 1, "active_licenses": 8, "total_licenses": 10},
    )

    res = await routes.get_license_records(
        entity_id=None,
        entity_type=None,
        license_type=None,
        expiring_within_days=None,
        is_active=None,
        sort_by="expiry_date",
        sort_order="asc",
        user={"user_id": "u1"},
        pagination={"skip": 0, "limit": 2},  # route expects dict-style access
        timer=fake_timer,
    )
    data = res["data"]
    assert data["total"] == 5
    assert data["has_more"] is True  # 0 + len(2) < 5
    assert data["summary"]["compliance_rate"] == 80.0


@pytest.mark.asyncio
async def test_get_license_records_error_returns_500(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "search_licenses", side_effect=Exception("boom"))
    res = await routes.get_license_records(
        entity_id=None,
        entity_type=None,
        license_type=None,
        expiring_within_days=None,
        is_active=None,
        sort_by="expiry_date",
        sort_order="asc",
        user={"user_id": "u1"},
        pagination={"skip": 0, "limit": 10},
        timer=fake_timer,
    )
    assert res["status_code"] == 500


# ---------- /licenses/{id} (GET) ----------

@pytest.mark.asyncio
async def test_get_license_record_not_found_returns_404(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "get_license_record", return_value=None)
    res = await routes.get_license_record(record_id="a" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 404


@pytest.mark.asyncio
async def test_get_license_record_success(mocker, rb_success, fake_timer):
    mocker.patch.object(routes.license_service, "get_license_record", return_value={"_id": "L1"})
    res = await routes.get_license_record(record_id="b" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert res["data"] == {"_id": "L1"}


# ---------- /licenses/{id} (PUT) ----------

@pytest.mark.asyncio
async def test_update_license_record_no_data_returns_400(mocker, rb_error, fake_timer):
    class _Req:
        def dict(self):
            return {}
    res = await routes.update_license_record(
        request=_Req(), record_id="a" * 24, user={"user_id": "u1"}, timer=fake_timer
    )
    assert res["status_code"] == 400


@pytest.mark.asyncio
async def test_update_license_record_sets_updated_by(mocker, rb_success, fake_timer):
    captured = {}
    async def _update(record_id, data):
        captured["record_id"] = record_id
        captured["data"] = data
        return {"_id": record_id, **data}
    mocker.patch.object(routes.license_service, "update_license_record", side_effect=_update)

    class _Req:
        def dict(self):
            return {"license_type": "roadworthy"}  # not None -> retained

    res = await routes.update_license_record(
        request=_Req(), record_id="c" * 24, user={"user_id": "u2"}, timer=fake_timer
    )
    assert captured["record_id"] == "c" * 24
    assert captured["data"]["updated_by"] == "u2"
    assert res["data"]["_id"] == "c" * 24


@pytest.mark.asyncio
async def test_update_license_record_not_found_returns_404(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "update_license_record", return_value=None)
    class _Req:
        def dict(self): return {"field": "value"}
    res = await routes.update_license_record(
        request=_Req(), record_id="d" * 24, user={"user_id": "u"}, timer=fake_timer
    )
    assert res["status_code"] == 404


@pytest.mark.asyncio
async def test_update_license_record_error_returns_500(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "update_license_record", side_effect=Exception("boom"))
    class _Req:
        def dict(self): return {"field": "value"}
    res = await routes.update_license_record(
        request=_Req(), record_id="e" * 24, user={"user_id": "u"}, timer=fake_timer
    )
    assert res["status_code"] == 500


# ---------- /licenses/{id} (DELETE) ----------

@pytest.mark.asyncio
async def test_delete_license_record_success(mocker, rb_success, fake_timer):
    mocker.patch.object(routes.license_service, "delete_license_record", return_value=True)
    res = await routes.delete_license_record(record_id="a" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert "deleted successfully" in res["message"]


@pytest.mark.asyncio
async def test_delete_license_record_not_found(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "delete_license_record", return_value=False)
    res = await routes.delete_license_record(record_id="b" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 404


@pytest.mark.asyncio
async def test_delete_license_record_error(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "delete_license_record", side_effect=Exception("boom"))
    res = await routes.delete_license_record(record_id="c" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 500


# ---------- /licenses/entity/{entity_id} ----------

@pytest.mark.asyncio
async def test_get_entity_licenses_success(mocker, rb_success, fake_timer):
    mocker.patch.object(routes.license_service, "get_entity_licenses", return_value=[{"_id": "L1"}])
    res = await routes.get_entity_licenses(
        entity_id="a" * 24, entity_type="vehicle", user={"user_id": "u"}, timer=fake_timer
    )
    assert res["metadata"]["entity_type"] == "vehicle"
    assert res["metadata"]["total"] == 1


@pytest.mark.asyncio
async def test_get_entity_licenses_value_error_returns_400(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "get_entity_licenses", side_effect=ValueError("bad"))
    res = await routes.get_entity_licenses(
        entity_id="b" * 24, entity_type="driver", user={"user_id": "u"}, timer=fake_timer
    )
    assert res["status_code"] == 400


# ---------- /licenses/status/expiring ----------

@pytest.mark.asyncio
async def test_get_expiring_licenses_success(mocker, rb_success, fake_timer):
    mocker.patch.object(routes.license_service, "get_expiring_licenses", return_value=[1, 2])
    res = await routes.get_expiring_licenses(days=30, user={"user_id": "u"}, timer=fake_timer)
    assert res["metadata"]["days"] == 30
    assert res["metadata"]["total"] == 2


@pytest.mark.asyncio
async def test_get_expiring_licenses_error(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "get_expiring_licenses", side_effect=Exception("boom"))
    res = await routes.get_expiring_licenses(days=15, user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 500


# ---------- /licenses/status/expired ----------

@pytest.mark.asyncio
async def test_get_expired_licenses_success(mocker, rb_success, fake_timer):
    mocker.patch.object(routes.license_service, "get_expired_licenses", return_value=[{"_id": "L1"}])
    res = await routes.get_expired_licenses(user={"user_id": "u"}, timer=fake_timer)
    assert res["metadata"]["total"] == 1


# ---------- /licenses/type/{license_type} ----------

@pytest.mark.asyncio
async def test_get_licenses_by_type_success(mocker, rb_success, fake_timer):
    mocker.patch.object(routes.license_service, "get_licenses_by_type", return_value=[1, 2, 3])
    res = await routes.get_licenses_by_type(license_type="roadworthy", user={"user_id": "u"}, timer=fake_timer)
    assert res["metadata"]["license_type"] == "roadworthy"
    assert res["metadata"]["total"] == 3


# ---------- /licenses/{id}/renew ----------

@pytest.mark.asyncio
async def test_renew_license_success(mocker, rb_success, fake_timer):
    mocker.patch.object(routes.license_service, "renew_license", return_value={"_id": "L1"})
    res = await routes.renew_license(
        record_id="a" * 24,
        new_expiry_date=date(2025, 1, 1),
        renewal_cost=100.0,
        user={"user_id": "u"},
        timer=fake_timer,
    )
    assert res["message"] == "License renewed successfully"
    assert res["data"]["_id"] == "L1"


@pytest.mark.asyncio
async def test_renew_license_not_found_returns_404(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "renew_license", return_value=None)
    res = await routes.renew_license(
        record_id="b" * 24, new_expiry_date=date(2025, 2, 1), renewal_cost=None, user={"user_id": "u"}, timer=fake_timer
    )
    assert res["status_code"] == 404


@pytest.mark.asyncio
async def test_renew_license_error_returns_500(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "renew_license", side_effect=Exception("boom"))
    res = await routes.renew_license(
        record_id="c" * 24, new_expiry_date=date(2025, 3, 1), renewal_cost=0.0, user={"user_id": "u"}, timer=fake_timer
    )
    assert res["status_code"] == 500


# ---------- /licenses/{id}/deactivate ----------

@pytest.mark.asyncio
async def test_deactivate_license_success(mocker, rb_success, fake_timer):
    mocker.patch.object(routes.license_service, "deactivate_license", return_value={"_id": "L1", "active": False})
    res = await routes.deactivate_license(record_id="a" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert res["message"] == "License deactivated successfully"
    assert res["data"]["active"] is False


@pytest.mark.asyncio
async def test_deactivate_license_not_found_returns_404(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "deactivate_license", return_value=None)
    res = await routes.deactivate_license(record_id="b" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 404


@pytest.mark.asyncio
async def test_deactivate_license_error_returns_500(mocker, rb_error, fake_timer):
    mocker.patch.object(routes.license_service, "deactivate_license", side_effect=Exception("boom"))
    res = await routes.deactivate_license(record_id="c" * 24, user={"user_id": "u"}, timer=fake_timer)
    assert res["status_code"] == 500