#!/usr/bin/env python3
"""
Script to test the last_access field update on successful login
"""

import requests
import json
from datetime import datetime

# API base URL - adjust this to match your server
BASE_URL = "http://localhost:8000/api/v1"

def test_login_and_last_access():
    """Test user login and verify last_access is updated"""
    print("🔐 Testing Login with Last Access Update...")
    
    # Test login data
    login_data = {
        "identifier": "+6281111111111",  # Use existing test user
        "password": "SecurePass123"
    }
    
    try:
        # First, get current user info to see last_access before login
        print("📊 Getting user info before login...")
        response = requests.get(f"{BASE_URL}/users/1")  # Assuming user ID 1
        if response.status_code == 200:
            user_before = response.json()
            print(f"   Last access before login: {user_before.get('last_access')}")
        
        # Perform login
        print("\n🔑 Performing login...")
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login successful!")
            print(f"   Token: {data['access_token'][:50]}...")
            
            # Get user info after login to see updated last_access
            print("\n📊 Getting user info after login...")
            headers = {"Authorization": f"Bearer {data['access_token']}"}
            response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            
            if response.status_code == 200:
                user_after = response.json()
                last_access = user_after.get('last_access')
                print(f"   ✅ Last access updated: {last_access}")
                
                if last_access:
                    print(f"   📅 Login timestamp: {last_access}")
                    return True
                else:
                    print(f"   ❌ Last access not updated")
                    return False
            else:
                print(f"   ❌ Failed to get user info: {response.text}")
                return False
        else:
            print(f"   ❌ Login failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")
        return False

def test_multiple_logins():
    """Test multiple logins to see last_access updates"""
    print("\n🔄 Testing Multiple Logins...")
    
    login_data = {
        "identifier": "+6281111111111",
        "password": "SecurePass123"
    }
    
    for i in range(3):
        print(f"\n   Login attempt {i+1}:")
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                headers = {"Authorization": f"Bearer {data['access_token']}"}
                user_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
                
                if user_response.status_code == 200:
                    user = user_response.json()
                    last_access = user.get('last_access')
                    print(f"      ✅ Last access: {last_access}")
                else:
                    print(f"      ❌ Failed to get user info")
            else:
                print(f"      ❌ Login failed")
                
        except requests.exceptions.RequestException as e:
            print(f"      ❌ Request error: {e}")

def main():
    """Run the last access update tests"""
    print("🚀 Starting Last Access Update Tests\n")
    
    # Test single login
    success = test_login_and_last_access()
    
    # Test multiple logins
    test_multiple_logins()
    
    if success:
        print("\n✅ Last access update tests completed successfully!")
    else:
        print("\n❌ Last access update tests failed!")

if __name__ == "__main__":
    main()