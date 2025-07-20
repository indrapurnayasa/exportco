from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.database import get_async_db
from app.services.prompt_library_service import PromptLibraryService
from app.schemas.prompt_library import (
    PromptLibraryCreate, PromptLibraryUpdate, PromptLibraryResponse
)
import openai
import os
from pydantic import BaseModel
from sqlalchemy import select, func
from app.models.prompt_library import PromptLibrary
from sqlalchemy import cast
from pgvector.sqlalchemy import Vector
from sqlalchemy import text
import numpy as np
from app.services.export_duty_service import ExportDutyService
from app.services.export_document_service import ExportDocumentService
import json
import re
import asyncio
from functools import lru_cache
import time
import traceback

router = APIRouter(prefix="/prompt-library", tags=["prompt-library"])

# Cache untuk embedding dan prompt
_embedding_cache = {}
_prompt_cache = {}

@router.get("/", response_model=List[PromptLibraryResponse])
async def get_prompts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)):
    service = PromptLibraryService(db)
    return await service.get_all(skip=skip, limit=limit)

@router.get("/{prompt_id}", response_model=PromptLibraryResponse)
async def get_prompt_by_id(prompt_id: int, db: AsyncSession = Depends(get_async_db)):
    service = PromptLibraryService(db)
    prompt = await service.get_by_id(prompt_id)
    if not prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    return prompt

