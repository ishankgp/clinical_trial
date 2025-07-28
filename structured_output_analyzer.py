#!/usr/bin/env python3
"""
Clinical Trial Analyzer with Structured Output
Uses OpenAI's response_format with JSON schema for lightweight structured output
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
import openai
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StructuredOutputAnalyzer:
    """
    Analyzes clinical trials using OpenAI's structured output feature
    without the overhead of Pydantic models
    """
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o"):
        """Initialize the analyzer with OpenAI API key and model"""
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.model = model
        logger.info(f"Initialized StructuredOutputAnalyzer using {self.model}")
        
        # Add project root to path for imports
        project_root = Path(__file__).resolve().parent.parent
        if str(project_root) not in os.environ["PATH"]:
            os.environ["PATH"] = f"{str(project_root)}:{os.environ['PATH']}"
    
    def fetch_trial_data(self, nct_id: str) -> Dict[str, Any]:
        """Fetch trial data from ClinicalTrials.gov API"""
        # Implementation would fetch data from API or local cache
        # For demonstration, return a simple mock
        return {
            "nct_id": nct_id,
            "title": f"Clinical Trial {nct_id}",
            "description": "Sample trial description"
        }
    
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
        
        # Define the JSON schema for structured output
        schema = {
            "type": "object",
            "properties": {
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
                "indication": {
                    "type": "string",
                    "description": "Primary disease indication"
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
                "line_of_therapy": {
                    "type": "string",
                    "description": "Line of therapy (e.g., 1L, 2L+, Adjuvant)"
                },
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
                }
            },
            "required": [
                "primary_drug", "primary_drug_moa", "primary_drug_target", 
                "primary_drug_modality", "indication", "primary_drug_roa", 
                "mono_combo", "combination_partner", "moa_of_combination", 
                "experimental_regimen", "moa_of_experimental_regimen",
                "line_of_therapy", "biomarker_mutations", "biomarker_stratification",
                "biomarker_wildtype", "histology", "prior_treatment", 
                "stage_of_disease", "patient_population", "trial_name"
            ],
            "additionalProperties": False
        }
        
        # Create the analysis prompt
        prompt = f"""
        You are an expert Clinical Trial Analysis Assistant. Your objective is to analyze clinical trial records 
        and extract structured data fields to generate a standardized Analysis-Ready Dataset (ARD).
        
        ## TRIAL INFORMATION
        NCT ID: {nct_id}
        
        {json.dumps(trial_data, indent=2)}
        
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
                },
                "semantic_analysis": {
                    "type": "string",
                    "description": "Semantic interpretation of the query"
                },
                "suggested_follow_ups": {
                    "type": "array",
                    "description": "Suggested follow-up questions",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": [
                "filters", "query_intent", "search_strategy", 
                "relevant_fields", "confidence_score", "semantic_analysis", 
                "suggested_follow_ups"
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
        6. Semantic analysis: A deeper interpretation of what the user is looking for
        7. Suggested follow-ups: Questions that would help refine the search
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

def main():
    """Test the structured output analyzer"""
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY not found in environment!")
        return
    
    # Initialize analyzer
    analyzer = StructuredOutputAnalyzer(openai_api_key, model="gpt-4o")
    
    # Test with a sample NCT ID
    nct_id = "NCT03778931"
    print(f"Analyzing clinical trial: {nct_id}")
    
    result = analyzer.analyze_trial(nct_id)
    
    # Print results
    print("\n" + "="*80)
    print("CLINICAL TRIAL ANALYSIS RESULTS (Structured Output)")
    print("="*80)
    
    # Group results by category
    categories = {
        "Basic Information": [
            "nct_id", "trial_name"
        ],
        "Drug Information": [
            "primary_drug", "primary_drug_moa", "primary_drug_target", 
            "primary_drug_modality", "primary_drug_roa", "mono_combo", 
            "combination_partner", "moa_of_combination", "experimental_regimen", 
            "moa_of_experimental_regimen"
        ],
        "Clinical Information": [
            "indication", "line_of_therapy", "histology", "prior_treatment", 
            "stage_of_disease", "patient_population"
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
    
    # Test query analysis
    query = "Find phase 3 trials for PD-1 inhibitors in bladder cancer"
    print("\n" + "="*80)
    print(f"QUERY ANALYSIS: '{query}'")
    print("="*80)
    
    query_result = analyzer.analyze_query(query)
    
    # Print query analysis results
    print("\nQuery Intent:", query_result.get("query_intent"))
    print("Search Strategy:", query_result.get("search_strategy"))
    print("Confidence Score:", query_result.get("confidence_score"))
    print("\nFilters:")
    for key, value in query_result.get("filters", {}).items():
        print(f"  {key}: {value}")
    print("\nRelevant Fields:", ", ".join(query_result.get("relevant_fields", [])))
    print("\nSemantic Analysis:", query_result.get("semantic_analysis"))
    print("\nSuggested Follow-ups:")
    for follow_up in query_result.get("suggested_follow_ups", []):
        print(f"  - {follow_up}")

if __name__ == "__main__":
    main() 