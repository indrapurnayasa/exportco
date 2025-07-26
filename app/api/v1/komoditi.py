from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from app.db.database import get_db
from app.services.komoditi_service import KomoditiService
from app.schemas.komoditi import (
    KomoditiCreate, 
    KomoditiUpdate, 
    KomoditiResponse, 
    KomoditiFilter
)
import redis

router = APIRouter(prefix="/komoditi", tags=["komoditi"])

# Initialize Redis client (global, outside endpoint)
redis_client = redis.Redis.from_url("redis://default:7HB9zBV8ZcStEv3S3uXIAzjncTlcxmtR@redis-14884.c292.ap-southeast-1-1.ec2.redns.redis-cloud.com:14884")

@router.get("/", response_model=List[KomoditiResponse])
async def get_komoditi(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all commodities with pagination"""
    komoditi_service = KomoditiService(db)
    result = komoditi_service.get_all(skip=skip, limit=limit)
    return result

@router.get("/{komoditi_id}", response_model=KomoditiResponse)
async def get_komoditi_by_id(
    komoditi_id: str,
    db: Session = Depends(get_db)
):
    """Get specific commodity by ID"""
    komoditi_service = KomoditiService(db)
    komoditi = komoditi_service.get_by_id(komoditi_id)
    if not komoditi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commodity not found"
        )
    return komoditi

@router.get("/kode/{kode_komoditi}", response_model=KomoditiResponse)
async def get_komoditi_by_kode(
    kode_komoditi: str,
    db: Session = Depends(get_db)
):
    """Get commodity by code"""
    cache_key = f"komoditi:kode:{kode_komoditi}"
    cached = redis_client.get(cache_key)
    if cached:
        import json
        return json.loads(cached)
    komoditi_service = KomoditiService(db)
    komoditi = komoditi_service.get_by_kode(kode_komoditi)
    if not komoditi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commodity not found"
        )
    import json
    redis_client.set(cache_key, json.dumps(komoditi, default=str), ex=1800)
    return komoditi

@router.post("/", response_model=KomoditiResponse, status_code=status.HTTP_201_CREATED)
async def create_komoditi(
    komoditi: KomoditiCreate,
    db: Session = Depends(get_db)
):
    """Create new commodity"""
    komoditi_service = KomoditiService(db)
    return komoditi_service.create(komoditi)

@router.put("/{komoditi_id}", response_model=KomoditiResponse)
async def update_komoditi(
    komoditi_id: str,
    komoditi: KomoditiUpdate,
    db: Session = Depends(get_db)
):
    """Update existing commodity"""
    komoditi_service = KomoditiService(db)
    updated_komoditi = komoditi_service.update(komoditi_id, komoditi)
    if not updated_komoditi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commodity not found"
        )
    return updated_komoditi

@router.delete("/{komoditi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_komoditi(
    komoditi_id: str,
    db: Session = Depends(get_db)
):
    """Delete commodity"""
    komoditi_service = KomoditiService(db)
    success = komoditi_service.delete(komoditi_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commodity not found"
        )

# Filtering endpoints
@router.get("/filter/", response_model=List[KomoditiResponse])
async def filter_komoditi(
    kode_komoditi: Optional[str] = Query(None, description="Commodity code"),
    nama_komoditi: Optional[str] = Query(None, description="Commodity name"),
    satuan_komoditi: Optional[str] = Query(None, description="Commodity unit"),
    min_harga: Optional[Decimal] = Query(None, description="Minimum price"),
    max_harga: Optional[Decimal] = Query(None, description="Maximum price"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Filter commodities by various criteria"""
    filters = KomoditiFilter(
        kode_komoditi=kode_komoditi,
        nama_komoditi=nama_komoditi,
        satuan_komoditi=satuan_komoditi,
        min_harga=min_harga,
        max_harga=max_harga
    )
    komoditi_service = KomoditiService(db)
    result = komoditi_service.filter_data(filters, skip=skip, limit=limit)
    return result

# Search endpoints
@router.get("/search/{search_term}", response_model=List[KomoditiResponse])
async def search_komoditi(
    search_term: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Search commodities by name or code (partial match)"""
    cache_key = f"komoditi:search:{search_term}:{skip}:{limit}"
    cached = redis_client.get(cache_key)
    if cached:
        import json
        return json.loads(cached)
    komoditi_service = KomoditiService(db)
    result = komoditi_service.search_komoditi(search_term, skip=skip, limit=limit)
    import json
    redis_client.set(cache_key, json.dumps(result, default=str), ex=1800)
    return result

@router.get("/by-nama/{nama_komoditi}", response_model=List[KomoditiResponse])
async def get_by_nama(
    nama_komoditi: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get commodities by name (partial match)"""
    komoditi_service = KomoditiService(db)
    return komoditi_service.get_by_nama(nama_komoditi, skip=skip, limit=limit)

@router.get("/by-satuan/{satuan_komoditi}", response_model=List[KomoditiResponse])
async def get_by_satuan(
    satuan_komoditi: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get commodities by unit"""
    komoditi_service = KomoditiService(db)
    return komoditi_service.get_by_satuan(satuan_komoditi, skip=skip, limit=limit)

@router.get("/by-harga-range/", response_model=List[KomoditiResponse])
async def get_by_harga_range(
    min_harga: Decimal = Query(..., description="Minimum price"),
    max_harga: Decimal = Query(..., description="Maximum price"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get commodities within price range"""
    komoditi_service = KomoditiService(db)
    return komoditi_service.get_harga_range(min_harga, max_harga, skip=skip, limit=limit)

# Statistics endpoint
@router.get("/statistics/")
async def get_statistics(db: Session = Depends(get_db)):
    """Get basic statistics about commodities"""
    cache_key = "komoditi:statistics"
    cached = redis_client.get(cache_key)
    if cached:
        import json
        return json.loads(cached)
    komoditi_service = KomoditiService(db)
    result = komoditi_service.get_statistics()
    import json
    redis_client.set(cache_key, json.dumps(result, default=str), ex=1800)
    return result 