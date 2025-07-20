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

# Add src to Python path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Fixed imports with proper fallback
try:
    from database.clinical_trial_database import ClinicalTrialDatabase
    from analysis.clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning
    from analysis.clinical_trial_analyzer_llm import ClinicalTrialAnalyzerLLM
except ImportError:
    # Fallback for direct execution from project root
    try:
        from src.database.clinical_trial_database import ClinicalTrialDatabase
        from src.analysis.clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning
        from src.analysis.clinical_trial_analyzer_llm import ClinicalTrialAnalyzerLLM
    except ImportError:
        # Final fallback - try to find modules in current directory
        print("Warning: Could not import required modules. Please ensure you're running from the project root.")
        ClinicalTrialDatabase = None
        ClinicalTrialAnalyzerReasoning = None
        ClinicalTrialAnalyzerLLM = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache for {key}: {e}")
            cache_file.unlink()  # Remove corrupted cache
            return None
    
    def set_cached_data(self, key: str, data: Dict[str, Any]):
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, 'w') as f:
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
            if not hasattr(self, 'api_key') or not self.api_key:
                raise AnalysisError("OpenAI API key not available")
            
            try:
                if model_name == "llm":
                    self.analyzers[model_name] = ClinicalTrialAnalyzerLLM(self.api_key)
                else:
                    self.analyzers[model_name] = ClinicalTrialAnalyzerReasoning(self.api_key, model=model_name)
                logger.info(f"Initialized analyzer for model: {model_name}")
            except Exception as e:
                raise AnalysisError(f"Failed to initialize analyzer for {model_name}: {e}")
        
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
                raise ValidationError(f"Invalid model: {arguments['analyze_with_model']}")
    
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
                                "nct_id": {"type": "string", "description": "NCT ID of the trial"},
                                "json_file_path": {"type": "string", "description": "Path to JSON file (optional)"},
                                "analyze_with_model": {"type": "string", "enum": ["gpt-4o", "gpt-4o-mini", "o4-mini", "gpt-4", "llm"], "default": "gpt-4o-mini", "description": "Model to use for analysis"},
                                "force_reanalyze": {"type": "boolean", "default": False, "description": "Force reanalysis even if trial exists"}
                            },
                            "required": ["nct_id"]
                        }
                    ),
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
                                        "enrollment_max": {"type": "integer"}
                                    }
                                },
                                "limit": {"type": "integer", "default": 50},
                                "format": {"type": "string", "enum": ["table", "json", "summary"], "default": "table"}
                            }
                        }
                    ),
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
                    )
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
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
                        raise ValidationError("nct_id is required for get_trial_details")
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
                    content=[TextContent(type="text", text=f"Validation Error: {str(e)}")]
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
            success = await self._store_trial_data(result, {
                "analysis_model": analyze_with_model,
                "analysis_timestamp": datetime.now().isoformat(),
                "source_file": json_file_path
            })
            
            if success:
                # Cache the result
                if self.cache_manager:
                    self.cache_manager.set_cached_data(cache_key, result)
                
                return f"✅ Successfully stored trial {nct_id} using {analyze_with_model} model"
            else:
                raise DatabaseError(f"Failed to store trial {nct_id}")
                
        except Exception as e:
            raise AnalysisError(f"Error processing trial {nct_id}: {str(e)}")
    
    async def _store_trial_data(self, trial_data: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
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
    
    async def _perform_search(self, query: str, filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
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
                result += f"- **Enrollment:** {trial.get('patient_enrollment', 'N/A')}\n"
                result += f"- **Sponsor:** {trial.get('sponsor', 'N/A')}\n"
                
                result += "\n## Drug Information\n"
                result += f"- **Primary Drug:** {trial.get('primary_drug', 'N/A')}\n"
                result += f"- **MoA:** {trial.get('primary_drug_moa', 'N/A')}\n"
                result += f"- **Target:** {trial.get('primary_drug_target', 'N/A')}\n"
                
                result += "\n## Clinical Information\n"
                result += f"- **Indication:** {trial.get('indication', 'N/A')}\n"
                result += f"- **Line of Therapy:** {trial.get('line_of_therapy', 'N/A')}\n"
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
        """Use AI to intelligently parse natural language query into search terms"""
        try:
            # Use the reasoning model to understand the query
            analyzer = await self._get_analyzer("o3-mini")
            
            prompt = f"""
            Analyze this clinical trial search query and extract relevant search terms:
            Query: "{query}"
            
            Available database fields to search:
            - trial_name: Contains disease names, drug names, trial descriptions
            - trial_phase: PHASE1, PHASE2, PHASE3, PHASE4
            - trial_status: RECRUITING, COMPLETED, TERMINATED, etc.
            - sponsor: Company or institution name
            - primary_endpoints: Trial objectives
            - secondary_endpoints: Additional objectives
            
            Return a JSON object with search terms that should be used to find relevant trials.
            Focus on the most important terms that would appear in trial names or descriptions.
            
            Example outputs:
            - "diabetes trials" → {{"search_terms": ["diabetes", "type 2 diabetes"]}}
            - "semaglutide phase 3" → {{"search_terms": ["semaglutide", "ozempic"], "phase": "PHASE3"}}
            - "bladder cancer immunotherapy" → {{"search_terms": ["bladder", "urothelial", "immunotherapy", "checkpoint inhibitor"]}}
            
            Return only the JSON object, no other text.
            """
            
            response = await analyzer.analyze_query(prompt)
            
            # Parse the AI response
            try:
                import json
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Fallback to basic extraction if AI parsing fails
                return self._fallback_query_parsing(query)
                
        except Exception as e:
            # Fallback to basic extraction if AI analysis fails
            return self._fallback_query_parsing(query)
    
    def _fallback_query_parsing(self, query: str) -> Dict[str, Any]:
        """Fallback method for basic query parsing"""
        filters = {}
        query_lower = query.lower()
        
        # Basic keyword extraction
        if "diabetes" in query_lower:
            filters["search_terms"] = ["diabetes"]
        if "cancer" in query_lower or "oncology" in query_lower:
            filters["search_terms"] = ["cancer"]
        if "semaglutide" in query_lower or "ozempic" in query_lower:
            filters["search_terms"] = ["semaglutide"]
        
        # Phase extraction
        if "phase 3" in query_lower or "phase iii" in query_lower:
            filters["phase"] = "PHASE3"
        elif "phase 2" in query_lower or "phase ii" in query_lower:
            filters["phase"] = "PHASE2"
        elif "phase 1" in query_lower or "phase i" in query_lower:
            filters["phase"] = "PHASE1"
        
        return filters
    
    def _format_table(self, results: List[Dict[str, Any]]) -> str:
        """Format results as a markdown table"""
        if not results:
            return "No results found."
        
        # Select key fields for display
        key_fields = ["nct_id", "trial_name", "trial_phase", "trial_status", "primary_drug", "indication"]
        display_fields = [field for field in key_fields if any(field in result for result in results)]
        
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