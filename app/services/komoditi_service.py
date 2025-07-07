from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from app.models.komoditi import Komoditi
from app.schemas.komoditi import KomoditiCreate, KomoditiUpdate, KomoditiFilter

class KomoditiService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Komoditi]:
        """Get all commodities with pagination"""
        return self.db.query(Komoditi).offset(skip).limit(limit).all()
    
    def get_by_id(self, komoditi_id: str) -> Optional[Komoditi]:
        """Get commodity by ID"""
        return self.db.query(Komoditi).filter(Komoditi.id == komoditi_id).first()
    
    def get_by_kode(self, kode_komoditi: str) -> Optional[Komoditi]:
        """Get commodity by code"""
        return self.db.query(Komoditi).filter(Komoditi.kode_komoditi == kode_komoditi).first()
    
    def create(self, komoditi: KomoditiCreate) -> Komoditi:
        """Create new commodity"""
        db_komoditi = Komoditi(**komoditi.dict())
        self.db.add(db_komoditi)
        self.db.commit()
        self.db.refresh(db_komoditi)
        return db_komoditi
    
    def update(self, komoditi_id: str, komoditi: KomoditiUpdate) -> Optional[Komoditi]:
        """Update existing commodity"""
        db_komoditi = self.get_by_id(komoditi_id)
        if not db_komoditi:
            return None
        
        update_data = komoditi.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_komoditi, field, value)
        
        self.db.commit()
        self.db.refresh(db_komoditi)
        return db_komoditi
    
    def delete(self, komoditi_id: str) -> bool:
        """Delete commodity"""
        db_komoditi = self.get_by_id(komoditi_id)
        if not db_komoditi:
            return False
        
        self.db.delete(db_komoditi)
        self.db.commit()
        return True
    
    def filter_data(self, filters: KomoditiFilter, skip: int = 0, limit: int = 100) -> List[Komoditi]:
        """Filter commodities based on various criteria"""
        query = self.db.query(Komoditi)
        
        # Apply filters
        if filters.kode_komoditi:
            query = query.filter(Komoditi.kode_komoditi == filters.kode_komoditi)
        
        if filters.nama_komoditi:
            query = query.filter(Komoditi.nama_komoditi.ilike(f"%{filters.nama_komoditi}%"))
        
        if filters.satuan_komoditi:
            query = query.filter(Komoditi.satuan_komoditi == filters.satuan_komoditi)
        
        if filters.min_harga is not None:
            query = query.filter(Komoditi.harga_komoditi >= filters.min_harga)
        
        if filters.max_harga is not None:
            query = query.filter(Komoditi.harga_komoditi <= filters.max_harga)
        
        if filters.start_date:
            query = query.filter(Komoditi.created_at >= filters.start_date)
        
        if filters.end_date:
            query = query.filter(Komoditi.created_at <= filters.end_date)
        
        return query.offset(skip).limit(limit).all()
    
    def get_by_nama(self, nama_komoditi: str, skip: int = 0, limit: int = 100) -> List[Komoditi]:
        """Get commodities by name (partial match)"""
        return self.db.query(Komoditi).filter(
            Komoditi.nama_komoditi.ilike(f"%{nama_komoditi}%")
        ).offset(skip).limit(limit).all()
    
    def get_by_satuan(self, satuan_komoditi: str, skip: int = 0, limit: int = 100) -> List[Komoditi]:
        """Get commodities by unit"""
        return self.db.query(Komoditi).filter(
            Komoditi.satuan_komoditi == satuan_komoditi
        ).offset(skip).limit(limit).all()
    
    def get_harga_range(self, min_harga: Decimal, max_harga: Decimal, skip: int = 0, limit: int = 100) -> List[Komoditi]:
        """Get commodities within price range"""
        return self.db.query(Komoditi).filter(
            and_(Komoditi.harga_komoditi >= min_harga, Komoditi.harga_komoditi <= max_harga)
        ).offset(skip).limit(limit).all()
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime, skip: int = 0, limit: int = 100) -> List[Komoditi]:
        """Get commodities within date range"""
        return self.db.query(Komoditi).filter(
            and_(Komoditi.created_at >= start_date, Komoditi.created_at <= end_date)
        ).offset(skip).limit(limit).all()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about commodities"""
        total_records = self.db.query(Komoditi).count()
        total_harga = self.db.query(Komoditi.harga_komoditi).filter(Komoditi.harga_komoditi.isnot(None)).all()
        
        # Calculate totals
        sum_harga = sum([float(h[0]) for h in total_harga if h[0] is not None])
        avg_harga = sum_harga / len(total_harga) if total_harga else 0
        
        # Get unique counts
        unique_kode = self.db.query(Komoditi.kode_komoditi).distinct().count()
        unique_satuan = self.db.query(Komoditi.satuan_komoditi).distinct().count()
        
        # Get min and max prices
        min_harga = self.db.query(Komoditi.harga_komoditi).order_by(Komoditi.harga_komoditi.asc()).first()
        max_harga = self.db.query(Komoditi.harga_komoditi).order_by(Komoditi.harga_komoditi.desc()).first()
        
        return {
            "total_records": total_records,
            "total_harga": sum_harga,
            "average_harga": avg_harga,
            "min_harga": float(min_harga[0]) if min_harga and min_harga[0] else 0,
            "max_harga": float(max_harga[0]) if max_harga and max_harga[0] else 0,
            "unique_kode": unique_kode,
            "unique_satuan": unique_satuan
        }
    
    def search_komoditi(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Komoditi]:
        """Search commodities by name or code (partial match)"""
        return self.db.query(Komoditi).filter(
            or_(
                Komoditi.nama_komoditi.ilike(f"%{search_term}%"),
                Komoditi.kode_komoditi.ilike(f"%{search_term}%")
            )
        ).offset(skip).limit(limit).all()
    
    def get_komoditi_by_price_range(self, min_price: Decimal, max_price: Decimal, skip: int = 0, limit: int = 100) -> List[Komoditi]:
        """Get commodities within specific price range"""
        return self.db.query(Komoditi).filter(
            and_(Komoditi.harga_komoditi >= min_price, Komoditi.harga_komoditi <= max_price)
        ).order_by(Komoditi.harga_komoditi.asc()).offset(skip).limit(limit).all()
    
    def get_komoditi_by_unit(self, satuan: str, skip: int = 0, limit: int = 100) -> List[Komoditi]:
        """Get commodities by specific unit"""
        return self.db.query(Komoditi).filter(
            Komoditi.satuan_komoditi == satuan
        ).order_by(Komoditi.nama_komoditi.asc()).offset(skip).limit(limit).all() 