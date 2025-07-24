#!/usr/bin/env python3
"""
Test script to verify reasoning models (o3, gpt-4o) are working correctly
"""

import os
import sys
from pathlib import Path

# Add the repository root directory to the import path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.analysis.clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning


def test_reasoning_models():
    """Test that reasoning models can be initialized and used"""

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        assert False, "OPENAI_API_KEY not found in environment"

    print("🧪 Testing Reasoning Models")
    print("=" * 50)

    # Test o3 model (default)
    print("\n1. Testing o3 model (default)...")
    try:
        analyzer_o3 = ClinicalTrialAnalyzerReasoning(api_key)  # o3 is now the default
        print("✅ o3 model initialized successfully")

        # Test query analysis with Pydantic model return
        test_query = "Find Phase 3 trials for bladder cancer with checkpoint inhibitors"
        result = analyzer_o3.analyze_query(test_query)
        print(f"✅ Query analysis successful: {result.query_intent}")
        
        # Test Pydantic model properties
        assert hasattr(result, 'filters')
        assert hasattr(result, 'query_intent')
        assert hasattr(result, 'search_strategy')
        assert hasattr(result, 'relevant_fields')
        print("✅ Pydantic model validation passed")

    except Exception as e:
        print(f"❌ o3 test failed: {e}")
        assert False, f"o3 test failed: {e}"

    # Test fallback to non-reasoning model
    print("\n2. Testing fallback to gpt-4o...")
    try:
        analyzer_fallback = ClinicalTrialAnalyzerReasoning(api_key, model="gpt-4o")
        print("✅ gpt-4o fallback initialized successfully")

        # Test query analysis
        test_query = "Find diabetes trials with semaglutide"
        result = analyzer_fallback.analyze_query(test_query)
        print(f"✅ Query analysis successful: {result.query_intent}")
        assert hasattr(result, 'filters')

    except Exception as e:
        print(f"❌ gpt-4o fallback test failed: {e}")
        assert False, f"gpt-4o fallback test failed: {e}"

    print("\n" + "=" * 50)
    print("🎉 All reasoning model tests passed!")
    print("\nReasoning models available:")
    print("- o3: Most powerful reasoning model (default)")
    print("- gpt-4o: Fallback non-reasoning model")
    print("\nNew features tested:")
    print("- Pydantic models for structured output")
    print("- Responses API with high-effort reasoning")


if __name__ == "__main__":
    test_reasoning_models()
