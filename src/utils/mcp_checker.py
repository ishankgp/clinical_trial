#!/usr/bin/env python3
"""
MCP Availability Checker
Checks if MCP dependencies are available and provides helpful feedback
"""

import os
import sys
from pathlib import Path

def check_mcp_availability():
    """Check if MCP is available and return status information"""
    
    status = {
        "mcp_package": False,
        "mcp_server_file": False,
        "mcp_chat_file": False,
        "python_path": False,
        "issues": [],
        "recommendations": []
    }
    
    # Check if MCP package is installed
    try:
        import mcp
        status["mcp_package"] = True
    except ImportError:
        status["issues"].append("MCP package not installed")
        status["recommendations"].append("Install MCP: pip install mcp")
    
    # Check if MCP server file exists
    server_path = Path(__file__).parent.parent / "mcp" / "clinical_trial_mcp_server_fixed.py"
    if server_path.exists():
        status["mcp_server_file"] = True
    else:
        status["issues"].append("MCP server file not found")
        status["recommendations"].append("Ensure clinical_trial_mcp_server_fixed.py exists")
    
    # Check if MCP chat file exists
    chat_path = Path(__file__).parent.parent / "mcp" / "clinical_trial_chat_mcp.py"
    if chat_path.exists():
        status["mcp_chat_file"] = True
    else:
        status["issues"].append("MCP chat file not found")
        status["recommendations"].append("Ensure clinical_trial_chat_mcp.py exists")
    
    # Check Python path
    if sys.executable:
        status["python_path"] = True
    else:
        status["issues"].append("Python executable not found")
        status["recommendations"].append("Check Python installation")
    
    # Determine overall availability
    status["available"] = all([
        status["mcp_package"],
        status["mcp_server_file"],
        status["mcp_chat_file"],
        status["python_path"]
    ])
    
    return status

def get_mcp_status_message():
    """Get a user-friendly status message about MCP availability"""
    
    status = check_mcp_availability()
    
    if status["available"]:
        return {
            "type": "success",
            "title": "✅ MCP Chat Available",
            "message": "Advanced chat functionality is ready to use!",
            "details": "All MCP components are properly configured."
        }
    else:
        return {
            "type": "warning",
            "title": "⚠️ MCP Chat Not Available",
            "message": "Advanced chat functionality requires additional setup.",
            "details": f"Issues found: {len(status['issues'])}",
            "issues": status["issues"],
            "recommendations": status["recommendations"]
        }

def get_mcp_setup_instructions():
    """Get step-by-step setup instructions for MCP"""
    
    return {
        "title": "🔧 MCP Setup Instructions",
        "steps": [
            {
                "step": 1,
                "title": "Install MCP Package",
                "command": "pip install mcp",
                "description": "Install the Model Context Protocol package"
            },
            {
                "step": 2,
                "title": "Verify Files",
                "description": "Ensure MCP server and chat files exist in src/mcp/"
            },
            {
                "step": 3,
                "title": "Start MCP Server",
                "command": "python src/mcp/clinical_trial_mcp_server_fixed.py",
                "description": "Run the MCP server in a separate terminal"
            },
            {
                "step": 4,
                "title": "Test Chat",
                "description": "Try the chat functionality in the UI"
            }
        ],
        "note": "MCP is optional - basic functionality works without it!"
    } 