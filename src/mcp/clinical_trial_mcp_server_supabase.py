#!/usr/bin/env python3
"""
Supabase MCP Server for Clinical Trial Analysis
Provides MCP tools for querying Supabase clinical trial data
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import requests
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
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupabaseMCPServer:
    """MCP Server for Supabase clinical trial data"""
    
    def __init__(self):
        self.supabase_url = "https://hvmazsmkfzjwmrbdilfq.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2bWF6c21rZnpqd21yYmRpbGZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2OTI5OTMsImV4cCI6MjA2OTI2ODk5M30.rajuDXjG_KSQhL968L8FRXgxRFgzIIuwo25pZ6ndoSU"
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # Initialize MCP server
        self.server = Server("clinical-trials-supabase")
        
        # Register tools
        self.server.list_tools(self.list_tools)
        self.server.call_tool(self.call_tool)
    
    async def list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """List available MCP tools"""
        tools = [
            Tool(
                name="search_trials",
                description="Search clinical trials using natural language query",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_trial_by_nct",
                description="Get detailed information about a specific trial by NCT ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "nct_id": {
                            "type": "string",
                            "description": "Clinical trial NCT ID"
                        }
                    },
                    "required": ["nct_id"]
                }
            ),
            Tool(
                name="get_trials_by_phase",
                description="Get trials filtered by phase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "phase": {
                            "type": "string",
                            "description": "Trial phase (Phase 1, Phase 2, Phase 3, Phase 4)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        }
                    },
                    "required": ["phase"]
                }
            ),
            Tool(
                name="get_trials_by_status",
                description="Get trials filtered by status",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Trial status (Recruiting, Completed, Terminated, etc.)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        }
                    },
                    "required": ["status"]
                }
            ),
            Tool(
                name="get_trials_by_drug",
                description="Get trials for a specific drug",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "drug_name": {
                            "type": "string",
                            "description": "Name of the drug"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        }
                    },
                    "required": ["drug_name"]
                }
            ),
            Tool(
                name="get_trial_statistics",
                description="Get statistics about clinical trials",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="store_trial",
                description="Store a new clinical trial in the database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "nct_id": {
                            "type": "string",
                            "description": "Clinical trial NCT ID"
                        },
                        "trial_name": {
                            "type": "string",
                            "description": "Name of the trial"
                        },
                        "trial_phase": {
                            "type": "string",
                            "description": "Trial phase"
                        },
                        "trial_status": {
                            "type": "string",
                            "description": "Trial status"
                        },
                        "patient_enrollment": {
                            "type": "integer",
                            "description": "Number of patients enrolled"
                        },
                        "sponsor": {
                            "type": "string",
                            "description": "Trial sponsor"
                        },
                        "primary_endpoints": {
                            "type": "string",
                            "description": "Primary endpoints"
                        },
                        "secondary_endpoints": {
                            "type": "string",
                            "description": "Secondary endpoints"
                        },
                        "inclusion_criteria": {
                            "type": "string",
                            "description": "Inclusion criteria"
                        },
                        "exclusion_criteria": {
                            "type": "string",
                            "description": "Exclusion criteria"
                        }
                    },
                    "required": ["nct_id", "trial_name"]
                }
            )
        ]
        
        return ListToolsResult(tools=tools)
    
    async def call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool calls"""
        try:
            if request.name == "search_trials":
                return await self.search_trials(request.arguments)
            elif request.name == "get_trial_by_nct":
                return await self.get_trial_by_nct(request.arguments)
            elif request.name == "get_trials_by_phase":
                return await self.get_trials_by_phase(request.arguments)
            elif request.name == "get_trials_by_status":
                return await self.get_trials_by_status(request.arguments)
            elif request.name == "get_trials_by_drug":
                return await self.get_trials_by_drug(request.arguments)
            elif request.name == "get_trial_statistics":
                return await self.get_trial_statistics(request.arguments)
            elif request.name == "store_trial":
                return await self.store_trial(request.arguments)
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {request.name}")]
                )
        except Exception as e:
            logger.error(f"Error in tool call {request.name}: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )
    
    async def search_trials(self, args: Dict[str, Any]) -> CallToolResult:
        """Search trials using natural language query"""
        query = args.get("query", "")
        limit = args.get("limit", 10)
        
        try:
            # Simple search implementation - can be enhanced with vector search
            response = requests.get(
                f"{self.supabase_url}/rest/v1/clinical_trials?select=*&limit={limit}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                trials = response.json()
                result_text = f"Found {len(trials)} trials matching '{query}':\n\n"
                
                for trial in trials:
                    result_text += f"**{trial.get('trial_name', 'Unknown')}**\n"
                    result_text += f"NCT ID: {trial.get('nct_id', 'Unknown')}\n"
                    result_text += f"Phase: {trial.get('trial_phase', 'Unknown')}\n"
                    result_text += f"Status: {trial.get('trial_status', 'Unknown')}\n"
                    result_text += f"Sponsor: {trial.get('sponsor', 'Unknown')}\n"
                    result_text += f"Enrollment: {trial.get('patient_enrollment', 'Unknown')}\n\n"
                
                return CallToolResult(
                    content=[TextContent(type="text", text=result_text)]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {response.status_code}")]
                )
                
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error searching trials: {str(e)}")]
            )
    
    async def get_trial_by_nct(self, args: Dict[str, Any]) -> CallToolResult:
        """Get trial by NCT ID"""
        nct_id = args.get("nct_id", "")
        
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/clinical_trials?nct_id=eq.{nct_id}&select=*,drug_info(*),clinical_info(*)",
                headers=self.headers
            )
            
            if response.status_code == 200:
                trials = response.json()
                if trials:
                    trial = trials[0]
                    result_text = f"**Trial Details for {nct_id}**\n\n"
                    result_text += f"Name: {trial.get('trial_name', 'Unknown')}\n"
                    result_text += f"Phase: {trial.get('trial_phase', 'Unknown')}\n"
                    result_text += f"Status: {trial.get('trial_status', 'Unknown')}\n"
                    result_text += f"Sponsor: {trial.get('sponsor', 'Unknown')}\n"
                    result_text += f"Enrollment: {trial.get('patient_enrollment', 'Unknown')}\n"
                    result_text += f"Primary Endpoints: {trial.get('primary_endpoints', 'Unknown')}\n"
                    result_text += f"Secondary Endpoints: {trial.get('secondary_endpoints', 'Unknown')}\n"
                    result_text += f"Inclusion Criteria: {trial.get('inclusion_criteria', 'Unknown')}\n"
                    result_text += f"Exclusion Criteria: {trial.get('exclusion_criteria', 'Unknown')}\n"
                    
                    return CallToolResult(
                        content=[TextContent(type="text", text=result_text)]
                    )
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"No trial found with NCT ID: {nct_id}")]
                    )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {response.status_code}")]
                )
                
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error getting trial: {str(e)}")]
            )
    
    async def get_trials_by_phase(self, args: Dict[str, Any]) -> CallToolResult:
        """Get trials by phase"""
        phase = args.get("phase", "")
        limit = args.get("limit", 10)
        
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/clinical_trials?trial_phase=eq.{phase}&select=*&limit={limit}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                trials = response.json()
                result_text = f"Found {len(trials)} {phase} trials:\n\n"
                
                for trial in trials:
                    result_text += f"**{trial.get('trial_name', 'Unknown')}**\n"
                    result_text += f"NCT ID: {trial.get('nct_id', 'Unknown')}\n"
                    result_text += f"Status: {trial.get('trial_status', 'Unknown')}\n"
                    result_text += f"Sponsor: {trial.get('sponsor', 'Unknown')}\n\n"
                
                return CallToolResult(
                    content=[TextContent(type="text", text=result_text)]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {response.status_code}")]
                )
                
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error getting trials by phase: {str(e)}")]
            )
    
    async def get_trials_by_status(self, args: Dict[str, Any]) -> CallToolResult:
        """Get trials by status"""
        status = args.get("status", "")
        limit = args.get("limit", 10)
        
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/clinical_trials?trial_status=eq.{status}&select=*&limit={limit}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                trials = response.json()
                result_text = f"Found {len(trials)} {status} trials:\n\n"
                
                for trial in trials:
                    result_text += f"**{trial.get('trial_name', 'Unknown')}**\n"
                    result_text += f"NCT ID: {trial.get('nct_id', 'Unknown')}\n"
                    result_text += f"Phase: {trial.get('trial_phase', 'Unknown')}\n"
                    result_text += f"Sponsor: {trial.get('sponsor', 'Unknown')}\n\n"
                
                return CallToolResult(
                    content=[TextContent(type="text", text=result_text)]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {response.status_code}")]
                )
                
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error getting trials by status: {str(e)}")]
            )
    
    async def get_trials_by_drug(self, args: Dict[str, Any]) -> CallToolResult:
        """Get trials by drug name"""
        drug_name = args.get("drug_name", "")
        limit = args.get("limit", 10)
        
        try:
            response = requests.get(
                f"{self.supabase_url}/rest/v1/drug_info?primary_drug=ilike.%25{drug_name}%25&select=*,clinical_trials(*)&limit={limit}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                drug_trials = response.json()
                result_text = f"Found {len(drug_trials)} trials for drug '{drug_name}':\n\n"
                
                for drug_trial in drug_trials:
                    trial = drug_trial.get('clinical_trials', {})
                    result_text += f"**{trial.get('trial_name', 'Unknown')}**\n"
                    result_text += f"NCT ID: {trial.get('nct_id', 'Unknown')}\n"
                    result_text += f"Phase: {trial.get('trial_phase', 'Unknown')}\n"
                    result_text += f"Status: {trial.get('trial_status', 'Unknown')}\n\n"
                
                return CallToolResult(
                    content=[TextContent(type="text", text=result_text)]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {response.status_code}")]
                )
                
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error getting trials by drug: {str(e)}")]
            )
    
    async def get_trial_statistics(self, args: Dict[str, Any]) -> CallToolResult:
        """Get trial statistics"""
        try:
            # Get total count
            response = requests.get(
                f"{self.supabase_url}/rest/v1/clinical_trials?select=count",
                headers=self.headers
            )
            
            if response.status_code == 200:
                total_trials = len(response.json())
                
                # Get phase distribution
                phase_response = requests.get(
                    f"{self.supabase_url}/rest/v1/clinical_trials?select=trial_phase",
                    headers=self.headers
                )
                
                phase_counts = {}
                if phase_response.status_code == 200:
                    phases = phase_response.json()
                    for trial in phases:
                        phase = trial.get('trial_phase', 'Unknown')
                        phase_counts[phase] = phase_counts.get(phase, 0) + 1
                
                result_text = f"**Clinical Trial Statistics**\n\n"
                result_text += f"Total Trials: {total_trials}\n\n"
                result_text += f"**Phase Distribution:**\n"
                for phase, count in phase_counts.items():
                    result_text += f"- {phase}: {count} trials\n"
                
                return CallToolResult(
                    content=[TextContent(type="text", text=result_text)]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {response.status_code}")]
                )
                
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error getting statistics: {str(e)}")]
            )
    
    async def store_trial(self, args: Dict[str, Any]) -> CallToolResult:
        """Store a new trial"""
        try:
            trial_data = {
                'nct_id': args.get('nct_id'),
                'trial_name': args.get('trial_name'),
                'trial_phase': args.get('trial_phase'),
                'trial_status': args.get('trial_status'),
                'patient_enrollment': args.get('patient_enrollment'),
                'sponsor': args.get('sponsor'),
                'primary_endpoints': args.get('primary_endpoints'),
                'secondary_endpoints': args.get('secondary_endpoints'),
                'inclusion_criteria': args.get('inclusion_criteria'),
                'exclusion_criteria': args.get('exclusion_criteria')
            }
            
            response = requests.post(
                f"{self.supabase_url}/rest/v1/clinical_trials",
                headers=self.headers,
                json=trial_data
            )
            
            if response.status_code == 201:
                result = response.json()
                return CallToolResult(
                    content=[TextContent(type="text", text=f"✅ Trial stored successfully with ID: {result[0].get('id')}")]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error storing trial: {response.status_code}")]
                )
                
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error storing trial: {str(e)}")]
            )
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="clinical-trials-supabase",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )

async def main():
    """Main function"""
    server = SupabaseMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main()) 