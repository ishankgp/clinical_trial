#!/usr/bin/env python3
"""
Inspect SQLite Database Schema
Prints the schema of all tables in the SQLite database
"""

import sqlite3
import pandas as pd
import os

def inspect_sqlite_schema(db_path: str):
    """Prints the schema and first few rows of each table"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at: {db_path}")
        return
        
    print(f"🔬 Inspecting database: {db_path}")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Get list of tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            return
            
        print(f"Found tables: {[table[0] for table in tables]}")
        
        # Print schema and head for each table
        for table in tables:
            table_name = table[0]
            print(f"\n🔎 Table: {table_name}")
            print("-" * 30)
            
            # Get schema info
            df = pd.read_sql_query(f"PRAGMA table_info({table_name});", conn)
            print("Schema:")
            print(df)
            
            # Get sample data
            df_head = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5;", conn)
            print("\nSample Data:")
            print(df_head)
            print("-" * 30)
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error inspecting SQLite database: {e}")

if __name__ == "__main__":
    inspect_sqlite_schema("clinical_trials.db") 