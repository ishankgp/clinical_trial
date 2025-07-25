#!/usr/bin/env python3
"""
Test Semantic Search Functionality
Tests the advanced semantic search capabilities using reasoning models
"""

import os
import sys
import asyncio
import json
from pathlib import Path
import pytest

# Add the repository root directory to the import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Now import from src
from src.mcp.clinical_trial_mcp_server import ClinicalTrialMCPServer


@pytest.mark.asyncio
async def test_semantic_search():
    """Test the semantic search capabilities with various query types"""

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False

    print("🧪 Testing Semantic Search Capabilities")
    print("=" * 60)

    try:
        # Initialize MCP server
        print("1. Initializing MCP server...")
        server = ClinicalTrialMCPServer()
        print("✅ MCP server initialized successfully")

        # Test queries
        test_queries = [
            {
                "name": "Basic drug query",
                "query": "Find trials using semaglutide",
                "model": "o3-mini"
            },
            {
                "name": "Complex indication query",
                "query": "cd src/mcp",
                "model": "o3-mini"
            },
            {
                "name": "Combination therapy query",
                "query": "Find trials combining checkpoint inhibitors with chemotherapy for lung cancer",
                "model": "o3-mini"
            },
            {
                "name": "Biomarker query",
                "query": "Trials for EGFR-mutated non-small cell lung cancer",
                "model": "o3-mini"
            },
            {
                "name": "Complex comparative query",
                "query": "Compare the efficacy endpoints in trials of PARP inhibitors for ovarian cancer",
                "model": "o3"
            }
        ]

        results = {}

        # Test each query with reasoning_query
        for i, test in enumerate(test_queries, 1):
            print(f"\n{i}. Testing {test['name']}...")
            print(f"Query: '{test['query']}'")
            print(f"Model: {test['model']}")
            
            result = await server._reasoning_query({
                "query": test["query"],
                "reasoning_model": test["model"],
                "include_analysis": True,
                "format": "analysis"
            })
            
            print(f"✅ Query completed - Result length: {len(result)} characters")
            print(f"First 100 chars: {result[:100]}...")
            
            results[test["name"]] = {
                "query": test["query"],
                "model": test["model"],
                "result_length": len(result),
                "result_preview": result[:200]
            }

        # Test comparison functionality
        print("\n6. Testing comparison functionality...")
        comparison_result = await server._compare_analysis({
            "comparison_criteria": "Compare Phase 3 trials for metastatic breast cancer",
            "auto_find_similar": True,
            "analysis_depth": "detailed"
        })
        
        print(f"✅ Comparison completed - Result length: {len(comparison_result)} characters")
        print(f"First 100 chars: {comparison_result[:100]}...")
        
        results["Comparison Analysis"] = {
            "criteria": "Compare Phase 3 trials for metastatic breast cancer",
            "result_length": len(comparison_result),
            "result_preview": comparison_result[:200]
        }

        # Test trend analysis functionality
        print("\n7. Testing trend analysis functionality...")
        trend_result = await server._trend_analysis({
            "trend_query": "Analyze trends in immunotherapy trials for solid tumors",
            "time_period": "last 5 years",
            "group_by": "indication",
            "include_insights": True
        })
        
        print(f"✅ Trend analysis completed - Result length: {len(trend_result)} characters")
        print(f"First 100 chars: {trend_result[:100]}...")
        
        results["Trend Analysis"] = {
            "query": "Analyze trends in immunotherapy trials for solid tumors",
            "result_length": len(trend_result),
            "result_preview": trend_result[:200]
        }

        # Save results to file
        print("\n8. Saving test results...")
        with open("semantic_search_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print("✅ Results saved to semantic_search_test_results.json")
        
        print("\n" + "=" * 60)
        print("🎉 All semantic search tests completed successfully!")
        print("\nSummary:")
        for name, data in results.items():
            print(f"- {name}: {data.get('result_length', 'N/A')} chars")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🔍 Semantic Search Functionality Test")
    print("=" * 60)

    success = await test_semantic_search()

    if success:
        print("\n🎉 All tests passed! Semantic search is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 