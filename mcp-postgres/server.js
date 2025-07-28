/**
 * MCP PostgreSQL Server for Clinical Trial Analyzer
 * 
 * This script creates a Model Context Protocol (MCP) server that connects to a
 * PostgreSQL database containing clinical trial data. It allows AI models to
 * query the database through a standardized protocol.
 */

// Use CommonJS require since the package.json specifies type: "commonjs"
const { createServer } = require('@modelcontextprotocol/server-postgres');
const fs = require('fs');
const path = require('path');

// Set connection parameters directly
const connectionConfig = {
  user: 'postgres',
  host: 'localhost',
  database: 'postgres',
  port: 5432,
  // No password - using trust authentication
};

// Build a connection string from the config
const connectionString = `postgresql://${connectionConfig.user}@${connectionConfig.host}:${connectionConfig.port}/${connectionConfig.database}`;

// Server configuration
const serverConfig = {
  connectionString,
  schema: 'public',
  readOnly: true,
  statementTimeout: 30000,
  rowLimit: 1000,
  vectorSearchEnabled: true,
  port: 5050,
};

console.log('Starting PostgreSQL MCP server with configuration:');
console.log({
  ...serverConfig,
  connectionString: '***REDACTED***', // Don't log the connection string with credentials
});

// Start the server
const server = createServer(serverConfig);

server.start().then(() => {
  console.log(`PostgreSQL MCP server is running on port ${serverConfig.port}`);
  console.log('Available tools:');
  console.log('- query: Execute SQL queries against the clinical trials database');
  console.log('- explain: Get query execution plan in JSON format');
  
  if (serverConfig.vectorSearchEnabled) {
    console.log('Vector search is enabled. You can use pgvector operators:');
    console.log('- <->: L2 distance (Euclidean)');
    console.log('- <=>: Cosine distance');
    console.log('- <#>: Inner product');
  }
}).catch(error => {
  console.error('Failed to start PostgreSQL MCP server:', error);
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('Shutting down PostgreSQL MCP server...');
  server.stop().then(() => {
    console.log('Server stopped gracefully');
    process.exit(0);
  }).catch(error => {
    console.error('Error stopping server:', error);
    process.exit(1);
  });
}); 