#!/bin/bash
# Bootstrap script for PostgreSQL database setup

# Load environment variables from .env file
if [ -f ../.env ]; then
  source ../.env
elif [ -f ../.env.example ]; then
  source ../.env.example
fi

# Check if required environment variables are set
if [ -z "$PGUSER" ] || [ -z "$PGPASSWORD" ] || [ -z "$PGDATABASE" ] || [ -z "$PGHOST" ] || [ -z "$PGPORT" ]; then
  echo "Error: Required PostgreSQL environment variables are not set."
  echo "Please set PGUSER, PGPASSWORD, PGDATABASE, PGHOST, and PGPORT in .env file."
  exit 1
fi

# Check if database dump file exists
DUMP_FILE="../clinical_db.sql"
if [ ! -f "$DUMP_FILE" ]; then
  echo "Error: Database dump file not found at $DUMP_FILE"
  exit 1
fi

# Check if the trials table already exists
echo "Checking if trials table already exists..."
TABLE_EXISTS=$(PGPASSWORD=$PGPASSWORD psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -c '\dt trials' -tA)

if [ -z "$TABLE_EXISTS" ]; then
  echo "Trials table not found. Bootstrapping database from $DUMP_FILE..."
  
  # Import the database dump
  PGPASSWORD=$PGPASSWORD psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -f $DUMP_FILE
  
  if [ $? -eq 0 ]; then
    echo "Database bootstrap completed successfully!"
  else
    echo "Error: Failed to bootstrap database."
    exit 1
  fi
else
  echo "Trials table already exists. Skipping database bootstrap."
fi

# Check if pgvector extension is installed
echo "Checking pgvector extension..."
PGVECTOR_EXISTS=$(PGPASSWORD=$PGPASSWORD psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -c "SELECT * FROM pg_extension WHERE extname = 'vector'" -tA)

if [ -z "$PGVECTOR_EXISTS" ]; then
  echo "pgvector extension not found. Attempting to install..."
  PGPASSWORD=$PGPASSWORD psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -c "CREATE EXTENSION IF NOT EXISTS vector" -tA
  
  if [ $? -eq 0 ]; then
    echo "pgvector extension installed successfully!"
  else
    echo "Warning: Failed to install pgvector extension. Vector search may not work."
  fi
else
  echo "pgvector extension is already installed."
fi

echo "Database setup complete!" 