#!/usr/bin/env python3
"""
Test script to create a trip and trigger detailed route info fetching
"""
import sys
import os
sys.path.append('/home/samfms/samfms-docker-deploy/repo/SAMFMS/Sblocks/trip_planning')

import asyncio
import json
from datetime import datetime, timedelta

# Test the routing service directly first
async def test_routing_service_directly():
    """Test the routing service to see what's causing the error"""
    print("🧪 Testing routing service directly...")
    
    try:
        from services.routing_service import routing_service
        
        # Test waypoints: Cape Town to Stellenbosch  
        waypoints = [(-33.9249, 18.4241), (-33.9321, 18.8602)]
        
        print(f"📍 Testing with waypoints: {waypoints}")
        
        # Step 1: Test basic route calculation first
        print("\n1️⃣ Testing calculate_route...")
        route_data = await routing_service.calculate_route(
            waypoints=waypoints,
            mode="drive",
            include_instructions=True,
            include_route_details=True
        )
        
        print(f"✅ calculate_route succeeded")
        print(f"📊 Response keys: {list(route_data.keys())}")
        if route_data.get("results"):
            print(f"📈 Results count: {len(route_data['results'])}")
            if route_data["results"]:
                result = route_data["results"][0]
                print(f"🗺️ First result type: {type(result)}")
                print(f"🗺️ First result sample: {str(result)[:200]}")
        
        # Step 2: Test get_detailed_route_info method
        print("\n2️⃣ Testing get_detailed_route_info...")
        try:
            detailed_info = await routing_service.get_detailed_route_info(waypoints)
            print(f"✅ get_detailed_route_info succeeded")
            print(f"📊 Detailed info keys: {list(detailed_info.keys())}")
            print(f"📍 Coordinates count: {len(detailed_info.get('coordinates', []))}")
        except Exception as e:
            print(f"❌ get_detailed_route_info failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 3: Test get_detailed_route_info_object
        print("\n3️⃣ Testing get_detailed_route_info_object...")
        try:
            detailed_obj = await routing_service.get_detailed_route_info_object(waypoints)
            print(f"✅ get_detailed_route_info_object succeeded")
            print(f"📊 Object type: {type(detailed_obj)}")
            print(f"📍 Coordinates count: {len(detailed_obj.coordinates)}")
            print(f"📏 Distance: {detailed_obj.distance}m")
            print(f"⏱️ Duration: {detailed_obj.duration}s")
        except Exception as e:
            print(f"❌ get_detailed_route_info_object failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error testing routing service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_routing_service_directly())