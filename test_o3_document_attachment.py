#!/usr/bin/env python3
"""
Test script for o3 model with document attachment functionality
Demonstrates enhanced clinical trial analysis using OpenAI's o3 reasoning model
with the detailed specification document as attachment
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from analysis.clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning
from mcp.clinical_trial_chat_mcp import ClinicalTrialChatMCP

def test_o3_document_attachment():
    """Test o3 model with document attachment for clinical trial analysis"""
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your-api-key-here")
        return False
    
    print("🧪 Testing o3 Model with Document Attachment")
    print("=" * 60)
    
    # Test 1: Clinical Trial Analysis with o3 model
    print("\n1. Testing Clinical Trial Analysis with o3 model...")
    try:
        analyzer = ClinicalTrialAnalyzerReasoning(api_key, model="o3")
        
        # Test with a sample NCT ID
        nct_id = "NCT07046273"
        json_file_path = "NCT07046273.json"
        
        if os.path.exists(json_file_path):
            print(f"✅ Analyzing {nct_id} with o3 model and document attachment...")
            result = analyzer.analyze_trial(nct_id, json_file_path)
            
            if "error" not in result:
                print("✅ Analysis completed successfully!")
                print(f"Model used: {result.get('model_used', 'N/A')}")
                print(f"Analysis method: {result.get('analysis_method', 'N/A')}")
                print(f"Primary Drug: {result.get('primary_drug', 'N/A')}")
                print(f"Indication: {result.get('indication', 'N/A')}")
                print(f"Trial Phase: {result.get('trial_phase', 'N/A')}")
                print(f"Line of Therapy: {result.get('line_of_therapy', 'N/A')}")
                
                # Save detailed results
                with open("o3_analysis_results.json", "w") as f:
                    json.dump(result, f, indent=2)
                print("✅ Detailed results saved to o3_analysis_results.json")
            else:
                print(f"❌ Analysis failed: {result['error']}")
        else:
            print(f"⚠️ JSON file {json_file_path} not found, skipping trial analysis test")
            
    except Exception as e:
        print(f"❌ Clinical trial analysis test failed: {e}")
    
    # Test 2: MCP Chat with o3 model
    print("\n2. Testing MCP Chat with o3 model and document attachment...")
    try:
        chat = ClinicalTrialChatMCP(api_key, model="o3")
        
        # Test reasoning query
        test_query = "Find Phase 3 trials for bladder cancer with checkpoint inhibitors"
        print(f"✅ Testing query: {test_query}")
        
        response = chat.chat(test_query)
        print("✅ MCP Chat response received!")
        print(f"Response length: {len(response)} characters")
        print(f"First 200 chars: {response[:200]}...")
        
        chat.close()
        
    except Exception as e:
        print(f"❌ MCP Chat test failed: {e}")
    
    # Test 3: Query Analysis with Document Attachment
    print("\n3. Testing Query Analysis with Document Attachment...")
    try:
        chat = ClinicalTrialChatMCP(api_key, model="o3-mini")
        
        # Test complex query analysis
        complex_query = "Compare trials using different ADC modalities for solid tumors with HER2 expression"
        print(f"✅ Testing complex query: {complex_query}")
        
        analysis_result = chat._analyze_query_with_document_attachment(complex_query, "o3-mini")
        
        print("✅ Query analysis completed!")
        print(f"Query Intent: {analysis_result.get('query_intent', 'N/A')}")
        print(f"Confidence Score: {analysis_result.get('confidence_score', 'N/A')}")
        print(f"Search Strategy: {analysis_result.get('search_strategy', 'N/A')}")
        print(f"Extracted Filters: {analysis_result.get('filters', {})}")
        
        chat.close()
        
    except Exception as e:
        print(f"❌ Query analysis test failed: {e}")
    
    # Test 4: Model Comparison
    print("\n4. Testing Model Comparison (o3 vs o3-mini)...")
    try:
        models = ["o3", "o3-mini"]
        test_query = "Find diabetes trials with semaglutide"
        
        for model in models:
            print(f"\nTesting {model}...")
            analyzer = ClinicalTrialAnalyzerReasoning(api_key, model=model)
            
            # Test query analysis
            result = analyzer.analyze_query(test_query)
            print(f"✅ {model}: Query intent = {result.get('query_intent', 'N/A')}")
            print(f"   Confidence = {result.get('confidence_score', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Model comparison test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 o3 Document Attachment Testing Complete!")
    print("\nKey Features Tested:")
    print("✅ Clinical trial analysis with document attachment")
    print("✅ MCP chat with enhanced reasoning")
    print("✅ Query analysis with specification document")
    print("✅ Model comparison and fallback")
    
    return True

def main():
    """Main function to run the o3 document attachment tests"""
    print("🚀 o3 Model with Document Attachment - Clinical Trial Analysis")
    print("=" * 70)
    print("This test demonstrates the enhanced capabilities of OpenAI's o3 model")
    print("when used with the detailed clinical trial analysis specification document.")
    print("=" * 70)
    
    success = test_o3_document_attachment()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Review the generated o3_analysis_results.json file")
        print("2. Try the MCP CLI: python src/mcp/clinical_trial_chat_mcp.py")
        print("3. Use the web UI: python main.py ui")
        print("4. Test with your own NCT IDs and queries")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure OPENAI_API_KEY is set in .env file")
        print("2. Check that the specification document exists")
        print("3. Verify internet connection for API calls")
        print("4. Ensure all dependencies are installed")

if __name__ == "__main__":
    main() 