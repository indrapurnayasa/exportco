from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.auth import UserRegister
from app.core.security import get_password_hash, verify_password
import re

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get a specific user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        if not email:
            return None
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        if not username:
            return None
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """Get a user by phone number"""
        if not phone_number:
            return None
        return self.db.query(User).filter(User.phone_number == phone_number).first()
    
    def get_user_by_identifier(self, identifier: str) -> Optional[User]:
        """Get a user by phone number, email, or username"""
        if not identifier:
            return None
        
        # Try to find by phone number first
        user = self.get_user_by_phone(identifier)
        if user:
            return user
        
        # Try to find by email
        user = self.get_user_by_email(identifier)
        if user:
            return user
        
        # Try to find by username
        user = self.get_user_by_username(identifier)
        if user:
            return user
        
        return None
    
    def validate_registration_data(self, user_data: UserRegister) -> List[str]:
        """Validate registration data and return list of errors"""
        errors = []
        
        # Check if phone number already exists
        if self.get_user_by_phone(user_data.phone_number):
            errors.append("Phone number already registered")
        
        # Check if email already exists (if provided)
        if user_data.email and self.get_user_by_email(user_data.email):
            errors.append("Email already registered")
        
        # Check if username already exists (if provided)
        if user_data.username and self.get_user_by_username(user_data.username):
            errors.append("Username already registered")
        
        # Validate phone number format (basic validation)
        if not re.match(r'^\+?[1-9]\d{1,13}$', user_data.phone_number):
            errors.append("Invalid phone number format or length (max 14 digits)")
        if len(user_data.phone_number) > 14:
            errors.append("Phone number must be at most 14 characters")
        
        # Validate email format (if provided)
        if user_data.email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', user_data.email):
            errors.append("Invalid email format")
        
        # Validate username format (if provided)
        if user_data.username:
            if len(user_data.username) < 3:
                errors.append("Username must be at least 3 characters long")
            if not re.match(r'^[a-zA-Z0-9_]+$', user_data.username):
                errors.append("Username can only contain letters, numbers, and underscores")
        
        # Validate password strength
        if len(user_data.password) < 8:
            errors.append("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', user_data.password):
            errors.append("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', user_data.password):
            errors.append("Password must contain at least one lowercase letter")
        if not re.search(r'\d', user_data.password):
            errors.append("Password must contain at least one number")
        
        return errors
    
    def create_user(self, user_data: UserRegister) -> User:
        """Create a new user with comprehensive validation"""
        # Validate registration data
        validation_errors = self.validate_registration_data(user_data)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))
        
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            phone_number=user_data.phone_number,
            name=user_data.name,
            region=user_data.region,
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            is_active=True
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update_user(self, user_id: int, user: UserUpdate) -> Optional[User]:
        """Update an existing user"""
        db_user = self.get_user(user_id)
        if not db_user:
            return None
        
        update_data = user.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        db_user = self.get_user(user_id)
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True
    
    def authenticate_user(self, identifier: str, password: str) -> Optional[User]:
        """Authenticate a user by phone number, email, or username and password"""
        user = self.get_user_by_identifier(identifier)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user 