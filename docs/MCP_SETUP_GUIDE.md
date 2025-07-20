# MCP Setup Guide

## 🤖 What is MCP?

MCP (Model Context Protocol) is an advanced feature that allows you to query across multiple clinical trials using natural language. It provides intelligent analysis and comparison capabilities.

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
python src/mcp/clinical_trial_mcp_server_fixed.py
```

### **3. Configure MCP Client**
The MCP chat interface will automatically connect to the server when available.

## 📋 MCP Features

When MCP is properly configured, you get access to:

- 🔍 **Natural Language Search**: "Find all diabetes trials with semaglutide"
- 📊 **Trial Comparison**: "Compare NCT03778931 and NCT04516746"
- 📈 **Advanced Statistics**: "Show me statistics grouped by trial phase"
- 💊 **Drug Analysis**: "Find trials using checkpoint inhibitors"
- 📤 **Data Export**: "Export all Phase 3 trials to CSV"

## 🎯 Example MCP Queries

```
"Find all trials for diabetes treatment"
"Compare the efficacy of different cancer drugs"
"Show me Phase 3 trials with more than 1000 patients"
"What are the most common biomarkers in oncology trials?"
"Export all trials from 2023 to Excel"
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
python src/mcp/clinical_trial_mcp_server_fixed.py

# 4. Start the UI
python main.py ui

# 5. Use advanced features!
```

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