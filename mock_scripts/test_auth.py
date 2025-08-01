#!/usr/bin/env python3
"""
Authentication Test Script
Tests login functionality and token retrieval
"""

import asyncio
import sys
from api_utils import AuthenticationManager, logger
from config import CORE_BASE_URL, MAINTENANCE_BASE_URL, LOGIN_EMAIL


async def test_authentication():
    """Test authentication with both services"""
    logger.info("🔐 Testing SAMFMS Authentication")
    logger.info("=" * 40)
    
    success_count = 0
    total_tests = 2
    
    # Test Core service authentication
    logger.info("Testing Core service authentication...")
    core_auth = AuthenticationManager(CORE_BASE_URL)
    core_success = await core_auth.login()
    
    if core_success:
        logger.info(f"✅ Core service login successful")
        logger.info(f"   Token: {core_auth.token[:20]}..." if core_auth.token else "   No token received")
        if core_auth.user_info:
            logger.info(f"   User: {core_auth.user_info.get('email', 'Unknown')}")
        success_count += 1
    else:
        logger.error("❌ Core service login failed")
    
    # Test Maintenance service authentication  
    logger.info("\nTesting Maintenance service authentication...")
    maintenance_auth = AuthenticationManager(MAINTENANCE_BASE_URL)
    maintenance_success = await maintenance_auth.login()
    
    if maintenance_success:
        logger.info(f"✅ Maintenance service login successful")
        logger.info(f"   Token: {maintenance_auth.token[:20]}..." if maintenance_auth.token else "   No token received")
        if maintenance_auth.user_info:
            logger.info(f"   User: {maintenance_auth.user_info.get('email', 'Unknown')}")
        success_count += 1
    else:
        logger.error("❌ Maintenance service login failed")
    
    # Summary
    logger.info("\n" + "=" * 40)
    logger.info(f"Authentication Test Results: {success_count}/{total_tests} successful")
    
    if success_count == total_tests:
        logger.info("🎉 All authentication tests passed!")
        logger.info("✅ Ready to run mock data generation scripts")
        return True
    elif success_count > 0:
        logger.warning("⚠️  Partial authentication success")
        logger.warning("   Some services may not work correctly")
        return False
    else:
        logger.error("❌ All authentication tests failed")
        logger.error("💡 Please check:")
        logger.error("   1. Services are running (Core: 21000, Maintenance: 21004)")
        logger.error("   2. Email and password are correct")
        logger.error("   3. User account exists and is active")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test SAMFMS authentication")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Testing authentication for: {LOGIN_EMAIL}")
    
    try:
        success = asyncio.run(test_authentication())
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during authentication test: {e}")
        sys.exit(1)
