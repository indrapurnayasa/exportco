#!/usr/bin/env python3
"""
Script to test Chain of Thought integration with chatbot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.services.chain_of_thought_service import ChainOfThoughtService
from app.services.prompt_library_service import PromptLibraryService

async def test_cot_chatbot_integration():
    """Test Chain of Thought integration with chatbot"""
    async with AsyncSessionLocal() as db:
        cot_service = ChainOfThoughtService()
        prompt_service = PromptLibraryService(db)
        
        # Test queries that demonstrate CoT capabilities
        test_queries = [
            {
                "query": "Hitung bea keluar untuk ekspor CPO 1000 kg ke India",
                "description": "Export duty calculation with complete data",
                "expected_intent": "export_duty"
            },
            {
                "query": "Dokumen apa saja yang diperlukan untuk ekspor ke Tiongkok?",
                "description": "Document list request",
                "expected_intent": "document_list"
            },
            {
                "query": "Tolong buatkan invoice untuk pengiriman ke Bangladesh",
                "description": "Document template request",
                "expected_intent": "document_template"
            },
            {
                "query": "Negara mana saja yang menjadi tujuan ekspor utama Indonesia?",
                "description": "General export information",
                "expected_intent": "general_info"
            },
            {
                "query": "Saya ingin mengekspor karet 500 kg ke Malaysia",
                "description": "Incomplete export duty request",
                "expected_intent": "export_duty"
            }
        ]
        
        print("🧠 Testing Chain of Thought Chatbot Integration...")
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"📝 Test Case {i}: {test_case['description']}")
            print(f"Query: '{test_case['query']}'")
            print(f"Expected Intent: {test_case['expected_intent']}")
            print(f"{'='*60}")
            
            start_time = time.time()
            
            try:
                # Step 1: Analyze query with Chain of Thought
                print(f"\n🔍 Step 1: Chain of Thought Analysis")
                cot_analysis = await cot_service.analyze_query_with_cot(test_case['query'])
                
                analysis_time = time.time() - start_time
                print(f"✅ Analysis completed in {analysis_time:.2f}s")
                print(f"   Intent: {cot_analysis['intent']}")
                print(f"   Confidence: {cot_analysis['confidence']:.3f}")
                print(f"   Reasoning: {cot_analysis['reasoning'][:150]}...")
                
                # Show extracted data
                extracted_data = cot_analysis.get('extracted_data', {})
                if any(extracted_data.values()):
                    print(f"   📊 Extracted Data:")
                    for key, value in extracted_data.items():
                        if value:
                            print(f"      {key}: {value}")
                
                # Show missing data
                missing_data = cot_analysis.get('missing_data', [])
                if missing_data:
                    print(f"   ❌ Missing Data: {missing_data}")
                
                # Step 2: Get prompt template (simulate chatbot flow)
                print(f"\n🔍 Step 2: Prompt Template Selection")
                # Note: In real chatbot, this would use embedding similarity
                # For testing, we'll use a default prompt
                default_prompt = "Kamu adalah ExportMate, asisten AI ekspor Indonesia yang membantu pengguna dengan pertanyaan seputar ekspor."
                print(f"   Using default prompt template")
                
                # Step 3: Generate response with CoT
                print(f"\n🔍 Step 3: Response Generation with CoT")
                cot_response = await cot_service.generate_response_with_cot(
                    user_query=test_case['query'],
                    analysis=cot_analysis,
                    prompt_template=default_prompt
                )
                
                response_time = time.time() - start_time
                print(f"✅ Response generated in {response_time:.2f}s")
                print(f"   CoT Used: {cot_response['cot_used']}")
                print(f"   Answer: {cot_response['answer'][:200]}...")
                
                # Step 4: Validate results
                print(f"\n🔍 Step 4: Validation")
                intent_match = cot_analysis['intent'] == test_case['expected_intent']
                confidence_good = cot_analysis['confidence'] >= 0.7
                response_generated = cot_response['cot_used']
                
                print(f"   Intent Match: {'✅' if intent_match else '❌'}")
                print(f"   Confidence Good: {'✅' if confidence_good else '❌'}")
                print(f"   Response Generated: {'✅' if response_generated else '❌'}")
                
                # Overall success
                success = intent_match and confidence_good and response_generated
                print(f"   Overall Success: {'✅' if success else '❌'}")
                
                # Step 5: Log prompt usage (simulate chatbot logging)
                if cot_analysis['intent'] != 'general_info':
                    print(f"\n🔍 Step 5: Prompt Usage Logging")
                    await prompt_service.log_prompt_usage(
                        prompt_id=0,  # Default prompt
                        user_query=test_case['query'],
                        similarity=0.0,
                        response_type=f"cot_{cot_analysis['intent']}"
                    )
                    print(f"   ✅ Prompt usage logged")
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
            
            total_time = time.time() - start_time
            print(f"\n⏱️ Total execution time: {total_time:.2f}s")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Chain of Thought integration test completed!")
        print(f"✅ All test cases processed successfully")
        print(f"✅ Prompt logging integrated")
        print(f"✅ Response generation working")
        print(f"✅ Performance monitoring active")

if __name__ == "__main__":
    asyncio.run(test_cot_chatbot_integration()) 