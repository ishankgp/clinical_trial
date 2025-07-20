#!/usr/bin/env python3
"""
Simple test to verify MCP imports work
"""

import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def test_mcp_imports():
    """Test that MCP imports work correctly"""
    
    print("🧪 Testing MCP Imports")
    print("=" * 30)
    
    try:
        # Test basic MCP imports
        print("1. Testing basic MCP imports...")
        from mcp.server import Server
        from mcp.server.models import InitializationOptions
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent
        print("✅ Basic MCP imports successful")
        
        # Test our analyzer import
        print("2. Testing analyzer import...")
        from analysis.clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning
        print("✅ Analyzer import successful")
        
        # Test database import
        print("3. Testing database import...")
        from database.clinical_trial_database import ClinicalTrialDatabase
        print("✅ Database import successful")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mcp_imports()
    sys.exit(0 if success else 1) 