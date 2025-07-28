# Clinical Trial Analysis Tool - Web UI

A modern, interactive web interface for analyzing clinical trials, powered by a Supabase backend and integrated with advanced AI models.

## 🚀 Features

### 📊 Single Trial Analysis
- Upload JSON files or enter NCT IDs.
- Choose from multiple OpenAI models (GPT-4o, GPT-4o-mini, o3, GPT-4).
- Real-time analysis with progress tracking.
- Comprehensive results display with categorized tabs.
- Download results as CSV.

### 🧪 Model Comparison Testing
- Test multiple models on the same trial data.
- Comprehensive tabular comparison with all key fields.
- Performance metrics (speed, quality, field counts).
- Summary statistics (averages, fastest, best quality).
- Optional individual model result viewing.
- Batch analysis capabilities.

### 💬 Integrated Chat Assistant
- **Powered by Supabase**: Natural language querying across all trials in the database.
- Advanced search capabilities with flexible filters.
- Trial comparison and statistical analysis.
- Data export in multiple formats.
- Conversation memory and context awareness.

### 📈 Results History & System Status
- View recent analysis files.
- **Database Status**: Monitor connection to Supabase and see the total number of trials.
- Cache management.
- File download history.

## 🛠️ Installation & Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r config/requirements_ui.txt
    ```

2.  **Set up Environment:**
    Run the setup script, which will create a `.env` file and prompt for your OpenAI API key.
    ```bash
    python main.py setup
    ```

3.  **Configure Supabase:**
    Add your Supabase credentials to the `.env` file:
    ```
    SUPABASE_URL="your_supabase_project_url"
    SUPABASE_KEY="your_supabase_api_key"
    ```

4.  **Run the Application:**
    ```bash
    python main.py ui
    ```
    The application will automatically connect to Supabase and start the required background services.

## 🎯 Usage

### Single Trial Analysis
1.  Go to the "Single Trial Analysis" tab.
2.  Choose an input method: Upload JSON, enter NCT ID, or use a sample file.
3.  Select an OpenAI model.
4.  Click "Start Analysis" and view the results.

### Model Comparison
1.  Go to the "Model Comparison" tab.
2.  Configure the test data and select the models to compare.
3.  Click "Run Model Comparison" to see a detailed comparison table.

### Chat Assistant
1.  Go to the "Chat Assistant" tab.
2.  Enter natural language queries (e.g., "show me phase 2 diabetes trials").
3.  View structured results and ask follow-up questions.

### Results History
-   View recent analysis files and check the system and database status.

## 🏛️ Architecture

-   **Frontend:** Streamlit
-   **Backend Logic**: Python
-   **Database:** **Supabase (PostgreSQL)**
-   **AI Models:** OpenAI API Integration
-   **Chat & Tool Use:** Integrated Model Context Protocol (MCP) Server

## 🐛 Troubleshooting

### Common Issues

1.  **"OpenAI API Key not found" or "Supabase credentials not found"**
    -   Ensure the `.env` file exists in the project root.
    -   Verify that your `OPENAI_API_KEY`, `SUPABASE_URL`, and `SUPABASE_KEY` are correct.
    -   Check that your API keys are valid and have sufficient credits/access.

2.  **"Failed to connect to Supabase"**
    -   Double-check your `SUPABASE_URL` and `SUPABASE_KEY`.
    -   Ensure your machine has an active internet connection.
    -   Check the Supabase project status in your Supabase dashboard.

3.  **Chat Assistant is not working**
    -   Verify all setup steps were completed correctly.
    -   Ensure the database migration to Supabase was successful and tables are populated.
    -   Check the console output for any error messages when starting the UI.

## 📝 File Structure

```
clinical_trial/
├── main.py                     # Main entry point
├── src/
│   ├── ui/
│   │   ├── app.py              # Streamlit application
│   ├── database/
│   │   └── clinical_trial_database_supabase.py # Supabase DB logic
│   ├── mcp/
│   │   └── clinical_trial_mcp_server_supabase.py # MCP Server for Supabase
│   └── ...
├── config/
│   └── requirements_ui.txt   # UI dependencies
├── docs/                       # Documentation
├── .env                        # Environment variables
└── clinical_trials.db          # Local SQLite DB (for migration)
```

---

**Happy Analyzing! 🏥📊** 