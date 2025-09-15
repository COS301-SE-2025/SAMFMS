"""
Geoapify Map Matching API service for speed limit checking
"""
import logging
import asyncio
import httpx
import json
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import os

from schemas.entities import LocationPoint

logger = logging.getLogger(__name__)


@dataclass
class SpeedLimitInfo:
    """Speed limit information for a location"""
    speed_limit: float  # in km/h
    place_id: str
    units: str = "KPH"
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class SpeedLimitService:
    """Service for checking speed limits using Geoapify Roads API"""
    
    CACHE_DURATION_SECONDS = 90  # Cache speed limits for 90 seconds
    API_BASE_URL = "https://api.geoapify.com/v1/roads"
    
    def __init__(self):
        # Try to get API key from config first, then environment, then default
        try:
            from config.settings import config
            self.api_key = config.trips.geoapify_api_key or os.getenv("GEOAPIFY_API_KEY", "8c5cae4820744254b3cb03ebd9b9ce13")
        except ImportError:
            self.api_key = os.getenv("GEOAPIFY_API_KEY", "8c5cae4820744254b3cb03ebd9b9ce13")
        
        if not self.api_key:
            logger.warning("GEOAPIFY_API_KEY not found in environment variables")
        
        # Cache: location_key -> SpeedLimitInfo
        self._speed_limit_cache: Dict[str, SpeedLimitInfo] = {}
        
    def _location_cache_key(self, location: LocationPoint) -> str:
        """Generate cache key for location (rounded to reduce cache size)"""
        # Round to 4 decimal places (~11m precision) to group nearby locations
        lat = round(location.coordinates[1], 4)
        lon = round(location.coordinates[0], 4)
        return f"{lat},{lon}"
    
    def _is_cache_valid(self, speed_info: SpeedLimitInfo) -> bool:
        """Check if cached speed limit info is still valid"""
        if not speed_info.timestamp:
            return False
        
        age = datetime.utcnow() - speed_info.timestamp
        return age.total_seconds() < self.CACHE_DURATION_SECONDS
    
    async def get_speed_limit(self, location: LocationPoint) -> SpeedLimitInfo:
        """
        Get speed limit for a location, with caching
        
        Args:
            location: GPS location to check
            
        Returns:
            SpeedLimitInfo (always returns a valid object, defaults to 50 km/h if API fails)
        """
        if not self.api_key:
            logger.warning("Geoapify API key not configured, using default speed limit")
            lat = location.coordinates[1]
            lon = location.coordinates[0]
            return SpeedLimitInfo(
                speed_limit=50.0,
                place_id=f"{lat},{lon}",
                units="KPH",
                timestamp=datetime.utcnow()
            )
        
        cache_key = self._location_cache_key(location)
        
        # Check cache first
        if cache_key in self._speed_limit_cache:
            cached_info = self._speed_limit_cache[cache_key]
            if self._is_cache_valid(cached_info):
                logger.info(f"[SpeedLimitService] Using cached speed limit {cached_info.speed_limit} km/h for {cache_key} (cached {(datetime.utcnow() - cached_info.timestamp).total_seconds():.1f}s ago)")
                return cached_info
            else:
                # Remove expired cache entry
                logger.info(f"[SpeedLimitService] Cache expired for {cache_key}, removing from cache")
                del self._speed_limit_cache[cache_key]
        
        # Fetch from API
        try:
            logger.info(f"[SpeedLimitService] Making API request for location {cache_key} (cache miss or expired)")
            speed_info = await self._fetch_speed_limit_from_api(location)
            if speed_info:
                # Cache the result
                self._speed_limit_cache[cache_key] = speed_info
                logger.info(f"[SpeedLimitService] Cached speed limit {speed_info.speed_limit} km/h for {cache_key} for {self.CACHE_DURATION_SECONDS} seconds")
                return speed_info
            
            # If API returned None, return default
            lat = location.coordinates[1]
            lon = location.coordinates[0]
            default_info = SpeedLimitInfo(
                speed_limit=50.0,
                place_id=f"{lat},{lon}",
                units="KPH",
                timestamp=datetime.utcnow()
            )
            return default_info
            
        except Exception as e:
            logger.error(f"[SpeedLimitService] Failed to get speed limit: {e}")
            # Return default on any error
            lat = location.coordinates[1]
            lon = location.coordinates[0]
            return SpeedLimitInfo(
                speed_limit=50.0,
                place_id=f"{lat},{lon}",
                units="KPH",
                timestamp=datetime.utcnow()
            )
    
    async def _fetch_speed_limit_from_api(self, location: LocationPoint) -> SpeedLimitInfo:
        """Fetch speed limit from Geoapify Roads API"""
        try:
            lat = location.coordinates[1]  # latitude
            lon = location.coordinates[0]  # longitude
            
            # Use Geoapify Roads API for road information at a specific point
            params = {
                "lat": lat,
                "lon": lon,
                "apiKey": self.api_key
            }
            
            headers = {
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.API_BASE_URL,
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"[SpeedLimitService] Full Geoapify Roads API response for {lat},{lon}: {json.dumps(data, indent=2)}")
                
                # Extract speed limit from response
                if "features" in data and data["features"]:
                    feature = data["features"][0]  # Take first matched feature
                    properties = feature.get("properties", {})
                    
                    # Look for speed limit in properties
                    speed_limit = properties.get("maxspeed")
                    if speed_limit:
                        # Convert to float and handle different units
                        if isinstance(speed_limit, str):
                            # Handle formats like "50", "50 km/h", "30 mph"
                            import re
                            numbers = re.findall(r'\d+', speed_limit)
                            if numbers:
                                speed_value = float(numbers[0])
                                if "mph" in speed_limit.lower():
                                    speed_value = speed_value * 1.60934  # Convert mph to km/h
                            else:
                                speed_value = 50.0  # Default fallback
                        else:
                            speed_value = float(speed_limit)
                        
                        # Generate a place_id from the road name or use coordinates
                        place_id = properties.get("name", f"{lat},{lon}")
                        
                        return SpeedLimitInfo(
                            speed_limit=speed_value,
                            place_id=place_id,
                            units="KPH",
                            timestamp=datetime.utcnow()
                        )
                    else:
                        # If no speed limit found, return a default based on road type
                        road_type = properties.get("highway", "residential")
                        default_speed = self._get_default_speed_limit(road_type)
                        
                        return SpeedLimitInfo(
                            speed_limit=default_speed,
                            place_id=properties.get("name", f"{lat},{lon}"),
                            units="KPH",
                            timestamp=datetime.utcnow()
                        )
                else:
                    # No road data found, return default urban speed limit
                    logger.debug(f"[SpeedLimitService] No road data found for location {lat},{lon}, using default")
                    return SpeedLimitInfo(
                        speed_limit=50.0,  # Default urban speed limit
                        place_id=f"{lat},{lon}",
                        units="KPH",
                        timestamp=datetime.utcnow()
                    )
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.error("[SpeedLimitService] Geoapify API access denied - check API key")
            elif e.response.status_code == 429:
                logger.warning("[SpeedLimitService] Geoapify API rate limit exceeded")
            else:
                logger.error(f"[SpeedLimitService] API HTTP error {e.response.status_code}: {e}")
            
            # Return default speed limit on API error
            lat = location.coordinates[1]
            lon = location.coordinates[0]
            return SpeedLimitInfo(
                speed_limit=50.0,
                place_id=f"{lat},{lon}",
                units="KPH",
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"[SpeedLimitService] Unexpected error fetching speed limit: {e}")
            
            # Return default speed limit on any error
            lat = location.coordinates[1]
            lon = location.coordinates[0]
            return SpeedLimitInfo(
                speed_limit=50.0,
                place_id=f"{lat},{lon}",
                units="KPH",
                timestamp=datetime.utcnow()
            )
    
    def _get_default_speed_limit(self, road_type: str) -> float:
        """Get default speed limit based on road type"""
        default_limits = {
            "motorway": 120.0,
            "trunk": 100.0,
            "primary": 80.0,
            "secondary": 60.0,
            "tertiary": 50.0,
            "residential": 30.0,
            "unclassified": 50.0,
            "service": 20.0,
            "track": 20.0,
            "path": 10.0
        }
        
        return default_limits.get(road_type, 50.0)  # Default to 50 km/h if unknown
    
    def calculate_speed_kmh(self, 
                           prev_location: LocationPoint, 
                           current_location: LocationPoint, 
                           prev_time: datetime, 
                           current_time: datetime) -> float:
        """
        Calculate speed between two GPS points
        
        Args:
            prev_location: Previous GPS location
            current_location: Current GPS location
            prev_time: Time of previous location
            current_time: Time of current location
            
        Returns:
            Speed in km/h
        """
        try:
            # Convert to UTC and remove timezone info to ensure compatibility
            if prev_time.tzinfo is not None:
                prev_time = prev_time.replace(tzinfo=None)
            if current_time.tzinfo is not None:
                current_time = current_time.replace(tzinfo=None)
                
            # Calculate distance using Haversine formula
            distance_km = self._haversine_distance(
                prev_location.coordinates[1], prev_location.coordinates[0],  # prev lat, lon
                current_location.coordinates[1], current_location.coordinates[0]  # curr lat, lon
            )
            
            # Calculate time difference in hours
            time_diff = current_time - prev_time
            time_hours = time_diff.total_seconds() / 3600.0
            
            # Prevent unrealistic speeds from very small time intervals
            # Minimum 5 seconds between measurements for reliable speed calculation
            if time_diff.total_seconds() < 5.0:
                logger.debug(f"[SpeedLimitService] Time interval too small ({time_diff.total_seconds():.3f}s), skipping speed calculation")
                return 0.0
            
            if time_hours <= 0:
                return 0.0
            
            speed_kmh = distance_km / time_hours
            
            # Cap maximum reasonable speed (e.g., 300 km/h for vehicles)
            if speed_kmh > 300.0:
                logger.warning(f"[SpeedLimitService] Calculated speed {speed_kmh:.1f} km/h seems unrealistic, capping at 300 km/h")
                speed_kmh = min(speed_kmh, 300.0)
            
            logger.debug(f"[SpeedLimitService] Calculated speed: {speed_kmh:.2f} km/h over {distance_km:.3f}km in {time_diff.total_seconds():.1f}s")
            
            return speed_kmh
            
        except Exception as e:
            logger.error(f"[SpeedLimitService] Error calculating speed: {e}")
            return 0.0
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth in kilometers
        """
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def clear_cache(self) -> None:
        """Clear the speed limit cache"""
        self._speed_limit_cache.clear()
        logger.info("[SpeedLimitService] Speed limit cache cleared")


# Global service instance
speed_limit_service = SpeedLimitService()