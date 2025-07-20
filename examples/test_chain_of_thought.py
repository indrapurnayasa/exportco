#!/usr/bin/env python3
"""
Script to test Chain of Thought functionality for chatbot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from app.services.chain_of_thought_service import ChainOfThoughtService

async def test_chain_of_thought():
    """Test Chain of Thought functionality"""
    cot_service = ChainOfThoughtService()
    
    # Test cases with different intents
    test_cases = [
        {
            "query": "Hitung bea keluar untuk ekspor CPO 1000 kg ke India",
            "expected_intent": "export_duty",
            "description": "Export duty calculation"
        },
        {
            "query": "Dokumen apa saja yang diperlukan untuk ekspor ke Tiongkok?",
            "expected_intent": "document_list",
            "description": "Document list request"
        },
        {
            "query": "Tolong buatkan invoice untuk pengiriman ke Bangladesh",
            "expected_intent": "document_template",
            "description": "Document template request"
        },
        {
            "query": "Negara mana saja yang menjadi tujuan ekspor utama Indonesia?",
            "expected_intent": "general_info",
            "description": "General export information"
        },
        {
            "query": "Apa kabar?",
            "expected_intent": "general_info",
            "description": "General conversation"
        }
    ]
    
    print("🧠 Testing Chain of Thought Analysis...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['description']}")
        print(f"   Query: '{test_case['query']}'")
        print(f"   Expected Intent: {test_case['expected_intent']}")
        
        try:
            # Analyze query with CoT
            analysis = await cot_service.analyze_query_with_cot(test_case['query'])
            
            print(f"   ✅ Analysis completed!")
            print(f"   Actual Intent: {analysis['intent']}")
            print(f"   Confidence: {analysis['confidence']:.3f}")
            print(f"   Reasoning: {analysis['reasoning'][:100]}...")
            
            # Check if intent matches expectation
            if analysis['intent'] == test_case['expected_intent']:
                print(f"   🎯 Intent match: YES")
            else:
                print(f"   ⚠️ Intent match: NO (expected: {test_case['expected_intent']})")
            
            # Show extracted data
            extracted_data = analysis.get('extracted_data', {})
            if any(extracted_data.values()):
                print(f"   📊 Extracted Data:")
                for key, value in extracted_data.items():
                    if value:
                        print(f"      {key}: {value}")
            
            # Show missing data
            missing_data = analysis.get('missing_data', [])
            if missing_data:
                print(f"   ❌ Missing Data: {missing_data}")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print(f"\n🧠 Testing Chain of Thought Response Generation...")
    
    # Test response generation
    test_response_case = {
        "query": "Hitung bea keluar untuk ekspor CPO 1000 kg ke India",
        "prompt_template": "Kamu adalah ExportMate, asisten AI ekspor yang membantu menghitung estimasi bea keluar berdasarkan regulasi yang berlaku di Indonesia."
    }
    
    print(f"\n📝 Response Generation Test:")
    print(f"   Query: '{test_response_case['query']}'")
    
    try:
        # Analyze first
        analysis = await cot_service.analyze_query_with_cot(test_response_case['query'])
        
        # Generate response
        response = await cot_service.generate_response_with_cot(
            user_query=test_response_case['query'],
            analysis=analysis,
            prompt_template=test_response_case['prompt_template']
        )
        
        print(f"   ✅ Response generated!")
        print(f"   CoT Used: {response['cot_used']}")
        print(f"   Answer: {response['answer'][:200]}...")
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print(f"\n✨ Chain of Thought test completed!")

if __name__ == "__main__":
    asyncio.run(test_chain_of_thought()) 