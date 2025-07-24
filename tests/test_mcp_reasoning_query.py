#!/usr/bin/env python3
"""
Test MCP Server with Reasoning Query
Test the complex query: "Compare Phase 3 trials for metastatic bladder cancer using different checkpoint inhibitors"
"""

import os
import sys
import asyncio
import json
from pathlib import Path
import pytest

# Add the repository root src directory to the import path
src_dir = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(src_dir))

from mcp.clinical_trial_mcp_server import ClinicalTrialMCPServer


@pytest.mark.asyncio
async def test_reasoning_query():
    """Test the MCP server with a complex reasoning query"""

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False

    print("🧪 Testing MCP Server with Reasoning Query")
    print("=" * 60)

    # Test query
    test_query = "Compare Phase 3 trials for metastatic bladder cancer using different checkpoint inhibitors"
    print(f"Query: {test_query}")
    print("-" * 60)

    try:
        # Initialize MCP server
        print("1. Initializing MCP server...")
        server = ClinicalTrialMCPServer()
        print("✅ MCP server initialized successfully")

        # Test with o3-mini model
        print("\n2. Testing with o3-mini reasoning model...")
        result_mini = await server._reasoning_query(
            {
                "query": test_query,
                "reasoning_model": "o3-mini",
                "include_analysis": True,
                "limit": 20,
                "format": "detailed",
            }
        )

        print("✅ o3-mini query completed")
        print(f"Result length: {len(result_mini)} characters")
        print(f"First 200 chars: {result_mini[:200]}...")

        # Test with o3 model (more powerful)
        print("\n3. Testing with o3 reasoning model...")
        result_o3 = await server._reasoning_query(
            {
                "query": test_query,
                "reasoning_model": "o3",
                "include_analysis": True,
                "limit": 20,
                "format": "analysis",
            }
        )

        print("✅ o3 query completed")
        print(f"Result length: {len(result_o3)} characters")
        print(f"First 200 chars: {result_o3[:200]}...")

        # Test compare_analysis tool
        print("\n4. Testing compare_analysis tool...")
        result_compare = await server._compare_analysis(
            {
                "comparison_criteria": test_query,
                "auto_find_similar": True,
                "analysis_depth": "expert",
            }
        )

        print("✅ compare_analysis completed")
        print(f"Result length: {len(result_compare)} characters")
        print(f"First 200 chars: {result_compare[:200]}...")

        # Test trend_analysis tool
        print("\n5. Testing trend_analysis tool...")
        result_trend = await server._trend_analysis(
            {
                "trend_query": "Analyze trends in checkpoint inhibitor trials for bladder cancer",
                "time_period": "last 5 years",
                "group_by": "drug",
                "include_insights": True,
            }
        )

        print("✅ trend_analysis completed")
        print(f"Result length: {len(result_trend)} characters")
        print(f"First 200 chars: {result_trend[:200]}...")

        # Save detailed results to file
        print("\n6. Saving detailed results...")
        results = {
            "query": test_query,
            "o3_mini_result": result_mini,
            "o3_result": result_o3,
            "compare_analysis_result": result_compare,
            "trend_analysis_result": result_trend,
        }

        with open("mcp_reasoning_test_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print("✅ Results saved to mcp_reasoning_test_results.json")

        print("\n" + "=" * 60)
        print("🎉 All MCP reasoning tests completed successfully!")
        print("\nSummary:")
        print(f"- o3-mini: {len(result_mini)} chars")
        print(f"- o3: {len(result_o3)} chars")
        print(f"- compare_analysis: {len(result_compare)} chars")
        print(f"- trend_analysis: {len(result_trend)} chars")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_simple_queries():
    """Test some simpler queries to verify basic functionality"""

    print("\n🧪 Testing Simple Queries")
    print("=" * 40)

    try:
        server = ClinicalTrialMCPServer()

        # Test 1: Simple search
        print("1. Testing simple search...")
        result1 = await server._smart_search(
            {"query": "bladder cancer trials", "limit": 5, "format": "table"}
        )
        print(f"✅ Simple search: {len(result1)} chars")

        # Test 2: Drug search
        print("2. Testing drug search...")
        result2 = await server._get_trials_by_drug(
            {"drug_name": "pembrolizumab", "limit": 5}
        )
        print(f"✅ Drug search: {len(result2)} chars")

        # Test 3: Indication search
        print("3. Testing indication search...")
        result3 = await server._get_trials_by_indication(
            {"indication": "bladder cancer", "limit": 5}
        )
        print(f"✅ Indication search: {len(result3)} chars")

        print("✅ All simple queries completed")
        return True

    except Exception as e:
        print(f"❌ Simple queries failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🏥 MCP Server Reasoning Query Test")
    print("=" * 60)

    # Test simple queries first
    simple_success = await test_simple_queries()

    # Test complex reasoning query
    reasoning_success = await test_reasoning_query()

    if simple_success and reasoning_success:
        print(
            "\n🎉 All tests passed! MCP server is working correctly with reasoning models."
        )
        return True
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
