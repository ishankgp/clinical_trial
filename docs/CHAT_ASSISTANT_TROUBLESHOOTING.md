# Chat Assistant Troubleshooting Guide

## 🤖 Overview

The Chat Assistant tab provides advanced natural language querying capabilities for clinical trials using the Model Context Protocol (MCP). This guide helps you resolve issues and get the chat functionality working.

## 🚨 Common Issues

### **1. "MCP Chat module is not available"**

**Symptoms:**
- Red error message in Chat Assistant tab
- "MCP Chat module not available" displayed
- Chat interface not functional

**Causes:**
- MCP package not installed
- MCP server files missing
- Import path issues
- Python path problems

**Solutions:**

#### **A. Install MCP Package**
```bash
# Install the MCP package
pip install mcp
```

#### **B. Verify MCP Files**
Ensure these files exist:
```
src/mcp/
├── clinical_trial_mcp_server.py  # ✅ Required
├── clinical_trial_chat_mcp.py    # ✅ Required
└── __init__.py                   # ✅ Required
```

#### **C. Check Python Path**
```bash
# Test MCP import
python -c "import mcp; print('✅ MCP available')"
```

### **2. "Failed to initialize MCP chat assistant"**

**Symptoms:**
- Error during chat interface initialization
- MCP server connection issues
- Subprocess errors

**Causes:**
- MCP server not starting
- Port conflicts
- File path issues
- Missing dependencies

**Solutions:**

#### **A. Start MCP Server Manually**
```bash
# In a separate terminal
cd src/mcp
python clinical_trial_mcp_server.py
```

#### **B. Check Server Logs**
Look for error messages in the terminal where you started the MCP server.

#### **C. Verify Dependencies**
```bash
# Check if all required packages are installed
pip install -r requirements_ui.txt
pip list | grep -E "(mcp|openai|sqlite)"
```

### **3. Import Errors**

**Symptoms:**
- ModuleNotFoundError
- ImportError messages
- Path-related errors

**Causes:**
- Incorrect import paths
- Missing __init__.py files
- Python path issues

**Solutions:**

#### **A. Fix Import Paths**
The UI app uses dynamic path resolution:
```python
# Automatically adds MCP path to sys.path
mcp_path = os.path.join(os.path.dirname(__file__), '..', 'mcp')
sys.path.append(mcp_path)
```

#### **B. Check File Structure**
Ensure the correct file structure:
```
clinical_trial/
├── src/
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── clinical_trial_mcp_server.py
│   │   └── clinical_trial_chat_mcp.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── mcp_checker.py
│   └── ui/
│       └── app.py
```

## 🔧 Step-by-Step Setup

### **Phase 1: Basic Setup**

1. **Install MCP Package**
   ```bash
   pip install mcp
   ```

2. **Verify Installation**
   ```bash
   python -c "import mcp; print('MCP version:', mcp.__version__)"
   ```

3. **Check File Structure**
   ```bash
   ls src/mcp/
   # Should show:
   # clinical_trial_mcp_server.py
   # clinical_trial_chat_mcp.py
   # __init__.py
   ```

### **Phase 2: Test MCP Server**

1. **Start MCP Server**
   ```bash
   cd src/mcp
   python clinical_trial_mcp_server.py
   ```

2. **Check Server Output**
   - Look for "Server started" messages
   - Check for any error messages
   - Verify port availability

3. **Test Server Response**
   - Server should respond to initialization
   - No immediate crashes or errors

### **Phase 3: Test Chat Interface**

1. **Start UI**
   ```bash
   python main.py ui
   ```

2. **Navigate to Chat Assistant**
   - Click on "Chat Assistant" tab
   - Check status messages

3. **Test Chat Functionality**
   - Try a simple query like "Find diabetes trials"
   - Check for response
   - Verify error handling

## 📊 Status Indicators

### **✅ Working Status**
- Green "✅ MCP Chat Available" message
- "Advanced chat functionality is ready to use!"
- Chat input field is active
- Example queries work

