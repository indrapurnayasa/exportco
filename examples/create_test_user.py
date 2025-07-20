#!/usr/bin/env python3
"""
Script to create a test user with authentication credentials
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.user_service import UserService
from app.schemas.auth import UserRegister

def create_test_user():
    """Create a test user for authentication"""
    db = SessionLocal()
    try:
        user_service = UserService(db)
        
        # Test user data with strong password
        test_user_data = UserRegister(
            phone_number="+6281111111111",
            name="Multi Login User",
            region="Surabaya",
            password="SecurePass123",  # Strong password meeting requirements
            email="multilogin@example.com",
            username="multiuser"
        )
        
        # Create the user
        user = user_service.create_user(test_user_data)
        print(f"✅ Test user created successfully!")
        print(f"   ID: {user.id}")
        print(f"   Phone: {user.phone_number}")
        print(f"   Name: {user.name}")
        print(f"   Region: {user.region}")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Active: {user.is_active}")
        print(f"   Created: {user.created_at}")
        
        # Test authentication with phone number
        authenticated_user = user_service.authenticate_user(
            test_user_data.phone_number, 
            test_user_data.password
        )
        
        if authenticated_user:
            print(f"✅ Authentication with phone number passed!")
        else:
            print(f"❌ Authentication with phone number failed!")
        
        # Test authentication with email
        authenticated_user = user_service.authenticate_user(
            test_user_data.email, 
            test_user_data.password
        )
        
        if authenticated_user:
            print(f"✅ Authentication with email passed!")
        else:
            print(f"❌ Authentication with email failed!")
        
        # Test authentication with username
        authenticated_user = user_service.authenticate_user(
            test_user_data.username, 
            test_user_data.password
        )
        
        if authenticated_user:
            print(f"✅ Authentication with username passed!")
        else:
            print(f"❌ Authentication with username failed!")
            
    except ValueError as e:
        print(f"❌ Error creating user: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user() 