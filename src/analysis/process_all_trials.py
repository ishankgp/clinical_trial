#!/usr/bin/env python3
"""
Process All Clinical Trials - Single Trial Analysis & Model Comparison
Analyzes all stored trials with multiple models and stores comparison results
"""

import os
import json
import time
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import sqlite3
import logging

# Import our analyzers
from .clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning
from .clinical_trial_analyzer_llm import ClinicalTrialAnalyzerLLM

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrialProcessor:
    """Process all clinical trials with multiple models and store results"""
    
    def __init__(self):
        """Initialize the trial processor"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        # Initialize analyzers
        self.analyzers = {
            "gpt-4o": ClinicalTrialAnalyzerReasoning(self.api_key, model="gpt-4o"),
            "gpt-4o-mini": ClinicalTrialAnalyzerReasoning(self.api_key, model="gpt-4o-mini"),
            "o3": ClinicalTrialAnalyzerReasoning(self.api_key, model="o3"),
            "gpt-4": ClinicalTrialAnalyzerReasoning(self.api_key, model="gpt-4"),
            "llm": ClinicalTrialAnalyzerLLM(self.api_key)
        }
        
        # Database connection
        from ..utils.paths import CLINICAL_TRIALS_DB, RESULTS_DB
        self.db_path = str(CLINICAL_TRIALS_DB)
        self.results_db_path = str(RESULTS_DB)
        self._init_results_database()
    
    def _init_results_database(self):
        """Initialize database for storing analysis results"""
        conn = sqlite3.connect(self.results_db_path)
        cursor = conn.cursor()
        
        # Create results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trial_analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nct_id TEXT NOT NULL,
                model_name TEXT NOT NULL,
                analysis_timestamp TEXT NOT NULL,
                analysis_time REAL NOT NULL,
                quality_score REAL,
                total_fields INTEGER,
                valid_fields INTEGER,
                error_fields INTEGER,
                na_fields INTEGER,
                result_data TEXT NOT NULL,
                UNIQUE(nct_id, model_name)
            )
        ''')
        
        # Create comparison summary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_comparison_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nct_id TEXT NOT NULL,
                comparison_timestamp TEXT NOT NULL,
                models_compared TEXT NOT NULL,
                best_model TEXT,
                best_quality_score REAL,
                average_quality_score REAL,
                total_analysis_time REAL,
                summary_data TEXT NOT NULL
            )
        ''')
        
        # Create trial metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trial_metadata (
                nct_id TEXT PRIMARY KEY,
                trial_name TEXT,
                trial_phase TEXT,
                trial_status TEXT,
                primary_drug TEXT,
                indication TEXT,
                sponsor TEXT,
                patient_enrollment TEXT,
                last_updated TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Initialized results database: {self.results_db_path}")
    
    def get_all_trials(self):
        """Get all NCT IDs from the main database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT nct_id FROM clinical_trials")
        trials = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return trials
    
    def analyze_trial_with_model(self, nct_id: str, model_name: str) -> dict:
        """Analyze a single trial with a specific model"""
        try:
            logger.info(f"Analyzing {nct_id} with {model_name}")
            
            start_time = time.time()
            analyzer = self.analyzers[model_name]
            
            # Analyze the trial - use web search for o3 model
            use_web_search = model_name == "o3"
            result = analyzer.analyze_trial(nct_id, None, use_web_search=use_web_search)
            end_time = time.time()
            
            analysis_time = end_time - start_time
            
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"],
                    "model": model_name,
                    "analysis_time": analysis_time
                }
            
            # Calculate quality metrics
            total_fields = len(result)
            valid_fields = sum(1 for v in result.values() if v and v != "NA" and v != "Error in analysis")
            error_fields = sum(1 for v in result.values() if v == "Error in analysis")
            na_fields = sum(1 for v in result.values() if v == "NA")
            quality_score = (valid_fields / total_fields * 100) if total_fields > 0 else 0
            
            return {
                "success": True,
                "result": result,
                "model": model_name,
                "analysis_time": analysis_time,
                "quality_score": quality_score,
                "total_fields": total_fields,
                "valid_fields": valid_fields,
                "error_fields": error_fields,
                "na_fields": na_fields
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {nct_id} with {model_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "model": model_name,
                "analysis_time": 0
            }
    
    def store_analysis_result(self, nct_id: str, analysis_result: dict):
        """Store analysis result in the database"""
        if not analysis_result["success"]:
            return False
        
        conn = sqlite3.connect(self.results_db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO trial_analysis_results 
                (nct_id, model_name, analysis_timestamp, analysis_time, quality_score, 
                 total_fields, valid_fields, error_fields, na_fields, result_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                nct_id,
                analysis_result["model"],
                datetime.now().isoformat(),
                analysis_result["analysis_time"],
                analysis_result["quality_score"],
                analysis_result["total_fields"],
                analysis_result["valid_fields"],
                analysis_result["error_fields"],
                analysis_result["na_fields"],
                json.dumps(analysis_result["result"])
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing result for {nct_id}: {e}")
            return False
        finally:
            conn.close()
    
    def store_comparison_summary(self, nct_id: str, comparison_results: list):
        """Store model comparison summary"""
        successful_results = [r for r in comparison_results if r["success"]]
        
        if not successful_results:
            return False
        
        # Find best model
        best_result = max(successful_results, key=lambda x: x["quality_score"])
        average_quality = sum(r["quality_score"] for r in successful_results) / len(successful_results)
        total_time = sum(r["analysis_time"] for r in successful_results)
        
        # Create summary data
        summary_data = {
            "models_compared": [r["model"] for r in comparison_results],
            "successful_models": [r["model"] for r in successful_results],
            "quality_scores": {r["model"]: r["quality_score"] for r in successful_results},
            "analysis_times": {r["model"]: r["analysis_time"] for r in successful_results},
            "field_counts": {r["model"]: {
                "total": r["total_fields"],
                "valid": r["valid_fields"],
                "error": r["error_fields"],
                "na": r["na_fields"]
            } for r in successful_results}
        }
        
        conn = sqlite3.connect(self.results_db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO model_comparison_summary 
                (nct_id, comparison_timestamp, models_compared, best_model, best_quality_score,
                 average_quality_score, total_analysis_time, summary_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                nct_id,
                datetime.now().isoformat(),
                json.dumps([r["model"] for r in comparison_results]),
                best_result["model"],
                best_result["quality_score"],
                average_quality,
                total_time,
                json.dumps(summary_data)
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing comparison summary for {nct_id}: {e}")
            return False
        finally:
            conn.close()
    
    def store_trial_metadata(self, nct_id: str, result_data: dict):
        """Store trial metadata for quick access"""
        conn = sqlite3.connect(self.results_db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO trial_metadata 
                (nct_id, trial_name, trial_phase, trial_status, primary_drug, 
                 indication, sponsor, patient_enrollment, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                nct_id,
                result_data.get("Trial Name", "N/A"),
                result_data.get("Trial Phase", "N/A"),
                result_data.get("Trial Status", "N/A"),
                result_data.get("Primary Drug", "N/A"),
                result_data.get("Indication", "N/A"),
                result_data.get("Sponsor", "N/A"),
                result_data.get("Patient Enrollment/Accrual", "N/A"),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing metadata for {nct_id}: {e}")
            return False
        finally:
            conn.close()
    
    def process_all_trials(self, model_to_use="gpt-4o-mini"):
        """Process all trials with single model analysis"""
        trials = self.get_all_trials()
        logger.info(f"Found {len(trials)} trials to process with {model_to_use}")
        
        total_processed = 0
        total_successful = 0
        
        for i, nct_id in enumerate(trials, 1):
            logger.info(f"[{i}/{len(trials)}] Processing {nct_id}")
            
            # Analyze with single model
            result = self.analyze_trial_with_model(nct_id, model_to_use)
            
            if result["success"]:
                # Store individual result
                self.store_analysis_result(nct_id, result)
                
                # Store metadata
                self.store_trial_metadata(nct_id, result["result"])
                
                total_successful += 1
                logger.info(f"✅ {nct_id}: Analysis successful (Quality: {result['quality_score']:.1f}%)")
            else:
                logger.warning(f"❌ {nct_id}: Analysis failed - {result['error']}")
            
            total_processed += 1
            
            # Progress update every 5 trials
            if i % 5 == 0:
                logger.info(f"Progress: {i}/{len(trials)} trials processed")
            
            # Rate limiting
            time.sleep(1)
        
        logger.info(f"🎉 Processing complete!")
        logger.info(f"Total trials processed: {total_processed}")
        logger.info(f"Total successful analyses: {total_successful}")
        
        return {
            "total_trials": len(trials),
            "processed_trials": total_processed,
            "total_successful": total_successful,
            "model_used": model_to_use
        }
    
    def get_analysis_results(self, nct_id: str = None):
        """Get analysis results from database"""
        conn = sqlite3.connect(self.results_db_path)
        
        if nct_id:
            # Get specific trial results
            df_results = pd.read_sql_query('''
                SELECT * FROM trial_analysis_results 
                WHERE nct_id = ? 
                ORDER BY analysis_timestamp DESC
            ''', conn, params=[nct_id])
            
            df_summary = pd.read_sql_query('''
                SELECT * FROM model_comparison_summary 
                WHERE nct_id = ? 
                ORDER BY comparison_timestamp DESC
            ''', conn, params=[nct_id])
            
            df_metadata = pd.read_sql_query('''
                SELECT * FROM trial_metadata 
                WHERE nct_id = ?
            ''', conn, params=[nct_id])
        else:
            # Get all results
            df_results = pd.read_sql_query('''
                SELECT * FROM trial_analysis_results 
                ORDER BY analysis_timestamp DESC
            ''', conn)
            
            df_summary = pd.read_sql_query('''
                SELECT * FROM model_comparison_summary 
                ORDER BY comparison_timestamp DESC
            ''', conn)
            
            df_metadata = pd.read_sql_query('''
                SELECT * FROM trial_metadata 
                ORDER BY last_updated DESC
            ''', conn)
        
        conn.close()
        
        return {
            "results": df_results,
            "summaries": df_summary,
            "metadata": df_metadata
        }

def main():
    """Main function to process all trials"""
    print("🏥 Clinical Trial Analysis Processor")
    print("=" * 50)
    
    try:
        processor = TrialProcessor()
        
        # Get user input for model
        print("Available models:")
        for i, model in enumerate(processor.analyzers.keys(), 1):
            print(f"{i}. {model}")
        
        print("\nSelect model to use for analysis:")
        user_input = input("Model (or press Enter for gpt-4o-mini): ").strip()
        
        if not user_input:
            model_to_use = "gpt-4o-mini"
        else:
            model_index = int(user_input) - 1
            model_to_use = list(processor.analyzers.keys())[model_index]
        
        print(f"\nSelected model: {model_to_use}")
        
        # Process all trials
        results = processor.process_all_trials(model_to_use)
        
        print("\n" + "=" * 50)
        print("📊 Processing Summary:")
        print(f"Total trials: {results['total_trials']}")
        print(f"Processed trials: {results['processed_trials']}")
        print(f"Successful analyses: {results['total_successful']}")
        print(f"Model used: {results['model_used']}")
        
        # Show some statistics
        all_results = processor.get_analysis_results()
        
        if not all_results["results"].empty:
            print(f"\n📈 Database Statistics:")
            print(f"Total analysis results: {len(all_results['results'])}")
            print(f"Unique trials analyzed: {all_results['results']['nct_id'].nunique()}")
            print(f"Average quality score: {all_results['results']['quality_score'].mean():.1f}%")
            print(f"Average analysis time: {all_results['results']['analysis_time'].mean():.1f}s")
        
        print("\n🎉 All trials processed and stored in database!")
        print("Results are now available in the UI under 'Results History' tab.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Processing failed: {e}")

if __name__ == "__main__":
    main() 