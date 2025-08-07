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
            # Use AI to generate error response instead of hardcoded
            error_response = await self._generate_ai_error_response(query, str(e))
            return {
                "answer": error_response,
                "success": False,
                "executionTime": execution_time,
                "error": str(e)
            }
    
    def _quick_intent_detection(self, query: str) -> str:
        """
        Fast intent detection without AI calls
        """
        query_lower = query.lower()
        
        # Check for general document requests first (no specific country mentioned)
        general_document_patterns = [
            "saya ingin membuat dokumen", "saya ingin buat dokumen",
            "saya mau membuat dokumen", "saya mau buat dokumen",
            "ingin membuat dokumen", "ingin buat dokumen",
            "mau membuat dokumen", "mau buat dokumen",
            "tolong buat dokumen", "bisa buat dokumen",
            "mohon buat dokumen", "minta buat dokumen"
        ]
        
        if any(pattern in query_lower for pattern in general_document_patterns):
            return "document_list"  # Treat as list request to get general info
        
        # Document template keywords (specific requests)
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
        Optimized document query handling with prompt library
        """
        try:
            document_result = await self.document_service.get_export_documents_response(
                query, 
                show_template=(intent == "document_template")
            )
            
            # Get prompt template for more natural responses
            query_embedding = await self._create_embedding_optimized(query)
            prompt, similarity = await self._get_prompt_optimized(query_embedding)
            
            execution_time = time.time() - start_time
            
            if intent == "document_template":
                # Handle general document requests (no specific country)
                if document_result["success"] and document_result.get("country") is None:
                    # Use prompt library for more natural response
                    cot_response = await self.cot_service.generate_response_with_cot(
                        user_query=query,
                        analysis={"intent": "document_list", "extracted_data": document_result},
                        prompt_template=prompt.prompt_template
                    )
                    
                    return {
                        "answer": cot_response["answer"],
                        "htmlTemplate": "",
                        "similarity": similarity,
                        "promptId": prompt.id,
                        "success": True,
                        "executionTime": execution_time,
                        "cotAnalysis": {"intent": "document_list", "extracted_data": document_result},
                        "cotUsed": cot_response["cot_used"],
                        "optimized": True
                    }
                
                # Handle specific document template requests
                templates = []
                if document_result["success"] and document_result.get("documents_with_templates"):
                    for doc in document_result["documents_with_templates"]:
                        if doc.get("template") and doc["template"].get("template_dokumen"):
                            templates.append({
                                "name": doc["document_name"],
                                "htmlTemplate": doc["template"]["template_dokumen"]
                            })
                
                if len(templates) == 1:
                    # Use AI to generate natural response for single template
                    template_response = await self._generate_template_response(query, templates[0], prompt)
                    return {
                        "answer": template_response,
                        "htmlTemplate": templates[0]["htmlTemplate"],
                        "documentTemplate": True,
                        "templateName": templates[0]['name'],
                        "similarity": similarity,
                        "promptId": prompt.id,
                        "success": True,
                        "executionTime": execution_time,
                        "optimized": True
                    }
                elif len(templates) > 1:
                    # Use AI to generate natural response for multiple templates
                    multiple_response = await self._generate_multiple_templates_response(query, templates, prompt)
                    return {
                        "answer": multiple_response,
                        "htmlTemplate": "",
                        "similarity": similarity,
                        "promptId": prompt.id,
                        "success": False,
                        "executionTime": execution_time,
                        "optimized": True
                    }
                else:
                    # Use AI to generate natural response for no templates
                    no_template_response = await self._generate_no_template_response(query, document_result, prompt)
                    return {
                        "answer": no_template_response,
                        "htmlTemplate": "",
                        "similarity": similarity,
                        "promptId": prompt.id,
                        "success": False,
                        "executionTime": execution_time,
                        "optimized": True
                    }
            else:  # document_list
                # Use prompt library for more natural document list response
                cot_response = await self.cot_service.generate_response_with_cot(
                    user_query=query,
                    analysis={"intent": "document_list", "extracted_data": document_result},
                    prompt_template=prompt.prompt_template
                )
                
                return {
                    "answer": cot_response["answer"],
                    "similarity": similarity,
                    "promptId": prompt.id,
                    "success": document_result["success"],
                    "executionTime": execution_time,
                    "cotAnalysis": {"intent": "document_list", "extracted_data": document_result},
                    "cotUsed": cot_response["cot_used"],
                    "optimized": True
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_response = await self._generate_ai_error_response(query, str(e))
            return {
                "answer": error_response,
                "success": False,
                "executionTime": execution_time,
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
                
                # Use AI to generate natural response for calculation results
                calculation_response = await self._generate_calculation_response(query, hasil, prompt)
                
                execution_time = time.time() - start_time
                return {
                    "answer": calculation_response,
                    "similarity": similarity,
                    "promptId": prompt.id,
                    "extractedData": extracted_data,
                    "calculationDetails": hasil,
                    "executionTime": execution_time,
                    "cotAnalysis": cot_analysis,
                    "cotUsed": True,
                    "optimized": True
                }
            else:
                # Missing data - use AI to generate natural response
                missing_response = await self._generate_missing_data_response(query, extracted_data, prompt)
                execution_time = time.time() - start_time
                return {
                    "answer": missing_response,
                    "similarity": similarity,
                    "promptId": prompt.id,
                    "extractedData": extracted_data,
                    "executionTime": execution_time,
                    "cotAnalysis": cot_analysis,
                    "cotUsed": True,
                    "optimized": True
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_response = await self._generate_ai_error_response(query, str(e))
            return {
                "answer": error_response,
                "success": False,
                "executionTime": execution_time,
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
                "promptId": prompt.id,
                "executionTime": execution_time,
                "cotAnalysis": cot_analysis,
                "cotUsed": cot_response["cot_used"],
                "optimized": True
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_response = await self._generate_ai_error_response(query, str(e))
            return {
                "answer": error_response,
                "success": False,
                "executionTime": execution_time,
                "optimized": True
            }
    
    async def _generate_template_response(self, query: str, template: Dict, prompt: PromptLibrary) -> str:
        """Generate natural response for single template"""
        try:
            cot_response = await self.cot_service.generate_response_with_cot(
                user_query=query,
                analysis={
                    "intent": "document_template",
                    "template_name": template["name"],
                    "has_template": True
                },
                prompt_template=prompt.prompt_template
            )
            return cot_response["answer"]
        except Exception as e:
            logger.error(f"Error generating template response: {e}")
            return f"Hai! 👋 Berikut adalah template dokumen {template['name']} untuk ekspor. Silakan lengkapi bagian yang kosong ya!"
    
    async def _generate_multiple_templates_response(self, query: str, templates: List[Dict], prompt: PromptLibrary) -> str:
        """Generate natural response for multiple templates"""
        try:
            template_names = [t["name"] for t in templates]
            cot_response = await self.cot_service.generate_response_with_cot(
                user_query=query,
                analysis={
                    "intent": "document_template",
                    "available_templates": template_names,
                    "template_count": len(templates)
                },
                prompt_template=prompt.prompt_template
            )
            return cot_response["answer"]
        except Exception as e:
            logger.error(f"Error generating multiple templates response: {e}")
            return "Hmm, sebaiknya kita fokus ke satu dokumen dulu ya! 😊 Silakan pilih dokumen mana yang ingin dibuat terlebih dahulu."
    
    async def _generate_no_template_response(self, query: str, document_result: Dict, prompt: PromptLibrary) -> str:
        """Generate natural response for no templates available"""
        try:
            cot_response = await self.cot_service.generate_response_with_cot(
                user_query=query,
                analysis={
                    "intent": "document_template",
                    "has_template": False,
                    "document_result": document_result
                },
                prompt_template=prompt.prompt_template
            )
            return cot_response["answer"]
        except Exception as e:
            logger.error(f"Error generating no template response: {e}")
            return "Maaf, template dokumen yang Anda minta tidak tersedia atau belum ada data untuk negara tersebut."
    
    async def _generate_calculation_response(self, query: str, hasil: Dict, prompt: PromptLibrary) -> str:
        """Generate natural response for calculation results"""
        try:
            cot_response = await self.cot_service.generate_response_with_cot(
                user_query=query,
                analysis={
                    "intent": "export_duty",
                    "calculation_result": hasil,
                    "has_all_data": True
                },
                prompt_template=prompt.prompt_template
            )
            return cot_response["answer"]
        except Exception as e:
            logger.error(f"Error generating calculation response: {e}")
            return f"""
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
    
    async def _generate_missing_data_response(self, query: str, extracted_data: Dict, prompt: PromptLibrary) -> str:
        """Generate natural response for missing data"""
        try:
            missing_fields = []
            if not extracted_data["nama_produk"]:
                missing_fields.append("nama_produk")
            if not extracted_data["berat_bersih_kg"]:
                missing_fields.append("berat_bersih (kg)")
            if not extracted_data["negara_tujuan"]:
                missing_fields.append("negara_tujuan")
            
            cot_response = await self.cot_service.generate_response_with_cot(
                user_query=query,
                analysis={
                    "intent": "export_duty",
                    "missing_fields": missing_fields,
                    "extracted_data": extracted_data
                },
                prompt_template=prompt.prompt_template
            )
            return cot_response["answer"]
        except Exception as e:
            logger.error(f"Error generating missing data response: {e}")
            missing_fields = []
            if not extracted_data["nama_produk"]:
                missing_fields.append("nama_produk")
            if not extracted_data["berat_bersih_kg"]:
                missing_fields.append("berat_bersih (kg)")
            if not extracted_data["negara_tujuan"]:
                missing_fields.append("negara_tujuan")
            missing_text = ", ".join(missing_fields)
            return f"Mohon lengkapi data berikut: {missing_text}."
    
    async def _generate_ai_error_response(self, query: str, error_message: str) -> str:
        """Generate natural error response using AI"""
        try:
            cot_response = await self.cot_service.generate_response_with_cot(
                user_query=query,
                analysis={
                    "intent": "error",
                    "error_message": error_message
                },
                prompt_template="Kamu adalah ExportIn, asisten AI ekspor Indonesia yang ramah dan interaktif! 😊 Jika terjadi kesalahan, berikan respons yang simpatik dan menenangkan kepada pengguna."
            )
            return cot_response["answer"]
        except Exception as e:
            logger.error(f"Error generating AI error response: {e}")
            return "Maaf, terjadi kesalahan dalam memproses pertanyaan Anda. Silakan coba lagi."
    
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
                    prompt_template="Kamu adalah ExportIn, asisten AI ekspor Indonesia yang ramah dan interaktif! 😊",
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