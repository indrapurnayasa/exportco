from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, asc, func, text, select
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio
from app.models.export_data import ExportData
from app.models.komoditi import Komoditi
from app.models.currency_rates import CurrencyRates
from app.schemas.export_data import ExportDataCreate, ExportDataUpdate, ExportDataFilter

class ExportDataService:
    def __init__(self, db: Session):
        self.db = db

class AsyncExportDataService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache
    
    def _get_cache_key(self, method: str, *args) -> str:
        """Generate cache key for method calls"""
        return f"{method}:{':'.join(str(arg) for arg in args)}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False
        return datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self._cache_ttl)
    
    async def _get_cached_or_fetch(self, method: str, *args):
        """Get data from cache or fetch from database"""
        cache_key = self._get_cache_key(method, *args)
        
        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            return self._cache[cache_key]['data']
        
        # Fetch from database
        if method == 'get_latest_quarter':
            data = await self._get_latest_quarter()
        elif method == 'get_commodity_data':
            data = await self._get_commodity_data(*args)
        else:
            data = None
        
        # Cache the result
        if data is not None:
            self._cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now()
            }
        
        return data
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ExportData]:
        """Get all export data with pagination"""
        result = await self.db.execute(
            select(ExportData).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_id(self, export_id: str) -> Optional[ExportData]:
        """Get export data by ID"""
        result = await self.db.execute(
            select(ExportData).filter(ExportData.id == export_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, export_data: ExportDataCreate) -> ExportData:
        """Create new export data"""
        db_export_data = ExportData(**export_data.dict())
        self.db.add(db_export_data)
        await self.db.commit()
        await self.db.refresh(db_export_data)
        return db_export_data
    
    async def update(self, export_id: str, export_data: ExportDataUpdate) -> Optional[ExportData]:
        """Update existing export data"""
        db_export_data = await self.get_by_id(export_id)
        if not db_export_data:
            return None
        
        update_data = export_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_export_data, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_export_data)
        return db_export_data
    
    async def delete(self, export_id: str) -> bool:
        """Delete export data"""
        db_export_data = await self.get_by_id(export_id)
        if not db_export_data:
            return False
        
        await self.db.delete(db_export_data)
        await self.db.commit()
        return True
    
    async def filter_data(self, filters: ExportDataFilter, skip: int = 0, limit: int = 100) -> List[ExportData]:
        """Filter export data based on various criteria"""
        query = select(ExportData)
        
        # Apply filters
        if filters.provorig:
            query = query.filter(ExportData.provorig == filters.provorig)
        
        if filters.ctr:
            query = query.filter(ExportData.ctr == filters.ctr)
        
        if filters.pod:
            query = query.filter(ExportData.pod == filters.pod)
        
        if filters.tahun:
            query = query.filter(ExportData.tahun == filters.tahun)
        
        if filters.bulan:
            query = query.filter(ExportData.bulan == filters.bulan)
        
        if filters.ctr_code:
            query = query.filter(ExportData.ctr_code == filters.ctr_code)
        
        if filters.comodity_code:
            query = query.filter(ExportData.comodity_code == filters.comodity_code)
        
        if filters.min_value is not None:
            query = query.filter(ExportData.value >= filters.min_value)
        
        if filters.max_value is not None:
            query = query.filter(ExportData.value <= filters.max_value)
        
        if filters.min_netweight is not None:
            query = query.filter(ExportData.netweight >= filters.min_netweight)
        
        if filters.max_netweight is not None:
            query = query.filter(ExportData.netweight <= filters.max_netweight)
        
        if filters.start_date:
            query = query.filter(ExportData.created_at >= filters.start_date)
        
        if filters.end_date:
            query = query.filter(ExportData.created_at <= filters.end_date)
        
        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about export data"""
        # Get total records
        result = await self.db.execute(select(func.count(ExportData.id)))
        total_records = result.scalar()
        
        # Get total value
        result = await self.db.execute(
            select(func.sum(ExportData.value)).filter(ExportData.value.isnot(None))
        )
        total_value = result.scalar() or 0
        
        # Get total netweight
        result = await self.db.execute(
            select(func.sum(ExportData.netweight)).filter(ExportData.netweight.isnot(None))
        )
        total_netweight = result.scalar() or 0
        
        # Get unique counts
        result = await self.db.execute(select(func.count(func.distinct(ExportData.provorig))))
        unique_provorig = result.scalar()
        
        result = await self.db.execute(select(func.count(func.distinct(ExportData.ctr))))
        unique_ctr = result.scalar()
        
        result = await self.db.execute(select(func.count(func.distinct(ExportData.pod))))
        unique_pod = result.scalar()
        
        result = await self.db.execute(select(func.count(func.distinct(ExportData.tahun))))
        unique_tahun = result.scalar()
        
        return {
            "total_records": total_records,
            "total_value": float(total_value),
            "total_netweight": float(total_netweight),
            "unique_provinces": unique_provorig,
            "unique_countries": unique_ctr,
            "unique_ports": unique_pod,
            "unique_years": unique_tahun
        }
    
    async def search_by_kodehs(self, kodehs_search: str, skip: int = 0, limit: int = 100) -> List[ExportData]:
        """Search export data by HS code (partial match)"""
        result = await self.db.execute(
            select(ExportData)
            .filter(ExportData.kodehs.ilike(f"%{kodehs_search}%"))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_seasonal_trend(self, end_date: str = None) -> Dict[str, Any]:
        """Get seasonal trend data for a specific quarter"""
        try:
            # Check cache first (include end_date in cache key if provided)
            cache_key = f"seasonal_trend_{end_date}" if end_date else "seasonal_trend"
            if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
                return self._cache[cache_key]['data']
            
            # Get the quarter data based on end_date or latest available
            if end_date:
                quarter_data = self._parse_end_date_to_quarter(end_date)
                if not quarter_data:
                    return {'data': []}
                latest_year, latest_quarter = quarter_data
            else:
                latest_quarter_data = await self._get_latest_quarter()
                if not latest_quarter_data:
                    return {'data': []}
                latest_year, latest_quarter = latest_quarter_data
            
            # Calculate month range for the quarter
            start_month = (latest_quarter - 1) * 3 + 1
            end_month = latest_quarter * 3
            
            # Get previous quarter info for growth calculations
            prev_year, prev_quarter = self._get_previous_quarter(latest_year, latest_quarter)
            prev_start_month = (prev_quarter - 1) * 3 + 1
            prev_end_month = prev_quarter * 3
            
            # Single optimized query to get all commodity data with aggregation
            result = await self.db.execute(
                text("""
                    SELECT 
                        ed.comodity_code,
                        SUM(ed.netweight) as total_netweight,
                        COUNT(DISTINCT ed.ctr_code) as country_count
                    FROM export_data ed
                    WHERE ed.tahun = :year 
                        AND CAST(ed.bulan AS INTEGER) BETWEEN :start_month AND :end_month
                        AND ed.comodity_code IS NOT NULL
                        AND ed.netweight IS NOT NULL
                    GROUP BY ed.comodity_code
                    ORDER BY total_netweight DESC
                    LIMIT 50
                """),
                {
                    'year': latest_year,
                    'start_month': start_month,
                    'end_month': end_month
                }
            )
            commodity_data = result.fetchall()
            
            if not commodity_data:
                return {'data': []}
            
            # Get top countries for each commodity in a single query
            commodity_codes = [row.comodity_code for row in commodity_data]
            
            result = await self.db.execute(
                text("""
                    SELECT 
                        ed.comodity_code,
                        ed.ctr_code,
                        SUM(ed.netweight) as country_netweight
                    FROM export_data ed
                    WHERE ed.tahun = :year 
                        AND CAST(ed.bulan AS INTEGER) BETWEEN :start_month AND :end_month
                        AND ed.comodity_code = ANY(:commodity_codes)
                        AND ed.ctr_code IS NOT NULL
                        AND ed.netweight IS NOT NULL
                    GROUP BY ed.comodity_code, ed.ctr_code
                    ORDER BY ed.comodity_code, country_netweight DESC
                """),
                {
                    'year': latest_year,
                    'start_month': start_month,
                    'end_month': end_month,
                    'commodity_codes': commodity_codes
                }
            )
            country_data = result.fetchall()
            
            # Get previous quarter data for growth calculations in batch
            result = await self.db.execute(
                text("""
                    SELECT 
                        comodity_code,
                        SUM(netweight) as total_netweight
                    FROM export_data 
                    WHERE tahun = :year 
                        AND CAST(bulan AS INTEGER) BETWEEN :start_month AND :end_month
                        AND comodity_code = ANY(:commodity_codes)
                        AND netweight IS NOT NULL
                    GROUP BY comodity_code
                """),
                {
                    'year': prev_year,
                    'start_month': prev_start_month,
                    'end_month': prev_end_month,
                    'commodity_codes': commodity_codes
                }
            )
            prev_quarter_data = {row.comodity_code: row.total_netweight for row in result.fetchall()}
            
            # Get commodity names and prices in batch
            result = await self.db.execute(
                select(Komoditi.kode_komoditi, Komoditi.nama_komoditi, Komoditi.harga_komoditi)
                .filter(Komoditi.kode_komoditi.in_(commodity_codes))
            )
            commodities = result.fetchall()
            commodity_map = {c.kode_komoditi: c for c in commodities}
            
            # Process country data by commodity
            country_by_commodity = {}
            for row in country_data:
                if row.comodity_code not in country_by_commodity:
                    country_by_commodity[row.comodity_code] = []
                country_by_commodity[row.comodity_code].append({
                    'countryId': row.ctr_code,
                    'netweight': row.country_netweight
                })
            
            # Build response
            result_data = []
            quarter_name = f"Q{latest_quarter} {latest_year}"
            
            for row in commodity_data:
                comodity_code = row.comodity_code
                current_netweight = row.total_netweight or 0
                
                # Calculate growth percentage
                prev_netweight = prev_quarter_data.get(comodity_code, 0)
                growth_percentage = 0.0
                if prev_netweight > 0:
                    growth_percentage = ((current_netweight - prev_netweight) / prev_netweight) * 100
                
                # Get commodity info
                commodity_info = commodity_map.get(comodity_code)
                comodity_name = commodity_info.nama_komoditi if commodity_info else comodity_code
                
                # Get average price
                average_price = "Rp 0/kg"
                if commodity_info and commodity_info.harga_komoditi:
                    try:
                        price = float(commodity_info.harga_komoditi)
                        average_price = f"Rp {price:,.0f}/kg".replace(",", ".")
                    except (ValueError, TypeError):
                        pass
                
                # Get top 3 countries
                countries = []
                if comodity_code in country_by_commodity:
                    top_countries = sorted(
                        country_by_commodity[comodity_code],
                        key=lambda x: x['netweight'],
                        reverse=True
                    )[:3]
                    countries = [{'countryId': c['countryId']} for c in top_countries]
                
                result_data.append({
                    'comodity': comodity_name,
                    'growthPercentage': round(growth_percentage, 2),
                    'averagePrice': average_price,
                    'countries': countries,
                    'period': quarter_name
                })
            
            # Sort by growth percentage from highest to lowest
            result_data.sort(key=lambda x: x['growthPercentage'], reverse=True)
            
            response_data = {'data': result_data}
            
            # Cache the result
            self._cache[cache_key] = {
                'data': response_data,
                'timestamp': datetime.now()
            }
            
            return response_data
            
        except Exception as e:
            print(f"Error in get_seasonal_trend: {e}")
            return {'data': []}
    
    async def _get_latest_quarter(self) -> Optional[tuple]:
        """Get the latest year and quarter efficiently using SQL aggregation"""
        try:
            # Use SQL to find the latest quarter directly
            result = await self.db.execute(
                text("""
                    SELECT 
                        tahun,
                        bulan,
                        CAST(bulan AS INTEGER) as month_num,
                        (CAST(bulan AS INTEGER) - 1) / 3 + 1 as quarter
                    FROM export_data 
                    WHERE tahun IS NOT NULL 
                        AND bulan IS NOT NULL
                        AND bulan ~ '^[0-9]+$'
                    ORDER BY 
                        CAST(tahun AS INTEGER) DESC,
                        CAST(bulan AS INTEGER) DESC
                    LIMIT 1
                """)
            )
            
            row = result.fetchone()
            if row:
                return (row.tahun, row.quarter)
            
            return None
            
        except Exception as e:
            print(f"Error getting latest quarter: {e}")
            return None
    
    def _process_quarter_data(self, records: List[ExportData], quarter: int) -> Dict[str, Any]:
        """Process quarter data in memory to get commodity summaries and top countries"""
        commodity_data = {}
        
        for record in records:
            # Calculate quarter from month
            try:
                month_num = int(record.bulan)
                record_quarter = (month_num - 1) // 3 + 1
                
                # Only process records for the target quarter
                if record_quarter != quarter:
                    continue
            except (ValueError, TypeError):
                continue
            
            comodity_code = record.comodity_code
            netweight = float(record.netweight) if record.netweight else 0
            country_code = record.ctr_code  # Use ctr_code instead of ctr
            
            # Initialize commodity data if not exists
            if comodity_code not in commodity_data:
                commodity_data[comodity_code] = {
                    'total_netweight': 0,
                    'countries': {}
                }
            
            # Add netweight
            commodity_data[comodity_code]['total_netweight'] += netweight
            
            # Track country data using country code
            if country_code:
                if country_code not in commodity_data[comodity_code]['countries']:
                    commodity_data[comodity_code]['countries'][country_code] = 0
                commodity_data[comodity_code]['countries'][country_code] += netweight
        
        # Convert to final format with top 3 countries
        result = {}
        for comodity_code, data in commodity_data.items():
            # Sort countries by netweight and get top 3
            sorted_countries = sorted(
                data['countries'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            
            countries_list = [
                {'countryId': country_code, 'rank': i + 1}
                for i, (country_code, _) in enumerate(sorted_countries)
            ]
            
            result[comodity_code] = {
                'total_netweight': data['total_netweight'],
                'countries': countries_list
            }
        
        return result
    
    async def _calculate_growth_percentage_optimized(self, comodity_code: str, current_year: str, current_quarter: int) -> float:
        """Calculate quarter-over-quarter growth percentage efficiently"""
        try:
            # Get current quarter total netweight
            current_netweight = await self._get_quarter_netweight(comodity_code, current_year, current_quarter)
            
            if current_netweight == 0:
                return 0.0
            
            # Calculate previous quarter
            prev_year, prev_quarter = self._get_previous_quarter(current_year, current_quarter)
            
            # Get previous quarter total netweight
            previous_netweight = await self._get_quarter_netweight(comodity_code, prev_year, prev_quarter)
            
            if previous_netweight == 0:
                return 0.0
            
            # Calculate growth percentage
            growth = ((current_netweight - previous_netweight) / previous_netweight) * 100
            return round(growth, 2)
            
        except Exception as e:
            print(f"Error calculating growth percentage: {e}")
            return 0.0
    
    async def _get_quarter_netweight(self, comodity_code: str, year: str, quarter: int) -> float:
        """Get total netweight for a specific quarter efficiently"""
        try:
            # Calculate month range for the quarter
            start_month = (quarter - 1) * 3 + 1
            end_month = quarter * 3
            
            # Get all records for the quarter
            result = await self.db.execute(
                select(ExportData).filter(
                    ExportData.comodity_code == comodity_code,
                    ExportData.tahun == year,
                    ExportData.netweight.isnot(None)
                )
            )
            records = result.scalars().all()
            
            total_netweight = 0
            for record in records:
                try:
                    month_num = int(record.bulan)
                    if start_month <= month_num <= end_month:
                        total_netweight += float(record.netweight) if record.netweight else 0
                except (ValueError, TypeError):
                    continue
            
            return total_netweight
            
        except Exception as e:
            print(f"Error getting quarter netweight: {e}")
            return 0.0
    
    def _parse_end_date_to_quarter(self, end_date: str) -> Optional[tuple]:
        """Parse end date in DD-MM-YYYY format and return year and quarter"""
        try:
            if not end_date:
                return None
                
            # Parse the date
            day, month, year = end_date.split('-')
            day, month, year = int(day), int(month), int(year)
            
            # Calculate quarter based on month
            quarter = (month - 1) // 3 + 1
            
            return (str(year), quarter)
            
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Error parsing end date '{end_date}': {e}")
            return None
    
    def _get_previous_quarter(self, year: str, quarter: int) -> tuple:
        """Get previous quarter year and quarter number"""
        if quarter == 1:
            return str(int(year) - 1), 4
        else:
            return year, quarter - 1
    
    def _get_previous_month(self, year: str, month: int) -> tuple:
        """Get previous month year and month number"""
        if month == 1:
            return str(int(year) - 1), 12
        else:
            return year, month - 1
    
    def _get_commodity_price(self, commodity_info: Optional[Komoditi]) -> str:
        """Get commodity price from commodity info formatted as Indonesian Rupiah per kg"""
        try:
            if commodity_info and commodity_info.harga_komoditi:
                price = float(commodity_info.harga_komoditi)
                # Format as Indonesian Rupiah per kg
                formatted_price = f"Rp {price:,.0f}/kg".replace(",", ".")
                return formatted_price
            return "Rp 0/kg"
        except Exception as e:
            print(f"Error getting commodity price: {e}")
            return "Rp 0/kg"
    
    async def _get_latest_usd_to_idr_rate(self) -> float:
        """Get the latest USD to IDR exchange rate"""
        try:
            result = await self.db.execute(
                select(CurrencyRates.rate)
                .filter(
                    CurrencyRates.base_currency == 'USD',
                    CurrencyRates.target_currency == 'IDR'
                )
                .order_by(CurrencyRates.rate_date.desc(), CurrencyRates.created_at.desc())
                .limit(1)
            )
            
            rate = result.scalar_one_or_none()
            if rate:
                return float(rate)
            else:
                print("No USD to IDR exchange rate found, using default rate of 1.0")
                return 1.0
                
        except Exception as e:
            print(f"Error getting USD to IDR exchange rate: {e}")
            return 1.0

    async def get_country_demand(self, end_date: str = None) -> Dict[str, Any]:
        """Get all commodities for top 20 countries with growth calculations"""
        try:
            # Check cache first (include end_date in cache key if provided)
            cache_key = f"country_demand_{end_date}" if end_date else "country_demand"
            if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
                return self._cache[cache_key]['data']
            
            # Get the quarter data based on end_date or latest available
            if end_date:
                quarter_data = self._parse_end_date_to_quarter(end_date)
                if not quarter_data:
                    return {'data': []}
                current_year, current_quarter = quarter_data
            else:
                latest_quarter_data = await self._get_latest_quarter()
                if not latest_quarter_data:
                    return {'data': []}
                current_year, current_quarter = latest_quarter_data
            
            # For month-over-month growth, we need to determine which month to use
            # If end_date is provided, extract the month from it
            if end_date:
                # Parse the end_date to get the specific month
                try:
                    day, month, year = end_date.split('-')
                    current_month = int(month)
                    current_year = year
                except:
                    # Fallback to using the last month of the quarter
                    current_month = current_quarter * 3
                    current_year = current_year
            else:
                # Use the last month of the current quarter
                current_month = current_quarter * 3
                current_year = current_year
            
            # Get previous month info (for month-over-month growth)
            prev_year, prev_month = self._get_previous_month(current_year, current_month)
            
            # Single query to get all country totals for current month with aggregation
            result = await self.db.execute(
                text("""
                    SELECT 
                        ctr_code,
                        ctr as country_name,
                        SUM(value) as total_value
                    FROM export_data 
                    WHERE tahun = :year 
                        AND CAST(bulan AS INTEGER) = :month
                        AND ctr_code IS NOT NULL 
                        AND value IS NOT NULL
                    GROUP BY ctr_code, ctr
                    ORDER BY total_value DESC
                    LIMIT 20
                """),
                {
                    'year': current_year,
                    'month': current_month
                }
            )
            top_countries_data = result.fetchall()
            
            if not top_countries_data:
                return {'data': []}
            
            # Get all commodity data for top countries in a single query
            country_codes = [row.ctr_code for row in top_countries_data]
            
            # Get commodity data for current month
            result = await self.db.execute(
                text("""
                    SELECT 
                        ed.ctr_code,
                        ed.comodity_code,
                        ed.ctr as country_name,
                        SUM(ed.netweight) as total_netweight,
                        SUM(ed.value) as total_value
                    FROM export_data ed
                    WHERE ed.tahun = :year 
                        AND CAST(ed.bulan AS INTEGER) = :month
                        AND ed.ctr_code = ANY(:country_codes)
                        AND ed.comodity_code IS NOT NULL
                        AND ed.netweight IS NOT NULL
                    GROUP BY ed.ctr_code, ed.comodity_code, ed.ctr
                    ORDER BY ed.ctr_code, total_netweight DESC
                """),
                {
                    'year': current_year,
                    'month': current_month,
                    'country_codes': country_codes
                }
            )
            commodity_data = result.fetchall()
            
            # Get commodity codes from the current quarter data
            commodity_codes = list(set([row.comodity_code for row in commodity_data]))
            
            # Get previous month data for country growth calculations
            result = await self.db.execute(
                text("""
                    SELECT 
                        ctr_code,
                        SUM(value) as total_value
                    FROM export_data 
                    WHERE tahun = :year 
                        AND CAST(bulan AS INTEGER) = :month
                        AND ctr_code = ANY(:country_codes)
                        AND value IS NOT NULL
                    GROUP BY ctr_code
                """),
                {
                    'year': prev_year,
                    'month': prev_month,
                    'country_codes': country_codes
                }
            )
            prev_month_data = {row.ctr_code: float(row.total_value) if row.total_value else 0.0 for row in result.fetchall()}
            
            # Get previous month data for commodity growth calculations
            if commodity_codes:  # Only query if we have commodity codes
                result = await self.db.execute(
                    text("""
                        SELECT 
                            ctr_code,
                            comodity_code,
                            SUM(value) as total_value
                        FROM export_data 
                        WHERE tahun = :year 
                            AND CAST(bulan AS INTEGER) = :month
                            AND ctr_code = ANY(:country_codes)
                            AND comodity_code = ANY(:commodity_codes)
                            AND value IS NOT NULL
                        GROUP BY ctr_code, comodity_code
                    """),
                    {
                        'year': prev_year,
                        'month': prev_month,
                        'country_codes': country_codes,
                        'commodity_codes': commodity_codes
                    }
                )
                prev_month_commodity_data = {}
                for row in result.fetchall():
                    key = f"{row.ctr_code}_{row.comodity_code}"
                    prev_month_commodity_data[key] = float(row.total_value) if row.total_value else 0.0
            else:
                prev_month_commodity_data = {}
            
            # Get commodity names and prices in batch
            result = await self.db.execute(
                select(Komoditi.kode_komoditi, Komoditi.nama_komoditi, Komoditi.harga_komoditi)
                .filter(Komoditi.kode_komoditi.in_(commodity_codes))
            )
            commodity_info = {row.kode_komoditi: row for row in result.fetchall()}
            
            # Get latest USD to IDR exchange rate
            usd_to_idr_rate = await self._get_latest_usd_to_idr_rate()
            # Ensure it's a float
            usd_to_idr_rate = float(usd_to_idr_rate)
            print(f"Debug: USD to IDR rate: {usd_to_idr_rate} (type: {type(usd_to_idr_rate)})")
            
            # Process data
            country_data_map = {}
            
            # Initialize country data
            for row in top_countries_data:
                prev_value = prev_month_data.get(row.ctr_code, 0)
                current_value_usd = float(row.total_value) if row.total_value else 0.0
                
                # Convert USD to IDR
                current_value_idr = current_value_usd * usd_to_idr_rate
                
                # Debug logging for first few countries
                if len(country_data_map) < 3:
                    print(f"Debug: {row.ctr_code} - USD: {current_value_usd} (type: {type(current_value_usd)}), IDR: {current_value_idr} (type: {type(current_value_idr)})")
                
                growth = 0.0
                if prev_value > 0:
                    growth = ((current_value_usd - float(prev_value)) / float(prev_value)) * 100
                
                country_data_map[row.ctr_code] = {
                    'countryId': row.ctr_code,
                    'countryName': row.country_name or row.ctr_code,
                    'growthPercentage': round(growth, 2),
                    'currentTotalTransaction': round(current_value_idr, 2),
                    'products': []
                }
            
            # Add commodity data
            for row in commodity_data:
                if row.ctr_code in country_data_map:
                    commodity_data_row = commodity_info.get(row.comodity_code)
                    commodity_name = commodity_data_row.nama_komoditi if commodity_data_row else row.comodity_code
                    
                    # Get price from commodity info
                    price = "Rp 0/kg"
                    if commodity_data_row and commodity_data_row.harga_komoditi:
                        try:
                            price_value = float(commodity_data_row.harga_komoditi)
                            price = f"Rp {price_value:,.0f}/kg".replace(",", ".")
                        except (ValueError, TypeError):
                            price = "Rp 0/kg"
                    
                    # Calculate commodity growth for this country
                    current_commodity_value = float(row.total_value) if row.total_value else 0.0
                    commodity_key = f"{row.ctr_code}_{row.comodity_code}"
                    prev_commodity_value = prev_month_commodity_data.get(commodity_key, 0.0)
                    
                    commodity_growth = 0.0
                    if prev_commodity_value > 0:
                        commodity_growth = ((current_commodity_value - prev_commodity_value) / prev_commodity_value) * 100
                    
                    country_data_map[row.ctr_code]['products'].append({
                        'id': row.comodity_code,
                        'name': commodity_name,
                        'price': price,
                        'growth': round(commodity_growth, 2)
                    })
            
            # Sort products within each country by growth percentage (highest to lowest)
            for country_code in country_data_map:
                country_data_map[country_code]['products'].sort(key=lambda x: x['growth'], reverse=True)
            
            # Convert to list and sort by growth percentage from highest to lowest
            all_country_data = list(country_data_map.values())
            all_country_data.sort(key=lambda x: x['growthPercentage'], reverse=True)
            
            result_data = {'data': all_country_data}
            
            # Cache the result
            self._cache[cache_key] = {
                'data': result_data,
                'timestamp': datetime.now()
            }
            
            return result_data
            
        except Exception as e:
            print(f"Error in get_country_demand: {e}")
            return {'data': []} 

    async def get_top_commodity_by_country(self, end_date: str = None, country_id: str = None) -> Dict[str, Any]:
        """Get the top commodity from every country with optional date and country filtering"""
        try:
            # Check cache first (include end_date and country_id in cache key if provided)
            cache_key = f"top_commodity_by_country_{end_date}_{country_id}" if end_date or country_id else "top_commodity_by_country"
            if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
                return self._cache[cache_key]['data']
            
            # Get the quarter data based on end_date or latest available
            if end_date:
                quarter_data = self._parse_end_date_to_quarter(end_date)
                if not quarter_data:
                    return {'data': []}
                current_year, current_quarter = quarter_data
            else:
                latest_quarter_data = await self._get_latest_quarter()
                if not latest_quarter_data:
                    return {'data': []}
                current_year, current_quarter = latest_quarter_data
            
            # For month-over-month growth, we need to determine which month to use
            # If end_date is provided, extract the month from it
            if end_date:
                # Parse the end_date to get the specific month
                try:
                    day, month, year = end_date.split('-')
                    current_month = int(month)
                    current_year = year
                except:
                    # Fallback to using the last month of the quarter
                    current_month = current_quarter * 3
                    current_year = current_year
            else:
                # Use the last month of the current quarter
                current_month = current_quarter * 3
                current_year = current_year
            
            # Get previous month info (for month-over-month growth)
            prev_year, prev_month = self._get_previous_month(current_year, current_month)
            
            # Build the query with optional country filtering
            if country_id:
                # Filter by specific country - get ALL commodities
                result = await self.db.execute(
                    text("""
                        SELECT 
                            ed.ctr_code,
                            ed.ctr as country_name,
                            ed.comodity_code,
                            SUM(ed.value) as total_value,
                            SUM(ed.netweight) as total_netweight
                        FROM export_data ed
                        WHERE ed.tahun = :year 
                            AND CAST(ed.bulan AS INTEGER) = :month
                            AND ed.ctr_code = :country_id
                            AND ed.comodity_code IS NOT NULL
                            AND ed.value IS NOT NULL
                        GROUP BY ed.ctr_code, ed.ctr, ed.comodity_code
                        ORDER BY ed.ctr_code, total_value DESC
                    """),
                    {
                        'year': current_year,
                        'month': current_month,
                        'country_id': country_id
                    }
                )
            else:
                # Get all countries - get ALL commodities
                result = await self.db.execute(
                    text("""
                        SELECT 
                            ed.ctr_code,
                            ed.ctr as country_name,
                            ed.comodity_code,
                            SUM(ed.value) as total_value,
                            SUM(ed.netweight) as total_netweight
                        FROM export_data ed
                        WHERE ed.tahun = :year 
                            AND CAST(ed.bulan AS INTEGER) = :month
                            AND ed.ctr_code IS NOT NULL 
                            AND ed.comodity_code IS NOT NULL
                            AND ed.value IS NOT NULL
                        GROUP BY ed.ctr_code, ed.ctr, ed.comodity_code
                        ORDER BY ed.ctr_code, total_value DESC
                    """),
                    {
                        'year': current_year,
                        'month': current_month
                    }
                )
            
            top_commodities_data = result.fetchall()
            
            if not top_commodities_data:
                return {'data': []}
            
            # Get commodity codes for price lookup
            commodity_codes = list(set([row.comodity_code for row in top_commodities_data]))
            
            # Get previous month data for growth calculations
            result = await self.db.execute(
                text("""
                    SELECT 
                        ctr_code,
                        comodity_code,
                        SUM(value) as total_value
                    FROM export_data 
                    WHERE tahun = :year 
                        AND CAST(bulan AS INTEGER) = :month
                        AND ctr_code = ANY(:country_codes)
                        AND comodity_code = ANY(:commodity_codes)
                        AND value IS NOT NULL
                    GROUP BY ctr_code, comodity_code
                """),
                {
                    'year': prev_year,
                    'month': prev_month,
                    'country_codes': [row.ctr_code for row in top_commodities_data],
                    'commodity_codes': commodity_codes
                }
            )
            prev_month_data = {}
            for row in result.fetchall():
                key = f"{row.ctr_code}_{row.comodity_code}"
                prev_month_data[key] = float(row.total_value) if row.total_value else 0.0
            
            # Get commodity names and prices in batch
            result = await self.db.execute(
                select(Komoditi.kode_komoditi, Komoditi.nama_komoditi, Komoditi.harga_komoditi)
                .filter(Komoditi.kode_komoditi.in_(commodity_codes))
            )
            commodity_info = {row.kode_komoditi: row for row in result.fetchall()}
            
            # Get latest USD to IDR exchange rate
            usd_to_idr_rate = await self._get_latest_usd_to_idr_rate()
            usd_to_idr_rate = float(usd_to_idr_rate)
            
            # Process data and calculate growth for all commodities per country
            country_commodities = {}
            
            for row in top_commodities_data:
                country_code = row.ctr_code
                if country_code not in country_commodities:
                    country_commodities[country_code] = {
                        'countryId': country_code,
                        'countryName': row.country_name or country_code,
                        'commodities': []
                    }
                
                # Get commodity info
                commodity_data_row = commodity_info.get(row.comodity_code)
                commodity_name = commodity_data_row.nama_komoditi if commodity_data_row else row.comodity_code
                
                # Get price from commodity info
                price = "Rp 0/kg"
                if commodity_data_row and commodity_data_row.harga_komoditi:
                    try:
                        price_value = float(commodity_data_row.harga_komoditi)
                        price = f"Rp {price_value:,.0f}/kg".replace(",", ".")
                    except (ValueError, TypeError):
                        price = "Rp 0/kg"
                
                # Calculate growth percentage
                current_value_usd = float(row.total_value) if row.total_value else 0.0
                commodity_key = f"{row.ctr_code}_{row.comodity_code}"
                prev_value = prev_month_data.get(commodity_key, 0.0)
                
                growth = 0.0
                if prev_value > 0:
                    growth = ((current_value_usd - prev_value) / prev_value) * 100
                
                # Convert USD to IDR
                current_value_idr = current_value_usd * usd_to_idr_rate
                
                country_commodities[country_code]['commodities'].append({
                    'id': row.comodity_code,
                    'name': commodity_name,
                    'price': price,
                    'growth': round(growth, 2),
                    'valueUSD': round(current_value_usd, 2),
                    'valueIDR': round(current_value_idr, 2),
                    'netweight': round(float(row.total_netweight) if row.total_netweight else 0.0, 2)
                })
            
            # Sort commodities by growth (highest to lowest) and get the top one for each country
            result_data = []
            
            for country_code, country_data in country_commodities.items():
                # Sort commodities by growth percentage (highest to lowest)
                sorted_commodities = sorted(
                    country_data['commodities'], 
                    key=lambda x: x['growth'], 
                    reverse=True
                )
                
                # Get the commodity with highest growth
                top_commodity = sorted_commodities[0] if sorted_commodities else None
                
                if top_commodity:
                    result_data.append({
                        'countryId': country_data['countryId'],
                        'countryName': country_data['countryName'],
                        'topCommodity': top_commodity
                    })
            
            # Sort countries by their top commodity's growth percentage (highest to lowest)
            result_data.sort(key=lambda x: x['topCommodity']['growth'], reverse=True)
            
            response_data = {'data': result_data}
            
            # Cache the result
            self._cache[cache_key] = {
                'data': response_data,
                'timestamp': datetime.now()
            }
            
            return response_data
            
        except Exception as e:
            print(f"Error in get_top_commodity_by_country: {e}")
            return {'data': []} 