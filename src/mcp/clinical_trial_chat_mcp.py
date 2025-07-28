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
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path for proper imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import database classes
from src.database.clinical_trial_database import ClinicalTrialDatabase
from src.database.clinical_trial_database_supabase import ClinicalTrialDatabaseSupabase


class ClinicalTrialChatMCP:
    """Chat interface for clinical trial queries using OpenAI LLM and MCP tools"""
    
    def __init__(self, openai_api_key: str, model: str = "o3", db_path: str = "clinical_trials.db"):
        """Initialize the chat interface with o3 reasoning model by default"""
        self.openai_api_key = openai_api_key
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.model = model
        self.conversation_history = []
        self.mcp_process = None
        self.mcp_tools = []
        
        # Load the clinical trial analysis document for attachment
        self._load_analysis_document()
        
        # Initialize database connection
        self.db = None
        
        # Prioritize Supabase if configured
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if supabase_url and supabase_key:
            try:
                self.db = ClinicalTrialDatabaseSupabase(supabase_url, supabase_key)
                logger.info("✅ Successfully connected to Supabase")
            except Exception as e:
                logger.error(f"⚠️ Supabase connection failed, falling back to SQLite: {e}")
                self.db = ClinicalTrialDatabase(db_path)
        else:
            self.db = ClinicalTrialDatabase(db_path)
        
        # Initialize MCP server and tools
        self._start_mcp_server()
        self._load_mcp_tools()
    
    def _load_analysis_document(self):
        """Load the clinical trial analysis specification document"""
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            doc_path = os.path.join(project_root, 'docs', 'GenAI_Case_Clinical_Trial_Analysis_PROMPT_ver1.00.docx.md')
            if os.path.exists(doc_path):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    self.analysis_document = f.read()
                logger.info("✅ Clinical trial analysis document loaded successfully")
            else:
                self.analysis_document = None
                logger.warning("⚠️ Clinical trial analysis document not found")
        except Exception as e:
            self.analysis_document = None
            logger.error(f"❌ Error loading analysis document: {e}")
    
    def _start_mcp_server(self):
        """Start the MCP server process"""
        try:
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
                    "description": "Store and analyze a clinical trial from NCT ID or JSON file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nct_id": {
                                "type": "string",
                                "description": "NCT ID of the clinical trial"
                            },
                            "json_file_path": {
                                "type": "string",
                                "description": "Optional path to JSON file containing trial data"
                            },
                            "analyze_with_model": {
                                "type": "string", 
                                "enum": ["o3", "gpt-4o", "gpt-4o-mini", "gpt-4", "llm"], 
                                "default": "o3",
                                "description": "Model to use for analysis"
                            },
                            "force_reanalyze": {
                                "type": "boolean",
                                "default": False,
                                "description": "Force reanalysis even if trial exists"
                            }
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
                            "limit": {"type": "integer", "default": 50}
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
                            "reasoning_model": {"type": "string", "enum": ["o3"], "default": "o3", "description": "Reasoning model to use for query interpretation"},
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
            if function_name == "search_trials":
                query = arguments.get("query", "")
                filters = arguments.get("filters", {})
                limit = arguments.get("limit", 50)
                
                # Ensure filters is a dictionary, not an integer
                if not isinstance(filters, dict):
                    filters = {}
                
                # Use the database's search method
                results = self.db.search_trials(query, filters, limit)
                if results:
                    return f"🔍 Found {len(results)} trials matching: {query}\n\n" + \
                           "\n".join([f"• {trial.get('nct_id', 'Unknown')}: {trial.get('trial_name', 'No name')}" 
                                     for trial in results[:5]])
                else:
                    return f"🔍 No trials found matching: {query}"
            
            elif function_name == "get_trial_details":
                nct_id = arguments.get("nct_id")
                trial_data = self.db.get_trial_by_nct_id(nct_id)
                if trial_data:
                    details = []
                    details.append(f"📋 **Trial Details for {nct_id}**")
                    details.append(f"**Name:** {trial_data.get('trial_name', 'N/A')}")
                    details.append(f"**Phase:** {trial_data.get('trial_phase', 'N/A')}")
                    details.append(f"**Status:** {trial_data.get('trial_status', 'N/A')}")
                    details.append(f"**Sponsor:** {trial_data.get('sponsor', 'N/A')}")
                    details.append(f"**Enrollment:** {trial_data.get('patient_enrollment', 'N/A')}")
                    return "\n".join(details)
                else:
                    return f"❌ Trial {nct_id} not found in database"
            
            elif function_name == "get_trials_by_drug":
                drug_name = arguments.get("drug_name", "")
                limit = arguments.get("limit", 20)
                results = self.db.get_trials_by_drug(drug_name, limit)
                if results:
                    return f"💊 **Trials for '{drug_name}'**\n\n" + \
                           "\n".join([f"• {trial.get('nct_id', 'Unknown')}: {trial.get('trial_name', 'No name')} (Phase: {trial.get('trial_phase', 'N/A')})" 
                                     for trial in results[:10]])
                else:
                    return f"💊 No trials found for '{drug_name}'"
            
            elif function_name == "get_trials_by_indication":
                indication = arguments.get("indication", "")
                limit = arguments.get("limit", 20)
                results = self.db.get_trials_by_indication(indication, limit)
                if results:
                    return f"🏥 **Trials for '{indication}'**\n\n" + \
                           "\n".join([f"• {trial.get('nct_id', 'Unknown')}: {trial.get('trial_name', 'No name')} (Phase: {trial.get('trial_phase', 'N/A')})" 
                                     for trial in results[:10]])
                else:
                    return f"🏥 No trials found for '{indication}'"
            
            elif function_name == "get_trial_statistics":
                stats = self.db.get_trial_statistics()
                if stats:
                    result = "📈 **Database Statistics**\n\n"
                    for key, value in stats.items():
                        result += f"• **{key}**: {value}\n"
                    return result
                else:
                    return "❌ No statistics available"
            
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
    
    def _analyze_query_with_document_attachment(self, query: str, model: str) -> Dict[str, Any]:
        """
        Analyze query using o3 model with document attachment for enhanced understanding
        """
        try:
            # Prepare the query analysis prompt
            analysis_prompt = f"""
Please analyze the following natural language query about clinical trials according to the detailed specifications provided in the attached document.

QUERY: "{query}"

Please extract structured information and return your analysis as a JSON object with the following structure:
{{
    "filters": {{
        "primary_drug": "extracted drug name or null",
        "indication": "extracted indication or null", 
        "trial_phase": "extracted phase or null",
        "trial_status": "extracted status or null",
        "sponsor": "extracted sponsor or null",
        "line_of_therapy": "extracted line of therapy or null",
        "biomarker": "extracted biomarker or null"
    }},
    "query_intent": "description of what the user wants",
    "search_strategy": "how to approach this search",
    "relevant_fields": ["list", "of", "relevant", "fields"],
    "confidence_score": 0.0-1.0
}}

Use the detailed specifications in the attached document to ensure accurate extraction of clinical trial terminology and concepts.
"""
            
            # Prepare the specification document attachment
            # Use absolute path with os.path.abspath to ensure correct path resolution
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            doc_path = os.path.join(project_root, 'docs', 'GenAI_Case_Clinical_Trial_Analysis_PROMPT_ver1.00.docx.md')
            
            if os.path.exists(doc_path):
                # Read the specification document content
                with open(doc_path, 'r', encoding='utf-8') as f:
                    doc_content = f.read()
                
                # Upload the document
                file_id = self._upload_document(doc_content, "clinical_trial_analysis_specs.md")
                
                # Create the API call with document attachment
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": analysis_prompt
                                },
                                {
                                    "type": "file",
                                    "file_id": file_id
                                }
                            ]
                        }
                    ],
                    max_completion_tokens=1500,
                    response_format={"type": "json_object"}
                )
                
                # Clean up uploaded file
                try:
                    self.openai_client.files.delete(file_id)
                except Exception as e:
                    logger.warning(f"Could not delete uploaded file: {e}")
                    
            else:
                # Fallback if document not found
                logger.warning(f"Document not found at {doc_path}, using text-based prompt")
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert clinical trial analyst. Extract structured information from natural language queries about clinical trials."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    max_completion_tokens=1500,
                    response_format={"type": "json_object"}
                )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error in document attachment query analysis: {e}")
            # Fallback to basic analysis
            return {
                "filters": {},
                "query_intent": f"Basic analysis of: {query}",
                "search_strategy": "Basic search",
                "relevant_fields": [],
                "confidence_score": 0.5
            }
    
    def _upload_document(self, content: str, filename: str) -> str:
        """
        Upload document content to OpenAI for attachment
        """
        try:
            # Create a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                f.write(content)
                temp_path = f.name
            
            # Upload the file
            with open(temp_path, 'rb') as f:
                file_response = self.openai_client.files.create(
                    file=f,
                    purpose="assistants"
                )
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return file_response.id
            
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            raise
    
    def close(self):
        """Close the chat interface and stop MCP server"""
        if self.mcp_process:
            self.mcp_process.terminate()
            self.mcp_process.wait()
            logger.info("MCP server stopped")

def main():
    """Main function to run the chat interface"""
    load_dotenv(encoding='utf-8-sig')
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == 'your_openai_api_key_here':
        print("❌ OPENAI_API_KEY not found or is a placeholder in .env file!")
        return
    
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