"""
Mock implementation to test coordinate extraction fix
This file simulates the coordinate extraction logic to verify it works correctly
"""

def extract_coordinates_from_route(route_data):
    """
    Mock function to test coordinate extraction logic
    """
    if not route_data.get("results"):
        return []
    
    route = route_data["results"][0]
    coordinates = []
    
    # Method 1: Try route-level geometry first (most common)
    route_geometry = route.get("geometry", {})
    if route_geometry.get("coordinates"):
        coordinates = route_geometry["coordinates"]
        print(f"✅ Found {len(coordinates)} route-level coordinates")
    else:
        # Method 2: Extract from legs if no route-level coordinates
        print("⚠️ No route-level coordinates, trying legs")
        for leg in route.get("legs", []):
            leg_coords = leg.get("geometry", {}).get("coordinates", [])
            if coordinates:
                # Skip first coordinate of subsequent legs to avoid duplication
                leg_coords = leg_coords[1:]
            coordinates.extend(leg_coords)
        print(f"✅ Extracted {len(coordinates)} coordinates from legs")
    
    # Convert from [lon, lat] to [lat, lon] format
    formatted_coords = [[coord[1], coord[0]] for coord in coordinates]
    
    return formatted_coords

# Test with mock data that represents typical Geoapify response
mock_route_data = {
    "results": [{
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [18.4241, -33.9249],  # lon, lat format from API
                [18.5000, -33.9300],
                [18.6000, -33.9350],
                [18.8602, -33.9321]
            ]
        },
        "legs": [
            {
                "distance": 50000,
                "time": 3600,
                "geometry": {
                    "type": "LineString", 
                    "coordinates": [
                        [18.4241, -33.9249],
                        [18.5000, -33.9300],
                        [18.6000, -33.9350],
                        [18.8602, -33.9321]
                    ]
                }
            }
        ]
    }]
}

if __name__ == "__main__":
    print("🧪 Testing coordinate extraction with mock data")
    print("=" * 50)
    
    coordinates = extract_coordinates_from_route(mock_route_data)
    
    print(f"📍 Extracted {len(coordinates)} coordinates")
    if coordinates:
        print(f"🎯 First coordinate (lat,lon): {coordinates[0]}")
        print(f"🎯 Last coordinate (lat,lon): {coordinates[-1]}")
        print(f"📊 All coordinates: {coordinates}")
    else:
        print("❌ No coordinates extracted")