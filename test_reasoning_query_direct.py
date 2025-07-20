#!/usr/bin/env python3
"""
Direct test of reasoning query functionality
Test the complex query: "Compare Phase 3 trials for metastatic bladder cancer using different checkpoint inhibitors"
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from analysis.clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning

def test_reasoning_query_direct():
    """Test the reasoning query functionality directly"""
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    print("🧪 Testing Reasoning Query Directly")
    print("=" * 60)
    
    # Test query
    test_query = "Compare Phase 3 trials for metastatic bladder cancer using different checkpoint inhibitors"
    print(f"Query: {test_query}")
    print("-" * 60)
    
    try:
        # Test with o3-mini model
        print("1. Testing with o3-mini reasoning model...")
        analyzer_mini = ClinicalTrialAnalyzerReasoning(api_key, model="o3-mini")
        result_mini = analyzer_mini.analyze_query(test_query)
        
        print("✅ o3-mini query analysis completed")
        print(f"Query Intent: {result_mini.get('query_intent', 'N/A')}")
        print(f"Confidence Score: {result_mini.get('confidence_score', 'N/A')}")
        print(f"Filters: {result_mini.get('filters', {})}")
        print(f"Search Strategy: {result_mini.get('search_strategy', 'N/A')}")
        
        # Test with o3 model (more powerful)
        print("\n2. Testing with o3 reasoning model...")
        analyzer_o3 = ClinicalTrialAnalyzerReasoning(api_key, model="o3")
        result_o3 = analyzer_o3.analyze_query(test_query)
        
        print("✅ o3 query analysis completed")
        print(f"Query Intent: {result_o3.get('query_intent', 'N/A')}")
        print(f"Confidence Score: {result_o3.get('confidence_score', 'N/A')}")
        print(f"Filters: {result_o3.get('filters', {})}")
        print(f"Search Strategy: {result_o3.get('search_strategy', 'N/A')}")
        
        # Test with gpt-4o for comparison
        print("\n3. Testing with gpt-4o (non-reasoning model)...")
        analyzer_gpt4o = ClinicalTrialAnalyzerReasoning(api_key, model="gpt-4o")
        result_gpt4o = analyzer_gpt4o.analyze_query(test_query)
        
        print("✅ gpt-4o query analysis completed")
        print(f"Query Intent: {result_gpt4o.get('query_intent', 'N/A')}")
        print(f"Confidence Score: {result_gpt4o.get('confidence_score', 'N/A')}")
        print(f"Filters: {result_gpt4o.get('filters', {})}")
        print(f"Search Strategy: {result_gpt4o.get('search_strategy', 'N/A')}")
        
        # Save detailed results to file
        print("\n4. Saving detailed results...")
        results = {
            "query": test_query,
            "o3_mini_result": result_mini,
            "o3_result": result_o3,
            "gpt4o_result": result_gpt4o
        }
        
        with open("reasoning_query_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print("✅ Results saved to reasoning_query_test_results.json")
        
        # Compare results
        print("\n" + "=" * 60)
        print("📊 Comparison of Results:")
        print("-" * 60)
        
        models = [
            ("o3-mini", result_mini),
            ("o3", result_o3),
            ("gpt-4o", result_gpt4o)
        ]
        
        for model_name, result in models:
            print(f"\n{model_name.upper()}:")
            print(f"  Confidence: {result.get('confidence_score', 'N/A')}")
            print(f"  Intent: {result.get('query_intent', 'N/A')[:100]}...")
            print(f"  Filters: {len(result.get('filters', {}))} filters extracted")
            print(f"  Strategy: {result.get('search_strategy', 'N/A')[:50]}...")
        
        print("\n" + "=" * 60)
        print("🎉 Reasoning query test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_queries():
    """Test some simpler queries"""
    
    print("\n🧪 Testing Simple Queries")
    print("=" * 40)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return False
    
    try:
        analyzer = ClinicalTrialAnalyzerReasoning(api_key, model="o3-mini")
        
        simple_queries = [
            "Find bladder cancer trials",
            "Show me Phase 3 trials",
            "Trials with pembrolizumab",
            "Checkpoint inhibitor trials"
        ]
        
        for i, query in enumerate(simple_queries, 1):
            print(f"{i}. Testing: {query}")
            result = analyzer.analyze_query(query)
            print(f"   Intent: {result.get('query_intent', 'N/A')[:50]}...")
            print(f"   Filters: {result.get('filters', {})}")
            print()
        
        print("✅ All simple queries completed")
        return True
        
    except Exception as e:
        print(f"❌ Simple queries failed: {e}")
        return False

def main():
    """Main test function"""
    print("🏥 Direct Reasoning Query Test")
    print("=" * 60)
    
    # Test simple queries first
    simple_success = test_simple_queries()
    
    # Test complex reasoning query
    reasoning_success = test_reasoning_query_direct()
    
    if simple_success and reasoning_success:
        print("\n🎉 All tests passed! Reasoning models are working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 