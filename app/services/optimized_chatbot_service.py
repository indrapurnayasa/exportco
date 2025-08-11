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
from app.utils.proposal_templates import EXPORT_PROPOSAL_HTML_TEMPLATE
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
    
    async def process_chatbot_query(self, query: str, suppress_intro: bool = False, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """
        Optimized chatbot processing with minimal delay
        """
        start_time = time.time()
        
        try:
            # Step 1: Quick intent detection (parallel with CoT analysis)
            quick_intent = self._quick_intent_detection(query)

            # Step 1b: Build minimal relevant context from history (topic-aware)
            selected_context = await self._select_relevant_history(query, conversation_history or [], max_turns=3, similarity_threshold=0.35)
            
            # Step 2: Parallel processing for different paths
            if quick_intent in ["document_template", "document_list"]:
                # Always suppress intros for document flows
                return await self._handle_document_query(query, quick_intent, start_time, suppress_intro=True)
            # Early path for export proposal template
            if quick_intent == "export_proposal":
                return await self._handle_export_proposal(query, start_time, suppress_intro=True, full_history=conversation_history or [])
            
            # Step 3: Parallel CoT analysis and embedding creation
            cot_context = "\n".join(selected_context) if selected_context else ""
            cot_task = asyncio.create_task(self.cot_service.analyze_query_with_cot(query, context=cot_context))
            embedding_task = asyncio.create_task(self._create_embedding_optimized(query))
            
            # Wait for both tasks to complete
            cot_analysis, query_embedding = await asyncio.gather(cot_task, embedding_task)
            
            # Step 4: Quick return for export duty with parallel data extraction
            if cot_analysis['intent'] == "export_duty":
                return await self._handle_export_duty_optimized(
                    query,
                    cot_analysis,
                    query_embedding,
                    start_time,
                    suppress_intro=suppress_intro,
                    context_snippets=selected_context,
                    full_history=conversation_history or []
                )
            
            # Step 5: Optimized general response generation
            return await self._handle_general_response_optimized(query, cot_analysis, query_embedding, start_time, suppress_intro=suppress_intro)
            
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
        
        # Prefer specific template requests first (highest precision)
        template_keywords = ["buatkan", "buat", "generate", "tampilkan", "show", "lihat", "preview", "template"]
        # Detect explicit document names to bias towards template
        doc_name_keywords = [
            "commercial invoice", "invoice", "packing list", "shipping instruction", "proforma invoice",
            "delivery order", "letter of credit", "lc", "si"
        ]
        if any(kw in query_lower for kw in template_keywords) and any(dn in query_lower for dn in doc_name_keywords):
            return "document_template"
        # If the pattern 'dokumen <name>' appears, treat as template
        import re
        if re.search(r"dokumen\s+(commercial\s+invoice|invoice|packing\s+list|proforma\s+invoice|shipping\s+instruction|delivery\s+order|letter\s+of\s+credit|lc)\b", query_lower):
            return "document_template"

        # Check for general document requests first (no specific country mentioned)
        general_document_patterns = [
            "saya ingin membuat dokumen", "saya ingin buat dokumen",
            "saya mau membuat dokumen", "saya mau buat dokumen",
            "ingin membuat dokumen", "ingin buat dokumen",
            "mau membuat dokumen", "mau buat dokumen",
            "tolong buat dokumen", "bisa buat dokumen",
            "mohon buat dokumen", "minta buat dokumen"
        ]
        # Only classify as list if we didn't already detect a template intent
        if any(pattern in query_lower for pattern in general_document_patterns):
            return "document_list"
        
        # Document list keywords
        list_keywords = ["dokumen", "document", "surat", "form", "persyaratan", "apa saja", "daftar"]
        if any(keyword in query_lower for keyword in list_keywords):
            return "document_list"
        
        # Export duty keywords
        duty_keywords = ["bea", "pajak", "tarif", "hitung", "perhitungan", "biaya", "cukai"]
        if any(keyword in query_lower for keyword in duty_keywords):
            return "export_duty"
        
        # Export proposal generation keywords
        proposal_keywords = [
            "proposal", "penawaran", "quotation", "quote", "buatkan proposal", "generate proposal",
            "proposal ekspor", "export proposal", "proposal export", "buat proposal"
        ]
        if any(keyword in query_lower for keyword in proposal_keywords):
            return "export_proposal"

        return "general_info"
    
    async def _handle_document_query(self, query: str, intent: str, start_time: float, suppress_intro: bool = False) -> Dict:
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
            prompt, similarity = await self._get_prompt_optimized(query_embedding, query_text=query)
            
            execution_time = time.time() - start_time
            
            if intent == "document_template":
                # Handle general document requests (no specific country)
                if document_result["success"] and document_result.get("country") is None:
                    # Use prompt library for more natural response
                    cot_response = await self.cot_service.generate_response_with_cot(
                        user_query=query,
                        analysis={"intent": "document_list", "extracted_data": document_result},
                        prompt_template=prompt.prompt_template,
                        suppress_intro=suppress_intro
                    )
                    
                    return {
                        "answer": cot_response["answer"],
                        "htmlTemplate": "",
                        "similarity": similarity,
                        "similarityPercentage": round(float(similarity) * 100.0, 1),
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
                    template_response = await self._generate_template_response(query, templates[0], prompt, suppress_intro=suppress_intro)
                    return {
                        "answer": template_response,
                        "htmlTemplate": templates[0]["htmlTemplate"],
                        "documentTemplate": True,
                        "templateName": templates[0]['name'],
                        "similarity": similarity,
                        "similarityPercentage": round(float(similarity) * 100.0, 1),
                        "promptId": prompt.id,
                        "success": True,
                        "executionTime": execution_time,
                        "optimized": True
                    }
                elif len(templates) > 1:
                    # Use AI to generate natural response for multiple templates
                    multiple_response = await self._generate_multiple_templates_response(query, templates, prompt, suppress_intro=suppress_intro)
                    return {
                        "answer": multiple_response,
                        "htmlTemplate": "",
                        "similarity": similarity,
                        "similarityPercentage": round(float(similarity) * 100.0, 1),
                        "promptId": prompt.id,
                        "success": False,
                        "executionTime": execution_time,
                        "optimized": True
                    }
                else:
                    # Use AI to generate natural response for no templates
                    no_template_response = await self._generate_no_template_response(query, document_result, prompt, suppress_intro=suppress_intro)
                    return {
                        "answer": no_template_response,
                        "htmlTemplate": "",
                        "similarity": similarity,
                        "similarityPercentage": round(float(similarity) * 100.0, 1),
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
                    prompt_template=prompt.prompt_template,
                    suppress_intro=suppress_intro
                )
                
                return {
                    "answer": cot_response["answer"],
                    "similarity": similarity,
                    "similarityPercentage": round(float(similarity) * 100.0, 1),
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

    async def _handle_export_proposal(self, query: str, start_time: float, suppress_intro: bool = True, full_history: Optional[List[Dict]] = None) -> Dict:
        """Multi-turn export proposal flow.

        1) Extract needed info from current message and prior history.
        2) If incomplete, ask for missing items (no htmlTemplate yet).
        3) If complete, return htmlTemplate and set generateProposal=True.

        Uses fixed promptId = 6.
        """
        try:
            # Extract proposal data from current query
            current = self._extract_proposal_data(query)
            merged = dict(current)

            # Enrich from history (scan last ~10 turns)
            if full_history:
                hist_text_parts: List[str] = []
                for turn in full_history[-10:]:
                    hist_text_parts.append(str(turn.get("user_query", "")))
                    hist_text_parts.append(str(turn.get("assistant_response", "")))
                augmented_text = "\n".join(hist_text_parts)
                historical = self._extract_proposal_data(augmented_text)
                for k, v in historical.items():
                    if not merged.get(k) and v:
                        merged[k] = v

            required_fields = [
                "exporter_name",
                "consignee_name",
                "destination_country",
                "contact_email",
                "contact_phone"
            ]
            missing = [f for f in required_fields if not merged.get(f)]

            if missing:
                # Ask user for the missing fields
                prompt_text = (
                    "Kamu adalah ExportIn. Minta data yang kurang untuk menyusun proposal ekspor: "
                    + ", ".join(missing) + ". Jawab singkat dan langsung ke poin."
                )
                cot_response = await self.cot_service.generate_response_with_cot(
                    user_query=query,
                    analysis={
                        "intent": "export_proposal",
                        "missing_fields": missing,
                        "collected": {k: v for k, v in merged.items() if v}
                    },
                    prompt_template=prompt_text,
                    suppress_intro=suppress_intro
                )
                execution_time = time.time() - start_time
                return {
                    "answer": self._sanitize_answer_text(cot_response.get("answer", "Saya butuh informasi tambahan untuk menyusun proposal.")),
                    "generateProposal": False,
                    "promptId": 6,
                    "proposalData": merged,
                    "missingFields": missing,
                    "success": True,
                    "executionTime": execution_time,
                    "optimized": True
                }

            # All required fields present → provide template
            # Also expose variables that the frontend can use to prefill placeholders
            variables = self._build_proposal_variables_from_data(merged)
            cot_response = await self.cot_service.generate_response_with_cot(
                user_query=query,
                analysis={
                    "intent": "export_proposal",
                    "requires_template": True,
                    "collected": variables
                },
                prompt_template=(
                    "Konfirmasi singkat bahwa proposal siap. Sarankan pengguna untuk meninjau ringkasan produk, keunggulan, harga & stok, dan CTA."
                ),
                suppress_intro=suppress_intro
            )

            execution_time = time.time() - start_time
            return {
                "answer": self._sanitize_answer_text(cot_response.get("answer", "Proposal siap ditampilkan.")),
                "htmlTemplate": EXPORT_PROPOSAL_HTML_TEMPLATE,
                "generateProposal": True,
                "promptId": 6,
                "proposalVariables": variables,
                "success": True,
                "executionTime": execution_time,
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

    def _extract_proposal_data(self, text: str) -> Dict[str, Optional[str]]:
        """Heuristic extraction of proposal fields from free text."""
        try:
            data: Dict[str, Optional[str]] = {
                "exporter_name": None,
                "consignee_name": None,
                "destination_country": None,
                "proposal_date": None,
                "contact_email": None,
                "contact_phone": None,
                "contact_website": None,
            }

            if not text:
                return data

            import re
            t = text

            # Names (simple patterns)
            m = re.search(r"(?:exporter|eksportir|pt|cv)\s*[:\-]?\s*([\w\s&.,'-]{3,})", t, re.IGNORECASE)
            if m:
                data["exporter_name"] = m.group(1).strip().strip(" -:,.\n")[:120]

            m = re.search(r"(?:consignee|pembeli|buyer)\s*[:\-]?\s*([\w\s&.,'-]{3,})", t, re.IGNORECASE)
            if m:
                data["consignee_name"] = m.group(1).strip().strip(" -:,.\n")[:120]

            # Country (simple list + generic pattern)
            countries = [
                "Indonesia","India","Tiongkok","China","Bangladesh","Malaysia","Singapura","Thailand","Vietnam",
                "Filipina","Jepang","Korea","Amerika","USA","Eropa","Australia","United Kingdom","UK",
                "United States","Germany","France","Italy","Spain","Netherlands","Saudi Arabia","UAE"
            ]
            for c in countries:
                if c.lower() in t.lower():
                    data["destination_country"] = c
                    break
            if not data["destination_country"]:
                m = re.search(r"negara\s+tujuan\s*[:\-]?\s*([A-Za-z\s]+)", t, re.IGNORECASE)
                if m:
                    data["destination_country"] = m.group(1).strip()[:80]

            # Date
            m = re.search(r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})", t)
            if m:
                data["proposal_date"] = m.group(1)

            # Contacts
            m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", t)
            if m:
                data["contact_email"] = m.group(0)

            m = re.search(r"(?:telp|telpon|telepon|phone|hp|wa|whatsapp)\s*[:\-]?\s*([+0-9()\s-]{6,20})", t, re.IGNORECASE)
            if m:
                data["contact_phone"] = re.sub(r"\s+", " ", m.group(1)).strip()
            else:
                m = re.search(r"\+?\d[0-9()\s-]{6,20}\d", t)
                if m:
                    data["contact_phone"] = re.sub(r"\s+", " ", m.group(0)).strip()

            m = re.search(r"https?://[\w.-]+(?:\/[\w./-]*)?", t)
            if m:
                data["contact_website"] = m.group(0)

            return data
        except Exception:
            return {
                "exporter_name": None,
                "consignee_name": None,
                "destination_country": None,
                "proposal_date": None,
                "contact_email": None,
                "contact_phone": None,
                "contact_website": None,
            }

    def _build_proposal_variables_from_data(self, data: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
        """Map extracted data to HTML placeholder variables; leave others None for client to fill."""
        return {
            "exporter_name": data.get("exporter_name"),
            "consignee_name": data.get("consignee_name"),
            "destination_country": data.get("destination_country"),
            "proposal_date": data.get("proposal_date"),
            "generated_product_summary": None,
            "generated_product_advantages": None,
            "generated_pricing_stock": None,
            "generated_exporter_edge": None,
            "generated_call_to_action": None,
            "contact_email": data.get("contact_email"),
            "contact_phone": data.get("contact_phone"),
            "contact_website": data.get("contact_website"),
        }
    
    async def _handle_export_duty_optimized(
        self,
        query: str,
        cot_analysis: Dict,
        query_embedding: List[float],
        start_time: float,
        suppress_intro: bool = False,
        context_snippets: Optional[List[str]] = None,
        full_history: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Optimized export duty handling with parallel processing
        """
        try:
            # Parallel tasks: prompt selection and data extraction
            prompt_task = asyncio.create_task(self._get_prompt_optimized(query_embedding, query_text=query))
            extraction_input = query if not context_snippets else "\n".join([query] + context_snippets)
            extraction_task = asyncio.create_task(self._extract_data_optimized(extraction_input))
            
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
                calculation_response = await self._generate_calculation_response(query, hasil, prompt, suppress_intro=suppress_intro)
                
                execution_time = time.time() - start_time
                return {
                    "answer": calculation_response,
                    "similarity": similarity,
                    "similarityPercentage": round(float(similarity) * 100.0, 1),
                    "promptId": prompt.id,
                    "extractedData": extracted_data,
                    "calculationDetails": hasil,
                    "executionTime": execution_time,
                    "cotAnalysis": cot_analysis,
                    "cotUsed": True,
                    "optimized": True
                }
            else:
                # Try to enrich from full history (fallback) if some fields missing
                if full_history:
                    hist_text_parts: List[str] = []
                    for turn in full_history[-10:]:
                        hist_text_parts.append(str(turn.get("user_query", "")))
                        hist_text_parts.append(str(turn.get("assistant_response", "")))
                    augmented = ("\n".join(hist_text_parts + [query]))[:4000]
                    enriched = await self._extract_data_optimized(augmented)
                    # Merge any newly found values
                    for key in ["nama_produk", "berat_bersih_kg", "negara_tujuan"]:
                        if not extracted_data.get(key) and enriched.get(key):
                            extracted_data[key] = enriched[key]

                # If now complete, compute; otherwise ask naturally
                if extracted_data["nama_produk"] and extracted_data["berat_bersih_kg"] and extracted_data["negara_tujuan"]:
                    hasil = await self.duty_service.calculate_export_duty(
                        nama_produk=extracted_data["nama_produk"],
                        berat_bersih=extracted_data["berat_bersih_kg"],
                        negara_tujuan=extracted_data["negara_tujuan"]
                    )
                    calculation_response = await self._generate_calculation_response(query, hasil, prompt, suppress_intro=suppress_intro)
                    execution_time = time.time() - start_time
                    return {
                        "answer": calculation_response,
                        "similarity": similarity,
                        "similarityPercentage": round(float(similarity) * 100.0, 1),
                        "promptId": prompt.id,
                        "extractedData": extracted_data,
                        "calculationDetails": hasil,
                        "executionTime": execution_time,
                        "cotAnalysis": cot_analysis,
                        "cotUsed": True,
                        "optimized": True
                    }

                # Missing data - use AI to generate natural response
                missing_response = await self._generate_missing_data_response(query, extracted_data, prompt, suppress_intro=suppress_intro)
                execution_time = time.time() - start_time
                return {
                    "answer": missing_response,
                    "similarity": similarity,
                    "similarityPercentage": round(float(similarity) * 100.0, 1),
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
    
    async def _handle_general_response_optimized(self, query: str, cot_analysis: Dict, query_embedding: List[float], start_time: float, suppress_intro: bool = False) -> Dict:
        """
        Optimized general response generation
        """
        try:
            # Get prompt template
            prompt, similarity = await self._get_prompt_optimized(query_embedding, query_text=query)
            
            # Generate response with CoT
            cot_response = await self.cot_service.generate_response_with_cot(
                user_query=query,
                analysis=cot_analysis,
                prompt_template=prompt.prompt_template,
                suppress_intro=suppress_intro
            )
            
            execution_time = time.time() - start_time
            return {
                "answer": cot_response["answer"],
                "similarity": similarity,
                "similarityPercentage": round(float(similarity) * 100.0, 1),
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
    
    async def _generate_template_response(self, query: str, template: Dict, prompt: PromptLibrary, suppress_intro: bool = False) -> str:
        """Generate natural response for single template"""
        try:
            cot_response = await self.cot_service.generate_response_with_cot(
                user_query=query,
                analysis={
                    "intent": "document_template",
                    "template_name": template["name"],
                    "has_template": True
                },
                prompt_template=prompt.prompt_template,
                suppress_intro=suppress_intro
            )
            return self._sanitize_answer_text(cot_response["answer"])
        except Exception as e:
            logger.error(f"Error generating template response: {e}")
            return await self._generate_ai_error_response(query, str(e))
    
    async def _generate_multiple_templates_response(self, query: str, templates: List[Dict], prompt: PromptLibrary, suppress_intro: bool = False) -> str:
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
                prompt_template=prompt.prompt_template,
                suppress_intro=suppress_intro
            )
            return self._sanitize_answer_text(cot_response["answer"])
        except Exception as e:
            logger.error(f"Error generating multiple templates response: {e}")
            return await self._generate_ai_error_response(query, str(e))
    
    async def _generate_no_template_response(self, query: str, document_result: Dict, prompt: PromptLibrary, suppress_intro: bool = False) -> str:
        """Generate natural response for no templates available"""
        try:
            cot_response = await self.cot_service.generate_response_with_cot(
                user_query=query,
                analysis={
                    "intent": "document_template",
                    "has_template": False,
                    "document_result": document_result
                },
                prompt_template=prompt.prompt_template,
                suppress_intro=suppress_intro
            )
            return self._sanitize_answer_text(cot_response["answer"])
        except Exception as e:
            logger.error(f"Error generating no template response: {e}")
            return await self._generate_ai_error_response(query, str(e))
    
    async def _generate_calculation_response(self, query: str, hasil: Dict, prompt: PromptLibrary, suppress_intro: bool = False) -> str:
        """Generate natural response for calculation results"""
        try:
            cot_response = await self.cot_service.generate_response_with_cot(
                user_query=query,
                analysis={
                    "intent": "export_duty",
                    "calculation_result": hasil,
                    "has_all_data": True
                },
                prompt_template=prompt.prompt_template,
                suppress_intro=suppress_intro
            )
            return self._sanitize_answer_text(cot_response["answer"])
        except Exception as e:
            logger.error(f"Error generating calculation response: {e}")
            return await self._generate_ai_error_response(query, str(e))
    
    async def _generate_missing_data_response(self, query: str, extracted_data: Dict, prompt: PromptLibrary, suppress_intro: bool = False) -> str:
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
                prompt_template=prompt.prompt_template,
                suppress_intro=suppress_intro
            )
            return self._sanitize_answer_text(cot_response["answer"])
        except Exception as e:
            logger.error(f"Error generating missing data response: {e}")
            return await self._generate_ai_error_response(query, str(e))
    
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
                model="text-embedding-3-small"
            )
            embedding = response.data[0].embedding
            self._embedding_cache[cache_key] = embedding
            return embedding
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            return []
    
    async def _get_prompt_optimized(self, query_embedding: List[float], query_text: Optional[str] = None) -> Tuple[PromptLibrary, float]:
        """
        Optimized prompt selection with caching
        """
        cache_key = hash(((tuple(query_embedding) if query_embedding else ()), (query_text or "")))
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        # Prefer blended selection: embeddings + keywords
        result = await self.prompt_service.get_best_prompt_blended(query_embedding, query_text)
        prompt: Optional[PromptLibrary] = None
        similarity: float = 0.0
        if result:
            prompt, similarity = result
        else:
            # Fallback: embeddings-only search
            emb_only = await self.prompt_service.get_most_similar_prompt(query_embedding, threshold=0.7)
            if emb_only:
                prompt, similarity = emb_only
            else:
                # Keywords-only fallback
                if query_text:
                    keyword_result = await self.prompt_service.get_best_prompt_by_keywords(query_text)
                    if keyword_result:
                        prompt, similarity = keyword_result
        
        if prompt is None:
            # Last resort: pick the first active prompt to ensure we use prompt_library
            try:
                active_prompts = await self.prompt_service.get_active_prompts()
                if active_prompts:
                    prompt = active_prompts[0]
                    similarity = 0.0
            except Exception:
                pass
        
        if prompt is None:
            # Absolute fallback: in-memory default
            if self._default_prompt_cache is None:
                self._default_prompt_cache = PromptLibrary(
                    id=0,
                    prompt_template="Kamu adalah ExportIn, asisten AI ekspor Indonesia yang ramah dan interaktif! 😊",
                    is_active=True
                )
            prompt = self._default_prompt_cache
            similarity = 0.0
        
        self._prompt_cache[cache_key] = (prompt, similarity)
        return prompt, similarity

    def _sanitize_answer_text(self, text: str) -> str:
        """Remove code fences/JSON blocks from model answer; return plain sentence."""
        try:
            import re
            if not isinstance(text, str):
                return text
            # Remove triple backtick blocks (``` ... ```)
            cleaned = re.sub(r"```[\s\S]*?```", "", text)
            # Remove stray code-like json starts
            cleaned = re.sub(r"^\s*\{\s*\"answer\"\s*:\s*\"", "", cleaned)
            # Collapse whitespace
            cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
            return cleaned.strip()
        except Exception:
            return text

    async def _select_relevant_history(self, query_text: str, history: List[Dict], max_turns: int = 3, similarity_threshold: float = 0.35) -> List[str]:
        """
        Select top-k relevant history snippets by embedding similarity and intent alignment.
        Returns a list of short strings like "User: ..." / "Assistant: ...".
        """
        if not history:
            return []

        try:
            # Create embedding for the current query once
            query_emb = await self._create_embedding_optimized(query_text)
            if not query_emb:
                return []

            scored: List[Tuple[float, str]] = []
            for turn in history[-10:]:  # look back up to 10 exchanges
                user_q = str(turn.get("user_query", ""))
                assistant_a = str(turn.get("assistant_response", ""))
                # Build a compact representation
                candidate_text = (user_q + " \n " + assistant_a)[:800]
                cand_emb = await self._create_embedding_optimized(candidate_text)
                if not cand_emb:
                    continue
                # Cosine similarity
                import numpy as np
                a = np.array(query_emb, dtype=float)
                b = np.array(cand_emb, dtype=float)
                if a.shape != b.shape:
                    continue
                denom = float(np.linalg.norm(a) * np.linalg.norm(b))
                if denom == 0:
                    continue
                sim = float(np.dot(a, b) / denom)
                if sim >= similarity_threshold:
                    # Store with small formatted snippet
                    snippet = f"User: {user_q[:300]}\nAssistant: {assistant_a[:400]}"
                    scored.append((sim, snippet))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [s for _, s in scored[:max_turns]]
        except Exception as e:
            logger.error(f"Error selecting relevant history: {e}")
            return []
    
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