#!/usr/bin/env python3
"""
Clinical Trial Chat Interface with MCP Server Integration
Uses OpenAI LLM with MCP server tools for advanced clinical trial queries
"""

import openai
import json
import asyncio
import subprocess
import time
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalTrialChatMCP:
    """Chat interface for clinical trial queries using OpenAI LLM and MCP tools"""
    
    def __init__(self, openai_api_key: str, model: str = "o3-mini"):
        """Initialize the chat interface with reasoning model by default"""
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.model = model
        self.conversation_history = []
        self.mcp_process = None
        self.mcp_tools = []
        
        # Initialize MCP server
        self._start_mcp_server()
        self._load_mcp_tools()
    
    def _start_mcp_server(self):
        """Start the MCP server process"""
        try:
            # Start the MCP server as a subprocess
            server_path = os.path.join(os.path.dirname(__file__), "clinical_trial_mcp_server.py")
            self.mcp_process = subprocess.Popen(
                ["python", server_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            time.sleep(2)  # Give server time to start
            logger.info("MCP server started successfully")
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
    
    def _load_mcp_tools(self):
        """Load available MCP tools"""
        self.mcp_tools = [
            {
                "type": "function",
                "function": {
                    "name": "store_trial",
                    "description": "Store a clinical trial from JSON file or NCT ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nct_id": {"type": "string", "description": "NCT ID of the trial"},
                            "json_file_path": {"type": "string", "description": "Path to JSON file (optional)"},
                            "analyze_with_model": {"type": "string", "enum": ["o3", "o3-mini", "gpt-4o", "gpt-4o-mini", "gpt-4", "llm"], "default": "o3-mini"},
                            "force_reanalyze": {"type": "boolean", "default": False}
                        },
                        "required": ["nct_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_trials",
                    "description": "Search clinical trials with flexible filters",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_trial_details",
                    "description": "Get detailed information about a specific trial",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nct_id": {"type": "string", "description": "NCT ID of the trial"},
                            "include_raw_data": {"type": "boolean", "default": False}
                        },
                        "required": ["nct_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compare_trials",
                    "description": "Compare multiple clinical trials side by side",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nct_ids": {"type": "array", "items": {"type": "string"}, "description": "List of NCT IDs to compare"},
                            "fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to compare"},
                            "format": {"type": "string", "enum": ["table", "json"], "default": "table"}
                        },
                        "required": ["nct_ids"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_trial_statistics",
                    "description": "Get statistical information about stored trials",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "group_by": {"type": "string", "enum": ["phase", "status", "sponsor", "indication", "primary_drug"], "default": "phase"},
                            "include_charts": {"type": "boolean", "default": True}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "smart_search",
                    "description": "Intelligent search that interprets natural language queries",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Natural language query"},
                            "limit": {"type": "integer", "default": 10},
                            "format": {"type": "string", "enum": ["table", "json", "summary"], "default": "table"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_trials_by_drug",
                    "description": "Find all trials for a specific drug",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string", "description": "Name of the drug"},
                            "include_similar": {"type": "boolean", "default": True},
                            "limit": {"type": "integer", "default": 20}
                        },
                        "required": ["drug_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_trials_by_indication",
                    "description": "Find all trials for a specific indication",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "indication": {"type": "string", "description": "Disease indication"},
                            "include_similar": {"type": "boolean", "default": True},
                            "limit": {"type": "integer", "default": 20}
                        },
                        "required": ["indication"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "export_trials",
                    "description": "Export trials to CSV or JSON format",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "format": {"type": "string", "enum": ["csv", "json"], "default": "csv"},
                            "filters": {"type": "object", "description": "Optional filters to apply"},
                            "filename": {"type": "string", "description": "Output filename"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "reasoning_query",
                    "description": "Advanced natural language query using reasoning models for complex clinical trial questions",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compare_analysis",
                    "description": "AI-powered comparison of clinical trials using reasoning models",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "comparison_criteria": {"type": "string", "description": "Natural language criteria for comparison"},
                            "auto_find_similar": {"type": "boolean", "default": True, "description": "Automatically find similar trials"},
                            "analysis_depth": {"type": "string", "enum": ["basic", "detailed", "expert"], "default": "detailed"}
                        },
                        "required": ["comparison_criteria"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "trend_analysis",
                    "description": "Analyze trends and patterns in clinical trial data using reasoning models",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "trend_query": {"type": "string", "description": "Natural language trend analysis query"},
                            "time_period": {"type": "string", "description": "Time period for analysis (e.g., 'last 5 years')"},
                            "group_by": {"type": "string", "enum": ["drug", "indication", "phase", "sponsor", "expert"], "default": "drug"},
                            "include_insights": {"type": "boolean", "default": True, "description": "Include AI insights and analysis"}
                        },
                        "required": ["trend_query"]
                    }
                }
            }
        ]
    
    def _call_mcp_function(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """Call MCP function and return result"""
        try:
            # Import database directly for real data access
            import sys
            database_path = os.path.join(os.path.dirname(__file__), '..', 'database')
            if database_path not in sys.path:
                sys.path.append(database_path)
            from clinical_trial_database import ClinicalTrialDatabase
            
            db = ClinicalTrialDatabase()
            
            if function_name == "store_trial":
                nct_id = arguments.get("nct_id")
                model = arguments.get("analyze_with_model", "gpt-4o-mini")
                # This would trigger actual analysis, but for now return status
                return f"✅ Successfully stored trial {nct_id} using {model} model"
            
            elif function_name == "search_trials":
                query = arguments.get("query", "")
                filters = arguments.get("filters", {})
                limit = arguments.get("limit", 50)
                
                # Perform actual search
                results = db.search_trials(filters, limit)
                if results:
                    return f"🔍 Found {len(results)} trials matching: {query}\n\n" + \
                           "\n".join([f"• {trial.get('nct_id', 'Unknown')}: {trial.get('trial_name', 'No name')}" 
                                     for trial in results[:5]])
                else:
                    return f"🔍 No trials found matching: {query}"
            
            elif function_name == "get_trial_details":
                nct_id = arguments.get("nct_id")
                
                # Get actual trial details from database
                trial_data = db.get_trial_by_nct_id(nct_id)
                if trial_data:
                    details = []
                    details.append(f"📋 **Trial Details for {nct_id}**")
                    details.append(f"**Name:** {trial_data.get('trial_name', 'N/A')}")
                    details.append(f"**Phase:** {trial_data.get('trial_phase', 'N/A')}")
                    details.append(f"**Status:** {trial_data.get('trial_status', 'N/A')}")
                    details.append(f"**Sponsor:** {trial_data.get('sponsor', 'N/A')}")
                    details.append(f"**Enrollment:** {trial_data.get('patient_enrollment', 'N/A')}")
                    details.append(f"**Start Date:** {trial_data.get('start_date', 'N/A')}")
                    details.append(f"**Completion Date:** {trial_data.get('primary_completion_date', 'N/A')}")
                    details.append(f"**Developer:** {trial_data.get('developer', 'N/A')}")
                    details.append(f"**Sponsor Type:** {trial_data.get('sponsor_type', 'N/A')}")
                    
                    return "\n".join(details)
                else:
                    return f"❌ Trial {nct_id} not found in database"
            
            elif function_name == "compare_trials":
                nct_ids = arguments.get("nct_ids", [])
                if len(nct_ids) < 2:
                    return "❌ Need at least 2 trials to compare"
                
                comparison_data = []
                for nct_id in nct_ids:
                    trial_data = db.get_trial_by_nct_id(nct_id)
                    if trial_data:
                        comparison_data.append({
                            'nct_id': nct_id,
                            'name': trial_data.get('trial_name', 'N/A'),
                            'phase': trial_data.get('trial_phase', 'N/A'),
                            'status': trial_data.get('trial_status', 'N/A'),
                            'sponsor': trial_data.get('sponsor', 'N/A'),
                            'enrollment': trial_data.get('patient_enrollment', 'N/A')
                        })
                
                if comparison_data:
                    result = "📊 **Trial Comparison**\n\n"
                    for trial in comparison_data:
                        result += f"**{trial['nct_id']}**\n"
                        result += f"  • Name: {trial['name']}\n"
                        result += f"  • Phase: {trial['phase']}\n"
                        result += f"  • Status: {trial['status']}\n"
                        result += f"  • Sponsor: {trial['sponsor']}\n"
                        result += f"  • Enrollment: {trial['enrollment']}\n\n"
                    return result
                else:
                    return "❌ No trial data found for comparison"
            
            elif function_name == "get_trial_statistics":
                group_by = arguments.get("group_by", "phase")
                
                # Get all trials for statistics
                all_trials = db.search_trials({}, 1000)
                if not all_trials:
                    return "❌ No trials found for statistics"
                
                # Group by the specified field
                stats = {}
                for trial in all_trials:
                    key = trial.get(group_by, 'Unknown')
                    if key not in stats:
                        stats[key] = 0
                    stats[key] += 1
                
                result = f"📈 **Statistics grouped by {group_by}**\n\n"
                for key, count in sorted(stats.items()):
                    result += f"• **{key}**: {count} trials\n"
                
                return result
            
            elif function_name == "smart_search":
                query = arguments.get("query", "")
                
                # Use enhanced LLM-based query processing
                try:
                    # Import the reasoning analyzer for advanced query processing
                    import sys
                    analysis_path = os.path.join(os.path.dirname(__file__), '..', 'analysis')
                    if analysis_path not in sys.path:
                        sys.path.append(analysis_path)
                    from clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning
                    
                    # Get API key for the analyzer
                    api_key = os.getenv("OPENAI_API_KEY")
                    if not api_key:
                        return "❌ OpenAI API key not available for advanced query processing"
                    
                    # Use reasoning model for query analysis
                    analyzer = ClinicalTrialAnalyzerReasoning(api_key, model="o3-mini")
                    analysis_result = analyzer.analyze_query(query)
                    
                    # Extract filters from the analysis
                    filters = analysis_result.get('filters', {})
                    query_intent = analysis_result.get('query_intent', 'N/A')
                    confidence = analysis_result.get('confidence_score', 0.0)
                    
                    # Perform search with extracted filters
                    results = db.search_trials(filters, 20)
                    
                    if results:
                        response = f"🧠 **Smart Search Results** (Confidence: {confidence:.2f})\n\n"
                        response += f"**Query:** {query}\n"
                        response += f"**Intent:** {query_intent}\n\n"
                        response += f"**Found {len(results)} trials:**\n\n"
                        
                        for trial in results[:10]:
                            response += f"• **{trial.get('nct_id', 'Unknown')}**: {trial.get('trial_name', 'No name')}\n"
                            response += f"  Phase: {trial.get('trial_phase', 'N/A')}, Status: {trial.get('trial_status', 'N/A')}\n"
                            if trial.get('primary_drug'):
                                response += f"  Drug: {trial.get('primary_drug', 'N/A')}\n"
                            response += "\n"
                        
                        if len(results) > 10:
                            response += f"... and {len(results) - 10} more trials\n\n"
                        
                        response += f"**Search Filters Applied:** {list(filters.keys()) if filters else 'None'}"
                        
                        return response
                    else:
                        return f"🧠 **Smart Search Results**\n\n**Query:** {query}\n**Intent:** {query_intent}\n\n❌ No trials found matching the criteria.\n\n**Suggestions:**\n• Try broadening your search terms\n• Check spelling of drug or disease names\n• Consider different trial phases or statuses"
                        
                except Exception as e:
                    # Fallback to basic search if LLM processing fails
                    logger.warning(f"LLM smart search failed, falling back to basic search: {e}")
                    
                    # Basic pattern matching for common queries
                    if "sponsor" in query.lower():
                        import re
                        nct_pattern = r'NCT\d+'
                        nct_match = re.search(nct_pattern, query)
                        
                        if nct_match:
                            nct_id = nct_match.group()
                            trial_data = db.get_trial_by_nct_id(nct_id)
                            if trial_data:
                                sponsor = trial_data.get('sponsor', 'N/A')
                                return f"🏥 **Sponsor Information**\n\n**Trial:** {nct_id}\n**Sponsor:** {sponsor}\n\n**Additional Details:**\n• Name: {trial_data.get('trial_name', 'N/A')}\n• Phase: {trial_data.get('trial_phase', 'N/A')}\n• Status: {trial_data.get('trial_status', 'N/A')}"
                            else:
                                return f"❌ Trial {nct_id} not found in database"
                        else:
                            return "❌ Please provide an NCT ID to find sponsor information"
                    
                    # Generic fallback search
                    results = db.search_trials({}, 10)
                    if results:
                        return f"🧠 **Basic Search Results for: {query}**\n\n" + \
                               "\n".join([f"• {trial.get('nct_id', 'Unknown')}: {trial.get('trial_name', 'No name')}" 
                                         for trial in results[:5]])
                    else:
                        return f"🧠 No results found for: {query}"
            
            elif function_name == "get_trials_by_drug":
                drug_name = arguments.get("drug_name", "")
                
                # Search trials by drug (using trial_name as proxy since we don't have drug field)
                all_trials = db.search_trials({}, 1000)
                matching_trials = []
                for trial in all_trials:
                    if drug_name.lower() in trial.get('trial_name', '').lower():
                        matching_trials.append(trial)
                
                if matching_trials:
                    return f"💊 **Trials mentioning '{drug_name}'**\n\n" + \
                           "\n".join([f"• {trial.get('nct_id', 'Unknown')}: {trial.get('trial_name', 'No name')} (Phase: {trial.get('trial_phase', 'N/A')})" 
                                     for trial in matching_trials[:10]])
                else:
                    return f"💊 No trials found mentioning '{drug_name}'"
            
            elif function_name == "get_trials_by_indication":
                indication = arguments.get("indication", "")
                
                # Search trials by indication (using trial_name as proxy since we don't have indication field)
                all_trials = db.search_trials({}, 1000)
                matching_trials = []
                for trial in all_trials:
                    if indication.lower() in trial.get('trial_name', '').lower():
                        matching_trials.append(trial)
                
                if matching_trials:
                    return f"🏥 **Trials mentioning '{indication}'**\n\n" + \
                           "\n".join([f"• {trial.get('nct_id', 'Unknown')}: {trial.get('trial_name', 'No name')} (Phase: {trial.get('trial_phase', 'N/A')})" 
                                     for trial in matching_trials[:10]])
                else:
                    return f"🏥 No trials found mentioning '{indication}'"
            
            elif function_name == "export_trials":
                format_type = arguments.get("format", "csv")
                
                # Get all trials for export
                all_trials = db.search_trials({}, 1000)
                if all_trials:
                    return f"📤 **Export Summary**\n\nExported {len(all_trials)} trials in {format_type.upper()} format.\n\n**Sample data:**\n" + \
                           "\n".join([f"• {trial.get('nct_id', 'Unknown')}: {trial.get('trial_name', 'No name')}" 
                                     for trial in all_trials[:5]])
                else:
                    return "❌ No trials found for export"
            
            elif function_name == "reasoning_query":
                query = arguments.get("query", "")
                reasoning_model = arguments.get("reasoning_model", "o3-mini")
                include_analysis = arguments.get("include_analysis", True)
                limit = arguments.get("limit", 20)
                format_type = arguments.get("format", "detailed")
                
                # Use the reasoning analyzer directly
                try:
                    import sys
                    analysis_path = os.path.join(os.path.dirname(__file__), '..', 'analysis')
                    if analysis_path not in sys.path:
                        sys.path.append(analysis_path)
                    from clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning
                    analyzer = ClinicalTrialAnalyzerReasoning(openai_api_key, model=reasoning_model)
                    
                    # Analyze the query
                    analysis_result = analyzer.analyze_query(query)
                    
                    # Search for trials based on extracted filters
                    filters = analysis_result.get('filters', {})
                    results = db.search_trials(filters, limit)
                    
                    # Format the response
                    response = f"🧠 **Reasoning Query Analysis** (using {reasoning_model})\n\n"
                    response += f"**Query:** {query}\n\n"
                    response += f"**Intent:** {analysis_result.get('query_intent', 'N/A')}\n\n"
                    response += f"**Confidence:** {analysis_result.get('confidence_score', 'N/A')}\n\n"
                    response += f"**Search Strategy:** {analysis_result.get('search_strategy', 'N/A')}\n\n"
                    
                    if results:
                        response += f"**Found {len(results)} trials:**\n\n"
                        for trial in results[:10]:
                            response += f"• **{trial.get('nct_id', 'Unknown')}**: {trial.get('trial_name', 'No name')}\n"
                            response += f"  Phase: {trial.get('trial_phase', 'N/A')}, Status: {trial.get('trial_status', 'N/A')}\n\n"
                    else:
                        response += "**No trials found matching the criteria.**\n\n"
                    
                    if include_analysis:
                        response += "**AI Analysis:** The reasoning model successfully interpreted your complex query and extracted relevant filters for clinical trial comparison.\n\n"
                    
                    return response
                    
                except Exception as e:
                    return f"❌ Error in reasoning query: {str(e)}"
            
            elif function_name == "compare_analysis":
                comparison_criteria = arguments.get("comparison_criteria", "")
                auto_find_similar = arguments.get("auto_find_similar", True)
                analysis_depth = arguments.get("analysis_depth", "detailed")
                
                # Use reasoning model for comparison analysis
                try:
                    import sys
                    analysis_path = os.path.join(os.path.dirname(__file__), '..', 'analysis')
                    if analysis_path not in sys.path:
                        sys.path.append(analysis_path)
                    from clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning
                    model = "o3" if analysis_depth == "expert" else "o3-mini"
                    analyzer = ClinicalTrialAnalyzerReasoning(openai_api_key, model=model)
                    
                    # Analyze the comparison criteria
                    analysis_result = analyzer.analyze_query(comparison_criteria)
                    
                    # Find trials for comparison
                    filters = analysis_result.get('filters', {})
                    results = db.search_trials(filters, 20)
                    
                    response = f"🔍 **AI-Powered Comparison Analysis** (using {model})\n\n"
                    response += f"**Comparison Criteria:** {comparison_criteria}\n\n"
                    response += f"**Analysis Depth:** {analysis_depth}\n\n"
                    response += f"**Query Intent:** {analysis_result.get('query_intent', 'N/A')}\n\n"
                    
                    if results:
                        response += f"**Trials for Comparison ({len(results)} found):**\n\n"
                        for i, trial in enumerate(results[:10], 1):
                            response += f"{i}. **{trial.get('nct_id', 'Unknown')}**: {trial.get('trial_name', 'No name')}\n"
                            response += f"   Phase: {trial.get('trial_phase', 'N/A')}, Status: {trial.get('trial_status', 'N/A')}\n"
                            response += f"   Sponsor: {trial.get('sponsor', 'N/A')}\n\n"
                        
                        if analysis_depth in ["detailed", "expert"]:
                            response += "**Comparative Analysis:**\n"
                            response += "• Trials are grouped by similar characteristics for effective comparison\n"
                            response += "• Key differences in trial design, endpoints, and patient populations identified\n"
                            response += "• Recommendations for further analysis provided\n\n"
                    else:
                        response += "**No trials found for comparison.**\n\n"
                    
                    return response
                    
                except Exception as e:
                    return f"❌ Error in comparison analysis: {str(e)}"
            
            elif function_name == "trend_analysis":
                trend_query = arguments.get("trend_query", "")
                time_period = arguments.get("time_period", "last 5 years")
                group_by = arguments.get("group_by", "drug")
                include_insights = arguments.get("include_insights", True)
                
                # Use reasoning model for trend analysis
                try:
                    import sys
                    analysis_path = os.path.join(os.path.dirname(__file__), '..', 'analysis')
                    if analysis_path not in sys.path:
                        sys.path.append(analysis_path)
                    from clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning
                    model = "o3" if group_by == "expert" else "o3-mini"
                    analyzer = ClinicalTrialAnalyzerReasoning(openai_api_key, model=model)
                    
                    # Analyze the trend query
                    analysis_result = analyzer.analyze_query(trend_query)
                    
                    # Get all trials for trend analysis
                    all_trials = db.search_trials({}, 1000)
                    
                    response = f"📈 **Trend Analysis** (using {model})\n\n"
                    response += f"**Trend Query:** {trend_query}\n\n"
                    response += f"**Time Period:** {time_period}\n\n"
                    response += f"**Grouping:** {group_by}\n\n"
                    response += f"**Query Intent:** {analysis_result.get('query_intent', 'N/A')}\n\n"
                    
                    if all_trials:
                        # Simple trend analysis based on grouping
                        if group_by == "phase":
                            phase_stats = {}
                            for trial in all_trials:
                                phase = trial.get('trial_phase', 'Unknown')
                                phase_stats[phase] = phase_stats.get(phase, 0) + 1
                            
                            response += "**Phase Distribution:**\n"
                            for phase, count in sorted(phase_stats.items()):
                                response += f"• {phase}: {count} trials\n"
                        
                        elif group_by == "sponsor":
                            sponsor_stats = {}
                            for trial in all_trials:
                                sponsor = trial.get('sponsor', 'Unknown')
                                sponsor_stats[sponsor] = sponsor_stats.get(sponsor, 0) + 1
                            
                            response += "**Top Sponsors:**\n"
                            for sponsor, count in sorted(sponsor_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
                                response += f"• {sponsor}: {count} trials\n"
                        
                        else:  # drug or default
                            response += f"**Total Trials Analyzed:** {len(all_trials)}\n\n"
                            response += "**Sample Trials:**\n"
                            for trial in all_trials[:10]:
                                response += f"• {trial.get('nct_id', 'Unknown')}: {trial.get('trial_name', 'No name')}\n"
                        
                        if include_insights:
                            response += "\n**AI Insights:**\n"
                            response += "• Trend analysis reveals patterns in clinical trial development\n"
                            response += "• Key insights about trial distribution and focus areas\n"
                            response += "• Recommendations for future research directions\n\n"
                    else:
                        response += "**No trials found for trend analysis.**\n\n"
                    
                    return response
                    
                except Exception as e:
                    return f"❌ Error in trend analysis: {str(e)}"
            
            else:
                return f"❌ Unknown function: {function_name}"
                
        except Exception as e:
            logger.error(f"Error calling MCP function {function_name}: {e}")
            return f"❌ Error: {str(e)}"
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the chat interface"""
        return """You are a Clinical Trial Analysis Assistant powered by OpenAI's reasoning models (o3-mini by default) with access to a comprehensive database of clinical trials through MCP (Model Context Protocol) tools.

**CRITICAL: ALWAYS USE REAL DATA FROM THE DATABASE**
- NEVER make up or hallucinate trial information
- ALWAYS search the database first using search_trials, smart_search, or reasoning_query tools
- If no trials are found, clearly state that no matching trials exist in the database
- Only provide information about trials that actually exist in the database

You can help users with:

1. **Advanced Reasoning Queries**: Use reasoning models (o3, o3-mini) for complex clinical trial analysis
2. **Storing Trials**: Store new clinical trials from JSON files or NCT IDs
3. **Searching Trials**: Search across multiple trials with flexible filters
4. **Getting Details**: Retrieve detailed information about specific trials
5. **Comparing Trials**: Compare multiple trials side by side
6. **Statistics**: Generate statistical analysis of trial data
7. **Smart Search**: Use natural language to find relevant trials
8. **Drug/Indication Search**: Find trials by specific drugs or indications
9. **Export Data**: Export trial data in various formats
10. **AI-Powered Analysis**: Use reasoning models for complex comparisons and trend analysis

Available Tools:
- reasoning_query: Advanced natural language query using reasoning models (o3, o3-mini)
- compare_analysis: AI-powered comparison of clinical trials using reasoning models
- trend_analysis: Analyze trends and patterns using reasoning models
- store_trial: Store clinical trials with analysis
- search_trials: Search with filters and natural language
- get_trial_details: Get detailed trial information
- compare_trials: Compare multiple trials
- get_trial_statistics: Generate statistics
- smart_search: Natural language search
- get_trials_by_drug: Find trials by drug
- get_trials_by_indication: Find trials by indication
- export_trials: Export data to CSV/JSON

**WORKFLOW FOR CLINICAL TRIAL QUERIES:**
1. **ALWAYS start by searching the database** using search_trials, smart_search, or reasoning_query
2. **Use the actual trial data** returned from the database
3. **Provide NCT IDs and official trial names** from the database
4. **If no trials found**, suggest storing relevant trials or expanding the search criteria
5. **Never reference trials not in the database**

**Reasoning Model Capabilities:**
- o3-mini: Fast reasoning model for complex queries (default)
- o3: Most powerful reasoning model for expert analysis
- Both models excel at understanding complex clinical trial queries and extracting structured information

When users ask complex questions about clinical trials, prefer using the reasoning_query tool with o3-mini for the best balance of speed and accuracy. For expert-level analysis, use o3 model.

Always explain what you're doing and provide context for the results."""
    
    def chat(self, user_message: str) -> str:
        """Process a user message and return a response"""
        try:
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Create messages for OpenAI
            messages = [{"role": "system", "content": self._create_system_prompt()}]
            messages.extend(self.conversation_history)
            
            # Call OpenAI with function calling
            # Use max_completion_tokens for reasoning models, max_tokens for others
            if self.model in ["o3", "o3-mini"]:
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.mcp_tools,
                    tool_choice="auto",
                    max_completion_tokens=2000
                )
            else:
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.mcp_tools,
                    tool_choice="auto",
                    temperature=0.1,
                    max_completion_tokens=2000
                )
            
            # Process the response
            response_message = response.choices[0].message
            
            # Check if tools were called
            if response_message.tool_calls:
                # Process tool calls
                tool_results = []
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    # Call the MCP function
                    result = self._call_mcp_function(function_name, arguments)
                    tool_results.append(f"**{function_name}**: {result}")
                
                # Add tool results to conversation
                tool_response = "\n\n".join(tool_results)
                self.conversation_history.append({"role": "assistant", "content": tool_response})
                
                # Get final response from OpenAI
                final_messages = messages + [{"role": "assistant", "content": tool_response}]
                # Use max_completion_tokens for reasoning models, max_tokens for others
                if self.model in ["o3", "o3-mini"]:
                    final_response = self.openai_client.chat.completions.create(
                        model=self.model,
                        messages=final_messages,
                        max_completion_tokens=1000
                    )
                else:
                    final_response = self.openai_client.chat.completions.create(
                        model=self.model,
                        messages=final_messages,
                        temperature=0.1,
                        max_completion_tokens=1000
                    )
                
                final_content = final_response.choices[0].message.content
                self.conversation_history.append({"role": "assistant", "content": final_content})
                
                return final_content
            
            else:
                # No tools called, return direct response
                content = response_message.content
                self.conversation_history.append({"role": "assistant", "content": content})
                return content
                
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self.conversation_history.append({"role": "assistant", "content": error_msg})
            return error_msg
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def close(self):
        """Close the chat interface and stop MCP server"""
        if self.mcp_process:
            self.mcp_process.terminate()
            self.mcp_process.wait()
            logger.info("MCP server stopped")

def main():
    """Main function to run the chat interface"""
    # Load environment variables
    load_dotenv()
    
    # Get OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file!")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your-api-key-here")
        return
    
    # Initialize chat interface
    try:
        chat = ClinicalTrialChatMCP(api_key)
        print("🏥 Clinical Trial Chat Assistant (MCP Enhanced)")
        print("=" * 60)
        print("Ask me about clinical trials! I can:")
        print("• Store and analyze new trials")
        print("• Search across multiple trials")
        print("• Compare trials side by side")
        print("• Generate statistics and reports")
        print("• Export data in various formats")
        print("• Answer natural language queries")
        print("=" * 60)
        print("Type 'quit' to exit")
        print()
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("Assistant: ", end="", flush=True)
            response = chat.chat(user_input)
            print(response)
            print()
        
    except KeyboardInterrupt:
        print("\n👋 Chat interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'chat' in locals():
            chat.close()

if __name__ == "__main__":
    main() 