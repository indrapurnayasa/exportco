from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.services.user_service import UserService
from app.schemas.user import UserUpdate, UserResponse
from app.schemas.auth import UserRegister
import redis

router = APIRouter(prefix="/users", tags=["users"])

# Initialize Redis client (global, outside endpoint)
redis_client = redis.Redis.from_url("redis://default:7HB9zBV8ZcStEv3S3uXIAzjncTlcxmtR@redis-14884.c292.ap-southeast-1-1.ec2.redns.redis-cloud.com:14884")

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all users with pagination"""
    user_service = UserService(db)
    result = user_service.get_users(skip=skip, limit=limit)
    return result

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific user by ID"""
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    """Create a new user"""
    user_service = UserService(db)
    return user_service.create_user(user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing user"""
    user_service = UserService(db)
    updated_user = user_service.update_user(user_id, user)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Delete a user"""
    user_service = UserService(db)
    success = user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        ) 