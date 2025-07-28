/**
 * Test script for MCP PostgreSQL Server
 * 
 * This script tests the MCP PostgreSQL server by making requests to its endpoints.
 */

const http = require('http');
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../.env.example') });

const PORT = parseInt(process.env.MCP_SERVER_PORT || '5050', 10);
const HOST = 'localhost';

/**
 * Make an HTTP request to the MCP server
 * @param {string} method - HTTP method (GET, POST, etc.)
 * @param {string} path - Request path
 * @param {object} body - Request body (for POST requests)
 * @returns {Promise<object>} - Response as JSON
 */
function makeRequest(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: HOST,
      port: PORT,
      path,
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const req = http.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const jsonData = data ? JSON.parse(data) : {};
          resolve({ statusCode: res.statusCode, data: jsonData });
        } catch (error) {
          resolve({ statusCode: res.statusCode, data, error: 'Failed to parse JSON' });
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    if (body) {
      req.write(JSON.stringify(body));
    }
    
    req.end();
  });
}

/**
 * Run the tests
 */
async function runTests() {
  console.log('Testing MCP PostgreSQL Server...');
  
  try {
    // Test 1: Get resources
    console.log('\nTest 1: GET /resources');
    const resourcesResponse = await makeRequest('GET', '/resources');
    console.log(`Status: ${resourcesResponse.statusCode}`);
    console.log('Resources:', resourcesResponse.data);
    
    // Test 2: Execute a simple query
    console.log('\nTest 2: POST /tools/query with "SELECT 1 as test"');
    const queryResponse = await makeRequest('POST', '/tools/query', {
      arguments: {
        sql: 'SELECT 1 as test'
      }
    });
    console.log(`Status: ${queryResponse.statusCode}`);
    console.log('Query result:', queryResponse.data);
    
    // Test 3: Test vector search if enabled
    if (process.env.MCP_VECTOR_SEARCH_ENABLED === 'true') {
      console.log('\nTest 3: Vector search with dummy vector');
      // Create a zero vector with 768 dimensions
      const zeroVector = Array(768).fill(0);
      
      const vectorQuery = `
        SELECT id, embedding <-> '[${zeroVector}]' as distance
        FROM embeddings
        ORDER BY distance
        LIMIT 3
      `;
      
      const vectorResponse = await makeRequest('POST', '/tools/query', {
        arguments: {
          sql: vectorQuery
        }
      });
      console.log(`Status: ${vectorResponse.statusCode}`);
      console.log('Vector search result:', vectorResponse.data);
    }
    
    console.log('\nAll tests completed!');
  } catch (error) {
    console.error('Test failed:', error);
  }
}

// Run the tests
runTests(); 