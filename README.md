# 🏥 Clinical Trial Analysis System

A comprehensive AI-powered system for analyzing clinical trials using OpenAI's reasoning models and Model Context Protocol (MCP).

## 🚀 Features

- **AI-Driven Search**: Uses OpenAI's reasoning models (o3) for intelligent natural language query understanding
- **MCP Integration**: Model Context Protocol for standardized AI tool access
- **Direct API Integration**: Fetches real trial data from ClinicalTrials.gov API
- **Web Interface**: Streamlit-based UI for easy interaction
- **Database Management**: SQLite database for storing and querying trial data
- **Advanced Analysis**: Multi-model analysis with reasoning capabilities
- **Enhanced LLM Query Processing**: Sophisticated LLM-based query parsing with robust fallback logic for synonyms, brand names, and multi-term queries

## 🏗️ Architecture

```
clinical_trial/
├── src/
│   ├── analysis/          # AI analysis modules
│   ├── database/          # Database management
│   ├── mcp/              # Model Context Protocol servers
│   ├── ui/               # Streamlit web interface
│   └── utils/            # Utility functions
├── data/                 # Data storage
├── docs/                 # Documentation
├── tests/                # Test files
└── config/               # Configuration files
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- OpenAI API key
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd clinical_trial
   ```

2. **Install dependencies**
   ```bash
   pip install -r config/requirements.txt
   pip install -r config/requirements_ui.txt
   ```

3. **Environment setup**
   ```bash
   python setup_env.py
   ```

4. **Configure API keys**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 🚀 Usage

### Quick Start

1. **Start the web interface**
   ```bash
   python main.py ui
   ```

2. **Open your browser**
   Navigate to `http://localhost:8502`

3. **Start analyzing trials**
   Use the chat interface to ask questions like:
   - "Find diabetes trials"
   - "Compare Phase 3 cancer immunotherapy trials"
   - "Show me recruiting bladder cancer trials"

### Command Line Interface

```bash
# Setup and configuration
python main.py setup

# Start web interface
python main.py ui

# Process all trials
python main.py process

# Populate database with trials
python main.py populate

# Run tests
python main.py test

# Test reasoning models
python main.py test-reasoning

# Test MCP functionality
python main.py test-mcp-query
python main.py test-mcp-chat
```

## 🧠 Consistent Query Logic Across CLI and UI

Both the **MCP chat CLI** (`python src/mcp/clinical_trial_chat_mcp.py`) and the **Streamlit UI** (MCP Chat tab) use the **same backend logic and database** for clinical trial queries. This ensures that:
- All advanced queries (natural language, smart search, statistics, etc.) are powered by the same MCP server and database.
- Results are consistent between the CLI and UI, provided both are using the same working directory and environment.

If you see different results between the CLI and UI:
- **Check that both are using the same `clinical_trials.db` file.**
- Ensure there are no duplicate database files in different folders.
- Confirm both are running in the same Python environment.

---

## 🤖 AI Features

### Reasoning Models
- **o3-mini**: Default reasoning model for complex analysis
- **o3**: Advanced reasoning for detailed insights
- **o4-mini**: Latest reasoning capabilities

### Enhanced LLM-Based Query Processing
- Natural language queries are parsed using advanced LLM reasoning (see `docs/ENHANCED_LLM_QUERY_PROCESSING.md`).
- The system can extract multiple synonyms, brand names, and related terms for each filter (e.g., "semaglutide", "Ozempic", "Wegovy").
- Robust fallback logic ensures queries work even if the LLM is unavailable.

### Natural Language Understanding
The system uses AI to understand complex queries:
- "Find diabetes trials with semaglutide"
- "Compare Phase 3 cancer immunotherapy trials"
- "What bladder cancer trials are recruiting?"

### MCP Tools
- `search_trials`: Intelligent trial search
- `smart_search`: Natural language search
- `reasoning_query`: Advanced semantic search using reasoning models
- `compare_analysis`: AI-powered comparison of clinical trials
- `trend_analysis`: Analyze trends and patterns in trial data
- `get_trial_details`: Detailed trial information
- `store_trial`: Add new trials to database

## 📊 Database Schema

The system uses a SQLite database with the following main table:

```sql
CREATE TABLE clinical_trials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nct_id TEXT UNIQUE NOT NULL,
    trial_name TEXT,
    trial_phase TEXT,
    trial_status TEXT,
    patient_enrollment INTEGER,
    sponsor TEXT,
    primary_endpoints TEXT,
    secondary_endpoints TEXT,
    inclusion_criteria TEXT,
    exclusion_criteria TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🛠️ Troubleshooting UI/CLI Result Mismatches

If you notice that the Streamlit UI and the CLI chat assistant show different results for the same query:

1. **Check Database Path Consistency**
   - Both the CLI and UI should use the same `clinical_trials.db` file (default in project root).
   - If you have multiple `.db` files, results may differ.

2. **Check Python Environment**
   - Ensure both are running in the same Python environment (check with `which python` or `pip list`).

3. **Check Working Directory**
   - Run both from the project root to avoid path issues.

4. **Check for Recent Data Population**
   - If you just populated the database, restart the UI to refresh its view.

5. **Check for UI Tab Differences**
   - Only the "MCP Chat" tab uses the full MCP backend. Other tabs may use direct analysis and not query the database.

---

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `