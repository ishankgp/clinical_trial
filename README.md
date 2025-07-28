# 🏥 Clinical Trial Analysis System

An AI-powered system for analyzing clinical trials, featuring a Supabase backend, a Streamlit UI, and advanced reasoning models.

## ✨ Key Features

-   **AI-Driven Search**: Natural language queries powered by OpenAI's reasoning models.
-   **Supabase Backend**: A scalable and robust PostgreSQL backend for all clinical trial data.
-   **Integrated MCP**: The Model Context Protocol (MCP) is now a core, automatically-run feature for advanced chat and tool use.
-   **Streamlit Web UI**: An intuitive interface for interacting with the system.
-   **Advanced Analysis**: In-depth analysis of trial data, including status, phase, and endpoints.

## 🏛️ Architecture

The system's architecture is built around a Streamlit frontend, a Python backend with an integrated MCP server, and a Supabase database.

```mermaid
graph TD
    A[User via Streamlit UI] --> B{Application Backend};
    B --> C{MCP Server (background process)};
    B --> D{OpenAI API};
    C --> E[Supabase Database];
    subgraph "User Interaction"
        A
    end
    subgraph "Application Logic"
        B
        C
        D
    end
    subgraph "Data Layer"
        E
    end
```

## 🛠️ Installation

### Prerequisites

-   Python 3.8+
-   An OpenAI API Key
-   A Supabase Project (URL and API Key)
-   Git

### Setup

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd clinical_trial
    ```

2.  **Install dependencies**
    ```bash
    pip install -r config/requirements.txt
    pip install -r config/requirements_ui.txt
    ```

3.  **Configure Environment**
    Run the setup script to create a `.env` file and add your OpenAI API Key:
    ```bash
    python main.py setup
    ```
    Then, manually add your Supabase credentials to the `.env` file:
    ```
    SUPABASE_URL="your_supabase_project_url"
    SUPABASE_KEY="your_supabase_api_key"
    ```

4.  **Database Migration (One-Time Setup)**
    Apply the schema from `corrected_supabase_setup.sql` to your Supabase project's SQL Editor. Then, run the migration script to populate your database from the local `clinical_trials.db` file:
    ```bash
    python migrate_data_to_supabase.py
    ```

## 🚀 Usage

### Quick Start

1.  **Start the web interface**
    ```bash
    python main.py ui
    ```
    This single command starts the Streamlit UI and the background MCP server.

2.  **Open your browser**
    Navigate to `http://localhost:8502`

3.  **Start analyzing trials**
    Use the integrated chat interface to ask questions like:
    -   "Find diabetes trials"
    -   "Compare Phase 3 cancer immunotherapy trials"
    -   "Show me recruiting bladder cancer trials"

### Command Line Interface

The `main.py` script provides several commands for managing the system:
```bash
# Setup and configuration
python main.py setup

# Start web interface (includes MCP server)
python main.py ui

# (Optional) Run tests against the configured database
python main.py test
python main.py test-mcp-chat
```

## 🧠 AI & Database Features

### Natural Language Understanding
The system uses AI to understand complex queries and interact with the Supabase database via MCP tools.

### MCP Tools
The integrated MCP server provides tools for:
-   `search_trials`: Intelligent trial search.
-   `get_trial_details`: Detailed trial information.
-   `get_trials_by_drug` / `get_trials_by_indication`: Filtered searches.
-   And more for comparison, statistics, and analysis.

## 📊 Database Schema

The system uses a **Supabase (PostgreSQL)** database with a schema distributed across multiple tables, including `clinical_trials`, `drug_info`, and `clinical_info` to store detailed trial data. The full schema can be found in `corrected_supabase_setup.sql`.

## 🔧 Troubleshooting

-   **Connection Errors**: Verify that your `OPENAI_API_KEY`, `SUPABASE_URL`, and `SUPABASE_KEY` in the `.env` file are correct and that you have an active internet connection.
-   **Data Not Appearing**: Ensure the database migration script ran without errors and that your Supabase tables are populated.
-   **General Issues**: Check the console output when running `python main.py ui` for any error messages.
-   **Detailed Docs**: For more detailed documentation, see the `docs/` directory.