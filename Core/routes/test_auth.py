"""
Test script for authentication endpoints
Run this after starting the core service to test login, signup, and delete functionality
"""
import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000"

async def test_auth_endpoints():
    """Test all authentication endpoints"""
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Signup
        print("🧪 Testing Signup...")
        signup_data = {
            "full_name": "Test User",
            "email": "test@example.com", 
            "password": "testpassword123",
            "role": "user",
            "phoneNo": "123-456-7890"
        }
        
        async with session.post(f"{BASE_URL}/signup", json=signup_data) as response:
            if response.status == 200:
                signup_result = await response.json()
                print("✅ Signup successful!")
                print(f"   User ID: {signup_result['user']['id']}")
                print(f"   Token: {signup_result['access_token'][:20]}...")
                access_token = signup_result['access_token']
            else:
                error_detail = await response.text()
                print(f"❌ Signup failed: {response.status} - {error_detail}")
                return
        
        # Test 2: Login
        print("\n🧪 Testing Login...")
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        async with session.post(f"{BASE_URL}/login", json=login_data) as response:
            if response.status == 200:
                login_result = await response.json()
                print("✅ Login successful!")
                print(f"   Welcome back: {login_result['user']['full_name']}")
                access_token = login_result['access_token']  # Use new token
            else:
                error_detail = await response.text()
                print(f"❌ Login failed: {response.status} - {error_detail}")
                return
        
        # Test 3: Get current user info
        print("\n🧪 Testing Get Current User...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with session.get(f"{BASE_URL}/me", headers=headers) as response:
            if response.status == 200:
                user_info = await response.json()
                print("✅ Get current user successful!")
                print(f"   Name: {user_info['full_name']}")
                print(f"   Email: {user_info['email']}")
                print(f"   Role: {user_info['role']}")
            else:
                error_detail = await response.text()
                print(f"❌ Get current user failed: {response.status} - {error_detail}")
        
        # Test 4: Change password
        print("\n🧪 Testing Change Password...")
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword456"
        }
        
        async with session.put(f"{BASE_URL}/change-password", json=password_data, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                print("✅ Password change successful!")
                print(f"   Message: {result['message']}")
            else:
                error_detail = await response.text()
                print(f"❌ Password change failed: {response.status} - {error_detail}")
        
        # Test 5: Test login with new password
        print("\n🧪 Testing Login with New Password...")
        new_login_data = {
            "email": "test@example.com",
            "password": "newpassword456"
        }
        
        async with session.post(f"{BASE_URL}/login", json=new_login_data) as response:
            if response.status == 200:
                print("✅ Login with new password successful!")
                new_login_result = await response.json()
                access_token = new_login_result['access_token']  # Update token
                headers = {"Authorization": f"Bearer {access_token}"}
            else:
                error_detail = await response.text()
                print(f"❌ Login with new password failed: {response.status} - {error_detail}")
                return
        
        # Test 6: Delete account
        print("\n🧪 Testing Delete Account...")
        async with session.delete(f"{BASE_URL}/account", headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                print("✅ Account deletion successful!")
                print(f"   Message: {result['message']}")
            else:
                error_detail = await response.text()
                print(f"❌ Account deletion failed: {response.status} - {error_detail}")
        
        # Test 7: Try to access with deleted account
        print("\n🧪 Testing Access After Deletion...")
        async with session.get(f"{BASE_URL}/me", headers=headers) as response:
            if response.status == 401:
                print("✅ Access correctly denied after account deletion!")
            else:
                print(f"❌ Unexpected response after deletion: {response.status}")

if __name__ == "__main__":
    print("🚀 Starting authentication endpoint tests...")
    print("Make sure the core service is running on localhost:8000")
    print("=" * 60)
    
    try:
        asyncio.run(test_auth_endpoints())
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🏁 Tests completed!")
