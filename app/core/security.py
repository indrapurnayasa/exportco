from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# In-memory blacklist for demonstration (use Redis or DB in production)
TOKEN_BLACKLIST = set()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict):
    """Create a JWT access token with NO expiration (unlimited session)"""
    to_encode = data.copy()
    # No 'exp' claim for unlimited session
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verify and decode a JWT token, and check blacklist"""
    if token in TOKEN_BLACKLIST:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            return None
        return phone_number
    except JWTError:
        return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from token, reject if blacklisted"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token in TOKEN_BLACKLIST:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been logged out. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    phone_number = verify_token(token)
    if phone_number is None:
        raise credentials_exception
    
    # Get user from database
    from app.services.user_service import UserService
    user_service = UserService(db)
    user = user_service.get_user_by_phone(phone_number)
    if user is None:
        raise credentials_exception
    
    return user

def blacklist_token(token: str):
    """Add a token to the blacklist (logout)"""
    TOKEN_BLACKLIST.add(token) 