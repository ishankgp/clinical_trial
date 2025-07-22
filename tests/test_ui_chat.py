#!/usr/bin/env python3
"""
Test UI Chat Interface with Reasoning Models
Simple test to verify the chat interface works correctly
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

def test_mcp_chat_initialization():
    """Test MCP chat initialization"""
    
    print("🧪 Testing MCP Chat Initialization")
    print("=" * 50)
    
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
        
        # Test simple query
        print("\n2. Testing simple query...")
        test_query = "Find trials for bladder cancer"
        print(f"Query: {test_query}")
        
        response = chat.chat(test_query)
        print(f"✅ Response received ({len(response)} characters)")
        print(f"First 200 chars: {response[:200]}...")
        
        # Test complex reasoning query
        print("\n3. Testing complex reasoning query...")
        complex_query = "Compare Phase 3 trials for metastatic bladder cancer using different checkpoint inhibitors"
        print(f"Query: {complex_query}")
        
        response2 = chat.chat(complex_query)
        print(f"✅ Response received ({len(response2)} characters)")
        print(f"First 200 chars: {response2[:200]}...")
        
        # Close chat
        chat.close()
        print("✅ Chat interface closed successfully")
        
        print("\n" + "=" * 50)
        print("🎉 MCP chat initialization test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_imports():
    """Test UI imports"""
    
    print("\n🧪 Testing UI Imports")
    print("=" * 30)
    
    try:
        # Test UI imports
        from ui.app import check_api_key
        
        # Test API key check
        has_key = check_api_key()
        print(f"✅ API key check: {'Available' if has_key else 'Not available'}")
        
        print("✅ UI imports test passed!")
        return True
        
    except Exception as e:
        print(f"❌ UI imports test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🏥 UI Chat Interface Test")
    print("=" * 60)
    
    # Test UI imports
    ui_success = test_ui_imports()
    
    # Test MCP chat
    mcp_success = test_mcp_chat_initialization()
    
    if ui_success and mcp_success:
        print("\n🎉 All tests passed! UI chat interface should work correctly.")
        print("\nTo test the UI:")
        print("1. Run: python main.py ui")
        print("2. Go to the 'Chat Assistant' tab")
        print("3. Try the example queries or type your own")
        return True
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 