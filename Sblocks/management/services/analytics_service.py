"""
Optimized Analytics Service with caching and background processing
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from repositories.repositories import (
    VehicleAssignmentRepository, 
    VehicleUsageLogRepository, 
    DriverRepository,
    AnalyticsRepository
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Optimized analytics service with caching"""
    
    def __init__(self):
        self.assignment_repo = VehicleAssignmentRepository()
        self.usage_repo = VehicleUsageLogRepository()
        self.driver_repo = DriverRepository()
        self.analytics_repo = AnalyticsRepository()
        
        # Cache TTL in minutes
        self.cache_ttl = {
            "fleet_utilization": 10,  # 10 minutes
            "vehicle_usage": 15,      # 15 minutes
            "assignment_metrics": 5,   # 5 minutes
            "driver_performance": 30,  # 30 minutes
            "cost_analytics": 60      # 1 hour
        }
    
    async def get_fleet_utilization(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get fleet utilization metrics"""
        metric_type = "fleet_utilization"
        
        if use_cache:
            cached = await self.analytics_repo.get_cached_metric(metric_type)
            if cached:
                logger.info(f"Returning cached {metric_type}")
                return cached["data"]
        
        logger.info(f"Calculating fresh {metric_type}")
        
        # Get assignment metrics
        assignment_metrics = await self.assignment_repo.get_assignment_metrics()
        status_breakdown = assignment_metrics.get("status_breakdown", {})
        
        total_assignments = sum(status_breakdown.values())
        active_assignments = status_breakdown.get("active", 0)
        completed_assignments = status_breakdown.get("completed", 0)
        
        utilization_rate = active_assignments / total_assignments if total_assignments > 0 else 0
        completion_rate = completed_assignments / total_assignments if total_assignments > 0 else 0
        
        data = {
            "total_assignments": total_assignments,
            "active_assignments": active_assignments,
            "completed_assignments": completed_assignments,
            "utilization_rate": round(utilization_rate, 3),
            "completion_rate": round(completion_rate, 3),
            "status_breakdown": status_breakdown,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Cache the result
        await self.analytics_repo.cache_metric(
            metric_type, 
            data, 
            self.cache_ttl[metric_type]
        )
        
        return data
    
    async def get_vehicle_usage_analytics(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get vehicle usage analytics"""
        metric_type = "vehicle_usage"
        
        if use_cache:
            cached = await self.analytics_repo.get_cached_metric(metric_type)
            if cached:
                logger.info(f"Returning cached {metric_type}")
                return cached["data"]
        
        logger.info(f"Calculating fresh {metric_type}")
        
        # Get usage statistics
        usage_stats = await self.usage_repo.get_vehicle_usage_stats()
        
        # Calculate aggregate metrics
        total_distance = sum(stat.get("total_distance", 0) for stat in usage_stats)
        total_fuel = sum(stat.get("total_fuel", 0) for stat in usage_stats)
        total_trips = sum(stat.get("trip_count", 0) for stat in usage_stats)
        
        avg_distance_per_trip = total_distance / total_trips if total_trips > 0 else 0
        avg_fuel_efficiency = total_fuel / total_distance if total_distance > 0 else 0
        
        data = {
            "vehicle_stats": usage_stats,
            "aggregate_metrics": {
                "total_distance_km": round(total_distance, 2),
                "total_fuel_consumed": round(total_fuel, 2),
                "total_trips": total_trips,
                "avg_distance_per_trip": round(avg_distance_per_trip, 2),
                "avg_fuel_efficiency": round(avg_fuel_efficiency, 4)
            },
            "top_performers": {
                "most_used": sorted(usage_stats, key=lambda x: x.get("trip_count", 0), reverse=True)[:5],
                "highest_mileage": sorted(usage_stats, key=lambda x: x.get("total_distance", 0), reverse=True)[:5],
                "most_efficient": sorted(usage_stats, key=lambda x: x.get("fuel_efficiency", 0))[:5]
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Cache the result
        await self.analytics_repo.cache_metric(
            metric_type, 
            data, 
            self.cache_ttl[metric_type]
        )
        
        return data
    
    async def get_assignment_metrics(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get assignment metrics"""
        metric_type = "assignment_metrics"
        
        if use_cache:
            cached = await self.analytics_repo.get_cached_metric(metric_type)
            if cached:
                logger.info(f"Returning cached {metric_type}")
                return cached["data"]
        
        logger.info(f"Calculating fresh {metric_type}")
        
        # Get assignment metrics from repository
        metrics = await self.assignment_repo.get_assignment_metrics()
        
        # Add timestamp
        metrics["generated_at"] = datetime.utcnow().isoformat()
        
        # Cache the result
        await self.analytics_repo.cache_metric(
            metric_type, 
            metrics, 
            self.cache_ttl[metric_type]
        )
        
        return metrics
    
    async def get_driver_performance(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get driver performance analytics"""
        metric_type = "driver_performance"
        
        if use_cache:
            cached = await self.analytics_repo.get_cached_metric(metric_type)
            if cached:
                logger.info(f"Returning cached {metric_type}")
                return cached["data"]
        
        logger.info(f"Calculating fresh {metric_type}")
        
        # Get driver performance stats
        performance_stats = await self.usage_repo.get_driver_performance_stats()
        
        # Get driver counts by status
        active_drivers = await self.driver_repo.count({"status": "active"})
        total_drivers = await self.driver_repo.count({})
        
        # Calculate aggregate metrics
        total_distance = sum(stat.get("total_distance", 0) for stat in performance_stats)
        total_trips = sum(stat.get("trip_count", 0) for stat in performance_stats)
        
        avg_distance_per_driver = total_distance / len(performance_stats) if performance_stats else 0
        avg_trips_per_driver = total_trips / len(performance_stats) if performance_stats else 0
        
        data = {
            "driver_stats": performance_stats,
            "summary": {
                "total_drivers": total_drivers,
                "active_drivers": active_drivers,
                "drivers_with_activity": len(performance_stats),
                "avg_distance_per_driver": round(avg_distance_per_driver, 2),
                "avg_trips_per_driver": round(avg_trips_per_driver, 2)
            },
            "top_performers": {
                "most_trips": sorted(performance_stats, key=lambda x: x.get("trip_count", 0), reverse=True)[:5],
                "highest_distance": sorted(performance_stats, key=lambda x: x.get("total_distance", 0), reverse=True)[:5]
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Cache the result
        await self.analytics_repo.cache_metric(
            metric_type, 
            data, 
            self.cache_ttl[metric_type]
        )
        
        return data
    
    async def get_dashboard_summary(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get dashboard summary with key metrics"""
        try:
            # Get all key metrics concurrently
            fleet_util, vehicle_usage, assignment_metrics, driver_perf = await asyncio.gather(
                self.get_fleet_utilization(use_cache),
                self.get_vehicle_usage_analytics(use_cache),
                self.get_assignment_metrics(use_cache),
                self.get_driver_performance(use_cache),
                return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(fleet_util, Exception):
                logger.error(f"Fleet utilization error: {fleet_util}")
                fleet_util = {}
            
            if isinstance(vehicle_usage, Exception):
                logger.error(f"Vehicle usage error: {vehicle_usage}")
                vehicle_usage = {}
            
            if isinstance(assignment_metrics, Exception):
                logger.error(f"Assignment metrics error: {assignment_metrics}")
                assignment_metrics = {}
            
            if isinstance(driver_perf, Exception):
                logger.error(f"Driver performance error: {driver_perf}")
                driver_perf = {}
            
            return {
                "fleet_utilization": fleet_util,
                "vehicle_usage": vehicle_usage,
                "assignment_metrics": assignment_metrics,
                "driver_performance": driver_perf,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating dashboard summary: {e}")
            raise
    
    async def refresh_all_cache(self):
        """Refresh all cached analytics"""
        logger.info("Refreshing all analytics cache")
        
        try:
            await asyncio.gather(
                self.get_fleet_utilization(use_cache=False),
                self.get_vehicle_usage_analytics(use_cache=False),
                self.get_assignment_metrics(use_cache=False),
                self.get_driver_performance(use_cache=False),
                return_exceptions=True
            )
            logger.info("Successfully refreshed all analytics cache")
            
        except Exception as e:
            logger.error(f"Error refreshing analytics cache: {e}")
    
    async def cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        try:
            deleted_count = await self.analytics_repo.cleanup_expired()
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired analytics cache entries")
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")


# Global analytics service instance
analytics_service = AnalyticsService()
