from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from typing import Dict, Any, Optional, List
from app.models.komoditi import Komoditi
from app.models.currency_rates import CurrencyRates
from app.models.export_duty_chunks import ExportDutyChunk
import numpy as np
import asyncio
import time
import logging
import os

class ExportDutyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache = {}
        self._logger = logging.getLogger(__name__)

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

    async def get_export_duty_chunks_optimized(self, nama_produk: str, country: Optional[str] = None) -> List[ExportDutyChunk]:
        """
        Get relevant export duty chunks using similarity search
        """
        cache_key = f"duty_chunks_{nama_produk.lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # Create embedding for the product name (and country if available) to search for relevant regulatory content
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # Enrich query with synonyms and tier keywords
            np_lower = (nama_produk or "").lower()
            syn = []
            if "kakao" in np_lower or "cocoa" in np_lower:
                syn.extend(["kakao", "cocoa"])
            if "kopi" in np_lower or "coffee" in np_lower:
                syn.extend(["kopi", "coffee"])
            if "karet" in np_lower or "rubber" in np_lower:
                syn.extend(["karet", "rubber"])
            syn_part = " ".join(sorted(set(syn)))
            query_text = (
                f"{nama_produk} {syn_part} {country or ''} tarif bea keluar BK pungutan ekspor export duty aturan regulasi "
                f"HPE threshold ambang bracket persentase levy per kg"
            )
            response = client.embeddings.create(
                input=query_text.strip(),
                model="text-embedding-3-small"
            )
            product_embedding = response.data[0].embedding
            
            # Convert to PostgreSQL vector string format
            vector_str = ','.join([str(x) for x in product_embedding])
            vector_str = f'[{vector_str}]'
            
            # Search for relevant regulatory content using similarity
            sql = text("""
                SELECT id, content, embedding, created_at,
                       1 - (embedding <-> :query_embedding) as similarity
                FROM export_duty_chunks 
                WHERE 1 - (embedding <-> :query_embedding) >= 0.35
                ORDER BY embedding <-> :query_embedding ASC
                LIMIT 8
            """)
            
            result = await self.db.execute(sql, {"query_embedding": vector_str})
            rows = result.fetchall()
            
            chunks = []
            for row in rows:
                chunk = ExportDutyChunk(
                    id=row.id,
                    content=row.content,
                    embedding=row.embedding,
                    created_at=row.created_at
                )
                chunks.append(chunk)
                # Log each selected chunk (id, similarity, preview)
                try:
                    preview = (row.content or "")[:120].replace("\n", " ")
                    sim = None
                    try:
                        sim = float(row.similarity)
                    except Exception:
                        sim = None
                    if sim is not None:
                        self._logger.info(f"[RAG export_duty_chunks] id={row.id} sim={sim:.3f} preview={preview}")
                    else:
                        self._logger.info(f"[RAG export_duty_chunks] id={row.id} preview={preview}")
                except Exception:
                    pass
            
            self._cache[cache_key] = chunks
            return chunks
            
        except Exception as e:
            print(f"Error getting export duty chunks: {e}")
            return []

    def _extract_tariff_and_price_from_chunks(self, chunks: List[ExportDutyChunk], default_product: str) -> tuple[Optional[float], Optional[float]]:
        """
        Heuristically extract tariff percent and price (USD per kg) from regulatory chunks.
        Returns (tarif_persen, harga_per_kg_usd) or (None, None) if not found.
        """
        import re
        if not chunks:
            return None, None

        tarif: Optional[float] = None
        price_per_kg: Optional[float] = None

        # Prefer percentages near terms like "tarif"/"bea keluar"/"BK"/"pungutan ekspor"
        percent_re = re.compile(r"(?:tarif|bea\s+keluar|bk|pungutan\s+ekspor)[^\d%]{0,40}(\d+(?:[.,]\d+)?)\s*%", re.IGNORECASE)
        # General fallback percent anywhere
        percent_any_re = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
        # Examples: USD 2,000/ton, 2000 USD per ton, USD 2.5/kg
        price_patterns = [
            re.compile(r"USD\s*([\d,.]+)\s*/\s*(kg|kilogram)", re.IGNORECASE),
            re.compile(r"([\d,.]+)\s*USD\s*/\s*(kg|kilogram)", re.IGNORECASE),
            re.compile(r"USD\s*([\d,.]+)\s*/\s*(ton|tonne|mt|metric\s*ton)", re.IGNORECASE),
            re.compile(r"([\d,.]+)\s*USD\s*/\s*(ton|tonne|mt|metric\s*ton)", re.IGNORECASE),
        ]

        for chunk in chunks:
            text = chunk.content or ""
            # Tariff: try contextual first
            if tarif is None:
                m = percent_re.search(text)
                if m:
                    try:
                        tarif = float(m.group(1).replace(',', '.'))
                    except Exception:
                        pass
            if tarif is None:
                m_any = percent_any_re.search(text)
                if m_any:
                    try:
                        tarif = float(m_any.group(1).replace(',', '.'))
                    except Exception:
                        pass
            # Price
            if price_per_kg is None:
                for pat in price_patterns:
                    m2 = pat.search(text)
                    if m2:
                        try:
                            val = float(m2.group(1).replace(',', '').replace(' ', ''))
                            unit = m2.group(2).lower()
                            if unit in ("kg", "kilogram"):
                                price_per_kg = val
                            else:
                                # per ton -> per kg
                                price_per_kg = val / 1000.0
                            break
                        except Exception:
                            continue
            if tarif is not None and price_per_kg is not None:
                break

        return tarif, price_per_kg

    def _extract_specific_levy_from_chunks(self, chunks: List[ExportDutyChunk]) -> tuple[Optional[float], Optional[float]]:
        """
        Extract specific levy as per-kg in USD or IDR from chunks.
        Returns (usd_per_kg, idr_per_kg)
        """
        import re
        if not chunks:
            return None, None

        usd_per_kg: Optional[float] = None
        idr_per_kg: Optional[float] = None

        # Focus around BK/Bea Keluar/Pungutan Ekspor context
        ctx = r"(?:bea\s+keluar|bk|pungutan\s+ekspor|export\s+duty)[^\n]{0,80}"
        # USD per kg/ton
        patt_usd_kg = re.compile(ctx + r"USD\s*([\d,.]+)\s*/\s*(kg|kilogram)", re.IGNORECASE)
        patt_usd_ton = re.compile(ctx + r"USD\s*([\d,.]+)\s*/\s*(ton|tonne|mt|metric\s*ton)", re.IGNORECASE)
        # IDR per kg/ton
        patt_idr_kg = re.compile(ctx + r"Rp\s*([\d,.]+)\s*/\s*(kg|kilogram)", re.IGNORECASE)
        patt_idr_ton = re.compile(ctx + r"Rp\s*([\d,.]+)\s*/\s*(ton|tonne|mt|metric\s*ton)", re.IGNORECASE)

        for ch in chunks:
            t = ch.content or ""
            if usd_per_kg is None:
                m1 = patt_usd_kg.search(t)
                if m1:
                    try:
                        usd_per_kg = float(m1.group(1).replace(',', '').replace(' ', ''))
                    except Exception:
                        pass
            if usd_per_kg is None:
                m2 = patt_usd_ton.search(t)
                if m2:
                    try:
                        val = float(m2.group(1).replace(',', '').replace(' ', ''))
                        usd_per_kg = val / 1000.0
                    except Exception:
                        pass
            if idr_per_kg is None:
                m3 = patt_idr_kg.search(t)
                if m3:
                    try:
                        idr_per_kg = float(m3.group(1).replace('.', '').replace(',', ''))
                    except Exception:
                        pass
            if idr_per_kg is None:
                m4 = patt_idr_ton.search(t)
                if m4:
                    try:
                        val = float(m4.group(1).replace('.', '').replace(',', ''))
                        idr_per_kg = val / 1000.0
                    except Exception:
                        pass

            if usd_per_kg is not None or idr_per_kg is not None:
                break

        return usd_per_kg, idr_per_kg

    def _extract_tier_tariff_from_chunks(self, chunks: List[ExportDutyChunk], usd_per_ton: Optional[float]) -> Optional[float]:
        """Return percent tariff from tier rules if usd_per_ton exceeds threshold.
        Matches patterns like "> USD 2,000/ton ... 5%" or "di atas USD 2000/ton ... 5%".
        """
        import re
        if usd_per_ton is None or not chunks:
            return None
        patt = re.compile(
            r"(>=|>|di\s+atas|lebih\s+dari)\s*USD\s*([\d,.]+)\s*/\s*(ton|tonne|mt|metric\s*ton)[^%]{0,120}?(\d+(?:[.,]\d+)?)\s*%",
            re.IGNORECASE,
        )
        for ch in chunks:
            t = ch.content or ""
            for m in patt.finditer(t):
                try:
                    thr = float(m.group(2).replace(",", ""))
                    pct = float(m.group(4).replace(",", "."))
                    if usd_per_ton > thr:
                        return pct
                except Exception:
                    continue
        return None

    async def _llm_extract_tariff_from_chunks(self, chunks: List[ExportDutyChunk], nama_produk: str, country: Optional[str]) -> Optional[float]:
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # Concatenate top chunks (limit to keep prompt small)
            combined = "\n\n---\n\n".join((c.content or "")[:800] for c in chunks[:5])
            question = (
                f"Produk: {nama_produk}\n"
                f"Negara tujuan: {country or '-'}\n"
                "Dari referensi berikut, berapa tarif bea keluar (dalam persen, angka saja) yang paling relevan?"
            )
            prompt = (
                "Ekstrak satu angka persen tarif bea keluar yang paling relevan dari referensi di bawah ini. "
                "Jika tidak ada angka tarif yang jelas, jawab 'NA'.\n\nREFERENSI:\n" + combined + "\n\nPERTANYAAN:\n" + question
            )
            resp = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Kembalikan hanya angka persen tanpa simbol, atau NA."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=10,
            )
            text = (resp.choices[0].message.content or "").strip()
            if text.upper().startswith("NA"):
                return None
            # Extract first float-like number
            import re as _re
            m = _re.search(r"(\d+(?:[.,]\d+)?)", text)
            if m:
                return float(m.group(1).replace(',', '.'))
            return None
        except Exception:
            return None

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
            duty_chunks = await self.get_export_duty_chunks_optimized(nama_produk, negara_tujuan)
            
            # Convert weight from kg to tons
            berat_ton = berat_bersih / 1000
            
            # Try to extract tariff and price from RAG chunks; avoid hardcoded defaults
            rag_tarif_persen, rag_price_per_kg = self._extract_tariff_and_price_from_chunks(duty_chunks, nama_produk)
            if rag_tarif_persen is None and duty_chunks:
                # As a secondary, use LLM to extract a single tariff number from the top chunks
                rag_tarif_persen = await self._llm_extract_tariff_from_chunks(duty_chunks, nama_produk, negara_tujuan)

            # Fallback for price from Komoditi table if available (IDR/kg)
            price_per_kg = rag_price_per_kg  # USD/kg if present from RAG
            komoditi_price_idr_per_kg: Optional[float] = None
            if price_per_kg is None and komoditi and getattr(komoditi, "harga_komoditi", None) is not None:
                try:
                    unit = (getattr(komoditi, "satuan_komoditi", "") or "").lower()
                    price_val = float(komoditi.harga_komoditi)
                    if "kg" in unit:
                        # Keep USD price None; record IDR/kg
                        komoditi_price_idr_per_kg = price_val
                    elif any(u in unit for u in ["ton", "tonne", "mt", "metric ton"]):
                        komoditi_price_idr_per_kg = price_val / 1000.0
                except Exception:
                    price_per_kg = None
                    komoditi_price_idr_per_kg = None

            tarif_persen = rag_tarif_persen

            missing_fields: List[str] = []
            if tarif_persen is None:
                missing_fields.append("tarif_bea_keluar_persen")
            if price_per_kg is None and komoditi_price_idr_per_kg is None:
                missing_fields.append("harga_ekspor_per_kg")

            # If required data is missing, return structured response without hardcoded assumptions
            # If we still miss tariff percent, try specific per-unit levy
            usd_levy_per_kg, idr_levy_per_kg = (None, None)
            if tarif_persen is None:
                usd_levy_per_kg, idr_levy_per_kg = self._extract_specific_levy_from_chunks(duty_chunks)

            # If still no rule, infer based on total value tiers from chunks
            prelim_total_usd: Optional[float] = None
            prelim_total_idr: Optional[float] = None
            try:
                rate_float = float(currency_rate.rate)
            except Exception:
                rate_float = None

            if price_per_kg is not None:
                prelim_total_usd = price_per_kg * berat_bersih
                if rate_float:
                    prelim_total_idr = prelim_total_usd * rate_float
            elif komoditi_price_idr_per_kg is not None:
                prelim_total_idr = komoditi_price_idr_per_kg * berat_bersih
                if rate_float and rate_float > 0:
                    prelim_total_usd = prelim_total_idr / rate_float

            if (tarif_persen is None and usd_levy_per_kg is None and idr_levy_per_kg is None and duty_chunks and (prelim_total_usd is not None or prelim_total_idr is not None)):
                rule_percent, rule_usd_kg, rule_idr_kg = await self._llm_extract_tariff_from_chunks(duty_chunks, nama_produk, negara_tujuan), None, None
                # keep legacy percent extraction result already in tarif_persen; this block reserved if extended in future

            # Can compute via specific levy path
            if tarif_persen is None and (usd_levy_per_kg is not None or idr_levy_per_kg is not None):
                execution_time = time.time() - start_time
                currency_rate_float = float(currency_rate.rate)
                if usd_levy_per_kg is not None:
                    bea_keluar_idr = usd_levy_per_kg * berat_bersih * currency_rate_float
                    calc_note = "computed via specific levy (USD/kg) from RAG"
                else:
                    bea_keluar_idr = idr_levy_per_kg * berat_bersih
                    calc_note = "computed via specific levy (IDR/kg) from RAG"

                regulatory_info = ""
                if duty_chunks:
                    regulatory_info = duty_chunks[0].content[:200] + "..." if len(duty_chunks[0].content) > 200 else duty_chunks[0].content

                return {
                    "nama_produk": nama_produk,
                    "berat_bersih_kg": berat_bersih,
                    "berat_ton": berat_ton,
                    "negara_tujuan": negara_tujuan,
                    "country": negara_tujuan,
                    "harga_ekspor_per_kg_usd": price_per_kg,
                    "harga_komoditi": komoditi_price_idr_per_kg,
                    "satuan_komoditi": ("Rp/kg" if komoditi_price_idr_per_kg is not None else None),
                    "kurs_usd_idr": currency_rate_float,
                    "tarif_bea_keluar_persen": None,
                    "bea_keluar_idr": bea_keluar_idr,
                    "calc_basis": calc_note,
                    "regulatory_info": regulatory_info,
                    "komoditi_id": komoditi.id if komoditi else None,
                    "currency_rate_id": currency_rate.id,
                    "rag_source_count": len(duty_chunks) if duty_chunks else 0,
                    "can_compute": True,
                    "calculation_time": execution_time,
                }

            # If only tariff is missing but price exists, attempt tier rule then fallback
            if missing_fields == ["tarif_bea_keluar_persen"] and (price_per_kg is not None or komoditi_price_idr_per_kg is not None):
                execution_time = time.time() - start_time
                currency_rate_float = float(currency_rate.rate)
                if price_per_kg is not None:
                    # USD/kg path
                    harga_per_ton_usd = price_per_kg * 1000.0
                    total_harga_ekspor_usd = harga_per_ton_usd * berat_ton
                    total_harga_ekspor_idr = total_harga_ekspor_usd * currency_rate_float
                    # Try tier extraction
                    try:
                        tier_pct = self._extract_tier_tariff_from_chunks(duty_chunks, harga_per_ton_usd)
                        if tier_pct is not None:
                            tarif_persen = tier_pct
                    except Exception:
                        pass
                else:
                    # IDR/kg path from komoditi
                    harga_per_ton_usd = None
                    total_harga_ekspor_idr = (komoditi_price_idr_per_kg or 0.0) * berat_bersih
                    total_harga_ekspor_usd = total_harga_ekspor_idr / currency_rate_float if currency_rate_float else 0.0
                    # Try tier extraction after converting to USD/ton
                    try:
                        usd_per_ton = total_harga_ekspor_usd / berat_ton if berat_ton else None
                        tier_pct = self._extract_tier_tariff_from_chunks(duty_chunks, usd_per_ton)
                        if tier_pct is not None:
                            tarif_persen = tier_pct
                    except Exception:
                        pass
                bea_keluar_idr = 0.0
                if tarif_persen is not None:
                    bea_keluar_idr = (tarif_persen / 100.0) * total_harga_ekspor_idr
                regulatory_info = ""
                if duty_chunks:
                    regulatory_info = duty_chunks[0].content[:200] + "..." if len(duty_chunks[0].content) > 200 else duty_chunks[0].content
                return {
                    "nama_produk": nama_produk,
                    "berat_bersih_kg": berat_bersih,
                    "berat_ton": berat_ton,
                    "negara_tujuan": negara_tujuan,
                    "country": negara_tujuan,
                    "harga_ekspor_per_ton_usd": harga_per_ton_usd,
                    "harga_ekspor_per_kg_usd": price_per_kg,
                    "harga_komoditi": komoditi_price_idr_per_kg,
                    "satuan_komoditi": ("Rp/kg" if komoditi_price_idr_per_kg is not None else None),
                    "total_harga_ekspor_usd": total_harga_ekspor_usd,
                    "kurs_usd_idr": currency_rate_float,
                    "total_harga_ekspor_idr": total_harga_ekspor_idr,
                    "tarif_bea_keluar_persen": float(tarif_persen or 0.0),
                    "bea_keluar_idr": bea_keluar_idr,
                    "calc_basis": ("tier percent from RAG" if tarif_persen is not None else "assumed 0% (no tariff found)"),
                    "regulatory_info": regulatory_info,
                    "komoditi_id": komoditi.id if komoditi else None,
                    "currency_rate_id": currency_rate.id,
                    "rag_source_count": len(duty_chunks) if duty_chunks else 0,
                    "can_compute": True,
                    "calculation_time": execution_time,
                }

            if missing_fields:
                execution_time = time.time() - start_time
                regulatory_info = ""
                if duty_chunks:
                    regulatory_info = duty_chunks[0].content[:200] + "..." if len(duty_chunks[0].content) > 200 else duty_chunks[0].content
                return {
                    "nama_produk": nama_produk,
                    "berat_bersih_kg": berat_bersih,
                    "berat_ton": berat_ton,
                    "negara_tujuan": negara_tujuan,
                    "country": negara_tujuan,
                    "harga_ekspor_per_kg_usd": price_per_kg,
                    "kurs_usd_idr": float(currency_rate.rate),
                    "tarif_bea_keluar_persen": tarif_persen,
                    "regulatory_info": regulatory_info,
                    "komoditi_id": komoditi.id if komoditi else None,
                    "currency_rate_id": currency_rate.id,
                    "rag_source_count": len(duty_chunks) if duty_chunks else 0,
                    "can_compute": False,
                    "missing_fields": missing_fields,
                    "calculation_time": execution_time,
                }

            # Compute using available data (USD/kg vs IDR/kg path)
            currency_rate_float = float(currency_rate.rate)
            if price_per_kg is not None:
                harga_per_ton_usd = price_per_kg * 1000.0
                total_harga_ekspor_usd = harga_per_ton_usd * berat_ton
                total_harga_ekspor_idr = total_harga_ekspor_usd * currency_rate_float
            else:
                harga_per_ton_usd = None
                total_harga_ekspor_idr = (komoditi_price_idr_per_kg or 0.0) * berat_bersih
                total_harga_ekspor_usd = total_harga_ekspor_idr / currency_rate_float if currency_rate_float else 0.0
            
            # Calculate export duty (apply tier rule if present)
            try:
                usd_per_ton_final = harga_per_ton_usd if harga_per_ton_usd is not None else (total_harga_ekspor_usd / berat_ton if berat_ton else None)
                tier_pct2 = self._extract_tier_tariff_from_chunks(duty_chunks, usd_per_ton_final)
                eff_pct = tier_pct2 if (tier_pct2 is not None) else tarif_persen
            except Exception:
                eff_pct = tarif_persen
            bea_keluar_idr = (float(eff_pct or 0.0) / 100.0) * total_harga_ekspor_idr
            
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
                "country": negara_tujuan,
                "harga_ekspor_per_ton_usd": harga_per_ton_usd,
                "harga_ekspor_per_kg_usd": price_per_kg,
                "harga_komoditi": komoditi_price_idr_per_kg,
                "satuan_komoditi": ("Rp/kg" if komoditi_price_idr_per_kg is not None else None),
                "total_harga_ekspor_usd": total_harga_ekspor_usd,
                "kurs_usd_idr": currency_rate_float,
                "total_harga_ekspor_idr": total_harga_ekspor_idr,
                "tarif_bea_keluar_persen": tarif_persen,
                "bea_keluar_idr": bea_keluar_idr,
                "regulatory_info": regulatory_info,
                "komoditi_id": komoditi.id if komoditi else None,
                "currency_rate_id": currency_rate.id,
                "rag_source_count": len(duty_chunks) if duty_chunks else 0,
                "can_compute": True,
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