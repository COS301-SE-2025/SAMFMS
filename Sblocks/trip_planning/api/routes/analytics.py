"""
Analytics API routes
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from schemas.requests import AnalyticsRequest
from schemas.responses import ResponseBuilder, StandardResponse, ResponseStatus
from services.analytics_service import analytics_service
from api.dependencies import get_current_user_legacy as get_current_user
from repositories.database import db_manager

logger = logging.getLogger(__name__)
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


@router.get("/trips/history-stats", response_model=Dict[str, Any])
async def get_trip_history_stats(
    days: Optional[int] = Query(None, description="Number of days to look back (default: all time)"),
    current_user: str = Depends(get_current_user)
):
    """Get trip history statistics including totals and averages"""
    try:
        stats = await analytics_service.get_trip_history_stats(days)
        
        return ResponseBuilder.success(
            data=stats,
            message="Trip history statistics retrieved successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to get trip history stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trip history statistics")


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


# Driver Behavior Analytics Endpoints

@router.get("/driver-behavior/violation-trends", response_model=StandardResponse)
async def get_violation_trends(
    period: str = Query("7d", description="Time period: 7d, 30d, 90d"),
    driver_id: Optional[str] = Query(None, description="Filter by specific driver"),
    current_user: str = Depends(get_current_user)
) -> StandardResponse:
    """
    Get violation trends over time by type
    
    Returns time-series data showing violation counts by type (speeding, braking, acceleration, phone usage)
    with daily, weekly, or monthly aggregations based on the specified period.
    """
    logger.info(f"[AnalyticsAPI] Getting violation trends for period {period}, driver_id: {driver_id}")
    
    try:
        # Parse period parameter
        days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 7)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build match filter - use both created_at and time fields for compatibility
        base_match = {
            "$or": [
                {"created_at": {"$gte": start_date}},
                {"time": {"$gte": start_date}}
            ]
        }
        if driver_id:
            base_match["driver_id"] = driver_id
        
        # Get data from each violation collection using aggregation
        violation_types = {
            "speed_violations": "speeding",
            "excessive_braking_violations": "braking", 
            "excessive_acceleration_violations": "acceleration",
            "phone_usage_violations": "phone_usage"
        }
        
        trends_data = {}
        total_violations = 0
        
        for collection_name, violation_type in violation_types.items():
            collection = getattr(db_manager, collection_name)
            
            # Use aggregation to get daily counts - handle both date field formats
            pipeline = [
                {"$match": base_match},
                {
                    "$addFields": {
                        "violation_date": {
                            "$ifNull": ["$created_at", "$time"]
                        }
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$violation_date"},
                            "month": {"$month": "$violation_date"},
                            "day": {"$dayOfMonth": "$violation_date"}
                        },
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            # Execute aggregation and collect results
            daily_counts = {}
            try:
                cursor = collection.aggregate(pipeline)
                docs = await cursor.to_list(length=None)
                for doc in docs:
                    date_key = f"{doc['_id']['year']}-{doc['_id']['month']:02d}-{doc['_id']['day']:02d}"
                    daily_counts[date_key] = doc['count']
                    total_violations += doc['count']
            except Exception as e:
                logger.warning(f"Error querying {collection_name}: {e}")
                daily_counts = {}
            
            # Fill in missing dates with 0 counts
            date_series = []
            current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            while current_date <= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0):
                date_key = current_date.strftime("%Y-%m-%d")
                date_series.append({
                    "date": date_key,
                    "count": daily_counts.get(date_key, 0)
                })
                current_date += timedelta(days=1)
            
            trends_data[violation_type] = date_series
        
        summary = {
            "total_violations": total_violations,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "driver_filter": driver_id
        }
        
        logger.info(f"[AnalyticsAPI] Retrieved violation trends: {total_violations} total violations over {days} days")
        
        return StandardResponse(
            status=ResponseStatus.SUCCESS,
            message="Violation trends retrieved successfully",
            data={
                "trends": trends_data,
                "summary": summary
            }
        )
        
    except Exception as e:
        logger.error(f"[AnalyticsAPI] Failed to get violation trends: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve violation trends: {str(e)}"
        )


@router.get("/driver-behavior/risk-distribution", response_model=StandardResponse)
async def get_risk_distribution(
    current_user: str = Depends(get_current_user)
) -> StandardResponse:
    """
    Get driver risk distribution based on violation history and safety scores
    
    Returns risk level distribution (low/medium/high) with driver counts and percentages,
    safety score ranges, and top/worst performing drivers.
    """
    logger.info("[AnalyticsAPI] Getting driver risk distribution")
    
    try:
        # Get all drivers from driver_history collection
        try:
            cursor = db_manager.driver_history.find({})
            drivers = await cursor.to_list(length=None)
        except Exception as e:
            logger.warning(f"Error querying driver_history: {e}")
            drivers = []
        
        if not drivers:
            # Return empty distribution if no driver data
            return StandardResponse(
                status=ResponseStatus.SUCCESS,
                message="No driver data available",
                data={
                    "distribution": {"low_risk": 0, "medium_risk": 0, "high_risk": 0},
                    "safety_score_ranges": {
                        "90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "below_60": 0
                    },
                    "performance_metrics": {
                        "avg_safety_score": 0, "violation_rate": 0, "improvement_trend": "neutral"
                    },
                    "top_performers": [],
                    "worst_performers": []
                }
            )
        
        # Analyze risk distribution
        risk_distribution = {"low_risk": 0, "medium_risk": 0, "high_risk": 0}
        safety_score_ranges = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "below_60": 0}
        safety_scores = []
        
        for driver in drivers:
            safety_score = driver.get("safety_score", driver.get("driver_safety_score", 0))
            safety_scores.append(safety_score)
            
            # Classify risk level based on safety score and violation count
            violation_count = driver.get("total_violations", 0)
            
            if safety_score >= 80 and violation_count <= 5:
                risk_distribution["low_risk"] += 1
            elif safety_score >= 60 and violation_count <= 15:
                risk_distribution["medium_risk"] += 1
            else:
                risk_distribution["high_risk"] += 1
            
            # Categorize safety score
            if safety_score >= 90:
                safety_score_ranges["90-100"] += 1
            elif safety_score >= 80:
                safety_score_ranges["80-89"] += 1
            elif safety_score >= 70:
                safety_score_ranges["70-79"] += 1
            elif safety_score >= 60:
                safety_score_ranges["60-69"] += 1
            else:
                safety_score_ranges["below_60"] += 1
        
        # Calculate performance metrics
        avg_safety_score = round(sum(safety_scores) / len(safety_scores), 2) if safety_scores else 0
        total_violations = sum(driver.get("total_violations", 0) for driver in drivers)
        total_trips = sum(driver.get("total_trips", 1) for driver in drivers)
        violation_rate = round(total_violations / total_trips, 3) if total_trips > 0 else 0
        
        # Determine improvement trend (simplified logic)
        recent_violations = sum(driver.get("recent_violations", 0) for driver in drivers)
        historical_violations = sum(driver.get("historical_violations", recent_violations) for driver in drivers)
        
        if recent_violations < historical_violations * 0.8:
            improvement_trend = "positive"
        elif recent_violations > historical_violations * 1.2:
            improvement_trend = "negative"
        else:
            improvement_trend = "neutral"
        
        performance_metrics = {
            "avg_safety_score": avg_safety_score,
            "violation_rate": violation_rate,
            "improvement_trend": improvement_trend
        }
        
        # Get top and worst performers
        sorted_drivers = sorted(drivers, key=lambda x: x.get("safety_score", x.get("driver_safety_score", 0)), reverse=True)
        top_performers = [
            {
                "driver_id": driver.get("driver_id", "Unknown"),
                "name": driver.get("name", driver.get("driver_name", "Unknown Driver")),
                "safety_score": driver.get("safety_score", driver.get("driver_safety_score", 0))
            }
            for driver in sorted_drivers[:5]
        ]
        
        worst_performers = [
            {
                "driver_id": driver.get("driver_id", "Unknown"),
                "name": driver.get("name", driver.get("driver_name", "Unknown Driver")),
                "safety_score": driver.get("safety_score", driver.get("driver_safety_score", 0))
            }
            for driver in sorted_drivers[-5:]
        ]
        
        logger.info(f"[AnalyticsAPI] Risk distribution calculated for {len(drivers)} drivers")
        
        return StandardResponse(
            status=ResponseStatus.SUCCESS,
            message="Driver risk distribution retrieved successfully",
            data={
                "distribution": risk_distribution,
                "safety_score_ranges": safety_score_ranges,
                "performance_metrics": performance_metrics,
                "top_performers": top_performers,
                "worst_performers": worst_performers
            }
        )
        
    except Exception as e:
        logger.error(f"[AnalyticsAPI] Failed to get risk distribution: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve driver risk distribution: {str(e)}"
        )


@router.get("/driver-behavior/performance-metrics", response_model=StandardResponse)
async def get_performance_metrics(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    current_user: str = Depends(get_current_user)
) -> StandardResponse:
    """
    Get overall performance metrics and key safety indicators
    
    Returns system-wide performance metrics including total violations, safety scores,
    improvement trends, and key performance indicators over the specified period.
    """
    logger.info(f"[AnalyticsAPI] Getting performance metrics for period {period}")
    
    try:
        # Parse period parameter
        days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get violation counts by type
        violation_counts = {}
        violation_types = {
            "speed_violations": "speeding",
            "excessive_braking_violations": "braking",
            "excessive_acceleration_violations": "acceleration",
            "phone_usage_violations": "phone_usage"
        }
        
        total_violations = 0
        for collection_name, violation_type in violation_types.items():
            try:
                collection = getattr(db_manager, collection_name)
                # Handle both created_at and time fields
                count = await collection.count_documents({
                    "$or": [
                        {"created_at": {"$gte": start_date}},
                        {"time": {"$gte": start_date}}
                    ]
                })
                violation_counts[violation_type] = count
                total_violations += count
            except Exception as e:
                logger.warning(f"Error counting {collection_name}: {e}")
                violation_counts[violation_type] = 0
        
        # Get driver statistics
        try:
            cursor = db_manager.driver_history.find({})
            drivers = await cursor.to_list(length=None)
        except Exception as e:
            logger.warning(f"Error querying driver_history: {e}")
            drivers = []
        
        # Calculate safety metrics
        if drivers:
            safety_scores = [d.get("safety_score", d.get("driver_safety_score", 0)) for d in drivers]
            avg_safety_score = round(sum(safety_scores) / len(safety_scores), 2)
            
            # Calculate trends (simplified - compare with previous period)
            prev_start_date = start_date - timedelta(days=days)
            prev_total_violations = 0
            
            for collection_name in violation_types.keys():
                try:
                    collection = getattr(db_manager, collection_name)
                    prev_count = await collection.count_documents({
                        "created_at": {"$gte": prev_start_date, "$lt": start_date}
                    })
                    prev_total_violations += prev_count
                except Exception as e:
                    logger.warning(f"Error counting previous {collection_name}: {e}")
            
            # Calculate improvement percentage
            if prev_total_violations > 0:
                period_change = round(((prev_total_violations - total_violations) / prev_total_violations) * 100, 2)
            else:
                period_change = 0
            
            # Mock other trend calculations (would need historical data)
            violation_rate_change = period_change * 0.6  # Approximate correlation
            avg_safety_score_change = 2.1 if period_change > 0 else -1.5
        else:
            avg_safety_score = 0
            period_change = 0
            violation_rate_change = 0
            avg_safety_score_change = 0
        
        # Calculate key performance indicators
        violations_per_driver = round(total_violations / len(drivers), 2) if drivers else 0
        violations_per_day = round(total_violations / days, 2)
        
        # Count critical violations (simplified criteria)
        critical_violations = 0
        for collection_name in violation_types.keys():
            try:
                collection = getattr(db_manager, collection_name)
                # Count violations that might be considered critical based on common fields
                critical_count = await collection.count_documents({
                    "created_at": {"$gte": start_date},
                    "$or": [
                        {"severity": {"$gt": 0.8}},
                        {"speed": {"$gt": 120}},
                        {"duration_seconds": {"$gt": 300}}
                    ]
                })
                critical_violations += critical_count
            except Exception as e:
                logger.warning(f"Error counting critical violations in {collection_name}: {e}")
        
        # Driver improvement and completion metrics
        improving_drivers = len([d for d in drivers if d.get("trend", "neutral") == "improving"])
        driver_improvement_rate = round(improving_drivers / len(drivers), 2) if drivers else 0
        
        total_trips = sum(d.get("total_trips", 0) for d in drivers)
        completed_trips = sum(d.get("completed_trips", 0) for d in drivers)
        avg_completion_rate = round(completed_trips / total_trips, 2) if total_trips > 0 else 0
        
        metrics = {
            "violation_counts": violation_counts,
            "total_violations": total_violations,
            "active_drivers": len(drivers),
            "safety_trends": {
                "period_change": period_change,
                "violation_rate_change": violation_rate_change,
                "avg_safety_score_change": avg_safety_score_change
            },
            "key_metrics": {
                "violations_per_driver": violations_per_driver,
                "violations_per_day": violations_per_day,
                "critical_violations": critical_violations,
                "avg_safety_score": avg_safety_score,
                "driver_improvement_rate": driver_improvement_rate,
                "avg_driver_completion_rate": avg_completion_rate
            }
        }
        
        logger.info(f"[AnalyticsAPI] Performance metrics calculated: {total_violations} violations, {len(drivers)} drivers")
        
        return StandardResponse(
            status=ResponseStatus.SUCCESS,
            message="Performance metrics retrieved successfully",
            data=metrics
        )
        
    except Exception as e:
        logger.error(f"[AnalyticsAPI] Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )


@router.get("/driver-behavior/violation-comparison", response_model=StandardResponse)
async def get_violation_comparison(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    current_user: str = Depends(get_current_user)
) -> StandardResponse:
    """
    Get comparative analysis of violation types and their frequency/severity
    
    Returns detailed breakdown of violation types by frequency, severity patterns,
    and geographic distribution if location data is available.
    """
    logger.info(f"[AnalyticsAPI] Getting violation comparison for period {period}")
    
    try:
        # Parse period parameter
        days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        comparison_data = {}
        total_violations = 0
        
        # Process speeding violations
        try:
            cursor = db_manager.speed_violations.find({
                "$or": [
                    {"created_at": {"$gte": start_date}},
                    {"time": {"$gte": start_date}}
                ]
            })
            speed_violations = await cursor.to_list(length=None)
            
            if speed_violations:
                severities = [doc.get("speed", 0) - doc.get("speed_limit", 0) for doc in speed_violations]
                severities = [s for s in severities if s > 0]  # Only positive values
                
                comparison_data["speeding"] = {
                    "count": len(speed_violations),
                    "avg_severity": round(sum(severities) / len(severities), 2) if severities else 0,
                    "max_severity": max(severities) if severities else 0,
                    "severity_ranges": {
                        "minor": len([s for s in severities if 0 < s <= 10]),
                        "moderate": len([s for s in severities if 10 < s <= 20]),
                        "severe": len([s for s in severities if s > 20])
                    }
                }
            else:
                comparison_data["speeding"] = {
                    "count": 0, "avg_severity": 0, "max_severity": 0,
                    "severity_ranges": {"minor": 0, "moderate": 0, "severe": 0}
                }
            total_violations += comparison_data["speeding"]["count"]
        except Exception as e:
            logger.warning(f"Error processing speed violations: {e}")
            comparison_data["speeding"] = {
                "count": 0, "avg_severity": 0, "max_severity": 0,
                "severity_ranges": {"minor": 0, "moderate": 0, "severe": 0}
            }
        
        # Process braking violations
        try:
            cursor = db_manager.excessive_braking_violations.find({
                "$or": [
                    {"created_at": {"$gte": start_date}},
                    {"time": {"$gte": start_date}}
                ]
            })
            braking_violations = await cursor.to_list(length=None)
            
            if braking_violations:
                severities = [doc.get("deceleration", 0) - doc.get("threshold", 0) for doc in braking_violations]
                severities = [s for s in severities if s > 0]
                
                comparison_data["braking"] = {
                    "count": len(braking_violations),
                    "avg_severity": round(sum(severities) / len(severities), 2) if severities else 0,
                    "max_severity": round(max(severities), 2) if severities else 0,
                    "severity_ranges": {
                        "minor": len([s for s in severities if 0 < s <= 2]),
                        "moderate": len([s for s in severities if 2 < s <= 4]),
                        "severe": len([s for s in severities if s > 4])
                    }
                }
            else:
                comparison_data["braking"] = {
                    "count": 0, "avg_severity": 0, "max_severity": 0,
                    "severity_ranges": {"minor": 0, "moderate": 0, "severe": 0}
                }
            total_violations += comparison_data["braking"]["count"]
        except Exception as e:
            logger.warning(f"Error processing braking violations: {e}")
            comparison_data["braking"] = {
                "count": 0, "avg_severity": 0, "max_severity": 0,
                "severity_ranges": {"minor": 0, "moderate": 0, "severe": 0}
            }
        
        # Process acceleration violations
        try:
            cursor = db_manager.excessive_acceleration_violations.find({
                "$or": [
                    {"created_at": {"$gte": start_date}},
                    {"time": {"$gte": start_date}}
                ]
            })
            acceleration_violations = await cursor.to_list(length=None)
            
            if acceleration_violations:
                severities = [doc.get("acceleration", 0) - doc.get("threshold", 0) for doc in acceleration_violations]
                severities = [s for s in severities if s > 0]
                
                comparison_data["acceleration"] = {
                    "count": len(acceleration_violations),
                    "avg_severity": round(sum(severities) / len(severities), 2) if severities else 0,
                    "max_severity": round(max(severities), 2) if severities else 0,
                    "severity_ranges": {
                        "minor": len([s for s in severities if 0 < s <= 1.5]),
                        "moderate": len([s for s in severities if 1.5 < s <= 3]),
                        "severe": len([s for s in severities if s > 3])
                    }
                }
            else:
                comparison_data["acceleration"] = {
                    "count": 0, "avg_severity": 0, "max_severity": 0,
                    "severity_ranges": {"minor": 0, "moderate": 0, "severe": 0}
                }
            total_violations += comparison_data["acceleration"]["count"]
        except Exception as e:
            logger.warning(f"Error processing acceleration violations: {e}")
            comparison_data["acceleration"] = {
                "count": 0, "avg_severity": 0, "max_severity": 0,
                "severity_ranges": {"minor": 0, "moderate": 0, "severe": 0}
            }
        
        # Process phone usage violations
        try:
            cursor = db_manager.phone_usage_violations.find({
                "$or": [
                    {"created_at": {"$gte": start_date}},
                    {"time": {"$gte": start_date}}
                ]
            })
            phone_violations = await cursor.to_list(length=None)
            
            if phone_violations:
                severities = [doc.get("duration_seconds", 0) for doc in phone_violations]
                severities = [s for s in severities if s > 0]
                
                comparison_data["phone_usage"] = {
                    "count": len(phone_violations),
                    "avg_severity": round(sum(severities) / len(severities), 2) if severities else 0,
                    "max_severity": max(severities) if severities else 0,
                    "severity_ranges": {
                        "minor": len([s for s in severities if 0 < s <= 30]),
                        "moderate": len([s for s in severities if 30 < s <= 120]),
                        "severe": len([s for s in severities if s > 120])
                    }
                }
            else:
                comparison_data["phone_usage"] = {
                    "count": 0, "avg_severity": 0, "max_severity": 0,
                    "severity_ranges": {"minor": 0, "moderate": 0, "severe": 0}
                }
            total_violations += comparison_data["phone_usage"]["count"]
        except Exception as e:
            logger.warning(f"Error processing phone usage violations: {e}")
            comparison_data["phone_usage"] = {
                "count": 0, "avg_severity": 0, "max_severity": 0,
                "severity_ranges": {"minor": 0, "moderate": 0, "severe": 0}
            }
        
        # Calculate percentages
        for violation_type, data in comparison_data.items():
            if total_violations > 0:
                data["percentage"] = round((data["count"] / total_violations) * 100, 2)
            else:
                data["percentage"] = 0
        
        # Find most common violation type
        most_common = max(comparison_data.items(), key=lambda x: x[1]["count"]) if total_violations > 0 else ("none", {"count": 0})
        
        summary = {
            "total_violations": total_violations,
            "most_common_type": most_common[0],
            "most_common_count": most_common[1]["count"],
            "period_days": days,
            "violations_per_day": round(total_violations / days, 2) if days > 0 else 0
        }
        
        logger.info(f"[AnalyticsAPI] Violation comparison calculated: {total_violations} total violations")
        
        return StandardResponse(
            status=ResponseStatus.SUCCESS,
            message="Violation comparison retrieved successfully",
            data={
                "comparison": comparison_data,
                "summary": summary
            }
        )
        
    except Exception as e:
        logger.error(f"[AnalyticsAPI] Failed to get violation comparison: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve violation comparison: {str(e)}"
        )
