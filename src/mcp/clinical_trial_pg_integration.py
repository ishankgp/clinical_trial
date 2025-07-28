#!/usr/bin/env python3
"""
PostgreSQL Integration for Clinical Trial MCP
Integrates the Node.js MCP PostgreSQL server with the Python codebase
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
import time

# Add the project root to the Python path for proper imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_nodejs_installation():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Node.js is installed: {result.stdout.strip()}")
            return True
        else:
            logger.error("Node.js is not installed or not in PATH")
            return False
    except Exception as e:
        logger.error(f"Error checking Node.js installation: {e}")
        return False

def check_npm_installation():
    """Check if npm is installed"""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"npm is installed: {result.stdout.strip()}")
            return True
        else:
            logger.error("npm is not installed or not in PATH")
            return False
    except Exception as e:
        logger.error(f"Error checking npm installation: {e}")
        return False

def start_pg_mcp_server():
    """Start the PostgreSQL MCP server"""
    try:
        logger.info("Starting PostgreSQL MCP server...")
        
        # Use subprocess.Popen to start the server in the background
        process = subprocess.Popen(
            ['npm', 'run', 'pg-mcp'],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for the server to start
        time.sleep(2)
        
        # Check if the process is still running
        if process.poll() is None:
            logger.info("PostgreSQL MCP server started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Failed to start PostgreSQL MCP server: {stderr}")
            return None
    except Exception as e:
        logger.error(f"Error starting PostgreSQL MCP server: {e}")
        return None

def stop_pg_mcp_server(process):
    """Stop the PostgreSQL MCP server"""
    if process:
        try:
            logger.info("Stopping PostgreSQL MCP server...")
            process.terminate()
            process.wait(timeout=5)
            logger.info("PostgreSQL MCP server stopped")
        except Exception as e:
            logger.error(f"Error stopping PostgreSQL MCP server: {e}")
            process.kill()

def configure_claude_desktop():
    """Configure Claude Desktop to use the PostgreSQL MCP server"""
    try:
        # Get the home directory
        home_dir = os.path.expanduser("~")
        claude_config_dir = os.path.join(home_dir, ".claude")
        
        # Create the directory if it doesn't exist
        os.makedirs(claude_config_dir, exist_ok=True)
        
        # Path to the Claude Desktop config file
        config_file = os.path.join(claude_config_dir, "claude_desktop_config.json")
        
        # Read the example config
        with open(os.path.join(project_root, "mcp-postgres", "claude_desktop_config.json"), "r") as f:
            config = json.load(f)
        
        # Write the config file
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"Claude Desktop configuration written to {config_file}")
        logger.info("Please update the database credentials in the config file")
        return True
    except Exception as e:
        logger.error(f"Error configuring Claude Desktop: {e}")
        return False

def configure_cursor():
    """Configure Cursor to use the PostgreSQL MCP server"""
    try:
        # Get the Cursor settings file path (platform-dependent)
        settings_dir = None
        if sys.platform == "win32":
            settings_dir = os.path.join(os.environ.get("APPDATA", ""), "Code", "User")
        elif sys.platform == "darwin":
            settings_dir = os.path.join(home_dir, "Library", "Application Support", "Code", "User")
        else:  # Linux
            settings_dir = os.path.join(home_dir, ".config", "Code", "User")
            
        if not settings_dir or not os.path.exists(settings_dir):
            logger.warning(f"Cursor settings directory not found at {settings_dir}")
            return False
            
        # Path to the settings.json file
        settings_file = os.path.join(settings_dir, "settings.json")
        
        # Read the example config
        with open(os.path.join(project_root, "mcp-postgres", "cursor_settings.json"), "r") as f:
            pg_config = json.load(f)
        
        # Read existing settings if the file exists
        existing_settings = {}
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r") as f:
                    existing_settings = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Error parsing existing settings file {settings_file}, creating new file")
        
        # Merge the configs
        if "mcp" not in existing_settings:
            existing_settings["mcp"] = {}
            
        if "servers" not in existing_settings["mcp"]:
            existing_settings["mcp"]["servers"] = {}
            
        existing_settings["mcp"]["servers"]["clinical-trials-pg"] = pg_config["mcp"]["servers"]["clinical-trials-pg"]
        
        # Write the settings file
        with open(settings_file, "w") as f:
            json.dump(existing_settings, f, indent=2)
            
        logger.info(f"Cursor configuration written to {settings_file}")
        logger.info("Please update the database credentials in the settings file")
        return True
    except Exception as e:
        logger.error(f"Error configuring Cursor: {e}")
        return False

def main():
    """Main function"""
    print("=" * 80)
    print("PostgreSQL Integration for Clinical Trial MCP")
    print("=" * 80)
    
    # Check Node.js and npm installation
    if not check_nodejs_installation() or not check_npm_installation():
        print("Please install Node.js and npm to use the PostgreSQL MCP server")
        return
    
    # Menu
    while True:
        print("\nOptions:")
        print("1. Start PostgreSQL MCP server")
        print("2. Configure Claude Desktop")
        print("3. Configure Cursor")
        print("4. Test PostgreSQL connection")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == "1":
            process = start_pg_mcp_server()
            if process:
                print("PostgreSQL MCP server is running. Press Enter to stop it.")
                input()
                stop_pg_mcp_server(process)
        elif choice == "2":
            configure_claude_desktop()
        elif choice == "3":
            configure_cursor()
        elif choice == "4":
            subprocess.run(['npm', 'run', 'test-connection'], cwd=project_root)
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 