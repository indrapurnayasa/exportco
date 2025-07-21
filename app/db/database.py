from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Create async database engine - SERVERLESS OPTIMIZED
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    poolclass=NullPool,        # ✅ Disable connection pooling for serverless
    pool_pre_ping=True,        # ✅ Test connection before use
    pool_recycle=300,          # ✅ Keep existing recycle time
    echo=False,
    connect_args={
        "server_settings": {
            "application_name": "fastapi_vercel_app",
        }
    }
)

# Create async SessionLocal class
AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Create Base class
Base = declarative_base()

# Dependency to get async database session - IMPROVED ERROR HANDLING
async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()  # ✅ Rollback on error
            raise e
        finally:
            await session.close()

# Keep the sync version for backward compatibility - ALSO OPTIMIZED
from sqlalchemy import create_engine

# Create sync database engine - SERVERLESS OPTIMIZED
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,        # ✅ Disable pooling for sync too
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "application_name": "fastapi_vercel_sync"
    }
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get database session - IMPROVED ERROR HANDLING
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()  # ✅ Rollback on error
        raise e
    finally:
        db.close()

# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)
