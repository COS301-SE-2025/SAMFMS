"""
Direct API test to Geoapify
"""
import asyncio
import aiohttp
import json

async def test_geoapify_direct():
    """Test direct API call to Geoapify"""
    
    api_key = "8c5cae4820744254b3cb03ebd9b9ce13"
    base_url = "https://api.geoapify.com/v1/routing"
    
    # Cape Town to Stellenbosch  
    waypoints_str = "-33.9249,18.4241|-33.9321,18.8602"
    
    params = {
        "waypoints": waypoints_str,
        "mode": "drive", 
        "format": "json",
        "details": "instruction_details,route_details",
        "apiKey": api_key
    }
    
    print(f"Testing direct API call...")
    print(f"URL: {base_url}")
    print(f"Params: {params}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                print(f"Response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Print structure
                    print(f"Response keys: {list(data.keys())}")
                    
                    if data.get("results"):
                        route = data["results"][0] 
                        print(f"Route keys: {list(route.keys())}")
                        
                        # Check route-level geometry
                        if "geometry" in route:
                            geometry = route["geometry"]
                            print(f"Route geometry keys: {list(geometry.keys())}")
                            if "coordinates" in geometry:
                                coords = geometry["coordinates"]
                                print(f"Route-level coordinates: {len(coords)} points")
                                print(f"Sample coordinates: {coords[:3]}")
                                
                                # Test coordinate conversion
                                formatted = [[c[1], c[0]] for c in coords[:3]]
                                print(f"Formatted (lat,lon): {formatted}")
                        else:
                            print("No route-level geometry")
                        
                        # Check legs
                        if "legs" in route:
                            legs = route["legs"]
                            print(f"Legs: {len(legs)}")
                            for i, leg in enumerate(legs):
                                if "geometry" in leg:
                                    leg_geom = leg["geometry"]
                                    if "coordinates" in leg_geom:
                                        leg_coords = leg_geom["coordinates"]
                                        print(f"Leg {i} coordinates: {len(leg_coords)} points")
                                    else:
                                        print(f"Leg {i} has no coordinates")
                                else:
                                    print(f"Leg {i} has no geometry")
                else:
                    text = await response.text()
                    print(f"Error response: {text}")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_geoapify_direct())