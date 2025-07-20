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

class ClinicalTrialAnalyzerLLM:
    """
    Clinical Trial Analysis System using LLM for complex field extraction
    Based on the detailed specifications in GenAI_Case_Clinical_Trial_Analysis_PROMPT_ver1.00.docx.md
    """
    
    def __init__(self, openai_api_key: str):
        """Initialize the analyzer with OpenAI API key"""
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"
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
    
    def extract_basic_fields(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
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
        
        basic_fields = {
            "Trial ID": identification.get("nctId"),
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
    
    def analyze_drug_fields_llm(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze drug-related fields using LLM according to specifications"""
        
        protocol = trial_data.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        description = protocol.get("descriptionModule", {})
        conditions = protocol.get("conditionsModule", {})
        arms = protocol.get("armsInterventionsModule", {})
        
        prompt = f"""
        You are a clinical trial analyst. Analyze the following clinical trial information and extract drug-related fields according to the specified rules:

        BRIEF TITLE: {identification.get("briefTitle", "")}
        OFFICIAL TITLE: {identification.get("officialTitle", "")}
        BRIEF SUMMARY: {description.get("briefSummary", "")}
        CONDITIONS: {conditions.get("conditions", [])}
        ARM GROUPS: {json.dumps(arms.get("armGroups", []), indent=2)}
        INTERVENTIONS: {json.dumps(arms.get("interventions", []), indent=2)}

        EXTRACTION RULES:
        1. Primary Drug: Identify the primary investigational drug being tested (not active comparators)
        2. Primary Drug MoA: Use standardized format like "Anti-PD-1", "PARP inhibitor", "GLP-1 Receptor Agonist"
        3. Primary Drug Target: Molecular target (e.g., "PD-1", "PARP", "GLP-1 Receptor")
        4. Primary Drug Modality: Drug modality (e.g., "Monoclonal antibody", "Small molecule", "Peptide", "ADC")
        5. Primary Drug ROA: Route of administration (e.g., "Intravenous (IV)", "Oral", "Subcutaneous (SC)")
        6. Mono/Combo: Classify as "Mono" or "Combo" based on whether drug is evaluated alone or in combination
        7. Combination Partner: List combination partners (use "NA" for mono)
        8. MoA of Combination: Mechanism of combination partners (use "NA" for mono)
        9. Experimental Regimen: Primary drug + combination partners
        10. MoA of Experimental Regimen: Combined MoA

        Return a JSON object with these exact field names: "Primary Drug", "Primary Drug MoA", "Primary Drug Target", "Primary Drug Modality", "Primary Drug ROA", "Mono/Combo", "Combination Partner", "MoA of Combination", "Experimental Regimen", "MoA of Experimental Regimen"
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}  # Ensure valid JSON output
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Response content: {content}")
                raise ValueError(f"Invalid JSON response: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in drug analysis: {e}")
            return {
                "Primary Drug": "Error in analysis",
                "Primary Drug MoA": "Error in analysis",
                "Primary Drug Target": "Error in analysis",
                "Primary Drug Modality": "Error in analysis",
                "Primary Drug ROA": "Error in analysis",
                "Mono/Combo": "Error in analysis",
                "Combination Partner": "Error in analysis",
                "MoA of Combination": "Error in analysis",
                "Experimental Regimen": "Error in analysis",
                "MoA of Experimental Regimen": "Error in analysis"
            }
    
    def analyze_clinical_fields_llm(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze clinical fields using LLM according to specifications"""
        
        protocol = trial_data.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        description = protocol.get("descriptionModule", {})
        conditions = protocol.get("conditionsModule", {})
        eligibility = protocol.get("eligibilityModule", {})
        
        prompt = f"""
        You are a clinical trial analyst. Analyze the following clinical trial information and extract clinical fields:

        BRIEF TITLE: {identification.get("briefTitle", "")}
        OFFICIAL TITLE: {identification.get("officialTitle", "")}
        BRIEF SUMMARY: {description.get("briefSummary", "")}
        CONDITIONS: {conditions.get("conditions", [])}
        ELIGIBILITY CRITERIA: {eligibility.get("eligibilityCriteria", "")}

        EXTRACTION RULES:
        1. Indication: Primary disease indication (e.g., "Type 2 Diabetes (T2DM)", "Bladder Cancer")
        2. Line of Therapy: Classify as "1L", "2L", "2L+", "Adjuvant", "Neoadjuvant", "Maintenance" based on eligibility criteria
        3. Histology: Disease histology if specified (e.g., "Urothelial carcinoma", "Adenocarcinoma")
        4. Prior Treatment: Previous therapies required (e.g., "Metformin", "Platinum-based chemotherapy")
        5. Stage of Disease: Disease stage (e.g., "Stage 3/4", "Stage 4", "Not Applicable")
        6. Patient Population: Detailed patient population description
        7. Trial Name: Trial acronym from orgStudyIdInfo or title

        Return a JSON object with these exact field names: "Indication", "Line of Therapy", "Histology", "Prior Treatment", "Stage of Disease", "Patient Population", "Trial Name"
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800,
                response_format={"type": "json_object"}  # Ensure valid JSON output
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Response content: {content}")
                raise ValueError(f"Invalid JSON response: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in clinical analysis: {e}")
            return {
                "Indication": "Error in analysis",
                "Line of Therapy": "Error in analysis",
                "Histology": "Error in analysis",
                "Prior Treatment": "Error in analysis",
                "Stage of Disease": "Error in analysis",
                "Patient Population": "Error in analysis",
                "Trial Name": "Error in analysis"
            }
    
    def analyze_biomarker_fields_llm(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze biomarker fields using LLM according to specifications"""
        
        protocol = trial_data.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        description = protocol.get("descriptionModule", {})
        eligibility = protocol.get("eligibilityModule", {})
        outcomes = protocol.get("outcomesModule", {})
        
        prompt = f"""
        You are a clinical trial analyst. Analyze the following clinical trial information and extract biomarker fields:

        BRIEF TITLE: {identification.get("briefTitle", "")}
        OFFICIAL TITLE: {identification.get("officialTitle", "")}
        BRIEF SUMMARY: {description.get("briefSummary", "")}
        ELIGIBILITY CRITERIA: {eligibility.get("eligibilityCriteria", "")}
        PRIMARY OUTCOMES: {json.dumps(outcomes.get("primaryOutcomes", []), indent=2)}
        SECONDARY OUTCOMES: {json.dumps(outcomes.get("secondaryOutcomes", []), indent=2)}

        EXTRACTION RULES:
        1. Biomarker (Mutations): List specific mutations/biomarkers required (e.g., "HER2", "PD-L1", "FGFR")
        2. Biomarker Stratification: Expression levels/thresholds (e.g., "CPS ≥10", "IHC 2+", "IHC 3+")
        3. Biomarker (Wildtype): Wildtype biomarkers if specified (e.g., "KRAS wild-type", "TP53 wild-type")

        Return a JSON object with these exact field names: "Biomarker (Mutations)", "Biomarker Stratification", "Biomarker (Wildtype)". Use "Not Available" if not found.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=600,
                response_format={"type": "json_object"}  # Ensure valid JSON output
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Response content: {content}")
                raise ValueError(f"Invalid JSON response: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in biomarker analysis: {e}")
            return {
                "Biomarker (Mutations)": "Not Available",
                "Biomarker Stratification": "Not Available",
                "Biomarker (Wildtype)": "Not Available"
            }
    
    def analyze_trial(self, nct_id: str, json_file_path: Optional[str] = None) -> Dict[str, Any]:
        """Complete analysis of a single clinical trial"""
        logger.info(f"Analyzing trial: {nct_id}")
        
        # Load trial data
        if json_file_path:
            trial_data = self.load_trial_data_from_file(json_file_path)
        else:
            trial_data = self.fetch_trial_data(nct_id)
            
        if not trial_data:
            return {"error": f"Failed to load data for {nct_id}"}
        
        # Extract basic fields
        basic_fields = self.extract_basic_fields(trial_data)
        
        # Analyze with LLM
        drug_fields = self.analyze_drug_fields_llm(trial_data)
        clinical_fields = self.analyze_clinical_fields_llm(trial_data)
        biomarker_fields = self.analyze_biomarker_fields_llm(trial_data)
        
        # Combine all fields
        result = {**basic_fields, **drug_fields, **clinical_fields, **biomarker_fields}
        result["NCT ID"] = nct_id
        
        return result
    
    def analyze_multiple_trials(self, nct_ids: List[str], json_file_paths: Optional[List[str]] = None) -> pd.DataFrame:
        """Analyze multiple clinical trials and return as DataFrame"""
        results = []
        
        for i, nct_id in enumerate(nct_ids):
            try:
                json_file_path = json_file_paths[i] if json_file_paths and i < len(json_file_paths) else None
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
        # This would need to be implemented based on actual API response structure
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

def main():
    """Main function to test the LLM analyzer"""
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY not found in .env file!")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your-api-key-here")
        return
    
    analyzer = ClinicalTrialAnalyzerLLM(openai_api_key)
    
    # Test with the provided JSON file
    json_file_path = "NCT07046273.json"
    nct_id = "NCT07046273"
    
    if not os.path.exists(json_file_path):
        print(f"Error: {json_file_path} not found!")
        return
    
    print(f"Analyzing clinical trial: {nct_id}")
    print("Using LLM for complex field analysis...")
    
    result = analyzer.analyze_trial(nct_id, json_file_path)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    # Print results
    print("\n" + "="*80)
    print("CLINICAL TRIAL ANALYSIS RESULTS (LLM-Enhanced)")
    print("="*80)
    
    # Group results by category
    categories = {
        "Basic Information": [
            "NCT ID", "Trial ID", "Trial Name", "Trial Phase", "Trial Status", 
            "Patient Enrollment/Accrual", "Sponsor", "Sponsor Type", "Developer"
        ],
        "Dates": [
            "Start Date (YY-MM-DD)", "Primary Completion Date (YY-MM-DD)", 
            "Study completion date (YY-MM-DD)"
        ],
        "Drug Information": [
            "Primary Drug", "Primary Drug MoA", "Primary Drug Target", 
            "Primary Drug Modality", "Primary Drug ROA", "Mono/Combo", 
            "Combination Partner", "MoA of Combination", "Experimental Regimen", 
            "MoA of Experimental Regimen"
        ],
        "Clinical Information": [
            "Indication", "Line of Therapy", "Histology", "Prior Treatment", 
            "Stage of Disease", "Patient Population"
        ],
        "Endpoints": [
            "Primary Endpoints", "Secondary Endpoints"
        ],
        "Biomarkers": [
            "Biomarker (Mutations)", "Biomarker Stratification", "Biomarker (Wildtype)"
        ],
        "Geography & Contacts": [
            "Trial Countries", "Geography", "Investigator Name", 
            "Investigator Designation", "Investigator Qualification", "Investigator Location"
        ]
    }
    
    for category, fields in categories.items():
        print(f"\n{category}:")
        print("-" * 40)
        for field in fields:
            if field in result:
                value = result[field]
                # Truncate long values for display
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"  {field}: {value}")
    
    # Save to CSV
    df = pd.DataFrame([result])
    output_file = f"clinical_trial_analysis_llm_{nct_id}.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to {output_file}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Total fields extracted: {len(result)}")
    print(f"  Fields with data: {sum(1 for v in result.values() if v and v != 'NA')}")
    print(f"  Fields with 'NA': {sum(1 for v in result.values() if v == 'NA')}")
    
    # Show key insights
    print(f"\nKey Insights (LLM Analysis):")
    print(f"  Primary Drug: {result.get('Primary Drug', 'Unknown')}")
    print(f"  Primary Drug MoA: {result.get('Primary Drug MoA', 'Unknown')}")
    print(f"  Indication: {result.get('Indication', 'Unknown')}")
    print(f"  Line of Therapy: {result.get('Line of Therapy', 'Unknown')}")
    print(f"  Trial Phase: {result.get('Trial Phase', 'Unknown')}")

if __name__ == "__main__":
    main() 