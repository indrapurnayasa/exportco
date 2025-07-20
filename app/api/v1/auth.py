from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import create_access_token, get_current_user, blacklist_token
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login endpoint using phone number, email, or username and password.
    
    The identifier field can be:
    - Phone number (e.g., +6281234567890)
    - Email address (e.g., user@example.com)
    - Username (e.g., johndoe)
    """
    user_service = UserService(db)
    user = user_service.authenticate_user(user_data.identifier, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect identifier or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token = create_access_token(data={"sub": user.phone_number})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=Token)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register new user with comprehensive validation.
    
    Validates:
    - Phone number format and uniqueness
    - Email format and uniqueness (if provided)
    - Username format and uniqueness (if provided)
    - Password strength requirements
    """
    user_service = UserService(db)
    
    try:
        user = user_service.create_user(user_data)
        access_token = create_access_token(data={"sub": user.phone_number})
        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError as e:
        # Split multiple validation errors
        error_messages = str(e).split("; ")
        if len(error_messages) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Multiple validation errors",
                    "errors": error_messages
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.post("/logout")
async def logout(request: Request):
    """Logout endpoint (client should discard the token and server blacklists it)"""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return {"message": "No token provided, nothing to logout"}
    token = auth_header.split(" ", 1)[1]
    blacklist_token(token)
    return {"message": "Successfully logged out"}

@router.get("/check-availability")
async def check_availability(
    phone_number: str = None,
    email: str = None,
    username: str = None,
    db: Session = Depends(get_db)
):
    """
    Check availability of phone number, email, or username.
    Returns True if available, False if already taken.
    """
    user_service = UserService(db)
    
    result = {}
    
    if phone_number:
        user = user_service.get_user_by_phone(phone_number)
        result["phone_number"] = {
            "available": user is None,
            "message": "Available" if user is None else "Phone number already registered"
        }
    
    if email:
        user = user_service.get_user_by_email(email)
        result["email"] = {
            "available": user is None,
            "message": "Available" if user is None else "Email already registered"
        }
    
    if username:
        user = user_service.get_user_by_username(username)
        result["username"] = {
            "available": user is None,
            "message": "Available" if user is None else "Username already taken"
        }
    
    return result 