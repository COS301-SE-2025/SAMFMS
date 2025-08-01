#!/usr/bin/env python3
"""
Quick Start Example for SAMFMS Mock Data Generation
Shows how to use the scripts with authentication
"""

import asyncio
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_utils import logger


def print_banner():
    """Print welcome banner"""
    print("🚀 SAMFMS Mock Data Generation - Quick Start")
    print("=" * 50)
    print()
    print("This example will guide you through:")
    print("1. Testing authentication")
    print("2. Running a quick data generation test")
    print("3. Verifying the results")
    print()


def print_auth_instructions():
    """Print authentication setup instructions"""
    print("🔐 Authentication Setup")
    print("-" * 25)
    print()
    print("Your login email is configured as: mvanheerdentuks@gmail.com")
    print()
    print("You can set your password in several ways:")
    print()
    print("Option 1 - Environment Variable (recommended):")
    print("   Windows: set SAMFMS_LOGIN_PASSWORD=your_password")
    print("   Unix:    export SAMFMS_LOGIN_PASSWORD=your_password")
    print()
    print("Option 2 - Interactive prompt (default):")
    print("   Scripts will ask for your password securely")
    print()
    print("Option 3 - Edit config.py:")
    print("   Change LOGIN_EMAIL if using a different account")
    print()


def print_usage_examples():
    """Print usage examples"""
    print("📋 Usage Examples")
    print("-" * 17)
    print()
    print("1. Test authentication first:")
    print("   python test_auth.py")
    print()
    print("2. Quick test with minimal data:")
    print("   python create_all_mock_data.py --quick")
    print()
    print("3. Full dataset generation (50 vehicles, 50 drivers, 10 managers):")
    print("   python create_all_mock_data.py")
    print()
    print("4. Custom data volumes:")
    print("   python create_all_mock_data.py --vehicles 25 --drivers 25")
    print()
    print("5. Individual scripts:")
    print("   python create_vehicles.py --count 10")
    print("   python create_users.py --drivers 5 --managers 2")
    print("   python create_maintenance_data.py --records 20")
    print()


async def run_auth_test():
    """Run authentication test"""
    print("🧪 Running Authentication Test...")
    print("-" * 33)
    
    try:
        # Import and run the auth test
        from test_auth import test_authentication
        success = await test_authentication()
        return success
    except Exception as e:
        logger.error(f"Error running authentication test: {e}")
        return False


async def run_quick_demo():
    """Run a quick demo with minimal data"""
    print("\n🎬 Running Quick Demo...")
    print("-" * 23)
    print("Creating minimal dataset: 3 vehicles, 2 users, 5 maintenance items")
    print("Note: All users will have password 'Password1!' for testing")
    print()
    
    try:
        # Import and run quick test
        from create_all_mock_data import create_all_mock_data
        results = await create_all_mock_data(
            vehicles_count=3,
            drivers_count=2,
            managers_count=1,
            maintenance_records_count=5,
            licenses_count=4,
            schedules_count=3
        )
        return results is not None
    except Exception as e:
        logger.error(f"Error running quick demo: {e}")
        return False


async def main():
    """Main interactive demo"""
    print_banner()
    
    # Check if user wants instructions
    response = input("Do you want to see authentication setup instructions? (y/n): ").lower()
    if response in ['y', 'yes']:
        print()
        print_auth_instructions()
        print()
    
    # Check if user wants usage examples
    response = input("Do you want to see usage examples? (y/n): ").lower()
    if response in ['y', 'yes']:
        print()
        print_usage_examples()
        print()
    
    # Ask if user wants to test authentication
    response = input("Do you want to test authentication now? (y/n): ").lower()
    if response in ['y', 'yes']:
        print()
        auth_success = await run_auth_test()
        
        if auth_success:
            print()
            response = input("Authentication successful! Run quick demo? (y/n): ").lower()
            if response in ['y', 'yes']:
                demo_success = await run_quick_demo()
                
                if demo_success:
                    print()
                    print("🎉 Quick demo completed successfully!")
                    print("✅ You're ready to run the full mock data generation scripts!")
                else:
                    print()
                    print("❌ Demo failed. Please check the logs and try again.")
            else:
                print()
                print("✅ Authentication is working. You can now run the data generation scripts manually.")
        else:
            print()
            print("❌ Authentication failed. Please check your credentials and try again.")
            print("💡 Make sure SAMFMS services are running and your password is correct.")
    else:
        print()
        print("ℹ️  You can test authentication later with: python test_auth.py")
    
    print()
    print("📚 For more information, see README.md")
    print("🎯 Happy mock data generation!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
