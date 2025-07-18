"""
Test script for the new simplified service routing system
"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Core service URL
CORE_URL = "http://localhost:21014"

async def test_service_routing():
    """Test the new service routing system"""
    
    async with aiohttp.ClientSession() as session:
        logger.info("🧪 Testing SAMFMS Core Service Routing")
        
        # Test 1: Check root endpoint
        try:
            async with session.get(f"{CORE_URL}/") as response:
                data = await response.json()
                logger.info(f"✅ Root endpoint: {data['service']}")
                logger.info(f"   Routing info: {data.get('routing', {})}")
        except Exception as e:
            logger.error(f"❌ Root endpoint failed: {e}")
        
        # Test 2: Check services endpoint
        try:
            async with session.get(f"{CORE_URL}/services") as response:
                data = await response.json()
                logger.info(f"✅ Services endpoint: {data['services']}")
        except Exception as e:
            logger.error(f"❌ Services endpoint failed: {e}")
        
        # Test 3: Test management service routing
        test_cases = [
            ("GET", "/management/vehicles", None, "List vehicles"),
            ("GET", "/management/drivers", None, "List drivers"),
            ("GET", "/management/assignments", None, "List assignments"),
            ("POST", "/management/vehicles", {"make": "Toyota", "model": "Camry"}, "Create vehicle"),
            ("GET", "/maintenance/schedules", None, "List maintenance schedules"),
            ("GET", "/gps/locations", None, "List GPS locations"),
            ("GET", "/trips/routes", None, "List trip routes")
        ]
        
        for method, path, body, description in test_cases:
            try:
                logger.info(f"🧪 Testing {method} {path} - {description}")
                
                if method == "GET":
                    async with session.get(f"{CORE_URL}{path}") as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"✅ {method} {path}: {response.status} - {data}")
                        else:
                            text = await response.text()
                            logger.info(f"⚠️  {method} {path}: {response.status} - {text}")
                
                elif method == "POST":
                    async with session.post(f"{CORE_URL}{path}", json=body) as response:
                        if response.status in [200, 201]:
                            data = await response.json()
                            logger.info(f"✅ {method} {path}: {response.status} - {data}")
                        else:
                            text = await response.text()
                            logger.info(f"⚠️  {method} {path}: {response.status} - {text}")
                
            except Exception as e:
                logger.error(f"❌ {method} {path} failed: {e}")
            
            # Small delay between requests
            await asyncio.sleep(0.5)
        
        logger.info("🏁 Service routing tests completed")

async def test_health_check():
    """Test health check endpoint"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{CORE_URL}/health") as response:
                data = await response.json()
                logger.info(f"✅ Health check: {data['status']}")
                logger.info(f"   Service: {data['service']}")
                logger.info(f"   Environment: {data['environment']}")
                return data['status'] == 'healthy'
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting SAMFMS Core Service Routing Tests")
    
    # Wait for service to be ready
    logger.info("⏳ Waiting for Core service to be ready...")
    for i in range(30):
        if await test_health_check():
            logger.info("✅ Core service is ready")
            break
        await asyncio.sleep(2)
    else:
        logger.error("❌ Core service not ready after 60 seconds")
        return
    
    # Run routing tests
    await test_service_routing()
    
    logger.info("🎉 All tests completed")

if __name__ == "__main__":
    asyncio.run(main())
