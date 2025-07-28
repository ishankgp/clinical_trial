#!/usr/bin/env python3
"""
Corrected Data Migration Script: SQLite to Supabase
Migrates all clinical trial data from SQLite to Supabase with matching schemas
"""

import os
import sqlite3
import requests
import json
import pandas as pd
from datetime import datetime
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CorrectedDataMigrator:
    """Handles migration of data from SQLite to Supabase with correct schemas"""
    
    def __init__(self):
        self.supabase_url = "https://hvmazsmkfzjwmrbdilfq.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2bWF6c21rZnpqd21yYmRpbGZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2OTI5OTMsImV4cCI6MjA2OTI2ODk5M30.rajuDXjG_KSQhL968L8FRXgxRFgzIIuwo25pZ6ndoSU"
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }
    
    def migrate_table(self, table_name: str, conn):
        """Migrate a single table from SQLite to Supabase"""
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            logger.info(f"Found {len(df)} records in '{table_name}' to migrate")
            
            # Remove the 'id' column if it exists, as Supabase will generate it
            if 'id' in df.columns:
                df = df.drop(columns=['id'])
            
            records = df.to_dict(orient='records')
            
            # Supabase prefers null instead of NaN for JSON
            for record in records:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
            
            # The REST API has a limit of around 1000 rows per request
            chunk_size = 500
            migrated_count = 0
            for i in range(0, len(records), chunk_size):
                chunk = records[i:i + chunk_size]
                response = requests.post(
                    f"{self.supabase_url}/rest/v1/{table_name}",
                    headers=self.headers,
                    json=chunk
                )
                
                if response.status_code == 201:
                    migrated_count += len(chunk)
                    logger.info(f"✅ Migrated {len(chunk)} records to '{table_name}'")
                else:
                    logger.error(f"❌ Failed to migrate chunk to '{table_name}': {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    # Try inserting row-by-row for this failed chunk to find the issue
                    for row in chunk:
                        row_res = requests.post(f"{self.supabase_url}/rest/v1/{table_name}", headers=self.headers, json=row)
                        if row_res.status_code != 201:
                            logger.error(f"Failed row in {table_name}: {row}")
                            logger.error(f"Reason: {row_res.text}")

            logger.info(f"✅ Finished migrating '{table_name}'. Migrated {migrated_count}/{len(df)} records.")

        except pd.io.sql.DatabaseError as e:
            logger.warning(f"⚠️ Could not read table '{table_name}' from SQLite: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during migration of '{table_name}': {e}")
    
    def run_migration(self):
        """Run the full data migration process"""
        sqlite_db_path = "clinical_trials.db"
        
        if not os.path.exists(sqlite_db_path):
            logger.error("❌ SQLite database file not found. Cannot proceed.")
            return

        try:
            # Add a delay to allow schema cache to update
            print("⏳ Waiting 5 seconds for Supabase schema cache to refresh...")
            time.sleep(5)

            with sqlite3.connect(sqlite_db_path) as conn:
                tables_to_migrate = [
                    'clinical_trials', 
                    'drug_info', 
                    'clinical_info', 
                    'biomarker_info', 
                    'analysis_metadata'
                ]
                
                for table in tables_to_migrate:
                    self.migrate_table(table, conn)
                    
            print("\n🎉 Full data migration process completed!")

        except Exception as e:
            logger.error(f"❌ A critical error occurred during the migration process: {e}")

if __name__ == "__main__":
    print("🚀 Starting Corrected Data Migration: SQLite to Supabase")
    print("Please make sure you have run 'corrected_supabase_setup.sql' in your Supabase project first.")
    print("=" * 70)
    
    migrator = CorrectedDataMigrator()
    migrator.run_migration()
    
    print("\n✅ Migration script finished. Check the logs for details.") 