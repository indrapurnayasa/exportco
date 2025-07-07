from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal

class ExportDataBase(BaseModel):
    provorig: Optional[str] = Field(None, max_length=10)
    value: Optional[Decimal] = None
    netweight: Optional[Decimal] = None
    kodehs: Optional[str] = None
    pod: Optional[str] = None
    ctr: Optional[str] = None
    tahun: Optional[str] = Field(None, max_length=6)
    bulan: Optional[str] = Field(None, max_length=20)
    ctr_code: Optional[str] = Field(None, max_length=2)
    comodity_code: Optional[str] = Field(None, max_length=10)

class ExportDataCreate(ExportDataBase):
    pass

class ExportDataUpdate(BaseModel):
    provorig: Optional[str] = Field(None, max_length=10)
    value: Optional[Decimal] = None
    netweight: Optional[Decimal] = None
    kodehs: Optional[str] = None
    pod: Optional[str] = None
    ctr: Optional[str] = None
    tahun: Optional[str] = Field(None, max_length=6)
    bulan: Optional[str] = Field(None, max_length=20)
    ctr_code: Optional[str] = Field(None, max_length=2)
    comodity_code: Optional[str] = Field(None, max_length=10)

class ExportDataResponse(ExportDataBase):
    id: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v) if v else None
        }

# Query schemas for filtering
class ExportDataFilter(BaseModel):
    provorig: Optional[str] = None
    ctr: Optional[str] = None
    pod: Optional[str] = None
    tahun: Optional[str] = None
    bulan: Optional[str] = None
    ctr_code: Optional[str] = None
    comodity_code: Optional[str] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    min_netweight: Optional[Decimal] = None
    max_netweight: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# Seasonal trend response schemas
class CountryInfo(BaseModel):
    countryId: str

class SeasonalTrendItem(BaseModel):
    comodity: str
    growthPercentage: float
    averagePrice: str  # Changed to string for currency formatting
    countries: List[CountryInfo]
    period: str  # Simplified to just string instead of object

class SeasonalTrendResponse(BaseModel):
    data: List[SeasonalTrendItem]

# Country demand response schemas
class ProductInfo(BaseModel):
    id: str
    name: str
    growth: float

class CountryDemandData(BaseModel):
    countryId: str
    countryName: str
    growthPercentage: float
    currentTotalTransaction: float
    products: List[ProductInfo]

class CountryDemandResponse(BaseModel):
    data: List[CountryDemandData]
    
