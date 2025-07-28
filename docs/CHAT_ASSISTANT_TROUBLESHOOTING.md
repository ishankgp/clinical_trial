# Chat Assistant Troubleshooting Guide

## 🤖 Overview

The Chat Assistant tab provides advanced natural language querying capabilities for clinical trials. It is powered by an integrated Model Context Protocol (MCP) server that connects to a **Supabase** database backend. This guide helps you resolve common issues.

## 🚨 Common Issues

### 1. "Failed to connect to Supabase"

**Symptoms:**
-   Red error message in the UI on startup.
-   "Failed to connect to Supabase" or similar database connection errors in the console logs.
-   The Chat Assistant tab may be unresponsive or show connection errors.

**Causes:**
-   Incorrect `SUPABASE_URL` or `SUPABASE_KEY` in the `.env` file.
-   No internet connection.
-   Supabase project is paused or experiencing issues.
-   Firewall or network policies blocking the connection.

**Solutions:**

-   **Verify `.env` file**: Double-check that your Supabase credentials in the `.env` file are correct.
-   **Check Internet Connection**: Ensure your machine can access the internet.
-   **Check Supabase Status**: Visit your Supabase project dashboard to ensure it's active.
-   **Test Connection**: Use a simple script to test the connection independently (see `simple_supabase_test.py`).

### 2. Chat Assistant Returns No Data or Errors

**Symptoms:**
-   Queries like "list all trials" return an empty result.
-   You see errors in the console related to `NoneType` or missing data.
-   The UI shows "No trials found" even when you expect data.

**Causes:**
-   The database migration was not run or failed.
-   The Supabase tables are empty.
-   Row Level Security (RLS) policies in Supabase are blocking access.

**Solutions:**

-   **Run Data Migration**: Ensure you have run `python migrate_data_to_supabase.py` successfully.
-   **Check Supabase Tables**: Log in to your Supabase project and verify that the `clinical_trials`, `drug_info`, and `clinical_info` tables contain data.
-   **Review RLS Policies**: Check the RLS policies on your tables. For testing, you can set up a permissive policy that allows reads for `anon` users. Refer to `fix_supabase_rls.sql` for an example.

### 3. "OpenAI API Key not found" or 401 Errors from OpenAI

**Symptoms:**
-   An error message indicating an issue with the OpenAI API key.
-   The assistant responds with an authentication error.

**Causes:**
-   `OPENAI_API_KEY` is missing from the `.env` file or is incorrect.
-   Your OpenAI account has insufficient credits.

**Solutions:**

-   **Verify API Key**: Ensure your `OPENAI_API_KEY` is correctly set in the `.env` file.
-   **Check OpenAI Account**: Check your OpenAI account status and usage limits.

## 🔧 Step-by-Step Troubleshooting

### Phase 1: Verify Configuration

1.  **Check `.env` file**:
    Make sure it contains all three required keys:
    ```
    OPENAI_API_KEY="sk-..."
    SUPABASE_URL="https://....supabase.co"
    SUPABASE_KEY="ey..."
    ```

2.  **Check Dependencies**:
    Ensure all requirements are installed:
    ```bash
    pip install -r config/requirements.txt
    pip install -r config/requirements_ui.txt
    ```

### Phase 2: Test Database Connection & Data

1.  **Run Supabase Connection Test**:
    Execute `simple_supabase_test.py` to verify that a basic connection can be established.

2.  **Inspect Supabase Data**:
    -   Log in to your Supabase dashboard.
    -   Use the Table Editor to view the `clinical_trials` table.
    -   Confirm that it has rows of data. If not, the migration failed.

### Phase 3: Test the Full Application

1.  **Run the UI**:
    ```bash
    python main.py ui
    ```

2.  **Check Console Logs**:
    -   Look for "✅ Connected to Supabase successfully".
    -   Look for "MCP server started successfully".
    -   Watch for any red error messages.

3.  **Test in the UI**:
    -   Navigate to the "Chat Assistant" tab.
    -   Start with a very simple query like `"list trials limit 1"`.
    -   If that works, try a more complex query like `"find diabetes trials"`.

## 🛠️ Advanced Troubleshooting

### 1. Debug Logging
If you're facing persistent issues, enable debug logging in the database and MCP files to get more detailed output.
-   In `src/database/clinical_trial_database_supabase.py`:
    ```python
    logging.basicConfig(level=logging.DEBUG)
    ```
-   In `src/mcp/clinical_trial_chat_mcp.py`:
    ```python
    logging.basicConfig(level=logging.DEBUG)
    ```
    Then, rerun `python main.py ui` and check the detailed logs.

### 2. Clearing the Database
If you suspect a corrupted migration, you can clear the data in your Supabase tables and re-run the migration.
-   Use the `clear_supabase_data.sql` script in your Supabase SQL Editor.
-   Then, run `python migrate_data_to_supabase.py` again.

## 🎉 Success Indicators

When everything is working correctly:

-   ✅ The UI starts without any connection errors in the console.
-   ✅ The "Database Status" in the UI shows a successful connection and the correct trial count.
-   ✅ The Chat Assistant is responsive.
-   ✅ Natural language queries return accurate results from your Supabase data. 