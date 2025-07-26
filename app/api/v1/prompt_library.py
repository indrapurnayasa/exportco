from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.database import get_async_db
from app.services.prompt_library_service import PromptLibraryService
from app.services.chain_of_thought_service import ChainOfThoughtService
from app.services.optimized_chatbot_service import OptimizedChatbotService
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
import redis
import random

router = APIRouter(prefix="/prompt-library", tags=["prompt-library"])

# Cache untuk embedding dan prompt
_embedding_cache = {}
_prompt_cache = {}

# Initialize Redis client (global, outside endpoint)
redis_client = redis.Redis.from_url("redis://default:7HB9zBV8ZcStEv3S3uXIAzjncTlcxmtR@redis-14884.c292.ap-southeast-1-1.ec2.redns.redis-cloud.com:14884")

# Use the new Redis configuration for logging
log_redis = redis.Redis.from_url("redis://default:ENRwPubGW1VmpdNmr5kSJG7jqW7IdyKG@redis-16098.crce185.ap-seast-1-1.ec2.redns.redis-cloud.com:16098")

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
            # Log prompt usage
            await service.log_prompt_usage(prompt.id, query, similarity, "dynamic_prompt")
            result_tuple = (prompt.prompt_template, similarity)
            _prompt_cache[cache_key] = result_tuple
            return result_tuple
        else:
            print(f"[DYNAMIC PROMPT] No prompt found with similarity > 70%")
            # Log default prompt usage
            await service.log_prompt_usage(0, query, 0.0, "default_dynamic_prompt")
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
    """
    Optimized chatbot endpoint with minimal delay and Redis caching
    """
    try:
        cache_key = f"chatbot:{payload.query}"
        cached = redis_client.get(cache_key)
        if cached:
            import json
            response = json.loads(cached)
            # Log the response to Redis log DB
            log_key = f"chatbotlog:{int(time.time())}:{random.randint(1000,9999)}"
            log_redis.set(log_key, json.dumps(response), ex=1800)
            return response

        # Use optimized chatbot service
        optimized_service = OptimizedChatbotService(db)
        result = await optimized_service.process_chatbot_query(payload.query)

        # Add prompt logging if available
        if "prompt_id" in result and result.get("cot_analysis"):
            try:
                prompt_service = PromptLibraryService(db)
                await prompt_service.log_prompt_usage(
                    prompt_id=result["prompt_id"],
                    user_query=payload.query,
                    similarity=result.get("similarity", 0.0),
                    response_type="optimized_chatbot"
                )
            except Exception as e:
                print(f"[OPTIMIZED] Error logging prompt usage: {e}")

        # Cache the result (as JSON string, set expiration to 1 hour)
        import json
        redis_client.set(cache_key, json.dumps(result), ex=3600)
        # Log the response to Redis log DB
        log_key = f"chatbotlog:{int(time.time())}:{random.randint(1000,9999)}"
        log_redis.set(log_key, json.dumps(result), ex=1800)
        return result

    except Exception as e:
        print(f"[OPTIMIZED] Error in chatbot endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def get_prompts_with_native_query(db: AsyncSession):
    sql = text("SELECT * FROM prompt_library WHERE is_active = true")
    result = await db.execute(sql)
    rows = result.fetchall()
    return rows 