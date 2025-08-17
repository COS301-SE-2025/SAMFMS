"""
Maintenance Analytics Service
Provides analytics and reporting for maintenance operations
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
from collections import defaultdict

from repositories import (
    MaintenanceRecordsRepository, 
    LicenseRecordsRepository,
    MaintenanceVendorsRepository
)

logger = logging.getLogger(__name__)


class MaintenanceAnalyticsService:
    """Service for maintenance analytics and reporting"""
    
    def __init__(self):
        self.maintenance_repo = MaintenanceRecordsRepository()
        self.license_repo = LicenseRecordsRepository()
        self.vendor_repo = MaintenanceVendorsRepository()
        
    async def get_maintenance_dashboard(self) -> Dict[str, Any]:
        """Get dashboard overview data"""
        try:
            now = datetime.utcnow()
            thirty_days_ago = now - timedelta(days=30)
            
            # Get key metrics
            total_vehicles = await self._get_vehicle_count()
            
            # Maintenance metrics
            overdue_count = len(await self.maintenance_repo.get_overdue_maintenance())
            upcoming_count = len(await self.maintenance_repo.get_upcoming_maintenance(7))
            
            # Cost metrics for last 30 days
            cost_summary = await self.maintenance_repo.get_cost_summary(
                start_date=thirty_days_ago, end_date=now
            )
            
            # License metrics
            expiring_licenses = len(await self.license_repo.get_expiring_soon(30))
            expired_licenses = len(await self.license_repo.get_expired_licenses())
            
            # Recent maintenance activity
            recent_maintenance = await self.maintenance_repo.find(
                query={"created_at": {"$gte": thirty_days_ago}},
                limit=10,
                sort=[("created_at", -1)]
            )
            
            return {
                "overview": {
                    "total_vehicles": total_vehicles,
                    "overdue_maintenance": overdue_count,
                    "upcoming_maintenance": upcoming_count,
                    "expiring_licenses": expiring_licenses,
                    "expired_licenses": expired_licenses
                },
                "costs": {
                    "total_cost_last_30_days": cost_summary.get("total_cost", 0),
                    "average_cost": cost_summary.get("average_cost", 0),
                    "total_jobs": cost_summary.get("maintenance_count", 0)
                },
                "recent_activity": recent_maintenance
            }
            
        except Exception as e:
            logger.error(f"Error generating maintenance dashboard: {e}")
            raise
            
    async def get_cost_analytics(self, 
                                vehicle_id: Optional[str] = None,
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None,
                                group_by: str = "month") -> Dict[str, Any]:
        """Get cost analytics with time-based grouping"""
        try:
            # Parse dates
            start_dt = None
            end_dt = None
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            else:
                start_dt = datetime.utcnow() - timedelta(days=365)  # Default to last year
                
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            else:
                end_dt = datetime.utcnow()
                
            # Build aggregation pipeline
            pipeline = [
                {
                    "$match": {
                        "status": "completed",
                        "completed_date": {
                            "$gte": start_dt,
                            "$lte": end_dt
                        }
                    }
                }
            ]
            
            if vehicle_id:
                pipeline[0]["$match"]["vehicle_id"] = vehicle_id
                
            # Group by time period
            if group_by == "month":
                group_format = {
                    "year": {"$year": "$completed_date"},
                    "month": {"$month": "$completed_date"}
                }
            elif group_by == "week":
                group_format = {
                    "year": {"$year": "$completed_date"},
                    "week": {"$week": "$completed_date"}
                }
            else:  # day
                group_format = {
                    "year": {"$year": "$completed_date"},
                    "month": {"$month": "$completed_date"},
                    "day": {"$dayOfMonth": "$completed_date"}
                }
                
            pipeline.extend([
                {
                    "$group": {
                        "_id": group_format,
                        "total_cost": {"$sum": "$actual_cost"},
                        "labor_cost": {"$sum": "$labor_cost"},
                        "parts_cost": {"$sum": "$parts_cost"},
                        "maintenance_count": {"$sum": 1},
                        "average_cost": {"$avg": "$actual_cost"}
                    }
                },
                {"$sort": {"_id": 1}}
            ])
            
            results = await self.maintenance_repo.aggregate(pipeline)
            
            # Get overall summary
            total_pipeline = [
                {
                    "$match": {
                        "status": "completed",
                        "completed_date": {
                            "$gte": start_dt,
                            "$lte": end_dt
                        }
                    }
                }
            ]
            
            if vehicle_id:
                total_pipeline[0]["$match"]["vehicle_id"] = vehicle_id
                
            total_pipeline.append({
                "$group": {
                    "_id": None,
                    "total_cost": {"$sum": "$actual_cost"},
                    "total_labor_cost": {"$sum": "$labor_cost"},
                    "total_parts_cost": {"$sum": "$parts_cost"},
                    "total_maintenance_count": {"$sum": 1},
                    "average_cost": {"$avg": "$actual_cost"}
                }
            })
            
            summary_results = await self.maintenance_repo.aggregate(total_pipeline)
            summary = summary_results[0] if summary_results else {}
            
            return {
                "time_series": results,
                "summary": summary,
                "group_by": group_by,
                "date_range": {
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating cost analytics: {e}")
            raise
            
    async def get_maintenance_trends(self, days: int = 90) -> Dict[str, Any]:
        """Get maintenance trends over time"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Maintenance by type
            type_pipeline = [
                {
                    "$match": {
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$maintenance_type",
                        "count": {"$sum": 1},
                        "avg_cost": {"$avg": "$actual_cost"}
                    }
                },
                {"$sort": {"count": -1}}
            ]
            
            maintenance_by_type = await self.maintenance_repo.aggregate(type_pipeline)
            
            # Maintenance by status
            status_pipeline = [
                {
                    "$match": {
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            maintenance_by_status = await self.maintenance_repo.aggregate(status_pipeline)
            
            # Top vehicles by maintenance count
            vehicle_pipeline = [
                {
                    "$match": {
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$vehicle_id",
                        "maintenance_count": {"$sum": 1},
                        "total_cost": {"$sum": "$actual_cost"}
                    }
                },
                {"$sort": {"maintenance_count": -1}},
                {"$limit": 10}
            ]
            
            top_vehicles = await self.maintenance_repo.aggregate(vehicle_pipeline)
            
            return {
                "period_days": days,
                "maintenance_by_type": maintenance_by_type,
                "maintenance_by_status": maintenance_by_status,
                "top_vehicles": top_vehicles
            }
            
        except Exception as e:
            logger.error(f"Error generating maintenance trends: {e}")
            raise
            
    async def get_vendor_analytics(self) -> Dict[str, Any]:
        """Get vendor performance analytics"""
        try:
            # Get all active vendors
            vendors = await self.vendor_repo.get_active_vendors()
            
            # Get vendor performance metrics
            vendor_performance = []
            for vendor in vendors:
                vendor_id = vendor["id"]
                
                # Get maintenance records for this vendor
                maintenance_records = await self.maintenance_repo.find(
                    query={"vendor_id": vendor_id, "status": "completed"},
                    limit=1000
                )
                
                if maintenance_records:
                    total_jobs = len(maintenance_records)
                    total_cost = sum(record.get("actual_cost", 0) for record in maintenance_records)
                    avg_cost = total_cost / total_jobs if total_jobs > 0 else 0
                    
                    # Calculate average duration
                    durations = []
                    for record in maintenance_records:
                        if record.get("actual_start_date") and record.get("actual_completion_date"):
                            start = record["actual_start_date"]
                            end = record["actual_completion_date"]
                            if isinstance(start, str):
                                start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                            if isinstance(end, str):
                                end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                            duration = (end - start).total_seconds() / 3600  # hours
                            durations.append(duration)
                    
                    avg_duration = sum(durations) / len(durations) if durations else 0
                    
                    vendor_performance.append({
                        "vendor_id": vendor_id,
                        "vendor_name": vendor["name"],
                        "total_jobs": total_jobs,
                        "total_cost": total_cost,
                        "average_cost": avg_cost,
                        "average_duration_hours": avg_duration,
                        "rating": vendor.get("rating", 0)
                    })
                    
            # Sort by total jobs
            vendor_performance.sort(key=lambda x: x["total_jobs"], reverse=True)
            
            return {
                "total_vendors": len(vendors),
                "active_vendors": len([v for v in vendors if v.get("is_active", True)]),
                "preferred_vendors": len([v for v in vendors if v.get("is_preferred", False)]),
                "vendor_performance": vendor_performance
            }
            
        except Exception as e:
            logger.error(f"Error generating vendor analytics: {e}")
            raise
            
    async def get_license_analytics(self) -> Dict[str, Any]:
        """Get license expiry analytics"""
        try:
            today = date.today()
            
            # Get license counts by type
            type_pipeline = [
                {"$match": {"is_active": True}},
                {
                    "$group": {
                        "_id": "$license_type",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}}
            ]
            
            licenses_by_type = await self.license_repo.aggregate(type_pipeline)
            
            # Get expiry timeline
            expiry_periods = [
                ("expired", {"$lt": today}),
                ("expiring_7_days", {"$gte": today, "$lte": today + timedelta(days=7)}),
                ("expiring_30_days", {"$gte": today, "$lte": today + timedelta(days=30)}),
                ("expiring_90_days", {"$gte": today, "$lte": today + timedelta(days=90)}),
            ]
            
            expiry_timeline = {}
            for period_name, date_filter in expiry_periods:
                count = await self.license_repo.count({
                    "is_active": True,
                    "expiry_date": date_filter
                })
                expiry_timeline[period_name] = count
                
            # Get licenses by entity type
            entity_pipeline = [
                {"$match": {"is_active": True}},
                {
                    "$group": {
                        "_id": "$entity_type",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            licenses_by_entity = await self.license_repo.aggregate(entity_pipeline)
            
            return {
                "licenses_by_type": licenses_by_type,
                "expiry_timeline": expiry_timeline,
                "licenses_by_entity": licenses_by_entity,
                "total_active_licenses": await self.license_repo.count({"is_active": True})
            }
            
        except Exception as e:
            logger.error(f"Error generating license analytics: {e}")
            raise
            
    async def _get_vehicle_count(self) -> int:
        """Get total vehicle count (placeholder - would integrate with vehicle service)"""
        # This would typically make a call to the vehicle service
        # For now, return a count based on unique vehicle IDs in maintenance records
        try:
            pipeline = [
                {"$group": {"_id": "$vehicle_id"}},
                {"$count": "total"}
            ]
            result = await self.maintenance_repo.aggregate(pipeline)
            return result[0]["total"] if result else 0
        except:
            return 0

    async def get_total_cost_timeframe(self, start_date: str, end_date: str) -> float:
        """Get total maintenance cost within a specific timeframe"""
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            pipeline = [
                {
                    "$match": {
                        "created_at": {
                            "$gte": start_dt,
                            "$lte": end_dt
                        },
                        "$or": [
                            {"actual_cost": {"$exists": True, "$ne": None}},
                            {"estimated_cost": {"$exists": True, "$ne": None}},
                            {"cost": {"$exists": True, "$ne": None}}
                        ]
                    }
                },
                {
                    "$addFields": {
                        "cost_value": {
                            "$cond": {
                                "if": {"$ne": ["$actual_cost", None]},
                                "then": "$actual_cost",
                                "else": {
                                    "$cond": {
                                        "if": {"$ne": ["$estimated_cost", None]},
                                        "then": "$estimated_cost",
                                        "else": {"$ifNull": ["$cost", 0]}
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_cost": {"$sum": "$cost_value"}
                    }
                }
            ]
            
            result = await self.maintenance_repo.aggregate(pipeline)
            return float(result[0]["total_cost"]) if result else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating total cost for timeframe: {e}")
            raise

    async def get_records_count_timeframe(self, start_date: str, end_date: str) -> int:
        """Get number of maintenance records within a specific timeframe"""
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            count = await self.maintenance_repo.count({
                "created_at": {
                    "$gte": start_dt,
                    "$lte": end_dt
                }
            })
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting records for timeframe: {e}")
            raise

    async def get_vehicles_serviced_timeframe(self, start_date: str, end_date: str) -> int:
        """Get number of unique vehicles serviced within a specific timeframe"""
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            pipeline = [
                {
                    "$match": {
                        "created_at": {
                            "$gte": start_dt,
                            "$lte": end_dt
                        },
                        "vehicle_id": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": "$vehicle_id"
                    }
                },
                {
                    "$count": "unique_vehicles"
                }
            ]
            
            result = await self.maintenance_repo.aggregate(pipeline)
            return result[0]["unique_vehicles"] if result else 0
            
        except Exception as e:
            logger.error(f"Error counting unique vehicles serviced for timeframe: {e}")
            raise

    async def get_maintenance_records_by_type(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get maintenance records grouped by maintenance type"""
        try:
            match_criteria = {"maintenance_type": {"$exists": True, "$ne": None}}
            
            if start_date and end_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                match_criteria["created_at"] = {"$gte": start_dt, "$lte": end_dt}
            
            pipeline = [
                {"$match": match_criteria},
                {
                    "$group": {
                        "_id": "$maintenance_type",
                        "count": {"$sum": 1},
                        "total_cost": {
                            "$sum": {
                                "$cond": {
                                    "if": {"$ne": ["$actual_cost", None]},
                                    "then": "$actual_cost",
                                    "else": {
                                        "$cond": {
                                            "if": {"$ne": ["$estimated_cost", None]},
                                            "then": "$estimated_cost",
                                            "else": {"$ifNull": ["$cost", 0]}
                                        }
                                    }
                                }
                            }
                        },
                        "average_cost": {
                            "$avg": {
                                "$cond": {
                                    "if": {"$ne": ["$actual_cost", None]},
                                    "then": "$actual_cost",
                                    "else": {
                                        "$cond": {
                                            "if": {"$ne": ["$estimated_cost", None]},
                                            "then": "$estimated_cost",
                                            "else": {"$ifNull": ["$cost", 0]}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    "$sort": {"count": -1}
                },
                {
                    "$project": {
                        "maintenance_type": "$_id",
                        "count": 1,
                        "total_cost": {"$round": ["$total_cost", 2]},
                        "average_cost": {"$round": ["$average_cost", 2]},
                        "_id": 0
                    }
                }
            ]
            
            result = await self.maintenance_repo.aggregate(pipeline)
            return result
            
        except Exception as e:
            logger.error(f"Error getting maintenance records by type: {e}")
            raise

    async def get_maintenance_cost_outliers(self, start_date: Optional[str] = None, end_date: Optional[str] = None, threshold_multiplier: float = 2.0) -> Dict[str, Any]:
        """Get maintenance records with outlier costs (significantly above average)"""
        try:
            match_criteria = {
                "$or": [
                    {"actual_cost": {"$exists": True, "$ne": None, "$gt": 0}},
                    {"estimated_cost": {"$exists": True, "$ne": None, "$gt": 0}},
                    {"cost": {"$exists": True, "$ne": None, "$gt": 0}}
                ]
            }
            
            if start_date and end_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                match_criteria["created_at"] = {"$gte": start_dt, "$lte": end_dt}
            
            # First, get the average cost
            avg_pipeline = [
                {"$match": match_criteria},
                {
                    "$addFields": {
                        "cost_value": {
                            "$cond": {
                                "if": {"$ne": ["$actual_cost", None]},
                                "then": "$actual_cost",
                                "else": {
                                    "$cond": {
                                        "if": {"$ne": ["$estimated_cost", None]},
                                        "then": "$estimated_cost",
                                        "else": {"$ifNull": ["$cost", 0]}
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "average_cost": {"$avg": "$cost_value"},
                        "total_records": {"$sum": 1}
                    }
                }
            ]
            
            avg_result = await self.maintenance_repo.aggregate(avg_pipeline)
            if not avg_result:
                return {"outliers": [], "statistics": {"average_cost": 0, "threshold": 0, "total_records": 0}}
            
            average_cost = avg_result[0]["average_cost"]
            total_records = avg_result[0]["total_records"]
            threshold = average_cost * threshold_multiplier
            
            # Now get the outliers
            outlier_pipeline = [
                {"$match": match_criteria},
                {
                    "$addFields": {
                        "cost_value": {
                            "$cond": {
                                "if": {"$ne": ["$actual_cost", None]},
                                "then": "$actual_cost",
                                "else": {
                                    "$cond": {
                                        "if": {"$ne": ["$estimated_cost", None]},
                                        "then": "$estimated_cost",
                                        "else": {"$ifNull": ["$cost", 0]}
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    "$match": {
                        "cost_value": {"$gte": threshold}
                    }
                },
                {
                    "$project": {
                        "id": {"$toString": "$_id"},
                        "vehicle_id": 1,
                        "maintenance_type": 1,
                        "title": 1,
                        "cost": "$cost_value",
                        "created_at": 1,
                        "cost_multiplier": {
                            "$round": [{"$divide": ["$cost_value", average_cost]}, 2]
                        }
                    }
                },
                {
                    "$sort": {"cost": -1}
                }
            ]
            
            outliers = await self.maintenance_repo.aggregate(outlier_pipeline)
            
            return {
                "outliers": outliers,
                "statistics": {
                    "average_cost": round(average_cost, 2),
                    "threshold": round(threshold, 2),
                    "threshold_multiplier": threshold_multiplier,
                    "total_records": total_records,
                    "outlier_count": len(outliers)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting maintenance cost outliers: {e}")
            raise

    async def get_maintenance_per_vehicle_timeframe(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get number of maintenance records per vehicle within a specific timeframe"""
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            pipeline = [
                {
                    "$match": {
                        "created_at": {
                            "$gte": start_dt,
                            "$lte": end_dt
                        },
                        "vehicle_id": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": "$vehicle_id",
                        "maintenance_count": {"$sum": 1},
                        "total_cost": {
                            "$sum": {
                                "$cond": {
                                    "if": {"$ne": ["$actual_cost", None]},
                                    "then": "$actual_cost",
                                    "else": {
                                        "$cond": {
                                            "if": {"$ne": ["$estimated_cost", None]},
                                            "then": "$estimated_cost",
                                            "else": {"$ifNull": ["$cost", 0]}
                                        }
                                    }
                                }
                            }
                        },
                        "maintenance_types": {
                            "$addToSet": "$maintenance_type"
                        },
                        "latest_maintenance": {"$max": "$created_at"},
                        "earliest_maintenance": {"$min": "$created_at"}
                    }
                },
                {
                    "$sort": {"maintenance_count": -1}
                },
                {
                    "$project": {
                        "vehicle_id": "$_id",
                        "maintenance_count": 1,
                        "total_cost": {"$round": ["$total_cost", 2]},
                        "average_cost": {"$round": [{"$divide": ["$total_cost", "$maintenance_count"]}, 2]},
                        "maintenance_types": 1,
                        "types_count": {"$size": "$maintenance_types"},
                        "latest_maintenance": 1,
                        "earliest_maintenance": 1,
                        "_id": 0
                    }
                }
            ]
            
            result = await self.maintenance_repo.aggregate(pipeline)
            return result
            
        except Exception as e:
            logger.error(f"Error getting maintenance per vehicle for timeframe: {e}")
            raise
    
    async def get_maintenance_per_vehicle_timeframe(self, 
                                                    start_date: str, 
                                                    end_date: str) -> List[Dict[str, Any]]:
        """Get maintenance records per vehicle within a specific timeframe"""
        try:
            # Parse dates
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            
            pipeline = [
                {
                    "$match": {
                        "created_at": {
                            "$gte": start_dt,
                            "$lte": end_dt
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$vehicle_id",
                        "maintenance_count": {"$sum": 1},
                        "total_cost": {
                            "$sum": {
                                "$cond": {
                                    "if": {"$ne": ["$actual_cost", None]},
                                    "then": "$actual_cost",
                                    "else": {
                                        "$cond": {
                                            "if": {"$ne": ["$estimated_cost", None]},
                                            "then": "$estimated_cost",
                                            "else": {"$ifNull": ["$cost", 0]}
                                        }
                                    }
                                }
                            }
                        },
                        "maintenance_types": {
                            "$addToSet": "$maintenance_type"
                        },
                        "latest_maintenance": {"$max": "$created_at"},
                        "earliest_maintenance": {"$min": "$created_at"}
                    }
                },
                {
                    "$sort": {"maintenance_count": -1}
                },
                {
                    "$project": {
                        "vehicle_id": "$_id",
                        "maintenance_count": 1,
                        "total_cost": {"$round": ["$total_cost", 2]},
                        "average_cost": {"$round": [{"$divide": ["$total_cost", "$maintenance_count"]}, 2]},
                        "maintenance_types": 1,
                        "types_count": {"$size": "$maintenance_types"},
                        "latest_maintenance": 1,
                        "earliest_maintenance": 1,
                        "_id": 0
                    }
                }
            ]
            
            result = await self.maintenance_repo.aggregate(pipeline)
            return result
            
        except Exception as e:
            logger.error(f"Error getting maintenance per vehicle for timeframe: {e}")
            raise


# Global service instance
maintenance_analytics_service = MaintenanceAnalyticsService()

# Alias for backward compatibility
analytics_service = maintenance_analytics_service
