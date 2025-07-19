"""
Test script to verify the cleaned up routing system
"""

import requests
import json
import time

# Test endpoints
CORE_URL = "http://localhost:8000"  # Core service
MGMT_URL = "http://localhost:8001"  # Management service

def test_core_routing():
    """Test the Core service routing"""
    print("🧪 Testing Core Service Routing...")
    
    try:
        # Test root endpoint
        response = requests.get(f"{CORE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Core root endpoint: {data.get('service', 'N/A')}")
            print(f"   Routing info: {data.get('routing', {})}")
        else:
            print(f"❌ Core root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Core root endpoint error: {e}")
    
    try:
        # Test services endpoint
        response = requests.get(f"{CORE_URL}/services")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Services endpoint: {data.get('services', [])}")
        else:
            print(f"❌ Services endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Services endpoint error: {e}")
    
    # Test management routing
    test_paths = [
        "/management/vehicles",
        "/management/drivers", 
        "/management/analytics"
    ]
    
    for path in test_paths:
        try:
            response = requests.get(f"{CORE_URL}{path}")
            print(f"✅ {path}: {response.status_code}")
        except Exception as e:
            print(f"❌ {path} error: {e}")

def test_management_service():
    """Test the Management service directly"""
    print("\n🧪 Testing Management Service...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{MGMT_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Management health: {data.get('status', 'N/A')}")
        else:
            print(f"❌ Management health failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Management health error: {e}")
    
    try:
        # Test root endpoint
        response = requests.get(f"{MGMT_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Management root: {data.get('service', 'N/A')}")
        else:
            print(f"❌ Management root failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Management root error: {e}")
    
    # Test the main routes
    test_routes = [
        "/vehicles",
        "/drivers",
        "/analytics"
    ]
    
    for route in test_routes:
        try:
            response = requests.get(f"{MGMT_URL}{route}")
            print(f"✅ {route}: {response.status_code}")
        except Exception as e:
            print(f"❌ {route} error: {e}")

if __name__ == "__main__":
    print("🚀 Testing SAMFMS Cleaned Up Routing System")
    print("=" * 50)
    
    test_core_routing()
    test_management_service()
    
    print("\n🎉 Testing completed!")
