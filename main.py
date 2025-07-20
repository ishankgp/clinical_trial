#!/usr/bin/env python3
"""
Clinical Trial Analysis System - Main Entry Point
A comprehensive system for analyzing clinical trials using AI models
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Main entry point for the clinical trial analysis system"""
    print("🏥 Clinical Trial Analysis System")
    print("=" * 50)
    print("Available commands:")
    print("1. python main.py setup       - Initial setup and configuration")
    print("2. python main.py ui          - Start the web interface")
    print("3. python main.py process     - Process all trials")
    print("4. python main.py populate    - Populate database with trials")
    print("5. python main.py test        - Run tests")
    print("6. python main.py test-reasoning - Test reasoning models")
    print("7. python main.py test-mcp-query - Test MCP server with reasoning query")
    print("8. python main.py test-mcp-chat - Test MCP chat with reasoning models")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Please specify a command. Example: python main.py ui")
        return
    
    command = sys.argv[1].lower()
    
    if command == "setup":
        from setup_env import main as setup_env
        setup_env()
    elif command == "ui":
        from ui.run_ui import main as run_ui
        run_ui()
    elif command == "process":
        from analysis.process_all_trials import main as process_trials
        process_trials()
    elif command == "populate":
        from database.populate_clinical_trials import main as populate_db
        populate_db()
    elif command == "test":
        import subprocess
        subprocess.run([sys.executable, "-m", "pytest", "tests/"])
    elif command == "test-reasoning":
        from test_reasoning_models import test_reasoning_models
        test_reasoning_models()
    elif command == "test-mcp-query":
        import asyncio
        from test_mcp_reasoning_query import main as test_mcp_query
        asyncio.run(test_mcp_query())
    elif command == "test-mcp-chat":
        from test_mcp_chat_reasoning import main as test_mcp_chat
        test_mcp_chat()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: setup, ui, process, populate, test, test-reasoning, test-mcp-query, test-mcp-chat")

if __name__ == "__main__":
    main() 