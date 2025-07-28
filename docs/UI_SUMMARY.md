# Clinical Trial Analysis Tool - UI Summary

## 🎯 Overview

This document summarizes the key features and architecture of the web-based UI for the Clinical Trial Analysis System. The UI is built with Streamlit and is now fully integrated with a **Supabase** backend, providing a seamless and powerful user experience.

## 🚀 Key Features

### 1. **Integrated Chat Assistant (Main Feature)**
-   **Backend**: Powered by a Supabase (PostgreSQL) database.
-   **Functionality**: Users can ask natural language questions (e.g., "find phase 3 diabetes trials") to query the entire clinical trial database.
-   **Technology**: Uses an integrated MCP (Model Context Protocol) server that starts automatically with the UI.

### 2. **Single Trial Analysis**
-   **Inputs**: Supports analysis via JSON file upload or by entering a ClinicalTrials.gov NCT ID.
-   **Models**: Allows users to choose from various OpenAI models (GPT-4o, GPT-4o-mini, etc.) for analysis.
-   **Output**: Displays comprehensive, categorized results and allows for CSV export.

### 3. **Model Comparison**
-   **Purpose**: Enables side-by-side comparison of different AI models on the same trial data.
-   **Metrics**: Provides performance metrics like speed and quality, along with data visualizations.

### 4. **System & Database Status**
-   **Monitoring**: The UI includes a section to monitor the connection status to the Supabase database, showing the total number of trials available.
-   **History**: Users can view a history of recently analyzed files.

## 🏛️ Technical Architecture

-   **Frontend**: Streamlit
-   **Backend**: Python, with an auto-starting MCP server for tool-use.
-   **Database**: **Supabase (PostgreSQL)**, managed via the `clinical_trial_database_supabase.py` adapter.
-   **Configuration**: All necessary keys (OpenAI, Supabase) are managed through a single `.env` file.

## 🛠️ Setup & Launch

1.  **Dependencies**: Install via `pip install -r config/requirements.txt` and `config/requirements_ui.txt`.
2.  **Environment**: Run `python main.py setup` and populate the created `.env` file with OpenAI and Supabase credentials.
3.  **Database Migration**: Populate the Supabase database by running the `migrate_data_to_supabase.py` script.
4.  **Launch**: Start the entire application (Streamlit UI and MCP server) with a single command:
    ```bash
    python main.py ui
    ```

## 🏆 Conclusion

The UI provides a robust and user-friendly interface for the Clinical Trial Analysis System. The migration to Supabase has centralized data management and enabled a powerful, integrated chat experience as the core feature, making complex database queries accessible through natural language. 