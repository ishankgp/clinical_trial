#!/usr/bin/env python3
"""
Supabase Migration Script for Clinical Trial Analysis System
Migrates from local PostgreSQL to Supabase cloud database
"""

import os
import json
import pandas as pd
from typing import Dict, List, Any
import logging
from pathlib import Path
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupabaseMigration:
    """
    Handles migration from local PostgreSQL to Supabase
    """
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize Supabase client
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Client = create_client(supabase_url, supabase_key)
        
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Test connection with a simple query
            response = self.client.table('clinical_trials').select('count').limit(1).execute()
            logger.info("✅ Successfully connected to Supabase")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            return False
    
    def create_tables(self) -> bool:
        """Create necessary tables in Supabase"""
        try:
            # Note: In Supabase, you typically create tables via SQL editor or migrations
            # This is a placeholder for the table creation logic
            logger.info("📋 Tables should be created via Supabase SQL editor")
            logger.info("Run the following SQL in your Supabase SQL editor:")
            
            sql_script = """
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
            """
            
            print("=" * 60)
            print("SUPABASE SQL SCRIPT")
            print("=" * 60)
            print(sql_script)
            print("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False
    
    def migrate_data_from_sqlite(self, sqlite_db_path: str) -> bool:
        """Migrate data from SQLite database to Supabase"""
        try:
            import sqlite3
            
            # Connect to SQLite database
            sqlite_conn = sqlite3.connect(sqlite_db_path)
            
            # Read data from SQLite
            trials_df = pd.read_sql_query("SELECT * FROM clinical_trials", sqlite_conn)
            drug_df = pd.read_sql_query("SELECT * FROM drug_info", sqlite_conn)
            clinical_df = pd.read_sql_query("SELECT * FROM clinical_info", sqlite_conn)
            
            logger.info(f"📊 Found {len(trials_df)} trials to migrate")
            
            # Migrate clinical trials
            if not trials_df.empty:
                for _, trial in trials_df.iterrows():
                    trial_data = trial.to_dict()
                    # Remove id to let Supabase auto-generate
                    if 'id' in trial_data:
                        del trial_data['id']
                    
                    # Insert into Supabase
                    response = self.client.table('clinical_trials').insert(trial_data).execute()
                    logger.info(f"Migrated trial: {trial_data.get('nct_id', 'Unknown')}")
            
            # Migrate drug info
            if not drug_df.empty:
                for _, drug in drug_df.iterrows():
                    drug_data = drug.to_dict()
                    if 'id' in drug_data:
                        del drug_data['id']
                    
                    response = self.client.table('drug_info').insert(drug_data).execute()
                    logger.info(f"Migrated drug info for trial: {drug_data.get('trial_id', 'Unknown')}")
            
            # Migrate clinical info
            if not clinical_df.empty:
                for _, clinical in clinical_df.iterrows():
                    clinical_data = clinical.to_dict()
                    if 'id' in clinical_data:
                        del clinical_data['id']
                    
                    response = self.client.table('clinical_info').insert(clinical_data).execute()
                    logger.info(f"Migrated clinical info for trial: {clinical_data.get('trial_id', 'Unknown')}")
            
            sqlite_conn.close()
            logger.info("✅ Data migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate data: {e}")
            return False
    
    def update_environment_config(self):
        """Update environment configuration for Supabase"""
        try:
            # Create new environment file for Supabase
            env_content = f"""# Supabase Configuration
SUPABASE_URL={self.supabase_url}
SUPABASE_KEY={self.supabase_key}

# Database URL for compatibility
DATABASE_URL=postgresql://postgres.hvmazsmkfzjwmrbdilfq.supabase.co:5432/postgres

# OpenAI Configuration
OPENAI_API_KEY={os.getenv('OPENAI_API_KEY', '')}

# MCP Server Configuration
MCP_SERVER_PORT=5050
MCP_READ_ONLY=true
MCP_STATEMENT_TIMEOUT=30000
MCP_ROW_LIMIT=1000
MCP_VECTOR_SEARCH_ENABLED=true
"""
            
            with open('.env.supabase', 'w') as f:
                f.write(env_content)
            
            logger.info("✅ Created .env.supabase configuration file")
            
            # Update pg_config.env for Supabase
            pg_config_content = f"""DATABASE_URL=postgresql://postgres.hvmazsmkfzjwmrbdilfq.supabase.co:5432/postgres
PGUSER=postgres
PGPASSWORD=your_supabase_password_here
PGDATABASE=postgres
PGHOST=db.hvmazsmkfzjwmrbdilfq.supabase.co
PGPORT=5432
MCP_SERVER_PORT=5050
MCP_READ_ONLY=true
MCP_STATEMENT_TIMEOUT=30000
MCP_ROW_LIMIT=1000
MCP_VECTOR_SEARCH_ENABLED=true
"""
            
            with open('pg_config.supabase.env', 'w') as f:
                f.write(pg_config_content)
            
            logger.info("✅ Created pg_config.supabase.env configuration file")
            
        except Exception as e:
            logger.error(f"Failed to update environment config: {e}")
    
    def test_queries(self):
        """Test various queries on Supabase"""
        try:
            logger.info("🧪 Testing Supabase queries...")
            
            # Test basic query
            response = self.client.table('clinical_trials').select('*').limit(5).execute()
            logger.info(f"✅ Basic query returned {len(response.data)} records")
            
            # Test filtered query
            response = self.client.table('clinical_trials').select('*').eq('trial_phase', 'Phase 3').limit(5).execute()
            logger.info(f"✅ Filtered query returned {len(response.data)} Phase 3 trials")
            
            # Test join query
            response = self.client.table('clinical_trials').select('*, drug_info(*)').limit(5).execute()
            logger.info(f"✅ Join query returned {len(response.data)} records with drug info")
            
            logger.info("✅ All query tests passed")
            
        except Exception as e:
            logger.error(f"Query test failed: {e}")

def main():
    """Main migration function"""
    print("🏥 Clinical Trial System - Supabase Migration")
    print("=" * 50)
    
    # Your Supabase credentials
    supabase_url = "https://hvmazsmkfzjwmrbdilfq.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2bWF6c21rZnpqd21yYmRpbGZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2OTI5OTMsImV4cCI6MjA2OTI2ODk5M30.rajuDXjG_KSQhL968L8FRXgxRFgzIIuwo25pZ6ndoSU"
    
    # Initialize migration
    migration = SupabaseMigration(supabase_url, supabase_key)
    
    # Test connection
    if not migration.test_connection():
        print("❌ Cannot proceed without Supabase connection")
        return
    
    # Create tables
    migration.create_tables()
    
    # Check if SQLite database exists
    sqlite_db_path = "clinical_trials.db"
    if os.path.exists(sqlite_db_path):
        print(f"\n📁 Found SQLite database: {sqlite_db_path}")
        migrate_data = input("Do you want to migrate data from SQLite? (y/n): ").lower().strip()
        
        if migrate_data == 'y':
            migration.migrate_data_from_sqlite(sqlite_db_path)
    else:
        print(f"\n📁 No SQLite database found at: {sqlite_db_path}")
    
    # Update configuration
    migration.update_environment_config()
    
    # Test queries
    migration.test_queries()
    
    print("\n🎉 Supabase migration completed!")
    print("\n📋 Next steps:")
    print("1. Run the SQL script in your Supabase SQL editor")
    print("2. Update your application to use Supabase credentials")
    print("3. Test your MCP server with the new Supabase connection")
    print("4. Update your environment variables to use .env.supabase")

if __name__ == "__main__":
    main() 