### **⚠️ Partial Issues**
- Yellow warning messages
- Some features working, others not
- Intermittent errors

### **❌ Not Working**
- Red error messages
- "MCP Chat module not available"
- No chat interface
- Import errors

## 🛠️ Advanced Troubleshooting

### **1. Debug MCP Server**

**Enable Debug Logging:**
```python
# In clinical_trial_mcp_server.py
logging.basicConfig(level=logging.DEBUG)
```

**Check Server Process:**
```bash
# Check if MCP server is running
ps aux | grep clinical_trial_mcp_server
# On Windows
tasklist | findstr python
```

### **2. Debug Chat Interface**

**Enable Verbose Output:**
```python
# In clinical_trial_chat_mcp.py
logging.basicConfig(level=logging.DEBUG)
```

**Test Individual Components:**
```bash
# Test MCP chat module directly
python -c "
import sys
sys.path.append('src/mcp')
from clinical_trial_chat_mcp import ClinicalTrialChatMCP
print('Chat module imported successfully')
"
```

### **3. Network and Port Issues**

**Check Port Availability:**
```bash
# Check if port 3000 is available (default MCP port)
# On Linux/Mac
netstat -an | grep 3000
# On Windows
netstat -an | findstr 3000
```

**Firewall Issues:**
- Ensure firewall allows local connections
- Check antivirus software blocking connections
- Try temporarily disabling firewall for testing

### **4. Database Issues**

**Verify Database Access:**
```bash
# Test database connection
python -c "
from src.database.clinical_trial_database import ClinicalTrialDatabase
db = ClinicalTrialDatabase()
print('Database connection successful')
"
```

## 🎯 Quick Fixes

### **Immediate Solutions:**

1. **Restart Everything**
   ```bash
   # Stop all processes (Linux/Mac)
   pkill -f "python.*main.py"
   pkill -f "python.*mcp"
   
   # On Windows
   taskkill /F /IM python.exe
   
   # Restart UI
   python main.py ui
   ```

2. **Reinstall MCP**
   ```bash
   pip uninstall mcp -y
   pip install mcp
   ```

3. **Clear Cache**
   ```bash
   # Remove Python cache
   find . -name "__pycache__" -type d -exec rm -rf {} +
   # On Windows
   for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
   ```

4. **Check Environment**
   ```bash
   # Verify Python environment
   python --version
   pip list | grep mcp
   ```

## 📋 Testing Checklist

### **Before Testing:**
- [ ] MCP package installed
- [ ] All MCP files present
- [ ] Database accessible
- [ ] OpenAI API key configured
- [ ] No port conflicts

### **During Testing:**
- [ ] UI starts without errors
- [ ] Chat Assistant tab accessible
- [ ] Status messages clear
- [ ] Chat input functional
- [ ] Responses received

### **After Testing:**
- [ ] Chat history maintained
- [ ] Error handling works
- [ ] Performance acceptable
- [ ] No memory leaks

## 🎉 Success Indicators

**When everything is working correctly:**

- ✅ **Chat Assistant tab shows green status**
- ✅ **Chat input field is active and responsive**
- ✅ **Natural language queries work**
- ✅ **Responses are relevant and helpful**
- ✅ **No error messages in console**
- ✅ **MCP server running in background**

**Example working query:**
```
User: "Find all diabetes trials with semaglutide"
Assistant: "I found 3 diabetes trials with semaglutide..."
```

## 💡 Pro Tips

1. **Keep MCP Server Running**: Start it in a separate terminal and keep it running
2. **Monitor Logs**: Watch for error messages during development
3. **Test Incrementally**: Start with simple queries before complex ones
4. **Use Debug Mode**: Enable debug logging when troubleshooting
5. **Check Dependencies**: Ensure all required packages are up to date

---

**Remember: MCP Chat is an advanced feature. The basic clinical trial analysis functionality works perfectly without it!** 🚀🏥📊 