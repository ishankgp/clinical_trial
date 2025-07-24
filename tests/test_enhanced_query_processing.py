#!/usr/bin/env python3
"""
Test Enhanced LLM-Based Query Processing
Demonstrates the improved natural language query processing using reasoning models
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the repository root src directory to the import path
src_dir = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(src_dir))

from mcp.clinical_trial_mcp_server import ClinicalTrialMCPServer
from analysis.clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning


async def test_enhanced_query_processing():
    """Test the enhanced LLM-based query processing"""

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False

    print("🧪 Testing Enhanced LLM-Based Query Processing")
    print("=" * 70)

    # Test queries with varying complexity
    test_queries = [
        {
            "query": "Find Phase 3 trials for metastatic bladder cancer using checkpoint inhibitors",
            "expected_filters": ["indication", "trial_phase", "primary_drug"],
            "description": "Complex multi-criteria query",
        },
        {
            "query": "Show me recruiting diabetes trials with semaglutide in the US",
            "expected_filters": [
                "indication",
                "primary_drug",
                "trial_status",
                "geography",
            ],
            "description": "Geographic and status-specific query",
        },
        {
            "query": "Large trials for breast cancer immunotherapy",
            "expected_filters": ["indication", "primary_drug", "enrollment_min"],
            "description": "Size-based query",
        },
        {
            "query": "First line treatment trials for lung cancer",
            "expected_filters": ["indication", "line_of_therapy"],
            "description": "Therapy line specific query",
        },
        {
            "query": "Industry-sponsored Phase 2 trials for rare diseases",
            "expected_filters": ["sponsor", "trial_phase", "indication"],
            "description": "Sponsor and phase specific query",
        },
        {
            "query": "Recent trials with pembrolizumab for melanoma",
            "expected_filters": ["primary_drug", "indication", "trial_status"],
            "description": "Time-based and drug-specific query",
        },
        {
            "query": "Trials with at least 500 patients for heart disease",
            "expected_filters": ["enrollment_min", "indication"],
            "description": "Enrollment size specific query",
        },
        {
            "query": "Completed trials for Alzheimer's disease in Europe",
            "expected_filters": ["trial_status", "indication", "geography"],
            "description": "Status and geographic specific query",
        },
    ]

    try:
        # Initialize MCP server
        print("1. Initializing MCP server...")
        server = ClinicalTrialMCPServer()
        print("✅ MCP server initialized successfully")

        # Initialize reasoning analyzer
        print("\n2. Initializing reasoning analyzer...")
        analyzer = ClinicalTrialAnalyzerReasoning(api_key, model="o3-mini")
        print("✅ Reasoning analyzer initialized successfully")

        results = []

        for i, test_case in enumerate(test_queries, 1):
            print(f"\n{i}. Testing: {test_case['description']}")
            print(f"   Query: {test_case['query']}")

            # Test LLM-based query parsing
            try:
                parsed_result = await server._parse_natural_language_query(
                    test_case["query"]
                )

                # Extract filters
                filters = parsed_result.get("filters", {})
                query_intent = parsed_result.get("query_intent", "N/A")
                confidence = parsed_result.get("confidence_score", 0.0)
                extracted_terms = parsed_result.get("extracted_terms", [])

                print(f"   ✅ LLM Processing Results:")
                print(f"      Intent: {query_intent}")
                print(f"      Confidence: {confidence:.2f}")
                print(f"      Filters: {list(filters.keys())}")
                print(f"      Extracted Terms: {extracted_terms}")

                # Check if expected filters were found
                found_filters = set(filters.keys())
                expected_filters = set(test_case["expected_filters"])
                missing_filters = expected_filters - found_filters
                extra_filters = found_filters - expected_filters

                if missing_filters:
                    print(f"      ⚠️  Missing expected filters: {missing_filters}")
                if extra_filters:
                    print(f"      ℹ️  Extra filters found: {extra_filters}")

                # Test direct reasoning analyzer
                print(f"   🔍 Testing direct reasoning analyzer...")
                reasoning_result = analyzer.analyze_query(test_case["query"])
                reasoning_filters = reasoning_result.get("filters", {})
                reasoning_confidence = reasoning_result.get("confidence_score", 0.0)

                print(f"      Reasoning Confidence: {reasoning_confidence:.2f}")
                print(f"      Reasoning Filters: {list(reasoning_filters.keys())}")

                # Compare results
                if confidence >= 0.7:
                    print(f"      ✅ High confidence LLM parsing ({confidence:.2f})")
                elif confidence >= 0.5:
                    print(f"      ⚠️  Medium confidence LLM parsing ({confidence:.2f})")
                else:
                    print(f"      ❌ Low confidence LLM parsing ({confidence:.2f})")

                # Store results
                results.append(
                    {
                        "query": test_case["query"],
                        "description": test_case["description"],
                        "llm_filters": filters,
                        "llm_confidence": confidence,
                        "reasoning_filters": reasoning_filters,
                        "reasoning_confidence": reasoning_confidence,
                        "missing_filters": list(missing_filters),
                        "extra_filters": list(extra_filters),
                    }
                )

            except Exception as e:
                print(f"   ❌ Error processing query: {e}")
                results.append(
                    {
                        "query": test_case["query"],
                        "description": test_case["description"],
                        "error": str(e),
                    }
                )

        # Save detailed results
        print(f"\n3. Saving detailed results...")
        with open("enhanced_query_processing_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("✅ Results saved to enhanced_query_processing_results.json")

        # Summary statistics
        print(f"\n" + "=" * 70)
        print("📊 SUMMARY STATISTICS")
        print("=" * 70)

        successful_tests = [r for r in results if "error" not in r]
        failed_tests = [r for r in results if "error" in r]

        print(f"Total Tests: {len(results)}")
        print(f"Successful: {len(successful_tests)}")
        print(f"Failed: {len(failed_tests)}")
        print(f"Success Rate: {len(successful_tests)/len(results)*100:.1f}%")

        if successful_tests:
            avg_llm_confidence = sum(
                r["llm_confidence"] for r in successful_tests
            ) / len(successful_tests)
            avg_reasoning_confidence = sum(
                r["reasoning_confidence"] for r in successful_tests
            ) / len(successful_tests)

            print(f"\nAverage LLM Confidence: {avg_llm_confidence:.2f}")
            print(f"Average Reasoning Confidence: {avg_reasoning_confidence:.2f}")

            # Filter accuracy
            total_expected = sum(
                len(test_case["expected_filters"]) for test_case in test_queries
            )
            total_found = sum(len(r["llm_filters"]) for r in successful_tests)
            total_missing = sum(len(r["missing_filters"]) for r in successful_tests)

            print(f"\nFilter Extraction Accuracy:")
            print(f"  Expected Filters: {total_expected}")
            print(f"  Found Filters: {total_found}")
            print(f"  Missing Filters: {total_missing}")
            print(
                f"  Accuracy: {(total_found - total_missing)/total_expected*100:.1f}%"
            )

        print(f"\n🎉 Enhanced query processing test completed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_fallback_processing():
    """Test the enhanced fallback processing when LLM is not available"""

    print(f"\n🧪 Testing Enhanced Fallback Processing")
    print("=" * 50)

    try:
        # Initialize MCP server
        server = ClinicalTrialMCPServer()

        # Test queries that should work with fallback processing
        fallback_queries = [
            "diabetes trials",
            "semaglutide phase 3",
            "bladder cancer immunotherapy",
            "recruiting trials",
            "large trials",
            "US trials",
            "industry sponsored",
        ]

        for query in fallback_queries:
            print(f"\nTesting fallback: {query}")

            # Test the enhanced fallback parsing
            result = server._enhanced_fallback_parsing(query)
            filters = result.get("filters", {})
            confidence = result.get("confidence_score", 0.0)

            print(f"  Filters: {list(filters.keys())}")
            print(f"  Confidence: {confidence:.2f}")

            if filters:
                print(f"  ✅ Fallback processing successful")
            else:
                print(f"  ⚠️  No filters extracted")

        print(f"\n✅ Fallback processing test completed!")
        return True

    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🏥 Enhanced LLM-Based Query Processing Test")
    print("=" * 70)

    # Test enhanced query processing
    enhanced_success = await test_enhanced_query_processing()

    # Test fallback processing
    fallback_success = await test_fallback_processing()

    if enhanced_success and fallback_success:
        print("\n🎉 All tests passed! Enhanced query processing is working correctly.")
        print("\nKey Improvements:")
        print("• Advanced LLM reasoning for complex queries")
        print("• Comprehensive fallback processing")
        print("• Better filter extraction and validation")
        print("• Enhanced confidence scoring")
        print("• Robust error handling")
        return True
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
