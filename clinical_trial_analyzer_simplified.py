#!/usr/bin/env python3
"""
Simplified Clinical Trial Analyzer
Uses OpenAI's structured output feature instead of Pydantic models
"""

import json
import requests
import time
import logging
import os
from typing import Dict, Any, List, Optional
import openai
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalTrialAnalyzerSimplified:
    """
    Clinical Trial Analysis System using OpenAI's structured output
    Simplified version without Pydantic models
    """
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o"):
        """Initialize the analyzer with OpenAI API key and model"""
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.model = model
        
        # Add project root to path for imports
        project_root = Path(__file__).resolve().parent.parent
        if str(project_root) not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{str(project_root)}:{os.environ.get('PATH', '')}"
        
        logger.info(f"Initialized ClinicalTrialAnalyzerSimplified using {self.model}")
    
    def fetch_trial_data(self, nct_id: str) -> Dict[str, Any]:
        """
        Fetch trial data from ClinicalTrials.gov API
        
        Args:
            nct_id: NCT ID of the trial
            
        Returns:
            Dictionary containing trial data
        """
        cache_dir = Path("data/cache")
        cache_dir.mkdir(exist_ok=True, parents=True)
        
        cache_file = cache_dir / f"{nct_id}.json"
        
        # Check if data is in cache
        if cache_file.exists():
            logger.info(f"Loading cached data for {nct_id}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Fetch from API
        logger.info(f"Fetching data for {nct_id} from ClinicalTrials.gov API")
        url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Cache the response
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, indent=2)
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching trial data for {nct_id}: {e}")
            return {"error": str(e)}
    
    def analyze_trial(self, nct_id: str) -> Dict[str, Any]:
        """
        Analyze a clinical trial using structured output
        
        Args:
            nct_id: NCT ID of the trial
            
        Returns:
            Dictionary containing extracted fields and analysis results
        """
        # Get trial data
        trial_data = self.fetch_trial_data(nct_id)
        if "error" in trial_data:
            return {
                "error": trial_data["error"],
                "nct_id": nct_id,
                "analysis_timestamp": time.time(),
                "model_used": self.model,
                "analysis_method": "error"
            }
        
        # Define the JSON schema for structured output
        schema = {
            "type": "object",
            "properties": {
                # Drug fields
                "primary_drug": {
                    "type": "string",
                    "description": "Primary investigational drug being tested"
                },
                "primary_drug_moa": {
                    "type": "string", 
                    "description": "Mechanism of action of primary drug"
                },
                "primary_drug_target": {
                    "type": "string",
                    "description": "Molecular target of primary drug"
                },
                "primary_drug_modality": {
                    "type": "string",
                    "description": "Drug modality (e.g., ADC, Small molecule)"
                },
                "primary_drug_roa": {
                    "type": "string",
                    "description": "Route of administration"
                },
                "mono_combo": {
                    "type": "string",
                    "enum": ["Mono", "Combo"],
                    "description": "Whether drug is tested as monotherapy or combination"
                },
                "combination_partner": {
                    "type": "string",
                    "description": "Combination partner drugs"
                },
                "moa_of_combination": {
                    "type": "string",
                    "description": "Mechanism of action of combination partners"
                },
                "experimental_regimen": {
                    "type": "string",
                    "description": "Primary drug + combination partners"
                },
                "moa_of_experimental_regimen": {
                    "type": "string",
                    "description": "Combined MoA"
                },
                
                # Clinical fields
                "indication": {
                    "type": "string",
                    "description": "Primary disease indication"
                },
                "line_of_therapy": {
                    "type": "string",
                    "description": "Line of therapy (e.g., 1L, 2L+, Adjuvant)"
                },
                "histology": {
                    "type": "string",
                    "description": "Disease histology"
                },
                "prior_treatment": {
                    "type": "string",
                    "description": "Previous therapies required"
                },
                "stage_of_disease": {
                    "type": "string",
                    "description": "Disease stage"
                },
                "patient_population": {
                    "type": "string",
                    "description": "Detailed patient population description"
                },
                "trial_name": {
                    "type": "string",
                    "description": "Trial acronym"
                },
                
                # Biomarker fields
                "biomarker_mutations": {
                    "type": "string",
                    "description": "Biomarker mutations required"
                },
                "biomarker_stratification": {
                    "type": "string",
                    "description": "Biomarker expression levels"
                },
                "biomarker_wildtype": {
                    "type": "string",
                    "description": "Wildtype biomarkers"
                },
                
                # Basic fields
                "trial_id": {
                    "type": "string",
                    "description": "Trial ID"
                },
                "trial_phase": {
                    "type": "string",
                    "description": "Trial phase"
                },
                "trial_status": {
                    "type": "string",
                    "description": "Trial status"
                },
                "patient_enrollment": {
                    "type": "string",
                    "description": "Number of patients enrolled"
                },
                "sponsor": {
                    "type": "string",
                    "description": "Trial sponsor"
                },
                "sponsor_type": {
                    "type": "string",
                    "description": "Sponsor type"
                },
                "developer": {
                    "type": "string",
                    "description": "Drug developer"
                },
                "start_date": {
                    "type": "string",
                    "description": "Trial start date (YY-MM-DD)"
                },
                "primary_completion_date": {
                    "type": "string",
                    "description": "Primary completion date (YY-MM-DD)"
                },
                "study_completion_date": {
                    "type": "string",
                    "description": "Study completion date (YY-MM-DD)"
                },
                "primary_endpoints": {
                    "type": "string",
                    "description": "Primary endpoints"
                },
                "secondary_endpoints": {
                    "type": "string",
                    "description": "Secondary endpoints"
                },
                "inclusion_criteria": {
                    "type": "string",
                    "description": "Inclusion criteria"
                },
                "exclusion_criteria": {
                    "type": "string",
                    "description": "Exclusion criteria"
                },
                "trial_countries": {
                    "type": "string",
                    "description": "Countries where trial is conducted"
                },
                "geography": {
                    "type": "string",
                    "description": "Geography classification"
                },
                "investigator_name": {
                    "type": "string",
                    "description": "Investigator name"
                },
                "investigator_designation": {
                    "type": "string",
                    "description": "Investigator designation"
                },
                "investigator_qualification": {
                    "type": "string",
                    "description": "Investigator qualification"
                },
                "investigator_location": {
                    "type": "string",
                    "description": "Investigator location"
                },
                "history_of_changes": {
                    "type": "string",
                    "description": "History of changes"
                }
            },
            "required": [
                "primary_drug", "primary_drug_moa", "primary_drug_target", 
                "primary_drug_modality", "primary_drug_roa", "mono_combo", 
                "combination_partner", "moa_of_combination", "experimental_regimen", 
                "moa_of_experimental_regimen", "indication", "line_of_therapy", 
                "histology", "prior_treatment", "stage_of_disease", "patient_population", 
                "trial_name", "biomarker_mutations", "biomarker_stratification", 
                "biomarker_wildtype", "trial_id", "trial_phase", "trial_status", 
                "patient_enrollment", "sponsor", "sponsor_type", "developer", 
                "start_date", "primary_completion_date", "study_completion_date", 
                "primary_endpoints", "secondary_endpoints", "inclusion_criteria", 
                "exclusion_criteria", "trial_countries", "geography", 
                "investigator_name", "investigator_designation", 
                "investigator_qualification", "investigator_location", 
                "history_of_changes"
            ],
            "additionalProperties": False
        }
        
        # Extract key information for the prompt
        protocol = trial_data.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        description = protocol.get("descriptionModule", {})
        conditions = protocol.get("conditionsModule", {})
        arms = protocol.get("armsInterventionsModule", {})
        eligibility = protocol.get("eligibilityModule", {})
        
        # Create the analysis prompt
        prompt = f"""
        You are an expert Clinical Trial Analysis Assistant. Your objective is to analyze clinical trial records 
        and extract structured data fields to generate a standardized Analysis-Ready Dataset (ARD).
        
        ## TRIAL INFORMATION
        NCT ID: {nct_id}
        Brief Title: {identification.get("briefTitle", "")}
        Official Title: {identification.get("officialTitle", "")}
        Brief Summary: {description.get("briefSummary", "")}
        Detailed Description: {description.get("detailedDescription", "")[:1000]}...
        Conditions: {conditions.get("conditions", [])}
        
        ## INTERVENTIONS
        {json.dumps(arms.get("interventions", []), indent=2)}
        
        ## ARM GROUPS
        {json.dumps(arms.get("armGroups", []), indent=2)}
        
        ## ELIGIBILITY CRITERIA
        {eligibility.get("eligibilityCriteria", "")[:1000]}...
        
        ## ANALYSIS RULES
        
        1. PRIMARY DRUG IDENTIFICATION:
           - Identify the primary investigational drug being tested
           - Exclude active comparators (e.g., "vs chemo" or "Active Comparator: Chemo")
           - Do not consider background therapies or standard-of-care agents as primary
           - Standardize to generic drug name (e.g., "pembrolizumab" not "Keytruda")
        
        2. MECHANISM OF ACTION (MoA) STANDARDIZATION:
           - Antibodies: "Anti-[Target]" (e.g., "Anti-Nectin-4", "Anti-PD-1")
           - Small molecules: "[Target] inhibitor" (e.g., "PARP inhibitor", "EGFR inhibitor")
           - Bispecifics: "Anti-[Target] × [Target]" (e.g., "Anti-PD-1 × CTLA-4")
        
        3. DRUG MODALITY CLASSIFICATION:
           - ADC: Antibody-drug conjugate
           - Monoclonal antibody: Drugs ending in -mab
           - Small molecule: Drugs ending in -tinib, kinase inhibitors
        
        4. MONO/COMBO CLASSIFICATION:
           - Mono: Drug evaluated alone (not in combination)
           - Combo: Drug evaluated in combination with one or more drugs
        
        5. LINE OF THERAPY (LOT):
           - 1L: Treatment-naive, previously untreated, newly diagnosed
           - 2L: Patients treated with no more than 1 prior therapy
           - 2L+: Patients treated with ≥1 prior therapy, refractory/intolerant to SOC
           - Adjuvant: Treatment after primary therapy (surgery)
           - Neoadjuvant: Treatment before primary therapy
           - Maintenance: Ongoing treatment after initial successful therapy
        
        6. BIOMARKER EXTRACTION:
           - Extract biomarkers mentioned in the trial (e.g., HER2, PD-L1, EGFR)
           - Standardize names (HER2 not ErbB2, PD-L1 not PDL1)
           - Wildtype: Format as "[Gene] wild-type" or "[Gene] negative"
        
        Analyze the trial data and provide structured output according to the schema.
        """
        
        # Make API call with structured output
        try:
            start_time = time.time()
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "clinical_trial_analysis",
                        "schema": schema,
                        "strict": True
                    }
                },
                temperature=0.1
            )
            
            # Parse the response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Add metadata
            result["nct_id"] = nct_id
            result["analysis_timestamp"] = time.time()
            result["model_used"] = self.model
            result["analysis_method"] = "structured_output"
            result["analysis_time"] = time.time() - start_time
            
            logger.info(f"Successfully analyzed trial {nct_id} in {result['analysis_time']:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing trial {nct_id}: {e}")
            return {
                "error": str(e),
                "nct_id": nct_id,
                "analysis_timestamp": time.time(),
                "model_used": self.model,
                "analysis_method": "error"
            }
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a natural language query about clinical trials
        
        Args:
            query: Natural language query string
            
        Returns:
            Dictionary containing structured query analysis
        """
        # Define the JSON schema for query analysis
        schema = {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "description": "Key-value pairs of filters to apply",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "query_intent": {
                    "type": "string",
                    "description": "The primary goal of the query"
                },
                "search_strategy": {
                    "type": "string",
                    "description": "How to approach answering this query"
                },
                "relevant_fields": {
                    "type": "array",
                    "description": "Which fields from the clinical trial data are most relevant",
                    "items": {
                        "type": "string"
                    }
                },
                "confidence_score": {
                    "type": "number",
                    "description": "How confident the model is in its analysis (0.0-1.0)"
                }
            },
            "required": [
                "filters", "query_intent", "search_strategy", 
                "relevant_fields", "confidence_score"
            ],
            "additionalProperties": False
        }
        
        # Create prompt for query analysis
        prompt = f"""
        You are an expert Clinical Trial Query Analyzer. Your task is to analyze the following query about clinical trials and extract structured information.
        
        ## QUERY
        {query}
        
        ## TASK
        Analyze this query and extract:
        1. Filters: Key-value pairs of filters that should be applied (e.g., indication, line of therapy, drug)
        2. Query intent: The primary goal of the query (e.g., finding trials, comparing drugs)
        3. Search strategy: How to approach answering this query
        4. Relevant fields: Which fields from the clinical trial data are most relevant
        5. Confidence score: How confident you are in your analysis (0.0-1.0)
        """
        
        # Make API call
        try:
            start_time = time.time()
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "query_analysis",
                        "schema": schema,
                        "strict": True
                    }
                },
                temperature=0.1
            )
            
            # Parse the response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Add metadata
            result["query"] = query
            result["analysis_timestamp"] = time.time()
            result["model_used"] = self.model
            result["analysis_time"] = time.time() - start_time
            
            logger.info(f"Successfully analyzed query in {result['analysis_time']:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {
                "error": str(e),
                "query": query,
                "analysis_timestamp": time.time(),
                "model_used": self.model
            }
    
    def reasoning_query(self, query: str) -> Dict[str, Any]:
        """
        Perform a semantic search using reasoning
        
        Args:
            query: Natural language query string
            
        Returns:
            Dictionary containing search results and reasoning
        """
        # Define the JSON schema for reasoning query
        schema = {
            "type": "object",
            "properties": {
                "query_intent": {
                    "type": "string",
                    "description": "The interpreted intent of the query"
                },
                "filters": {
                    "type": "object",
                    "description": "Structured filters extracted from the query",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "semantic_analysis": {
                    "type": "string",
                    "description": "Detailed semantic analysis of the query"
                },
                "suggested_follow_ups": {
                    "type": "array",
                    "description": "Suggested follow-up questions",
                    "items": {
                        "type": "string"
                    }
                },
                "confidence_score": {
                    "type": "number",
                    "description": "Confidence in the analysis (0.0-1.0)"
                }
            },
            "required": [
                "query_intent", "filters", "semantic_analysis", 
                "suggested_follow_ups", "confidence_score"
            ],
            "additionalProperties": False
        }
        
        # Create prompt for reasoning query
        prompt = f"""
        You are an expert Clinical Trial Search Assistant. Your task is to analyze the following query about clinical trials
        and extract structured information for semantic search.
        
        ## QUERY
        {query}
        
        ## TASK
        Analyze this query and extract:
        1. Query intent: The interpreted intent of the query
        2. Filters: Structured filters extracted from the query (e.g., indication, line of therapy, drug)
        3. Semantic analysis: Detailed semantic analysis of the query
        4. Suggested follow-ups: Questions that would help refine the search
        5. Confidence score: How confident you are in your analysis (0.0-1.0)
        """
        
        # Make API call
        try:
            start_time = time.time()
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "reasoning_query",
                        "schema": schema,
                        "strict": True
                    }
                },
                temperature=0.1
            )
            
            # Parse the response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Add metadata
            result["query"] = query
            result["analysis_timestamp"] = time.time()
            result["model_used"] = self.model
            result["analysis_time"] = time.time() - start_time
            
            logger.info(f"Successfully processed reasoning query in {result['analysis_time']:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Reasoning query failed: {e}")
            return {
                "error": str(e),
                "query": query,
                "analysis_timestamp": time.time(),
                "model_used": self.model
            }
    
    def compare_analysis(self, query: str, trials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare clinical trials based on a query
        
        Args:
            query: Natural language query string
            trials: List of trial data dictionaries
            
        Returns:
            Dictionary containing comparison results
        """
        # Define the JSON schema for comparison analysis
        schema = {
            "type": "object",
            "properties": {
                "query_intent": {
                    "type": "string",
                    "description": "The interpreted intent of the comparison query"
                },
                "comparison_summary": {
                    "type": "string",
                    "description": "Overall summary of the comparison"
                },
                "key_differences": {
                    "type": "array",
                    "description": "Key differences between the trials",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Category of difference (e.g., 'Drug', 'Eligibility')"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the difference"
                            }
                        },
                        "required": ["category", "description"],
                        "additionalProperties": False
                    }
                },
                "recommendation": {
                    "type": "string",
                    "description": "Recommendation based on the comparison"
                },
                "confidence_score": {
                    "type": "number",
                    "description": "Confidence in the analysis (0.0-1.0)"
                }
            },
            "required": [
                "query_intent", "comparison_summary", "key_differences", 
                "recommendation", "confidence_score"
            ],
            "additionalProperties": False
        }
        
        # Format trial data for the prompt
        trials_summary = []
        for i, trial in enumerate(trials[:5]):  # Limit to 5 trials for prompt size
            summary = f"Trial {i+1} - {trial.get('nct_id', 'Unknown')}: {trial.get('trial_name', 'Unnamed Trial')}\n"
            summary += f"Primary Drug: {trial.get('primary_drug', 'N/A')}\n"
            summary += f"Indication: {trial.get('indication', 'N/A')}\n"
            summary += f"Phase: {trial.get('trial_phase', 'N/A')}\n"
            summary += f"Status: {trial.get('trial_status', 'N/A')}\n"
            trials_summary.append(summary)
        
        trials_text = "\n\n".join(trials_summary)
        
        # Create prompt for comparison analysis
        prompt = f"""
        You are an expert Clinical Trial Comparison Assistant. Your task is to compare the following clinical trials
        based on the user's query.
        
        ## QUERY
        {query}
        
        ## TRIALS TO COMPARE
        {trials_text}
        
        ## TASK
        Compare these trials and provide:
        1. Query intent: The interpreted intent of the comparison query
        2. Comparison summary: Overall summary of the comparison
        3. Key differences: Key differences between the trials
        4. Recommendation: Recommendation based on the comparison
        5. Confidence score: How confident you are in your analysis (0.0-1.0)
        """
        
        # Make API call
        try:
            start_time = time.time()
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "comparison_analysis",
                        "schema": schema,
                        "strict": True
                    }
                },
                temperature=0.1
            )
            
            # Parse the response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Add metadata
            result["query"] = query
            result["analysis_timestamp"] = time.time()
            result["model_used"] = self.model
            result["analysis_time"] = time.time() - start_time
            result["trials_compared"] = [trial.get("nct_id", "Unknown") for trial in trials[:5]]
            
            logger.info(f"Successfully completed comparison analysis in {result['analysis_time']:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Comparison analysis failed: {e}")
            return {
                "error": str(e),
                "query": query,
                "analysis_timestamp": time.time(),
                "model_used": self.model
            }

