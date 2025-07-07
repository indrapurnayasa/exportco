from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, asc, func, text, select
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio
from app.models.export_data import ExportData
from app.models.komoditi import Komoditi
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

    async def get_seasonal_trend(self) -> Dict[str, Any]:
        """Get seasonal trend data for the latest quarter"""
        try:
            # Step 1: Get the latest quarter efficiently
            latest_quarter_data = await self._get_latest_quarter()
            if not latest_quarter_data:
                return {'data': []}
            
            latest_year, latest_quarter = latest_quarter_data
            
            # Step 2: Get all export data for the latest quarter in one query
            # Add timeout and connection management
            result = await self.db.execute(
                select(ExportData).filter(
                    ExportData.tahun == latest_year,
                    ExportData.netweight.isnot(None),
                    ExportData.comodity_code.isnot(None)
                ).limit(10000)  # Add reasonable limit for production
            )
            latest_quarter_records = result.scalars().all()
            
            if not latest_quarter_records:
                return {'data': []}
            
            # Step 3: Process data in memory (much faster than multiple DB calls)
            commodity_data = self._process_quarter_data(latest_quarter_records, latest_quarter)
            
            if not commodity_data:
                return {'data': []}
            
            # Step 4: Get commodity names and prices in one query
            commodity_codes = list(commodity_data.keys())
            result = await self.db.execute(
                select(Komoditi).filter(Komoditi.kode_komoditi.in_(commodity_codes))
            )
            commodities = result.scalars().all()
            commodity_map = {c.kode_komoditi: c for c in commodities}
            
            # Step 5: Build response with growth and price calculations
            result_data = []
            quarter_name = f"Q{latest_quarter} {latest_year}"
            
            for comodity_code, data in commodity_data.items():
                commodity_info = commodity_map.get(comodity_code)
                comodity_name = commodity_info.nama_komoditi if commodity_info else comodity_code
                
                # Calculate growth percentage
                growth_percentage = await self._calculate_growth_percentage_optimized(
                    comodity_code, latest_year, latest_quarter
                )
                
                # Get average price
                average_price = self._get_commodity_price(commodity_info)
                
                # Format countries list
                countries = [{'countryId': c['countryId']} for c in data['countries']]
                
                result_data.append({
                    'comodity': comodity_name,
                    'growthPercentage': growth_percentage,
                    'averagePrice': average_price,
                    'countries': countries,
                    'period': quarter_name
                })
            
            return {'data': result_data}
            
        except Exception as e:
            # Add proper logging for production
            print(f"Error in get_seasonal_trend: {e}")
            # Return empty data instead of failing completely
            return {'data': []}
        finally:
            # Ensure we don't hold connections too long
            await self.db.close()
    
    async def _get_latest_quarter(self) -> Optional[tuple]:
        """Get the latest year and quarter efficiently"""
        try:
            # Get all unique year-month combinations
            result = await self.db.execute(
                select(ExportData.tahun, ExportData.bulan)
                .filter(
                    ExportData.tahun.isnot(None),
                    ExportData.bulan.isnot(None)
                )
                .distinct()
            )
            year_month_data = result.all()
            
            if not year_month_data:
                return None
            
            # Find the latest quarter
            latest_year = None
            latest_quarter = None
            
            for tahun, bulan in year_month_data:
                try:
                    month_num = int(bulan)
                    quarter = (month_num - 1) // 3 + 1
                    
                    if latest_year is None or (
                        int(tahun) > int(latest_year) or 
                        (int(tahun) == int(latest_year) and quarter > latest_quarter)
                    ):
                        latest_year = tahun
                        latest_quarter = quarter
                except (ValueError, TypeError):
                    continue
            
            return (latest_year, latest_quarter) if latest_year else None
            
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
    
    def _get_previous_quarter(self, year: str, quarter: int) -> tuple:
        """Get previous quarter year and quarter number"""
        if quarter == 1:
            return str(int(year) - 1), 4
        else:
            return year, quarter - 1
    
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
    
    async def get_country_demand(self) -> Dict[str, Any]:
        """Get all commodities for top 20 countries with growth calculations"""
        try:
            # Get the latest quarter data
            latest_quarter_data = await self._get_latest_quarter()
            if not latest_quarter_data:
                return {'data': []}
            
            current_year, current_quarter = latest_quarter_data
            
            # Get all unique countries for the current year
            result = await self.db.execute(
                select(ExportData.ctr_code)
                .filter(
                    ExportData.ctr_code.isnot(None),
                    ExportData.tahun == current_year
                )
                .distinct()
            )
            all_countries = result.scalars().all()
            
            if not all_countries:
                return {'data': []}
            
            # Calculate total value for each country to get top 10
            country_totals = {}
            for country in all_countries:
                # Get all records for the current quarter and country
                result = await self.db.execute(
                    select(ExportData).filter(
                        ExportData.ctr_code == country,
                        ExportData.tahun == current_year,
                        ExportData.value.isnot(None)
                    )
                )
                records = result.scalars().all()
                
                total_value = 0
                for record in records:
                    try:
                        month_num = int(record.bulan)
                        record_quarter = (month_num - 1) // 3 + 1
                        if record_quarter == current_quarter:
                            total_value += float(record.value) if record.value else 0
                    except (ValueError, TypeError):
                        continue
                
                country_totals[country] = total_value
            
            # Get top 20 countries by total value
            top_countries = sorted(
                country_totals.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]
            
            # Get data for top 20 countries only
            all_country_data = []
            
            for country, _ in top_countries:
                # Get all records for the current quarter and country
                result = await self.db.execute(
                    select(ExportData).filter(
                        ExportData.ctr_code == country,
                        ExportData.tahun == current_year,
                        ExportData.value.isnot(None),
                        ExportData.comodity_code.isnot(None)
                    )
                )
                records = result.scalars().all()
                
                # Get country name from the first record (if available)
                country_name = records[0].ctr if records and records[0].ctr else country
                
                # Process quarter data to get commodity summaries
                quarter_data = self._process_quarter_data_for_country(records, current_quarter, country)
                
                # Get all commodities by netweight (no limit)
                all_commodities = sorted(
                    quarter_data.items(),
                    key=lambda x: x[1]['total_netweight'],
                    reverse=True
                )
                
                # Calculate country growth percentage (quarter-over-quarter) using total value
                country_growth = await self._calculate_country_growth_percentage_by_value(country, current_year, current_quarter)
                
                # Get current quarter total transaction value for the country
                current_total_transaction = await self._get_current_quarter_total_value(country, current_year, current_quarter)
                
                # Build products list
                products = []
                for comodity_code, data in all_commodities:
                    try:
                        # Get commodity name from komoditi table
                        commodity_info = await self._get_commodity_info(comodity_code)
                        commodity_name = commodity_info.nama_komoditi if commodity_info else comodity_code
                        
                        # Calculate growth for this commodity
                        commodity_growth = await self._calculate_growth_percentage_optimized(
                            comodity_code, current_year, current_quarter
                        )
                        
                        products.append({
                            'id': comodity_code,
                            'name': commodity_name,
                            'growth': commodity_growth
                        })
                    except Exception as e:
                        print(f"Error processing commodity {comodity_code}: {e}")
                        # Add commodity with code as name if lookup fails
                        products.append({
                            'id': comodity_code,
                            'name': comodity_code,
                            'growth': 0.0
                        })
                
                all_country_data.append({
                    'countryId': country,
                    'countryName': country_name,
                    'growthPercentage': country_growth,
                    'currentTotalTransaction': current_total_transaction,
                    'products': products
                })
            
            # Sort countries alphabetically
            all_country_data.sort(key=lambda x: x['countryName'])
            
            return {
                'data': all_country_data
            }
            
        except Exception as e:
            print(f"Error in get_country_demand: {e}")
            return {'data': []}
    
    def _process_quarter_data_for_country(self, records: List[ExportData], quarter: int, country_code: str) -> Dict[str, Any]:
        """Process quarter data for a specific country to get commodity summaries"""
        commodity_data = {}
        
        for record in records:
            # Calculate quarter from month
            try:
                month_num = int(record.bulan)
                record_quarter = (month_num - 1) // 3 + 1
                
                # Only process records for the target quarter and country
                if record_quarter != quarter or record.ctr_code != country_code:
                    continue
            except (ValueError, TypeError):
                continue
            
            comodity_code = record.comodity_code
            netweight = float(record.netweight) if record.netweight else 0
            
            # Initialize commodity data if not exists
            if comodity_code not in commodity_data:
                commodity_data[comodity_code] = {
                    'total_netweight': 0
                }
            
            # Add netweight
            commodity_data[comodity_code]['total_netweight'] += netweight
        
        return commodity_data
    
    async def _calculate_country_growth_percentage_by_value(self, country_code: str, current_year: str, current_quarter: int) -> float:
        """Calculate quarter-over-quarter growth percentage for a country using total value"""
        try:
            # Get current quarter total transaction value for the country
            current_total_transaction = await self._get_current_quarter_total_value(country_code, current_year, current_quarter)
            
            if current_total_transaction == 0:
                return 0.0
            
            # Calculate previous quarter
            prev_year, prev_quarter = self._get_previous_quarter(current_year, current_quarter)
            
            # Get previous quarter total transaction value for the country
            previous_total_transaction = await self._get_current_quarter_total_value(country_code, prev_year, prev_quarter)
            
            if previous_total_transaction == 0:
                return 0.0
            
            # Calculate growth percentage
            growth = ((current_total_transaction - previous_total_transaction) / previous_total_transaction) * 100
            return round(growth, 2)
            
        except Exception as e:
            print(f"Error calculating country growth percentage: {e}")
            return 0.0
    
    async def _get_current_quarter_total_value(self, country_code: str, year: str, quarter: int) -> float:
        """Get current quarter total transaction value for a country"""
        try:
            # Calculate month range for the quarter
            start_month = (quarter - 1) * 3 + 1
            end_month = quarter * 3
            
            # Get all records for the quarter and country
            result = await self.db.execute(
                select(ExportData).filter(
                    ExportData.ctr_code == country_code,
                    ExportData.tahun == year,
                    ExportData.value.isnot(None)
                )
            )
            records = result.scalars().all()
            
            total_value = 0
            for record in records:
                try:
                    month_num = int(record.bulan)
                    if start_month <= month_num <= end_month:
                        if record.value:
                            total_value += float(record.value)
                except (ValueError, TypeError):
                    continue
            
            return total_value
            
        except Exception as e:
            print(f"Error getting current quarter total transaction value for {country_code}: {e}")
            return 0.0
    
    async def _get_commodity_info(self, comodity_code: str) -> Optional[Komoditi]:
        """Get commodity information by code"""
        try:
            if not comodity_code:
                return None
                
            result = await self.db.execute(
                select(Komoditi).filter(Komoditi.kode_komoditi == comodity_code)
            )
            commodity = result.scalars().first()  # Use first() instead of scalar_one_or_none() to handle duplicates
            
            if not commodity:
                print(f"No commodity found for code: {comodity_code}")
            
            return commodity
        except Exception as e:
            print(f"Error getting commodity info for {comodity_code}: {e}")
            return None 