import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Configuration class for the Hackathon Service API"""
    
    # Basic settings
    PROJECT_NAME: str = "Hackathon Service API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API for Hackathon Service"
    API_V1_STR: str = "/api/v1"
    
    # Database settings - use environment variables
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "hackathondb")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "maverick")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "Hackathon2025")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    # Construct DATABASE_URL from components
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # Production database settings
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate limiting settings
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "1"))  # 1 second window
    
    # Cache settings
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))
    
    # Query limits for production - OPTIMIZED FOR VERCEL
    MAX_QUERY_LIMIT: int = int(os.getenv("MAX_QUERY_LIMIT", "1000"))  # Reduced from 10000
    QUERY_TIMEOUT: int = int(os.getenv("QUERY_TIMEOUT", "8"))  # Reduced from 30 to 8 seconds for Vercel
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    def validate(self):
        """Validate critical settings"""
        # Removed database validation for development
        # Removed SECRET_KEY validation for development
        pass

# Create settings instance
settings = Settings() 