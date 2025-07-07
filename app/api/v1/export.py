from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.services.export_data_service import AsyncExportDataService
from app.schemas.export_data import SeasonalTrendResponse, CountryDemandResponse
from app.core.config import settings
import time
import asyncio

router = APIRouter(prefix="/export", tags=["export"])

# Simple rate limiting (in production, use Redis or similar)
_request_timestamps = {}

def _check_rate_limit(client_id: str = "default"):
    """Simple rate limiting implementation - configurable requests per second"""
    current_time = time.time()
    
    if client_id not in _request_timestamps:
        _request_timestamps[client_id] = []
    
    # Remove old timestamps outside the configured window
    _request_timestamps[client_id] = [
        ts for ts in _request_timestamps[client_id] 
        if current_time - ts < settings.RATE_LIMIT_WINDOW
    ]
    
    # Check if limit exceeded using configuration
    if len(_request_timestamps[client_id]) >= settings.RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {settings.RATE_LIMIT_REQUESTS} requests per {settings.RATE_LIMIT_WINDOW} second(s) allowed."
        )
    
    # Add current request timestamp
    _request_timestamps[client_id].append(current_time)

@router.get("/seasonal-trend", response_model=SeasonalTrendResponse)
async def get_seasonal_trend(db: AsyncSession = Depends(get_async_db)):
    """Get seasonal trend data for the latest quarter"""
    start_time = time.time()
    
    try:
        # Rate limiting using configuration
        _check_rate_limit()
        
        # Add timeout for the entire operation
        export_service = AsyncExportDataService(db)
        
        # Set timeout for the operation using configuration
        result = await asyncio.wait_for(
            export_service.get_seasonal_trend(),
            timeout=settings.QUERY_TIMEOUT
        )
        
        # Log performance metrics
        execution_time = time.time() - start_time
        print(f"Seasonal trend query executed in {execution_time:.2f} seconds")
        
        return result
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timeout. Please try again."
        )
    except Exception as e:
        # Log error for monitoring
        print(f"Error in seasonal trend endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error. Please try again later."
        )

@router.get("/country-demand", response_model=CountryDemandResponse)
async def get_country_demand(db: AsyncSession = Depends(get_async_db)):
    """
    Get all commodities for top 20 countries with growth calculations.
    Countries are ranked by total transaction value in the latest quarter.
    """
    start_time = time.time()
    
    try:
        # Rate limiting using configuration
        _check_rate_limit()
        
        # Add timeout for the entire operation
        export_service = AsyncExportDataService(db)
        
        # Set timeout for the operation using configuration
        result = await asyncio.wait_for(
            export_service.get_country_demand(),
            timeout=settings.QUERY_TIMEOUT
        )
        
        # Log performance metrics
        execution_time = time.time() - start_time
        print(f"Country demand query executed in {execution_time:.2f} seconds")
        
        if not result['data']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No data found or no data available"
            )
        
        return result
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timeout. Please try again."
        )
    except HTTPException:
        raise
    except Exception as e:
        # Log error for monitoring
        print(f"Error in country demand endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error. Please try again later."
        ) 