/**
 * Test PostgreSQL Connection
 * 
 * This script tests the connection to the PostgreSQL database.
 */

const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');

// Set connection parameters directly instead of using a connection string
const connectionConfig = {
  user: 'postgres',
  host: 'localhost',
  database: 'postgres',
  port: 5432,
  // No password - using trust authentication
};

console.log('Testing PostgreSQL connection...');
console.log('Connection config:', {
  ...connectionConfig,
  // Don't log password if it was set
  password: connectionConfig.password ? '***REDACTED***' : undefined
});

// Create a connection pool
const pool = new Pool(connectionConfig);

// Test the connection
async function testConnection() {
  let client;
  
  try {
    // Connect to the database
    client = await pool.connect();
    console.log('✅ Successfully connected to PostgreSQL database');
    
    // Test a simple query
    const result = await client.query('SELECT version()');
    console.log(`PostgreSQL version: ${result.rows[0].version}`);
    
    // Check for pgvector extension
    try {
      const vectorResult = await client.query("SELECT * FROM pg_extension WHERE extname = 'vector'");
      if (vectorResult.rowCount > 0) {
        console.log('✅ pgvector extension is installed');
      } else {
        console.log('❌ pgvector extension is not installed');
        console.log('To install pgvector, run: CREATE EXTENSION IF NOT EXISTS vector;');
      }
    } catch (vectorError) {
      console.error('Error checking pgvector extension:', vectorError.message);
    }
    
    // List tables in the database
    try {
      const tablesResult = await client.query(`
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
      `);
      
      console.log('\nDatabase tables:');
      if (tablesResult.rowCount === 0) {
        console.log('No tables found in the public schema');
      } else {
        tablesResult.rows.forEach(row => {
          console.log(`- ${row.table_name}`);
        });
      }
    } catch (tablesError) {
      console.error('Error listing tables:', tablesError.message);
    }
    
  } catch (error) {
    console.error('❌ Failed to connect to PostgreSQL database');
    console.error('Error:', error.message);
    process.exit(1);
  } finally {
    // Release the client back to the pool
    if (client) {
      client.release();
    }
    
    // Close the pool
    await pool.end();
  }
}

// Run the test
testConnection(); 