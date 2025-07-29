from fastapi import APIRouter, Depends, HTTPException, status, Query
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

@router.get("/health-fast")
async def health_check_fast():
    """
    Fast health check endpoint for Vercel integration.
    Returns immediately without database queries.
    """
    return {
        "status": "healthy",
        "service": "export-api",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@router.get("/seasonal-trend", response_model=SeasonalTrendResponse)
async def get_seasonal_trend(
    endDate: str = None,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get seasonal trend data for a specific quarter.
    Results are sorted by growth percentage from highest to lowest.
    
    Args:
        endDate: End date in DD-MM-YYYY format (e.g., 31-03-2025 for Q1 2025)
                 If not provided, uses the latest available quarter
    """
    start_time = time.time()
    
    try:
        # Rate limiting using configuration
        _check_rate_limit()
        
        # Add timeout for the entire operation
        export_service = AsyncExportDataService(db)
        
        # Set timeout for the operation using configuration
        result = await asyncio.wait_for(
            export_service.get_seasonal_trend(endDate),
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
async def get_country_demand(
    endDate: str = None,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all commodities for top 20 countries with growth calculations and prices.
    Countries are sorted by growth percentage from highest to lowest.
    Products within each country are also sorted by growth percentage from highest to lowest.
    Growth is calculated month-over-month (comparing to the previous month).
    Each product includes price and growth information for that commodity in that country.
    Transaction values are converted from USD to IDR using the latest exchange rate.
    
    Args:
        endDate: End date in DD-MM-YYYY format (e.g., 31-03-2025 for Q1 2025)
                 If not provided, uses the latest available quarter
                 
    Returns:
        Returns empty data array if no data exists for the specified quarter
    """
    start_time = time.time()
    
    try:
        # Rate limiting using configuration
        _check_rate_limit()
        
        # Add timeout for the entire operation
        export_service = AsyncExportDataService(db)
        
        # Set timeout for the operation using configuration (increased for complex query)
        result = await asyncio.wait_for(
            export_service.get_country_demand(endDate),
            timeout=settings.QUERY_TIMEOUT * 2  # Double timeout for this complex operation
        )
        
        # Log performance metrics
        execution_time = time.time() - start_time
        print(f"Country demand query executed in {execution_time:.2f} seconds")
        
        # Return empty result instead of 404 - this is valid when no data exists for the date
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

@router.get("/top-commodity-by-country")
async def get_top_commodity_by_country(
    endDate: str = Query(None, description="End date in DD-MM-YYYY format (e.g., 31-12-2024)"),
    countryId: str = Query(None, description="Country ID to filter by (e.g., US, CN, ID)"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get the top commodity from every country with optional date and country filtering.
    Returns the commodity with the highest growth percentage for each country.
    Countries are sorted by their top commodity's growth percentage from highest to lowest.
    
    Args:
        endDate: End date in DD-MM-YYYY format (e.g., 31-12-2024)
                 If not provided, uses the latest available data
        countryId: Country ID to filter by (e.g., US, CN, ID)
                  If not provided, returns data for all countries
                  
    Returns:
        List of countries with their top commodity (by growth percentage) information
    """
    start_time = time.time()
    
    try:
        # Rate limiting using configuration
        _check_rate_limit()
        
        # Add timeout for the entire operation
        export_service = AsyncExportDataService(db)
        
        # Set timeout for the operation using configuration
        result = await asyncio.wait_for(
            export_service.get_top_commodity_by_country(endDate, countryId),
            timeout=settings.QUERY_TIMEOUT
        )
        
        # Log performance metrics
        execution_time = time.time() - start_time
        print(f"Top commodity by country query executed in {execution_time:.2f} seconds")
        
        return result
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Request timeout. Please try again."
        )
    except Exception as e:
        # Log error for monitoring
        print(f"Error in top commodity by country endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 