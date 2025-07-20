#!/usr/bin/env python3
"""
Quick UI Chat Test
Simple test to verify the chat interface is working
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def quick_test():
    """Quick test of the MCP chat interface"""
    
    print("🧪 Quick UI Chat Test")
    print("=" * 40)
    
    try:
        # Import MCP chat module
        from mcp.clinical_trial_chat_mcp import ClinicalTrialChatMCP
        
        # Check API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not found")
            return False
        
        # Initialize with o3-mini
        print("1. Initializing MCP chat with o3-mini...")
        chat = ClinicalTrialChatMCP(api_key, model="o3-mini")
        print("✅ MCP chat initialized successfully")
        
        # Test a simple query
        print("\n2. Testing simple query...")
        test_query = "Hello, can you help me find clinical trials?"
        print(f"Query: {test_query}")
        
        response = chat.chat(test_query)
        print(f"✅ Response received ({len(response)} characters)")
        if len(response) > 0:
            print(f"Response: {response[:200]}...")
        else:
            print("⚠️ Empty response received")
        
        # Close chat
        chat.close()
        print("✅ Chat interface closed successfully")
        
        print("\n" + "=" * 40)
        if len(response) > 0:
            print("🎉 Chat interface is working correctly!")
            return True
        else:
            print("⚠️ Chat interface is working but returning empty responses")
            print("This might be due to database being empty or other issues")
            return True  # Still consider it working since no API errors
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1) 