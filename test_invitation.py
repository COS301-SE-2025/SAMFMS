#!/usr/bin/env python3
"""
Test script for the user invitation flow
This script tests the OTP-based user invitation system

Prerequisites:
- Core and Security services running
- Admin user created and logged in
- Email configuration set up in environment
"""

import requests
import json
import os
from datetime import datetime

# Configuration
CORE_URL = os.getenv("CORE_URL", "http://localhost:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
TEST_INVITE_EMAIL = os.getenv("TEST_INVITE_EMAIL", "test@example.com")

def login_as_admin():
    """Login as admin and return auth token"""
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    response = requests.post(f"{CORE_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Admin login successful")
        return data["access_token"]
    else:
        print(f"❌ Admin login failed: {response.status_code}")
        print(response.text)
        return None

def send_invitation(token, invite_data):
    """Send invitation using admin token"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{CORE_URL}/auth/invite-user", 
                           json=invite_data, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Invitation sent successfully to {invite_data['email']}")
        print(f"   Message: {data.get('message')}")
        print(f"   Expires: {data.get('expires_at')}")
        return data
    else:
        print(f"❌ Failed to send invitation: {response.status_code}")
        print(response.text)
        return None

def get_pending_invitations(token):
    """Get list of pending invitations"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{CORE_URL}/auth/invitations", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        invitations = data.get('invitations', [])
        print(f"✅ Retrieved {len(invitations)} pending invitations")
        for inv in invitations:
            print(f"   - {inv['email']} ({inv['role']}) - {inv['full_name']}")
        return invitations
    else:
        print(f"❌ Failed to get invitations: {response.status_code}")
        print(response.text)
        return []

def test_otp_verification(email, otp):
    """Test OTP verification (public endpoint)"""
    verify_data = {
        "email": email,
        "otp": otp
    }
    response = requests.post(f"{CORE_URL}/auth/verify-otp", json=verify_data)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ OTP verification successful for {email}")
        print(f"   Welcome: {data.get('full_name')} ({data.get('role')})")
        return data
    else:
        print(f"❌ OTP verification failed: {response.status_code}")
        print(response.text)
        return None

def test_complete_registration(email, otp, username, password):
    """Test completing registration"""
    registration_data = {
        "email": email,
        "otp": otp,
        "username": username,
        "password": password
    }
    response = requests.post(f"{CORE_URL}/auth/complete-registration", 
                           json=registration_data)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Registration completed successfully!")
        print(f"   User ID: {data.get('user_id')}")
        print(f"   Role: {data.get('role')}")
        return data
    else:
        print(f"❌ Registration completion failed: {response.status_code}")
        print(response.text)
        return None

def main():
    print("🔐 Testing User Invitation Flow")
    print("=" * 50)
    
    # Step 1: Login as admin
    token = login_as_admin()
    if not token:
        print("❌ Cannot proceed without admin token")
        return
    
    # Step 2: Send invitation
    invite_data = {
        "full_name": "Test User",
        "email": TEST_INVITE_EMAIL,
        "role": "driver",
        "phoneNo": "+1234567890"
    }
    
    invitation_result = send_invitation(token, invite_data)
    if not invitation_result:
        print("❌ Cannot proceed without successful invitation")
        return
    
    # Step 3: Get pending invitations
    invitations = get_pending_invitations(token)
    
    # Step 4: Manual OTP verification test
    print("\n📧 Check your email for the OTP")
    print("💡 To test OTP verification, you would need the actual OTP from email")
    print("💡 Example test commands:")
    print(f"   python test_invitation.py verify {TEST_INVITE_EMAIL} 123456")
    print(f"   python test_invitation.py complete {TEST_INVITE_EMAIL} 123456 testuser password123")
    
    print("\n✅ Invitation flow test completed!")
    print("📝 Next steps:")
    print("   1. Check email for OTP")
    print("   2. Use /activate page in frontend to complete registration")
    print("   3. Or use the API endpoints directly for testing")

def test_verify_command(email, otp):
    """Test OTP verification command"""
    print(f"🔍 Testing OTP verification for {email}")
    result = test_otp_verification(email, otp)
    return result is not None

def test_complete_command(email, otp, username, password):
    """Test complete registration command"""
    print(f"🔄 Testing registration completion for {email}")
    result = test_complete_registration(email, otp, username, password)
    return result is not None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "verify" and len(sys.argv) >= 4:
            email = sys.argv[2]
            otp = sys.argv[3]
            test_verify_command(email, otp)
        elif command == "complete" and len(sys.argv) >= 6:
            email = sys.argv[2]
            otp = sys.argv[3]
            username = sys.argv[4]
            password = sys.argv[5]
            test_complete_command(email, otp, username, password)
        else:
            print("Usage:")
            print("  python test_invitation.py                    # Full test")
            print("  python test_invitation.py verify EMAIL OTP  # Test OTP verification")
            print("  python test_invitation.py complete EMAIL OTP USERNAME PASSWORD  # Test completion")
    else:
        main()
