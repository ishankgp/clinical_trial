# MCP PostgreSQL Server for Clinical Trial Analyzer

This directory contains a Model Context Protocol (MCP) server that connects to a PostgreSQL database containing clinical trial data. It allows AI models to query the database through a standardized protocol.

## Features

- **Schema Discovery**: Automatically discovers database schema on startup
- **SQL Query Tool**: Execute SQL queries against the clinical trials database
- **Query Explain Tool**: Get query execution plans in JSON format
- **Vector Search Support**: Use pgvector operators for vector similarity search
- **Security**: Read-only mode and query timeout guards
- **Connection Pooling**: Efficient database connection management

## Prerequisites

- Node.js 18 or higher
- PostgreSQL database with clinical trial data
- pgvector extension installed (for vector search)

## Setup

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Configure environment variables**
   Copy the example environment file and update it with your PostgreSQL credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Bootstrap the database** (if needed)
   If you have a SQL dump file named `clinical_db.sql` in the project root, you can use the bootstrap script to set up the database:
   ```bash
   npm run bootstrap-db
   ```

## Usage

### Start the server

```bash
# Development mode (with auto-reload)
npm run dev

# Production mode
npm start
```

The server will start on port 5050 (or the port specified in your environment variables).

### Test the server

```bash
npm test
```

This will run tests to verify that the server is working correctly.

## MCP Client Integration

### Claude Desktop

1. Open Claude Desktop settings
2. Navigate to the Developer tab
3. Click "Edit Config"
4. Copy the contents of `claude_desktop_config.json` into the configuration file
5. Update the database credentials
6. Save and restart Claude Desktop

### Cursor

1. Open Cursor settings
2. Search for "MCP"
3. Click "Edit in settings.json"
4. Copy the contents of `cursor_settings.json` into the settings file
5. Update the database credentials
6. Save and restart Cursor

## API Examples

### Query Tool

```json
{
  "tool": "query",
  "arguments": {
    "sql": "SELECT * FROM clinical_trials LIMIT 10"
  }
}
```

### Explain Tool

```json
{
  "tool": "explain",
  "arguments": {
    "sql": "SELECT * FROM clinical_trials WHERE indication = 'diabetes'"
  }
}
```

### Vector Search Example

```json
{
  "tool": "query",
  "arguments": {
    "sql": "SELECT id, embedding <-> '[0,0,0,...]' as distance FROM embeddings ORDER BY distance LIMIT 5"
  }
}
```

## Troubleshooting

- **Connection Issues**: Verify your database credentials in the `.env` file
- **Schema Discovery Fails**: Ensure the database user has permissions to access schema information
- **Vector Search Errors**: Check that pgvector extension is installed with `SELECT * FROM pg_extension WHERE extname = 'vector'` 