#!/usr/bin/env python3
"""
Populate Clinical Trials Database
Downloads and stores clinical trials from ClinicalTrials.gov API
"""

import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
# Import database using dynamic path resolution
import sys
database_path = os.path.dirname(__file__)
if database_path not in sys.path:
    sys.path.append(database_path)
from clinical_trial_database import ClinicalTrialDatabase

# Import analyzer using dynamic path resolution
analysis_path = os.path.join(os.path.dirname(__file__), '..', 'analysis')
if analysis_path not in sys.path:
    sys.path.append(analysis_path)
from clinical_trial_analyzer_reasoning import ClinicalTrialAnalyzerReasoning

# Load environment variables
load_dotenv()

# Clinical trials to download
CLINICAL_TRIALS = [
    {"nct_id": "NCT03778931", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03778931"},
    {"nct_id": "NCT04516746", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT04516746"},
    {"nct_id": "NCT03127514", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03127514"},
    {"nct_id": "NCT05269394", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT05269394"},
    {"nct_id": "NCT02119819", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT02119819"},
    {"nct_id": "NCT02122952", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT02122952"},
    {"nct_id": "NCT03057951", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03057951"},
    {"nct_id": "NCT05104866", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT05104866"},
    {"nct_id": "NCT03369444", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03369444"},
    {"nct_id": "NCT03887455", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03887455"},
    {"nct_id": "NCT04657003", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT04657003"},
    {"nct_id": "NCT03036124", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03036124"},
    {"nct_id": "NCT03434769", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03434769"},
    {"nct_id": "NCT03775200", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03775200"},
    {"nct_id": "NCT03728322", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03728322"},
    {"nct_id": "NCT00282152", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT00282152"},
    {"nct_id": "NCT03934372", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03934372"},
    {"nct_id": "NCT04334928", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT04334928"},
    {"nct_id": "NCT04028349", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT04028349"},
    {"nct_id": "NCT03896724", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03896724"},
    {"nct_id": "NCT03912207", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03912207"},
    {"nct_id": "NCT04828382", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT04828382"},
    {"nct_id": "NCT03693430", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03693430"},
    {"nct_id": "NCT03308968", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03308968"},
    {"nct_id": "NCT05001373", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT05001373"},
    {"nct_id": "NCT03745287", "json_url": "https://clinicaltrials.gov/api/v2/studies/NCT03745287"},
]

def download_trial_data(nct_id: str, json_url: str) -> dict:
    """Download trial data from ClinicalTrials.gov API"""
    try:
        print(f"📥 Downloading {nct_id}...")
        response = requests.get(json_url, timeout=30)
        response.raise_for_status()
        
        # Save raw JSON
        cache_dir = Path("cache")
        cache_dir.mkdir(exist_ok=True)
        
        json_file = cache_dir / f"{nct_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, indent=2)
        
        print(f"✅ Downloaded {nct_id} to {json_file}")
        return response.json()
        
    except Exception as e:
        print(f"❌ Error downloading {nct_id}: {e}")
        return None

def analyze_and_store_trial(nct_id: str, trial_data: dict, analyzer, db) -> bool:
    """Analyze and store trial in database"""
    try:
        print(f"🔍 Analyzing {nct_id}...")
        
        # Analyze the trial
        result = analyzer.analyze_trial(nct_id, None)
        
        if "error" in result:
            print(f"❌ Analysis error for {nct_id}: {result['error']}")
            return False
        
        # Store in database
        success = db.store_trial_data(result, {
            "analysis_model": "gpt-4o-mini",
            "analysis_timestamp": datetime.now().isoformat(),
            "source_url": f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
        })
        
        if success:
            print(f"✅ Stored {nct_id} in database")
            return True
        else:
            print(f"❌ Failed to store {nct_id} in database")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {nct_id}: {e}")
        return False

def main():
    """Main function to populate database"""
    print("🏥 Clinical Trials Database Population")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file!")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your-api-key-here")
        return
    
    # Initialize components
    db = ClinicalTrialDatabase()
    analyzer = ClinicalTrialAnalyzerReasoning(api_key, model="gpt-4o-mini")
    
    print(f"📊 Processing {len(CLINICAL_TRIALS)} clinical trials...")
    print()
    
    successful_downloads = 0
    successful_stores = 0
    
    for i, trial in enumerate(CLINICAL_TRIALS, 1):
        nct_id = trial["nct_id"]
        json_url = trial["json_url"]
        
        print(f"[{i}/{len(CLINICAL_TRIALS)}] Processing {nct_id}")
        
        # Check if already exists
        existing_trial = db.get_trial_by_nct_id(nct_id)
        if existing_trial:
            print(f"⏭️  {nct_id} already exists in database, skipping...")
            continue
        
        # Download trial data
        trial_data = download_trial_data(nct_id, json_url)
        if trial_data:
            successful_downloads += 1
            
            # Analyze and store
            if analyze_and_store_trial(nct_id, trial_data, analyzer, db):
                successful_stores += 1
            
            # Rate limiting
            time.sleep(1)
        
        print()
    
    # Summary
    print("=" * 50)
    print("📊 Population Summary:")
    print(f"Total trials: {len(CLINICAL_TRIALS)}")
    print(f"Successful downloads: {successful_downloads}")
    print(f"Successful stores: {successful_stores}")
    print(f"Skipped (already exists): {len(CLINICAL_TRIALS) - successful_downloads}")
    
    # Get database stats
    all_trials = db.search_trials({}, 1000)
    print(f"Total trials in database: {len(all_trials)}")
    
    if all_trials:
        # Show some statistics
        phases = {}
        statuses = {}
        drugs = {}
        
        for trial in all_trials:
            phase = trial.get("trial_phase", "Unknown")
            status = trial.get("trial_status", "Unknown")
            drug = trial.get("primary_drug", "Unknown")
            
            phases[phase] = phases.get(phase, 0) + 1
            statuses[status] = statuses.get(status, 0) + 1
            if drug != "Unknown":
                drugs[drug] = drugs.get(drug, 0) + 1
        
        print("\n📈 Database Statistics:")
        print("By Phase:")
        for phase, count in phases.items():
            print(f"  {phase}: {count}")
        
        print("\nBy Status:")
        for status, count in statuses.items():
            print(f"  {status}: {count}")
        
        print("\nTop Drugs:")
        sorted_drugs = sorted(drugs.items(), key=lambda x: x[1], reverse=True)[:5]
        for drug, count in sorted_drugs:
            print(f"  {drug}: {count}")
    
    print("\n🎉 Database population completed!")

if __name__ == "__main__":
    main() 