#!/usr/bin/env python3
"""
Launcher script for Clinical Trial Analysis Tool UI
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import streamlit
        import plotly
        import pandas
        import openai
        from dotenv import load_dotenv
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements_ui.txt")
        return False

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists(".env"):
        print("❌ .env file not found!")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your-api-key-here")
        return False
    return True

def main():
    """Main launcher function"""
    print("🏥 Clinical Trial Analysis Tool - UI Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check environment file
    if not check_env_file():
        return
    
    # Check if app.py exists in the ui directory
    app_path = Path(__file__).parent / "app.py"
    if not app_path.exists():
        print("❌ app.py not found!")
        print(f"Expected location: {app_path}")
        print("Please ensure the Streamlit app file exists.")
        return
    
    print("✅ All checks passed!")
    print("🚀 Starting Streamlit application...")
    print("📱 The UI will open in your default web browser")
    print("🔗 If it doesn't open automatically, go to: http://localhost:8502")
    print("\nPress Ctrl+C to stop the application")
    print("-" * 50)
    
    try:
        # Run Streamlit app from the ui directory with auto port selection
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", "8502"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")

if __name__ == "__main__":
    main() 