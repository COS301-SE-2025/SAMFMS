"""
Quick test for coordinate extraction
"""
import sys
import os
sys.path.append(os.path.abspath('.'))

import asyncio
from services.routing_service import RoutingService

async def test_coordinates():
    """Quick test for coordinate extraction"""
    
    routing_service = RoutingService()
    
    # Test waypoints: Cape Town to Stellenbosch  
    waypoints = [(-33.9249, 18.4241), (-33.9321, 18.8602)]
    
    print(f"Testing coordinate extraction for route: {waypoints}")
    
    try:
        # Test get_route_geometry
        coords = await routing_service.get_route_geometry(waypoints)
        print(f"✅ get_route_geometry returned {len(coords)} coordinates")
        if coords:
            print(f"First 3 coordinates: {coords[:3]}")
        
        # Test get_detailed_route_info_object  
        detailed_info = await routing_service.get_detailed_route_info_object(waypoints)
        print(f"✅ DetailedRouteInfo has {len(detailed_info.coordinates)} coordinates")
        if detailed_info.coordinates:
            print(f"First 3 detailed coordinates: {detailed_info.coordinates[:3]}")
        
        print(f"Route distance: {detailed_info.distance}m")
        print(f"Route duration: {detailed_info.duration}s")
        print(f"Instructions count: {len(detailed_info.instructions)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_coordinates())