def main():
    """Test the simplified clinical trial analyzer"""
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY not found in environment!")
        return
    
    # Initialize analyzer
    analyzer = ClinicalTrialAnalyzerSimplified(openai_api_key, model="gpt-4o")
    
    # Test with a sample NCT ID
    nct_id = "NCT03778931"
    print(f"Analyzing clinical trial: {nct_id}")
    
    result = analyzer.analyze_trial(nct_id)
    
    # Print results
    print("\n" + "="*80)
    print("CLINICAL TRIAL ANALYSIS RESULTS (Simplified)")
    print("="*80)
    
    # Group results by category
    categories = {
        "Basic Information": [
            "nct_id", "trial_name", "trial_phase", "trial_status"
        ],
        "Drug Information": [
            "primary_drug", "primary_drug_moa", "primary_drug_target", 
            "primary_drug_modality", "primary_drug_roa", "mono_combo"
        ],
        "Clinical Information": [
            "indication", "line_of_therapy", "histology", "stage_of_disease"
        ],
        "Biomarkers": [
            "biomarker_mutations", "biomarker_stratification", "biomarker_wildtype"
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
    
    # Test reasoning query
    query = "Find phase 3 trials for PD-1 inhibitors in bladder cancer"
    print("\n" + "="*80)
    print(f"REASONING QUERY: '{query}'")
    print("="*80)
    
    query_result = analyzer.reasoning_query(query)
    
    # Print query analysis results
    print("\nQuery Intent:", query_result.get("query_intent"))
    print("Confidence Score:", query_result.get("confidence_score"))
    print("\nFilters:")
    for key, value in query_result.get("filters", {}).items():
        print(f"  {key}: {value}")
    print("\nSemantic Analysis:", query_result.get("semantic_analysis"))
    print("\nSuggested Follow-ups:")
    for follow_up in query_result.get("suggested_follow_ups", []):
        print(f"  - {follow_up}")

if __name__ == "__main__":
    main() 