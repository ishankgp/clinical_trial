#!/usr/bin/env python3
"""
Clinical Trial MCP Server
Provides MCP-compatible API for clinical trial analysis and search
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from datetime import datetime
from contextlib import asynccontextmanager
import traceback

# Add the project root to the Python path for proper imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import MCP types
try:
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
except ImportError:
    # Fallback to local types if MCP package not available
    from .server_stub import (
        Server,
        InitializationOptions,
        Tool,
        ListToolsResult,
        CallToolResult,
        TextContent,
        ImageContent,
        EmbeddedResource,
        LoggingLevel,
        ListToolsRequest,
        CallToolRequest,
        stdio_server,
    )

# Add src to Python path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Fixed imports with proper fallback
try:
    from database.clinical_trial_database import ClinicalTrialDatabase
    from analysis.clinical_trial_analyzer_reasoning import (
        ClinicalTrialAnalyzerReasoning,
    )
    from analysis.clinical_trial_analyzer_llm import ClinicalTrialAnalyzerLLM
except ImportError:
    # Fallback for direct execution from project root
    try:
        from src.database.clinical_trial_database import ClinicalTrialDatabase
        from src.analysis.clinical_trial_analyzer_reasoning import (
            ClinicalTrialAnalyzerReasoning,
        )
        from src.analysis.clinical_trial_analyzer_llm import ClinicalTrialAnalyzerLLM
    except ImportError:
        # Final fallback - try to find modules in current directory
        print(
            "Warning: Could not import required modules. Please ensure you're running from the project root."
        )
        ClinicalTrialDatabase = None
        ClinicalTrialAnalyzerReasoning = None
        ClinicalTrialAnalyzerLLM = None

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Custom exceptions
class MCPError(Exception):
    """Base exception for MCP server errors"""

    pass


class ValidationError(MCPError):
    """Validation error"""

    pass


class DatabaseError(MCPError):
    """Database error"""

    pass


class AnalysisError(MCPError):
    """Analysis error"""

    pass


class DatabasePool:
    """Thread-safe database connection pool using standard sqlite3"""

    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool = []
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def get_connection(self):
        async with self._lock:
            if self._pool:
                conn = self._pool.pop()
            else:
                # Use standard sqlite3 instead of aiosqlite
                conn = sqlite3.connect(self.db_path)

        try:
            yield conn
        finally:
            async with self._lock:
                if len(self._pool) < self.max_connections:
                    self._pool.append(conn)
                else:
                    conn.close()


class CacheManager:
    """Proper cache management with expiration"""

    def __init__(self, cache_dir: Path, max_age_hours: int = 24):
        self.cache_dir = cache_dir
        self.max_age_seconds = max_age_hours * 3600
        self.cache_dir.mkdir(exist_ok=True)

    def get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        # Check if cache is stale
        import time

        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > self.max_age_seconds:
            cache_file.unlink()  # Remove stale cache
            return None

        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache for {key}: {e}")
            cache_file.unlink()  # Remove corrupted cache
            return None

    def set_cached_data(self, key: str, data: Dict[str, Any]):
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache for {key}: {e}")


class ClinicalTrialMCPServer:
    """MCP Server for clinical trial data management and querying - Fixed Version"""

    def __init__(self):
        """Initialize the MCP server with proper error handling"""
        # Check if required modules are available
        if ClinicalTrialDatabase is None:
            raise ImportError("ClinicalTrialDatabase module not available")

        self.server = Server("clinical-trial-mcp-server-fixed")
        self.db = None
        self.analyzers = {}
        self.cache_manager = None
        self.db_pool = None

        # Initialize components
        self._init_database()
        self._init_cache()
        self._init_analyzers()

        # Register tools
        self._register_tools()

    def _init_database(self):
        """Initialize database connection"""
        try:
            from src.database.clinical_trial_database import ClinicalTrialDatabase
            self.db = ClinicalTrialDatabase()
            logger.info("Database initialized successfully")
        except ImportError:
            logger.error("ClinicalTrialDatabase module not available")
            raise ImportError("ClinicalTrialDatabase module not available")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _init_cache(self):
        """Initialize cache manager"""
        try:
            cache_dir = Path("data/cache")
            self.cache_manager = CacheManager(cache_dir)
            logger.info("Cache manager initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize cache: {e}")
            self.cache_manager = None

    def _init_analyzers(self):
        """Initialize analyzers for different models"""
        try:
            # Import analyzers
            from src.analysis.clinical_trial_analyzer_llm import ClinicalTrialAnalyzerLLM
            from src.analysis.clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning
            
            # Get API key
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            
            # Initialize analyzers for different models
            self.analyzers = {
                "gpt-4o": ClinicalTrialAnalyzerLLM(api_key, model="gpt-4o"),
                "gpt-4o-mini": ClinicalTrialAnalyzerLLM(api_key, model="gpt-4o-mini"),
                "o3": ClinicalTrialAnalyzerReasoning(api_key, model="o3"),
                "gpt-4": ClinicalTrialAnalyzerLLM(api_key, model="gpt-4"),
            }
            
            logger.info("Analyzers initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to import analyzers: {e}")
            self.analyzers = {}
        except Exception as e:
            logger.error(f"Failed to initialize analyzers: {e}")
            self.analyzers = {}
    
    async def _get_analyzer(self, model_name: str):
        """Get analyzer for specified model"""
        if not self.analyzers:
            await self._init_analyzers_async()
        
        # Validate model
        valid_models = ["gpt-4o", "gpt-4o-mini", "o3", "gpt-4", "llm"]
        if model_name not in valid_models:
            logger.warning(f"Invalid model: {model_name}, using gpt-4o-mini")
            model_name = "gpt-4o-mini"
        
        return self.analyzers.get(model_name)

    def _validate_nct_id(self, nct_id: str) -> bool:
        """Validate NCT ID format"""
        if not nct_id or not isinstance(nct_id, str):
            return False
        return nct_id.upper().startswith("NCT") and len(nct_id) >= 8

    def _validate_store_trial_args(self, arguments: Dict[str, Any]):
        """Validate arguments for store_trial tool"""
        if "nct_id" not in arguments:
            raise ValidationError("nct_id is required")

        nct_id = arguments["nct_id"]
        if not self._validate_nct_id(nct_id):
            raise ValidationError(f"Invalid NCT ID format: {nct_id}")

        # Validate model if provided
        if "analyze_with_model" in arguments:
            valid_models = ["gpt-4o", "gpt-4o-mini", "o3", "gpt-4", "llm"]
            if arguments["analyze_with_model"] not in valid_models:
                raise ValidationError(
                    f"Invalid model: {arguments['analyze_with_model']}"
                )

    def _register_tools(self):
        """Register all available tools with proper validation"""

        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List all available tools"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="store_trial",
                        description="Store a clinical trial from JSON file or NCT ID",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "nct_id": {
                                    "type": "string",
                                    "description": "NCT ID of the trial",
                                },
                                "json_file_path": {
                                    "type": "string",
                                    "description": "Path to JSON file (optional)",
                                },
                                "analyze_with_model": {
                                    "type": "string",
                                    "enum": [
                                        "gpt-4o",
                                        "gpt-4o-mini",
                                        "o3",
                                        "gpt-4",
                                        "llm",
                                    ],
                                    "default": "gpt-4o-mini",
                                    "description": "Model to use for analysis",
                                },
                                "force_reanalyze": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "Force reanalysis even if trial exists",
                                },
                            },
                            "required": ["nct_id"],
                        },
                    ),
                    Tool(
                        name="search_trials",
                        description="Search clinical trials with flexible filters",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Natural language search query",
                                },
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
                                    },
                                },
                                "limit": {"type": "integer", "default": 50},
                                "format": {
                                    "type": "string",
                                    "enum": ["table", "json", "summary"],
                                    "default": "table",
                                },
                            },
                        },
                    ),
                    Tool(
                        name="get_trial_details",
                        description="Get detailed information about a specific trial",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "nct_id": {
                                    "type": "string",
                                    "description": "NCT ID of the trial",
                                },
                                "include_raw_data": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "Include raw JSON data",
                                },
                            },
                            "required": ["nct_id"],
                        },
                    ),
                    Tool(
                        name="smart_search",
                        description="Intelligent search that interprets natural language queries",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Natural language query",
                                },
                                "limit": {"type": "integer", "default": 10},
                                "format": {
                                    "type": "string",
                                    "enum": ["table", "json", "summary"],
                                    "default": "table",
                                },
                            },
                            "required": ["query"],
                        },
                    ),
                    Tool(
                        name="reasoning_query",
                        description="Advanced semantic search using reasoning models for complex clinical trial questions",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Complex natural language query requiring reasoning",
                                },
                                "reasoning_model": {
                                    "type": "string",
                                    "enum": ["o3", "o3-mini"],
                                    "default": "o3-mini",
                                    "description": "Reasoning model to use for query interpretation",
                                },
                                "include_analysis": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Include AI analysis and insights",
                                },
                                "limit": {"type": "integer", "default": 20},
                                "format": {
                                    "type": "string",
                                    "enum": ["detailed", "analysis", "json"],
                                    "default": "detailed",
                                },
                            },
                            "required": ["query"],
                        },
                    ),
                    Tool(
                        name="compare_analysis",
                        description="AI-powered comparison of clinical trials using reasoning models",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "comparison_criteria": {
                                    "type": "string",
                                    "description": "Natural language criteria for comparison",
                                },
                                "auto_find_similar": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Automatically find similar trials",
                                },
                                "analysis_depth": {
                                    "type": "string",
                                    "enum": ["basic", "detailed", "expert"],
                                    "default": "detailed",
                                },
                            },
                            "required": ["comparison_criteria"],
                        },
                    ),
                    Tool(
                        name="trend_analysis",
                        description="Analyze trends and patterns in clinical trial data using reasoning models",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "trend_query": {
                                    "type": "string",
                                    "description": "Natural language trend analysis query",
                                },
                                "time_period": {
                                    "type": "string",
                                    "description": "Time period for analysis (e.g., 'last 5 years')",
                                },
                                "group_by": {
                                    "type": "string",
                                    "enum": ["drug", "indication", "phase", "sponsor", "expert"],
                                    "default": "drug",
                                },
                                "include_insights": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Include AI insights and analysis",
                                },
                            },
                            "required": ["trend_query"],
                        },
                    ),
                ]
            )

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> CallToolResult:
            """Handle tool calls with proper error handling"""
            try:
                # Validate arguments based on tool
                if name == "store_trial":
                    self._validate_store_trial_args(arguments)
                    result = await self._store_trial(arguments)
                elif name == "search_trials":
                    result = await self._search_trials(arguments)
                elif name == "get_trial_details":
                    if "nct_id" not in arguments:
                        raise ValidationError(
                            "nct_id is required for get_trial_details"
                        )
                    result = await self._get_trial_details(arguments)
                elif name == "smart_search":
                    if "query" not in arguments:
                        raise ValidationError("query is required for smart_search")
                    result = await self._smart_search(arguments)
                elif name == "reasoning_query":
                    if "query" not in arguments:
                        raise ValidationError("query is required for reasoning_query")
                    result = await self._reasoning_query(arguments)
                elif name == "compare_analysis":
                    if "comparison_criteria" not in arguments:
                        raise ValidationError("comparison_criteria is required for compare_analysis")
                    result = await self._compare_analysis(arguments)
                elif name == "trend_analysis":
                    if "trend_query" not in arguments:
                        raise ValidationError("trend_query is required for trend_analysis")
                    result = await self._trend_analysis(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {name}")]
                    )

                return CallToolResult(content=[TextContent(type="text", text=result)])

            except ValidationError as e:
                logger.warning(f"Validation error in tool {name}: {e}")
                return CallToolResult(
                    content=[
                        TextContent(type="text", text=f"Validation Error: {str(e)}")
                    ]
                )
            except DatabaseError as e:
                logger.error(f"Database error in tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Database Error: {str(e)}")]
                )
            except AnalysisError as e:
                logger.error(f"Analysis error in tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Analysis Error: {str(e)}")]
                )
            except Exception as e:
                logger.error(f"Unexpected error in tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")]
                )

    async def _store_trial(self, arguments: Dict[str, Any]) -> str:
        """Store and analyze a clinical trial with proper error handling"""
        nct_id = arguments["nct_id"]
        json_file_path = arguments.get("json_file_path")
        analyze_with_model = arguments.get("analyze_with_model", "gpt-4o-mini")
        force_reanalyze = arguments.get("force_reanalyze", False)

        # Check cache first
        cache_key = f"trial_{nct_id}_{analyze_with_model}"
        if not force_reanalyze and self.cache_manager:
            cached_result = self.cache_manager.get_cached_data(cache_key)
            if cached_result:
                return f"✅ Retrieved cached analysis for trial {nct_id}"

        # Check if trial already exists
        existing_trial = self.db.get_trial_by_nct_id(nct_id)
        if existing_trial and not force_reanalyze:
            return f"Trial {nct_id} already exists in database. Use force_reanalyze=true to reanalyze."

        # Get analyzer and perform analysis
        try:
            analyzer = await self._get_analyzer(analyze_with_model)
            result = analyzer.analyze_trial(nct_id, json_file_path)

            if "error" in result:
                raise AnalysisError(f"Analysis failed: {result['error']}")

            # Store in database
            success = await self._store_trial_data(
                result,
                {
                    "analysis_model": analyze_with_model,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "source_file": json_file_path,
                },
            )

            if success:
                # Cache the result
                if self.cache_manager:
                    self.cache_manager.set_cached_data(cache_key, result)

                return f"✅ Successfully stored trial {nct_id} using {analyze_with_model} model"
            else:
                raise DatabaseError(f"Failed to store trial {nct_id}")

        except Exception as e:
            raise AnalysisError(f"Error processing trial {nct_id}: {str(e)}")

    async def _store_trial_data(
        self, trial_data: Dict[str, Any], metadata: Dict[str, Any]
    ) -> bool:
        """Store trial data in database"""
        try:
            return self.db.store_trial_data(trial_data, metadata)
        except Exception as e:
            logger.error(f"Failed to store trial data: {e}")
            return False

    async def _search_trials(self, arguments: Dict[str, Any]) -> str:
        """Search trials with proper error handling"""
        query = arguments.get("query", "")
        filters = arguments.get("filters", {})
        limit = arguments.get("limit", 50)
        format_type = arguments.get("format", "table")
        try:
            results = await self._perform_search(query, filters, limit)
            if not results:
                return "No trials found matching the criteria."
            # Format results
            if format_type == "json":
                return json.dumps(results, indent=2)
            elif format_type == "summary":
                return self._format_summary(results)
            else:  # table format
                return self._format_table(results)
        except Exception as e:
            raise DatabaseError(f"Search failed: {str(e)}")

    async def _perform_search(
        self, query: str, filters: Dict[str, Any], limit: int
    ) -> List[Dict[str, Any]]:
        """Perform the actual search operation using AI-driven query understanding"""
        # Use AI to parse the natural language query
        if query:
            ai_result = await self._parse_natural_language_query(query)
            ai_filters = ai_result.get("filters", {})
            # Merge AI-generated filters with explicit filters
            search_filters = {**ai_filters, **filters}
        else:
            search_filters = filters

        # Execute search with AI-generated search terms
        return self.db.search_trials(search_filters, limit)

    async def _get_trial_details(self, arguments: Dict[str, Any]) -> str:
        """Get detailed trial information"""
        nct_id = arguments["nct_id"]
        include_raw_data = arguments.get("include_raw_data", False)
        try:
            trial = self.db.get_trial_by_nct_id(nct_id)
            if not trial:
                return f"Trial {nct_id} not found in database."
            if include_raw_data:
                return json.dumps(trial, indent=2)
            else:
                # Format as readable text
                result = f"# Trial Details: {nct_id}\n\n"
                result += "## Basic Information\n"
                result += f"- **Trial Name:** {trial.get('trial_name', 'N/A')}\n"
                result += f"- **Phase:** {trial.get('trial_phase', 'N/A')}\n"
                result += f"- **Status:** {trial.get('trial_status', 'N/A')}\n"
                result += (
                    f"- **Enrollment:** {trial.get('patient_enrollment', 'N/A')}\n"
                )
                result += f"- **Sponsor:** {trial.get('sponsor', 'N/A')}\n"
                result += "\n## Drug Information\n"
                result += f"- **Primary Drug:** {trial.get('primary_drug', 'N/A')}\n"
                result += f"- **MoA:** {trial.get('primary_drug_moa', 'N/A')}\n"
                result += f"- **Target:** {trial.get('primary_drug_target', 'N/A')}\n"
                result += "\n## Clinical Information\n"
                result += f"- **Indication:** {trial.get('indication', 'N/A')}\n"
                result += (
                    f"- **Line of Therapy:** {trial.get('line_of_therapy', 'N/A')}\n"
                )
                result += f"- **Patient Population:** {trial.get('patient_population', 'N/A')}\n"
                return result
        except Exception as e:
            raise DatabaseError(f"Failed to get trial details: {str(e)}")

    async def _smart_search(self, arguments: Dict[str, Any]) -> str:
        """Intelligent search with natural language processing"""
        query = arguments["query"]
        limit = arguments.get("limit", 10)
        format_type = arguments.get("format", "table")
        try:
            # Parse natural language query
            ai_result = await self._parse_natural_language_query(query)
            filters = ai_result.get("filters", {})
            # Perform search
            results = self.db.search_trials(filters, limit)
            if not results:
                return f"No trials found matching: {query}"
            # Format results
            if format_type == "json":
                return json.dumps(results, indent=2)
            elif format_type == "summary":
                return self._format_summary(results)
            else:  # table format
                return self._format_table(results)
        except Exception as e:
            raise AnalysisError(f"Smart search failed: {str(e)}")

    async def _reasoning_query(self, arguments: Dict[str, Any]) -> str:
        """
        Advanced semantic search using reasoning models for complex clinical trial queries
        This provides more sophisticated analysis than the basic smart_search
        """
        query = arguments["query"]
        reasoning_model = arguments.get("reasoning_model", "o3-mini")
        include_analysis = arguments.get("include_analysis", True)
        limit = arguments.get("limit", 20)
        format_type = arguments.get("format", "detailed")
        
        try:
            # Get the appropriate analyzer
            analyzer = await self._get_analyzer(reasoning_model)
            
            # Enhanced query analysis with reasoning model
            enhanced_prompt = f"""
            You are an expert clinical trial analyst with deep domain knowledge. Analyze this complex query about clinical trials:
            
            QUERY: "{query}"
            
            TASK: Perform a detailed semantic analysis of this query to extract structured search parameters and generate insights.
            
            1. Extract all relevant search parameters including:
               - Drugs (including drug classes, mechanisms, modalities)
               - Indications (diseases, conditions, specific subtypes)
               - Trial phases
               - Trial status
               - Patient populations
               - Biomarkers
               - Geographic regions
               - Sponsors or sponsor types
               - Endpoints or outcome measures
               - Any other relevant parameters
            
            2. Identify the core intent of the query
            
            3. Develop a search strategy that would best address this query
            
            4. Determine which database fields would be most relevant to search
            
            5. Generate insights about what the user is likely trying to learn
            
            RESPONSE FORMAT: Return a JSON object with the following structure:
            {{
                "filters": {{
                    "primary_drug": ["list", "of", "drug", "names", "and", "classes"],
                    "indication": ["list", "of", "diseases", "and", "conditions"],
                    "trial_phase": ["PHASE1", "PHASE2", ...],
                    "trial_status": ["RECRUITING", ...],
                    "sponsor": ["list", "of", "sponsors"],
                    "line_of_therapy": ["first line", ...],
                    "biomarker": ["list", "of", "biomarkers"],
                    "enrollment_min": number or null,
                    "enrollment_max": number or null,
                    "geography": ["US", ...]
                }},
                "query_intent": "Detailed description of what the user is trying to learn",
                "search_strategy": "Detailed explanation of how to approach this search",
                "relevant_fields": ["list", "of", "database", "fields", "to", "search"],
                "confidence_score": 0.0-1.0,
                "semantic_analysis": "In-depth analysis of the query's meaning and implications",
                "suggested_follow_ups": ["list", "of", "follow-up", "questions", "or", "refinements"]
            }}
            """
            
            # Get LLM response - note that analyze_query is not async
            try:
                # Call the non-async analyze_query method
                analysis_result = analyzer.analyze_query(enhanced_prompt)
                
                # Convert the QueryAnalysisResult to a dictionary
                parsed_result = analysis_result.dict()
                
                # Normalize the filters
                filters = parsed_result.get("filters", {})
                for k, v in filters.items():
                    if v is None:
                        filters[k] = []
                    elif not isinstance(v, list):
                        filters[k] = [v]
                
                # Search for trials based on the extracted filters
                search_results = self.db.search_trials(filters, limit)
                
                # Format the response based on the requested format
                if format_type == "json":
                    # Return full JSON with both analysis and results
                    full_result = {
                        "analysis": parsed_result,
                        "results": search_results
                    }
                    return json.dumps(full_result, indent=2)
                
                elif format_type == "analysis":
                    # Focus on the analysis with minimal results
                    response = f"## Semantic Analysis of: '{query}'\n\n"
                    response += f"**Query Intent:** {parsed_result.get('query_intent', 'N/A')}\n\n"
                    response += f"**Search Strategy:** {parsed_result.get('search_strategy', 'N/A')}\n\n"
                    response += f"**Confidence Score:** {parsed_result.get('confidence_score', 'N/A')}\n\n"
                    
                    if "semantic_analysis" in parsed_result:
                        response += f"**Semantic Analysis:**\n{parsed_result['semantic_analysis']}\n\n"
                    
                    response += f"**Extracted Filters:**\n"
                    for filter_name, filter_values in filters.items():
                        if filter_values:
                            response += f"- {filter_name}: {', '.join(str(v) for v in filter_values)}\n"
                    
                    response += f"\n**Results Summary:** Found {len(search_results)} matching trials\n\n"
                    
                    if "suggested_follow_ups" in parsed_result and parsed_result["suggested_follow_ups"]:
                        response += "**Suggested Follow-ups:**\n"
                        for i, follow_up in enumerate(parsed_result["suggested_follow_ups"], 1):
                            response += f"{i}. {follow_up}\n"
                    
                    return response
                
                else:  # detailed format
                    # Comprehensive response with both analysis and detailed results
                    response = f"# Advanced Semantic Search Results\n\n"
                    response += f"**Query:** {query}\n\n"
                    response += f"**Intent:** {parsed_result.get('query_intent', 'N/A')}\n\n"
                    
                    if include_analysis:
                        response += f"**Search Strategy:** {parsed_result.get('search_strategy', 'N/A')}\n\n"
                        response += f"**Confidence:** {parsed_result.get('confidence_score', 'N/A')}\n\n"
                        
                        if "semantic_analysis" in parsed_result:
                            response += f"**Semantic Analysis:**\n{parsed_result['semantic_analysis']}\n\n"
                    
                    response += f"## Search Results ({len(search_results)} trials found)\n\n"
                    
                    if search_results:
                        for i, trial in enumerate(search_results[:min(10, len(search_results))], 1):
                            response += f"### {i}. {trial.get('nct_id', 'Unknown ID')}\n"
                            response += f"**Name:** {trial.get('trial_name', 'No name')}\n"
                            response += f"**Phase:** {trial.get('trial_phase', 'N/A')}\n"
                            response += f"**Status:** {trial.get('trial_status', 'N/A')}\n"
                            response += f"**Sponsor:** {trial.get('sponsor', 'N/A')}\n"
                            
                            if trial.get('primary_drug'):
                                response += f"**Drug:** {trial.get('primary_drug', 'N/A')}\n"
                            
                            if trial.get('indication'):
                                response += f"**Indication:** {trial.get('indication', 'N/A')}\n"
                            
                            response += "\n"
                        
                        if len(search_results) > 10:
                            response += f"... and {len(search_results) - 10} more trials\n\n"
                    else:
                        response += "No trials found matching the criteria.\n\n"
                        
                        # Provide suggestions when no results are found
                        response += "**Suggestions:**\n"
                        response += "- Try broadening your search terms\n"
                        response += "- Check spelling of drug or disease names\n"
                        response += "- Consider different trial phases or statuses\n"
                    
                    return response
                
            except json.JSONDecodeError:
                # Handle non-JSON responses from the model
                logger.warning(f"Non-JSON response from reasoning model: {analysis_result[:100]}...")
                
                # Attempt to extract some meaning from the text response
                filters = self._enhanced_fallback_parsing(query)
                search_results = self.db.search_trials(filters, limit)
                
                response = f"# Semantic Search Results (Fallback Mode)\n\n"
                response += f"**Query:** {query}\n\n"
                response += f"**Results:** Found {len(search_results)} trials\n\n"
                
                if search_results:
                    for i, trial in enumerate(search_results[:min(10, len(search_results))], 1):
                        response += f"{i}. **{trial.get('nct_id', 'Unknown')}**: {trial.get('trial_name', 'No name')}\n"
                        response += f"   Phase: {trial.get('trial_phase', 'N/A')}, Status: {trial.get('trial_status', 'N/A')}\n\n"
                
                return response
                
        except Exception as e:
            logger.error(f"Reasoning query failed: {str(e)}")
            raise AnalysisError(f"Reasoning query failed: {str(e)}")

    async def _compare_analysis(self, arguments: Dict[str, Any]) -> str:
        """
        AI-powered comparison of clinical trials using reasoning models
        """
        comparison_criteria = arguments["comparison_criteria"]
        auto_find_similar = arguments.get("auto_find_similar", True)
        analysis_depth = arguments.get("analysis_depth", "detailed")
        
        try:
            # Select model based on analysis depth
            model_name = "o3" if analysis_depth == "expert" else "o3-mini"
            analyzer = await self._get_analyzer(model_name)
            
            # First, use reasoning to extract search filters
            filters_prompt = f"""
            You are an expert clinical trial analyst. Extract structured search filters from this comparison request:
            
            REQUEST: "{comparison_criteria}"
            
            Return a JSON object with filters that would find relevant trials for this comparison:
            {{
                "filters": {{
                    "primary_drug": ["list", "of", "drug", "names"],
                    "indication": ["list", "of", "diseases"],
                    "trial_phase": ["PHASE1", "PHASE2", ...],
                    "trial_status": ["RECRUITING", ...],
                    "sponsor": ["list", "of", "sponsors"],
                    "line_of_therapy": ["first line", ...],
                    "biomarker": ["list", "of", "biomarkers"]
                }}
            }}
            """
            
            # Get filter results
            filter_response = analyzer.analyze_query(filters_prompt)
            
            try:
                # Parse filters
                filter_data = filter_response.dict()
                filters = filter_data.get("filters", {})
                
                # Normalize filters
                for k, v in filters.items():
                    if v is None:
                        filters[k] = []
                    elif not isinstance(v, list):
                        filters[k] = [v]
                
                # Search for trials
                trials = self.db.search_trials(filters, 20)
                
                if not trials:
                    return f"No trials found matching the criteria: {comparison_criteria}"
                
                # For detailed comparison, use reasoning model to analyze the trials
                if len(trials) >= 2:
                    # Prepare trial data for comparison
                    trial_data = []
                    for trial in trials[:10]:  # Limit to 10 trials for comparison
                        trial_data.append({
                            "nct_id": trial.get("nct_id", "Unknown"),
                            "name": trial.get("trial_name", "No name"),
                            "phase": trial.get("trial_phase", "N/A"),
                            "status": trial.get("trial_status", "N/A"),
                            "sponsor": trial.get("sponsor", "N/A"),
                            "drug": trial.get("primary_drug", "N/A"),
                            "indication": trial.get("indication", "N/A"),
                            "enrollment": trial.get("patient_enrollment", "N/A"),
                            "primary_endpoints": trial.get("primary_endpoints", "N/A"),
                            "secondary_endpoints": trial.get("secondary_endpoints", "N/A")
                        })
                    
                    # Create comparison prompt
                    comparison_prompt = f"""
                    You are an expert clinical trial analyst. Compare these clinical trials based on the following criteria:
                    
                    COMPARISON CRITERIA: "{comparison_criteria}"
                    
                    TRIALS TO COMPARE:
                    {json.dumps(trial_data, indent=2)}
                    
                    ANALYSIS DEPTH: {analysis_depth}
                    
                    Perform a {analysis_depth} comparison focusing on:
                    1. Key similarities and differences
                    2. Strengths and weaknesses of each trial
                    3. Methodological differences
                    4. Patient population differences
                    5. Endpoint differences
                    6. Statistical considerations
                    
                    Return your analysis in markdown format with appropriate headings and bullet points.
                    Include a summary table at the end comparing the key parameters across trials.
                    """
                    
                    # Get comparison analysis
                    comparison_result = analyzer.analyze_query(comparison_prompt)
                    
                    # Format the response
                    response = f"# Clinical Trial Comparison Analysis\n\n"
                    response += f"**Comparison Criteria:** {comparison_criteria}\n\n"
                    response += f"**Analysis Depth:** {analysis_depth}\n\n"
                    response += f"**Trials Compared:** {len(trial_data)}\n\n"
                    response += f"**Model Used:** {model_name}\n\n"
                    response += f"## Detailed Comparison\n\n"
                    response += comparison_result.query_intent  # Use query_intent as the comparison text
                    
                    return response
                else:
                    # Not enough trials for comparison
                    return f"Found only {len(trials)} trial(s) matching the criteria. At least 2 trials are needed for comparison."
            
            except json.JSONDecodeError:
                # Handle non-JSON responses
                logger.warning(f"Non-JSON response from reasoning model: {filter_response[:100]}...")
                
                # Fallback to basic comparison
                trials = self.db.search_trials({}, 10)
                
                response = f"# Clinical Trial Comparison (Basic)\n\n"
                response += f"**Comparison Criteria:** {comparison_criteria}\n\n"
                response += f"**Found {len(trials)} trials for basic comparison**\n\n"
                
                # Create a simple comparison table
                response += "## Trial Comparison Table\n\n"
                response += "| NCT ID | Trial Name | Phase | Status | Sponsor |\n"
                response += "|--------|------------|-------|--------|--------|\n"
                
                for trial in trials[:10]:
                    response += f"| {trial.get('nct_id', 'Unknown')} | {trial.get('trial_name', 'No name')[:30]}... | "
                    response += f"{trial.get('trial_phase', 'N/A')} | {trial.get('trial_status', 'N/A')} | "
                    response += f"{trial.get('sponsor', 'N/A')} |\n"
                
                return response
                
        except Exception as e:
            logger.error(f"Compare analysis failed: {str(e)}")
            raise AnalysisError(f"Compare analysis failed: {str(e)}")

    async def _trend_analysis(self, arguments: Dict[str, Any]) -> str:
        """
        Analyze trends and patterns in clinical trial data using reasoning models
        """
        trend_query = arguments["trend_query"]
        time_period = arguments.get("time_period", "last 5 years")
        group_by = arguments.get("group_by", "drug")
        include_insights = arguments.get("include_insights", True)
        
        try:
            # Select model based on grouping complexity
            model_name = "o3" if group_by == "expert" else "o3-mini"
            analyzer = await self._get_analyzer(model_name)
            
            # Get all trials for trend analysis
            all_trials = self.db.search_trials({}, 1000)
            
            if not all_trials:
                return "No trials found in the database for trend analysis."
            
            # Group trials based on the specified parameter
            grouped_data = {}
            
            if group_by == "drug":
                for trial in all_trials:
                    drug = trial.get("primary_drug", "Unknown")
                    if drug not in grouped_data:
                        grouped_data[drug] = []
                    grouped_data[drug].append(trial)
            
            elif group_by == "indication":
                for trial in all_trials:
                    indication = trial.get("indication", "Unknown")
                    if indication not in grouped_data:
                        grouped_data[indication] = []
                    grouped_data[indication].append(trial)
            
            elif group_by == "phase":
                for trial in all_trials:
                    phase = trial.get("trial_phase", "Unknown")
                    if phase not in grouped_data:
                        grouped_data[phase] = []
                    grouped_data[phase].append(trial)
            
            elif group_by == "sponsor":
                for trial in all_trials:
                    sponsor = trial.get("sponsor", "Unknown")
                    if sponsor not in grouped_data:
                        grouped_data[sponsor] = []
                    grouped_data[sponsor].append(trial)
            
            else:  # expert grouping - use the model to determine the best grouping
                # Prepare a simplified trial dataset for the model
                simplified_trials = []
                for trial in all_trials[:100]:  # Limit to 100 trials for performance
                    simplified_trials.append({
                        "nct_id": trial.get("nct_id", "Unknown"),
                        "name": trial.get("trial_name", "No name"),
                        "phase": trial.get("trial_phase", "N/A"),
                        "status": trial.get("trial_status", "N/A"),
                        "sponsor": trial.get("sponsor", "N/A"),
                        "drug": trial.get("primary_drug", "N/A"),
                        "indication": trial.get("indication", "N/A"),
                        "enrollment": trial.get("patient_enrollment", "N/A")
                    })
                
                # Create expert grouping prompt
                expert_prompt = f"""
                You are an expert clinical trial analyst. Analyze these trials and identify the most meaningful groupings based on this query:
                
                TREND QUERY: "{trend_query}"
                TIME PERIOD: {time_period}
                
                TRIAL DATA:
                {json.dumps(simplified_trials[:20], indent=2)}  # Send only first 20 for prompt size
                
                Based on the query, determine the most insightful way to group these trials. Then create a JSON response with:
                1. The recommended grouping approach
                2. The rationale for this grouping
                3. Key trends observed across the dataset
                4. Recommendations for further analysis
                
                Format your response as:
                {{
                    "recommended_grouping": "name of grouping parameter",
                    "grouping_rationale": "explanation of why this grouping is insightful",
                    "observed_trends": ["list", "of", "key", "trends"],
                    "recommendations": ["list", "of", "recommendations"]
                }}
                """
                
                # Get expert grouping recommendation
                expert_response = analyzer.analyze_query(expert_prompt)
                
                try:
                    # Parse expert recommendation
                    expert_data = expert_response.dict()
                    recommended_grouping = expert_data.get("recommended_grouping", "drug")
                    
                    # Re-group based on recommendation
                    for trial in all_trials:
                        group_value = trial.get(recommended_grouping, "Unknown")
                        if group_value not in grouped_data:
                            grouped_data[group_value] = []
                        grouped_data[group_value].append(trial)
                    
                    # Use the expert grouping for the response
                    group_by = recommended_grouping
                    
                except json.JSONDecodeError:
                    # Fallback to drug grouping if expert recommendation fails
                    for trial in all_trials:
                        drug = trial.get("primary_drug", "Unknown")
                        if drug not in grouped_data:
                            grouped_data[drug] = []
                        grouped_data[drug].append(trial)
            
            # Generate trend analysis
            if include_insights:
                # Prepare data for trend analysis
                trend_data = {
                    "query": trend_query,
                    "time_period": time_period,
                    "group_by": group_by,
                    "total_trials": len(all_trials),
                    "groups": {}
                }
                
                # Add summary data for each group
                for group_name, trials in grouped_data.items():
                    if group_name == "Unknown" or not group_name:
                        continue
                        
                    trend_data["groups"][group_name] = {
                        "trial_count": len(trials),
                        "phases": {},
                        "statuses": {},
                        "avg_enrollment": sum(trial.get("patient_enrollment", 0) or 0 for trial in trials) / max(len(trials), 1)
                    }
                    
                    # Count phases and statuses
                    for trial in trials:
                        phase = trial.get("trial_phase", "Unknown")
                        status = trial.get("trial_status", "Unknown")
                        
                        if phase not in trend_data["groups"][group_name]["phases"]:
                            trend_data["groups"][group_name]["phases"][phase] = 0
                        trend_data["groups"][group_name]["phases"][phase] += 1
                        
                        if status not in trend_data["groups"][group_name]["statuses"]:
                            trend_data["groups"][group_name]["statuses"][status] = 0
                        trend_data["groups"][group_name]["statuses"][status] += 1
                
                # Create trend analysis prompt
                trend_prompt = f"""
                You are an expert clinical trial analyst. Analyze this trend data and provide insights:
                
                TREND QUERY: "{trend_query}"
                TIME PERIOD: {time_period}
                GROUPING BY: {group_by}
                
                TREND DATA:
                {json.dumps(trend_data, indent=2)}
                
                Provide a comprehensive trend analysis in markdown format that includes:
                1. Summary of key findings
                2. Major trends observed
                3. Comparative analysis across groups
                4. Insights on trial phases and status distribution
                5. Recommendations for further investigation
                
                Format your response with appropriate headings, bullet points, and emphasis.
                """
                
                # Get trend analysis
                trend_analysis = analyzer.analyze_query(trend_prompt)
                
                # Format the response
                response = f"# Clinical Trial Trend Analysis\n\n"
                response += f"**Trend Query:** {trend_query}\n\n"
                response += f"**Time Period:** {time_period}\n\n"
                response += f"**Grouped By:** {group_by}\n\n"
                response += f"**Total Trials Analyzed:** {len(all_trials)}\n\n"
                response += f"**Model Used:** {model_name}\n\n"
                response += trend_analysis.query_intent  # Use query_intent for the analysis text
                
                return response
            
            else:
                # Basic trend analysis without AI insights
                response = f"# Clinical Trial Trend Analysis\n\n"
                response += f"**Trend Query:** {trend_query}\n\n"
                response += f"**Time Period:** {time_period}\n\n"
                response += f"**Grouped By:** {group_by}\n\n"
                response += f"**Total Trials Analyzed:** {len(all_trials)}\n\n"
                
                # Add group statistics
                response += "## Group Statistics\n\n"
                response += "| Group | Trial Count | Top Phase | Top Status |\n"
                response += "|-------|------------|-----------|------------|\n"
                
                for group_name, trials in sorted(grouped_data.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
                    if group_name == "Unknown" or not group_name:
                        continue
                        
                    # Count phases and statuses
                    phases = {}
                    statuses = {}
                    for trial in trials:
                        phase = trial.get("trial_phase", "Unknown")
                        status = trial.get("trial_status", "Unknown")
                        
                        if phase not in phases:
                            phases[phase] = 0
                        phases[phase] += 1
                        
                        if status not in statuses:
                            statuses[status] = 0
                        statuses[status] += 1
                    
                    # Find top phase and status
                    top_phase = max(phases.items(), key=lambda x: x[1])[0] if phases else "N/A"
                    top_status = max(statuses.items(), key=lambda x: x[1])[0] if statuses else "N/A"
                    
                    response += f"| {group_name} | {len(trials)} | {top_phase} | {top_status} |\n"
                
                return response
                
        except Exception as e:
            logger.error(f"Trend analysis failed: {str(e)}")
            raise AnalysisError(f"Trend analysis failed: {str(e)}")

    async def _parse_natural_language_query(self, query: str) -> Dict[str, Any]:
        """Use advanced LLM reasoning to intelligently parse natural language query into structured search filters"""
        try:
            # Use the reasoning model to understand the query with enhanced prompt
            analyzer = await self._get_analyzer("o3-mini")

            enhanced_prompt = f"""
            You are an expert clinical trial search assistant. Analyze this natural language query and extract structured search parameters.

            QUERY: "{query}"

            DATABASE SCHEMA:
            - nct_id: Trial identifier (e.g., NCT07046273)
            - trial_name: Full trial name and description
            - trial_phase: PHASE1, PHASE2, PHASE3, PHASE4, PHASE1/2, PHASE2/3
            - trial_status: RECRUITING, COMPLETED, TERMINATED, NOT_YET_RECRUITING, ACTIVE_NOT_RECRUITING, SUSPENDED, WITHDRAWN, ENROLLING_BY_INVITATION
            - sponsor: Company or institution name
            - primary_drug: Main drug being tested
            - indication: Disease or condition being treated
            - line_of_therapy: First line, second line, etc.
            - patient_enrollment: Number of participants
            - start_date: Trial start date
            - primary_completion_date: Expected completion date
            - primary_endpoints: Main trial objectives
            - secondary_endpoints: Additional objectives
            - inclusion_criteria: Patient eligibility criteria
            - exclusion_criteria: Patient exclusion criteria
            - trial_countries: Countries where trial is conducted
            - geography: Global, US, Europe, Asia, etc.

            TASK: Extract search filters from the natural language query. For each filter (e.g., drug, indication, sponsor), return a LIST of all possible synonyms, brand names, and related terms that could match in the database. If only one term is found, return a single-item list. If no value, return an empty list or null.

            RESPONSE FORMAT: Return a JSON object with the following structure:
            {{
                "filters": {{
                    "primary_drug": ["list", "of", "drug", "names"],
                    "indication": ["list", "of", "diseases"],
                    "trial_phase": ["PHASE1", "PHASE2", ...],
                    "trial_status": ["RECRUITING", ...],
                    "sponsor": ["list", "of", "sponsors"],
                    "line_of_therapy": ["first line", ...],
                    "biomarker": ["list", "of", "biomarkers"],
                    "enrollment_min": number or null,
                    "enrollment_max": number or null,
                    "geography": ["US", ...]
                }},
                "query_intent": "Brief description of what the user is looking for",
                "search_strategy": "How to approach this search",
                "confidence_score": 0.0-1.0,
                "extracted_terms": ["list", "of", "key", "terms", "extracted"]
            }}

            EXAMPLES:
            Query: "Show me trials for semaglutide or Ozempic"
            Response: {{
                "filters": {{
                    "primary_drug": ["semaglutide", "ozempic"],
                    "indication": [],
                    ...
                }},
                ...
            }}

            Query: "Find Phase 3 trials for metastatic bladder cancer using checkpoint inhibitors"
            Response: {{
                "filters": {{
                    "indication": "metastatic bladder cancer",
                    "trial_phase": "PHASE3",
                    "primary_drug": "checkpoint inhibitors"
                }},
                "query_intent": "User wants Phase 3 clinical trials for metastatic bladder cancer that use checkpoint inhibitors",
                "search_strategy": "Search for trials with bladder cancer indication, Phase 3, and checkpoint inhibitor drugs",
                "confidence_score": 0.95,
                "extracted_terms": ["phase 3", "metastatic bladder cancer", "checkpoint inhibitors"]
            }}

            Query: "Show me recruiting diabetes trials with semaglutide in the US"
            Response: {{
                "filters": {{
                    "indication": "diabetes",
                    "primary_drug": "semaglutide",
                    "trial_status": "RECRUITING",
                    "geography": "US"
                }},
                "query_intent": "User wants currently recruiting diabetes trials using semaglutide in the United States",
                "search_strategy": "Search for diabetes trials with semaglutide, recruiting status, and US geography",
                "confidence_score": 0.92,
                "extracted_terms": ["diabetes", "semaglutide", "recruiting", "US"]
            }}

            Query: "Large trials for breast cancer immunotherapy"
            Response: {{
                "filters": {{
                    "indication": "breast cancer",
                    "primary_drug": "immunotherapy",
                    "enrollment_min": 100
                }},
                "query_intent": "User wants large clinical trials for breast cancer using immunotherapy",
                "search_strategy": "Search for breast cancer trials with immunotherapy and minimum enrollment of 100",
                "confidence_score": 0.88,
                "extracted_terms": ["breast cancer", "immunotherapy", "large trials"]
            }}

            Now analyze the provided query and return the structured JSON response. Return ONLY the JSON object, no additional text.
            """

            # Get LLM response
            try:
                response = await analyzer.analyze_query(enhanced_prompt)
                import json

                result = json.loads(response)
                if not isinstance(result, dict):
                    raise ValueError("Response is not a dictionary")
                if "filters" not in result:
                    result["filters"] = {}
                # Accept both single values and lists, but always convert to list for downstream
                for k, v in result["filters"].items():
                    if v is None:
                        result["filters"][k] = []
                    elif not isinstance(v, list):
                        result["filters"][k] = [v]
                logger.info(
                    f"LLM parsed query '{query}' into filters: {result['filters']}"
                )
                return result
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Failed to parse LLM response for query '{query}': {e}")
                logger.warning(f"Raw response: {response}")
                # Fallback to enhanced string-based parsing
                return self._enhanced_fallback_parsing(query)
            except Exception as e:
                logger.error(f"LLM query parsing failed for '{query}': {e}")
                # Fallback to enhanced string-based parsing
                return self._enhanced_fallback_parsing(query)
        except Exception as e:
            logger.error(f"Error in _parse_natural_language_query: {e}")
            raise

    def _enhanced_fallback_parsing(self, query: str) -> Dict[str, Any]:
        """Enhanced fallback method for query parsing using advanced string processing"""
        import re

        filters = {}
        query_lower = query.lower()

        # Enhanced disease/indication extraction
        disease_patterns = {
            "diabetes": ["diabetes", "diabetic", "t2dm", "type 2 diabetes"],
            "cancer": [
                "cancer",
                "oncology",
                "tumor",
                "malignant",
                "carcinoma",
                "sarcoma",
                "leukemia",
                "lymphoma",
            ],
            "breast cancer": ["breast cancer", "mammary cancer"],
            "lung cancer": [
                "lung cancer",
                "pulmonary cancer",
                "non-small cell",
                "nsclc",
                "small cell",
                "sclc",
            ],
            "bladder cancer": [
                "bladder cancer",
                "urothelial cancer",
                "urothelial carcinoma",
            ],
            "prostate cancer": ["prostate cancer", "prostatic cancer"],
            "colorectal cancer": ["colorectal cancer", "colon cancer", "rectal cancer"],
            "pancreatic cancer": ["pancreatic cancer", "pancreas cancer"],
            "ovarian cancer": ["ovarian cancer", "ovary cancer"],
            "melanoma": ["melanoma", "skin cancer"],
            "leukemia": ["leukemia", "aml", "all", "cll", "cml"],
            "lymphoma": ["lymphoma", "hodgkin", "non-hodgkin", "nhl"],
            "heart disease": ["heart disease", "cardiovascular", "cardiac", "coronary"],
            "kidney disease": ["kidney disease", "renal", "nephropathy"],
            "liver disease": ["liver disease", "hepatic", "hepatitis"],
            "alzheimer": ["alzheimer", "dementia", "cognitive"],
            "parkinson": ["parkinson", "parkinson's"],
            "multiple sclerosis": ["multiple sclerosis", "ms"],
            "rheumatoid arthritis": ["rheumatoid arthritis", "ra"],
            "psoriasis": ["psoriasis", "psoriatic"],
            "asthma": ["asthma", "asthmatic"],
            "copd": ["copd", "chronic obstructive"],
            "fibrosis": ["fibrosis", "pulmonary fibrosis", "cystic fibrosis"],
            "sickle cell": ["sickle cell", "sickle cell anemia"],
            "hemophilia": ["hemophilia", "hemophiliac"],
        }

        for disease, patterns in disease_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                filters["indication"] = disease
                break

        # Enhanced drug extraction
        drug_patterns = {
            "semaglutide": ["semaglutide", "ozempic", "wegovy", "rybelsus"],
            "pembrolizumab": ["pembrolizumab", "keytruda"],
            "nivolumab": ["nivolumab", "opdivo"],
            "atezolizumab": ["atezolizumab", "tecentriq"],
            "durvalumab": ["durvalumab", "imfinzi"],
            "avelumab": ["avelumab", "bavencio"],
            "tremelimumab": ["tremelimumab"],
            "ipilimumab": ["ipilimumab", "yervoy"],
            "trastuzumab": ["trastuzumab", "herceptin"],
            "bevacizumab": ["bevacizumab", "avastin"],
            "cetuximab": ["cetuximab", "erbitux"],
            "panitumumab": ["panitumumab", "vectibix"],
            "rituximab": ["rituximab", "rituxan"],
            "obinutuzumab": ["obinutuzumab", "gazyva"],
            "daratumumab": ["daratumumab", "darzalex"],
            "elotuzumab": ["elotuzumab", "emplicti"],
            "brentuximab": ["brentuximab", "adcetris"],
            "polatuzumab": ["polatuzumab", "polivy"],
            "enfortumab": ["enfortumab", "padcev"],
            "sacituzumab": ["sacituzumab", "trodelvy"],
            "tisotumab": ["tisotumab", "tivdak"],
            "mirvetuximab": ["mirvetuximab", "elahere"],
            "checkpoint inhibitors": [
                "checkpoint inhibitor",
                "pdl1",
                "pd-l1",
                "pd1",
                "pd-1",
                "ctla4",
                "ctla-4",
            ],
            "immunotherapy": ["immunotherapy", "immune therapy", "immune checkpoint"],
            "adc": ["adc", "antibody drug conjugate", "antibody-drug conjugate"],
            "car-t": ["car-t", "car t", "chimeric antigen receptor"],
            "bispecific": ["bispecific", "bi-specific", "dual targeting"],
            "adc": ["adc", "antibody drug conjugate", "antibody-drug conjugate"],
            "vaccine": ["vaccine", "vaccination"],
            "hormone therapy": [
                "hormone therapy",
                "hormonal therapy",
                "endocrine therapy",
            ],
            "chemotherapy": ["chemotherapy", "chemo", "cytotoxic"],
            "targeted therapy": [
                "targeted therapy",
                "targeted treatment",
                "precision medicine",
            ],
            "gene therapy": ["gene therapy", "gene editing", "crispr"],
            "cell therapy": ["cell therapy", "stem cell", "cellular therapy"],
        }

        for drug, patterns in drug_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                filters["primary_drug"] = drug
                break

        # Enhanced phase extraction
        phase_patterns = {
            "PHASE1": ["phase 1", "phase i", "phase1", "phasei"],
            "PHASE2": ["phase 2", "phase ii", "phase2", "phaseii"],
            "PHASE3": ["phase 3", "phase iii", "phase3", "phaseiii"],
            "PHASE4": ["phase 4", "phase iv", "phase4", "phaseiv"],
            "PHASE1/2": ["phase 1/2", "phase i/ii", "phase1/2", "phasei/ii"],
            "PHASE2/3": ["phase 2/3", "phase ii/iii", "phase2/3", "phaseii/iii"],
        }

        for phase, patterns in phase_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                filters["trial_phase"] = phase
                break

        # Enhanced status extraction
        status_patterns = {
            "RECRUITING": [
                "recruiting",
                "enrolling",
                "open",
                "active",
                "currently recruiting",
            ],
            "COMPLETED": ["completed", "finished", "done", "concluded"],
            "TERMINATED": ["terminated", "stopped", "discontinued", "cancelled"],
            "NOT_YET_RECRUITING": [
                "not yet recruiting",
                "not recruiting yet",
                "planning",
            ],
            "ACTIVE_NOT_RECRUITING": [
                "active not recruiting",
                "active but not recruiting",
            ],
            "SUSPENDED": ["suspended", "on hold", "paused"],
            "WITHDRAWN": ["withdrawn", "withdrew", "cancelled"],
            "ENROLLING_BY_INVITATION": ["enrolling by invitation", "invitation only"],
        }

        for status, patterns in status_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                filters["trial_status"] = status
                break

        # Geographic extraction
        geo_patterns = {
            "US": ["us", "united states", "usa", "america", "american"],
            "Europe": ["europe", "european", "eu", "european union"],
            "Asia": ["asia", "asian", "china", "japan", "korea"],
            "Global": ["global", "worldwide", "international", "multi-national"],
        }

        for geo, patterns in geo_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                filters["geography"] = geo
                break

        # Enrollment size extraction
        enrollment_patterns = {
            "large": ["large", "big", "major", "extensive"],
            "small": ["small", "minor", "limited", "pilot"],
            "medium": ["medium", "moderate", "standard"],
        }

        for size, patterns in enrollment_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                if size == "large":
                    filters["enrollment_min"] = 100
                elif size == "small":
                    filters["enrollment_max"] = 50
                break

        # Numeric enrollment extraction
        enrollment_numbers = re.findall(
            r"(\d+)\s*(?:patients?|participants?|subjects?)", query_lower
        )
        if enrollment_numbers:
            try:
                number = int(enrollment_numbers[0])
                if "minimum" in query_lower or "at least" in query_lower:
                    filters["enrollment_min"] = number
                elif "maximum" in query_lower or "up to" in query_lower:
                    filters["enrollment_max"] = number
                else:
                    # Default to minimum if no context
                    filters["enrollment_min"] = number
            except ValueError:
                pass

        # Line of therapy extraction
        therapy_patterns = {
            "first line": ["first line", "1st line", "initial", "primary"],
            "second line": ["second line", "2nd line", "secondary"],
            "third line": ["third line", "3rd line", "tertiary"],
            "maintenance": ["maintenance", "maintenance therapy"],
            "adjuvant": ["adjuvant", "adjuvant therapy"],
            "neoadjuvant": ["neoadjuvant", "neoadjuvant therapy"],
        }

        for therapy, patterns in therapy_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                filters["line_of_therapy"] = therapy
                break

        # Sponsor type extraction
        sponsor_patterns = {
            "industry": [
                "industry",
                "pharmaceutical",
                "pharma",
                "biotech",
                "biotechnology",
                "company",
                "corporate",
            ],
            "academic": [
                "academic",
                "university",
                "medical center",
                "hospital",
                "institution",
            ],
            "government": ["government", "federal", "national", "public"],
        }

        for sponsor_type, patterns in sponsor_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                filters["sponsor"] = sponsor_type
                break

        # Time period extraction
        time_patterns = {
            "recent": ["recent", "latest", "new", "current", "ongoing"],
            "completed": ["completed", "finished", "past", "historical"],
            "upcoming": ["upcoming", "future", "planned", "scheduled"],
        }

        for time_period, patterns in time_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                if time_period == "recent":
                    filters["trial_status"] = "RECRUITING"
                elif time_period == "completed":
                    filters["trial_status"] = "COMPLETED"
                break

        # Create structured result
        result = {
            "filters": filters,
            "query_intent": f"User is searching for clinical trials matching: {query}",
            "search_strategy": f"Apply extracted filters: {list(filters.keys())}",
            "confidence_score": 0.7 if filters else 0.3,
            "extracted_terms": list(filters.values()) if filters else [],
        }

        logger.info(f"Enhanced fallback parsed query '{query}' into: {result}")
        return result

    def _format_table(self, results: List[Dict[str, Any]]) -> str:
        """Format results as a markdown table"""
        if not results:
            return "No results found."

        # Select key fields for display
        key_fields = [
            "nct_id",
            "trial_name",
            "trial_phase",
            "trial_status",
            "primary_drug",
            "indication",
        ]
        display_fields = [
            field for field in key_fields if any(field in result for result in results)
        ]

        result = f"## Found {len(results)} trials\n\n"
        result += "| " + " | ".join(display_fields) + " |\n"
        result += "|" + "|".join(["---" for _ in display_fields]) + "|\n"

        for trial in results:
            row = []
            for field in display_fields:
                value = trial.get(field, "N/A")
                if isinstance(value, str) and len(value) > 30:
                    value = value[:27] + "..."
                row.append(str(value))
            result += "| " + " | ".join(row) + " |\n"

        return result

    def _format_summary(self, results: List[Dict[str, Any]]) -> str:
        """Format results as a summary"""
        if not results:
            return "No results found."

        result = f"## Summary: {len(results)} trials found\n\n"

        # Count by phase
        phases = {}
        for trial in results:
            phase = trial.get("trial_phase", "Unknown")
            phases[phase] = phases.get(phase, 0) + 1

        result += "### By Phase:\n"
        for phase, count in phases.items():
            result += f"- {phase}: {count} trials\n"

        return result

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="clinical-trial-mcp-server-fixed",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )


def main():
    """Main function to run the MCP server"""
    try:
        server = ClinicalTrialMCPServer()
        print("🏥 Clinical Trial MCP Server - Fixed Version")
        print("=" * 50)
        print("Starting MCP server...")
        print("Available tools:")
        print("- store_trial: Store clinical trials")
        print("- search_trials: Search with filters")
        print("- get_trial_details: Get trial details")
        print("- smart_search: Natural language search")
        print("=" * 50)
        asyncio.run(server.run())
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please ensure all required modules are available.")
    except Exception as e:
        print(f"❌ Server Error: {e}")
        logger.error(f"Server error: {e}")


if __name__ == "__main__":
    main()
