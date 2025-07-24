import json
import requests
import pandas as pd
from typing import List, Dict, Any, Optional
import openai
from datetime import datetime
import re
import logging
import os
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseAnalyzer:
    """
    Base Clinical Trial Analysis System
    Contains common methods for all analyzer types
    """
    
    def __init__(self, openai_api_key: str):
        """Initialize the base analyzer with OpenAI API key"""
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"
        
        # Import paths using dynamic path resolution
        import sys
        utils_path = os.path.join(os.path.dirname(__file__), '..', 'utils')
        if utils_path not in sys.path:
            sys.path.append(utils_path)
        try:
            from paths import CACHE_DIR
            self.cache_dir = CACHE_DIR
        except ImportError:
            self.cache_dir = Path("cache")
        
        self.cache_dir.mkdir(exist_ok=True)
    
    def fetch_trial_data(self, nct_id: str) -> Optional[Dict[str, Any]]:
        """Fetch clinical trial data from ClinicalTrials.gov API"""
        cache_file = self.cache_dir / f"{nct_id}.json"
        
        # Check cache first
        if cache_file.exists():
            logger.info(f"Loading {nct_id} from cache")
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load from cache: {e}")
        
        # Fetch from API
        try:
            logger.info(f"Fetching {nct_id} from API")
            url = f"{self.base_url}/{nct_id}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching data for {nct_id}: {e}")
            return None
    
    def load_trial_data_from_file(self, json_file_path: str) -> Optional[Dict[str, Any]]:
        """Load clinical trial data from local JSON file"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading JSON file {json_file_path}: {e}")
            return None
    
    def extract_basic_fields(self, trial_data: Dict[str, Any], nct_id: str = None) -> Dict[str, Any]:
        """Extract basic fields using rule-based approach"""
        protocol = trial_data.get("protocolSection", {})
        
        # Basic identification
        identification = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        sponsor = protocol.get("sponsorCollaboratorsModule", {})
        design = protocol.get("designModule", {})
        outcomes = protocol.get("outcomesModule", {})
        eligibility = protocol.get("eligibilityModule", {})
        contacts = protocol.get("contactsLocationsModule", {})
        
        # Robust NCT ID extraction
        nct_id_extracted = (
            identification.get("nctId") or
            trial_data.get("nct_id") or
            trial_data.get("NCT ID") or
            trial_data.get("NCTId") or
            trial_data.get("nctId") or
            nct_id
        )
        
        basic_fields = {
            "NCT ID": nct_id_extracted,
            "Trial ID": nct_id_extracted,
            "Trial Phase": self._extract_phase(design.get("phases", [])),
            "Trial Status": status.get("overallStatus"),
            "Patient Enrollment/Accrual": design.get("enrollmentInfo", {}).get("count"),
            "Sponsor": sponsor.get("leadSponsor", {}).get("name"),
            "Start Date (YY-MM-DD)": self._format_date(status.get("startDateStruct", {}).get("date")),
            "Primary Completion Date (YY-MM-DD)": self._format_date(status.get("primaryCompletionDateStruct", {}).get("date")),
            "Study completion date (YY-MM-DD)": self._format_date(status.get("completionDateStruct", {}).get("date")),
            "Primary Endpoints": self._extract_endpoints(outcomes.get("primaryOutcomes", [])),
            "Secondary Endpoints": self._extract_endpoints(outcomes.get("secondaryOutcomes", [])),
            "Inclusion Criteria": self._extract_inclusion_criteria(eligibility.get("eligibilityCriteria", "")),
            "Exclusion Criteria": self._extract_exclusion_criteria(eligibility.get("eligibilityCriteria", "")),
            "Trial Countries": self._extract_countries(contacts),
            "Geography": self._classify_geography(contacts),
            "Sponsor Type": self._classify_sponsor_type(sponsor),
            "Developer": self._extract_developer(sponsor),
            "Investigator Name": self._extract_investigator_info(contacts),
            "Investigator Designation": self._extract_investigator_designation(contacts),
            "Investigator Qualification": self._extract_investigator_qualification(contacts),
            "Investigator Location": self._extract_investigator_location(contacts),
        }
        
        return basic_fields
    
    def analyze_multiple_trials(self, nct_ids: List[str], json_file_paths: Optional[List[str]] = None) -> pd.DataFrame:
        """Analyze multiple clinical trials and return as DataFrame"""
        results = []
        
        # Ensure json_file_paths is the same length as nct_ids or None
        if json_file_paths and len(json_file_paths) != len(nct_ids):
            logger.warning(f"json_file_paths length ({len(json_file_paths)}) doesn't match nct_ids length ({len(nct_ids)})")
            json_file_paths = None
        
        for i, nct_id in enumerate(nct_ids):
            logger.info(f"Analyzing trial {i+1}/{len(nct_ids)}: {nct_id}")
            
            try:
                # Get file path if available
                json_file_path = json_file_paths[i] if json_file_paths else None
                
                # Analyze trial
                result = self.analyze_trial(nct_id, json_file_path)
                
                if "error" not in result:
                    results.append(result)
                else:
                    logger.error(f"Error analyzing {nct_id}: {result['error']}")
            except Exception as e:
                logger.error(f"Exception analyzing {nct_id}: {e}")
            
            # Add delay to avoid overwhelming the API
            if not json_file_paths and i < len(nct_ids) - 1:
                time.sleep(1)
        
        if results:
            df = pd.DataFrame(results)
            return df
        else:
            return pd.DataFrame()
    
    # Helper methods for rule-based extraction
    def _extract_phase(self, phases: List[str]) -> str:
        """Extract trial phase"""
        if not phases:
            return "NA"
        return ", ".join(phases)
    
    def _format_date(self, date_str: str) -> str:
        """Format date to YY-MM-DD"""
        if not date_str:
            return "NA"
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%y-%m-%d")
        except:
            return date_str
    
    def _extract_endpoints(self, outcomes: List[Dict]) -> str:
        """Extract endpoint descriptions"""
        if not outcomes:
            return "NA"
        return "; ".join([f"{outcome.get('measure', '')} ({outcome.get('timeFrame', '')})" for outcome in outcomes])
    
    def _extract_inclusion_criteria(self, criteria: str) -> str:
        """Extract inclusion criteria"""
        if not criteria:
            return "NA"
        if "Exclusion Criteria:" in criteria:
            return criteria.split("Exclusion Criteria:")[0].strip()
        return criteria.strip()
    
    def _extract_exclusion_criteria(self, criteria: str) -> str:
        """Extract exclusion criteria"""
        if not criteria or "Exclusion Criteria:" not in criteria:
            return "NA"
        return criteria.split("Exclusion Criteria:")[1].strip()
    
    def _extract_countries(self, contacts: Dict) -> str:
        """Extract trial countries"""
        return "NA"
    
    def _classify_geography(self, contacts: Dict) -> str:
        """Classify trial geography"""
        return "NA"
    
    def _classify_sponsor_type(self, sponsor: Dict) -> str:
        """Classify sponsor type"""
        lead_sponsor = sponsor.get("leadSponsor", {})
        sponsor_class = lead_sponsor.get("class", "")
        
        if sponsor_class == "INDUSTRY":
            return "Industry Only"
        elif sponsor_class == "OTHER":
            return "Academic Only"
        else:
            return "Industry-Academic Collaboration"
    
    def _extract_developer(self, sponsor: Dict) -> str:
        """Extract drug developer"""
        lead_sponsor = sponsor.get("leadSponsor", {})
        return lead_sponsor.get("name", "NA")
    
    def _extract_investigator_info(self, contacts: Dict) -> str:
        """Extract investigator information"""
        central_contacts = contacts.get("centralContacts", [])
        if central_contacts:
            return central_contacts[0].get("name", "NA")
        return "NA"
    
    def _extract_investigator_designation(self, contacts: Dict) -> str:
        """Extract investigator designation"""
        central_contacts = contacts.get("centralContacts", [])
        if central_contacts:
            return central_contacts[0].get("role", "NA")
        return "NA"
    
    def _extract_investigator_qualification(self, contacts: Dict) -> str:
        """Extract investigator qualification"""
        return "NA"
    
    def _extract_investigator_location(self, contacts: Dict) -> str:
        """Extract investigator location"""
        return "NA" 