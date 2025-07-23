"""
Analytics API routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from schemas.requests import AnalyticsRequest
from schemas.responses import ResponseBuilder, TripAnalyticsResponse, DriverPerformanceResponse
from services.analytics_service import analytics_service
from api.dependencies import get_current_user

router = APIRouter()


@router.get("/trips/summary", response_model=Dict[str, Any])
async def get_trip_summary_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    driver_ids: Optional[List[str]] = Query(None, description="Filter by driver IDs"),
    vehicle_ids: Optional[List[str]] = Query(None, description="Filter by vehicle IDs"),
    trip_ids: Optional[List[str]] = Query(None, description="Filter by trip IDs"),
    group_by: Optional[str] = Query(None, regex="^(day|week|month|driver|vehicle)$"),
    metrics: List[str] = Query(["duration", "distance", "fuel", "cost"], description="Metrics to include"),
    current_user: str = Depends(get_current_user)
):
    """Get comprehensive trip analytics summary"""
    try:
        request = AnalyticsRequest(
            start_date=start_date,
            end_date=end_date,
            driver_ids=driver_ids,
            vehicle_ids=vehicle_ids,
            trip_ids=trip_ids,
            group_by=group_by,
            metrics=metrics
        )
        
        analytics = await analytics_service.get_trip_analytics(request)
        
        return ResponseBuilder.success(
            data=analytics,
            message="Trip analytics retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get trip analytics")


@router.get("/drivers/performance", response_model=Dict[str, Any])
async def get_driver_performance_analytics(
    driver_ids: Optional[List[str]] = Query(None, description="Specific driver IDs"),
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    current_user: str = Depends(get_current_user)
):
    """Get driver performance metrics"""
    try:
        performance_data = await analytics_service.get_driver_performance(
            driver_ids=driver_ids,
            start_date=start_date,
            end_date=end_date
        )
        
        return ResponseBuilder.success(
            data={"drivers": performance_data},
            message="Driver performance analytics retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get driver performance analytics")


@router.get("/routes/efficiency", response_model=Dict[str, Any])
async def get_route_efficiency_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for analysis"),
    current_user: str = Depends(get_current_user)
):
    """Get route efficiency analysis"""
    try:
        efficiency_data = await analytics_service.get_route_efficiency_analysis(
            start_date=start_date,
            end_date=end_date
        )
        
        return ResponseBuilder.success(
            data=efficiency_data,
            message="Route efficiency analytics retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get route efficiency analytics")


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_analytics(
    period: str = Query("month", regex="^(day|week|month|quarter|year)$"),
    current_user: str = Depends(get_current_user)
):
    """Get dashboard analytics for the specified period"""
    try:
        # Calculate date range based on period
        now = datetime.utcnow()
        if period == "day":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = start_date - timedelta(days=start_date.weekday())
        elif period == "month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "quarter":
            quarter_start_month = ((now.month - 1) // 3) * 3 + 1
            start_date = now.replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "year":
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get analytics for the period
        request = AnalyticsRequest(
            start_date=start_date,
            end_date=now,
            metrics=["duration", "distance", "fuel", "cost"]
        )
        
        analytics = await analytics_service.get_trip_analytics(request)
        
        # Get driver performance for top performers
        top_drivers = await analytics_service.get_driver_performance(
            start_date=start_date,
            end_date=now
        )
        
        # Combine dashboard data
        dashboard_data = {
            "period": period,
            "period_start": start_date,
            "period_end": now,
            "trip_analytics": analytics,
            "top_drivers": top_drivers[:5] if top_drivers else [],  # Top 5 drivers
            "generated_at": now
        }
        
        return ResponseBuilder.success(
            data=dashboard_data,
            message="Dashboard analytics retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get dashboard analytics")


@router.get("/kpis", response_model=Dict[str, Any])
async def get_key_performance_indicators(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: str = Depends(get_current_user)
):
    """Get key performance indicators"""
    try:
        request = AnalyticsRequest(
            start_date=start_date,
            end_date=end_date,
            metrics=["duration", "distance", "cost"]
        )
        
        analytics = await analytics_service.get_trip_analytics(request)
        
        # Calculate KPIs
        kpis = {
            "total_trips": analytics.get("total_trips", 0),
            "completion_rate": analytics.get("completion_rate", 0),
            "on_time_percentage": analytics.get("on_time_percentage", 0),
            "average_trip_duration": analytics.get("average_duration", 0),
            "total_distance": analytics.get("total_distance", 0),
            "average_cost_per_trip": analytics.get("average_cost_per_trip", 0),
            "fuel_efficiency": analytics.get("fuel_efficiency", 0),
            "period_start": analytics.get("period_start"),
            "period_end": analytics.get("period_end")
        }
        
        return ResponseBuilder.success(
            data=kpis,
            message="KPIs retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get KPIs")


@router.get("/trends", response_model=Dict[str, Any])
async def get_analytics_trends(
    metric: str = Query("trip_count", description="Metric to analyze for trends"),
    period: str = Query("week", regex="^(day|week|month)$"),
    periods_back: int = Query(12, ge=1, le=52, description="Number of periods to go back"),
    current_user: str = Depends(get_current_user)
):
    """Get trend analysis for a specific metric"""
    try:
        # This would implement proper trend calculation
        # For now, return mock trend data
        
        from datetime import timedelta
        
        trends = []
        now = datetime.utcnow()
        
        for i in range(periods_back):
            if period == "day":
                period_start = now - timedelta(days=i+1)
                period_end = now - timedelta(days=i)
            elif period == "week":
                period_start = now - timedelta(weeks=i+1)
                period_end = now - timedelta(weeks=i)
            elif period == "month":
                # Simplified month calculation
                period_start = now - timedelta(days=(i+1)*30)
                period_end = now - timedelta(days=i*30)
            
            # Mock data - would calculate actual trends
            trends.append({
                "period_start": period_start,
                "period_end": period_end,
                "value": 50 + (i % 10),  # Mock trending value
                "change_percentage": ((i % 10) - 5) * 2  # Mock change percentage
            })
        
        trends.reverse()  # Order from oldest to newest
        
        return ResponseBuilder.success(
            data={
                "metric": metric,
                "period": period,
                "trends": trends
            },
            message="Trend analysis retrieved successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get trend analysis")
