#!/usr/bin/env python3
"""
Simple test to debug coordinate extraction from Geoapify API
"""
import sys
import os
sys.path.append(os.path.abspath('.'))

import asyncio
import json
from services.routing_service import RoutingService

async def test_coordinate_extraction():
    """Test coordinate extraction with real API call"""
    
    print("🔍 Testing coordinate extraction...")
    
    routing_service = RoutingService()
    
    # Test waypoints: Cape Town to Stellenbosch  
    waypoints = [(-33.9249, 18.4241), (-33.9321, 18.8602)]
    
    try:
        # Get raw route data first
        print("📡 Making API call...")
        route_data = await routing_service.calculate_route(
            waypoints=waypoints,
            mode="drive",
            include_instructions=True,
            include_route_details=True
        )
        
        print("✅ API call successful!")
        print(f"📊 Top-level keys: {list(route_data.keys())}")
        
        if route_data.get("results"):
            route = route_data["results"][0]
            print(f"🗺️  Route keys: {list(route.keys())}")
            
            # Check route-level geometry
            if route.get("geometry"):
                geometry = route["geometry"]
                print(f"📐 Route-level geometry keys: {list(geometry.keys())}")
                if geometry.get("coordinates"):
                    coords = geometry["coordinates"]
                    print(f"📍 Route-level coordinates found: {len(coords)} points")
                    print(f"🎯 First 3 coordinates: {coords[:3]}")
                else:
                    print("❌ No route-level coordinates found")
            else:
                print("❌ No route-level geometry found")
            
            # Check leg-level geometry
            if route.get("legs"):
                legs = route["legs"]
                print(f"🦵 Found {len(legs)} legs")
                
                total_leg_coords = 0
                for i, leg in enumerate(legs):
                    print(f"🦵 Leg {i} keys: {list(leg.keys())}")
                    if leg.get("geometry"):
                        leg_geometry = leg["geometry"]
                        print(f"📐 Leg {i} geometry keys: {list(leg_geometry.keys())}")
                        if leg_geometry.get("coordinates"):
                            leg_coords = leg_geometry["coordinates"]
                            print(f"📍 Leg {i} coordinates: {len(leg_coords)} points")
                            print(f"🎯 Leg {i} first 3 coordinates: {leg_coords[:3]}")
                            total_leg_coords += len(leg_coords)
                        else:
                            print(f"❌ No coordinates in leg {i}")
                    else:
                        print(f"❌ No geometry in leg {i}")
                
                print(f"📊 Total leg coordinates: {total_leg_coords}")
            else:
                print("❌ No legs found")
        
        # Now test our get_detailed_route_info method
        print("\n🧪 Testing get_detailed_route_info method...")
        detailed_info = await routing_service.get_detailed_route_info(waypoints)
        print(f"📍 Extracted coordinates: {len(detailed_info.get('coordinates', []))}")
        if detailed_info.get('coordinates'):
            print(f"🎯 First 3 extracted coordinates: {detailed_info['coordinates'][:3]}")
        else:
            print("❌ No coordinates extracted by method")
        
        # Save raw response for inspection
        with open("/tmp/route_debug.json", "w") as f:
            json.dump(route_data, f, indent=2)
        print("💾 Raw response saved to /tmp/route_debug.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_coordinate_extraction())