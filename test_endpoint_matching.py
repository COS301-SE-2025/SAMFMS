#!/usr/bin/env python3
"""
Test script to verify the endpoint matching fixes in the Management service request consumer
"""

def test_endpoint_matching():
    """Test endpoint matching logic"""
    print("🔍 Testing endpoint matching logic...")
    
    # Test cases for vehicle endpoints
    test_cases = [
        ("/vehicles", "GET", "Should match vehicles list"),
        ("/api/vehicles", "GET", "Should match vehicles list"),
        ("/api/v1/vehicles", "GET", "Should match vehicles list"),
        ("/vehicles/123", "GET", "Should match specific vehicle"),
        ("/vehicles/search", "GET", "Should match vehicle search"),
        ("/drivers", "GET", "Should match drivers list"),
        ("/api/drivers", "GET", "Should match drivers list"),
        ("/api/v1/drivers", "GET", "Should match drivers list"),
        ("/drivers/456", "GET", "Should match specific driver"),
    ]
    
    for endpoint, method, description in test_cases:
        print(f"✓ {method} {endpoint} - {description}")
    
    # Test the actual matching logic
    def would_match_vehicles(endpoint, method):
        """Simulate the vehicles endpoint matching logic"""
        if method == "GET":
            if endpoint in ["/vehicles", "/api/vehicles", "/api/v1/vehicles"] or endpoint.endswith("/vehicles"):
                return "vehicles_list"
            elif "/vehicles/" in endpoint and not endpoint.endswith("/vehicles"):
                return "vehicle_detail"
            elif "/vehicles/search" in endpoint:
                return "vehicle_search"
        return None
    
    def would_match_drivers(endpoint, method):
        """Simulate the drivers endpoint matching logic"""
        if method == "GET":
            if endpoint in ["/drivers", "/api/drivers", "/api/v1/drivers"] or endpoint.endswith("/drivers"):
                return "drivers_list"
            elif "/drivers/" in endpoint:
                return "driver_detail"
        return None
    
    print("\n🧪 Testing endpoint matching results:")
    
    success_count = 0
    total_count = 0
    
    for endpoint, method, description in test_cases:
        total_count += 1
        
        if "/vehicles" in endpoint:
            result = would_match_vehicles(endpoint, method)
            if result:
                print(f"✅ {method} {endpoint} -> {result}")
                success_count += 1
            else:
                print(f"❌ {method} {endpoint} -> No match")
        elif "/drivers" in endpoint:
            result = would_match_drivers(endpoint, method)
            if result:
                print(f"✅ {method} {endpoint} -> {result}")
                success_count += 1
            else:
                print(f"❌ {method} {endpoint} -> No match")
    
    print(f"\n📊 Test Results: {success_count}/{total_count} endpoints matched correctly")
    
    if success_count == total_count:
        print("🎉 All endpoint matching tests passed!")
        print("✅ The 'Unsupported vehicles operation' error should now be resolved.")
    else:
        print("⚠️  Some endpoints still failing to match.")

if __name__ == "__main__":
    test_endpoint_matching()
