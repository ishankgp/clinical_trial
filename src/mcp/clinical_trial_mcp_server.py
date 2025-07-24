#!/usr/bin/env python3
"""
Clinical Trial MCP Server - Fixed Version
Addresses logic gaps in the original implementation
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime
import os
import sys
from pathlib import Path
import sqlite3
import pandas as pd
from contextlib import asynccontextmanager

# MCP imports
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
except Exception:  # pragma: no cover - fallback to local stubs
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
    )

    def stdio_server(*args, **kwargs):
        pass


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
            self.db = ClinicalTrialDatabase()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

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
        """Initialize AI analyzers"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY not found in environment")
                return

            # Initialize analyzers lazily when needed
            self.api_key = api_key
            logger.info("Analyzers ready for initialization")
        except Exception as e:
            logger.warning(f"Failed to initialize analyzers: {e}")

    async def _get_analyzer(self, model_name: str) -> Any:
        """Get or create analyzer for specified model"""
        if model_name not in self.analyzers:
            if not hasattr(self, "api_key") or not self.api_key:
                raise AnalysisError("OpenAI API key not available")

            try:
                if model_name == "llm":
                    self.analyzers[model_name] = ClinicalTrialAnalyzerLLM(self.api_key)
                else:
                    self.analyzers[model_name] = ClinicalTrialAnalyzerReasoning(
                        self.api_key, model=model_name
                    )
                logger.info(f"Initialized analyzer for model: {model_name}")
            except Exception as e:
                raise AnalysisError(
                    f"Failed to initialize analyzer for {model_name}: {e}"
                )

        return self.analyzers[model_name]

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
            valid_models = ["gpt-4o", "gpt-4o-mini", "o4-mini", "gpt-4", "llm"]
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
                                        "o4-mini",
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
            ai_filters = await self._parse_natural_language_query(query)
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
            filters = await self._parse_natural_language_query(query)
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
