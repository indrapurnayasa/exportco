from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import user, auth, export_data, komoditi, export
from app.api.v1.prompt_library import router as prompt_library_router
from app.db.database import create_tables
from app.utils.logger import log_server_startup, log_server_shutdown, log_database_connection, log_configuration_validation
from app.middleware.logging_middleware import LoggingMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

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
        log_configuration_validation(True)
    except ValueError as e:
        log_configuration_validation(False, [str(e)])
        raise
    
    # Create database tables
    try:
        create_tables()
        log_database_connection(True)
    except Exception as e:
        log_database_connection(False, str(e))
        raise

@app.get("/")
async def root():
    return {"message": "Welcome to Hackathon Service API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 