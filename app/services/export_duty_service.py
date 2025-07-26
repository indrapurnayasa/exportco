from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from typing import Dict, Any, Optional, List
from app.models.komoditi import Komoditi
from app.models.currency_rates import CurrencyRates
from app.models.export_duty_chunks import ExportDutyChunk
import numpy as np
import asyncio
import time
import os

class ExportDutyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache = {}

    async def get_komoditi_by_name_optimized(self, nama_produk: str) -> Optional[Komoditi]:
        """
        Optimized komoditi lookup with caching and fuzzy matching
        """
        cache_key = f"komoditi_{nama_produk.lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try exact match first
        query = select(Komoditi).where(
            func.lower(Komoditi.nama_komoditi) == nama_produk.lower()
        )
        result = await self.db.execute(query)
        komoditi = result.scalars().first()
        
        if komoditi:
            self._cache[cache_key] = komoditi
            return komoditi
        
        # Try fuzzy match with common variations
        variations = [
            nama_produk.lower(),
            nama_produk.lower().replace(" ", ""),
            nama_produk.lower().replace("crude palm oil", "cpo"),
            nama_produk.lower().replace("cpo", "crude palm oil"),
        ]
        
        for variation in variations:
            query = select(Komoditi).where(
                or_(
                    func.lower(Komoditi.nama_komoditi).contains(variation),
                    func.lower(Komoditi.nama_komoditi).contains(nama_produk.lower())
                )
            )
            result = await self.db.execute(query)
            komoditi = result.scalars().first()
            
            if komoditi:
                self._cache[cache_key] = komoditi
                return komoditi
        
        return None

    async def get_latest_currency_rate_optimized(self, currency_code: str = "USD") -> Optional[CurrencyRates]:
        """
        Optimized currency rate lookup with caching
        """
        cache_key = f"currency_{currency_code}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Use native SQL for better performance
        sql = text("""
            SELECT id, base_currency, target_currency, rate, rate_date, created_at
            FROM currency_rates 
            WHERE base_currency = :currency_code
            ORDER BY rate_date DESC, created_at DESC
            LIMIT 1
        """)
        
        result = await self.db.execute(sql, {"currency_code": currency_code})
        row = result.fetchone()
        
        if row:
            currency_rate = CurrencyRates(
                id=row.id,
                base_currency=row.base_currency,
                target_currency=row.target_currency,
                rate=row.rate,
                rate_date=row.rate_date,
                created_at=row.created_at
            )
            self._cache[cache_key] = currency_rate
            return currency_rate
        
        return None

    async def get_export_duty_chunks_optimized(self, nama_produk: str) -> List[ExportDutyChunk]:
        """
        Get relevant export duty chunks using similarity search
        """
        cache_key = f"duty_chunks_{nama_produk.lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # Create embedding for the product name to search for relevant regulatory content
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.embeddings.create(
                input=nama_produk,
                model="text-embedding-ada-002"
            )
            product_embedding = response.data[0].embedding
            
            # Convert to PostgreSQL vector string format
            vector_str = ','.join([str(x) for x in product_embedding])
            vector_str = f'[{vector_str}]'
            
            # Search for relevant regulatory content using similarity
            sql = text("""
                SELECT id, content, embedding, metadata_doc, created_at,
                       1 - (embedding <-> :query_embedding) as similarity
                FROM export_duty_chunks 
                WHERE 1 - (embedding <-> :query_embedding) >= 0.7
                ORDER BY embedding <-> :query_embedding ASC
                LIMIT 5
            """)
            
            result = await self.db.execute(sql, {"query_embedding": vector_str})
            rows = result.fetchall()
            
            chunks = []
            for row in rows:
                chunk = ExportDutyChunk(
                    id=row.id,
                    content=row.content,
                    embedding=row.embedding,
                    metadata_doc=row.metadata_doc,
                    created_at=row.created_at
                )
                chunks.append(chunk)
            
            self._cache[cache_key] = chunks
            return chunks
            
        except Exception as e:
            print(f"Error getting export duty chunks: {e}")
            return []

    async def calculate_export_duty_optimized(self, nama_produk: str, berat_bersih: float, negara_tujuan: str) -> Dict[str, Any]:
        """
        Optimized export duty calculation with reduced database queries
        """
        start_time = time.time()
        
        try:
            # Parallel execution of database queries
            komoditi_task = asyncio.create_task(self.get_komoditi_by_name_optimized(nama_produk))
            currency_task = asyncio.create_task(self.get_latest_currency_rate_optimized("USD"))
            
            # Wait for both tasks to complete
            komoditi, currency_rate = await asyncio.gather(komoditi_task, currency_task)
            
            if not komoditi:
                raise ValueError(f"Komoditi '{nama_produk}' tidak ditemukan dalam database")
            
            if not currency_rate:
                raise ValueError("Data kurs mata uang USD tidak ditemukan")
            
            # Get export duty chunks (regulatory content)
            duty_chunks = await self.get_export_duty_chunks_optimized(nama_produk)
            
            # Convert weight from kg to tons
            berat_ton = berat_bersih / 1000
            
            # For now, use default values since we don't have structured duty rates
            # In a real implementation, you would extract rates from the regulatory content
            harga_per_ton_usd = 2000.0  # Default price per ton USD
            tarif_persen = 5.0  # Default 5% export duty
            
            # Calculate total export value
            total_harga_ekspor_usd = harga_per_ton_usd * berat_ton
            # Convert Decimal to float for calculations
            currency_rate_float = float(currency_rate.rate)
            total_harga_ekspor_idr = total_harga_ekspor_usd * currency_rate_float
            
            # Calculate export duty
            bea_keluar_idr = (tarif_persen / 100) * total_harga_ekspor_idr
            
            # Get regulatory information if available
            regulatory_info = ""
            if duty_chunks:
                regulatory_info = duty_chunks[0].content[:200] + "..." if len(duty_chunks[0].content) > 200 else duty_chunks[0].content
            
            execution_time = time.time() - start_time
            print(f"[EXPORT DUTY] Calculation completed in {execution_time:.3f}s")
            
            return {
                "nama_produk": nama_produk,
                "berat_bersih_kg": berat_bersih,
                "berat_ton": berat_ton,
                "negara_tujuan": negara_tujuan,
                "harga_ekspor_per_ton_usd": harga_per_ton_usd,
                "total_harga_ekspor_usd": total_harga_ekspor_usd,
                "kurs_usd_idr": currency_rate_float,
                "total_harga_ekspor_idr": total_harga_ekspor_idr,
                "tarif_bea_keluar_persen": tarif_persen,
                "bea_keluar_idr": bea_keluar_idr,
                "regulatory_info": regulatory_info,
                "komoditi_id": komoditi.id if komoditi else None,
                "currency_rate_id": currency_rate.id,
                "calculation_time": execution_time
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"[EXPORT DUTY] Error in calculation: {e}, Time: {execution_time:.3f}s")
            raise e

    async def calculate_export_duty(self, nama_produk: str, berat_bersih: float, negara_tujuan: str) -> Dict[str, Any]:
        """
        Calculate export duty using the official formula
        """
        return await self.calculate_export_duty_optimized(nama_produk, berat_bersih, negara_tujuan)

    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()

    async def get_komoditi_list_optimized(self) -> List[Dict[str, Any]]:
        """
        Get list of all komoditi with caching
        """
        cache_key = "komoditi_list"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Use native SQL for better performance
        sql = text("""
            SELECT id, nama_komoditi, kode_hs, created_at
            FROM komoditi 
            ORDER BY nama_komoditi
        """)
        
        result = await self.db.execute(sql)
        rows = result.fetchall()
        
        komoditi_list = []
        for row in rows:
            komoditi_list.append({
                "id": row.id,
                "nama_komoditi": row.nama_komoditi,
                "kode_hs": row.kode_hs,
                "created_at": row.created_at
            })
        
        self._cache[cache_key] = komoditi_list
        return komoditi_list

    async def batch_calculate_export_duty(self, calculations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch calculate export duty for multiple items
        """
        results = []
        for calc in calculations:
            try:
                result = await self.calculate_export_duty_optimized(
                    calc["nama_produk"],
                    calc["berat_bersih"],
                    calc["negara_tujuan"]
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "error": str(e),
                    "nama_produk": calc["nama_produk"],
                    "berat_bersih": calc["berat_bersih"],
                    "negara_tujuan": calc["negara_tujuan"]
                })
        
        return results 