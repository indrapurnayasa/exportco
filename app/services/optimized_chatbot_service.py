import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.chain_of_thought_service import ChainOfThoughtService
from app.services.prompt_library_service import PromptLibraryService
from app.services.export_document_service import ExportDocumentService
from app.services.export_duty_service import ExportDutyService
from app.models.prompt_library import PromptLibrary
import openai
import os

logger = logging.getLogger(__name__)

class OptimizedChatbotService:
    """
    Optimized chatbot service that reduces delays through:
    - Parallel processing
    - Intelligent caching
    - Optimized flows
    - Early returns
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cot_service = ChainOfThoughtService()
        self.prompt_service = PromptLibraryService(db)
        self.document_service = ExportDocumentService(db)
        self.duty_service = ExportDutyService(db)
        
        # Cache for frequently used data
        self._default_prompt_cache = None
        self._embedding_cache = {}
        self._prompt_cache = {}
    
    async def process_chatbot_query(self, query: str) -> Dict:
        """
        Optimized chatbot processing with minimal delay
        """
        start_time = time.time()
        
        try:
            # Step 1: Quick intent detection (parallel with CoT analysis)
            quick_intent = self._quick_intent_detection(query)
            
            # Step 2: Parallel processing for different paths
            if quick_intent in ["document_template", "document_list"]:
                return await self._handle_document_query(query, quick_intent, start_time)
            
            # Step 3: Parallel CoT analysis and embedding creation
            cot_task = asyncio.create_task(self.cot_service.analyze_query_with_cot(query))
            embedding_task = asyncio.create_task(self._create_embedding_optimized(query))
            
            # Wait for both tasks to complete
            cot_analysis, query_embedding = await asyncio.gather(cot_task, embedding_task)
            
            # Step 4: Quick return for export duty with parallel data extraction
            if cot_analysis['intent'] == "export_duty":
                return await self._handle_export_duty_optimized(query, cot_analysis, query_embedding, start_time)
            
            # Step 5: Optimized general response generation
            return await self._handle_general_response_optimized(query, cot_analysis, query_embedding, start_time)
            
        except Exception as e:
            logger.error(f"[OPTIMIZED] Error in chatbot processing: {e}")
            execution_time = time.time() - start_time
            return {
                "answer": "Maaf, terjadi kesalahan dalam memproses pertanyaan Anda. Silakan coba lagi.",
                "success": False,
                "execution_time": execution_time,
                "error": str(e)
            }
    
    def _quick_intent_detection(self, query: str) -> str:
        """
        Fast intent detection without AI calls
        """
        query_lower = query.lower()
        
        # Document template keywords
        template_keywords = ["buatkan", "buat", "generate", "tampilkan", "show", "lihat", "preview", "template"]
        if any(keyword in query_lower for keyword in template_keywords):
            return "document_template"
        
        # Document list keywords
        list_keywords = ["dokumen", "document", "surat", "form", "persyaratan", "apa saja", "daftar"]
        if any(keyword in query_lower for keyword in list_keywords):
            return "document_list"
        
        # Export duty keywords
        duty_keywords = ["bea", "pajak", "tarif", "hitung", "perhitungan", "biaya", "cukai"]
        if any(keyword in query_lower for keyword in duty_keywords):
            return "export_duty"
        
        return "general_info"
    
    async def _handle_document_query(self, query: str, intent: str, start_time: float) -> Dict:
        """
        Optimized document query handling
        """
        try:
            document_result = await self.document_service.get_export_documents_response(
                query, 
                show_template=(intent == "document_template")
            )
            
            execution_time = time.time() - start_time
            
            if intent == "document_template":
                templates = []
                if document_result["success"] and document_result["documents_with_templates"]:
                    for doc in document_result["documents_with_templates"]:
                        if doc.get("template") and doc["template"].get("template_dokumen"):
                            templates.append({
                                "name": doc["document_name"],
                                "html_template": doc["template"]["template_dokumen"]
                            })
                
                if len(templates) == 1:
                    return {
                        "answer": f"Berikut adalah template dokumen {templates[0]['name']} untuk ekspor. Silakan lengkapi bagian yang kosong.",
                        "html_template": templates[0]["html_template"],
                        "success": True,
                        "execution_time": execution_time,
                        "optimized": True
                    }
                elif len(templates) > 1:
                    return {
                        "answer": "Mohon minta satu dokumen saja dalam satu waktu. Silakan sebutkan dokumen yang ingin dibuat.",
                        "html_template": "",
                        "success": False,
                        "execution_time": execution_time,
                        "optimized": True
                    }
                else:
                    return {
                        "answer": "Maaf, template dokumen yang Anda minta tidak tersedia atau belum ada data untuk negara tersebut.",
                        "html_template": "",
                        "success": False,
                        "execution_time": execution_time,
                        "optimized": True
                    }
            else:  # document_list
                return {
                    "answer": document_result["message"],
                    "success": document_result["success"],
                    "execution_time": execution_time,
                    "optimized": True
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "answer": f"Terjadi kesalahan dalam memproses dokumen: {str(e)}",
                "success": False,
                "execution_time": execution_time,
                "optimized": True
            }
    
    async def _handle_export_duty_optimized(self, query: str, cot_analysis: Dict, query_embedding: List[float], start_time: float) -> Dict:
        """
        Optimized export duty handling with parallel processing
        """
        try:
            # Parallel tasks: prompt selection and data extraction
            prompt_task = asyncio.create_task(self._get_prompt_optimized(query_embedding))
            extraction_task = asyncio.create_task(self._extract_data_optimized(query))
            
            # Wait for both tasks
            prompt_result, extracted_data = await asyncio.gather(prompt_task, extraction_task)
            prompt, similarity = prompt_result
            
            # Check if we have all required data
            if extracted_data["nama_produk"] and extracted_data["berat_bersih_kg"] and extracted_data["negara_tujuan"]:
                # Calculate export duty
                hasil = await self.duty_service.calculate_export_duty(
                    nama_produk=extracted_data["nama_produk"],
                    berat_bersih=extracted_data["berat_bersih_kg"],
                    negara_tujuan=extracted_data["negara_tujuan"]
                )
                
                response_text = f"""
