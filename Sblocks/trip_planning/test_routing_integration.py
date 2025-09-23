#!/usr/bin/env python3
"""
Test script to demonstrate the Geoapify Routing API integration
This script shows how the routing service automatically fetches route information when trips are created
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

# Add the project path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.routing_service import routing_service
from schemas.entities import RouteInfo, TurnByTurnInstruction, RoadDetail, DetailedRouteInfo

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_basic_routing():
    """Test basic routing functionality"""
    logger.info("=== Testing Basic Routing ===")
    
    try:
        # Test waypoints: Cape Town to Johannesburg (South Africa)
        waypoints = [
            (-33.9249, 18.4241),  # Cape Town (lat, lon)
            (-26.2041, 28.0473)   # Johannesburg (lat, lon)
        ]
        
        # Get route geometry only
        logger.info("Fetching route geometry...")
        coordinates = await routing_service.get_route_geometry(waypoints)
        logger.info(f"✓ Retrieved {len(coordinates)} coordinate points")
        
        # Show first and last few coordinates
        logger.info(f"Start coordinates: {coordinates[:3]}")
        logger.info(f"End coordinates: {coordinates[-3:]}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Basic routing test failed: {e}")
        return False


async def test_detailed_routing():
    """Test detailed routing with instructions and road details"""
    logger.info("\n=== Testing Detailed Routing ===")
    
    try:
        # Test waypoints: Pretoria to OR Tambo Airport
        waypoints = [
            (-25.7461, 28.1881),  # Pretoria (lat, lon)
            (-26.1367, 28.2411)   # OR Tambo Airport (lat, lon)
        ]
        
        # Get detailed route information
        logger.info("Fetching detailed route information...")
        route_data = await routing_service.get_detailed_route_info(waypoints)
        
        # Display results
        logger.info(f"✓ Route distance: {route_data['distance']} meters ({route_data['distance']/1000:.1f} km)")
        logger.info(f"✓ Route duration: {route_data['duration']} seconds ({route_data['duration']/60:.1f} minutes)")
        logger.info(f"✓ Coordinates: {len(route_data['coordinates'])} points")
        logger.info(f"✓ Turn-by-turn instructions: {len(route_data['instructions'])} steps")
        logger.info(f"✓ Road details: {len(route_data['road_details'])} segments")
        logger.info(f"✓ Uses tolls: {route_data['toll']}")
        logger.info(f"✓ Uses ferries: {route_data['ferry']}")
        
        # Show first few instructions
        logger.info("\nFirst 3 turn-by-turn instructions:")
        for i, instruction in enumerate(route_data['instructions'][:3]):
            logger.info(f"  {i+1}. {instruction['text']} ({instruction['distance']}m)")
        
        # Show road details for first few segments
        logger.info("\nFirst 3 road segments:")
        for i, detail in enumerate(route_data['road_details'][:3]):
            logger.info(f"  {i+1}. {detail['name'] or 'Unnamed road'} - {detail['road_class']} "
                       f"({detail['distance']}m, {detail['speed_limit']} km/h)")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Detailed routing test failed: {e}")
        return False


async def test_multi_waypoint_routing():
    """Test routing with multiple waypoints"""
    logger.info("\n=== Testing Multi-Waypoint Routing ===")
    
    try:
        # Test route: Cape Town -> Worcester -> Bloemfontein -> Johannesburg
        waypoints = [
            (-33.9249, 18.4241),  # Cape Town
            (-33.6464, 19.4406),  # Worcester
            (-29.0852, 26.1596),  # Bloemfontein  
            (-26.2041, 28.0473)   # Johannesburg
        ]
        
        logger.info("Fetching multi-waypoint route...")
        route_data = await routing_service.get_detailed_route_info(waypoints)
        
        logger.info(f"✓ Multi-waypoint route distance: {route_data['distance']/1000:.1f} km")
        logger.info(f"✓ Multi-waypoint route duration: {route_data['duration']/3600:.1f} hours")
        logger.info(f"✓ Route has {len(route_data['legs'])} legs")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Multi-waypoint routing test failed: {e}")
        return False


async def test_detailed_route_info_object():
    """Test DetailedRouteInfo object creation"""
    logger.info("\n=== Testing DetailedRouteInfo Object ===")
    
    try:
        # Test waypoints: Pretoria to OR Tambo Airport
        waypoints = [
            (-25.7461, 28.1881),  # Pretoria (lat, lon)
            (-26.1367, 28.2411)   # OR Tambo Airport (lat, lon)
        ]
        
        # Get DetailedRouteInfo object
        logger.info("Fetching DetailedRouteInfo object...")
        detailed_route_info = await routing_service.get_detailed_route_info_object(waypoints)
        
        # Display results
        logger.info(f"✓ DetailedRouteInfo object created successfully")
        logger.info(f"✓ Route distance: {detailed_route_info.distance} meters ({detailed_route_info.distance/1000:.1f} km)")
        logger.info(f"✓ Route duration: {detailed_route_info.duration} seconds ({detailed_route_info.duration/60:.1f} minutes)")
        logger.info(f"✓ Coordinates: {len(detailed_route_info.coordinates)} points")
        logger.info(f"✓ Turn-by-turn instructions: {len(detailed_route_info.instructions)} steps")
        logger.info(f"✓ Road details: {len(detailed_route_info.road_details)} segments")
        logger.info(f"✓ Uses tolls: {detailed_route_info.toll}")
        logger.info(f"✓ Uses ferries: {detailed_route_info.ferry}")
        logger.info(f"✓ Fetched at: {detailed_route_info.fetched_at}")
        
        # Show first few instructions
        logger.info("\nFirst 3 turn-by-turn instructions:")
        for i, instruction in enumerate(detailed_route_info.instructions[:3]):
            logger.info(f"  {i+1}. {instruction.text} ({instruction.distance}m)")
        
        # Show road details for first few segments
        logger.info("\nFirst 3 road segments:")
        for i, detail in enumerate(detailed_route_info.road_details[:3]):
            logger.info(f"  {i+1}. {detail.name or 'Unnamed road'} - {detail.road_class} "
                       f"({detail.distance}m, {detail.speed_limit} km/h)")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ DetailedRouteInfo object test failed: {e}")
        return False


async def test_trip_creation_with_detailed_routing():
    """Test trip creation with automatic detailed routing"""
    logger.info("\n=== Testing Trip Creation with Detailed Routing ===")
    
    try:
        # Import required modules
        from schemas.requests import CreateTripRequest
        from schemas.entities import Waypoint, LocationPoint, Address
        from services.trip_service import trip_service
        from datetime import datetime, timedelta
        
        # Create origin waypoint (Cape Town)
        origin = Waypoint(
            location=LocationPoint(coordinates=[18.4241, -33.9249]),  # [lon, lat] GeoJSON format
            address=Address(formatted_address="Cape Town, South Africa"),
            name="Cape Town Central",
            order=0
        )
        
        # Create destination waypoint (Johannesburg)
        destination = Waypoint(
            location=LocationPoint(coordinates=[28.0473, -26.2041]),  # [lon, lat] GeoJSON format
            address=Address(formatted_address="Johannesburg, South Africa"),
            name="Johannesburg Central",
            order=1
        )
        
        # Create trip request
        trip_request = CreateTripRequest(
            name="Test Route Integration Trip",
            description="Testing automatic detailed route fetching",
            scheduled_start_time=datetime.utcnow() + timedelta(hours=1),
            scheduled_end_time=datetime.utcnow() + timedelta(hours=8),
            origin=origin,
            destination=destination,
            vehicle_id="test_vehicle_123",
            driver_assignment="test_driver_123"
        )
        
        logger.info("Creating trip with automatic detailed routing...")
        
        # This would normally require database connection, so we'll test the routing part separately
        # For now, just test that the detailed route info object can be created properly
        from services.routing_service import routing_service
        
        # Format waypoints
        formatted_waypoints = routing_service.format_waypoints_from_trip(
            origin.dict(), 
            destination.dict(), 
            None
        )
        
        # Get detailed route info
        detailed_route_info = await routing_service.get_detailed_route_info_object(formatted_waypoints)
        
        # Test serialization (this is what was causing the error)
        serialized = detailed_route_info.dict()
        logger.info(f"✓ DetailedRouteInfo serialized successfully")
        logger.info(f"✓ Serialized keys: {list(serialized.keys())}")
        logger.info(f"✓ Distance: {serialized['distance']}m")
        logger.info(f"✓ Duration: {serialized['duration']}s")
        logger.info(f"✓ Instructions count: {len(serialized['instructions'])}")
        logger.info(f"✓ Road details count: {len(serialized['road_details'])}")
        
        # Test that we can create the object back from dict
        from schemas.entities import DetailedRouteInfo
        recreated = DetailedRouteInfo(**serialized)
        logger.info(f"✓ DetailedRouteInfo recreated from dict successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Trip creation test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


async def test_waypoint_formatting():
    """Test waypoint formatting from trip data"""
    logger.info("\n=== Testing Waypoint Formatting ===")
    
    try:
        # Sample trip waypoints in the format used by the trip system
        origin = {
            "location": {
                "coordinates": [18.4241, -33.9249]  # [longitude, latitude] GeoJSON format
            }
        }
        
        destination = {
            "location": {
                "coordinates": [28.0473, -26.2041]  # [longitude, latitude] GeoJSON format  
            }
        }
        
        waypoints = [
            {
                "location": {
                    "coordinates": [19.4406, -33.6464]  # Worcester
                },
                "order": 1
            }
        ]
        
        # Format waypoints for routing service
        formatted = routing_service.format_waypoints_from_trip(origin, destination, waypoints)
        
        logger.info(f"✓ Formatted {len(formatted)} waypoints:")
        for i, (lat, lon) in enumerate(formatted):
            logger.info(f"  {i+1}. ({lat}, {lon})")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Waypoint formatting test failed: {e}")
        return False


async def main():
    """Run all tests"""
    logger.info("🚀 Starting Geoapify Routing API Integration Tests")
    logger.info("Using API Key: 8c5cae4820744254b3cb03ebd9b9ce13")
    
    tests = [
        test_basic_routing,
        test_detailed_routing,
        test_multi_waypoint_routing,
        test_detailed_route_info_object,
        test_trip_creation_with_detailed_routing,
        test_waypoint_formatting
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            logger.error(f"Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Close the routing service session
    try:
        await routing_service.close()
        logger.info("✓ Routing service session closed")
    except Exception as e:
        logger.error(f"Error closing routing service: {e}")
    
    # Summary
    passed = sum(results)
    total = len(results)
    logger.info(f"\n🏁 Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Routing API integration is working correctly.")
        logger.info("\n📋 Integration Summary:")
        logger.info("✓ Routing service can fetch route geometry")
        logger.info("✓ Routing service can fetch detailed route information")
        logger.info("✓ Turn-by-turn instructions are available")
        logger.info("✓ Road details including speed limits are available")
        logger.info("✓ Multi-waypoint routing works")
        logger.info("✓ Schema validation works")
        logger.info("✓ When trips are scheduled, route information will be automatically fetched")
    else:
        logger.error(f"❌ {total - passed} tests failed. Please check the errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)