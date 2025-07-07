from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class KomoditiBase(BaseModel):
    kode_komoditi: str = Field(..., max_length=10, description="Commodity code")
    nama_komoditi: str = Field(..., description="Commodity name")
    harga_komoditi: Decimal = Field(..., description="Commodity price")
    satuan_komoditi: str = Field(..., max_length=20, description="Commodity unit")

class KomoditiCreate(KomoditiBase):
    pass

class KomoditiUpdate(BaseModel):
    kode_komoditi: Optional[str] = Field(None, max_length=10)
    nama_komoditi: Optional[str] = None
    harga_komoditi: Optional[Decimal] = None
    satuan_komoditi: Optional[str] = Field(None, max_length=20)

class KomoditiResponse(KomoditiBase):
    id: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v) if v else None
        }

# Query schemas for filtering
class KomoditiFilter(BaseModel):
    kode_komoditi: Optional[str] = None
    nama_komoditi: Optional[str] = None
    min_harga: Optional[Decimal] = None
    max_harga: Optional[Decimal] = None
    satuan_komoditi: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None 