#!/usr/bin/env python3
"""
Clinical Trial MCP Server
=========================

This module implements a Model Context Protocol (MCP) server that exposes clinical trial 
database operations as tools for AI chat interfaces. The server acts as a bridge between 
AI models and the clinical trial database, allowing natural language queries and 
automated data processing.

Key Features:
- Store and analyze clinical trials from ClinicalTrials.gov
- Search trials with natural language and structured filters
- Compare multiple trials side by side
- Generate statistics and reports
- Export data in various formats
- Smart search with natural language processing

Architecture:
- Uses MCP protocol for standardized AI tool integration
- Integrates with SQLite database for data persistence
- Supports multiple AI models for trial analysis
- Provides both structured and natural language interfaces
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime
import os
from pathlib import Path
import sqlite3
import pandas as pd

# MCP (Model Context Protocol) imports - Core framework for AI tool integration
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)

# Import our custom database and analysis modules
from ..database.clinical_trial_database import ClinicalTrialDatabase
from ..analysis.clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning
from ..analysis.clinical_trial_analyzer_llm import ClinicalTrialAnalyzerLLM

# Configure logging for debugging and monitoring
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalTrialMCPServer:
    """
    MCP Server for clinical trial data management and querying
    
    This class implements the core MCP server functionality, providing tools that AI models
    can use to interact with clinical trial data. It handles:
    - Tool registration and management
    - Database operations
    - Trial analysis and processing
    - Data formatting and export
    - Natural language query processing
    """
    
    def __init__(self):
        """
        Initialize the MCP server with database connection and tool registration
        
        Sets up:
        - MCP server instance with unique identifier
        - Database connection for clinical trial data
        - Cache for AI model analyzers (to avoid re-initialization)
        - Tool registration for all available operations
        """
        # Create MCP server instance with unique name
        self.server = Server("clinical-trial-mcp-server")
        
        # Initialize database connection for clinical trial data
        self.db = ClinicalTrialDatabase()
        
        # Cache for AI model analyzers to avoid re-initialization
        # Key: model_name, Value: analyzer instance
        self.analyzers = {}
        
        # Register all available tools with the MCP server
        self._register_tools()
        
    def _register_tools(self):
        """
        Register all available tools with the MCP server
        
        This method defines all the tools that AI models can use to interact with
        clinical trial data. Each tool has:
        - A unique name
        - A description of its functionality
        - An input schema defining required and optional parameters
        - A corresponding implementation method
        
        Tools are categorized into:
        - Data Management: store_trial, search_trials, get_trial_details
        - Analysis: compare_trials, get_trial_statistics, analyze_trial_with_model
        - Export: export_trials, get_available_columns
        - Specialized Queries: get_trials_by_drug, get_trials_by_indication, smart_search
        """
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """
            List all available tools for AI models
            
            This is called by AI clients to discover what tools are available.
            Returns a structured list of all tools with their schemas.
            """
            return ListToolsResult(
                tools=[
                    # Tool 1: Store and analyze clinical trials
                    Tool(
                        name="store_trial",
                        description="Store a clinical trial from JSON file or NCT ID",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "nct_id": {"type": "string", "description": "NCT ID of the trial"},
                                "json_file_path": {"type": "string", "description": "Path to JSON file (optional)"},
                                "analyze_with_model": {"type": "string", "enum": ["o3", "o3-mini", "gpt-4o", "gpt-4o-mini", "gpt-4", "llm"], "default": "o3-mini", "description": "Model to use for analysis (o3/o3-mini are reasoning models)"},
                                "force_reanalyze": {"type": "boolean", "default": False, "description": "Force reanalysis even if trial exists"}
                            },
                            "required": ["nct_id"]
                        }
                    ),
                    
                    # Tool 2: Search trials with flexible filters
                    Tool(
                        name="search_trials",
                        description="Search clinical trials with flexible filters",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Natural language search query"},
                                "filters": {
                                    "type": "object",
                                    "properties": {
                                        "primary_drug": {"type": "string"},
                                        "indication": {"type": "string"},
                                        "trial_phase": {"type": "string"},
                                        "trial_status": {"type": "string"},
                                        "sponsor": {"type": "string"},
                                        "line_of_therapy": {"type": "string"},
                                        "biomarker": {"type": "string"},
                                        "enrollment_min": {"type": "integer"},
                                        "enrollment_max": {"type": "integer"},
                                        "start_date_from": {"type": "string", "description": "Start date from (YYYY-MM-DD)"},
                                        "start_date_to": {"type": "string", "description": "Start date to (YYYY-MM-DD)"}
                                    }
                                },
                                "limit": {"type": "integer", "default": 50},
                                "format": {"type": "string", "enum": ["table", "json", "summary"], "default": "table"}
                            }
                        }
                    ),
                    
                    # Tool 3: Get detailed trial information
                    Tool(
                        name="get_trial_details",
                        description="Get detailed information about a specific trial",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "nct_id": {"type": "string", "description": "NCT ID of the trial"},
                                "include_raw_data": {"type": "boolean", "default": False, "description": "Include raw JSON data"}
                            },
                            "required": ["nct_id"]
                        }
                    ),
                    
                    # Tool 4: Compare multiple trials
                    Tool(
                        name="compare_trials",
                        description="Compare multiple clinical trials side by side",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "nct_ids": {"type": "array", "items": {"type": "string"}, "description": "List of NCT IDs to compare"},
                                "fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to compare (default: all)"},
                                "format": {"type": "string", "enum": ["table", "json"], "default": "table"}
                            },
                            "required": ["nct_ids"]
                        }
                    ),
                    
                    # Tool 5: Get trial statistics
                    Tool(
                        name="get_trial_statistics",
                        description="Get statistical information about stored trials",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "group_by": {"type": "string", "enum": ["phase", "status", "sponsor", "indication", "primary_drug"], "default": "phase"},
                                "include_charts": {"type": "boolean", "default": True}
                            }
                        }
                    ),
                    
                    # Tool 6: Analyze trial with specific model
                    Tool(
                        name="analyze_trial_with_model",
                        description="Analyze a trial with a specific model and store results",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "nct_id": {"type": "string", "description": "NCT ID of the trial"},
                                "model": {"type": "string", "enum": ["o3", "o3-mini", "gpt-4o", "gpt-4o-mini", "gpt-4", "llm"], "default": "o3-mini"},
                                "json_file_path": {"type": "string", "description": "Path to JSON file (optional)"}
                            },
                            "required": ["nct_id", "model"]
                        }
                    ),
                    
                    # Tool 7: Get database schema information
                    Tool(
                        name="get_available_columns",
                        description="Get list of available columns in the database",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "table": {"type": "string", "enum": ["clinical_trials", "drug_info", "clinical_info", "biomarker_info"], "default": "clinical_trials"}
                            }
                        }
                    ),
                    
                    # Tool 8: Export trial data
                    Tool(
                        name="export_trials",
                        description="Export trials to CSV or JSON format",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "format": {"type": "string", "enum": ["csv", "json"], "default": "csv"},
                                "filters": {"type": "object", "description": "Optional filters to apply"},
                                "filename": {"type": "string", "description": "Output filename"}
                            }
                        }
                    ),
                    
                    # Tool 9: Find trials by drug
                    Tool(
                        name="get_trials_by_drug",
                        description="Find all trials for a specific drug",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "drug_name": {"type": "string", "description": "Name of the drug"},
                                "include_similar": {"type": "boolean", "default": True, "description": "Include similar drug names"},
                                "limit": {"type": "integer", "default": 20}
                            },
                            "required": ["drug_name"]
                        }
                    ),
                    
                    # Tool 10: Find trials by indication
                    Tool(
                        name="get_trials_by_indication",
                        description="Find all trials for a specific indication",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "indication": {"type": "string", "description": "Disease indication"},
                                "include_similar": {"type": "boolean", "default": True, "description": "Include similar indications"},
                                "limit": {"type": "integer", "default": 20}
                            },
                            "required": ["indication"]
                        }
                    ),
                    
                    # Tool 11: Smart natural language search
                    Tool(
                        name="smart_search",
                        description="Intelligent search that interprets natural language queries",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Natural language query"},
                                "limit": {"type": "integer", "default": 10},
                                "format": {"type": "string", "enum": ["table", "json", "summary"], "default": "table"}
                            },
                            "required": ["query"]
                        }
                    ),
                    
                    # Tool 12: Advanced reasoning-based query (NEW)
                    Tool(
                        name="reasoning_query",
                        description="Advanced natural language query using reasoning models for complex clinical trial questions",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Complex natural language query requiring reasoning"},
                                "reasoning_model": {"type": "string", "enum": ["o3", "o3-mini"], "default": "o3-mini", "description": "Reasoning model to use for query interpretation"},
                                "include_analysis": {"type": "boolean", "default": True, "description": "Include AI analysis and insights"},
                                "limit": {"type": "integer", "default": 20},
                                "format": {"type": "string", "enum": ["detailed", "summary", "analysis"], "default": "detailed"}
                            },
                            "required": ["query"]
                        }
                    ),
                    
                    # Tool 13: Comparative analysis (NEW)
                    Tool(
                        name="compare_analysis",
                        description="Compare trials based on natural language criteria with AI-powered insights",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "comparison_criteria": {"type": "string", "description": "Natural language description of what to compare"},
                                "trial_ids": {"type": "array", "items": {"type": "string"}, "description": "Optional specific NCT IDs to compare"},
                                "auto_find_similar": {"type": "boolean", "default": True, "description": "Automatically find similar trials if no IDs provided"},
                                "analysis_depth": {"type": "string", "enum": ["basic", "detailed", "expert"], "default": "detailed"}
                            },
                            "required": ["comparison_criteria"]
                        }
                    ),
                    
                    # Tool 14: Trend analysis (NEW)
                    Tool(
                        name="trend_analysis",
                        description="Analyze trends and patterns in clinical trials using natural language queries",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "trend_query": {"type": "string", "description": "Natural language description of trends to analyze"},
                                "time_period": {"type": "string", "description": "Time period for analysis (e.g., 'last 5 years', '2020-2024')"},
                                "group_by": {"type": "string", "enum": ["drug", "indication", "phase", "sponsor", "geography"], "default": "drug"},
                                "include_insights": {"type": "boolean", "default": True}
                            },
                            "required": ["trend_query"]
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """
            Handle tool execution requests from AI models
            
            This is the main dispatcher that routes tool calls to their appropriate
            implementation methods. It includes error handling and logging.
            
            Args:
                name: Name of the tool to execute
                arguments: Dictionary of arguments for the tool
                
            Returns:
                CallToolResult: Structured result with text content
            """
            try:
                # Route tool calls to appropriate implementation methods
                if name == "store_trial":
                    result = await self._store_trial(arguments)
                elif name == "search_trials":
                    result = await self._search_trials(arguments)
                elif name == "get_trial_details":
                    result = await self._get_trial_details(arguments)
                elif name == "compare_trials":
                    result = await self._compare_trials(arguments)
                elif name == "get_trial_statistics":
                    result = await self._get_trial_statistics(arguments)
                elif name == "analyze_trial_with_model":
                    result = await self._analyze_trial_with_model(arguments)
                elif name == "get_available_columns":
                    result = await self._get_available_columns(arguments)
                elif name == "export_trials":
                    result = await self._export_trials(arguments)
                elif name == "get_trials_by_drug":
                    result = await self._get_trials_by_drug(arguments)
                elif name == "get_trials_by_indication":
                    result = await self._get_trials_by_indication(arguments)
                elif name == "smart_search":
                    result = await self._smart_search(arguments)
                elif name == "reasoning_query":
                    result = await self._reasoning_query(arguments)
                elif name == "compare_analysis":
                    result = await self._compare_analysis(arguments)
                elif name == "trend_analysis":
                    result = await self._trend_analysis(arguments)
                else:
                    # Handle unknown tools gracefully
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {name}")]
                    )
                
                # Return successful result
                return CallToolResult(content=[TextContent(type="text", text=result)])
                
            except Exception as e:
                # Log and return error information
                logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")]
                )
    
    async def _store_trial(self, arguments: Dict[str, Any]) -> str:
        """
        Store and analyze a clinical trial in the database
        
        This method handles the complete pipeline of:
        1. Checking if trial already exists
        2. Initializing appropriate AI analyzer
        3. Analyzing trial data with AI model
        4. Storing results in database
        
        Args:
            arguments: Dictionary containing:
                - nct_id: NCT ID of the trial
                - json_file_path: Optional path to JSON file
                - analyze_with_model: AI model to use for analysis
                - force_reanalyze: Whether to reanalyze existing trials
                
        Returns:
            str: Success/error message
        """
        # Extract parameters from arguments
        nct_id = arguments["nct_id"]
        json_file_path = arguments.get("json_file_path")
        analyze_with_model = arguments.get("analyze_with_model", "o3-mini")
        force_reanalyze = arguments.get("force_reanalyze", False)
        
        # Check if trial already exists in database
        existing_trial = self.db.get_trial_by_nct_id(nct_id)
        if existing_trial and not force_reanalyze:
            return f"Trial {nct_id} already exists in database. Use force_reanalyze=true to reanalyze."
        
        # Get or create AI analyzer instance (cached for performance)
        if analyze_with_model not in self.analyzers:
            # Get OpenAI API key from environment
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return "Error: OPENAI_API_KEY not found in environment"
            
            # Initialize appropriate analyzer based on model type
            if analyze_with_model == "llm":
                # Use LLM-based analyzer for simple extraction
                self.analyzers[analyze_with_model] = ClinicalTrialAnalyzerLLM(api_key)
            else:
                # Use reasoning-based analyzer for complex analysis
                self.analyzers[analyze_with_model] = ClinicalTrialAnalyzerReasoning(api_key, model=analyze_with_model)
        
        analyzer = self.analyzers[analyze_with_model]
        
        # Analyze the trial using AI model
        try:
            result = analyzer.analyze_trial(nct_id, json_file_path)
            if "error" in result:
                return f"Error analyzing trial {nct_id}: {result['error']}"
            
            # Store analyzed results in database with metadata
            success = self.db.store_trial_data(result, {
                "analysis_model": analyze_with_model,
                "analysis_timestamp": datetime.now().isoformat(),
                "source_file": json_file_path
            })
            
            if success:
                return f"✅ Successfully stored trial {nct_id} using {analyze_with_model} model"
            else:
                return f"❌ Failed to store trial {nct_id}"
                
        except Exception as e:
            return f"Error processing trial {nct_id}: {str(e)}"
    
    async def _search_trials(self, arguments: Dict[str, Any]) -> str:
        """
        Search clinical trials with flexible filters and natural language processing
        
        This method combines structured filters with natural language query processing
        to provide flexible search capabilities.
        
        Args:
            arguments: Dictionary containing:
                - query: Natural language search query
                - filters: Structured filters (drug, indication, phase, etc.)
                - limit: Maximum number of results
                - format: Output format (table, json, summary)
                
        Returns:
            str: Formatted search results
        """
        # Extract search parameters
        query = arguments.get("query", "")
        filters = arguments.get("filters", {})
        limit = arguments.get("limit", 50)
        format_type = arguments.get("format", "table")
        
        # Build search filters combining natural language and structured filters
        search_filters = {}
        
        # Process natural language query to extract structured filters
        if query:
            # Simple keyword matching for common terms
            if "diabetes" in query.lower():
                search_filters["indication"] = "diabetes"
            if "cancer" in query.lower():
                search_filters["indication"] = "cancer"
            if "phase" in query.lower():
                # Extract phase information from query
                if "1" in query:
                    search_filters["trial_phase"] = "PHASE1"
                elif "2" in query:
                    search_filters["trial_phase"] = "PHASE2"
                elif "3" in query:
                    search_filters["trial_phase"] = "PHASE3"
        
        # Merge with explicit filters (explicit filters take precedence)
        search_filters.update(filters)
        
        # Execute search against database
        results = self.db.search_trials(search_filters, limit)
        
        if not results:
            return "No trials found matching the criteria."
        
        # Format results based on requested format
        if format_type == "json":
            return json.dumps(results, indent=2)
        elif format_type == "summary":
            return self._format_summary(results)
        else:  # table format (default)
            return self._format_table(results)
    
    async def _get_trial_details(self, arguments: Dict[str, Any]) -> str:
        """
        Get detailed information about a specific clinical trial
        
        Retrieves comprehensive trial information and formats it for easy reading.
        Can include raw JSON data if requested.
        
        Args:
            arguments: Dictionary containing:
                - nct_id: NCT ID of the trial
                - include_raw_data: Whether to include raw JSON data
                
        Returns:
            str: Formatted trial details
        """
        nct_id = arguments["nct_id"]
        include_raw_data = arguments.get("include_raw_data", False)
        
        # Retrieve trial from database
        trial = self.db.get_trial_by_nct_id(nct_id)
        if not trial:
            return f"Trial {nct_id} not found in database."
        
        # Return raw JSON if requested
        if include_raw_data:
            return json.dumps(trial, indent=2)
        else:
            # Format as readable markdown text
            result = f"# Trial Details: {nct_id}\n\n"
            
            # Basic trial information section
            result += "## Basic Information\n"
            result += f"- **Trial Name:** {trial.get('trial_name', 'N/A')}\n"
            result += f"- **Phase:** {trial.get('trial_phase', 'N/A')}\n"
            result += f"- **Status:** {trial.get('trial_status', 'N/A')}\n"
            result += f"- **Enrollment:** {trial.get('patient_enrollment', 'N/A')}\n"
            result += f"- **Sponsor:** {trial.get('sponsor', 'N/A')}\n"
            
            # Drug information section
            result += "\n## Drug Information\n"
            result += f"- **Primary Drug:** {trial.get('primary_drug', 'N/A')}\n"
            result += f"- **MoA:** {trial.get('primary_drug_moa', 'N/A')}\n"
            result += f"- **Target:** {trial.get('primary_drug_target', 'N/A')}\n"
            result += f"- **Modality:** {trial.get('primary_drug_modality', 'N/A')}\n"
            result += f"- **Route:** {trial.get('primary_drug_roa', 'N/A')}\n"
            
            # Clinical information section
            result += "\n## Clinical Information\n"
            result += f"- **Indication:** {trial.get('indication', 'N/A')}\n"
            result += f"- **Line of Therapy:** {trial.get('line_of_therapy', 'N/A')}\n"
            result += f"- **Patient Population:** {trial.get('patient_population', 'N/A')}\n"
            
            return result
    
    async def _compare_trials(self, arguments: Dict[str, Any]) -> str:
        """
        Compare multiple clinical trials side by side
        
        Creates a comparison table or JSON output showing differences between trials
        across specified fields.
        
        Args:
            arguments: Dictionary containing:
                - nct_ids: List of NCT IDs to compare
                - fields: List of fields to compare (default: key fields)
                - format: Output format (table, json)
                
        Returns:
            str: Formatted comparison results
        """
        nct_ids = arguments["nct_ids"]
        fields = arguments.get("fields", [])
        format_type = arguments.get("format", "table")
        
        # Validate input
        if len(nct_ids) < 2:
            return "Please provide at least 2 NCT IDs to compare."
        
        # Retrieve trial data for all specified NCT IDs
        trials = []
        for nct_id in nct_ids:
            trial = self.db.get_trial_by_nct_id(nct_id)
            if trial:
                trials.append(trial)
            else:
                return f"Trial {nct_id} not found in database."
        
        # Return JSON format if requested
        if format_type == "json":
            return json.dumps(trials, indent=2)
        else:
            # Create comparison table
            if not fields:
                # Default fields for comparison
                fields = [
                    "nct_id", "trial_name", "trial_phase", "trial_status", 
                    "primary_drug", "primary_drug_moa", "indication", 
                    "line_of_therapy", "sponsor", "patient_enrollment"
                ]
            
            # Build comparison table
            result = "## Trial Comparison\n\n"
            result += "| Field | " + " | ".join([f"**{nct_id}**" for nct_id in nct_ids]) + " |\n"
            result += "|-------|" + "|".join(["---" for _ in nct_ids]) + "|\n"
            
            # Add each field as a row
            for field in fields:
                values = []
                for trial in trials:
                    value = trial.get(field, "N/A")
                    # Truncate long values for table display
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:47] + "..."
                    values.append(str(value))
                result += f"| {field} | " + " | ".join(values) + " |\n"
            
            return result
    
    async def _get_trial_statistics(self, arguments: Dict[str, Any]) -> str:
        """
        Get statistical information about stored trials
        
        Generates summary statistics grouped by various criteria such as phase,
        status, sponsor, indication, or drug.
        
        Args:
            arguments: Dictionary containing:
                - group_by: Field to group statistics by
                - include_charts: Whether to include chart data
                
        Returns:
            str: Formatted statistics
        """
        group_by = arguments.get("group_by", "phase")
        include_charts = arguments.get("include_charts", True)
        
        # Retrieve all trials from database
        all_trials = self.db.search_trials({}, 1000)
        
        if not all_trials:
            return "No trials found in database."
        
        # Create pandas DataFrame for statistical analysis
        df = pd.DataFrame(all_trials)
        
        # Generate statistics based on grouping field
        if group_by == "phase":
            stats = df["trial_phase"].value_counts()
        elif group_by == "status":
            stats = df["trial_status"].value_counts()
        elif group_by == "sponsor":
            stats = df["sponsor"].value_counts().head(10)  # Top 10 sponsors
        elif group_by == "indication":
            stats = df["indication"].value_counts().head(10)  # Top 10 indications
        elif group_by == "primary_drug":
            stats = df["primary_drug"].value_counts().head(10)  # Top 10 drugs
        else:
            return f"Invalid group_by field: {group_by}"
        
        # Format statistics as markdown table
        result = f"## Trial Statistics (Grouped by {group_by})\n\n"
        result += "| Category | Count |\n"
        result += "|----------|-------|\n"
        
        for category, count in stats.items():
            result += f"| {category} | {count} |\n"
        
        # Add summary information
        result += f"\n**Total Trials:** {len(all_trials)}\n"
        result += f"**Unique {group_by.title()}s:** {len(stats)}\n"
        
        return result
    
    async def _analyze_trial_with_model(self, arguments: Dict[str, Any]) -> str:
        """
        Analyze a trial with a specific AI model and store results
        
        This method allows re-analysis of trials with different AI models or
        analysis of new trials with specified models.
        
        Args:
            arguments: Dictionary containing:
                - nct_id: NCT ID of the trial
                - model: AI model to use for analysis
                - json_file_path: Optional path to JSON file
                
        Returns:
            str: Analysis result message
        """
        nct_id = arguments["nct_id"]
        model = arguments["model"]
        json_file_path = arguments.get("json_file_path")
        
        # Get or create AI analyzer for the specified model
        if model not in self.analyzers:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return "Error: OPENAI_API_KEY not found in environment"
            
            # Initialize appropriate analyzer
            if model == "llm":
                self.analyzers[model] = ClinicalTrialAnalyzerLLM(api_key)
            else:
                self.analyzers[model] = ClinicalTrialAnalyzerReasoning(api_key, model=model)
        
        analyzer = self.analyzers[model]
        
        # Perform analysis
        try:
            result = analyzer.analyze_trial(nct_id, json_file_path)
            if "error" in result:
                return f"Error analyzing trial {nct_id}: {result['error']}"
            
            # Store results in database with metadata
            success = self.db.store_trial_data(result, {
                "analysis_model": model,
                "analysis_timestamp": datetime.now().isoformat(),
                "source_file": json_file_path
            })
            
            if success:
                return f"✅ Successfully analyzed and stored trial {nct_id} using {model} model"
            else:
                return f"❌ Failed to store trial {nct_id}"
                
        except Exception as e:
            return f"Error processing trial {nct_id}: {str(e)}"
    
    async def _get_available_columns(self, arguments: Dict[str, Any]) -> str:
        """
        Get list of available columns in the database
        
        Provides schema information for database tables, useful for understanding
        what data is available and how it's structured.
        
        Args:
            arguments: Dictionary containing:
                - table: Table name to get columns for
                
        Returns:
            str: Formatted column information
        """
        table = arguments.get("table", "clinical_trials")
        
        try:
            # Query database schema information
            cursor = self.db.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            # Format as markdown table
            result = f"## Available Columns in {table}\n\n"
            result += "| Column | Type | Not Null | Default | Primary Key |\n"
            result += "|--------|------|----------|---------|-------------|\n"
            
            for col in columns:
                result += f"| {col[1]} | {col[2]} | {col[3]} | {col[4] or 'NULL'} | {col[5]} |\n"
            
            return result
            
        except Exception as e:
            return f"Error getting column information: {str(e)}"
    
    async def _export_trials(self, arguments: Dict[str, Any]) -> str:
        """
        Export trials to CSV or JSON format
        
        Allows bulk export of trial data for external analysis or reporting.
        
        Args:
            arguments: Dictionary containing:
                - format: Export format (csv, json)
                - filters: Optional filters to apply
                - filename: Output filename
                
        Returns:
            str: Export result message
        """
        format_type = arguments.get("format", "csv")
        filters = arguments.get("filters", {})
        filename = arguments.get("filename")
        
        # Get trials based on filters
        trials = self.db.search_trials(filters, 1000)
        
        if not trials:
            return "No trials found to export."
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"clinical_trials_export_{timestamp}.{format_type}"
        
        try:
            # Export based on format
            if format_type == "csv":
                df = pd.DataFrame(trials)
                df.to_csv(filename, index=False)
            else:  # json format
                with open(filename, 'w') as f:
                    json.dump(trials, f, indent=2)
            
            return f"✅ Successfully exported {len(trials)} trials to {filename}"
            
        except Exception as e:
            return f"Error exporting trials: {str(e)}"
    
    async def _get_trials_by_drug(self, arguments: Dict[str, Any]) -> str:
        """
        Find all trials for a specific drug
        
        Specialized search function for drug-specific queries.
        
        Args:
            arguments: Dictionary containing:
                - drug_name: Name of the drug to search for
                - include_similar: Whether to include similar drug names
                - limit: Maximum number of results
                
        Returns:
            str: Formatted trial results
        """
        drug_name = arguments["drug_name"]
        include_similar = arguments.get("include_similar", True)
        limit = arguments.get("limit", 20)
        
        # Build search filter
        filters = {"primary_drug": drug_name}
        
        # TODO: Implement fuzzy matching for similar drug names
        if include_similar:
            # This would need more sophisticated fuzzy matching
            # For now, just search for the exact drug name
            pass
        
        # Execute search
        results = self.db.search_trials(filters, limit)
        
        if not results:
            return f"No trials found for drug: {drug_name}"
        
        return self._format_table(results)
    
    async def _get_trials_by_indication(self, arguments: Dict[str, Any]) -> str:
        """
        Find all trials for a specific indication (disease)
        
        Specialized search function for indication-specific queries.
        
        Args:
            arguments: Dictionary containing:
                - indication: Disease indication to search for
                - include_similar: Whether to include similar indications
                - limit: Maximum number of results
                
        Returns:
            str: Formatted trial results
        """
        indication = arguments["indication"]
        include_similar = arguments.get("include_similar", True)
        limit = arguments.get("limit", 20)
        
        # Build search filter
        filters = {"indication": indication}
        
        # TODO: Implement fuzzy matching for similar indications
        if include_similar:
            # This would need more sophisticated fuzzy matching
            # For now, just search for the exact indication
            pass
        
        # Execute search
        results = self.db.search_trials(filters, limit)
        
        if not results:
            return f"No trials found for indication: {indication}"
        
        return self._format_table(results)
    
    async def _smart_search(self, arguments: Dict[str, Any]) -> str:
        """
        Intelligent search that interprets natural language queries
        
        Advanced search function that parses natural language queries and
        converts them to structured database searches.
        
        Args:
            arguments: Dictionary containing:
                - query: Natural language search query
                - limit: Maximum number of results
                - format: Output format
                
        Returns:
            str: Formatted search results
        """
        query = arguments["query"]
        limit = arguments.get("limit", 10)
        format_type = arguments.get("format", "table")
        
        # Parse natural language query to extract structured filters
        filters = {}
        
        # Extract drug information from query
        if "semaglutide" in query.lower():
            filters["primary_drug"] = "semaglutide"
        elif "ozempic" in query.lower():
            filters["primary_drug"] = "semaglutide"  # Ozempic is semaglutide
        
        # Extract indication information
        if "diabetes" in query.lower():
            filters["indication"] = "diabetes"
        elif "cancer" in query.lower():
            filters["indication"] = "cancer"
        
        # Extract trial phase information
        if "phase 1" in query.lower() or "phase i" in query.lower():
            filters["trial_phase"] = "PHASE1"
        elif "phase 2" in query.lower() or "phase ii" in query.lower():
            filters["trial_phase"] = "PHASE2"
        elif "phase 3" in query.lower() or "phase iii" in query.lower():
            filters["trial_phase"] = "PHASE3"
        
        # Extract trial status information
        if "recruiting" in query.lower():
            filters["trial_status"] = "RECRUITING"
        elif "completed" in query.lower():
            filters["trial_status"] = "COMPLETED"
        
        # Execute search with extracted filters
        results = self.db.search_trials(filters, limit)
        
        if not results:
            return f"No trials found matching: {query}"
        
        # Format results based on requested format
        if format_type == "json":
            return json.dumps(results, indent=2)
        elif format_type == "summary":
            return self._format_summary(results)
        else:  # table format
            return self._format_table(results)
    
    async def _reasoning_query(self, arguments: Dict[str, Any]) -> str:
        """
        Advanced reasoning-based query using reasoning models for complex clinical trial questions.
        
        This tool interprets natural language queries and uses reasoning models
        to extract structured filters and perform more sophisticated searches.
        
        Args:
            arguments: Dictionary containing:
                - query: Complex natural language query requiring reasoning
                - reasoning_model: Reasoning model to use for query interpretation
                - include_analysis: Whether to include AI analysis and insights
                - limit: Maximum number of results
                - format: Output format (detailed, summary, analysis)
                
        Returns:
            str: Formatted analysis result
        """
        query = arguments["query"]
        reasoning_model = arguments.get("reasoning_model", "gpt-4o")
        include_analysis = arguments.get("include_analysis", True)
        limit = arguments.get("limit", 20)
        format_type = arguments.get("format", "detailed")
        
        # Get or create reasoning analyzer
        if reasoning_model not in self.analyzers:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return "Error: OPENAI_API_KEY not found in environment"
            
            self.analyzers[reasoning_model] = ClinicalTrialAnalyzerReasoning(api_key, model=reasoning_model)
        
        analyzer = self.analyzers[reasoning_model]
        
        # Perform reasoning to extract filters and query intent
        try:
            analysis_result = analyzer.analyze_query(query)
            
            # Extract structured filters and query intent
            filters = analysis_result.get("filters", {})
            query_intent = analysis_result.get("query_intent", "unknown")
            
            # Combine natural language query with extracted filters
            final_query_text = query
            if filters:
                final_query_text += " with filters: " + json.dumps(filters)
            
            # Execute search with combined filters
            results = self.db.search_trials(filters, limit)
            
            if not results:
                return f"No trials found for query: {final_query_text}"
            
            # Format results based on requested format
            if format_type == "detailed":
                return json.dumps(results, indent=2)
            elif format_type == "summary":
                return self._format_summary(results)
            else: # analysis format
                return json.dumps(analysis_result, indent=2)
                
        except Exception as e:
            return f"Error processing reasoning query: {str(e)}"
    
    async def _compare_analysis(self, arguments: Dict[str, Any]) -> str:
        """
        Compare trials based on natural language criteria with AI-powered insights.
        
        This tool interprets a natural language description of what to compare
        and uses reasoning models to find relevant trials and provide insights.
        
        Args:
            arguments: Dictionary containing:
                - comparison_criteria: Natural language description of what to compare
                - trial_ids: Optional specific NCT IDs to compare
                - auto_find_similar: Whether to automatically find similar trials if no IDs provided
                - analysis_depth: Depth of analysis (basic, detailed, expert)
                
        Returns:
            str: Formatted comparison result
        """
        comparison_criteria = arguments["comparison_criteria"]
        trial_ids = arguments.get("trial_ids", [])
        auto_find_similar = arguments.get("auto_find_similar", True)
        analysis_depth = arguments.get("analysis_depth", "detailed")
        
        # Get or create reasoning analyzer
        reasoning_model = "o3-mini" # Default reasoning model
        if analysis_depth == "expert":
            reasoning_model = "o3" # Use the more powerful o3 model for expert analysis
        
        if reasoning_model not in self.analyzers:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return "Error: OPENAI_API_KEY not found in environment"
            
            self.analyzers[reasoning_model] = ClinicalTrialAnalyzerReasoning(api_key, model=reasoning_model)
        
        analyzer = self.analyzers[reasoning_model]
        
        # Perform reasoning to extract filters and query intent
        try:
            analysis_result = analyzer.analyze_query(comparison_criteria)
            
            # Extract structured filters and query intent
            filters = analysis_result.get("filters", {})
            query_intent = analysis_result.get("query_intent", "unknown")
            
            # Combine natural language query with extracted filters
            final_query_text = comparison_criteria
            if filters:
                final_query_text += " with filters: " + json.dumps(filters)
            
            # Execute search with combined filters
            results = self.db.search_trials(filters, 1000) # Fetch all results for comparison
            
            if not results:
                return f"No trials found for query: {final_query_text}"
            
            # Format results based on requested format
            if analysis_depth == "basic":
                return json.dumps(results, indent=2)
            elif analysis_depth == "detailed":
                return json.dumps(analysis_result, indent=2)
            else: # expert format
                return json.dumps(analysis_result, indent=2)
                
        except Exception as e:
            return f"Error processing compare analysis: {str(e)}"
    
    async def _trend_analysis(self, arguments: Dict[str, Any]) -> str:
        """
        Analyze trends and patterns in clinical trials using natural language queries.
        
        This tool interprets a natural language description of trends to analyze
        and uses reasoning models to extract relevant data and provide insights.
        
        Args:
            arguments: Dictionary containing:
                - trend_query: Natural language description of trends to analyze
                - time_period: Time period for analysis (e.g., 'last 5 years', '2020-2024')
                - group_by: Field to group analysis by (drug, indication, phase, sponsor, geography)
                - include_insights: Whether to include AI insights
                
        Returns:
            str: Formatted trend analysis result
        """
        trend_query = arguments["trend_query"]
        time_period = arguments.get("time_period", "last 5 years")
        group_by = arguments.get("group_by", "drug")
        include_insights = arguments.get("include_insights", True)
        
        # Get or create reasoning analyzer
        reasoning_model = "o3-mini" # Default reasoning model
        if group_by == "expert":
            reasoning_model = "o3" # Use the more powerful o3 model for expert analysis
        
        if reasoning_model not in self.analyzers:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return "Error: OPENAI_API_KEY not found in environment"
            
            self.analyzers[reasoning_model] = ClinicalTrialAnalyzerReasoning(api_key, model=reasoning_model)
        
        analyzer = self.analyzers[reasoning_model]
        
        # Perform reasoning to extract filters and query intent
        try:
            analysis_result = analyzer.analyze_query(trend_query)
            
            # Extract structured filters and query intent
            filters = analysis_result.get("filters", {})
            query_intent = analysis_result.get("query_intent", "unknown")
            
            # Combine natural language query with extracted filters
            final_query_text = trend_query
            if filters:
                final_query_text += " with filters: " + json.dumps(filters)
            
            # Execute search with combined filters
            results = self.db.search_trials(filters, 1000) # Fetch all results for trend analysis
            
            if not results:
                return f"No trials found for query: {final_query_text}"
            
            # Format results based on requested format
            if include_insights:
                return json.dumps(analysis_result, indent=2)
            else:
                return json.dumps(results, indent=2)
                
        except Exception as e:
            return f"Error processing trend analysis: {str(e)}"
    
    def _format_table(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results as a markdown table
        
        Creates a readable table format for displaying trial search results
        with key fields and truncated long values.
        
        Args:
            results: List of trial dictionaries
            
        Returns:
            str: Formatted markdown table
        """
        if not results:
            return "No results found."
        
        # Get all unique keys from results
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        
        # Select key fields for display (prioritize important fields)
        key_fields = [
            "nct_id", "trial_name", "trial_phase", "trial_status", 
            "primary_drug", "indication", "sponsor", "patient_enrollment"
        ]
        
        # Filter to only include fields that exist in the data
        display_fields = [field for field in key_fields if field in all_keys]
        
        # Build table header
        result = f"## Found {len(results)} trials\n\n"
        result += "| " + " | ".join(display_fields) + " |\n"
        result += "|" + "|".join(["---" for _ in display_fields]) + "|\n"
        
        # Add data rows
        for trial in results:
            row = []
            for field in display_fields:
                value = trial.get(field, "N/A")
                # Truncate long values for better table display
                if isinstance(value, str) and len(value) > 30:
                    value = value[:27] + "..."
                row.append(str(value))
            result += "| " + " | ".join(row) + " |\n"
        
        return result
    
    def _format_summary(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results as a summary with statistics
        
        Creates a summary view showing counts by various categories
        instead of detailed trial information.
        
        Args:
            results: List of trial dictionaries
            
        Returns:
            str: Formatted summary with statistics
        """
        if not results:
            return "No results found."
        
        result = f"## Summary: {len(results)} trials found\n\n"
        
        # Count trials by phase
        phases = {}
        for trial in results:
            phase = trial.get("trial_phase", "Unknown")
            phases[phase] = phases.get(phase, 0) + 1
        
        result += "### By Phase:\n"
        for phase, count in phases.items():
            result += f"- {phase}: {count} trials\n"
        
        # Count trials by status
        statuses = {}
        for trial in results:
            status = trial.get("trial_status", "Unknown")
            statuses[status] = statuses.get(status, 0) + 1
        
        result += "\n### By Status:\n"
        for status, count in statuses.items():
            result += f"- {status}: {count} trials\n"
        
        # Count trials by drug (top drugs)
        drugs = {}
        for trial in results:
            drug = trial.get("primary_drug", "Unknown")
            if drug != "Unknown":
                drugs[drug] = drugs.get(drug, 0) + 1
        
        if drugs:
            result += "\n### Top Drugs:\n"
            # Sort by count and take top 5
            sorted_drugs = sorted(drugs.items(), key=lambda x: x[1], reverse=True)[:5]
            for drug, count in sorted_drugs:
                result += f"- {drug}: {count} trials\n"
        
        return result
    
    async def run(self):
        """
        Run the MCP server using stdio transport
        
        This method starts the MCP server and handles communication with AI clients
        through standard input/output streams. It sets up the server with proper
        initialization options and capabilities.
        """
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="clinical-trial-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )

def main():
    """
    Main function to run the MCP server
    
    This is the entry point for running the MCP server as a standalone process.
    It initializes the server, displays available tools, and handles graceful shutdown.
    """
    # Create and initialize the MCP server
    server = ClinicalTrialMCPServer()
    
    # Display server information and available tools
    print("🏥 Clinical Trial MCP Server")
    print("=" * 50)
    print("Starting MCP server...")
    print("Available tools:")
    print("- store_trial: Store clinical trials")
    print("- search_trials: Search with filters")
    print("- get_trial_details: Get trial details")
    print("- compare_trials: Compare multiple trials")
    print("- get_trial_statistics: Get statistics")
    print("- analyze_trial_with_model: Analyze with specific model")
    print("- get_available_columns: List database columns")
    print("- export_trials: Export to CSV/JSON")
    print("- get_trials_by_drug: Find trials by drug")
    print("- get_trials_by_indication: Find trials by indication")
    print("- smart_search: Natural language search")
    print("- reasoning_query: Advanced reasoning-based queries")
    print("- compare_analysis: AI-powered trial comparison")
    print("- trend_analysis: Trend and pattern analysis")
    print("=" * 50)
    
    try:
        # Start the server and run until interrupted
        asyncio.run(server.run())
    except KeyboardInterrupt:
        # Handle graceful shutdown on Ctrl+C
        print("\nServer stopped by user")
    except Exception as e:
        # Handle and log any server errors
        print(f"Server error: {e}")
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main() 