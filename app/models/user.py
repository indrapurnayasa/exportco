from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(14), unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    region = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)  # Optional for backward compatibility
    username = Column(String, unique=True, index=True, nullable=True)  # Optional for backward compatibility
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 