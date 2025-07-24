# MCP Setup & Usage Guide

## 🤖 What is MCP?

MCP (Model Context Protocol) is an advanced feature that enables natural language querying across multiple clinical trials. It provides intelligent analysis, comparison capabilities, and advanced search functionality.

## 🚀 Key Features

- **Multi-Trial Storage**: Store and query across multiple clinical trials
- **Natural Language Search**: Ask questions in plain English
- **Advanced Filtering**: Search by drug, indication, phase, status, etc.
- **Trial Comparison**: Compare multiple trials side-by-side
- **Statistical Analysis**: Generate insights across trial databases
- **Data Export**: Export results in CSV/JSON formats

## ⚠️ Current Status

The MCP functionality is **optional** and not required for basic clinical trial analysis. The main UI will work perfectly without it.

## 🚀 Basic Usage (No MCP Required)

You can use all the core features without MCP:

- ✅ **Single Trial Analysis**: Analyze individual trials with AI models
- ✅ **Model Comparison**: Compare different AI models
- ✅ **Results History**: View and export analysis results
- ✅ **Database Management**: Store and retrieve trial data

## 🔧 Setting Up MCP (Optional)

If you want to enable the advanced MCP chat functionality:

### **1. Install MCP Dependencies**
```bash
pip install mcp
```

### **2. Start MCP Server**
```bash
# Run the MCP server in a separate terminal
python src/mcp/clinical_trial_mcp_server.py
```

### **3. Configure MCP Client**
The MCP chat interface will automatically connect to the server when available.

## 📋 Available MCP Tools

When MCP is properly configured, you get access to these tools:

### **Core Storage & Analysis**
1. **`store_trial`**: Store and analyze clinical trials
2. **`analyze_trial_with_model`**: Analyze with specific models
3. **`get_available_columns`**: List database schema

### **Advanced Search**
4. **`search_trials`**: Flexible search with filters
5. **`smart_search`**: Natural language search
6. **`get_trials_by_drug`**: Find trials by drug name
7. **`get_trials_by_indication`**: Find trials by disease

### **Analysis & Comparison**
8. **`get_trial_details`**: Detailed trial information
9. **`compare_trials`**: Side-by-side comparison
10. **`get_trial_statistics`**: Statistical analysis

### **Data Export**
11. **`export_trials`**: Export to CSV/JSON formats

## 🎯 Example MCP Queries

```
"Find all diabetes trials with semaglutide"
"Show me phase 3 recruiting trials"
"What trials are there for cancer treatment?"
"Compare NCT07046273 and NCT04895709"
"Generate statistics grouped by trial phase"
"Export all phase 3 trials to CSV"
```

## 🔍 Troubleshooting

### **MCP Module Not Found**
If you see "MCP Chat module not available":
- This is normal if MCP is not installed
- The basic functionality will still work
- Install MCP if you want advanced features

### **MCP Server Connection Issues**
If MCP is installed but not working:
1. Check if the MCP server is running
2. Verify the server port (default: 3000)
3. Check firewall settings
4. Review server logs for errors

### **Performance Issues**
- MCP queries can be slower than basic analysis
- Large datasets may take time to process
- Consider using filters to narrow down results

## 🏥 Recommended Workflow

### **For New Users**
1. Start with basic single trial analysis
2. Learn the interface and features
3. Set up MCP later if needed

### **For Advanced Users**
1. Set up MCP server
2. Use natural language queries
3. Leverage advanced analytics

### **For Researchers**
1. Use both basic and MCP features
2. Export data for further analysis
3. Compare multiple trials efficiently

## 📊 Feature Comparison

| Feature | Basic UI | With MCP |
|---------|----------|----------|
| Single Trial Analysis | ✅ | ✅ |
| Model Comparison | ✅ | ✅ |
| Results History | ✅ | ✅ |
| Natural Language Search | ❌ | ✅ |
| Multi-Trial Comparison | ❌ | ✅ |
| Advanced Statistics | ❌ | ✅ |
| Data Export | Basic | Advanced |

## 🎉 Getting Started

### **Quick Start (No MCP)**
```bash
# 1. Set up environment
python main.py setup

# 2. Start the UI
python main.py ui

# 3. Begin analyzing trials!
```

### **Full Setup (With MCP)**
```bash
# 1. Set up environment
python main.py setup

# 2. Install MCP
pip install mcp

# 3. Start MCP server (in separate terminal)
python src/mcp/clinical_trial_mcp_server.py

# 4. Start the UI
python main.py ui

# 5. Use advanced features!
```

## 🏗️ Technical Architecture

```
User Query → Chat Interface → OpenAI LLM → Function Calling → MCP Server → Database → Results
```

### **Data Flow**
1. **User Input**: Natural language or structured query
2. **LLM Processing**: OpenAI interprets intent and selects tools
3. **MCP Execution**: Server processes request using appropriate tools
4. **Database Query**: SQLite database returns relevant trials
5. **Result Formatting**: Results formatted as requested
6. **Response**: Comprehensive answer with context

## 🔧 Model Integration

- **GPT-4o**: Fast, JSON schema support
- **GPT-4o-mini**: Cost-effective analysis
- **o4-mini**: Reasoning-optimized
- **GPT-4**: Comprehensive analysis

## 🆘 Support

### **Basic Issues**
- Check the main README.md
- Review error messages in the UI
- Verify your OpenAI API key

### **MCP Issues**
- Check MCP server logs
- Verify network connectivity
- Review MCP documentation

### **Getting Help**
- Check the documentation in `docs/`
- Review error logs
- Test with simple queries first

---

**Remember: MCP is optional! The basic clinical trial analysis system works perfectly without it.** 🚀🏥📊 