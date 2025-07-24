#!/usr/bin/env python3
"""
Clinical Trial Database Module
Stores processed clinical trial data for MCP server access
"""

import sqlite3
import json
import pandas as pd
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging
from pathlib import Path
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalTrialDatabase:
    """
    Database interface for storing and querying processed clinical trial data
    """
    
    def __init__(self, db_path: str = "clinical_trials.db", db_type: str = "sqlite"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to database file or connection string
            db_type: Database type ("sqlite" or "postgresql")
        """
        self.db_path = db_path
        self.db_type = db_type
        self.connection = None
        
        # Create database directory if needed
        if db_type == "sqlite":
            db_dir = Path(db_path).parent
            db_dir.mkdir(exist_ok=True)
        
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish database connection"""
        try:
            if self.db_type == "sqlite":
                self.connection = sqlite3.connect(self.db_path)
                # Enable foreign keys
                self.connection.execute("PRAGMA foreign_keys = ON")
                logger.info(f"Connected to SQLite database: {self.db_path}")
            
            elif self.db_type == "postgresql":
                import psycopg2
                self.connection = psycopg2.connect(self.db_path)
                logger.info("Connected to PostgreSQL database")
            
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
                
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        try:
            cursor = self.connection.cursor()
            
            # Main clinical trials table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clinical_trials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nct_id TEXT UNIQUE NOT NULL,
                    trial_id TEXT,
                    trial_name TEXT,
                    trial_phase TEXT,
                    trial_status TEXT,
                    patient_enrollment INTEGER,
                    sponsor TEXT,
                    sponsor_type TEXT,
                    developer TEXT,
                    start_date TEXT,
                    primary_completion_date TEXT,
                    study_completion_date TEXT,
                    primary_endpoints TEXT,
                    secondary_endpoints TEXT,
                    inclusion_criteria TEXT,
                    exclusion_criteria TEXT,
                    trial_countries TEXT,
                    geography TEXT,
                    investigator_name TEXT,
                    investigator_designation TEXT,
                    investigator_qualification TEXT,
                    investigator_location TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Drug information table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drug_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nct_id TEXT NOT NULL,
                    primary_drug TEXT,
                    primary_drug_moa TEXT,
                    primary_drug_target TEXT,
                    primary_drug_modality TEXT,
                    primary_drug_roa TEXT,
                    mono_combo TEXT,
                    combination_partner TEXT,
                    moa_of_combination TEXT,
                    experimental_regimen TEXT,
                    moa_of_experimental_regimen TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (nct_id) REFERENCES clinical_trials(nct_id) ON DELETE CASCADE
                )
            """)
            
            # Clinical information table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clinical_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nct_id TEXT NOT NULL,
                    indication TEXT,
                    line_of_therapy TEXT,
                    histology TEXT,
                    prior_treatment TEXT,
                    stage_of_disease TEXT,
                    patient_population TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (nct_id) REFERENCES clinical_trials(nct_id) ON DELETE CASCADE
                )
            """)
            
            # Biomarker information table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS biomarker_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nct_id TEXT NOT NULL,
                    biomarker_mutations TEXT,
                    biomarker_stratification TEXT,
                    biomarker_wildtype TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (nct_id) REFERENCES clinical_trials(nct_id) ON DELETE CASCADE
                )
            """)
            
            # Analysis metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nct_id TEXT NOT NULL,
                    analysis_model TEXT,
                    analysis_time REAL,
                    quality_score REAL,
                    total_fields INTEGER,
                    valid_fields INTEGER,
                    error_fields INTEGER,
                    na_fields INTEGER,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (nct_id) REFERENCES clinical_trials(nct_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nct_id ON clinical_trials(nct_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trial_phase ON clinical_trials(trial_phase)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trial_status ON clinical_trials(trial_status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sponsor ON clinical_trials(sponsor)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_primary_drug ON drug_info(primary_drug)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_indication ON clinical_info(indication)")
            
            self.connection.commit()
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def store_trial_data(self, trial_data: Dict[str, Any], analysis_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store processed clinical trial data in database
        
        Args:
            trial_data: Dictionary containing trial analysis results
            analysis_metadata: Optional metadata about the analysis (model, timing, etc.)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cursor = self.connection.cursor()
            nct_id = trial_data.get("NCT ID")
            
            if not nct_id:
                logger.error("NCT ID is required for storing trial data")
                return False
            
            # Check if trial already exists
            cursor.execute("SELECT id FROM clinical_trials WHERE nct_id = ?", (nct_id,))
            existing_trial = cursor.fetchone()
            
            if existing_trial:
                # Update existing trial
                self._update_trial_data(cursor, trial_data)
            else:
                # Insert new trial
                self._insert_trial_data(cursor, trial_data)
            
            # Store analysis metadata if provided
            if analysis_metadata:
                self._store_analysis_metadata(cursor, nct_id, analysis_metadata)
            
            self.connection.commit()
            logger.info(f"Successfully stored trial data for {nct_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store trial data: {e}")
            self.connection.rollback()
            return False
    
    def _insert_trial_data(self, cursor, trial_data: Dict[str, Any]):
        """Insert new trial data"""
        # Insert main trial data
        cursor.execute("""
            INSERT INTO clinical_trials (
                nct_id, trial_id, trial_name, trial_phase, trial_status, patient_enrollment,
                sponsor, sponsor_type, developer, start_date, primary_completion_date,
                study_completion_date, primary_endpoints, secondary_endpoints,
                inclusion_criteria, exclusion_criteria, trial_countries, geography,
                investigator_name, investigator_designation, investigator_qualification,
                investigator_location
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trial_data.get("NCT ID"),
            trial_data.get("Trial ID"),
            trial_data.get("Trial Name"),
            trial_data.get("Trial Phase"),
            trial_data.get("Trial Status"),
            trial_data.get("Patient Enrollment/Accrual"),
            trial_data.get("Sponsor"),
            trial_data.get("Sponsor Type"),
            trial_data.get("Developer"),
            trial_data.get("Start Date (YY-MM-DD)"),
            trial_data.get("Primary Completion Date (YY-MM-DD)"),
            trial_data.get("Study completion date (YY-MM-DD)"),
            trial_data.get("Primary Endpoints"),
            trial_data.get("Secondary Endpoints"),
            trial_data.get("Inclusion Criteria"),
            trial_data.get("Exclusion Criteria"),
            trial_data.get("Trial Countries"),
            trial_data.get("Geography"),
            trial_data.get("Investigator Name"),
            trial_data.get("Investigator Designation"),
            trial_data.get("Investigator Qualification"),
            trial_data.get("Investigator Location")
        ))
        
        # Insert drug information
        cursor.execute("""
            INSERT INTO drug_info (
                nct_id, primary_drug, primary_drug_moa, primary_drug_target,
                primary_drug_modality, primary_drug_roa, mono_combo, combination_partner,
                moa_of_combination, experimental_regimen, moa_of_experimental_regimen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trial_data.get("NCT ID"),
            trial_data.get("Primary Drug"),
            trial_data.get("Primary Drug MoA"),
            trial_data.get("Primary Drug Target"),
            trial_data.get("Primary Drug Modality"),
            trial_data.get("Primary Drug ROA"),
            trial_data.get("Mono/Combo"),
            trial_data.get("Combination Partner"),
            trial_data.get("MoA of Combination"),
            trial_data.get("Experimental Regimen"),
            trial_data.get("MoA of Experimental Regimen")
        ))
        
        # Insert clinical information
        cursor.execute("""
            INSERT INTO clinical_info (
                nct_id, indication, line_of_therapy, histology, prior_treatment,
                stage_of_disease, patient_population
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            trial_data.get("NCT ID"),
            trial_data.get("Indication"),
            trial_data.get("Line of Therapy"),
            trial_data.get("Histology"),
            trial_data.get("Prior Treatment"),
            trial_data.get("Stage of Disease"),
            trial_data.get("Patient Population")
        ))
        
        # Insert biomarker information
        cursor.execute("""
            INSERT INTO biomarker_info (
                nct_id, biomarker_mutations, biomarker_stratification, biomarker_wildtype
            ) VALUES (?, ?, ?, ?)
        """, (
            trial_data.get("NCT ID"),
            trial_data.get("Biomarker (Mutations)"),
            trial_data.get("Biomarker Stratification"),
            trial_data.get("Biomarker (Wildtype)")
        ))
    
    def _update_trial_data(self, cursor, trial_data: Dict[str, Any]):
        """Update existing trial data"""
        # Update main trial data
        cursor.execute("""
            UPDATE clinical_trials SET
                trial_id = ?, trial_name = ?, trial_phase = ?, trial_status = ?,
                patient_enrollment = ?, sponsor = ?, sponsor_type = ?, developer = ?,
                start_date = ?, primary_completion_date = ?, study_completion_date = ?,
                primary_endpoints = ?, secondary_endpoints = ?, inclusion_criteria = ?,
                exclusion_criteria = ?, trial_countries = ?, geography = ?,
                investigator_name = ?, investigator_designation = ?, investigator_qualification = ?,
                investigator_location = ?, updated_at = CURRENT_TIMESTAMP
            WHERE nct_id = ?
        """, (
            trial_data.get("Trial ID"),
            trial_data.get("Trial Name"),
            trial_data.get("Trial Phase"),
            trial_data.get("Trial Status"),
            trial_data.get("Patient Enrollment/Accrual"),
            trial_data.get("Sponsor"),
            trial_data.get("Sponsor Type"),
            trial_data.get("Developer"),
            trial_data.get("Start Date (YY-MM-DD)"),
            trial_data.get("Primary Completion Date (YY-MM-DD)"),
            trial_data.get("Study completion date (YY-MM-DD)"),
            trial_data.get("Primary Endpoints"),
            trial_data.get("Secondary Endpoints"),
            trial_data.get("Inclusion Criteria"),
            trial_data.get("Exclusion Criteria"),
            trial_data.get("Trial Countries"),
            trial_data.get("Geography"),
            trial_data.get("Investigator Name"),
            trial_data.get("Investigator Designation"),
            trial_data.get("Investigator Qualification"),
            trial_data.get("Investigator Location"),
            trial_data.get("NCT ID")
        ))
        
        # Update drug information
        cursor.execute("""
            UPDATE drug_info SET
                primary_drug = ?, primary_drug_moa = ?, primary_drug_target = ?,
                primary_drug_modality = ?, primary_drug_roa = ?, mono_combo = ?,
                combination_partner = ?, moa_of_combination = ?, experimental_regimen = ?,
                moa_of_experimental_regimen = ?
            WHERE nct_id = ?
        """, (
            trial_data.get("Primary Drug"),
            trial_data.get("Primary Drug MoA"),
            trial_data.get("Primary Drug Target"),
            trial_data.get("Primary Drug Modality"),
            trial_data.get("Primary Drug ROA"),
            trial_data.get("Mono/Combo"),
            trial_data.get("Combination Partner"),
            trial_data.get("MoA of Combination"),
            trial_data.get("Experimental Regimen"),
            trial_data.get("MoA of Experimental Regimen"),
            trial_data.get("NCT ID")
        ))
        
        # Update clinical information
        cursor.execute("""
            UPDATE clinical_info SET
                indication = ?, line_of_therapy = ?, histology = ?, prior_treatment = ?,
                stage_of_disease = ?, patient_population = ?
            WHERE nct_id = ?
        """, (
            trial_data.get("Indication"),
            trial_data.get("Line of Therapy"),
            trial_data.get("Histology"),
            trial_data.get("Prior Treatment"),
            trial_data.get("Stage of Disease"),
            trial_data.get("Patient Population"),
            trial_data.get("NCT ID")
        ))
        
        # Update biomarker information
        cursor.execute("""
            UPDATE biomarker_info SET
                biomarker_mutations = ?, biomarker_stratification = ?, biomarker_wildtype = ?
            WHERE nct_id = ?
        """, (
            trial_data.get("Biomarker (Mutations)"),
            trial_data.get("Biomarker Stratification"),
            trial_data.get("Biomarker (Wildtype)"),
            trial_data.get("NCT ID")
        ))
    
    def _store_analysis_metadata(self, cursor, nct_id: str, metadata: Dict[str, Any]):
        """Store analysis metadata"""
        cursor.execute("""
            INSERT INTO analysis_metadata (
                nct_id, analysis_model, analysis_time, quality_score,
                total_fields, valid_fields, error_fields, na_fields
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nct_id,
            metadata.get("model"),
            metadata.get("time"),
            metadata.get("quality_score"),
            metadata.get("total_fields"),
            metadata.get("valid_fields"),
            metadata.get("error_fields"),
            metadata.get("na_fields")
        ))
    
    def get_trial_by_nct_id(self, nct_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve complete trial data by NCT ID"""
        try:
            cursor = self.connection.cursor()
            
            # Get main trial data
            cursor.execute("""
                SELECT * FROM clinical_trials WHERE nct_id = ?
            """, (nct_id,))
            trial_row = cursor.fetchone()
            
            if not trial_row:
                return None
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            trial_data = dict(zip(columns, trial_row))
            
            # Get drug information
            cursor.execute("SELECT * FROM drug_info WHERE nct_id = ?", (nct_id,))
            drug_row = cursor.fetchone()
            if drug_row:
                drug_columns = [description[0] for description in cursor.description]
                trial_data.update(dict(zip(drug_columns, drug_row)))
            
            # Get clinical information
            cursor.execute("SELECT * FROM clinical_info WHERE nct_id = ?", (nct_id,))
            clinical_row = cursor.fetchone()
            if clinical_row:
                clinical_columns = [description[0] for description in cursor.description]
                trial_data.update(dict(zip(clinical_columns, clinical_row)))
            
            # Get biomarker information
            cursor.execute("SELECT * FROM biomarker_info WHERE nct_id = ?", (nct_id,))
            biomarker_row = cursor.fetchone()
            if biomarker_row:
                biomarker_columns = [description[0] for description in cursor.description]
                trial_data.update(dict(zip(biomarker_columns, biomarker_row)))
            
            return trial_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve trial data: {e}")
            return None
    
    def search_trials(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search trials with optional filters using AI-generated search terms
        Args:
            filters: Dictionary of field filters (can include AI-generated search_terms)
            limit: Maximum number of results
        Returns:
            List of trial data dictionaries
        """
        try:
            cursor = self.connection.cursor()
            query = (
                "SELECT ct.*, di.*, ci.*, bi.* "
                "FROM clinical_trials ct "
                "LEFT JOIN drug_info di ON ct.nct_id = di.nct_id "
                "LEFT JOIN clinical_info ci ON ct.nct_id = ci.nct_id "
                "LEFT JOIN biomarker_info bi ON ct.nct_id = bi.nct_id"
            )
            params = []
            where_clauses = []
            # Helper for multi-term, multi-field search
            def multi_field_or_like(fields, terms):
                clauses = []
                for term in terms:
                    for field in fields:
                        clauses.append(f"LOWER({field}) LIKE ?")
                        params.append(f"%{term.lower()}%")
                return "(" + " OR ".join(clauses) + ")" if clauses else None
            if filters:
                for field, value in filters.items():
                    if value is None or value == []:
                        continue
                    # Accept both single values and lists
                    values = value if isinstance(value, list) else [value]
                    if field in ["primary_drug", "drug"]:
                        clause = multi_field_or_like([
                            "primary_drug", "trial_name", "combination_partner", "experimental_regimen"
                        ], values)
                        if clause:
                            where_clauses.append(clause)
                    elif field in ["indication", "disease"]:
                        clause = multi_field_or_like([
                            "indication", "trial_name"
                        ], values)
                        if clause:
                            where_clauses.append(clause)
                    elif field == "trial_phase" or field == "phase":
                        clause = multi_field_or_like(["trial_phase"], values)
                        if clause:
                            where_clauses.append(clause)
                    elif field == "trial_status" or field == "status":
                        clause = multi_field_or_like(["trial_status"], values)
                        if clause:
                            where_clauses.append(clause)
                    elif field == "sponsor":
                        clause = multi_field_or_like(["sponsor"], values)
                        if clause:
                            where_clauses.append(clause)
                    elif field == "line_of_therapy":
                        clause = multi_field_or_like(["line_of_therapy"], values)
                        if clause:
                            where_clauses.append(clause)
                    elif field == "biomarker":
                        clause = multi_field_or_like(["biomarker_mutations", "biomarker_stratification", "biomarker_wildtype"], values)
                        if clause:
                            where_clauses.append(clause)
                    elif field == "geography":
                        clause = multi_field_or_like(["geography"], values)
                        if clause:
                            where_clauses.append(clause)
                    elif field == "enrollment_min":
                        where_clauses.append("patient_enrollment >= ?")
                        params.append(int(values[0]))
                    elif field == "enrollment_max":
                        where_clauses.append("patient_enrollment <= ?")
                        params.append(int(values[0]))
                    # Add more fields as needed
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            query += f" ORDER BY ct.created_at DESC LIMIT {limit}"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            results = []
            for row in rows:
                trial_data = dict(zip(columns, row))
                results.append(trial_data)
            return results
        except Exception as e:
            logger.error(f"Failed to search trials: {e}")
            return []
    
    def get_trial_count(self) -> int:
        """Get total number of trials in database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM clinical_trials")
            return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get trial count: {e}")
            return 0
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        try:
            cursor = self.connection.cursor()
            
            # Get model performance stats
            cursor.execute("""
                SELECT 
                    analysis_model,
                    COUNT(*) as analysis_count,
                    AVG(analysis_time) as avg_time,
                    AVG(quality_score) as avg_quality,
                    AVG(valid_fields) as avg_valid_fields
                FROM analysis_metadata
                GROUP BY analysis_model
            """)
            
            model_stats = []
            for row in cursor.fetchall():
                model_stats.append({
                    "model": row[0],
                    "analysis_count": row[1],
                    "avg_time": row[2],
                    "avg_quality": row[3],
                    "avg_valid_fields": row[4]
                })
            
            # Get phase distribution
            cursor.execute("""
                SELECT trial_phase, COUNT(*) as count
                FROM clinical_trials
                GROUP BY trial_phase
                ORDER BY count DESC
            """)
            
            phase_distribution = dict(cursor.fetchall())
            
            return {
                "total_trials": self.get_trial_count(),
                "model_stats": model_stats,
                "phase_distribution": phase_distribution
            }
            
        except Exception as e:
            logger.error(f"Failed to get analysis stats: {e}")
            return {}
    
    def export_to_csv(self, output_file: str = "clinical_trials_export.csv") -> bool:
        """Export all trial data to CSV"""
        try:
            cursor = self.connection.cursor()
            
            # Get all data joined
            cursor.execute("""
                SELECT 
                    ct.*, di.*, ci.*, bi.*
                FROM clinical_trials ct
                LEFT JOIN drug_info di ON ct.nct_id = di.nct_id
                LEFT JOIN clinical_info ci ON ct.nct_id = ci.nct_id
                LEFT JOIN biomarker_info bi ON ct.nct_id = bi.nct_id
            """)
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            df = pd.DataFrame(rows, columns=columns)
            df.to_csv(output_file, index=False)
            
            logger.info(f"Exported {len(df)} trials to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

def main():
    """Test the database functionality"""
    # Initialize database
    db = ClinicalTrialDatabase()
    
    # Test data
    test_trial = {
        "NCT ID": "NCT07046273",
        "Trial ID": "NCT07046273",
        "Trial Name": "Test Trial",
        "Trial Phase": "PHASE3",
        "Trial Status": "NOT_YET_RECRUITING",
        "Patient Enrollment/Accrual": 496,
        "Sponsor": "Test Sponsor",
        "Primary Drug": "Semaglutide",
        "Primary Drug MoA": "GLP-1 Receptor Agonist",
        "Indication": "Type 2 Diabetes",
        "Line of Therapy": "1L"
    }
    
    # Store test data
    success = db.store_trial_data(test_trial, {
        "model": "gpt-4o-mini",
        "time": 7.5,
        "quality_score": 85.0,
        "total_fields": 41,
        "valid_fields": 35,
        "error_fields": 0,
        "na_fields": 6
    })
    
    if success:
        print("✅ Test data stored successfully")
        
        # Retrieve and display
        retrieved = db.get_trial_by_nct_id("NCT07046273")
        if retrieved:
            print("✅ Data retrieved successfully")
            print(f"Trial: {retrieved.get('trial_name')}")
            print(f"Phase: {retrieved.get('trial_phase')}")
            print(f"Drug: {retrieved.get('primary_drug')}")
        
        # Get stats
        stats = db.get_analysis_stats()
        print(f"✅ Database stats: {stats.get('total_trials')} trials")
    
    db.close()

if __name__ == "__main__":
    main() 