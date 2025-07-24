# Clinical Trial Analysis System Documentation

Welcome to the documentation for the Clinical Trial Analysis System. This guide will help you navigate the available documentation files.

## 📚 Documentation Index

### 🚀 Getting Started
- [**MCP Setup & Usage Guide**](MCP_SETUP_GUIDE.md) - Complete guide to setting up and using the Model Context Protocol features
- [**README_UI**](README_UI.md) - Overview of the web UI features and usage

### 🔧 Troubleshooting & Support
- [**Chat Assistant Troubleshooting**](CHAT_ASSISTANT_TROUBLESHOOTING.md) - Resolve issues with the chat assistant functionality

### 🧠 Technical Documentation
- [**Enhanced LLM Query Processing**](ENHANCED_LLM_QUERY_PROCESSING.md) - How the system processes natural language queries
- [**Reasoning Model Improvements**](REASONING_MODEL_IMPROVEMENTS.md) - Details on the reasoning model enhancements
- [**Tabular Comparison Update**](TABULAR_COMPARISON_UPDATE.md) - Information about the tabular comparison feature

### 📋 Reference
- [**GenAI Case Clinical Trial Analysis Prompt**](GenAI_Case_Clinical_Trial_Analysis_PROMPT_ver1.00.docx.md) - Detailed prompt for clinical trial analysis

## 🔍 Quick Start

1. **Basic Usage (No MCP Required)**
   ```bash
   # Set up environment
   python main.py setup
   
   # Start the UI
   python main.py ui
   ```

2. **Advanced Usage (With MCP)**
   ```bash
   # Set up environment
   python main.py setup
   
   # Install MCP
   pip install mcp
   
   # Start MCP server (in separate terminal)
   python src/mcp/clinical_trial_mcp_server.py
   
   # Start the UI
   python main.py ui
   ```

## 🆘 Getting Help

If you encounter issues:

1. Check the relevant troubleshooting guide
2. Review error messages in the console
3. Verify your OpenAI API key is correctly set up
4. Try the basic functionality without MCP first

Remember that the MCP functionality is optional - the core clinical trial analysis features work perfectly without it. 