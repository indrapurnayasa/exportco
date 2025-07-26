from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from app.db.database import get_db
from app.services.export_data_service import ExportDataService
from app.schemas.export_data import (
    ExportDataCreate, 
    ExportDataUpdate, 
    ExportDataResponse, 
    ExportDataFilter
)
import redis

router = APIRouter(prefix="/export-data", tags=["export-data"])

# Initialize Redis client (global, outside endpoint)
redis_client = redis.Redis.from_url("redis://default:7HB9zBV8ZcStEv3S3uXIAzjncTlcxmtR@redis-14884.c292.ap-southeast-1-1.ec2.redns.redis-cloud.com:14884")

@router.get("/", response_model=List[ExportDataResponse])
async def get_export_data(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all export data with pagination"""
    export_service = ExportDataService(db)
    result = export_service.get_all(skip=skip, limit=limit)
    return result

@router.get("/{export_id}", response_model=ExportDataResponse)
async def get_export_data_by_id(
    export_id: str,
    db: Session = Depends(get_db)
):
    """Get specific export data by ID"""
    export_service = ExportDataService(db)
    export_data = export_service.get_by_id(export_id)
    if not export_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export data not found"
        )
    return export_data

@router.post("/", response_model=ExportDataResponse, status_code=status.HTTP_201_CREATED)
async def create_export_data(
    export_data: ExportDataCreate,
    db: Session = Depends(get_db)
):
    """Create new export data"""
    export_service = ExportDataService(db)
    return export_service.create(export_data)

@router.put("/{export_id}", response_model=ExportDataResponse)
async def update_export_data(
    export_id: str,
    export_data: ExportDataUpdate,
    db: Session = Depends(get_db)
):
    """Update existing export data"""
    export_service = ExportDataService(db)
    updated_data = export_service.update(export_id, export_data)
    if not updated_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export data not found"
        )
    return updated_data

@router.delete("/{export_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_export_data(
    export_id: str,
    db: Session = Depends(get_db)
):
    """Delete export data"""
    export_service = ExportDataService(db)
    success = export_service.delete(export_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export data not found"
        )

# Filtering endpoints
@router.get("/filter/", response_model=List[ExportDataResponse])
async def filter_export_data(
    provorig: Optional[str] = Query(None, description="Province of origin"),
    ctr: Optional[str] = Query(None, description="Country"),
    pod: Optional[str] = Query(None, description="Port of destination"),
    tahun: Optional[str] = Query(None, description="Year"),
    bulan: Optional[str] = Query(None, description="Month"),
    ctr_code: Optional[str] = Query(None, description="Country code"),
    comodity_code: Optional[str] = Query(None, description="Commodity code"),
    min_value: Optional[Decimal] = Query(None, description="Minimum value"),
    max_value: Optional[Decimal] = Query(None, description="Maximum value"),
    min_netweight: Optional[Decimal] = Query(None, description="Minimum netweight"),
    max_netweight: Optional[Decimal] = Query(None, description="Maximum netweight"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Filter export data by various criteria"""
    filters = ExportDataFilter(
        provorig=provorig,
        ctr=ctr,
        pod=pod,
        tahun=tahun,
        bulan=bulan,
        ctr_code=ctr_code,
        comodity_code=comodity_code,
        min_value=min_value,
        max_value=max_value,
        min_netweight=min_netweight,
        max_netweight=max_netweight
    )
    export_service = ExportDataService(db)
    result = export_service.filter_data(filters, skip=skip, limit=limit)
    return result

@router.get("/search/kodehs/{kodehs_search}", response_model=List[ExportDataResponse])
async def search_by_kodehs(
    kodehs_search: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Search export data by HS code (partial match)"""
    export_service = ExportDataService(db)
    return export_service.search_by_kodehs(kodehs_search, skip=skip, limit=limit)

# Statistics endpoint
@router.get("/statistics/")
async def get_statistics(db: Session = Depends(get_db)):
    """Get basic statistics about export data"""
    cache_key = "export_data:statistics"
    cached = redis_client.get(cache_key)
    if cached:
        import json
        return json.loads(cached)
    export_service = ExportDataService(db)
    result = export_service.get_statistics()
    import json
    redis_client.set(cache_key, json.dumps(result, default=str), ex=1800)
    return result 