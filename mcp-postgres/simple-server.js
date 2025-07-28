/**
 * Simplified MCP PostgreSQL Server
 * 
 * A minimal implementation to test PostgreSQL MCP server functionality
 */

const { createServer } = require('@modelcontextprotocol/server-postgres');

// Server configuration
const serverConfig = {
  // Use environment variables for connection
  user: 'postgres',
  host: 'localhost',
  database: 'postgres',
  port: 5432,
  // Other server settings
  schema: 'public',
  readOnly: true,
  statementTimeout: 30000,
  rowLimit: 1000,
  vectorSearchEnabled: false,
  serverPort: 5050,
};

console.log('Starting simplified PostgreSQL MCP server...');
console.log('Configuration:', {
  ...serverConfig,
  password: undefined // Don't log password
});

// Start the server
try {
  const server = createServer(serverConfig);
  
  server.start().then(() => {
    console.log(`PostgreSQL MCP server is running on port ${serverConfig.serverPort}`);
    console.log('Available tools:');
    console.log('- query: Execute SQL queries against the clinical trials database');
    console.log('- explain: Get query execution plan in JSON format');
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
} catch (error) {
  console.error('Error creating PostgreSQL MCP server:', error);
} 