📊 **HASIL PERHITUNGAN BEA KELUAR EKSPOR**

**Detail Ekspor:**
• Nama Produk: {hasil['nama_produk']}
• Berat: {hasil['berat_bersih_kg']} kg ({hasil['berat_ton']:.3f} ton)
• Negara Tujuan: {hasil['negara_tujuan']}

**Perhitungan Harga:**
• Harga Ekspor: USD {hasil['harga_ekspor_per_ton_usd']:,.2f}/ton
• Total Harga Ekspor: USD {hasil['total_harga_ekspor_usd']:,.2f}
• Kurs USD/IDR: Rp {hasil['kurs_usd_idr']:,.2f}
• Total Harga dalam Rupiah: Rp {hasil['total_harga_ekspor_idr']:,.2f}

**Perhitungan Bea Keluar:**
• Tarif Bea Keluar: {hasil['tarif_bea_keluar_persen']:.1f}%
• **BEA KELUAR: Rp {hasil['bea_keluar_idr']:,.2f}**

**Rumus:** Bea Keluar = Tarif × Harga Ekspor × Jumlah Barang × Nilai Tukar
"""
                
                execution_time = time.time() - start_time
                return {
                    "answer": response_text,
                    "similarity": similarity,
                    "prompt_id": prompt.id,
                    "extracted_data": extracted_data,
                    "calculation_details": hasil,
                    "execution_time": execution_time,
                    "cot_analysis": cot_analysis,
                    "cot_used": True,
                    "optimized": True
                }
            else:
                # Missing data - return quickly
                missing_fields = []
                if not extracted_data["nama_produk"]:
                    missing_fields.append("nama_produk")
                if not extracted_data["berat_bersih_kg"]:
                    missing_fields.append("berat_bersih (kg)")
                if not extracted_data["negara_tujuan"]:
                    missing_fields.append("negara_tujuan")
                
                missing_text = ", ".join(missing_fields)
                execution_time = time.time() - start_time
                return {
                    "answer": f"Mohon lengkapi data berikut: {missing_text}.",
                    "similarity": similarity,
                    "prompt_id": prompt.id,
                    "extracted_data": extracted_data,
                    "execution_time": execution_time,
                    "cot_analysis": cot_analysis,
                    "cot_used": True,
                    "optimized": True
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "answer": f"Terjadi kesalahan dalam perhitungan: {str(e)}",
                "success": False,
                "execution_time": execution_time,
                "optimized": True
            }
    
    async def _handle_general_response_optimized(self, query: str, cot_analysis: Dict, query_embedding: List[float], start_time: float) -> Dict:
        """
        Optimized general response generation
        """
        try:
            # Get prompt template
            prompt, similarity = await self._get_prompt_optimized(query_embedding)
            
            # Generate response with CoT
            cot_response = await self.cot_service.generate_response_with_cot(
                user_query=query,
                analysis=cot_analysis,
                prompt_template=prompt.prompt_template
            )
            
            execution_time = time.time() - start_time
            return {
                "answer": cot_response["answer"],
                "similarity": similarity,
                "prompt_id": prompt.id,
                "execution_time": execution_time,
                "cot_analysis": cot_analysis,
                "cot_used": cot_response["cot_used"],
                "optimized": True
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "answer": f"Terjadi kesalahan dalam memproses pertanyaan: {str(e)}",
                "success": False,
                "execution_time": execution_time,
                "optimized": True
            }
    
    async def _create_embedding_optimized(self, text: str) -> List[float]:
        """
        Optimized embedding creation with caching
        """
        cache_key = hash(text)
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = await asyncio.to_thread(
                client.embeddings.create,
                input=text,
                model="text-embedding-ada-002"
            )
            embedding = response.data[0].embedding
            self._embedding_cache[cache_key] = embedding
            return embedding
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            return []
    
    async def _get_prompt_optimized(self, query_embedding: List[float]) -> Tuple[PromptLibrary, float]:
        """
        Optimized prompt selection with caching
        """
        cache_key = hash(tuple(query_embedding))
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        result = await self.prompt_service.get_most_similar_prompt(query_embedding, threshold=0.7)
        if not result:
            # Use cached default prompt
            if self._default_prompt_cache is None:
                self._default_prompt_cache = PromptLibrary(
                    id=0,
                    prompt_template="Kamu adalah ExportMate, asisten AI ekspor Indonesia yang membantu pengguna dengan pertanyaan seputar ekspor.",
                    is_active=True
                )
            prompt = self._default_prompt_cache
            similarity = 0.0
        else:
            prompt, similarity = result
        
        self._prompt_cache[cache_key] = (prompt, similarity)
        return prompt, similarity
    
    async def _extract_data_optimized(self, query: str) -> Dict:
        """
        Optimized data extraction
        """
        try:
            # Simple keyword-based extraction for speed
            data = {
                "nama_produk": None,
                "berat_bersih_kg": None,
                "negara_tujuan": None
            }
            
            # Extract weight
            import re
            weight_pattern = r'(\d+(?:\.\d+)?)\s*(?:kg|kilogram)'
            weight_match = re.search(weight_pattern, query, re.IGNORECASE)
            if weight_match:
                data["berat_bersih_kg"] = float(weight_match.group(1))
            
            # Extract country
            countries = ["Indonesia", "India", "Tiongkok", "China", "Bangladesh", "Malaysia", "Singapura", "Thailand", "Vietnam", "Filipina", "Jepang", "Korea", "Amerika", "USA", "Eropa", "Australia"]
            for country in countries:
                if country.lower() in query.lower():
                    data["negara_tujuan"] = country
                    break
            
            # Extract product
            commodities = ["CPO", "Crude Palm Oil", "Karet", "Kopi", "Kakao", "Cokelat", "Teh", "Beras", "Jagung", "Kedelai", "Gula", "Tembakau", "Kayu", "Batu Bara", "Minyak", "Gas"]
            for commodity in commodities:
                if commodity.lower() in query.lower():
                    data["nama_produk"] = commodity
                    break
            
            return data
            
        except Exception as e:
            logger.error(f"Error in data extraction: {e}")
            return {
                "nama_produk": None,
                "berat_bersih_kg": None,
                "negara_tujuan": None
            } 