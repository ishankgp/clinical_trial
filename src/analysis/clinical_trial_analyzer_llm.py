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
from src.analysis.base_analyzer import BaseAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalTrialAnalyzerLLM(BaseAnalyzer):
    """
    Clinical Trial Analysis System using LLM for complex field extraction
    Based on the detailed specifications in GenAI_Case_Clinical_Trial_Analysis_PROMPT_ver1.00.docx.md
    """
    
    def __init__(self, openai_api_key: str):
        """Initialize the analyzer with OpenAI API key"""
        super().__init__(openai_api_key)
        
    # These methods are inherited from BaseAnalyzer
    
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
    
    # analyze_multiple_trials is inherited from BaseAnalyzer
    
    # Helper methods for rule-based extraction
    # Helper methods are inherited from BaseAnalyzer

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