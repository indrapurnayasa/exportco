from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import user, auth, export_data, komoditi, export
from app.api.v1.prompt_library import router as prompt_library_router
from app.db.database import create_tables

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(user.router, prefix=settings.API_V1_STR)
app.include_router(export_data.router, prefix=settings.API_V1_STR)
app.include_router(komoditi.router, prefix=settings.API_V1_STR)
app.include_router(export.router, prefix=settings.API_V1_STR)
app.include_router(prompt_library_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Initialize configuration and database tables on startup"""
    # Validate configuration
    try:
        settings.validate()
        print("✅ Configuration validated successfully")
    except ValueError as e:
        print(f"❌ Configuration validation failed: {e}")
        raise
    
    # Create database tables
    create_tables()
    print("✅ Database tables initialized")

@app.get("/")
async def root():
    return {"message": "Welcome to Hackathon Service API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 