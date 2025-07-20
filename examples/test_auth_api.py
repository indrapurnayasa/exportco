#!/usr/bin/env python3
"""
Script to test the authentication API endpoints with multiple login methods
"""

import requests
import json

# API base URL - adjust this to match your server
BASE_URL = "http://localhost:8000/api/v1"

def test_register():
    """Test user registration"""
    print("🔐 Testing User Registration...")
    
    register_data = {
        "phone_number": "+6289876543210",
        "name": "API Test User",
        "region": "Bandung",
        "password": "SecurePass123",
        "email": "apitest@example.com",
        "username": "apitestuser"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Registration successful!")
            print(f"   Token: {data['access_token'][:50]}...")
            return data['access_token']
        else:
            print(f"   ❌ Registration failed: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")
        return None

def test_login_with_phone():
    """Test user login with phone number"""
    print("\n🔐 Testing User Login with Phone Number...")
    
    login_data = {
        "identifier": "+6281111111111",  # Use the new test user we created
        "password": "SecurePass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login with phone number successful!")
            print(f"   Token: {data['access_token'][:50]}...")
            return data['access_token']
        else:
            print(f"   ❌ Login with phone number failed: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")
        return None

def test_login_with_email():
    """Test user login with email"""
    print("\n🔐 Testing User Login with Email...")
    
    login_data = {
        "identifier": "multilogin@example.com",  # Use the new test user's email
        "password": "SecurePass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login with email successful!")
            print(f"   Token: {data['access_token'][:50]}...")
            return data['access_token']
        else:
            print(f"   ❌ Login with email failed: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")
        return None

def test_login_with_username():
    """Test user login with username"""
    print("\n🔐 Testing User Login with Username...")
    
    login_data = {
        "identifier": "multiuser",  # Use the new test user's username
        "password": "SecurePass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login with username successful!")
            print(f"   Token: {data['access_token'][:50]}...")
            return data['access_token']
        else:
            print(f"   ❌ Login with username failed: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")
        return None

def test_me_endpoint(token):
    """Test getting current user info"""
    print("\n👤 Testing /me endpoint...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ User info retrieved successfully!")
            print(f"   ID: {data['id']}")
            print(f"   Name: {data['name']}")
            print(f"   Phone: {data['phone_number']}")
            print(f"   Region: {data['region']}")
            print(f"   Email: {data['email']}")
            print(f"   Username: {data['username']}")
            print(f"   Active: {data['is_active']}")
        else:
            print(f"   ❌ Failed to get user info: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")

def test_check_availability():
    """Test availability checking endpoint"""
    print("\n🔍 Testing Availability Check...")
    
    try:
        # Check existing phone number
        response = requests.get(f"{BASE_URL}/auth/check-availability?phone_number=+6281111111111")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Availability check successful!")
            print(f"   Phone number availability: {data['phone_number']}")
        else:
            print(f"   ❌ Availability check failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")

def test_registration_validation():
    """Test registration validation with invalid data"""
    print("\n⚠️ Testing Registration Validation...")
    
    # Test with existing phone number
    register_data = {
        "phone_number": "+6281111111111",  # Already exists
        "name": "Duplicate User",
        "password": "WeakPass"  # Weak password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 400:
            data = response.json()
            print(f"   ✅ Validation working correctly!")
            if isinstance(data, dict) and 'errors' in data:
                print(f"   Validation errors: {data['errors']}")
            else:
                print(f"   Error: {data}")
        else:
            print(f"   ❌ Expected validation error but got: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")

def test_logout(token):
    """Test logout endpoint"""
    print("\n🚪 Testing Logout...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Logout successful!")
        else:
            print(f"   ❌ Logout failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")

def main():
    """Run all authentication tests"""
    print("🚀 Starting Enhanced Authentication API Tests\n")
    
    # Test registration
    register_token = test_register()
    
    # Test login with different identifiers
    phone_token = test_login_with_phone()
    email_token = test_login_with_email()
    username_token = test_login_with_username()
    
    # Test /me endpoint with any valid token
    if phone_token:
        test_me_endpoint(phone_token)
    
    # Test availability checking
    test_check_availability()
    
    # Test registration validation
    test_registration_validation()
    
    # Test logout
    if phone_token:
        test_logout(phone_token)
    
    print("\n✨ Enhanced Authentication API tests completed!")

if __name__ == "__main__":
    main() 