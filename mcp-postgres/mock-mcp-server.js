/**
 * Mock MCP Server for Clinical Trial Data
 * 
 * This script creates a simple HTTP server that implements the Model Context Protocol
 * without requiring a PostgreSQL database. It provides mock data for testing purposes.
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

// Mock clinical trial data
const mockTrials = [
  {
    nct_id: 'NCT12345678',
    trial_name: 'Study of Drug X in Patients with Cancer',
    trial_phase: 'Phase 3',
    trial_status: 'Recruiting',
    primary_drug: 'Drug X',
    indication: 'Cancer',
    sponsor: 'Pharma Company'
  },
  {
    nct_id: 'NCT87654321',
    trial_name: 'Efficacy of Drug Y in Diabetes',
    trial_phase: 'Phase 2',
    trial_status: 'Completed',
    primary_drug: 'Drug Y',
    indication: 'Diabetes',
    sponsor: 'University Medical Center'
  },
  {
    nct_id: 'NCT11223344',
    trial_name: 'Safety Study of Drug Z in Hypertension',
    trial_phase: 'Phase 1',
    trial_status: 'Active, not recruiting',
    primary_drug: 'Drug Z',
    indication: 'Hypertension',
    sponsor: 'Biotech Inc.'
  }
];

// Server port
const PORT = 5050;

// Create HTTP server
const server = http.createServer((req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  // Handle OPTIONS requests (preflight)
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }
  
  // Parse URL
  const url = new URL(req.url, `http://${req.headers.host}`);
  const pathname = url.pathname;
  
  // Handle different endpoints
  if (pathname === '/resources' && req.method === 'GET') {
    // Return available resources
    const resources = {
      resources: [
        {
          name: 'clinical_trials',
          description: 'Clinical trial data',
          type: 'table'
        }
      ]
    };
    
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(resources));
  }
  else if (pathname === '/tools' && req.method === 'GET') {
    // Return available tools
    const tools = {
      tools: [
        {
          name: 'query',
          description: 'Execute SQL queries against the clinical trials database',
          inputSchema: {
            type: 'object',
            properties: {
              sql: {
                type: 'string',
                description: 'SQL query to execute'
              }
            },
            required: ['sql']
          }
        },
        {
          name: 'explain',
          description: 'Get query execution plan in JSON format',
          inputSchema: {
            type: 'object',
            properties: {
              sql: {
                type: 'string',
                description: 'SQL query to explain'
              }
            },
            required: ['sql']
          }
        }
      ]
    };
    
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(tools));
  }
  else if (pathname === '/tools/query' && req.method === 'POST') {
    // Handle query tool
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        const sql = data.arguments?.sql;
        
        if (!sql) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'SQL query is required' }));
          return;
        }
        
        // Process the SQL query (mock implementation)
        if (sql.toLowerCase().includes('select * from clinical_trials')) {
          // Return all trials
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ result: mockTrials }));
        }
        else if (sql.toLowerCase().includes('select count(*) from clinical_trials')) {
          // Return count
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ result: [{ count: mockTrials.length }] }));
        }
        else if (sql.toLowerCase().includes('select 1')) {
          // Simple test query
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ result: [{ '?column?': 1 }] }));
        }
        else {
          // Default response for other queries
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ result: [] }));
        }
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
    });
  }
  else if (pathname === '/tools/explain' && req.method === 'POST') {
    // Handle explain tool
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });
    
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        const sql = data.arguments?.sql;
        
        if (!sql) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'SQL query is required' }));
          return;
        }
        
        // Return mock explain plan
        const explainPlan = {
          "Plan": {
            "Node Type": "Seq Scan",
            "Relation Name": "clinical_trials",
            "Alias": "clinical_trials",
            "Startup Cost": 0.00,
            "Total Cost": 11.40,
            "Plan Rows": 140,
            "Plan Width": 512
          }
        };
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ result: explainPlan }));
      } catch (error) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
    });
  }
  else {
    // Handle 404
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not Found' }));
  }
});

// Start the server
server.listen(PORT, () => {
  console.log(`Mock MCP Server running on http://localhost:${PORT}`);
  console.log('Available endpoints:');
  console.log('- GET /resources: List available resources');
  console.log('- GET /tools: List available tools');
  console.log('- POST /tools/query: Execute SQL queries');
  console.log('- POST /tools/explain: Get query execution plan');
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('Shutting down Mock MCP Server...');
  server.close(() => {
    console.log('Server stopped gracefully');
    process.exit(0);
  });
}); 