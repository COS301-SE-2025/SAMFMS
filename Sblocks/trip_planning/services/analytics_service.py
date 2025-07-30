"""
Analytics service for trip performance and statistics
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from repositories.database import db_manager
from schemas.entities import TripAnalytics, TripStatus
from schemas.requests import AnalyticsRequest

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for trip analytics and performance metrics"""
    
    def __init__(self):
        self.db = db_manager
        
    async def get_trip_analytics(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Get comprehensive trip analytics"""
        try:
            # Build query
            query = await self._build_analytics_query(request)
            
            # Get trip statistics
            stats = await self._calculate_trip_statistics(query, request)
            
            # Get performance metrics
            performance = await self._calculate_performance_metrics(query, request)
            
            # Get efficiency metrics
            efficiency = await self._calculate_efficiency_metrics(query, request)
            
            # Get cost metrics
            cost = await self._calculate_cost_metrics(query, request)
            
            # Get breakdown data if requested
            breakdown_data = {}
            if request.group_by:
                breakdown_data = await self._get_breakdown_data(query, request)
            
            # Combine all analytics
            analytics = {
                "period_start": request.start_date or datetime.utcnow() - timedelta(days=30),
                "period_end": request.end_date or datetime.utcnow(),
                **stats,
                **performance,
                **efficiency,
                **cost,
                **breakdown_data
            }
            
            logger.info("Generated trip analytics")
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get trip analytics: {e}")
            raise
    
    async def get_driver_performance(
        self,
        driver_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get driver performance metrics"""
        try:
            # Build query
            query = {}
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = start_date
                if end_date:
                    date_query["$lte"] = end_date
                query["scheduled_start_time"] = date_query
            
            if driver_ids:
                query["driver_assignment.driver_id"] = {"$in": driver_ids}
            else:
                # Get all drivers with trips in the period
                query["driver_assignment.driver_id"] = {"$exists": True}
            
            # Aggregate by driver
            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": "$driver_assignment.driver_id",
                        "total_trips": {"$sum": 1},
                        "completed_trips": {
                            "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                        },
                        "cancelled_trips": {
                            "$sum": {"$cond": [{"$eq": ["$status", "cancelled"]}, 1, 0]}
                        },
                        "total_planned_duration": {"$sum": "$estimated_duration"},
                        "total_actual_duration": {"$sum": "$actual_duration"},
                        "total_distance": {"$sum": "$estimated_distance"},
                        "on_time_trips": {
                            "$sum": {
                                "$cond": [
                                    {"$lte": ["$actual_start_time", "$scheduled_start_time"]},
                                    1, 0
                                ]
                            }
                        }
                    }
                }
            ]
            
            driver_stats = []
            async for driver_data in self.db.trips.aggregate(pipeline):
                driver_id = driver_data["_id"]
                total_trips = driver_data["total_trips"]
                completed_trips = driver_data["completed_trips"]
                
                performance = {
                    "driver_id": driver_id,
                    "total_trips": total_trips,
                    "completed_trips": completed_trips,
                    "cancelled_trips": driver_data["cancelled_trips"],
                    "on_time_rate": (driver_data["on_time_trips"] / total_trips * 100) if total_trips > 0 else 0,
                    "completion_rate": (completed_trips / total_trips * 100) if total_trips > 0 else 0,
                    "average_trip_duration": (
                        driver_data["total_actual_duration"] / completed_trips
                    ) if completed_trips > 0 else None,
                    "total_distance": driver_data["total_distance"]
                }
                
                # Get additional metrics from analytics data
                analytics_data = await self._get_driver_analytics_data(driver_id, start_date, end_date)
                performance.update(analytics_data)
                
                driver_stats.append(performance)
            
            return driver_stats
            
        except Exception as e:
            logger.error(f"Failed to get driver performance: {e}")
            raise
    
    async def get_route_efficiency_analysis(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Analyze route efficiency metrics"""
        try:
            query = {"status": TripStatus.COMPLETED}
            
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query["$gte"] = start_date
                if end_date:
                    date_query["$lte"] = end_date
                query["actual_end_time"] = date_query
            
            # Aggregate efficiency metrics
            pipeline = [
                {"$match": query},
                {
                    "$lookup": {
                        "from": "trip_analytics",
                        "localField": "_id",
                        "foreignField": "trip_id",
                        "as": "analytics"
                    }
                },
                {"$unwind": {"path": "$analytics", "preserveNullAndEmptyArrays": True}},
                {
                    "$group": {
                        "_id": None,
                        "total_trips": {"$sum": 1},
                        "avg_planned_duration": {"$avg": "$estimated_duration"},
                        "avg_actual_duration": {"$avg": "$analytics.actual_duration"},
                        "avg_planned_distance": {"$avg": "$estimated_distance"},
                        "avg_actual_distance": {"$avg": "$analytics.actual_distance"},
                        "total_delays": {"$sum": "$analytics.delays"},
                        "total_fuel": {"$sum": "$analytics.fuel_consumption"},
                        "total_cost": {"$sum": "$analytics.cost"}
                    }
                }
            ]
            
            result = await self.db.trips.aggregate(pipeline).to_list(length=1)
            
            if result:
                data = result[0]
                efficiency = {
                    "total_completed_trips": data["total_trips"],
                    "average_planned_duration": data["avg_planned_duration"],
                    "average_actual_duration": data["avg_actual_duration"],
                    "duration_variance": (
                        data["avg_actual_duration"] - data["avg_planned_duration"]
                    ) if data["avg_planned_duration"] else 0,
                    "average_planned_distance": data["avg_planned_distance"],
                    "average_actual_distance": data["avg_actual_distance"],
                    "distance_variance": (
                        data["avg_actual_distance"] - data["avg_planned_distance"]
                    ) if data["avg_planned_distance"] else 0,
                    "average_delay": data["total_delays"] / data["total_trips"] if data["total_trips"] > 0 else 0,
                    "fuel_efficiency": data["total_fuel"] / data["avg_actual_distance"] if data["avg_actual_distance"] else 0,
                    "cost_per_km": data["total_cost"] / data["avg_actual_distance"] if data["avg_actual_distance"] else 0
                }
            else:
                efficiency = {
                    "total_completed_trips": 0,
                    "message": "No completed trips found in the specified period"
                }
            
            return efficiency
            
        except Exception as e:
            logger.error(f"Failed to get route efficiency analysis: {e}")
            raise
    
    async def _build_analytics_query(self, request: AnalyticsRequest) -> Dict[str, Any]:
        """Build database query from analytics request"""
        query = {}
        
        # Date filters
        if request.start_date or request.end_date:
            date_query = {}
            if request.start_date:
                date_query["$gte"] = request.start_date
            if request.end_date:
                date_query["$lte"] = request.end_date
            query["scheduled_start_time"] = date_query
        
        # Entity filters
        if request.driver_ids:
            query["driver_assignment.driver_id"] = {"$in": request.driver_ids}
        
        if request.vehicle_ids:
            query["vehicle_id"] = {"$in": request.vehicle_ids}
        
        if request.trip_ids:
            query["_id"] = {"$in": [ObjectId(trip_id) for trip_id in request.trip_ids]}
        
        return query
    
    async def _calculate_trip_statistics(
        self,
        query: Dict[str, Any],
        request: AnalyticsRequest
    ) -> Dict[str, Any]:
        """Calculate basic trip statistics"""
        total_trips = await self.db.trips.count_documents(query)
        
        completed_query = {**query, "status": TripStatus.COMPLETED}
        completed_trips = await self.db.trips.count_documents(completed_query)
        
        cancelled_query = {**query, "status": TripStatus.CANCELLED}
        cancelled_trips = await self.db.trips.count_documents(cancelled_query)
        
        return {
            "total_trips": total_trips,
            "completed_trips": completed_trips,
            "cancelled_trips": cancelled_trips,
            "completion_rate": (completed_trips / total_trips * 100) if total_trips > 0 else 0
        }
    
    async def _calculate_performance_metrics(
        self,
        query: Dict[str, Any],
        request: AnalyticsRequest
    ) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if "duration" not in request.metrics:
            return {}
        
        pipeline = [
            {"$match": {**query, "status": TripStatus.COMPLETED}},
            {
                "$group": {
                    "_id": None,
                    "avg_duration": {"$avg": "$estimated_duration"},
                    "total_distance": {"$sum": "$estimated_distance"},
                    "avg_distance": {"$avg": "$estimated_distance"}
                }
            }
        ]
        
        result = await self.db.trips.aggregate(pipeline).to_list(length=1)
        
        if result:
            data = result[0]
            return {
                "average_duration": data["avg_duration"],
                "total_distance": data["total_distance"],
                "average_distance": data["avg_distance"]
            }
        
        return {}
    
    async def _calculate_efficiency_metrics(
        self,
        query: Dict[str, Any],
        request: AnalyticsRequest
    ) -> Dict[str, Any]:
        """Calculate efficiency metrics"""
        # Calculate on-time performance
        on_time_query = {
            **query,
            "status": TripStatus.COMPLETED,
            "$expr": {"$lte": ["$actual_start_time", "$scheduled_start_time"]}
        }
        
        on_time_trips = await self.db.trips.count_documents(on_time_query)
        completed_query = {**query, "status": TripStatus.COMPLETED}
        total_completed = await self.db.trips.count_documents(completed_query)
        
        return {
            "on_time_percentage": (on_time_trips / total_completed * 100) if total_completed > 0 else 0
        }
    
    async def _calculate_cost_metrics(
        self,
        query: Dict[str, Any],
        request: AnalyticsRequest
    ) -> Dict[str, Any]:
        """Calculate cost metrics"""
        if "cost" not in request.metrics:
            return {}
        
        # This would typically integrate with analytics data
        # For now, return placeholder values
        return {
            "total_cost": 0.0,
            "average_cost_per_trip": 0.0,
            "cost_per_km": 0.0
        }
    
    async def _get_breakdown_data(
        self,
        query: Dict[str, Any],
        request: AnalyticsRequest
    ) -> Dict[str, Any]:
        """Get breakdown data by specified grouping"""
        breakdown = {}
        
        if request.group_by == "driver":
            breakdown["by_driver"] = await self._get_driver_breakdown(query)
        elif request.group_by == "vehicle":
            breakdown["by_vehicle"] = await self._get_vehicle_breakdown(query)
        elif request.group_by in ["day", "week", "month"]:
            breakdown["by_period"] = await self._get_period_breakdown(query, request.group_by)
        
        return breakdown
    
    async def _get_driver_breakdown(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get breakdown by driver"""
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$driver_assignment.driver_id",
                    "trip_count": {"$sum": 1},
                    "completed_trips": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    }
                }
            }
        ]
        
        breakdown = []
        async for item in self.db.trips.aggregate(pipeline):
            breakdown.append({
                "driver_id": item["_id"],
                "trip_count": item["trip_count"],
                "completed_trips": item["completed_trips"]
            })
        
        return breakdown
    
    async def _get_vehicle_breakdown(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get breakdown by vehicle"""
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$vehicle_id",
                    "trip_count": {"$sum": 1},
                    "total_distance": {"$sum": "$estimated_distance"}
                }
            }
        ]
        
        breakdown = []
        async for item in self.db.trips.aggregate(pipeline):
            breakdown.append({
                "vehicle_id": item["_id"],
                "trip_count": item["trip_count"],
                "total_distance": item["total_distance"]
            })
        
        return breakdown
    
    async def _get_period_breakdown(
        self,
        query: Dict[str, Any],
        period: str
    ) -> List[Dict[str, Any]]:
        """Get breakdown by time period"""
        # This would implement date grouping based on the period
        # For now, return placeholder
        return []
    
    async def _get_driver_analytics_data(
        self,
        driver_id: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Get additional analytics data for a driver"""
        query = {"trip_id": {"$in": []}}  # Would need to get trip IDs for driver
        
        # Placeholder for additional metrics
        return {
            "fuel_efficiency": None,
            "safety_score": None,
            "average_rating": None
        }


# Global instance
analytics_service = AnalyticsService()
