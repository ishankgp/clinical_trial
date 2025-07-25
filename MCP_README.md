# MCP Server and Chat Interface

This document explains how to run the MCP (Model Context Protocol) server and chat interface for the Clinical Trial Analyzer.

## Prerequisites

1. Make sure you have Python 3.8+ installed
2. Set up your OpenAI API key as an environment variable:
   ```
   export OPENAI_API_KEY=your-api-key-here  # Linux/Mac
   set OPENAI_API_KEY=your-api-key-here     # Windows
   ```
   Or create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

3. Install the required dependencies:
   ```
   pip install -r config/requirements.txt
   ```

## Running the MCP Components

### Option 1: Using the Convenience Scripts (Recommended)

We've created convenience scripts that ensure the Python path is set up correctly:

1. To run the chat interface:
   ```
   python run_mcp_chat.py
   ```

2. To run the MCP server directly:
   ```
   python run_mcp_server.py
   ```

### Option 2: Running from the Project Root

You can also run the modules directly from the project root:

1. To run the chat interface:
   ```
   python src/mcp/clinical_trial_chat_mcp.py
   ```

2. To run the MCP server directly:
   ```
   python src/mcp/clinical_trial_mcp_server.py
   ```

## Using the Chat Interface

The chat interface provides a command-line interface to interact with the clinical trial database. You can:

1. Ask natural language questions about clinical trials
2. Search for trials using various criteria
3. Compare trials
4. Analyze trends across trials
5. Get detailed information about specific trials

### Example Queries

- "Find trials using semaglutide"
- "What trials exist for metastatic triple-negative breast cancer?"
- "Find trials combining checkpoint inhibitors with chemotherapy for lung cancer"
- "Trials for EGFR-mutated non-small cell lung cancer"
- "Compare the efficacy endpoints in trials of PARP inhibitors for ovarian cancer"
- "Analyze trends in immunotherapy trials for solid tumors"

## Advanced Semantic Search

The system implements three levels of search sophistication:

1. **Basic Search**: Simple keyword matching in the database
2. **Smart Search**: LLM-enhanced query understanding with structured filters
3. **Reasoning Query**: Advanced semantic analysis using reasoning models (o3, o3-mini)

The reasoning query capability provides:
- Deep semantic understanding of complex queries
- Extraction of implicit relationships and concepts
- Comprehensive analysis of search intent
- Suggested follow-up queries
- Detailed explanations of search strategies

## Troubleshooting

If you encounter import errors:

1. Make sure you're running the scripts from the project root directory
2. Use the convenience scripts (`run_mcp_chat.py` or `run_mcp_server.py`)
3. Check that your Python environment has all the required dependencies installed
4. Ensure your OpenAI API key is set correctly

For other issues, check the logs for detailed error messages. 