#!/usr/bin/env python3
"""
Script to test Chain of Thought error fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from app.services.chain_of_thought_service import ChainOfThoughtService

async def test_cot_error_fix():
    """Test that the answer.split error has been fixed"""
    cot_service = ChainOfThoughtService()
    
    # Test queries that might cause issues
    test_queries = [
        "Hitung bea keluar untuk ekspor CPO 1000 kg ke India",
        "Dokumen apa saja yang diperlukan untuk ekspor ke Tiongkok?",
        "Apa kabar?",
        "Negara mana saja yang menjadi tujuan ekspor utama Indonesia?"
    ]
    
    print("🔧 Testing Chain of Thought Error Fix...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test Case {i}: '{query}'")
        
        try:
            # Test analysis
            print(f"   🔍 Testing analysis...")
            analysis = await cot_service.analyze_query_with_cot(query)
            
            # Validate analysis response
            if isinstance(analysis, dict):
                print(f"   ✅ Analysis successful: {analysis.get('intent', 'unknown')}")
                print(f"   ✅ Analysis type: {type(analysis)}")
            else:
                print(f"   ❌ Analysis failed: expected dict, got {type(analysis)}")
                continue
            
            # Test response generation
            print(f"   🔍 Testing response generation...")
            default_prompt = "Kamu adalah ExportMate, asisten AI ekspor Indonesia."
            response = await cot_service.generate_response_with_cot(
                user_query=query,
                analysis=analysis,
                prompt_template=default_prompt
            )
            
            # Validate response
            if isinstance(response, dict):
                answer = response.get('answer', '')
                if isinstance(answer, str):
                    print(f"   ✅ Response successful: {len(answer)} characters")
                    print(f"   ✅ Answer type: {type(answer)}")
                    
                    # Test that answer can be split (this was the original error)
                    try:
                        words = answer.split()
                        print(f"   ✅ Answer.split() works: {len(words)} words")
                    except Exception as split_error:
                        print(f"   ❌ Answer.split() failed: {split_error}")
                else:
                    print(f"   ❌ Answer is not string: {type(answer)}")
            else:
                print(f"   ❌ Response failed: expected dict, got {type(response)}")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✨ Error fix test completed!")

if __name__ == "__main__":
    asyncio.run(test_cot_error_fix()) 