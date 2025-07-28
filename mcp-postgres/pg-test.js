/**
 * Simple PostgreSQL Connection Test
 */

const { Client } = require('pg');
const readline = require('readline');

// Create readline interface for password input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Prompt for password
rl.question('Enter PostgreSQL password: ', async (password) => {
  // Connection configuration
  const config = {
    user: 'postgres',
    host: 'localhost',
    database: 'postgres',
    port: 5432,
    password: password, // Use the entered password
  };

  console.log('Testing PostgreSQL connection with config:', {
    ...config,
    password: '***REDACTED***' // Don't log the actual password
  });

  // Create a client
  const client = new Client(config);

  // Connect and run a test query
  try {
    // Connect to the database
    await client.connect();
    console.log('✅ Successfully connected to PostgreSQL database');
    
    // Test a simple query
    const result = await client.query('SELECT version()');
    console.log(`PostgreSQL version: ${result.rows[0].version}`);
    
    // List tables in the database
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
    
    console.log('\nConnection test completed successfully');
  } catch (error) {
    console.error('❌ Failed to connect to PostgreSQL database');
    console.error('Error:', error.message);
  } finally {
    // Close the connection
    await client.end();
    rl.close();
  }
}); 