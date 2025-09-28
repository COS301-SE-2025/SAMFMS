#!/usr/bin/env python3
"""
Test script to debug the remove-user 422 error
"""
import requests
import json

def test_remove_user():
    # Test the remove-user endpoint directly
    url = "http://localhost:21004/auth/remove-user"
    
    # Get a valid token first by logging in
    login_url = "http://localhost:21004/auth/login"
    login_data = {
        "email": "admin@samfms.net",
        "password": "admin"
    }
    
    print("Step 1: Logging in to get token...")
    try:
        login_response = requests.post(login_url, json=login_data)
        print(f"Login response status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get('token')
            print(f"Token obtained: {token[:50]}..." if token else "No token in response")
            
            if token:
                print("\nStep 2: Testing remove-user endpoint...")
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                # Test with a sample email (not actually removing admin)
                # Let's try with a test email that shouldn't exist
                remove_data = {"email": "test@example.com"}
                
                print(f"Request data: {json.dumps(remove_data, indent=2)}")
                print(f"Request headers: Authorization: Bearer {token[:20]}...")
                
                remove_response = requests.post(url, json=remove_data, headers=headers)
                print(f"Remove-user response status: {remove_response.status_code}")
                
                if remove_response.status_code != 200:
                    try:
                        error_data = remove_response.json()
                        print(f"Error response: {json.dumps(error_data, indent=2)}")
                    except:
                        print(f"Raw error response: {remove_response.text}")
                else:
                    result = remove_response.json()
                    print(f"Success response: {json.dumps(result, indent=2)}")
                    
        else:
            print(f"Login failed: {login_response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_remove_user()