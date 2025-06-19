#!/usr/bin/env python
"""
User Management Integration Test Script
This script tests the integration between the frontend and backend user management functionality.

Usage:
    python test_user_management.py
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration - Update these URLs as needed
CORE_URL = "http://localhost:8000" 
SECURITY_URL = "http://localhost:8005"
ADMIN_EMAIL = "admin@samfms.com"
ADMIN_PASSWORD = "admin"

# Test user to be created
TEST_USER = {
    "full_name": f"Test User {datetime.now().strftime('%Y%m%d%H%M%S')}",
    "email": f"test{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
    "role": "driver",
    "phoneNo": "1234567890"
}

def log(message):
    """Print log message with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def test_auth_endpoints():
    """Test the authentication endpoints"""
    log("Testing authentication endpoints...")
    
    # Test login
    try:
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(f"{CORE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            log("✅ Login successful")
            return token_data["access_token"]
        else:
            log(f"❌ Login failed: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        log(f"❌ Error during login: {str(e)}")
        return None

def test_user_management(token):
    """Test user management functionality"""
    if not token:
        log("No authentication token available. Skipping user management tests.")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    success = True
    
    # Step 1: List existing users
    try:
        response = requests.get(f"{CORE_URL}/auth/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            log(f"✅ Successfully listed users. Found {len(users)} users.")
        else:
            log(f"❌ Failed to list users: {response.status_code}, {response.text}")
            success = False
    except Exception as e:
        log(f"❌ Error listing users: {str(e)}")
        success = False
    
    # Step 2: Create a new user
    created_user_id = None
    try:
        response = requests.post(f"{CORE_URL}/auth/invite-user", 
                                headers=headers, 
                                json=TEST_USER)
        
        if response.status_code == 200:
            result = response.json()
            created_user_id = result.get("user_id")
            log(f"✅ Successfully created user: {TEST_USER['email']}")
        else:
            log(f"❌ Failed to create user: {response.status_code}, {response.text}")
            success = False
    except Exception as e:
        log(f"❌ Error creating user: {str(e)}")
        success = False
    
    # Step 3: Verify user was created
    if created_user_id:
        try:
            response = requests.get(f"{CORE_URL}/auth/users", headers=headers)
            if response.status_code == 200:
                users = response.json()
                new_user = next((u for u in users if u.get("id") == created_user_id), None)
                
                if new_user:
                    log(f"✅ Verified user was created with ID: {created_user_id}")
                else:
                    log(f"❌ Could not find newly created user in user list")
                    success = False
            else:
                log(f"❌ Failed to verify user creation: {response.status_code}, {response.text}")
                success = False
        except Exception as e:
            log(f"❌ Error verifying user creation: {str(e)}")
            success = False
    
    # Step 4: Update user permissions
    if created_user_id:
        try:
            update_data = {
                "user_id": created_user_id,
                "role": "fleet_manager"
            }
            
            response = requests.post(f"{CORE_URL}/auth/update-permissions", 
                                    headers=headers, 
                                    json=update_data)
            
            if response.status_code == 200:
                log(f"✅ Successfully updated user role to fleet_manager")
            else:
                log(f"❌ Failed to update user role: {response.status_code}, {response.text}")
                success = False
        except Exception as e:
            log(f"❌ Error updating user permissions: {str(e)}")
            success = False
        
        # Verify role was updated
        try:
            time.sleep(1)  # Brief delay to ensure update is processed
            response = requests.get(f"{CORE_URL}/auth/users", headers=headers)
            if response.status_code == 200:
                users = response.json()
                updated_user = next((u for u in users if u.get("id") == created_user_id), None)
                
                if updated_user and updated_user.get("role") == "fleet_manager":
                    log(f"✅ Verified user role was updated to fleet_manager")
                else:
                    log(f"❌ User role was not updated properly")
                    success = False
            else:
                log(f"❌ Failed to verify user update: {response.status_code}, {response.text}")
                success = False
        except Exception as e:
            log(f"❌ Error verifying user update: {str(e)}")
            success = False
    
    return success

def main():
    """Run all tests"""
    log("Beginning user management integration tests")
    
    token = test_auth_endpoints()
    success = test_user_management(token)
    
    if success:
        log("✅ All user management tests passed")
        return 0
    else:
        log("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
