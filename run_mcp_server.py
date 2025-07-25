#!/usr/bin/env python3
"""
Run MCP Server
This script ensures the proper Python path is set before running the MCP server
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import and run the main function from the MCP server module
from src.mcp.clinical_trial_mcp_server import main

if __name__ == "__main__":
    main() 