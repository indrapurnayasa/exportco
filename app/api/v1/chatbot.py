from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.database import get_async_db
from app.services.optimized_chatbot_service import OptimizedChatbotService
from app.services.prompt_library_service import PromptLibraryService
import redis
import json
import time
import random
import traceback

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Initialize Redis client (global, outside endpoint)
redis_client = redis.Redis.from_url("redis://default:7HB9zBV8ZcStEv3S3uXIAzjncTlcxmtR@redis-14884.c292.ap-southeast-1-1.ec2.redns.redis-cloud.com:14884")

# Use the new Redis configuration for logging
log_redis = redis.Redis.from_url("redis://default:ENRwPubGW1VmpdNmr5kSJG7jqW7IdyKG@redis-16098.crce185.ap-seast-1-1.ec2.redns.redis-cloud.com:16098")

class ChatbotQuery(BaseModel):
    query: str

@router.post("/")
async def chatbot(payload: ChatbotQuery, db: AsyncSession = Depends(get_async_db)):
    """
    Direct chatbot endpoint with optimized processing and Redis caching
    """
    try:
        cache_key = f"chatbot:{payload.query}"
        cached = redis_client.get(cache_key)
        if cached:
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
        redis_client.set(cache_key, json.dumps(result), ex=3600)
        # Log the response to Redis log DB
        log_key = f"chatbotlog:{int(time.time())}:{random.randint(1000,9999)}"
        log_redis.set(log_key, json.dumps(result), ex=1800)
        return result

    except Exception as e:
        print(f"[OPTIMIZED] Error in chatbot endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 