"""
Analytics service for trip performance and statistics
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from bson import ObjectId

from repositories.database import db_manager, db_manager_management
from schemas.entities import TripAnalytics, TripStatus
from schemas.requests import AnalyticsRequest

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for trip analytics and performance metrics"""
    
    def __init__(self):
        self.db = db_manager
    
    async def _get_driver_names(driver_ids: List[str]) -> Dict[str, str]:
        """
        Get driver names from driver IDs.
        """
        try:
            if not driver_ids:
                return {}
                
            # Convert to ObjectIds if they are valid ObjectId strings, otherwise keep as strings
            query_ids = []
            for driver_id in driver_ids:
                if len(driver_id) == 24:  # Standard ObjectId length
                    try:
                        query_ids.append(ObjectId(driver_id))
                    except:
                        query_ids.append(driver_id)
                else:
                    query_ids.append(driver_id)
            
            # Query drivers collection - adjust field names based on your schema
            drivers_cursor = db_manager_management.drivers.find(
                {"_id": {"$in": query_ids}},
                {"first_name": 1, "last_name": 1}
            )
            
            drivers_data = await drivers_cursor.to_list(None)
            driver_names = {}
            
            for driver in drivers_data:
                driver_id = str(driver["_id"])
                
                # Try different name field combinations based on your schema
                name = (
                    f"{driver.get('first_name', '')} {driver.get('last_name', '')}".strip()
                )
                
                driver_names[driver_id] = name
            
            # Add default names for drivers not found in the drivers collection
            for original_id in driver_ids:
                if original_id not in driver_names:
                    driver_names[original_id] = f"Driver {original_id}"
            
            return driver_names
            
        except Exception as e:
            logger.warning(f"Failed to get driver names: {e}")
            # Return default names
            return {driver_id: f"Driver {driver_id}" for driver_id in driver_ids}
    
    async def get_analytics_first(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Retrieve analytics for trips within the specified date range from trip_history collection.
        """
        try:
            logger.info(f"[DriverAnalytics] Starting analytics calculation for period: {start_date} to {end_date}")
            
            # Ensure dates are timezone-aware (UTC)
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            
            logger.info(f"[DriverAnalytics] Executing MongoDB aggregation pipeline")
            # MongoDB aggregation pipeline
            pipeline = [
                # Match trips within the date range
                {
                    "$match": {
                        "moved_to_history_at": {
                            "$gte": start_date,
                            "$lte": end_date
                        }
                    }
                },
                # Add calculated fields
                {
                    "$addFields": {
                        "trip_duration_hours": {
                            "$cond": {
                                "if": {"$and": ["$actual_start_time", "$actual_end_time"]},
                                "then": {
                                    "$divide": [
                                        {"$subtract": ["$actual_end_time", "$actual_start_time"]},
                                        3600000  # Convert milliseconds to hours
                                    ]
                                },
                                "else": 0
                            }
                        },
                        "is_completed": {"$eq": ["$status", "completed"]},
                        "is_cancelled": {"$eq": ["$status", "cancelled"]}
                    }
                },
                # Group by driver
                {
                    "$group": {
                        "_id": "$driver_assignment",
                        "completedTrips": {"$sum": {"$cond": ["$is_completed", 1, 0]}},
                        "cancelledTrips": {"$sum": {"$cond": ["$is_cancelled", 1, 0]}},
                        "totalHours": {"$sum": "$trip_duration_hours"},
                        "totalTrips": {"$sum": 1}
                    }
                },
                # Sort by driver ID
                {"$sort": {"_id": 1}}
            ]
            
            # Execute aggregation
            driver_results = await db_manager.trip_history.aggregate(pipeline).to_list(None)
            logger.info(f"[DriverAnalytics] Found {len(driver_results)} driver results")
            
            # Get driver names
            logger.info("[DriverAnalytics] Fetching driver names")
            driver_names = self._get_driver_names([result["_id"] for result in driver_results if result["_id"]])
            
            # Format driver analytics
            drivers = []
            total_trips = 0
            total_completed = 0
            
            logger.info("[DriverAnalytics] Processing individual driver statistics")
            for result in driver_results:
                driver_id = result["_id"]
                if not driver_id:
                    logger.debug("[DriverAnalytics] Skipping entry without driver_id")
                    continue
                
                driver_stats = {
                    "driverId": driver_id,
                    "driverName": driver_names.get(driver_id, f"Driver {driver_id}"),
                    "completedTrips": result["completedTrips"],
                    "cancelledTrips": result["cancelledTrips"],
                    "totalHours": round(result["totalHours"], 2)
                }
                logger.debug(f"[DriverAnalytics] Processed stats for driver {driver_id}: {driver_stats}")
                drivers.append(driver_stats)
                
                total_trips += result["totalTrips"]
                total_completed += result["completedTrips"]
            
            # Calculate timeframe summary
            logger.info("[DriverAnalytics] Calculating timeframe summary")
            completion_rate = round((total_completed / total_trips * 100), 2) if total_trips > 0 else 0.0
            days_in_range = (end_date - start_date).days + 1
            average_trips_per_day = round((total_trips / days_in_range), 2) if days_in_range > 0 else 0.0
            
            response_data = {
                "drivers": drivers,
                "timeframeSummary": {
                    "totalTrips": total_trips,
                    "completionRate": completion_rate,
                    "averageTripsPerDay": average_trips_per_day
                }
            }
            
            logger.info(f"[DriverAnalytics] Completed successfully. Total drivers: {len(drivers)}")
            logger.debug(f"[DriverAnalytics] Response data: {response_data}")
            return response_data
        
        except Exception as e:
            logger.error(f"[DriverAnalytics] Error calculating analytics: {str(e)}", exc_info=True)
            return {
                "drivers": [],
                "timeframeSummary": {
                    "totalTrips": 0,
                    "completionRate": 0.0,
                    "averageTripsPerDay": 0.0
                }
            }

    async def get_analytics_second(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Retrieve vehicle analytics for trips within the specified date range.
        """
        try:
            logger.info(f"[VehicleAnalytics] Starting analytics calculation for period: {start_date} to {end_date}")
            
            # Ensure dates are timezone-aware (UTC)
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            
            logger.info("[VehicleAnalytics] Executing MongoDB aggregation pipeline")
            # MongoDB aggregation pipeline
            pipeline = [
                # Match trips within the date range
                {
                    "$match": {
                        "moved_to_history_at": {
                            "$gte": start_date,
                            "$lte": end_date
                        }
                    }
                },
                # Add calculated fields for distance
                {
                    "$addFields": {
                        "trip_distance": {
                            "$cond": {
                                "if": {"$gt": [{"$ifNull": ["$estimated_distance", 0]}, 0]},
                                "then": "$estimated_distance",
                                "else": {
                                    "$cond": {
                                        "if": {"$gt": [{"$ifNull": ["$actual_distance", 0]}, 0]},
                                        "then": "$actual_distance",
                                        "else": 0
                                    }
                                }
                            }
                        }
                    }
                },
                # Group by vehicle
                {
                    "$group": {
                        "_id": "$vehicle_id",
                        "totalTrips": {"$sum": 1},
                        "totalDistance": {"$sum": "$trip_distance"}
                    }
                },
                # Sort by vehicle ID
                {"$sort": {"_id": 1}}
            ]
            
            # Execute aggregation
            vehicle_results = await db_manager.trip_history.aggregate(pipeline).to_list(None)
            logger.info(f"[VehicleAnalytics] Found {len(vehicle_results)} vehicle results")
            
            # Format vehicle analytics
            vehicles = []
            total_distance_sum = 0
            
            logger.info("[VehicleAnalytics] Processing individual vehicle statistics")
            for result in vehicle_results:
                vehicle_id = result["_id"]
                if not vehicle_id:
                    logger.debug("[VehicleAnalytics] Skipping entry without vehicle_id")
                    continue
                
                total_trips = result["totalTrips"]
                total_distance = round(result["totalDistance"], 2)
                
                vehicle_stats = {
                    "vehicleId": vehicle_id,
                    "totalTrips": total_trips,
                    "totalDistance": total_distance
                }
                logger.debug(f"[VehicleAnalytics] Processed stats for vehicle {vehicle_id}: {vehicle_stats}")
                vehicles.append(vehicle_stats)
                
                total_distance_sum += total_distance
            
            response_data = {
                "vehicles": vehicles,
                "timeframeSummary": {
                    "totalDistance": round(total_distance_sum, 2)
                }
            }
            
            logger.info(f"[VehicleAnalytics] Completed successfully. Total vehicles: {len(vehicles)}")
            logger.debug(f"[VehicleAnalytics] Response data: {response_data}")
            return response_data
        
        except Exception as e:
            logger.error(f"[VehicleAnalytics] Error calculating analytics: {str(e)}", exc_info=True)
            return {
                "vehicles": [],
                "timeframeSummary": {
                    "totalDistance": 0
                }
            }

    async def get_vehicle_analytics_with_route_distance(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Alternative version that calculates distance from route coordinates if distance fields are not available.
        This uses the Haversine formula to calculate distance from origin to destination coordinates.
        """
        try:
            # Ensure dates are timezone-aware (UTC)
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            
            # Get all trips in the date range
            query = {
                "moved_to_history_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            trips = await db_manager.trip_history.find(query).to_list(None)
            
            # Process each trip to calculate distances and group by vehicle
            vehicle_stats = {}
            
            for trip in trips:
                vehicle_id = trip.get("vehicle_id")
                if not vehicle_id:
                    continue
                
                if vehicle_id not in vehicle_stats:
                    vehicle_stats[vehicle_id] = {
                        "totalTrips": 0,
                        "totalDistance": 0
                    }
                
                vehicle_stats[vehicle_id]["totalTrips"] += 1
                
                # Try to get distance from stored fields first
                distance = 0
                #if trip.get("estimated_distance"):
                 #   distance = trip["estimated_distance"]
                #elif trip.get("actual_distance"):
                 #   distance = trip["actual_distance"]
                #else:
                    # Calculate from coordinates if available
                distance = self._calculate_trip_distance(trip)
                
                vehicle_stats[vehicle_id]["totalDistance"] += distance
            
            # Format results
            vehicles = []
            total_distance_sum = 0
            
            for vehicle_id, stats in vehicle_stats.items():
                total_distance = round(stats["totalDistance"], 2)
                
                vehicles.append({
                    "vehicleId": vehicle_id,
                    "totalTrips": stats["totalTrips"],
                    "totalDistance": total_distance
                })
                
                total_distance_sum += total_distance
            
            # Sort by vehicle ID
            vehicles.sort(key=lambda x: x["vehicleId"])
            
            return {
                "vehicles": vehicles,
                "timeframeSummary": {
                    "totalDistance": round(total_distance_sum, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get vehicle analytics with route distance: {e}")
            return {
                "vehicles": [],
                "timeframeSummary": {
                    "totalDistance": 0
                }
            }

    def _calculate_trip_distance(trip: Dict[str, Any]) -> float:
        """
        Calculate trip distance from origin/destination coordinates using Haversine formula.
        
        Args:
            trip: Trip document with origin and destination coordinates
        
        Returns:
            Distance in kilometers
        """
        try:
            origin = trip.get("origin", {})
            destination = trip.get("destination", {})
            
            origin_coords = origin.get("location", {}).get("coordinates", [])
            dest_coords = destination.get("location", {}).get("coordinates", [])
            
            if len(origin_coords) < 2 or len(dest_coords) < 2:
                return 0
            
            # Coordinates are in [longitude, latitude] format (GeoJSON)
            lon1, lat1 = origin_coords[0], origin_coords[1]
            lon2, lat2 = dest_coords[0], dest_coords[1]
            
            # Haversine formula
            import math
            
            R = 6371  # Earth's radius in kilometers
            
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lon = math.radians(lon2 - lon1)
            
            a = (math.sin(delta_lat / 2) ** 2 + 
                math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
            distance = R * c
            
            # Add waypoint distances if they exist
            waypoints = trip.get("waypoints", [])
            if waypoints:
                all_points = [origin_coords] + [wp.get("location", {}).get("coordinates", []) for wp in waypoints] + [dest_coords]
                total_distance = 0
                
                for i in range(len(all_points) - 1):
                    if len(all_points[i]) >= 2 and len(all_points[i + 1]) >= 2:
                        lon1, lat1 = all_points[i][0], all_points[i][1]
                        lon2, lat2 = all_points[i + 1][0], all_points[i + 1][1]
                        
                        lat1_rad = math.radians(lat1)
                        lat2_rad = math.radians(lat2)
                        delta_lat = math.radians(lat2 - lat1)
                        delta_lon = math.radians(lon2 - lon1)
                        
                        a = (math.sin(delta_lat / 2) ** 2 + 
                            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                        
                        total_distance += R * c
                
                return total_distance
            
            return distance
            
        except Exception as e:
            logger.warning(f"Failed to calculate trip distance: {e}")
            return 
        
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

    async def get_trip_history_stats(self, days: Optional[int] = None) -> Dict[str, Any]:
        """
        Get trip history statistics including totals and averages
        
        Args:
            days: Number of days to look back (None for all time)
            
        Returns:
            Dictionary containing trip history statistics
        """
        try:
            logger.info(f"[TripHistoryStats] Starting calculation for days: {days}")
            
            # Build query for completed trips
            query = {
                "status": TripStatus.COMPLETED.value
            }
            
            # Add date filter if specified
            if days:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                query["actual_end_time"] = {
                    "$gte": start_date,
                    "$lte": end_date
                }
                logger.info(f"[TripHistoryStats] Filtering by date range: {start_date} to {end_date}")
            else:
                logger.info("[TripHistoryStats] Calculating stats for all time")
            
            # MongoDB aggregation pipeline to calculate statistics
            pipeline = [
                {"$match": query},
                {
                    "$addFields": {
                        # Calculate trip duration in hours
                        "duration_hours": {
                            "$cond": {
                                "if": {"$and": ["$actual_start_time", "$actual_end_time"]},
                                "then": {
                                    "$divide": [
                                        {"$subtract": ["$actual_end_time", "$actual_start_time"]},
                                        3600000  # Convert milliseconds to hours
                                    ]
                                },
                                "else": 0
                            }
                        },
                        # Use route_info distance first, then actual_distance, then estimated_distance
                        "trip_distance": {
                            "$cond": {
                                "if": {"$gt": [{"$ifNull": ["$route_info.distance", 0]}, 0]},
                                "then": {"$divide": ["$route_info.distance", 1000]},  # Convert meters to km
                                "else": {
                                    "$cond": {
                                        "if": {"$gt": [{"$ifNull": ["$actual_distance", 0]}, 0]},
                                        "then": "$actual_distance",
                                        "else": {"$ifNull": ["$estimated_distance", 0]}
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_trips": {"$sum": 1},
                        "total_duration_hours": {"$sum": "$duration_hours"},
                        "total_distance": {"$sum": "$trip_distance"},
                        "avg_duration_hours": {"$avg": "$duration_hours"},
                        "avg_distance": {"$avg": "$trip_distance"},
                        # Additional metrics
                        "max_duration": {"$max": "$duration_hours"},
                        "min_duration": {"$min": "$duration_hours"},
                        "max_distance": {"$max": "$trip_distance"},
                        "min_distance": {"$min": "$trip_distance"}
                    }
                }
            ]
            
            logger.info("[TripHistoryStats] Executing MongoDB aggregation pipeline")
            result = await db_manager.trip_history.aggregate(pipeline).to_list(None)
            
            if result:
                data = result[0]
                stats = {
                    "total_trips": data.get("total_trips", 0),
                    "total_duration_hours": round(data.get("total_duration_hours", 0), 2),
                    "total_distance_km": round(data.get("total_distance", 0), 2),
                    "average_duration_hours": round(data.get("avg_duration_hours", 0), 2),
                    "average_distance_km": round(data.get("avg_distance", 0), 2),
                    "max_duration_hours": round(data.get("max_duration", 0), 2),
                    "min_duration_hours": round(data.get("min_duration", 0), 2),
                    "max_distance_km": round(data.get("max_distance", 0), 2),
                    "min_distance_km": round(data.get("min_distance", 0), 2),
                    "time_period": f"Last {days} days" if days else "All time"
                }
                
                logger.info(f"[TripHistoryStats] Successfully calculated stats: {stats}")
                return stats
            else:
                logger.info("[TripHistoryStats] No completed trips found")
                return {
                    "total_trips": 0,
                    "total_duration_hours": 0,
                    "total_distance_km": 0,
                    "average_duration_hours": 0,
                    "average_distance_km": 0,
                    "max_duration_hours": 0,
                    "min_duration_hours": 0,
                    "max_distance_km": 0,
                    "min_distance_km": 0,
                    "time_period": f"Last {days} days" if days else "All time"
                }
            
        except Exception as e:
            logger.error(f"[TripHistoryStats] Error calculating statistics: {str(e)}", exc_info=True)
            raise


# Global instance
analytics_service = AnalyticsService()
