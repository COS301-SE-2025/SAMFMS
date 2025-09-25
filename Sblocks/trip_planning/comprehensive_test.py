"""
Comprehensive test and fix for coordinate extraction
"""
import sys
import os
sys.path.append('/home/samfms/samfms-docker-deploy/repo/SAMFMS')

import asyncio
import json
from Sblocks.trip_planning.services.routing_service import RoutingService

async def comprehensive_coordinate_test():
    """Test coordinate extraction comprehensively"""
    
    print("🧪 Comprehensive Coordinate Test")
    print("=" * 50)
    
    routing_service = RoutingService()
    
    # Test waypoints: Cape Town to Stellenbosch  
    waypoints = [(-33.9249, 18.4241), (-33.9321, 18.8602)]
    
    print(f"📍 Testing route: {waypoints}")
    
    try:
        # Step 1: Test basic route calculation
        print("\n1️⃣ Testing basic route calculation...")
        route_data = await routing_service.calculate_route(
            waypoints=waypoints,
            mode="drive",
            include_instructions=True,
            include_route_details=True
        )
        
        if route_data.get("results"):
            route = route_data["results"][0]
            print(f"✅ Route calculation successful")
            print(f"📊 Route keys: {list(route.keys())}")
            
            # Check route-level geometry
            if route.get("geometry"):
                geometry = route["geometry"]
                print(f"📐 Route geometry keys: {list(geometry.keys())}")
                if geometry.get("coordinates"):
                    coords = geometry["coordinates"]
                    print(f"📍 Route-level coordinates: {len(coords)} points")
                    print(f"🎯 First coordinate (lon,lat): {coords[0]}")
                    print(f"🎯 Last coordinate (lon,lat): {coords[-1]}")
                    
                    # Show coordinate conversion
                    converted = [coords[0][1], coords[0][0]]  # lat, lon
                    print(f"🔄 Converted first coordinate (lat,lon): {converted}")
            
            # Check legs
            if route.get("legs"):
                print(f"🦵 Found {len(route['legs'])} legs")
                for i, leg in enumerate(route["legs"]):
                    if leg.get("geometry", {}).get("coordinates"):
                        leg_coords = leg["geometry"]["coordinates"]
                        print(f"🦵 Leg {i}: {len(leg_coords)} coordinates")
        
        # Step 2: Test get_route_geometry 
        print("\n2️⃣ Testing get_route_geometry...")
        geometry_coords = await routing_service.get_route_geometry(waypoints)
        print(f"📍 get_route_geometry returned: {len(geometry_coords)} coordinates")
        if geometry_coords:
            print(f"🎯 First coordinate: {geometry_coords[0]}")
            print(f"🎯 Last coordinate: {geometry_coords[-1]}")
        
        # Step 3: Test get_detailed_route_info
        print("\n3️⃣ Testing get_detailed_route_info...")
        detailed_info = await routing_service.get_detailed_route_info(waypoints)
        print(f"📍 Detailed info coordinates: {len(detailed_info.get('coordinates', []))}")
        if detailed_info.get('coordinates'):
            print(f"🎯 First coordinate: {detailed_info['coordinates'][0]}")
            print(f"🎯 Last coordinate: {detailed_info['coordinates'][-1]}")
        
        # Step 4: Test get_detailed_route_info_object
        print("\n4️⃣ Testing get_detailed_route_info_object...")
        detailed_obj = await routing_service.get_detailed_route_info_object(waypoints)
        print(f"📍 DetailedRouteInfo coordinates: {len(detailed_obj.coordinates)}")
        if detailed_obj.coordinates:
            print(f"🎯 First coordinate: {detailed_obj.coordinates[0]}")
            print(f"🎯 Last coordinate: {detailed_obj.coordinates[-1]}")
        
        print(f"📏 Distance: {detailed_obj.distance}m")
        print(f"⏱️ Duration: {detailed_obj.duration}s")
        print(f"📋 Instructions: {len(detailed_obj.instructions)}")
        print(f"🛣️ Road details: {len(detailed_obj.road_details)}")
        
        # Step 5: Show dictionary serialization
        print("\n5️⃣ Testing dictionary serialization...")
        obj_dict = detailed_obj.dict()
        print(f"📍 Serialized coordinates: {len(obj_dict.get('coordinates', []))}")
        
        # Save raw response for debugging
        with open("/tmp/routing_test_debug.json", "w") as f:
            json.dump({
                "raw_api_response": route_data,
                "detailed_info": detailed_info,
                "detailed_obj_dict": obj_dict
            }, f, indent=2)
        print("💾 Debug data saved to /tmp/routing_test_debug.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(comprehensive_coordinate_test())
    print(f"\n{'✅ Test completed successfully' if success else '❌ Test failed'}")