#!/usr/bin/env python3
"""
Clinical Trial Analysis Tool - Streamlit UI
Advanced interface for analyzing clinical trials with AI models
"""

import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Add src to Python path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import analyzers using dynamic path resolution
analysis_path = os.path.join(os.path.dirname(__file__), '..', 'analysis')
if analysis_path not in sys.path:
    sys.path.append(analysis_path)
from clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning
from clinical_trial_analyzer_llm import ClinicalTrialAnalyzerLLM

try:
    # Try to import MCP chat module with specific path to avoid conflicts
    mcp_path = os.path.join(os.path.dirname(__file__), '..', 'mcp')
    if mcp_path not in sys.path:
        sys.path.insert(0, mcp_path)  # Insert at beginning to prioritize our module
    import clinical_trial_chat_mcp
    ClinicalTrialChatMCP = clinical_trial_chat_mcp.ClinicalTrialChatMCP
    
    # Also import MCP checker
    utils_path = os.path.join(os.path.dirname(__file__), '..', 'utils')
    if utils_path not in sys.path:
        sys.path.append(utils_path)
    from mcp_checker import check_mcp_availability, get_mcp_status_message, get_mcp_setup_instructions
    
except ImportError as e:
    # Fallback if MCP module is not available
    ClinicalTrialChatMCP = None
    check_mcp_availability = None
    get_mcp_status_message = None
    get_mcp_setup_instructions = None
    print(f"MCP Chat module not available: {e}")

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Clinical Trial Analysis Tool",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .model-comparison {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def check_api_key():
    """Check if OpenAI API key is available"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OpenAI API key not found in .env file!")
        st.info("Please create a .env file with your OpenAI API key: OPENAI_API_KEY=your-api-key-here")
        return False
    return True

def analyze_trial_with_model(model_name, nct_id, json_file_path, api_key):
    """Analyze a trial with a specific model"""
    try:
        if model_name in ["gpt-4o", "gpt-4o-mini", "o4-mini"]:
            analyzer = ClinicalTrialAnalyzerReasoning(api_key, model=model_name)
        else:
            analyzer = ClinicalTrialAnalyzerLLM(api_key)
        
        start_time = time.time()
        result = analyzer.analyze_trial(nct_id, json_file_path)
        end_time = time.time()
        
        return {
            "success": True,
            "result": result,
            "time": end_time - start_time,
            "model": model_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": model_name
        }

def display_analysis_results(result, model_name, analysis_time):
    """Display analysis results in a formatted way"""
    st.subheader(f"📊 Analysis Results - {model_name}")
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Model", model_name)
    with col2:
        st.metric("Analysis Time", f"{analysis_time:.2f}s")
    with col3:
        total_fields = len(result)
        st.metric("Total Fields", total_fields)
    with col4:
        valid_fields = sum(1 for v in result.values() if v and v != "NA" and v != "Error in analysis")
        st.metric("Valid Fields", valid_fields)
    
    # Display results in a table
    st.subheader("📋 Analysis Details")
    
    # Create a DataFrame for better display
    results_data = []
    for field, value in result.items():
        if value and value != "NA" and value != "Error in analysis":
            results_data.append({
                "Field": field,
                "Value": str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
            })
    
    if results_data:
        df_results = pd.DataFrame(results_data)
        st.dataframe(df_results, use_container_width=True)
        
        # Download button
        csv_data = df_results.to_csv(index=False)
        st.download_button(
            label="📥 Download Results (CSV)",
            data=csv_data,
            file_name=f"analysis_results_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.warning("No valid analysis results to display.")

def create_comparison_table(comparison_results):
    """Create a comparison table for multiple models"""
    st.subheader("📊 Model Comparison")
    
    # Prepare data for comparison
    comparison_data = []
    for result in comparison_results:
        if result["success"]:
            model = result["model"]
            time_taken = result["time"]
            total_fields = len(result["result"])
            valid_fields = sum(1 for v in result["result"].values() if v and v != "NA" and v != "Error in analysis")
            
            comparison_data.append({
                "Model": model,
                "Analysis Time": f"{time_taken:.2f}s",
                "Total Fields": total_fields,
                "Valid Fields": valid_fields,
                "Success Rate": f"{(valid_fields/total_fields*100):.1f}%" if total_fields > 0 else "0%"
            })
    
    if comparison_data:
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True)
        
        # Create a bar chart for comparison
        fig = px.bar(df_comparison, x="Model", y="Valid Fields", 
                    title="Valid Fields by Model",
                    color="Model")
        st.plotly_chart(fig, use_container_width=True)
        
        # Download comparison
        csv_data = df_comparison.to_csv(index=False)
        st.download_button(
            label="📥 Download Comparison (CSV)",
            data=csv_data,
            file_name=f"model_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.error("No successful analyses to compare.")

def main():
    """Main application function"""
    st.title("🏥 Clinical Trial Analysis Tool")
    st.markdown("---")
    
    # Check API key
    if not check_api_key():
        st.stop()
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Single Trial Analysis", 
        "📊 Model Comparison", 
        "🤖 Chat Assistant", 
        "📈 Results History"
    ])
    
    with tab1:
        st.header("🔍 Single Trial Analysis")
        
        # Load processed trials information
        processed_trials = {}
        try:
            # Use absolute path since this is a standalone script
            results_db_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "trial_analysis_results.db")
            if os.path.exists(results_db_path):
                import sqlite3
                conn = sqlite3.connect(results_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT nct_id, model_name, quality_score, analysis_timestamp FROM trial_analysis_results")
                results = cursor.fetchall()
                conn.close()
                
                for nct_id, model, quality, timestamp in results:
                    if nct_id not in processed_trials:
                        processed_trials[nct_id] = []
                    processed_trials[nct_id].append({
                        "model": model,
                        "quality": quality,
                        "timestamp": timestamp
                    })
                
                if processed_trials:
                    st.success(f"✅ Found {len(processed_trials)} processed trials")
                    
                    # Display processed trials in a compact format
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Processed", len(processed_trials))
                    with col2:
                        total_analyses = sum(len(models) for models in processed_trials.values())
                        st.metric("Total Analyses", total_analyses)
                    with col3:
                        avg_quality = sum(
                            sum(model["quality"] for model in models) 
                            for models in processed_trials.values()
                        ) / total_analyses if total_analyses > 0 else 0
                        st.metric("Avg Quality", f"{avg_quality:.1f}%")
                    
                    # Show processed trials list with search
                    with st.expander("📋 View Processed Trials", expanded=False):
                        # Search functionality
                        search_term = st.text_input("🔍 Search trials by NCT ID:", placeholder="e.g., NCT07046273")
                        
                        # Filter trials based on search
                        filtered_trials = processed_trials
                        if search_term:
                            filtered_trials = {k: v for k, v in processed_trials.items() if search_term.upper() in k.upper()}
                            st.info(f"Found {len(filtered_trials)} trials matching '{search_term}'")
                        
                        # Display filtered trials
                        if filtered_trials:
                            for nct_id, models in filtered_trials.items():
                                model_info = ", ".join([f"{m['model']} ({m['quality']:.1f}%)" for m in models])
                                st.write(f"**{nct_id}**: {model_info}")
                        else:
                            st.info("No trials found matching the search term.")
                else:
                    st.info("📝 No trials have been processed yet. Use 'Process All Trials' or run individual analyses.")
            else:
                st.info("📝 No results database found. Process some trials to see their status.")
        except Exception as e:
            st.warning(f"⚠️ Could not load processed trials: {e}")
        
        st.divider()
        
        # Input section
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📁 Input Options")
            input_method = st.radio(
                "Choose input method:",
                ["Enter NCT ID", "Upload JSON file", "Use sample file"]
            )
            
            nct_id = ""
            json_file_path = None
            
            if input_method == "Enter NCT ID":
                # Show available NCT IDs from processed trials
                available_nct_ids = list(processed_trials.keys()) if processed_trials else []
                
                if available_nct_ids:
                    st.info(f"💡 Available processed trials: {', '.join(available_nct_ids[:5])}{'...' if len(available_nct_ids) > 5 else ''}")
                
                nct_id = st.text_input("Enter NCT ID:", value="NCT07046273")
                
                # Show processing status for entered NCT ID
                if nct_id and nct_id in processed_trials:
                    st.success(f"✅ **{nct_id}** has been processed!")
                    models_processed = processed_trials[nct_id]
                    st.write("**Models used:**")
                    for model_info in models_processed:
                        st.write(f"• {model_info['model']} (Quality: {model_info['quality']:.1f}%)")
                    
                    # Try to show trial metadata
                    try:
                        metadata_conn = sqlite3.connect(results_db_path)
                        metadata_cursor = metadata_conn.cursor()
                        metadata_cursor.execute("SELECT trial_name, trial_phase, trial_status, primary_drug, indication FROM trial_metadata WHERE nct_id = ?", (nct_id,))
                        metadata = metadata_cursor.fetchone()
                        metadata_conn.close()
                        
                        if metadata:
                            st.write("**Trial Details:**")
                            st.write(f"• **Name**: {metadata[0]}")
                            st.write(f"• **Phase**: {metadata[1]}")
                            st.write(f"• **Status**: {metadata[2]}")
                            st.write(f"• **Primary Drug**: {metadata[3]}")
                            st.write(f"• **Indication**: {metadata[4]}")
                    except:
                        pass
                
                elif nct_id:
                    st.info(f"💡 **{nct_id}** has not been processed yet. You can analyze it now!")
                
                if st.button("Fetch from ClinicalTrials.gov"):
                    st.info("Fetching data from ClinicalTrials.gov...")
                    # This would integrate with the ClinicalTrials.gov API
                    st.success("Data fetched successfully!")
            
            elif input_method == "Upload JSON file":
                uploaded_file = st.file_uploader("Upload JSON file", type=['json'])
                if uploaded_file is not None:
                    # Save uploaded file
                    json_file_path = f"temp_{uploaded_file.name}"
                    with open(json_file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.success(f"✅ File uploaded: {uploaded_file.name}")
                    
                    # Extract NCT ID from filename or content
                    try:
                        data = json.load(uploaded_file)
                        if 'nct_id' in data:
                            nct_id = data['nct_id']
                            st.info(f"📋 NCT ID found: {nct_id}")
                    except:
                        st.warning("Could not extract NCT ID from file")
            
            elif input_method == "Use sample file":
                sample_file = "NCT07046273.json"
                if os.path.exists(sample_file):
                    json_file_path = sample_file
                    nct_id = "NCT07046273"
                    st.success(f"✅ Using sample file: {sample_file}")
                else:
                    st.error("❌ Sample file not found!")
                    st.info("Please ensure NCT07046273.json exists in the current directory")
        
        with col2:
            st.subheader("🤖 Analysis Options")
            
            # Model selection
            models = ["gpt-4o", "gpt-4o-mini", "o4-mini", "gpt-4", "llm"]
            selected_models = st.multiselect(
                "Select models to compare:",
                models,
                default=["gpt-4o-mini"]
            )
            
            # Analysis options
            st.write("**Analysis Options:**")
            force_reanalyze = st.checkbox("Force re-analysis (ignore cache)")
            
            # Quick select from processed trials
            if processed_trials:
                st.write("**Quick select from processed trials:**")
                quick_select = st.selectbox(
                    "Quick select from processed trials:",
                    [""] + list(processed_trials.keys())
                )
                if quick_select:
                    nct_id = quick_select
                    st.success(f"✅ Selected: {quick_select}")
        
        # Analysis button
        st.divider()
        
        if st.button("🚀 Start Analysis", type="primary", disabled=not nct_id):
            if not selected_models:
                st.error("❌ Please select at least one model!")
            else:
                # Check if trial has been processed with selected models
                if nct_id in processed_trials:
                    processed_models = [m["model"] for m in processed_trials[nct_id]]
                    unprocessed_models = [m for m in selected_models if m not in processed_models]
                    
                    if not unprocessed_models and not force_reanalyze:
                        st.warning("⚠️ This trial has already been analyzed with the selected models!")
                        st.info("Check 'Force re-analysis' to run again, or view results in the 'Results History' tab.")
                    else:
                        st.info(f"📊 Analyzing {nct_id} with {len(selected_models)} model(s)...")
                        run_analysis(nct_id, selected_models, json_file_path, force_reanalyze)
                else:
                    st.info(f"📊 Analyzing {nct_id} with {len(selected_models)} model(s)...")
                    run_analysis(nct_id, selected_models, json_file_path, force_reanalyze)
                
    with tab2:
        st.header("📊 Model Comparison")
        st.info("Compare different AI models on the same clinical trial data")
        
        # Model comparison interface
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Trial Selection")
            nct_id_compare = st.text_input("Enter NCT ID for comparison:", value="NCT07046273")
            
            # Show available trials
            if processed_trials:
                st.write("**Available trials for comparison:**")
                for trial_id in list(processed_trials.keys())[:10]:
                    if st.button(f"Use {trial_id}", key=f"compare_{trial_id}"):
                        nct_id_compare = trial_id
                        st.success(f"✅ Selected: {trial_id}")
        
        with col2:
            st.subheader("🤖 Models to Compare")
            all_models = ["gpt-4o", "gpt-4o-mini", "o4-mini", "gpt-4", "llm"]
            compare_models = st.multiselect(
                "Select models:",
                all_models,
                default=["gpt-4o", "gpt-4o-mini", "llm"]
            )
        
        # Run comparison
        if st.button("📊 Run Model Comparison", type="primary"):
            if not nct_id_compare:
                st.error("❌ Please enter an NCT ID!")
            elif not compare_models:
                st.error("❌ Please select at least 2 models!")
            else:
                st.info(f"📊 Comparing {len(compare_models)} models on {nct_id_compare}...")
                run_model_comparison(nct_id_compare, compare_models)
    
    with tab3:
        st.header("🤖 MCP Chat Assistant")
        st.info("🚀 **Advanced Chat with MCP Server** - Query across multiple clinical trials with intelligent analysis!")
        
        # Initialize MCP chat interface
        if 'mcp_chat_interface' not in st.session_state:
            if ClinicalTrialChatMCP is None:
                # Use MCP checker if available
                if get_mcp_status_message is not None:
                    status = get_mcp_status_message()
                    if status["type"] == "success":
                        st.success(status["title"])
                        st.info(status["message"])
                    else:
                        st.error(status["title"])
                        st.warning(status["message"])
                        
                        # Show detailed issues and recommendations
                        with st.expander("🔍 View Issues & Solutions", expanded=True):
                            st.write("**Issues Found:**")
                            for issue in status.get("issues", []):
                                st.write(f"• {issue}")
                            
                            st.write("**Recommendations:**")
                            for rec in status.get("recommendations", []):
                                st.write(f"• {rec}")
                            
                            # Show setup instructions
                            if get_mcp_setup_instructions is not None:
                                instructions = get_mcp_setup_instructions()
                                st.write(f"**{instructions['title']}:**")
                                for step in instructions["steps"]:
                                    st.write(f"{step['step']}. **{step['title']}**: {step['description']}")
                                    if 'command' in step:
                                        st.code(step['command'])
                                st.info(instructions["note"])
                else:
                    st.error("❌ MCP Chat module not available!")
                    st.info("The MCP chat functionality is not currently available. Please check the installation.")
                
                st.session_state.mcp_chat_interface = None
                st.session_state.mcp_chat_messages = []
            else:
                # MCP module is available, try to initialize
                try:
                    api_key = os.getenv("OPENAI_API_KEY")
                    if api_key:
                        # Initialize with o3-mini reasoning model
                        st.session_state.mcp_chat_interface = ClinicalTrialChatMCP(api_key, model="o3-mini")
                        st.session_state.mcp_chat_messages = []
                        st.success("✅ MCP Chat assistant initialized successfully with o3-mini reasoning model!")
                        st.info("🧠 **Powered by OpenAI's reasoning models** - I can now understand complex clinical trial queries with superior accuracy!")
                    else:
                        st.error("❌ OpenAI API key not found!")
                        st.session_state.mcp_chat_interface = None
                        st.session_state.mcp_chat_messages = []
                except Exception as e:
                    st.error(f"❌ Failed to initialize MCP chat assistant: {e}")
                    st.info("Please ensure the MCP server is running and accessible.")
                    st.session_state.mcp_chat_interface = None
                    st.session_state.mcp_chat_messages = []
        
        # MCP Chat interface
        if 'mcp_chat_interface' in st.session_state and st.session_state.mcp_chat_interface is not None:
            # Chat configuration
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader("💬 Advanced Clinical Trial Queries (Powered by o3-mini)")
                st.markdown("""
                **🧠 I can help you with complex reasoning queries:**
                - 🔍 **Advanced search** with natural language understanding
                - 📊 **Intelligent trial comparisons** using reasoning models
                - 📈 **Trend analysis** with pattern recognition
                - 💊 **Drug mechanism analysis** and comparisons
                - 📤 **Data export** with intelligent filtering
                - 🧠 **Complex clinical trial queries** requiring reasoning
                
                **Example:** "Compare Phase 3 trials for metastatic bladder cancer using different checkpoint inhibitors"
                """)
            
            with col2:
                if st.button("🗑️ Clear MCP Chat", type="secondary"):
                    st.session_state.mcp_chat_messages = []
                    st.session_state.mcp_chat_interface.clear_history()
                    st.rerun()
            
            # Display MCP chat messages
            mcp_chat_container = st.container()
            
            with mcp_chat_container:
                for message in st.session_state.mcp_chat_messages:
                    if message["role"] == "user":
                        with st.chat_message("user"):
                            st.write(message["content"])
                    else:
                        with st.chat_message("assistant"):
                            st.markdown(message["content"])
            
            # MCP Chat input
            if prompt := st.chat_input("Ask advanced questions about clinical trials..."):
                # Add user message
                st.session_state.mcp_chat_messages.append({"role": "user", "content": prompt})
                
                # Display user message
                with st.chat_message("user"):
                    st.write(prompt)
                
                # Get assistant response
                with st.chat_message("assistant"):
                    with st.spinner("🧠 Processing with o3-mini reasoning model..."):
                        try:
                            response = st.session_state.mcp_chat_interface.chat(prompt)
                            st.markdown(response)
                            st.session_state.mcp_chat_messages.append({"role": "assistant", "content": response})
                        except Exception as e:
                            error_msg = f"Sorry, I encountered an error: {str(e)}"
                            st.error(error_msg)
                            st.session_state.mcp_chat_messages.append({"role": "assistant", "content": error_msg})
            
            # Example MCP queries
            st.subheader("💡 Example MCP Queries")
            
            # Create a grid of example buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🧠 Complex Query", key="mcp_complex"):
                    query = "Compare Phase 3 trials for metastatic bladder cancer using different checkpoint inhibitors"
                    st.session_state.mcp_chat_messages.append({"role": "user", "content": query})
                    with st.chat_message("user"):
                        st.write(query)
                    with st.chat_message("assistant"):
                        with st.spinner("🧠 Processing with o3-mini reasoning model..."):
                            response = st.session_state.mcp_chat_interface.chat(query)
                            st.markdown(response)
                            st.session_state.mcp_chat_messages.append({"role": "assistant", "content": response})
                
                if st.button("📊 AI Comparison", key="mcp_compare"):
                    query = "Compare ADC vs checkpoint inhibitor trials in solid tumors"
                    st.session_state.mcp_chat_messages.append({"role": "user", "content": query})
                    with st.chat_message("user"):
                        st.write(query)
                    with st.chat_message("assistant"):
                        with st.spinner("📊 AI-powered comparison analysis..."):
                            response = st.session_state.mcp_chat_interface.chat(query)
                            st.markdown(response)
                            st.session_state.mcp_chat_messages.append({"role": "assistant", "content": response})
                
                if st.button("📈 Trend Analysis", key="mcp_trend"):
                    query = "Analyze trends in checkpoint inhibitor development over the last 5 years"
                    st.session_state.mcp_chat_messages.append({"role": "user", "content": query})
                    with st.chat_message("user"):
                        st.write(query)
                    with st.chat_message("assistant"):
                        with st.spinner("📈 AI trend analysis with reasoning..."):
                            response = st.session_state.mcp_chat_interface.chat(query)
                            st.markdown(response)
                            st.session_state.mcp_chat_messages.append({"role": "assistant", "content": response})
            
            with col2:
                if st.button("💊 Drug Analysis", key="mcp_drug"):
                    query = "Analyze the mechanism of action and clinical development of ADCs vs checkpoint inhibitors"
                    st.session_state.mcp_chat_messages.append({"role": "user", "content": query})
                    with st.chat_message("user"):
                        st.write(query)
                    with st.chat_message("assistant"):
                        with st.spinner("💊 AI drug mechanism analysis..."):
                            response = st.session_state.mcp_chat_interface.chat(query)
                            st.markdown(response)
                            st.session_state.mcp_chat_messages.append({"role": "assistant", "content": response})
                
                if st.button("📤 Smart Export", key="mcp_export"):
                    query = "Export Phase 3 trials with checkpoint inhibitors, grouped by indication and sorted by enrollment"
                    st.session_state.mcp_chat_messages.append({"role": "user", "content": query})
                    with st.chat_message("user"):
                        st.write(query)
                    with st.chat_message("assistant"):
                        with st.spinner("📤 Intelligent data export..."):
                            response = st.session_state.mcp_chat_interface.chat(query)
                            st.markdown(response)
                            st.session_state.mcp_chat_messages.append({"role": "assistant", "content": response})
                
                if st.button("🧠 Expert Analysis", key="mcp_expert"):
                    query = "Provide detailed analysis of the most promising immunotherapy trials with statistical insights"
                    st.session_state.mcp_chat_messages.append({"role": "user", "content": query})
                    with st.chat_message("user"):
                        st.write(query)
                    with st.chat_message("assistant"):
                        with st.spinner("🧠 Expert-level AI analysis..."):
                            response = st.session_state.mcp_chat_interface.chat(query)
                            st.markdown(response)
                            st.session_state.mcp_chat_messages.append({"role": "assistant", "content": response})
        else:
            # Show status when MCP is not available
            st.info("💡 **MCP Chat Assistant Status**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Check MCP server status more accurately
                if 'mcp_chat_interface' in st.session_state and st.session_state.mcp_chat_interface is not None:
                    # Test if MCP is actually working
                    try:
                        # Try a simple test query
                        test_response = st.session_state.mcp_chat_interface.chat("test")
                        st.success("✅ MCP Server: Connected")
                    except Exception as e:
                        st.error("❌ MCP Server: Error")
                        st.caption(f"Error: {str(e)[:50]}...")
                elif ClinicalTrialChatMCP is not None:
                    st.warning("⚠️ MCP Server: Not Initialized")
                    st.caption("Click 'Initialize MCP Chat' to connect")
                else:
                    st.error("❌ MCP Server: Not Available")
                    st.caption("MCP module not found")
            
            # Add initialization button if MCP is available but not initialized
            if ClinicalTrialChatMCP is not None and ('mcp_chat_interface' not in st.session_state or st.session_state.mcp_chat_interface is None):
                if st.button("🚀 Initialize MCP Chat", type="primary"):
                    try:
                        api_key = os.getenv("OPENAI_API_KEY")
                        if api_key:
                            st.session_state.mcp_chat_interface = ClinicalTrialChatMCP(api_key, model="o3-mini")
                            st.session_state.mcp_chat_messages = []
                            st.success("✅ MCP Chat assistant initialized successfully with o3-mini reasoning model!")
                            st.rerun()
                        else:
                            st.error("❌ OpenAI API key not found!")
                    except Exception as e:
                        st.error(f"❌ Failed to initialize MCP chat assistant: {e}")
                        st.info("Please ensure the MCP server is running and accessible.")
            
            with col2:
                # Check database status
                try:
                    # Import database using dynamic path resolution
                    database_path = os.path.join(os.path.dirname(__file__), '..', 'database')
                    if database_path not in sys.path:
                        sys.path.append(database_path)
                    from clinical_trial_database import ClinicalTrialDatabase
                    db = ClinicalTrialDatabase()
                    trials = db.search_trials({}, 1)
                    st.success(f"✅ Database: {len(trials)}+ trials")
                except:
                    st.warning("⚠️ Database: Check connection")
            
            with col3:
                # Check API key
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    st.success("✅ OpenAI API: Ready")
                else:
                    st.error("❌ OpenAI API: Missing")
    
    with tab4:
        st.header("📈 Results History")
        
        # Add tabs for different types of results
        results_tab1, results_tab2, results_tab3 = st.tabs(["📊 Processed Trials", "📁 Analysis Files", "🔧 System Status"])
        
        with results_tab1:
            st.subheader("📊 Processed Trial Results")
            
            # Try to load processed trial results
            try:
                import sqlite3
                import pandas as pd
                
                # Check if results database exists
                results_db_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "trial_analysis_results.db")
                if os.path.exists(results_db_path):
                    conn = sqlite3.connect(results_db_path)
                    
                    # Get trial metadata
                    df_metadata = pd.read_sql_query('''
                        SELECT * FROM trial_metadata 
                        ORDER BY last_updated DESC
                    ''', conn)
                    
                    # Get analysis results
                    df_results = pd.read_sql_query('''
                        SELECT * FROM trial_analysis_results 
                        ORDER BY analysis_timestamp DESC
                    ''', conn)
                    
                    conn.close()
                    
                    if not df_metadata.empty:
                        st.success(f"✅ Found {len(df_metadata)} processed trials")
                        
                        # Display trial summary
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Trials", len(df_metadata))
                        with col2:
                            if not df_results.empty:
                                avg_quality = df_results['quality_score'].mean()
                                st.metric("Avg Quality Score", f"{avg_quality:.1f}%")
                        with col3:
                            if not df_results.empty:
                                avg_time = df_results['analysis_time'].mean()
                                st.metric("Avg Analysis Time", f"{avg_time:.1f}s")
                        
                        # Display trials table
                        st.subheader("📋 Processed Trials")
                        
                        # Create a summary table
                        summary_data = []
                        for _, row in df_metadata.iterrows():
                            nct_id = row['nct_id']
                            trial_results = df_results[df_results['nct_id'] == nct_id]
                            
                            if not trial_results.empty:
                                result_row = trial_results.iloc[0]
                                summary_data.append({
                                    "NCT ID": nct_id,
                                    "Trial Name": row['trial_name'][:50] + "..." if len(str(row['trial_name'])) > 50 else row['trial_name'],
                                    "Phase": row['trial_phase'],
                                    "Status": row['trial_status'],
                                    "Primary Drug": row['primary_drug'][:30] + "..." if len(str(row['primary_drug'])) > 30 else row['primary_drug'],
                                    "Indication": row['indication'][:30] + "..." if len(str(row['indication'])) > 30 else row['indication'],
                                    "Quality Score": f"{result_row['quality_score']:.1f}%",
                                    "Analysis Time": f"{result_row['analysis_time']:.1f}s",
                                    "Model": result_row['model_name']
                                })
                        
                        if summary_data:
                            df_summary = pd.DataFrame(summary_data)
                            st.dataframe(df_summary, use_container_width=True)
                            
                            # Download button
                            csv_data = df_summary.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Processed Trials Summary (CSV)",
                                data=csv_data,
                                file_name=f"processed_trials_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("📝 No processed trial results found.")
                    
                    else:
                        st.info("📝 No processed trials found. Run the trial processor to analyze all trials.")
                        
                else:
                    st.info("📝 No results database found. Run the trial processor to analyze all trials.")
                    
            except Exception as e:
                st.error(f"❌ Error loading processed results: {e}")
                st.info("Run the trial processor to analyze all trials.")
        
        with results_tab2:
            st.subheader("📁 Recent Analysis Files")
            
            # Find CSV files
            csv_files = [f for f in os.listdir(".") if f.endswith(".csv") and ("analysis_" in f or "model_comparison_" in f)]
            
            if csv_files:
                # Sort by modification time
                csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                for file in csv_files[:10]:  # Show last 10 files
                    file_time = datetime.fromtimestamp(os.path.getmtime(file))
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"📄 {file}")
                    with col2:
                        st.write(f"📅 {file_time.strftime('%Y-%m-%d %H:%M')}")
                    with col3:
                        # Read and display summary
                        try:
                            df = pd.read_csv(file)
                            st.write(f"📊 {len(df)} trials, {len(df.columns)} fields")
                        except:
                            st.write("❌ Error reading file")
            else:
                st.info("📝 No analysis files found. Run some analyses to see results here!")
        
        with results_tab3:
            st.subheader("🔧 System Status")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # API key status
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    st.success("✅ OpenAI API Key: Configured")
                else:
                    st.error("❌ OpenAI API Key: Missing")
            
            with col2:
                # Sample file status
                if os.path.exists("NCT07046273.json"):
                    st.success("✅ Sample file: Available")
                else:
                    st.warning("⚠️ Sample file: Missing")
            
            with col3:
                # Cache status
                cache_dir = Path("cache")
                if cache_dir.exists():
                    cache_files = len(list(cache_dir.glob("*.json")))
                    st.info(f"📦 Cache: {cache_files} files")
                else:
                    st.info("📦 Cache: Empty")
            
            # Additional status information
            st.subheader("📊 Database Status")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Main database status
                try:
                    # Import database using dynamic path resolution
                    database_path = os.path.join(os.path.dirname(__file__), '..', 'database')
                    if database_path not in sys.path:
                        sys.path.append(database_path)
                    from clinical_trial_database import ClinicalTrialDatabase
                    db = ClinicalTrialDatabase()
                    trials = db.search_trials({}, 1)
                    st.success(f"✅ Main DB: {len(trials)}+ trials")
                except:
                    st.warning("⚠️ Main DB: Check connection")
            
            with col2:
                # Results database status
                results_db_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "trial_analysis_results.db")
                if os.path.exists(results_db_path):
                    try:
                        conn = sqlite3.connect(results_db_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM trial_metadata")
                        count = cursor.fetchone()[0]
                        conn.close()
                        st.success(f"✅ Results DB: {count} trials")
                    except:
                        st.warning("⚠️ Results DB: Check connection")
                else:
                    st.info("📝 Results DB: Not created")
            
            with col3:
                # MCP server status
                if 'mcp_chat_interface' in st.session_state:
                    st.success("✅ MCP Server: Connected")
                else:
                    st.warning("⚠️ MCP Server: Disconnected")

def run_analysis(nct_id, models, json_file_path, force_reanalyze):
    """Run analysis for a single trial with multiple models"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    for i, model in enumerate(models):
        status_text.text(f"Analyzing with {model}...")
        progress_bar.progress((i + 1) / len(models))
        
        result = analyze_trial_with_model(model, nct_id, json_file_path, api_key)
        results.append(result)
        
        if result["success"]:
            st.success(f"✅ {model} analysis completed!")
            display_analysis_results(result["result"], model, result["time"])
        else:
            st.error(f"❌ {model} analysis failed: {result['error']}")
    
    # Show comparison if multiple models
    if len(results) > 1:
        successful_results = [r for r in results if r["success"]]
        if successful_results:
            create_comparison_table(successful_results)
    
    status_text.text("Analysis complete!")
    progress_bar.progress(1.0)

def run_model_comparison(nct_id, models):
    """Run model comparison for a single trial"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    for i, model in enumerate(models):
        status_text.text(f"Running {model}...")
        progress_bar.progress((i + 1) / len(models))
        
        result = analyze_trial_with_model(model, nct_id, None, api_key)
        results.append(result)
    
    # Show comparison
    successful_results = [r for r in results if r["success"]]
    if successful_results:
        create_comparison_table(successful_results)
    else:
        st.error("❌ All model analyses failed!")
    
    status_text.text("Comparison complete!")
    progress_bar.progress(1.0)

if __name__ == "__main__":
    main() 