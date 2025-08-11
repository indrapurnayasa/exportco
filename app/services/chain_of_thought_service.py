import openai
import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class ChainOfThoughtService:
    """
    Service untuk implementasi Chain of Thought (CoT) pada chatbot
    Membantu chatbot berpikir step-by-step sebelum memberikan jawaban
    """
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def analyze_query_with_cot(self, user_query: str, context: str = "") -> Dict:
        """
        Menganalisis query user menggunakan Chain of Thought
        """
        try:
            # Prompt untuk Chain of Thought
            cot_prompt = f"""
Kamu adalah ExportIn, asisten AI ekspor Indonesia yang menggunakan Chain of Thought untuk menganalisis pertanyaan.

PERTANYAAN USER: {user_query}

CONTEXT: {context}

LANGKAH-LANGKAH ANALISIS (Chain of Thought):

1. **IDENTIFIKASI INTENT**
   - Apa yang sebenarnya ingin diketahui user?
   - Apakah ini pertanyaan tentang dokumen ekspor?
   - Apakah ini pertanyaan tentang bea keluar/pajak?
   - Apakah ini pertanyaan general tentang ekspor?
   - Apakah ini permintaan pembuatan template dokumen?

2. **ANALISIS KONTEKS**
   - Negara mana yang disebutkan?
   - Produk/komoditas apa yang disebutkan?
   - Dokumen apa yang diminta?
   - Data numerik apa yang ada (berat, harga, dll)?

3. **KLASIFIKASI JENIS RESPONSE**
   - Document List: Jika user minta daftar dokumen
   - Document Template: Jika user minta template dokumen
   - Export Duty: Jika user minta perhitungan bea keluar
   - General Info: Jika user minta informasi umum ekspor
   - Data Extraction: Jika perlu ekstrak data dari query

4. **VALIDASI DATA**
   - Apakah semua data yang diperlukan sudah lengkap?
   - Data apa yang masih kurang?
   - Apakah format data sudah benar?

5. **RENCANA RESPONSE**
   - Response apa yang akan diberikan?
   - Template dokumen mana yang akan ditampilkan?
   - Perhitungan apa yang perlu dilakukan?

Sekarang, berikan analisis dalam format JSON:

{{
    "intent": "document_list|document_template|export_duty|general_info|data_extraction",
    "confidence": 0.95,
    "extracted_data": {{
        "country": "string atau null",
        "product": "string atau null", 
        "weight": "number atau null",
        "document_type": "string atau null",
        "currency": "string atau null"
    }},
    "missing_data": ["list data yang kurang"],
    "reasoning": "Penjelasan step-by-step mengapa intent ini dipilih",
    "response_plan": "Rencana response yang akan diberikan",
    "requires_template": true/false,
    "template_type": "invoice|packing_list|coo|dll atau null"
}}
"""
            
            # Call OpenAI dengan Chain of Thought
            response = await self._call_openai_cot(cot_prompt)
            
            # Validate response is string
            if not isinstance(response, str):
                logger.error(f"[COT] Analysis response is not string: {type(response)} - {response}")
                return self._get_fallback_analysis(user_query)
            
            # Parse response
            try:
                analysis = json.loads(response)
                logger.info(f"[COT] Analysis completed: {analysis['intent']} with confidence {analysis['confidence']}")
                return analysis
            except json.JSONDecodeError:
                logger.error(f"[COT] Failed to parse JSON response: {response}")
                return self._get_fallback_analysis(user_query)
                
        except Exception as e:
            logger.error(f"[COT] Error in analyze_query_with_cot: {e}")
            return self._get_fallback_analysis(user_query)
    
    async def generate_response_with_cot(self, user_query: str, analysis: Dict, prompt_template: str, suppress_intro: bool = False) -> Dict:
        """
        Generate response menggunakan Chain of Thought berdasarkan analisis
        """
        try:
            # Prompt untuk response generation dengan CoT
            intro_rule = "Jangan gunakan kalimat pembuka seperti 'Saya ExportIn' atau sapaan pembuka." if suppress_intro else ""

            # Truncate large parts of analysis to control token count
            def _shorten(obj, max_len=1200):
                try:
                    s = json.dumps(obj, ensure_ascii=False)
                    return s[:max_len]
                except Exception:
                    return str(obj)[:max_len]

            response_prompt = f"""
Kamu adalah ExportIn, asisten AI ekspor Indonesia.

ANALISIS SEBELUMNYA:
{_shorten(analysis, 1400)}

PROMPT TEMPLATE:
{prompt_template[:1200]}

PERTANYAAN USER:
{user_query[:800]}

CHAIN OF THOUGHT UNTUK RESPONSE:

1. **REVIEW ANALISIS**
   - Intent yang teridentifikasi: {analysis.get('intent', 'unknown')}
   - Data yang diekstrak: {analysis.get('extracted_data', {})}
   - Data yang kurang: {analysis.get('missing_data', [])}

2. **PLAN RESPONSE STRUCTURE**
   - Jika intent = document_list: Berikan daftar dokumen lengkap
   - Jika intent = document_template: Berikan template dokumen
   - Jika intent = export_duty: Hitung dan jelaskan bea keluar
   - Jika intent = general_info: Berikan informasi umum ekspor
   - Jika intent = data_extraction: Minta data yang kurang

3. **FORMAT RESPONSE**
   - Gunakan bahasa yang jelas dan informatif
   - Berikan penjelasan step-by-step jika diperlukan
   - Sertakan contoh konkret jika relevan
   - Pastikan response sesuai dengan prompt template
   - {intro_rule}

4. **VALIDATE RESPONSE**
   - Apakah response menjawab pertanyaan user?
   - Apakah format response sudah benar?
   - Apakah ada informasi yang kurang?

Sekarang berikan response yang sesuai dengan analisis dan prompt template di atas.
"""
            
            # Generate response
            response = await self._call_openai_response(response_prompt)
            
            # Validate response is string
            if not isinstance(response, str):
                logger.error(f"[COT] Response is not string: {type(response)} - {response}")
                response = "Maaf, terjadi kesalahan dalam memproses pertanyaan Anda. Silakan coba lagi."
            else:
                response = self._polish_style(response)
            
            return {
                "answer": response,
                "analysis": analysis,
                "cot_used": True,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[COT] Error in generate_response_with_cot: {e}")
            return {
                "answer": self._polish_style("Maaf, terjadi kesalahan dalam memproses pertanyaan Anda. Silakan coba lagi."),
                "analysis": analysis,
                "cot_used": False,
                "error": str(e)
            }
    
    async def _call_openai_cot(self, prompt: str) -> str:
        """Call OpenAI untuk Chain of Thought analysis"""
        try:
            response = await self._async_openai_call(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": "Kamu adalah asisten yang menggunakan Chain of Thought untuk menganalisis pertanyaan dengan teliti. Gaya bahasa santai ala chat teman. Jangan mulai dengan frasa permintaan maaf seperti 'Maaf'. Hindari penggunaan emoji (maksimal 1 jika sangat diperlukan). Berikan analisis dalam format JSON yang valid."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            # Extract text content from OpenAI response
            if hasattr(response, 'choices') and response.choices:
                return response.choices[0].message.content.strip()
            else:
                logger.error(f"[COT] Invalid OpenAI response format: {response}")
                raise ValueError("Invalid OpenAI response format")
        except Exception as e:
            logger.error(f"[COT] OpenAI call error: {e}")
            raise
    
    async def _call_openai_response(self, prompt: str) -> str:
        """Call OpenAI untuk response generation"""
        try:
            response = await self._async_openai_call(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Kamu adalah ExportIn, asisten AI ekspor Indonesia. Gaya ngobrol santai, akrab, langsung ke inti. Hindari sapaan pembuka dan pengulangan. Jangan mulai dengan perkenalan diri. Hindari emoji. Jangan terlalu formal."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            # Extract text content from OpenAI response
            if hasattr(response, 'choices') and response.choices:
                return response.choices[0].message.content.strip()
            else:
                logger.error(f"[COT] Invalid OpenAI response format: {response}")
                raise ValueError("Invalid OpenAI response format")
        except Exception as e:
            logger.error(f"[COT] OpenAI response call error: {e}")
            raise
    
    async def _async_openai_call(self, **kwargs):
        """Async wrapper untuk OpenAI call"""
        import asyncio
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            **kwargs
        )
        return response
    
    def _get_fallback_analysis(self, user_query: str) -> Dict:
        """Fallback analysis jika CoT gagal"""
        return {
            "intent": "general_info",
            "confidence": 0.5,
            "extracted_data": {
                "country": None,
                "product": None,
                "weight": None,
                "document_type": None,
                "currency": None
            },
            "missing_data": [],
            "reasoning": "Fallback analysis karena error dalam CoT",
            "response_plan": "Berikan jawaban umum tentang ekspor",
            "requires_template": False,
            "template_type": None
        }

    def _polish_style(self, text: str) -> str:
        """Remove leading apologies/greetings to avoid always starting with them; keep tone casual."""
        if not isinstance(text, str):
            return text
        polished = re.sub(r"^\s*(?:maaf|hai|halo|hello|hi)[!.,:;\-–—\s]*", "", text, flags=re.IGNORECASE)
        # Remove common intro lines like "Saya ExportIn ..." or "Wah, keren! ..." at the start
        lines = polished.splitlines()
        intro_patterns = [
            re.compile(r"^\s*saya\s+exportin.*", re.IGNORECASE),
            re.compile(r"^\s*wah,?\s*keren!?\s*.*", re.IGNORECASE),
        ]
        removed = True
        # Drop up to first 2 intro lines if they match
        drops = 0
        while lines and drops < 2:
            if any(p.match(lines[0]) for p in intro_patterns):
                lines.pop(0)
                drops += 1
            else:
                break
        polished = "\n".join(lines)
        # Also strip leading non-word punctuations/newlines left behind
        polished = re.sub(r"^\s*[-–—,:;.!?\n\r]+\s*", "", polished)
        # Reduce emoji usage: remove all emojis
        emoji_pattern = re.compile(
            r"[\U0001F600-\U0001F64F]"  # emoticons
            r"|[\U0001F300-\U0001F5FF]"  # symbols & pictographs
            r"|[\U0001F680-\U0001F6FF]"  # transport & map
            r"|[\U0001F1E6-\U0001F1FF]"  # flags
            r"|[\U00002702-\U000027B0]"  # dingbats
            r"|[\U000024C2-\U0001F251]",
            flags=re.UNICODE,
        )
        polished = emoji_pattern.sub("", polished)
        # Collapse multiple blank lines
        polished = re.sub(r"\n{3,}", "\n\n", polished)
        return polished.strip()
    
    def extract_keywords_for_cot(self, text: str) -> List[str]:
        """
        Extract keywords untuk membantu Chain of Thought
        """
        keywords = []
        
        # Keywords untuk dokumen
        doc_keywords = ["dokumen", "document", "template", "surat", "form", "invoice", "packing", "list", "coo", "certificate"]
        # Keywords untuk bea keluar
        duty_keywords = ["bea", "pajak", "tarif", "hitung", "perhitungan", "biaya", "cukai"]
        # Keywords untuk negara
        country_keywords = ["indonesia", "india", "china", "japan", "singapore", "malaysia", "thailand", "vietnam", "philippines"]
        # Keywords untuk produk
        product_keywords = ["cpo", "palm oil", "karet", "kopi", "teh", "beras", "gula", "kakao", "cocoa"]
        
        text_lower = text.lower()
        
        for keyword in doc_keywords:
            if keyword in text_lower:
                keywords.append(f"document:{keyword}")
        
        for keyword in duty_keywords:
            if keyword in text_lower:
                keywords.append(f"duty:{keyword}")
        
        for keyword in country_keywords:
            if keyword in text_lower:
                keywords.append(f"country:{keyword}")
        
        for keyword in product_keywords:
            if keyword in text_lower:
                keywords.append(f"product:{keyword}")
        
        return keywords 