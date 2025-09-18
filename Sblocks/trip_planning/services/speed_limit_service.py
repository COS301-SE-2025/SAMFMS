"""
Google Roads API service for speed limit checking
"""
import logging
import asyncio
import httpx
from typing import Dict, Optional, List, Tuple
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
    """Service for checking speed limits using Google Roads API"""
    
    CACHE_DURATION_SECONDS = 30  # Cache speed limits for 30 seconds
    API_BASE_URL = "https://roads.googleapis.com/v1/speedLimits"
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not found in environment variables")
        
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
    
    async def get_speed_limit(self, location: LocationPoint) -> Optional[SpeedLimitInfo]:
        """
        Get speed limit for a location, with caching
        
        Args:
            location: GPS location to check
            
        Returns:
            SpeedLimitInfo if found, None if API error or no data
        """
        if not self.api_key:
            logger.warning("Google Maps API key not configured, cannot check speed limits")
            return None
        
        cache_key = self._location_cache_key(location)
        
        # Check cache first
        if cache_key in self._speed_limit_cache:
            cached_info = self._speed_limit_cache[cache_key]
            if self._is_cache_valid(cached_info):
                logger.debug(f"[SpeedLimitService] Using cached speed limit for {cache_key}")
                return cached_info
            else:
                # Remove expired cache entry
                del self._speed_limit_cache[cache_key]
        
        # Fetch from API
        try:
            speed_info = await self._fetch_speed_limit_from_api(location)
            if speed_info:
                # Cache the result
                self._speed_limit_cache[cache_key] = speed_info
                logger.info(f"[SpeedLimitService] Cached speed limit {speed_info.speed_limit} km/h for {cache_key}")
            
            return speed_info
            
        except Exception as e:
            logger.error(f"[SpeedLimitService] Failed to get speed limit: {e}")
            return None
    
    async def _fetch_speed_limit_from_api(self, location: LocationPoint) -> Optional[SpeedLimitInfo]:
        """Fetch speed limit from Google Roads API"""
        try:
            lat = location.coordinates[1]  # latitude
            lon = location.coordinates[0]  # longitude
            
            params = {
                "path": f"{lat},{lon}",
                "units": "KPH",
                "key": self.api_key
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.API_BASE_URL, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract speed limit from response
                speed_limits = data.get("speedLimits", [])
                if not speed_limits:
                    logger.debug(f"[SpeedLimitService] No speed limit data for location {lat},{lon}")
                    return None
                
                # Use the first speed limit (should only be one for single point)
                speed_data = speed_limits[0]
                
                return SpeedLimitInfo(
                    speed_limit=float(speed_data["speedLimit"]),
                    place_id=speed_data["placeId"],
                    units=speed_data.get("units", "KPH"),
                    timestamp=datetime.utcnow()
                )
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.error("[SpeedLimitService] Google Maps API access denied - check API key and billing")
            elif e.response.status_code == 429:
                logger.warning("[SpeedLimitService] Google Maps API rate limit exceeded")
            else:
                logger.error(f"[SpeedLimitService] API HTTP error {e.response.status_code}: {e}")
            return None
            
        except Exception as e:
            logger.error(f"[SpeedLimitService] Unexpected error fetching speed limit: {e}")
            return None
    
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
            # Calculate distance using Haversine formula
            distance_km = self._haversine_distance(
                prev_location.coordinates[1], prev_location.coordinates[0],  # prev lat, lon
                current_location.coordinates[1], current_location.coordinates[0]  # curr lat, lon
            )
            
            # Calculate time difference in hours
            time_diff = current_time - prev_time
            time_hours = time_diff.total_seconds() / 3600.0
            
            if time_hours <= 0:
                return 0.0
            
            speed_kmh = distance_km / time_hours
            
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