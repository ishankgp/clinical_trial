#!/usr/bin/env python3
"""
Run MCP Chat Interface
This script ensures the proper Python path is set before running the MCP chat interface
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import and run the main function from the chat MCP module
from src.mcp.clinical_trial_chat_mcp import main

if __name__ == "__main__":
    main() 