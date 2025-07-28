#!/usr/bin/env python3
"""
Simple Supabase Connection Test
Tests connection to your Supabase project
"""

import requests
import json

def test_supabase_connection():
    """Test basic Supabase connection"""
    
    # Your Supabase credentials
    supabase_url = "https://hvmazsmkfzjwmrbdilfq.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2bWF6c21rZnpqd21yYmRpbGZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2OTI5OTMsImV4cCI6MjA2OTI2ODk5M30.rajuDXjG_KSQhL968L8FRXgxRFgzIIuwo25pZ6ndoSU"
    
    print("🏥 Testing Supabase Connection")
    print("=" * 50)
    print(f"URL: {supabase_url}")
    print(f"API Key: {supabase_key[:20]}...")
    print()
    
    # Test 1: Basic API connection
    print("1. Testing basic API connection...")
    try:
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # Test the REST API endpoint
        response = requests.get(f"{supabase_url}/rest/v1/", headers=headers)
        
        if response.status_code == 200:
            print("✅ Basic API connection successful!")
        else:
            print(f"❌ API connection failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    # Test 2: Check if clinical_trials table exists
    print("\n2. Testing clinical_trials table...")
    try:
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # Try to query the clinical_trials table
        response = requests.get(
            f"{supabase_url}/rest/v1/clinical_trials?select=count",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ clinical_trials table exists and is accessible!")
            data = response.json()
            print(f"   Table data: {data}")
        elif response.status_code == 404:
            print("⚠️  clinical_trials table doesn't exist yet")
            print("   This is expected - you need to create the tables first")
        else:
            print(f"❌ Table query failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Table test error: {e}")
    
    # Test 3: Test inserting a sample record
    print("\n3. Testing data insertion...")
    try:
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # Sample trial data
        sample_trial = {
            'nct_id': 'NCT12345678',
            'trial_name': 'Test Clinical Trial',
            'trial_phase': 'Phase 2',
            'trial_status': 'Recruiting',
            'patient_enrollment': 100,
            'sponsor': 'Test Sponsor',
            'primary_endpoints': 'Safety and efficacy',
            'secondary_endpoints': 'Quality of life',
            'inclusion_criteria': 'Age 18-65',
            'exclusion_criteria': 'Pregnancy'
        }
        
        response = requests.post(
            f"{supabase_url}/rest/v1/clinical_trials",
            headers=headers,
            json=sample_trial
        )
        
        if response.status_code == 201:
            print("✅ Data insertion successful!")
            data = response.json()
            print(f"   Inserted record: {data}")
        elif response.status_code == 404:
            print("⚠️  Table doesn't exist - need to create tables first")
        else:
            print(f"❌ Insertion failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Insertion test error: {e}")
    
    print("\n" + "=" * 50)
    print("📋 NEXT STEPS:")
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Run the SQL script from supabase_setup.sql")
    print("4. Test the connection again")
    print("5. Update your environment variables")
    print("=" * 50)

def create_environment_files():
    """Create environment configuration files"""
    
    print("\n🔧 Creating environment configuration files...")
    
    # Create .env.supabase
    env_content = """# Supabase Configuration
SUPABASE_URL=https://hvmazsmkfzjwmrbdilfq.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2bWF6c21rZnpqd21yYmRpbGZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2OTI5OTMsImV4cCI6MjA2OTI2ODk5M30.rajuDXjG_KSQhL968L8FRXgxRFgzIIuwo25pZ6ndoSU

# Database URL for compatibility
DATABASE_URL=postgresql://postgres.hvmazsmkfzjwmrbdilfq.supabase.co:5432/postgres

# OpenAI Configuration (keep your existing key)
OPENAI_API_KEY=your_openai_api_key_here

# MCP Server Configuration
MCP_SERVER_PORT=5050
MCP_READ_ONLY=true
MCP_STATEMENT_TIMEOUT=30000
MCP_ROW_LIMIT=1000
MCP_VECTOR_SEARCH_ENABLED=true
"""
    
    with open('.env.supabase', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env.supabase")
    
    # Create SQL script file
    sql_script = """-- Supabase SQL Script for Clinical Trial Tables
-- Run this in your Supabase SQL Editor

-- Create clinical_trials table
CREATE TABLE IF NOT EXISTS clinical_trials (
    id BIGSERIAL PRIMARY KEY,
    nct_id TEXT UNIQUE NOT NULL,
    trial_name TEXT,
    trial_phase TEXT,
    trial_status TEXT,
    patient_enrollment INTEGER,
    sponsor TEXT,
    primary_endpoints TEXT,
    secondary_endpoints TEXT,
    inclusion_criteria TEXT,
    exclusion_criteria TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create drug_info table
CREATE TABLE IF NOT EXISTS drug_info (
    id BIGSERIAL PRIMARY KEY,
    trial_id BIGINT REFERENCES clinical_trials(id) ON DELETE CASCADE,
    primary_drug TEXT,
    drug_class TEXT,
    mechanism_of_action TEXT,
    dosage_form TEXT,
    dosage_schedule TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create clinical_info table
CREATE TABLE IF NOT EXISTS clinical_info (
    id BIGSERIAL PRIMARY KEY,
    trial_id BIGINT REFERENCES clinical_trials(id) ON DELETE CASCADE,
    indication TEXT,
    disease_area TEXT,
    patient_population TEXT,
    age_range TEXT,
    gender_eligibility TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_nct_id ON clinical_trials(nct_id);
CREATE INDEX IF NOT EXISTS idx_trial_phase ON clinical_trials(trial_phase);
CREATE INDEX IF NOT EXISTS idx_trial_status ON clinical_trials(trial_status);
CREATE INDEX IF NOT EXISTS idx_sponsor ON clinical_trials(sponsor);
CREATE INDEX IF NOT EXISTS idx_primary_drug ON drug_info(primary_drug);
CREATE INDEX IF NOT EXISTS idx_indication ON clinical_info(indication);

-- Enable Row Level Security (RLS)
ALTER TABLE clinical_trials ENABLE ROW LEVEL SECURITY;
ALTER TABLE drug_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical_info ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (adjust based on your security needs)
CREATE POLICY "Allow read access to all users" ON clinical_trials
    FOR SELECT USING (true);
    
CREATE POLICY "Allow read access to all users" ON drug_info
    FOR SELECT USING (true);
    
CREATE POLICY "Allow read access to all users" ON clinical_info
    FOR SELECT USING (true);

-- Create a function to get schema information
CREATE OR REPLACE FUNCTION get_schema_info()
RETURNS TABLE(table_name text, column_name text, data_type text) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.table_name::text,
        c.column_name::text,
        c.data_type::text
    FROM information_schema.tables t
    JOIN information_schema.columns c ON t.table_name = c.table_name
    WHERE t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_name, c.ordinal_position;
END;
$$ LANGUAGE plpgsql;
"""
    
    with open('supabase_setup.sql', 'w') as f:
        f.write(sql_script)
    
    print("✅ Created supabase_setup.sql")
    print("\n📋 SQL Script Instructions:")
    print("1. Go to https://supabase.com/dashboard/project/hvmazsmkfzjwmrbdilfq")
    print("2. Click on 'SQL Editor' in the left sidebar")
    print("3. Copy and paste the contents of supabase_setup.sql")
    print("4. Click 'Run' to execute the script")
    print("5. Come back and run this test again")

if __name__ == "__main__":
    test_supabase_connection()
    create_environment_files() 