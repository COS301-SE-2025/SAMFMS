"""
Routing Service using Geoapify Routing API
Provides route calculation, turn-by-turn instructions, and route details
"""

import asyncio
import logging
import aiohttp
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class RoutingService:
    """
    Service for calculating routes using Geoapify Routing API
    """
    
    def __init__(self, api_key: str = "8c5cae4820744254b3cb03ebd9b9ce13"):
        """
        Initialize the routing service
        
        Args:
            api_key: Geoapify API key
        """
        self.api_key = api_key
        self.base_url = "https://api.geoapify.com/v1/routing"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def calculate_route(
        self,
        waypoints: List[Tuple[float, float]],
        mode: str = "drive",
        include_instructions: bool = True,
        include_route_details: bool = True,
        include_elevation: bool = False,
        avoid: Optional[List[str]] = None,
        traffic_model: str = "free_flow"
    ) -> Dict[str, Any]:
        """
        Calculate route using Geoapify Routing API
        
        Args:
            waypoints: List of (latitude, longitude) tuples
            mode: Transportation mode (drive, truck, bicycle, walk, etc.)
            include_instructions: Whether to include turn-by-turn instructions
            include_route_details: Whether to include detailed route information
            include_elevation: Whether to include elevation data
            avoid: List of things to avoid (tolls, highways, ferries)
            traffic_model: Traffic model to use (free_flow, approximated)
            
        Returns:
            Dict containing route information from Geoapify API
        """
        if len(waypoints) < 2:
            raise ValueError("At least 2 waypoints are required")

        try:
            # Format waypoints as lat,lon|lat,lon
            waypoints_str = "|".join([f"{lat},{lon}" for lat, lon in waypoints])
            
            # Build parameters
            params = {
                "waypoints": waypoints_str,
                "mode": mode,
                "format": "json",
                "apiKey": self.api_key,
                "traffic": traffic_model
            }
            
            # Add details if requested
            details = []
            if include_instructions:
                details.append("instruction_details")
            if include_route_details:
                details.append("route_details")
            if include_elevation:
                details.append("elevation")
            
            if details:
                params["details"] = ",".join(details)
            
            # Add avoids if specified
            if avoid:
                params["avoid"] = "|".join(avoid)
            
            # Make API request
            session = await self._get_session()
            url = f"{self.base_url}?{urlencode(params)}"
            
            logger.debug(f"[RoutingService] Making request to: {url}")
            
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"[RoutingService] API request failed with status {response.status}: {error_text}")
                    raise Exception(f"Routing API request failed: {response.status} - {error_text}")
                
                data = await response.json()
                logger.debug(f"[RoutingService] API response received successfully")
                
                return data
                
        except Exception as e:
            logger.error(f"[RoutingService] Failed to calculate route: {e}")
            raise

    async def get_route_geometry(
        self,
        waypoints: List[Tuple[float, float]],
        mode: str = "drive"
    ) -> List[List[float]]:
        """
        Get route geometry (coordinates) only
        
        Args:
            waypoints: List of (latitude, longitude) tuples
            mode: Transportation mode
            
        Returns:
            List of [latitude, longitude] coordinate pairs
        """
        try:
            # Get basic route without extra details for efficiency
            route_data = await self.calculate_route(
                waypoints=waypoints,
                mode=mode,
                include_instructions=False,
                include_route_details=False,
                include_elevation=False
            )
            
            if not route_data.get("results") or not route_data["results"]:
                raise Exception("No route found in API response")
            
            route = route_data["results"][0]
            logger.debug(f"[RoutingService.get_route_geometry] Route type: {type(route)}")
            logger.debug(f"[RoutingService.get_route_geometry] Route content sample: {str(route)[:200] if isinstance(route, dict) else route}")
            
            # Ensure route is a dictionary
            if not isinstance(route, dict):
                logger.error(f"[RoutingService.get_route_geometry] Expected route to be dict, got {type(route)}: {route}")
                raise Exception(f"Invalid route data structure: expected dict, got {type(route)}")
            
            # Extract coordinates - try route level first, then legs
            coordinates = []
            
            # Method 1: Try route-level geometry first
            route_geometry = route.get("geometry", {})
            if route_geometry.get("coordinates"):
                coordinates = route_geometry["coordinates"]
                logger.debug(f"[RoutingService] Found {len(coordinates)} route-level coordinates")
            else:
                # Method 2: Extract from legs if no route-level coordinates
                logger.debug(f"[RoutingService] No route-level coordinates, trying legs")
                legs = route.get("legs", [])
                for i, leg in enumerate(legs):
                    if not isinstance(leg, dict):
                        logger.error(f"[RoutingService.get_route_geometry] Leg {i} is not a dict: {leg}")
                        continue
                        
                    leg_coords = leg.get("geometry", {}).get("coordinates", [])
                    if coordinates:
                        # Skip first coordinate of subsequent legs to avoid duplication
                        leg_coords = leg_coords[1:]
                    coordinates.extend(leg_coords)
                logger.debug(f"[RoutingService] Extracted {len(coordinates)} coordinates from legs")
            
            # Convert from [lon, lat] to [lat, lon] format
            formatted_coords = [[coord[1], coord[0]] for coord in coordinates]
            
            logger.debug(f"[RoutingService] Extracted {len(formatted_coords)} coordinate points")
            return formatted_coords
            
        except Exception as e:
            logger.error(f"[RoutingService] Failed to get route geometry: {e}")
            raise

    async def get_raw_route_info(
        self,
        waypoints: List[Tuple[float, float]],
        mode: str = "drive",
        avoid: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get raw route information from Geoapify API without parsing
        
        Args:
            waypoints: List of (latitude, longitude) tuples
            mode: Transportation mode
            avoid: List of things to avoid
            
        Returns:
            Raw API response as dictionary
        """
        try:
            # Get full route data with all details
            route_data = await self.calculate_route(
                waypoints=waypoints,
                mode=mode,
                include_instructions=True,
                include_route_details=True,
                include_elevation=False,
                avoid=avoid
            )
            
            logger.info(f"[RoutingService] Successfully fetched raw route data")
            return route_data
            
        except Exception as e:
            logger.error(f"[RoutingService] Failed to get raw route info: {e}")
            raise

    async def get_detailed_route_info(
        self,
        waypoints: List[Tuple[float, float]],
        mode: str = "drive",
        avoid: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive route information including all available details
        
        Args:
            waypoints: List of (latitude, longitude) tuples
            mode: Transportation mode
            avoid: List of things to avoid
            
        Returns:
            Structured route information including geometry, instructions, and details
        """
        try:
            # Get full route data with all details
            route_data = await self.calculate_route(
                waypoints=waypoints,
                mode=mode,
                include_instructions=True,
                include_route_details=True,
                include_elevation=False,  # Can be enabled if needed
                avoid=avoid
            )
            
            if not route_data.get("results") or not route_data["results"]:
                raise Exception("No route found in API response")
            
            route = route_data["results"][0]
            logger.debug(f"[RoutingService] Route type: {type(route)}")
            logger.debug(f"[RoutingService] Route keys: {list(route.keys()) if isinstance(route, dict) else 'Not a dict'}")
            
            # Ensure route is a dictionary
            if not isinstance(route, dict):
                logger.error(f"[RoutingService] Expected route to be dict, got {type(route)}: {route}")
                raise Exception(f"Invalid route data structure: expected dict, got {type(route)}")
            
            # Extract route geometry - try route level first, then legs
            coordinates = []
            
            # Method 1: Try route-level geometry first
            route_geometry = route.get("geometry", {})
            if route_geometry.get("coordinates"):
                coordinates = route_geometry["coordinates"]
                logger.debug(f"[RoutingService] Found {len(coordinates)} route-level coordinates")
            else:
                # Method 2: Extract from legs if no route-level coordinates
                logger.debug(f"[RoutingService] No route-level coordinates, trying legs")
                legs = route.get("legs", [])
                for i, leg in enumerate(legs):
                    if not isinstance(leg, dict):
                        logger.error(f"[RoutingService] Coordinate extraction: Leg {i} is not a dict: {leg}")
                        continue
                        
                    leg_coords = leg.get("geometry", {}).get("coordinates", [])
                    if coordinates:
                        leg_coords = leg_coords[1:]  # Skip first to avoid duplication
                    coordinates.extend(leg_coords)
                logger.debug(f"[RoutingService] Extracted {len(coordinates)} coordinates from legs")
            
            # Convert coordinates from [lon, lat] to [lat, lon]
            formatted_coords = [[coord[1], coord[0]] for coord in coordinates]
            
            # Extract turn-by-turn instructions
            instructions = []
            legs = route.get("legs", [])
            logger.debug(f"[RoutingService] Legs type: {type(legs)}, count: {len(legs) if isinstance(legs, list) else 'not a list'}")
            
            for i, leg in enumerate(legs):
                logger.debug(f"[RoutingService] Leg {i} type: {type(leg)}")
                if not isinstance(leg, dict):
                    logger.error(f"[RoutingService] Leg {i} is not a dict: {leg}")
                    continue
                    
                for step in leg.get("steps", []):
                    instruction = step.get("instruction", {})
                    if instruction and instruction.get("text"):
                        instructions.append({
                            "text": instruction["text"],
                            "type": instruction.get("type"),
                            "distance": step.get("distance", 0),
                            "time": step.get("time", 0),
                            "from_index": step.get("from_index"),
                            "to_index": step.get("to_index")
                        })
            
            # Extract speed limits and road details
            road_details = []
            legs = route.get("legs", [])
            for i, leg in enumerate(legs):
                if not isinstance(leg, dict):
                    logger.error(f"[RoutingService] Road details: Leg {i} is not a dict: {leg}")
                    continue
                    
                for step in leg.get("steps", []):
                    detail = {
                        "distance": step.get("distance", 0),
                        "time": step.get("time", 0),
                        "speed_limit": step.get("speed_limit"),
                        "road_class": step.get("road_class"),
                        "surface": step.get("surface"),
                        "lane_count": step.get("lane_count"),
                        "name": step.get("name"),
                        "toll": step.get("toll", False),
                        "ferry": step.get("ferry", False),
                        "tunnel": step.get("tunnel", False),
                        "bridge": step.get("bridge", False)
                    }
                    road_details.append(detail)
            
            # Build comprehensive route info
            detailed_info = {
                # Basic route information
                "distance": route.get("distance", 0),
                "duration": route.get("time", 0),
                "coordinates": formatted_coords,
                "toll": route.get("toll", False),
                "ferry": route.get("ferry", False),
                
                # Turn-by-turn instructions
                "instructions": instructions,
                
                # Road details
                "road_details": road_details,
                
                # Route legs information
                "legs": route.get("legs", []),
                
                # Original API response for reference
                "raw_response": route_data
            }
            
            logger.info(f"[RoutingService] Generated detailed route info: {route.get('distance', 0)}m, {route.get('time', 0)}s, {len(instructions)} instructions")
            
            return detailed_info
            
        except Exception as e:
            logger.error(f"[RoutingService] Failed to get detailed route info: {e}")
            raise

    async def get_detailed_route_info_object(
        self,
        waypoints: List[Tuple[float, float]],
        mode: str = "drive",
        avoid: Optional[List[str]] = None
    ):
        """
        Get comprehensive route information as DetailedRouteInfo object
        
        Args:
            waypoints: List of (latitude, longitude) tuples
            mode: Transportation mode
            avoid: List of things to avoid
            
        Returns:
            DetailedRouteInfo object with all route data
        """
        try:
            # Import here to avoid circular imports
            from schemas.entities import DetailedRouteInfo, TurnByTurnInstruction, RoadDetail
            
            # Get detailed route data
            route_data = await self.get_detailed_route_info(waypoints, mode, avoid)
            
            # Create DetailedRouteInfo object
            detailed_route_info = DetailedRouteInfo(
                distance=route_data["distance"],
                duration=route_data["duration"],
                coordinates=route_data["coordinates"],
                toll=route_data.get("toll", False),
                ferry=route_data.get("ferry", False),
                instructions=[
                    TurnByTurnInstruction(**instruction) 
                    for instruction in route_data.get("instructions", [])
                ],
                road_details=[
                    RoadDetail(**detail) 
                    for detail in route_data.get("road_details", [])
                ],
                raw_response=route_data.get("raw_response")
            )
            
            logger.info(f"[RoutingService] Created DetailedRouteInfo object: {detailed_route_info.distance}m, {detailed_route_info.duration}s")
            return detailed_route_info
            
        except Exception as e:
            logger.error(f"[RoutingService] Failed to get DetailedRouteInfo object: {e}")
            raise

    def format_waypoints_from_trip(self, origin: Dict, destination: Dict, waypoints: Optional[List[Dict]] = None) -> List[Tuple[float, float]]:
        """
        Convert trip waypoints to format expected by routing service
        
        Args:
            origin: Origin waypoint with location.coordinates [lon, lat]
            destination: Destination waypoint with location.coordinates [lon, lat]
            waypoints: Optional intermediate waypoints
            
        Returns:
            List of (latitude, longitude) tuples
        """
        try:
            formatted_waypoints = []
            
            # Add origin
            origin_coords = origin["location"]["coordinates"]
            formatted_waypoints.append((origin_coords[1], origin_coords[0]))  # Convert to (lat, lon)
            
            # Add intermediate waypoints if any
            if waypoints:
                sorted_waypoints = sorted(waypoints, key=lambda w: w.get("order", 0))
                for waypoint in sorted_waypoints:
                    coords = waypoint["location"]["coordinates"]
                    formatted_waypoints.append((coords[1], coords[0]))  # Convert to (lat, lon)
            
            # Add destination
            dest_coords = destination["location"]["coordinates"]
            formatted_waypoints.append((dest_coords[1], dest_coords[0]))  # Convert to (lat, lon)
            
            logger.debug(f"[RoutingService] Formatted {len(formatted_waypoints)} waypoints for routing")
            return formatted_waypoints
            
        except Exception as e:
            logger.error(f"[RoutingService] Failed to format waypoints: {e}")
            raise


# Global instance
routing_service = RoutingService()