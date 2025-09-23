import logging
import os
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from bson import ObjectId
import asyncio

from schemas.entities import Trip, TripCombinationRecommendation, RouteInfo, Waypoint, LocationPoint, RouteBounds
from repositories.database import db_manager
from services.trip_service import trip_service

logger = logging.getLogger(__name__)

# Configuration constants
MAX_TRAVEL_DISTANCE_KM = 15.0  # Max distance between trips to consider combination
MIN_TIME_BUFFER_MINUTES = 30   # Minimum time between trip end and next start
MAX_TIME_BUFFER_HOURS = 4      # Maximum time gap to consider combination
MIN_TIME_SAVINGS_MINUTES = 20  # Minimum time savings to recommend combination
MAX_ADDITIONAL_DISTANCE_KM = 10.0  # Max additional distance acceptable
DRIVER_EFFICIENCY_WEIGHT = 0.3  # Weight for driver efficiency in scoring


ORS_API_KEY = os.getenv("ORS_API_KEY")

class UpcomingRecommendationsService:
    """Service for analyzing and recommending trip combinations"""

    def __init__(self):
        self.db = db_manager
        self.combination_recommendations: Dict[str, TripCombinationRecommendation] = {}

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371.0  # Earth's radius in km
        dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
        a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))
    
    def _calculate_bounds(self, coords: List[List[float]]) -> RouteBounds:
        """Calculate bounding box for route coordinates"""
        if not coords:
            return None
        
        lats = [c[0] for c in coords]  # First element is latitude
        lngs = [c[1] for c in coords]  # Second element is longitude
        
        return RouteBounds(
            southWest={"lat": min(lats), "lng": min(lngs)},
            northEast={"lat": max(lats), "lng": max(lngs)}
        )

    def _calculate_travel_distance(self, trip1: Trip, trip2: Trip) -> float:
        """Calculate distance between end of trip1 and start of trip2"""
        try:
            # Get coordinates from trip destinations/origins
            trip1_end = trip1.destination.location.coordinates  # [lng, lat]
            trip2_start = trip2.origin.location.coordinates     # [lng, lat]
            
            logger.debug(f"Trip1 end coordinates: {trip1_end}, Trip2 start coordinates: {trip2_start}")
            
            distance = self._haversine(
                trip1_end[1], trip1_end[0],    # lat1, lon1
                trip2_start[1], trip2_start[0]  # lat2, lon2
            )
            
            logger.debug(f"Calculated travel distance: {distance:.2f}km")
            return distance
            
        except Exception as e:
            logger.warning(f"Error calculating travel distance: {e}")
            logger.debug(f"Trip1 destination: {getattr(trip1, 'destination', 'N/A')}")
            logger.debug(f"Trip2 origin: {getattr(trip2, 'origin', 'N/A')}")
            return float('inf')

    def _calculate_time_gap(self, trip1: Trip, trip2: Trip) -> float:
        """Calculate time gap between trips in hours"""
        try:
            trip1_end = trip1.scheduled_end_time
            trip2_start = trip2.scheduled_start_time
            
            logger.debug(f"Trip1 end time: {trip1_end}, Trip2 start time: {trip2_start}")
            
            if isinstance(trip1_end, str):
                trip1_end = datetime.fromisoformat(trip1_end.replace('Z', '+00:00'))
            if isinstance(trip2_start, str):
                trip2_start = datetime.fromisoformat(trip2_start.replace('Z', '+00:00'))
            
            time_gap = (trip2_start - trip1_end).total_seconds() / 3600.0
            time_gap = max(0, time_gap)
            
            logger.debug(f"Calculated time gap: {time_gap:.2f} hours")
            return time_gap
            
        except Exception as e:
            logger.warning(f"Error calculating time gap: {e}")
            logger.debug(f"Trip1 end: {trip1_end}, Trip2 start: {trip2_start}")
            return 0
    
    async def _check_time_feasibility(self, trip1: Trip, trip2: Trip, travel_distance_km: float, 
                                available_time_hours: float) -> tuple[bool, float, float]:
        """
        Check if there's enough time to travel between trip1 end and trip2 start
        Returns: (is_feasible, required_travel_time_minutes, time_buffer_minutes)
        """
        try:
            # If trips overlap or have negative time gap, not feasible
            if available_time_hours <= 0:
                return False, 0, 0
            
            available_time_minutes = available_time_hours * 60
            
            # Method 1: Quick estimation using distance and average speed
            # Assume average city driving speed of 30 km/h (conservative estimate)
            AVERAGE_CITY_SPEED_KMH = 30
            estimated_travel_time_minutes = (travel_distance_km / AVERAGE_CITY_SPEED_KMH) * 60
            
            # Add buffer time for:
            # - Traffic variations: 20% extra time
            # - Driver break/preparation: 10 minutes minimum
            TRAFFIC_BUFFER_PERCENT = 0.2
            MIN_PREPARATION_TIME_MINUTES = 10
            
            required_travel_time_minutes = (
                estimated_travel_time_minutes * (1 + TRAFFIC_BUFFER_PERCENT) + 
                MIN_PREPARATION_TIME_MINUTES
            )
            
            time_buffer_minutes = available_time_minutes - required_travel_time_minutes
            is_feasible = time_buffer_minutes >= 0
            
            logger.debug(f"Time feasibility check:")
            logger.debug(f"  Distance: {travel_distance_km:.2f}km")
            logger.debug(f"  Available time: {available_time_minutes:.1f}min")
            logger.debug(f"  Estimated travel time: {estimated_travel_time_minutes:.1f}min")
            logger.debug(f"  Required time (with buffers): {required_travel_time_minutes:.1f}min")
            logger.debug(f"  Time buffer: {time_buffer_minutes:.1f}min")
            logger.debug(f"  Feasible: {is_feasible}")
            
            return is_feasible, required_travel_time_minutes, time_buffer_minutes
            
        except Exception as e:
            logger.error(f"Error checking time feasibility: {e}")
            return False, 0, 0

    async def _get_route_with_waypoints(self, start_location_lat, start_location_long, end_location_lat, end_location_long, waypoints=[]):
        try:
            # Build coordinates array in [lng, lat] format
            coordinates = (
                [[start_location_long, start_location_lat]]
                + waypoints  # waypoints should already be [lng, lat] pairs
                + [[end_location_long, end_location_lat]]
            )

            logger.debug(f"Route coordinates: {coordinates}")

            url = "https://api.openrouteservice.org/v2/directions/driving-car"
            headers = {"Authorization": ORS_API_KEY}
            params = {
                "coordinates": coordinates
            }

            try:
                logger.debug(f"Making ORS API request to {url}")
                logger.debug(f"Request headers: {headers}")
                logger.debug(f"Request params: {params}")
                
                resp = requests.post(url, headers=headers, json=params)
                logger.debug(f"Response status code: {resp.status_code}")
                logger.debug(f"Response headers: {dict(resp.headers)}")
                
                # Log the raw response text for debugging
                response_text = resp.text
                logger.debug(f"Raw response text: {response_text[:500]}...")  # First 500 chars
                
                resp.raise_for_status()
                data = resp.json()
                
                # Check if response has expected structure (ORS returns 'routes' not 'features')
                if "routes" not in data:
                    logger.error(f"ORS response missing 'routes' key. Full response: {data}")
                    return None
                    
                if not data["routes"]:
                    logger.error(f"ORS response has empty routes array. Full response: {data}")
                    return None
                    
                if "segments" not in data["routes"][0]:
                    logger.error(f"ORS response missing 'segments'. Full response: {data}")
                    return None
                
                # Get the first segment (should contain the route summary)
                route = data["routes"][0]["segments"][0]
                
                # For coordinates, we need to decode the geometry or use way_points
                # The response includes encoded polyline geometry, let's use the summary data
                total_distance = data["routes"][0]["summary"]["distance"]  # meters
                total_duration = data["routes"][0]["summary"]["duration"]   # seconds
                
                # Create a simplified route object
                route_summary = {
                    "distance": total_distance,
                    "duration": total_duration
                }
                
                # For coordinates, we can create a simple line between start and end points
                # In a production system, you'd want to decode the geometry properly
                coords = [
                    [start_location_lat, start_location_long],
                    [end_location_lat, end_location_long]
                ] 
                
                logger.debug(f"ORS response: distance={route_summary.get('distance', 'N/A')}m, duration={route_summary.get('duration', 'N/A')}s")
                return route_summary, coords
                
            except requests.exceptions.HTTPError as e:
                logger.error(f"ORS API HTTP error: {e}")
                logger.error(f"Response status: {resp.status_code}")
                logger.error(f"Response content: {resp.text}")
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"ORS API request failed: {e}")
                return None
            except KeyError as e:
                logger.error(f"ORS response structure error: {e}")
                logger.error(f"Full ORS response: {data}")
                return None
            except ValueError as e:
                logger.error(f"ORS JSON parsing error: {e}")
                logger.error(f"Response text: {response_text}")
                return None
                
        except Exception as e:
            logger.error(f"Route calculation failed: {e}")
            return None


    async def _calculate_combined_route_info(self, primary_trip: Trip, secondary_trip: Trip) -> Optional[RouteInfo]:
        """Calculate route information for combined trip"""
        try:
            # Create waypoint coordinates: origin -> destination1 -> origin2 -> destination2
            # The waypoints array should be [lng, lat] pairs, not Waypoint objects
            waypoint_coordinates = [
                # First waypoint: primary trip destination
                [primary_trip.destination.location.coordinates[0], primary_trip.destination.location.coordinates[1]],
                # Second waypoint: secondary trip origin  
                [secondary_trip.origin.location.coordinates[0], secondary_trip.origin.location.coordinates[1]]
            ]
            
            logger.debug(f"Waypoint coordinates: {waypoint_coordinates}")
            
            # Get route from primary origin to secondary destination via waypoints
            route, coords = await self._get_route_with_waypoints(
                primary_trip.origin.location.coordinates[1],    # start_lat
                primary_trip.origin.location.coordinates[0],    # start_lon
                secondary_trip.destination.location.coordinates[1],  # end_lat
                secondary_trip.destination.location.coordinates[0],  # end_lon
                waypoint_coordinates  # Pass coordinate pairs, not Waypoint objects
            )
            
            if route:
                return RouteInfo(
                    distance=route["distance"],
                    duration=route["duration"],
                    coordinates=coords,
                    bounds=self._calculate_bounds(coords)
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error calculating combined route: {e}")
            logger.error(f"Primary trip origin: {primary_trip.origin.location.coordinates}")
            logger.error(f"Primary trip destination: {primary_trip.destination.location.coordinates}")
            logger.error(f"Secondary trip origin: {secondary_trip.origin.location.coordinates}")
            logger.error(f"Secondary trip destination: {secondary_trip.destination.location.coordinates}")
            return None

    def _calculate_combination_benefits(self, primary_trip: Trip, secondary_trip: Trip, 
                                     combined_route: RouteInfo) -> Dict[str, Any]:
        """Calculate benefits of combining two trips"""
        
        # Original totals
        original_distance = primary_trip.estimated_distance + secondary_trip.estimated_distance
        original_duration = primary_trip.estimated_duration + secondary_trip.estimated_duration
        
        # Combined totals (convert from meters/seconds to km/minutes)
        combined_distance = combined_route.distance / 1000.0
        combined_duration = combined_route.duration / 60.0
        
        # Calculate savings
        distance_savings = original_distance - combined_distance
        time_savings = original_duration - combined_duration
        
        # Fuel efficiency estimate (simplified)
        fuel_savings_percent = (distance_savings / original_distance * 100) if original_distance > 0 else 0
        
        # Driver efficiency - one driver instead of two
        driver_utilization = "100% efficiency - one driver handles both trips"
        
        return {
            "distance_savings_km": distance_savings,
            "time_savings_minutes": time_savings,
            "fuel_efficiency_improvement": f"{fuel_savings_percent:.1f}% fuel savings",
            "driver_utilization": driver_utilization,
            "cost_savings": f"Estimated ${abs(distance_savings * 2.5):.2f} in fuel and driver costs",
            "combined_distance_km": combined_distance,
            "combined_duration_minutes": combined_duration
        }

    def _calculate_combination_score(self, primary_trip: Trip, secondary_trip: Trip, 
                                   benefits: Dict[str, Any], travel_distance: float, 
                                   time_gap: float) -> float:
        """Calculate a score for how good this combination is (0-1)"""
        score = 0.0
        
        # Time savings component (0-0.4)
        time_savings = benefits.get("time_savings_minutes", 0)
        if time_savings > MIN_TIME_SAVINGS_MINUTES:
            score += min(0.4, time_savings / 120.0)  # Max score at 2 hours savings
        
        # Distance efficiency component (0-0.3)
        distance_savings = benefits.get("distance_savings_km", 0)
        if distance_savings > 0:
            score += min(0.3, distance_savings / 20.0)  # Max score at 20km savings
        
        # Travel distance penalty (0-0.2 deduction)
        if travel_distance <= 5.0:
            score += 0.2
        elif travel_distance <= 10.0:
            score += 0.1
        # No bonus for > 10km travel distance
        
        # Time gap efficiency (0-0.1)
        if 0.5 <= time_gap <= 2.0:  # Sweet spot: 30min - 2 hours
            score += 0.1
        elif time_gap <= 4.0:
            score += 0.05
        
        return min(1.0, max(0.0, score))

    async def find_combination_opportunities(self) -> List[TripCombinationRecommendation]:
        """Find opportunities to combine upcoming trips"""
        try:
            trips = await trip_service.get_all_upcoming_trips()
            recommendations = []
            processed_pairs = set()
            
            logger.info(f"Analyzing {len(trips)} trips for combination opportunities")
            
            # Log trip details for debugging
            for idx, trip in enumerate(trips):
                logger.info(f"Trip {idx}: '{trip.name}' - Driver: {trip.driver_assignment}, "
                        f"Start: {trip.scheduled_start_time}, End: {trip.scheduled_end_time}")
            logger.info(f"Time gap constraints: {MIN_TIME_BUFFER_MINUTES}min - {MAX_TIME_BUFFER_HOURS}h")
            
            total_pairs = 0
            filtered_out = {
                'same_driver': 0,
                'travel_distance': 0,
                'time_feasibility': 0,
                'time_gap': 0,
                'route_calculation_failed': 0,
                'insufficient_time_savings': 0,
                'negative_distance_savings': 0,
                'low_score': 0
            }
            
            for i, primary_trip in enumerate(trips):
                for j, secondary_trip in enumerate(trips):
                    if i >= j:  # Skip same trip and avoid duplicate pairs
                        continue
                    
                    total_pairs += 1
                    pair_key = tuple(sorted([primary_trip.id, secondary_trip.id]))
                    
                    logger.debug(f"Evaluating pair {total_pairs}: {primary_trip.name} -> {secondary_trip.name}")
                    
                    if pair_key in processed_pairs:
                        logger.debug(f"Pair already processed, skipping")
                        continue
                    processed_pairs.add(pair_key)
                    
                    # Check same driver filter
                    if primary_trip.driver_assignment == secondary_trip.driver_assignment:
                        filtered_out['same_driver'] += 1
                        logger.debug(f"Same driver assigned ({primary_trip.driver_assignment}), skipping")
                        continue
                    
                    # Calculate metrics
                    travel_distance = self._calculate_travel_distance(primary_trip, secondary_trip)
                    available_time_gap = self._calculate_time_gap(primary_trip, secondary_trip)
                    
                    logger.debug(f"Travel distance: {travel_distance:.2f}km, Available time: {available_time_gap:.2f}h")
                    
                    # Apply distance filter (keep this as a sanity check)
                    if travel_distance > MAX_TRAVEL_DISTANCE_KM:
                        filtered_out['travel_distance'] += 1
                        logger.debug(f"Travel distance {travel_distance:.2f}km > {MAX_TRAVEL_DISTANCE_KM}km, skipping")
                        continue
                    
                    # Check time feasibility - calculate if there's enough time to travel between trips
                    is_time_feasible, required_travel_time, time_buffer = await self._check_time_feasibility(
                        primary_trip, secondary_trip, travel_distance, available_time_gap
                    )
                    
                    if not is_time_feasible:
                        filtered_out['time_feasibility'] += 1
                        logger.info(f"❌ TIME FEASIBILITY: {primary_trip.name} -> {secondary_trip.name}: "
                                f"available={available_time_gap*60:.0f}min, required={required_travel_time:.0f}min, "
                                f"buffer={time_buffer:.0f}min")
                        continue
                    
                    logger.info(f"✓ TIME FEASIBLE: {primary_trip.name} -> {secondary_trip.name}: "
                            f"available={available_time_gap*60:.0f}min, required={required_travel_time:.0f}min, "
                            f"buffer={time_buffer:.0f}min")
                    
                    logger.debug(f"Calculating combined route for viable pair...")
                    
                    # Calculate combined route
                    combined_route = await self._calculate_combined_route_info(primary_trip, secondary_trip)
                    if not combined_route:
                        filtered_out['route_calculation_failed'] += 1
                        logger.debug("Combined route calculation failed, skipping")
                        continue
                    
                    logger.debug(f"Combined route: {combined_route.distance/1000:.2f}km, {combined_route.duration/60:.1f}min")
                    
                    # Calculate benefits
                    benefits = self._calculate_combination_benefits(primary_trip, secondary_trip, combined_route)
                    
                    logger.debug(f"Benefits: time_savings={benefits.get('time_savings_minutes', 0):.1f}min, "
                            f"distance_savings={benefits.get('distance_savings_km', 0):.2f}km")
                    
                    # Check if benefits meet minimum criteria
                    time_savings = benefits.get("time_savings_minutes", 0)
                    if time_savings < MIN_TIME_SAVINGS_MINUTES:
                        filtered_out['insufficient_time_savings'] += 1
                        logger.debug(f"Time savings {time_savings:.1f}min < {MIN_TIME_SAVINGS_MINUTES}min, skipping")
                        continue
                    
                    distance_savings = benefits.get("distance_savings_km", 0)
                    if distance_savings < 0:
                        filtered_out['negative_distance_savings'] += 1
                        logger.debug(f"Negative distance savings {distance_savings:.2f}km, skipping")
                        continue
                    
                    # Calculate score
                    score = self._calculate_combination_score(
                        primary_trip, secondary_trip, benefits, travel_distance, available_time_gap
                    )
                    
                    logger.debug(f"Combination score: {score:.3f}")
                    
                    if score < 0.3:
                        filtered_out['low_score'] += 1
                        logger.debug(f"Score {score:.3f} < 0.3, skipping")
                        continue
                    
                    logger.info(f"✓ VIABLE COMBINATION FOUND: {primary_trip.name} + {secondary_trip.name} "
                            f"(score: {score:.3f}, time_savings: {time_savings:.1f}min)")
                    
                    # Create recommendation
                    recommendation = TripCombinationRecommendation(
                        id=f"combo_{primary_trip.id[:8]}_{secondary_trip.id[:8]}",
                        primary_trip_id=primary_trip.id,
                        secondary_trip_id=secondary_trip.id,
                        primary_trip_name=primary_trip.name,
                        secondary_trip_name=secondary_trip.name,
                        recommended_driver=primary_trip.driver_assignment,
                        recommended_vehicle=primary_trip.vehicle_id,
                        combined_route=combined_route,
                        travel_distance_km=travel_distance,
                        time_gap_hours=available_time_gap,
                        benefits=benefits,
                        confidence_score=score,
                        reasoning=[
                            f"Combining trips saves {benefits['time_savings_minutes']:.0f} minutes",
                            f"Travel distance between trips is only {travel_distance:.1f}km",
                            f"Time gap of {available_time_gap:.1f} hours allows comfortable transition",
                            f"One driver can handle both trips efficiently",
                            f"Reduces overall fleet utilization"
                        ],
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(hours=24)
                    )
                    
                    recommendations.append(recommendation)
            
            # Log filtering summary
            logger.info(f"FILTERING SUMMARY:")
            logger.info(f"  Total pairs evaluated: {total_pairs}")
            logger.info(f"  Filtered out by same driver: {filtered_out['same_driver']}")
            logger.info(f"  Filtered out by travel distance: {filtered_out['travel_distance']}")
            logger.info(f"  Filtered out by time feasibility: {filtered_out['time_feasibility']}")
            logger.info(f"  Filtered out by route calculation failure: {filtered_out['route_calculation_failed']}")
            logger.info(f"  Filtered out by insufficient time savings: {filtered_out['insufficient_time_savings']}")
            logger.info(f"  Filtered out by negative distance savings: {filtered_out['negative_distance_savings']}")
            logger.info(f"  Filtered out by low score: {filtered_out['low_score']}")
            
            # Sort by confidence score
            recommendations.sort(key=lambda r: r.confidence_score, reverse=True)
            
            logger.info(f"Generated {len(recommendations)} trip combination recommendations")
            return recommendations[:10]  # Return top 10
            
        except Exception as e:
            logger.error(f"Error finding combination opportunities: {e}")
            return []

    async def store_recommendation(self, recommendation: TripCombinationRecommendation):
        """Store combination recommendation in database"""
        try:
            recommendation_doc = {
                "id": recommendation.id,
                "primary_trip_id": recommendation.primary_trip_id,
                "secondary_trip_id": recommendation.secondary_trip_id,
                "primary_trip_name": recommendation.primary_trip_name,
                "secondary_trip_name": recommendation.secondary_trip_name,
                "recommended_driver": recommendation.recommended_driver,
                "recommended_vehicle": recommendation.recommended_vehicle,
                "combined_route": recommendation.combined_route.dict() if recommendation.combined_route else None,
                "travel_distance_km": recommendation.travel_distance_km,
                "time_gap_hours": recommendation.time_gap_hours,
                "benefits": recommendation.benefits,
                "confidence_score": recommendation.confidence_score,
                "reasoning": recommendation.reasoning,
                "status": "pending",
                "created_at": recommendation.created_at,
                "expires_at": recommendation.expires_at
            }
            
            await self.db.upcoming_recommendations.update_one(
                {"id": recommendation.id},
                {"$set": recommendation_doc},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error storing combination recommendation: {e}")

    async def get_combination_recommendations(self) -> List[Dict[str, Any]]:
        """Get active combination recommendations"""
        try:
            query = {
                "status": "pending",
                "expires_at": {"$gt": datetime.utcnow()}
            }
            
            cursor = self.db.upcoming_recommendations.find(query).sort("confidence_score", -1)
            recommendations = await cursor.to_list(None)
            
            # Convert ObjectId to string
            for rec in recommendations:
                rec["_id"] = str(rec["_id"])
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting combination recommendations: {e}")
            return []

    async def accept_combination_recommendation(self, recommendation_id: str) -> bool:
        """Accept a trip combination recommendation"""
        try:
            # Get the recommendation
            recommendation = await self.db.upcoming_recommendations.find_one({
                "id": recommendation_id,
                "status": "pending"
            })
            
            if not recommendation:
                return False
            
            # Update the primary trip to include secondary trip as waypoints
            primary_trip_id = recommendation["primary_trip_id"]
            secondary_trip_id = recommendation["secondary_trip_id"]
            
            # Get both trips
            primary_trip = await self.db.trips.find_one({"_id": ObjectId(primary_trip_id)})
            secondary_trip = await self.db.trips.find_one({"_id": ObjectId(secondary_trip_id)})
            
            if not primary_trip or not secondary_trip:
                return False
            
            # Create combined trip by updating primary trip
            combined_waypoints = [
                {
                    "name": secondary_trip["origin"]["name"],
                    "location": secondary_trip["origin"]["location"],
                    "order": 1
                },
                {
                    "name": secondary_trip["destination"]["name"], 
                    "location": secondary_trip["destination"]["location"],
                    "order": 2
                }
            ]
            
            # Update primary trip
            update_result = await self.db.trips.update_one(
                {"_id": ObjectId(primary_trip_id)},
                {
                    "$set": {
                        "waypoints": combined_waypoints,
                        "route_info": recommendation["combined_route"],
                        "estimated_distance": recommendation["benefits"]["combined_distance_km"],
                        "estimated_duration": recommendation["benefits"]["combined_duration_minutes"],
                        "scheduled_end_time": secondary_trip["scheduled_end_time"],
                        "combination_info": {
                            "is_combined": True,
                            "original_secondary_trip": secondary_trip_id,
                            "combined_at": datetime.utcnow()
                        },
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Cancel the secondary trip
            await self.db.trips.update_one(
                {"_id": ObjectId(secondary_trip_id)},
                {
                    "$set": {
                        "status": "cancelled",
                        "cancellation_reason": "combined_with_other_trip",
                        "combined_into": primary_trip_id,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Mark recommendation as accepted
            await self.db.upcoming_recommendations.update_one(
                {"id": recommendation_id},
                {
                    "$set": {
                        "status": "accepted",
                        "accepted_at": datetime.utcnow()
                    }
                }
            )
            
            return update_result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error accepting combination recommendation: {e}")
            return False
    
    async def reject_combination_recommendation(self, recommendation_id: str) -> bool:
      """Reject a trip combination recommendation by deleting it from MongoDB"""
      try:
          result = await self.db.upcoming_recommendations.delete_one({"id": recommendation_id})
          return result.deleted_count > 0  # True if something was deleted
      except Exception as e:
          logger.error(f"Error rejecting combination recommendation: {e}")
          return False



    async def analyze_and_store_combinations(self):
        """Main method to analyze upcoming trips and store recommendations"""
        try:
            recommendations = await self.find_combination_opportunities()
            
            for recommendation in recommendations:
                await self.store_recommendation(recommendation)
            
            logger.info(f"Analyzed and stored {len(recommendations)} combination recommendations")
            return len(recommendations)
            
        except Exception as e:
            logger.error(f"Error in analyze_and_store_combinations: {e}")
            return 0


# Global service instance
upcoming_recommendation_service = UpcomingRecommendationsService()