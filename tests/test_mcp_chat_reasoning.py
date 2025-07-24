#!/usr/bin/env python3
"""
Test MCP Chat with Reasoning Models
Test the chat interface with o3-mini reasoning model
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the repository root src directory to the import path
src_dir = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(src_dir))

from mcp.clinical_trial_chat_mcp import ClinicalTrialChatMCP


def test_mcp_chat_reasoning():
    """Test the MCP chat interface with reasoning models"""

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False

    print("🧪 Testing MCP Chat with Reasoning Models")
    print("=" * 60)

    try:
        # Initialize chat interface with o3-mini
        print("1. Initializing MCP chat with o3-mini...")
        chat = ClinicalTrialChatMCP(api_key, model="o3-mini")
        print("✅ MCP chat initialized successfully")

        # Test complex reasoning query
        print("\n2. Testing complex reasoning query...")
        test_query = "Compare Phase 3 trials for metastatic bladder cancer using different checkpoint inhibitors"
        print(f"Query: {test_query}")

        response = chat.chat(test_query)
        print(f"✅ Response received ({len(response)} characters)")
        print(f"First 300 chars: {response[:300]}...")

        # Test simple query
        print("\n3. Testing simple query...")
        simple_query = "Find trials for bladder cancer"
        print(f"Query: {simple_query}")

        response2 = chat.chat(simple_query)
        print(f"✅ Response received ({len(response2)} characters)")
        print(f"First 300 chars: {response2[:300]}...")

        # Test trend analysis
        print("\n4. Testing trend analysis...")
        trend_query = "Analyze trends in checkpoint inhibitor trials"
        print(f"Query: {trend_query}")

        response3 = chat.chat(trend_query)
        print(f"✅ Response received ({len(response3)} characters)")
        print(f"First 300 chars: {response3[:300]}...")

        # Get conversation history
        print("\n5. Checking conversation history...")
        history = chat.get_conversation_history()
        print(f"✅ Conversation history: {len(history)} messages")

        # Close the chat
        chat.close()
        print("✅ Chat interface closed successfully")

        print("\n" + "=" * 60)
        print("🎉 All MCP chat tests completed successfully!")
        print("\nSummary:")
        print(f"- Complex reasoning query: {len(response)} chars")
        print(f"- Simple query: {len(response2)} chars")
        print(f"- Trend analysis: {len(response3)} chars")
        print(f"- Conversation history: {len(history)} messages")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_different_models():
    """Test different reasoning models"""

    print("\n🧪 Testing Different Reasoning Models")
    print("=" * 50)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return False

    models = ["o3-mini", "o3", "gpt-4o"]
    test_query = "Find Phase 3 trials for breast cancer with immunotherapy"

    for model in models:
        try:
            print(f"\nTesting {model}...")
            chat = ClinicalTrialChatMCP(api_key, model=model)

            response = chat.chat(test_query)
            print(f"✅ {model}: {len(response)} characters")
            print(f"   First 200 chars: {response[:200]}...")

            chat.close()

        except Exception as e:
            print(f"❌ {model} failed: {e}")


def main():
    """Main test function"""
    print("🏥 MCP Chat Reasoning Model Test")
    print("=" * 60)

    # Test main functionality
    success = test_mcp_chat_reasoning()

    # Test different models
    test_different_models()

    if success:
        print(
            "\n🎉 All tests passed! MCP chat with reasoning models is working correctly."
        )
        return True
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
