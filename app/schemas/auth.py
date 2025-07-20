from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    identifier: str  # Can be phone_number, email, or username
    password: str

class UserRegister(BaseModel):
    phone_number: str
    name: str
    region: Optional[str] = None
    password: str
    email: Optional[str] = None
    username: Optional[str] = None

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Phone number is required')
        v = v.strip()
        if len(v) > 14:
            raise ValueError('Phone number must be at most 14 characters')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v.strip() if v else None
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v.strip() if v else None

class UserResponse(BaseModel):
    id: int
    phone_number: str
    name: str
    region: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 