@router.post("/", response_model=PromptLibraryResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(prompt: PromptLibraryCreate, db: AsyncSession = Depends(get_async_db)):
    service = PromptLibraryService(db)
    return await service.create(prompt)

@router.put("/{prompt_id}", response_model=PromptLibraryResponse)
async def update_prompt(prompt_id: int, prompt: PromptLibraryUpdate, db: AsyncSession = Depends(get_async_db)):
    service = PromptLibraryService(db)
    updated = await service.update(prompt_id, prompt)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    return updated

@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(prompt_id: int, db: AsyncSession = Depends(get_async_db)):
    service = PromptLibraryService(db)
    deleted = await service.delete(prompt_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    return None

class ChatbotQuery(BaseModel):
    query: str

async def create_embedding_optimized(text: str) -> List[float]:
    """Optimized embedding creation with caching"""
    cache_key = hash(text)
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]
    
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        embedding = response.data[0].embedding
        _embedding_cache[cache_key] = embedding
        return embedding
    except Exception as e:
        print(f"Error creating embedding: {e}")
        return None

async def get_dynamic_prompt_from_db_optimized(query: str, db: AsyncSession) -> tuple[str, float]:
    """
    Optimized dynamic prompt selection with caching
    """
    try:
        # Check cache first
        cache_key = hash(query)
        if cache_key in _prompt_cache:
            return _prompt_cache[cache_key]
        
        # Create embedding for user query
        query_embedding = await create_embedding_optimized(query)
        if not query_embedding:
            return await get_default_extraction_prompt_from_db(db), 0.0
        
        # Search for most similar prompt with 70% threshold
        service = PromptLibraryService(db)
        result = await service.get_most_similar_prompt(query_embedding, threshold=0.7)
        
        if result:
            prompt, similarity = result
            print(f"[DYNAMIC PROMPT] Found prompt ID: {prompt.id} with similarity: {similarity:.3f}")
            result_tuple = (prompt.prompt_template, similarity)
            _prompt_cache[cache_key] = result_tuple
            return result_tuple
        else:
            print(f"[DYNAMIC PROMPT] No prompt found with similarity > 70%")
            result_tuple = (await get_default_extraction_prompt_from_db(db), 0.0)
            _prompt_cache[cache_key] = result_tuple
            return result_tuple
            
    except Exception as e:
        print(f"Error in dynamic prompt selection: {e}")
        return await get_default_extraction_prompt_from_db(db), 0.0

async def get_default_extraction_prompt_from_db(db: AsyncSession) -> str:
    result = await db.execute(select(PromptLibrary).where(PromptLibrary.is_default == True))
    prompt = result.scalar_one_or_none()
    if prompt:
        return prompt.prompt_template
    return "Prompt default tidak tersedia. Silakan hubungi admin."

async def extract_data_from_query_optimized(query: str, db: AsyncSession) -> dict:
    """
    Optimized data extraction with reduced API calls
    """
    try:
        # Get dynamic prompt from database using similarity search
        extraction_prompt_template, similarity_score = await get_dynamic_prompt_from_db_optimized(query, db)
        
        # Prompt untuk ekstraksi data
        extraction_prompt = f"""
        {extraction_prompt_template}

        Kalimat pengguna:
        "{query}"
        """
        
        # Use async OpenAI client for better performance
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Kamu adalah asisten yang mengekstrak data dari teks dan mengembalikan dalam format JSON yang valid."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        extracted_text = response.choices[0].message.content.strip()
        
        # Coba parse JSON dari response
        try:
            # Cari JSON dalam response (jika ada teks tambahan)
            json_match = re.search(r'\{.*\}', extracted_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
            else:
                data = json.loads(extracted_text)
            
            return {
                "nama_produk": data.get("nama_produk"),
                "berat_bersih_kg": data.get("berat_bersih_kg"),
                "negara_tujuan": data.get("negara_tujuan"),
                "prompt_similarity": similarity_score
            }
        except json.JSONDecodeError:
            return extract_data_manually(extracted_text)
            
    except Exception as e:
        print(f"Error extracting data: {e}")
        return {
            "nama_produk": None,
            "berat_bersih_kg": None,
            "negara_tujuan": None,
            "prompt_similarity": 0.0
        }

def extract_data_manually(text: str) -> dict:
    """
    Manual extraction fallback jika AI parsing gagal
    """
    data = {
        "nama_produk": None,
        "berat_bersih_kg": None,
        "negara_tujuan": None,
        "prompt_similarity": 0.0
    }
    
    # Cari berat dalam kg
    weight_pattern = r'(\d+(?:\.\d+)?)\s*(?:kg|kilogram)'
    weight_match = re.search(weight_pattern, text, re.IGNORECASE)
    if weight_match:
        data["berat_bersih_kg"] = float(weight_match.group(1))
    
    # Cari negara tujuan (daftar negara umum)
    countries = ["Indonesia", "India", "Tiongkok", "China", "Bangladesh", "Malaysia", "Singapura", "Thailand", "Vietnam", "Filipina", "Jepang", "Korea", "Amerika", "USA", "Eropa", "Australia"]
    for country in countries:
        if country.lower() in text.lower():
            data["negara_tujuan"] = country
            break
    
    # Cari nama produk (komoditas umum)
    commodities = ["CPO", "Crude Palm Oil", "Karet", "Kopi", "Kakao", "Cokelat", "Teh", "Beras", "Jagung", "Kedelai", "Gula", "Tembakau", "Kayu", "Batu Bara", "Minyak", "Gas"]
    for commodity in commodities:
        if commodity.lower() in text.lower():
            data["nama_produk"] = commodity
            break
    
    return data

@router.post("/chatbot/")
async def chatbot(payload: ChatbotQuery, db: AsyncSession = Depends(get_async_db)):
    start_time = time.time()
    query = payload.query
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    try:
        # Intent detection
        document_service = ExportDocumentService(db)
        intent = document_service.detect_intent_and_action(query)

        if intent == "document_template":
            # Get document templates for the query
            document_result = await document_service.get_export_documents_response(query, show_template=True)
            templates = []
            if document_result["success"] and document_result["documents_with_templates"]:
                for doc in document_result["documents_with_templates"]:
                    if doc.get("template") and doc["template"].get("template_dokumen"):
                        templates.append({
                            "name": doc["document_name"],
                            "html_template": doc["template"]["template_dokumen"]
                        })
                execution_time = time.time() - start_time
                if len(templates) == 1:
                    return {
                        "answer": f"Berikut adalah template dokumen {templates[0]['name']} untuk ekspor. Silakan lengkapi bagian yang kosong.",
                        "html_template": templates[0]["html_template"],
                        "success": True,
                        "execution_time": execution_time
                    }
                elif len(templates) > 1:
                    return {
                        "answer": "Mohon minta satu dokumen saja dalam satu waktu. Silakan sebutkan dokumen yang ingin dibuat.",
                        "html_template": "",
                        "success": False,
                        "execution_time": execution_time
                    }
                else:
                    return {
                        "answer": "Maaf, template dokumen yang Anda minta tidak tersedia atau belum ada data untuk negara tersebut.",
                        "html_template": "",
                        "success": False,
                        "execution_time": execution_time
                    }
            else:
                execution_time = time.time() - start_time
                return {
                    "answer": "Maaf, template dokumen yang Anda minta tidak tersedia atau belum ada data untuk negara tersebut.",
                    "html_template": "",
                    "success": False,
                    "execution_time": execution_time
                }
        elif intent == "document_list":
            document_result = await document_service.get_export_documents_response(query, show_template=False)
            execution_time = time.time() - start_time
            return {
                "answer": document_result["message"],
                "success": document_result["success"],
                "execution_time": execution_time
            }
        
        # Optimized embedding creation
        query_embedding = await create_embedding_optimized(query)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to create embedding")
        
        # Get most similar prompt for chatbot response
        service = PromptLibraryService(db)
        result = await service.get_most_similar_prompt(query_embedding, threshold=0.7)
        if not result:
            print(f"[CHATBOT] No similar prompt found (similarity < 0.7), using default prompt")
            # Use default prompt when no similar prompt is found
            prompt = PromptLibrary(
                id=0,
                prompt_template=await get_default_extraction_prompt_from_db(db),
                is_active=True
            )
            similarity = 0.0
        else:
            prompt, similarity = result
            print(f"[CHATBOT] Using prompt ID: {prompt.id}")
        
        # Optimized AI response generation
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt.prompt_template.strip()},
                {"role": "user", "content": payload.query}
            ],
            temperature=0.7,
            max_tokens=400  # Reduced for faster response
        )
        jawaban = response.choices[0].message.content.strip()

        # Deteksi intent untuk membuat dokumen tertentu (template preview)
        if any(keyword in query.lower() for keyword in ["buat", "buatkan", "generate", "tampilkan", "show", "lihat", "preview"]) and any(keyword in query.lower() for keyword in ["invoice", "packing", "list", "dokumen", "surat", "form"]):
            try:
                document_service = ExportDocumentService(db)
                document_result = await document_service.get_export_documents_response(query, show_template=True)
                
                if document_result["success"] and document_result["documents_with_templates"]:
                    execution_time = time.time() - start_time
                    return {
                        "answer": document_result["message"],
                        "similarity": similarity,
                        "prompt_id": prompt.id,
                        "execution_time": execution_time
                    }
                else:
                    execution_time = time.time() - start_time
                    return {
                        "answer": "Maaf, template dokumen yang Anda minta tidak tersedia atau belum ada data untuk negara tersebut.",
                        "similarity": similarity,
                        "prompt_id": prompt.id,
                        "execution_time": execution_time
                    }
            except Exception as e:
                execution_time = time.time() - start_time
                return {
                    "answer": f"Terjadi kesalahan dalam pembuatan dokumen: {str(e)}",
                    "similarity": similarity,
                    "prompt_id": prompt.id,
                    "execution_time": execution_time
                }
        # Deteksi intent untuk daftar dokumen ekspor (tanpa template)
        elif any(keyword in query.lower() for keyword in ["dokumen", "document", "surat", "form", "template", "persyaratan"]):
            try:
                document_service = ExportDocumentService(db)
                document_result = await document_service.get_export_documents_response(query, show_template=False)
                
                execution_time = time.time() - start_time
                return {
                    "answer": document_result["message"],
                    "similarity": similarity,
                    "prompt_id": prompt.id,
                    "execution_time": execution_time
                }
            except Exception as e:
                execution_time = time.time() - start_time
                return {
                    "answer": f"Terjadi kesalahan dalam pencarian dokumen: {str(e)}",
                    "similarity": similarity,
                    "prompt_id": prompt.id,
                    "execution_time": execution_time
                }
        
        # Deteksi intent untuk bea keluar (existing logic)
        elif "bea" in prompt.prompt_template.lower() or "pajak" in prompt.prompt_template.lower() or "cukai" in prompt.prompt_template.lower():
            # Ekstrak data dari query user menggunakan AI dengan dynamic prompt
            extracted_data = await extract_data_from_query_optimized(query, db)
            
            # Cek apakah semua data diperlukan sudah lengkap
            if extracted_data["nama_produk"] and extracted_data["berat_bersih_kg"] and extracted_data["negara_tujuan"]:
                try:
                    duty_service = ExportDutyService(db)
                    hasil = await duty_service.calculate_export_duty(
                        nama_produk=extracted_data["nama_produk"],
                        berat_bersih=extracted_data["berat_bersih_kg"],
                        negara_tujuan=extracted_data["negara_tujuan"]
                    )
                    
                    # Format response yang lebih informatif
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
                    print(f"[PERFORMANCE] Total execution time: {execution_time:.2f}s")
                    
                    # Gabungkan hasil ke response AI
                    return {
                        "answer": response_text,
                        "similarity": similarity,
                        "prompt_id": prompt.id,
                        "extracted_data": extracted_data,
                        "calculation_details": hasil,
                        "prompt_similarity": extracted_data.get("prompt_similarity", 0.0),
                        "execution_time": execution_time
                    }
                except Exception as e:
                    execution_time = time.time() - start_time
                    return {
                        "answer": f"Terjadi kesalahan dalam perhitungan: {str(e)}",
                        "similarity": similarity,
                        "prompt_id": prompt.id,
                        "extracted_data": extracted_data,
                        "execution_time": execution_time
                    }
            else:
                # Jika data belum lengkap, minta user melengkapi dengan detail yang kurang
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
                    "execution_time": execution_time
                }

        execution_time = time.time() - start_time
        return {
            "answer": jawaban,
            "similarity": similarity,
            "execution_time": execution_time
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"[ERROR] Execution time: {execution_time:.2f}s, Error: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}\n{traceback.format_exc()}")

async def get_prompts_with_native_query(db: AsyncSession):
    sql = text("SELECT * FROM prompt_library WHERE is_active = true")
    result = await db.execute(sql)
    rows = result.fetchall()
    return rows 