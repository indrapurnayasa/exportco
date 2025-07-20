#!/usr/bin/env python3
"""
Script to test prompt logging functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.services.prompt_library_service import PromptLibraryService

async def test_prompt_logging():
    """Test prompt logging functionality"""
    async with AsyncSessionLocal() as db:
        service = PromptLibraryService(db)
        
        # Test logging for different scenarios
        test_cases = [
            {
                "prompt_id": 1,
                "query": "Hitung bea keluar untuk ekspor CPO 1000 kg ke India",
                "similarity": 0.85,
                "response_type": "chatbot"
            },
            {
                "prompt_id": 2,
                "query": "Dokumen apa saja yang diperlukan untuk ekspor ke Tiongkok?",
                "similarity": 0.92,
                "response_type": "document_query"
            },
            {
                "prompt_id": 0,  # Default prompt
                "query": "Apa kabar?",
                "similarity": 0.0,
                "response_type": "default_prompt"
            }
        ]
        
        print("🧪 Testing Prompt Logging...")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test Case {i}:")
            print(f"   Prompt ID: {test_case['prompt_id']}")
            print(f"   Query: '{test_case['query']}'")
            print(f"   Similarity: {test_case['similarity']:.3f}")
            print(f"   Type: {test_case['response_type']}")
            
            # Log the prompt usage
            await service.log_prompt_usage(
                prompt_id=test_case['prompt_id'],
                user_query=test_case['query'],
                similarity=test_case['similarity'],
                response_type=test_case['response_type']
            )
            
            print(f"   ✅ Logged successfully")
        
        # Check updated usage counts
        print(f"\n📊 Checking Updated Usage Counts...")
        for test_case in test_cases:
            if test_case['prompt_id'] > 0:  # Skip default prompt (ID 0)
                prompt = await service.get_by_id(test_case['prompt_id'])
                if prompt:
                    print(f"   Prompt ID {prompt.id}: {prompt.usage_count} uses")
        
        print(f"\n✨ Prompt logging test completed!")

if __name__ == "__main__":
    asyncio.run(test_prompt_logging()) 