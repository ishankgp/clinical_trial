#!/usr/bin/env python3
"""
Test script to verify reasoning models (o3, o3-mini) are working correctly
"""

import os
import sys
from pathlib import Path

# Add the project src directory to the import path
src_dir = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(src_dir))

from analysis.clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning


def test_reasoning_models():
    """Test that reasoning models can be initialized and used"""

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False

    print("🧪 Testing Reasoning Models")
    print("=" * 50)

    # Test o3-mini model
    print("\n1. Testing o3-mini model...")
    try:
        analyzer_mini = ClinicalTrialAnalyzerReasoning(api_key, model="o3-mini")
        print("✅ o3-mini model initialized successfully")

        # Test query analysis
        test_query = "Find Phase 3 trials for bladder cancer with checkpoint inhibitors"
        result = analyzer_mini.analyze_query(test_query)
        print(f"✅ Query analysis successful: {result.get('query_intent', 'N/A')}")

    except Exception as e:
        print(f"❌ o3-mini test failed: {e}")
        return False

    # Test o3 model
    print("\n2. Testing o3 model...")
    try:
        analyzer_o3 = ClinicalTrialAnalyzerReasoning(api_key, model="o3")
        print("✅ o3 model initialized successfully")

        # Test query analysis
        test_query = "Compare trials using different ADC modalities for solid tumors"
        result = analyzer_o3.analyze_query(test_query)
        print(f"✅ Query analysis successful: {result.get('query_intent', 'N/A')}")

    except Exception as e:
        print(f"❌ o3 test failed: {e}")
        return False

    # Test fallback to non-reasoning model
    print("\n3. Testing fallback to gpt-4o...")
    try:
        analyzer_fallback = ClinicalTrialAnalyzerReasoning(api_key, model="gpt-4o")
        print("✅ gpt-4o fallback initialized successfully")

        # Test query analysis
        test_query = "Find diabetes trials with semaglutide"
        result = analyzer_fallback.analyze_query(test_query)
        print(f"✅ Query analysis successful: {result.get('query_intent', 'N/A')}")

    except Exception as e:
        print(f"❌ gpt-4o fallback test failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 All reasoning model tests passed!")
    print("\nReasoning models available:")
    print("- o3: Most powerful reasoning model")
    print("- o3-mini: Fast reasoning model (default)")
    print("- gpt-4o: Fallback non-reasoning model")

    return True


if __name__ == "__main__":
    success = test_reasoning_models()
    sys.exit(0 if success else 1)
