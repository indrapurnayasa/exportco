#!/usr/bin/env python3
"""
Script to test performance optimization of chatbot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
import statistics
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.services.optimized_chatbot_service import OptimizedChatbotService

async def test_performance_optimization():
    """Test performance optimization of chatbot"""
    async with AsyncSessionLocal() as db:
        optimized_service = OptimizedChatbotService(db)
        
        # Test queries with different complexity levels
        test_queries = [
            {
                "query": "Dokumen apa saja yang diperlukan untuk ekspor ke Tiongkok?",
                "type": "document_list",
                "expected_fast": True
            },
            {
                "query": "Tolong buatkan invoice untuk pengiriman ke Bangladesh",
                "type": "document_template", 
                "expected_fast": True
            },
            {
                "query": "Hitung bea keluar untuk ekspor CPO 1000 kg ke India",
                "type": "export_duty",
                "expected_fast": False  # More complex
            },
            {
                "query": "Negara mana saja yang menjadi tujuan ekspor utama Indonesia?",
                "type": "general_info",
                "expected_fast": False  # Requires CoT
            },
            {
                "query": "Apa kabar?",
                "type": "general_info",
                "expected_fast": False  # Requires CoT
            }
        ]
        
        print("🚀 Testing Performance Optimization...")
        print("=" * 60)
        
        results = []
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n📝 Test Case {i}: {test_case['type']}")
            print(f"Query: '{test_case['query']}'")
            print(f"Expected Fast: {test_case['expected_fast']}")
            
            # Run multiple times for accurate measurement
            execution_times = []
            responses = []
            
            for run in range(3):  # 3 runs for average
                try:
                    start_time = time.time()
                    response = await optimized_service.process_chatbot_query(test_case['query'])
                    execution_time = time.time() - start_time
                    
                    execution_times.append(execution_time)
                    responses.append(response)
                    
                    print(f"   Run {run + 1}: {execution_time:.3f}s")
                    
                except Exception as e:
                    print(f"   Run {run + 1}: Error - {str(e)}")
                    execution_times.append(999)  # High value for error
            
            # Calculate statistics
            if execution_times:
                avg_time = statistics.mean(execution_times)
                min_time = min(execution_times)
                max_time = max(execution_times)
                
                print(f"   📊 Results:")
                print(f"      Average: {avg_time:.3f}s")
                print(f"      Min: {min_time:.3f}s")
                print(f"      Max: {max_time:.3f}s")
                
                # Check if optimized
                is_optimized = responses[0].get("optimized", False) if responses else False
                print(f"      Optimized: {is_optimized}")
                
                # Performance assessment
                if avg_time < 1.0:
                    performance = "🚀 Excellent"
                elif avg_time < 2.0:
                    performance = "✅ Good"
                elif avg_time < 3.0:
                    performance = "⚠️ Acceptable"
                else:
                    performance = "❌ Slow"
                
                print(f"      Performance: {performance}")
                
                results.append({
                    "type": test_case['type'],
                    "query": test_case['query'],
                    "avg_time": avg_time,
                    "min_time": min_time,
                    "max_time": max_time,
                    "is_optimized": is_optimized,
                    "expected_fast": test_case['expected_fast']
                })
            
            print("-" * 40)
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 PERFORMANCE SUMMARY")
        print(f"{'='*60}")
        
        if results:
            # Overall statistics
            all_times = [r['avg_time'] for r in results]
            overall_avg = statistics.mean(all_times)
            overall_min = min(all_times)
            overall_max = max(all_times)
            
            print(f"Overall Performance:")
            print(f"   Average: {overall_avg:.3f}s")
            print(f"   Min: {overall_min:.3f}s")
            print(f"   Max: {overall_max:.3f}s")
            
            # Fast queries performance
            fast_queries = [r for r in results if r['expected_fast']]
            if fast_queries:
                fast_times = [r['avg_time'] for r in fast_queries]
                fast_avg = statistics.mean(fast_times)
                print(f"\nFast Queries Performance:")
                print(f"   Average: {fast_avg:.3f}s")
                print(f"   Target: < 1.0s")
                print(f"   Status: {'✅ Achieved' if fast_avg < 1.0 else '❌ Not achieved'}")
            
            # Complex queries performance
            complex_queries = [r for r in results if not r['expected_fast']]
            if complex_queries:
                complex_times = [r['avg_time'] for r in complex_queries]
                complex_avg = statistics.mean(complex_times)
                print(f"\nComplex Queries Performance:")
                print(f"   Average: {complex_avg:.3f}s")
                print(f"   Target: < 3.0s")
                print(f"   Status: {'✅ Achieved' if complex_avg < 3.0 else '❌ Not achieved'}")
            
            # Optimization status
            optimized_count = sum(1 for r in results if r['is_optimized'])
            print(f"\nOptimization Status:")
            print(f"   Optimized responses: {optimized_count}/{len(results)}")
            print(f"   Optimization rate: {optimized_count/len(results)*100:.1f}%")
            
            # Recommendations
            print(f"\n💡 Recommendations:")
            if overall_avg > 2.0:
                print(f"   ⚠️ Consider further optimization for slow queries")
            if fast_avg > 1.0:
                print(f"   ⚠️ Fast queries should be under 1 second")
            if complex_avg > 3.0:
                print(f"   ⚠️ Complex queries should be under 3 seconds")
            if optimized_count < len(results):
                print(f"   ⚠️ Some responses not using optimization")
            
            if overall_avg < 2.0 and optimized_count == len(results):
                print(f"   ✅ Excellent performance achieved!")
        
        print(f"\n✨ Performance test completed!")

if __name__ == "__main__":
    asyncio.run(test_performance_optimization()) 