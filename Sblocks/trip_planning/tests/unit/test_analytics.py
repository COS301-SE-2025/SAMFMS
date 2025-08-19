import pytest
import api.routes.analytics as m
from fastapi import HTTPException


class RB:
    @staticmethod
    def success(data=None, message=""): return {"success": True, "message": message, "data": data}
m.ResponseBuilder = RB  

@pytest.mark.asyncio
async def test_get_trip_summary_analytics_ok(monkeypatch):
    async def _ana(req): return {"total_trips": 3}
    monkeypatch.setattr(m.analytics_service, "get_trip_analytics", _ana)
    res = await m.get_trip_summary_analytics(
        start_date=None,
        end_date=None,
        driver_ids=None,
        vehicle_ids=None,
        trip_ids=None,
        group_by=None,
        metrics=["duration", "distance", "fuel", "cost"],
        current_user="u",
    )
    assert res["data"]["total_trips"] == 3

@pytest.mark.asyncio
async def test_get_trip_history_stats_ok(monkeypatch):
    async def _hist(days): return {"total": 10}
    monkeypatch.setattr(m.analytics_service, "get_trip_history_stats", _hist)
    res = await m.get_trip_history_stats(current_user="u")
    assert res["data"]["total"] == 10

@pytest.mark.asyncio
async def test_get_driver_performance_analytics_ok(monkeypatch):
    async def _perf(driver_ids=None, start_date=None, end_date=None): return [{"id":"d1"}]
    monkeypatch.setattr(m.analytics_service, "get_driver_performance", _perf)
    res = await m.get_driver_performance_analytics(current_user="u")
    assert res["data"]["drivers"][0]["id"] == "d1"

@pytest.mark.asyncio
async def test_get_route_efficiency_analytics_ok(monkeypatch):
    async def _eff(start_date=None, end_date=None): return {"eff": 0.9}
    monkeypatch.setattr(m.analytics_service, "get_route_efficiency_analysis", _eff)
    res = await m.get_route_efficiency_analytics(current_user="u")
    assert res["data"]["eff"] == 0.9

@pytest.mark.asyncio
async def test_get_dashboard_analytics_ok(monkeypatch):
    async def _ana(req): return {"summary": True}
    async def _perf(start_date=None, end_date=None): return [{"id": "d1"}, {"id":"d2"}]
    monkeypatch.setattr(m.analytics_service, "get_trip_analytics", _ana)
    monkeypatch.setattr(m.analytics_service, "get_driver_performance", _perf)
    res = await m.get_dashboard_analytics(period="month", current_user="u")
    assert res["data"]["trip_analytics"]["summary"] is True
    assert len(res["data"]["top_drivers"]) <= 5

@pytest.mark.asyncio
async def test_get_key_performance_indicators_ok(monkeypatch):
    async def _ana(req):
        return {
            "total_trips": 4,
            "completion_rate": 0.75,
            "on_time_percentage": 0.8,
            "average_duration": 42,
            "total_distance": 1000,
            "average_cost_per_trip": 12.5,
            "fuel_efficiency": 33.3,
            "period_start": "ps",
            "period_end": "pe",
        }
    monkeypatch.setattr(m.analytics_service, "get_trip_analytics", _ana)
    res = await m.get_key_performance_indicators(
        start_date=None, end_date=None, current_user="u"
    )
    assert res["data"]["total_trips"] == 4
    assert "period_start" in res["data"]

@pytest.mark.asyncio
async def test_get_analytics_trends_ok():
    res = await m.get_analytics_trends(
        metric="trip_count", period="week", periods_back=12, current_user="u"
    )
    assert res["data"]["metric"] == "trip_count"
    assert len(res["data"]["trends"]) > 0
