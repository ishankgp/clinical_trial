#!/usr/bin/env python3
"""
Clinical Trial Supabase Database Module
Stores processed clinical trial data in Supabase for MCP server access
"""

import json
import pandas as pd
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging
from pathlib import Path
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalTrialDatabaseSupabase:
    """
    Supabase database interface for storing and querying processed clinical trial data
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Initialize Supabase connection
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and API key must be provided or set as environment variables")
            
        # Initialize Supabase client
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test Supabase connection"""
        try:
            # Test connection with a simple query
            response = self.client.table('clinical_trials').select('count').limit(1).execute()
            logger.info("✅ Connected to Supabase successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            raise
    
    def store_trial_data(self, trial_data: Dict[str, Any]) -> bool:
        """
        Store clinical trial data in Supabase
        
        Args:
            trial_data: Dictionary containing trial information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare trial data
            trial_record = {
                'nct_id': trial_data.get('nct_id'),
                'trial_name': trial_data.get('trial_name'),
                'trial_phase': trial_data.get('trial_phase'),
                'trial_status': trial_data.get('trial_status'),
                'patient_enrollment': trial_data.get('patient_enrollment'),
                'sponsor': trial_data.get('sponsor'),
                'primary_endpoints': trial_data.get('primary_endpoints'),
                'secondary_endpoints': trial_data.get('secondary_endpoints'),
                'inclusion_criteria': trial_data.get('inclusion_criteria'),
                'exclusion_criteria': trial_data.get('exclusion_criteria'),
                'created_at': datetime.now().isoformat()
            }
            
            # Insert trial data
            response = self.client.table('clinical_trials').insert(trial_record).execute()
            
            if response.data:
                trial_id = response.data[0]['id']
                logger.info(f"✅ Stored trial {trial_data.get('nct_id')} with ID: {trial_id}")
                
                # Store drug information if available
                if 'drug_info' in trial_data and trial_data['drug_info']:
                    drug_record = {
                        'trial_id': trial_id,
                        'primary_drug': trial_data['drug_info'].get('primary_drug'),
                        'drug_class': trial_data['drug_info'].get('drug_class'),
                        'mechanism_of_action': trial_data['drug_info'].get('mechanism_of_action'),
                        'dosage_form': trial_data['drug_info'].get('dosage_form'),
                        'dosage_schedule': trial_data['drug_info'].get('dosage_schedule'),
                        'created_at': datetime.now().isoformat()
                    }
                    
                    self.client.table('drug_info').insert(drug_record).execute()
                    logger.info(f"✅ Stored drug info for trial {trial_id}")
                
                # Store clinical information if available
                if 'clinical_info' in trial_data and trial_data['clinical_info']:
                    clinical_record = {
                        'trial_id': trial_id,
                        'indication': trial_data['clinical_info'].get('indication'),
                        'disease_area': trial_data['clinical_info'].get('disease_area'),
                        'patient_population': trial_data['clinical_info'].get('patient_population'),
                        'age_range': trial_data['clinical_info'].get('age_range'),
                        'gender_eligibility': trial_data['clinical_info'].get('gender_eligibility'),
                        'created_at': datetime.now().isoformat()
                    }
                    
                    self.client.table('clinical_info').insert(clinical_record).execute()
                    logger.info(f"✅ Stored clinical info for trial {trial_id}")
                
                return True
            else:
                logger.error("❌ Failed to store trial data")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error storing trial data: {e}")
            return False
    
    def search_trials(self, query: str, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search clinical trials using natural language query
        
        Args:
            query: Natural language search query
            filters: Additional filters to apply
            limit: Maximum number of results
            
        Returns:
            List of trial dictionaries
        """
        try:
            # Start with base query
            base_query = self.client.table('clinical_trials').select('*')
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if value:
                        # Handle special cases for different tables
                        if key == 'indication':
                            # Search in clinical_info table
                            clinical_response = self.client.table('clinical_info').select('nct_id').ilike('indication', f'%{value}%').execute()
                            if clinical_response.data:
                                nct_ids = [item['nct_id'] for item in clinical_response.data]
                                base_query = base_query.in_('nct_id', nct_ids)
                        elif key == 'primary_drug':
                            # Search in drug_info table
                            drug_response = self.client.table('drug_info').select('nct_id').ilike('primary_drug', f'%{value}%').execute()
                            if drug_response.data:
                                nct_ids = [item['nct_id'] for item in drug_response.data]
                                base_query = base_query.in_('nct_id', nct_ids)
                        else:
                            # Direct filter on clinical_trials table
                            base_query = base_query.eq(key, value)
            
            # Apply limit
            base_query = base_query.limit(limit)
            
            # Execute query
            response = base_query.execute()
            
            if response.data:
                logger.info(f"✅ Found {len(response.data)} trials matching query")
                return response.data
            else:
                logger.info("No trials found matching query")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error searching trials: {e}")
            return []
    
    def get_trial_by_nct_id(self, nct_id: str) -> Optional[Dict[str, Any]]:
        """
        Get trial by NCT ID
        
        Args:
            nct_id: Clinical trial NCT ID
            
        Returns:
            Trial dictionary or None if not found
        """
        try:
            response = self.client.table('clinical_trials').select('*').eq('nct_id', nct_id).execute()
            
            if response.data:
                logger.info(f"✅ Found trial with NCT ID: {nct_id}")
                return response.data[0]
            else:
                logger.info(f"No trial found with NCT ID: {nct_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting trial by NCT ID: {e}")
            return None
    
    def get_trials_by_phase(self, phase: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get trials by phase
        
        Args:
            phase: Trial phase (e.g., 'Phase 1', 'Phase 2', 'Phase 3', 'Phase 4')
            limit: Maximum number of results
            
        Returns:
            List of trial dictionaries
        """
        try:
            response = self.client.table('clinical_trials').select('*').eq('trial_phase', phase).limit(limit).execute()
            
            if response.data:
                logger.info(f"✅ Found {len(response.data)} {phase} trials")
                return response.data
            else:
                logger.info(f"No {phase} trials found")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting trials by phase: {e}")
            return []
    
    def get_trials_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get trials by status
        
        Args:
            status: Trial status (e.g., 'Recruiting', 'Completed', 'Terminated')
            limit: Maximum number of results
            
        Returns:
            List of trial dictionaries
        """
        try:
            response = self.client.table('clinical_trials').select('*').eq('trial_status', status).limit(limit).execute()
            
            if response.data:
                logger.info(f"✅ Found {len(response.data)} {status} trials")
                return response.data
            else:
                logger.info(f"No {status} trials found")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting trials by status: {e}")
            return []
    
    def get_trials_by_drug(self, drug_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get trials by drug name
        
        Args:
            drug_name: Name of the drug
            limit: Maximum number of results
            
        Returns:
            List of trial dictionaries
        """
        try:
            # Query drug_info table first, then get trials
            drug_response = self.client.table('drug_info').select('nct_id').ilike('primary_drug', f'%{drug_name}%').limit(limit).execute()
            
            if drug_response.data:
                nct_ids = [item['nct_id'] for item in drug_response.data]
                response = self.client.table('clinical_trials').select('*').in_('nct_id', nct_ids).execute()
            else:
                response = type('obj', (object,), {'data': []})()
            
            if response.data:
                logger.info(f"✅ Found {len(response.data)} trials for drug: {drug_name}")
                return response.data
            else:
                logger.info(f"No trials found for drug: {drug_name}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting trials by drug: {e}")
            return []
    
    def get_trials_by_indication(self, indication: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get trials by indication/disease
        
        Args:
            indication: Disease or indication
            limit: Maximum number of results
            
        Returns:
            List of trial dictionaries
        """
        try:
            # Query clinical_info table first, then get trials
            clinical_response = self.client.table('clinical_info').select('nct_id').ilike('indication', f'%{indication}%').limit(limit).execute()
            
            if clinical_response.data:
                nct_ids = [item['nct_id'] for item in clinical_response.data]
                response = self.client.table('clinical_trials').select('*').in_('nct_id', nct_ids).execute()
            else:
                response = type('obj', (object,), {'data': []})()
            
            if response.data:
                logger.info(f"✅ Found {len(response.data)} trials for indication: {indication}")
                return response.data
            else:
                logger.info(f"No trials found for indication: {indication}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting trials by indication: {e}")
            return []
    
    def get_trial_statistics(self) -> Dict[str, Any]:
        """
        Get trial statistics
        
        Returns:
            Dictionary with trial statistics
        """
        try:
            # Get total count
            total_response = self.client.table('clinical_trials').select('count').execute()
            total_trials = total_response.count if hasattr(total_response, 'count') else 0
            
            # Get phase distribution
            phase_response = self.client.table('clinical_trials').select('trial_phase').execute()
            phase_counts = {}
            if phase_response.data:
                for trial in phase_response.data:
                    phase = trial.get('trial_phase', 'Unknown')
                    phase_counts[phase] = phase_counts.get(phase, 0) + 1
            
            # Get status distribution
            status_response = self.client.table('clinical_trials').select('trial_status').execute()
            status_counts = {}
            if status_response.data:
                for trial in status_response.data:
                    status = trial.get('trial_status', 'Unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
            
            stats = {
                'total_trials': total_trials,
                'phase_distribution': phase_counts,
                'status_distribution': status_counts
            }
            
            logger.info(f"✅ Retrieved trial statistics: {total_trials} total trials")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting trial statistics: {e}")
            return {}
    
    def update_trial(self, nct_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update trial information
        
        Args:
            nct_id: Clinical trial NCT ID
            updates: Dictionary with fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add updated timestamp
            updates['updated_at'] = datetime.now().isoformat()
            
            response = self.client.table('clinical_trials').update(updates).eq('nct_id', nct_id).execute()
            
            if response.data:
                logger.info(f"✅ Updated trial {nct_id}")
                return True
            else:
                logger.error(f"❌ Failed to update trial {nct_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating trial: {e}")
            return False
    
    def delete_trial(self, nct_id: str) -> bool:
        """
        Delete trial by NCT ID
        
        Args:
            nct_id: Clinical trial NCT ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = self.client.table('clinical_trials').delete().eq('nct_id', nct_id).execute()
            
            if response.data:
                logger.info(f"✅ Deleted trial {nct_id}")
                return True
            else:
                logger.error(f"❌ Failed to delete trial {nct_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting trial: {e}")
            return False
    
    def export_to_csv(self, filepath: str, filters: Dict[str, Any] = None) -> bool:
        """
        Export trials to CSV file
        
        Args:
            filepath: Path to save CSV file
            filters: Optional filters to apply
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get all trials
            trials = self.search_trials("", filters, limit=10000)
            
            if trials:
                # Convert to DataFrame
                df = pd.DataFrame(trials)
                
                # Save to CSV
                df.to_csv(filepath, index=False)
                logger.info(f"✅ Exported {len(trials)} trials to {filepath}")
                return True
            else:
                logger.info("No trials to export")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error exporting to CSV: {e}")
            return False

def main():
    """Test the Supabase database functionality"""
    # Check if Supabase credentials are provided
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("SUPABASE_URL and SUPABASE_KEY environment variables not set.")
        print("Please set them to test Supabase functionality.")
        return
        
    try:
        # Initialize database
        db = ClinicalTrialDatabaseSupabase(supabase_url, supabase_key)
        
        # Test data
        test_trial = {
            'nct_id': 'NCT12345678',
            'trial_name': 'Test Clinical Trial',
            'trial_phase': 'Phase 2',
            'trial_status': 'Recruiting',
            'patient_enrollment': 100,
            'sponsor': 'Test Sponsor',
            'primary_endpoints': 'Safety and efficacy',
            'secondary_endpoints': 'Quality of life',
            'inclusion_criteria': 'Age 18-65',
            'exclusion_criteria': 'Pregnancy',
            'drug_info': {
                'primary_drug': 'Test Drug',
                'drug_class': 'Small molecule',
                'mechanism_of_action': 'Inhibitor',
                'dosage_form': 'Oral',
                'dosage_schedule': 'Once daily'
            },
            'clinical_info': {
                'indication': 'Diabetes',
                'disease_area': 'Endocrinology',
                'patient_population': 'Adults',
                'age_range': '18-65',
                'gender_eligibility': 'All'
            }
        }
        
        # Test storing trial
        success = db.store_trial_data(test_trial)
        if success:
            print("✅ Test trial stored successfully")
        
        # Test searching trials
        trials = db.search_trials("diabetes", limit=5)
        print(f"✅ Found {len(trials)} trials matching 'diabetes'")
        
        # Test getting statistics
        stats = db.get_trial_statistics()
        print(f"✅ Trial statistics: {stats}")
        
    except Exception as e:
        print(f"❌ Error testing Supabase database: {e}")

if __name__ == "__main__":
    main() 