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
from .base_analyzer import BaseAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalTrialAnalyzerReasoning(BaseAnalyzer):
    """
    Clinical Trial Analysis System using OpenAI's o3 Reasoning Models
    Based on detailed specifications in GenAI_Case_Clinical_Trial_Analysis_PROMPT_ver1.00.docx.md
    
    This analyzer extracts structured data from clinical trial records to generate
    Analysis-Ready Datasets (ARD) for downstream analysis and dashboard visualization.
    """
    
    def __init__(self, openai_api_key: str, model: str = "o3"):
        """Initialize the analyzer with OpenAI API key and o3 reasoning model"""
        super().__init__(openai_api_key)
        
        # Validate model choice - prioritize o3 reasoning models
        available_models = ["o3", "gpt-4o", "gpt-4o-mini", "gpt-4"]
        if model not in available_models:
            print(f"Warning: Model '{model}' not in available models. Using 'o3' instead.")
            self.model = "o3"
        else:
            self.model = model
            
        print(f"🏥 Clinical Trial Analyzer using {self.model}")
        print("📋 Enhanced analysis based on detailed clinical trial specifications...")
        
        # Check if model is a reasoning model
        reasoning_models = ["o3"]
        if self.model in reasoning_models:
            print(f"✅ {self.model} is a reasoning model - excellent for complex clinical trial analysis")
            print("🧠 Optimized for structured data extraction and field standardization")
        else:
            print(f"⚠️ {self.model} is not a reasoning model - consider using o3 for better results")
        
        # Load the comprehensive analysis prompt
        self._load_analysis_prompt()
    
    def _load_analysis_prompt(self):
        """Load the comprehensive clinical trial analysis prompt"""
        self.analysis_prompt = """
You are an expert Clinical Trial Analysis Assistant powered by OpenAI's o3 reasoning models. Your objective is to analyze clinical trial records from ClinicalTrials.gov and extract structured data fields to generate a standardized, valuable, and human-intelligent Analysis-Ready Dataset (ARD).

## ANALYSIS OBJECTIVE
For each provided NCT ID, analyze the full clinical trial record and extract structured data fields according to the detailed specifications below.

## CRITICAL ANALYSIS RULES

### 1. PRIMARY DRUG IDENTIFICATION
- **Source Sections**: Brief Title, Brief Summary, Description, Official Title, Intervention
- **Objective**: Identify the primary investigational drug being tested
- **Rules**:
  - Focus on the trial's main objective and evaluation focus
  - Exclude active comparators (e.g., "vs chemo" or "Active Comparator: Chemo")
  - Do not consider background therapies or standard-of-care agents as primary unless part of novel investigational combination
  - For novel combinations of two investigational agents, consider both drugs as primary in separate rows
  - Standardize to generic drug name (e.g., "pembrolizumab" not "Keytruda")
  - Use code name if generic name unavailable

### 2. MECHANISM OF ACTION (MoA) STANDARDIZATION
- **Format Rules**:
  - Antibodies: "Anti-[Target]" (e.g., "Anti-Nectin-4", "Anti-PD-1")
  - Small molecules: "[Target] inhibitor" (e.g., "PARP inhibitor", "EGFR inhibitor")
  - Bispecifics: "Anti-[Target] × [Target]" (e.g., "Anti-PD-1 × CTLA-4")
  - Trispecifics: "Anti-[Target] × [Target] × [Target]"
  - Agonists: "[Target] agonist" (e.g., "TLR9 agonist")
  - Antagonists: "[Target] antagonist" (e.g., "CCR4 antagonist")

### 3. DRUG MODALITY CLASSIFICATION
- **ADC**: Antibody-drug conjugate
- **Monoclonal antibody**: Drugs ending in -mab
- **Small molecule**: Drugs ending in -tinib, kinase inhibitors
- **CAR-T**: Chimeric antigen receptor T cell
- **T-cell engager**: T-cell redirecting bispecific
- **Cell therapy**: Cell-based therapies (NK, T-cell)
- **Gene therapy**: Gene-altering/encoding drugs
- **Radiopharmaceutical**: Radiolabeled ligands
- **Fusion protein**: Protein fusion constructs

### 4. INDICATION ANALYSIS
- **Primary Indication**: Main disease of interest/scope
- **Other Indications**: All other disease indications studied
- **Grouping**: Group and deduplicate disease names logically
- **Output Format**: [Primary Indication] + [Other Indications]

### 5. ROUTE OF ADMINISTRATION (ROA)
- **Standardized Formats**:
  - Intravenous (IV)
  - Subcutaneous (SC)
  - Oral
  - Intratumoral (IT)
- **Rules**: Do not infer ROA unless clearly stated or supported by secondary reference

### 6. MONO/COMBO CLASSIFICATION
- **Mono**: Drug evaluated alone (not in combination)
- **Combo**: Drug evaluated in combination with one or more drugs
- **Special Cases**: Profile mono and combo separately in different rows if both evaluated

### 7. LINE OF THERAPY (LOT)
- **1L**: Treatment-naive, previously untreated, newly diagnosed
- **2L**: Patients treated with no more than 1 prior therapy
- **2L+**: Patients treated with ≥1 prior therapy, refractory/intolerant to SOC
- **Adjuvant**: Treatment after primary therapy (surgery)
- **Neoadjuvant**: Treatment before primary therapy
- **Maintenance**: Ongoing treatment after initial successful therapy

### 8. BIOMARKER EXTRACTION
- **Common Biomarkers**: HER2, PD-L1, EGFR, HLA-A*02:01, PIK3CA, TROP2, MAGE-A4, MSI-H/dMMR, ALK, ROS1, BRAF, RET, MET, KRAS, Nectin-4, TP53, 5T4, MTAP, CD39, CD103, CD8+, B7-H3
- **Standardization**: Use exact gene names (HER2 not ErbB2, PD-L1 not PDL1)
- **Wildtype**: Format as "[Gene] wild-type" or "[Gene] negative"

### 9. SPONSOR TYPE CLASSIFICATION
- **Industry Only**: Pharmaceutical company sponsor
- **Academic Only**: Academic institution, university, non-profit sponsor
- **Industry-Academic Collaboration**: Mix of industry and academic sponsors

### 10. GEOGRAPHY CLASSIFICATION
- **Global**: Includes US, EU, Japan, and China
- **International**: Europe with/without Japan, China, and other countries
- **China Only**: Only China or China and Taiwan

## OUTPUT FORMAT
Return a JSON object with the following structure:

{
  "primary_drug": "string",
  "primary_drug_moa": "string", 
  "primary_drug_target": "string",
  "primary_drug_modality": "string",
  "indication": "string",
  "primary_drug_roa": "string",
  "mono_combo": "string",
  "combination_partner": "string",
  "moa_of_combination": "string",
  "experimental_regimen": "string",
  "moa_of_experimental_regimen": "string",
  "trial_name": "string",
  "trial_id": "string",
  "trial_phase": "string",
  "line_of_therapy": "string",
  "biomarker_mutations": "string",
  "biomarker_stratification": "string",
  "biomarker_wildtype": "string",
  "histology": "string",
  "prior_treatment": "string",
  "stage_of_disease": "string",
  "trial_status": "string",
  "patient_enrollment": "string",
  "sponsor_type": "string",
  "sponsor": "string",
  "collaborator": "string",
  "developer": "string",
  "start_date": "string",
  "primary_completion_date": "string",
  "study_completion_date": "string",
  "primary_endpoints": "string",
  "secondary_endpoints": "string",
  "patient_population": "string",
  "inclusion_criteria": "string",
  "exclusion_criteria": "string",
  "trial_countries": "string",
  "geography": "string",
  "investigator_name": "string",
  "investigator_designation": "string",
  "investigator_qualification": "string",
  "investigator_location": "string",
  "history_of_changes": "string"
}

## ANALYSIS PROCESS
1. Extract all relevant information from the trial record
2. Apply standardization rules consistently
3. Handle missing data appropriately (use "Not Available" when needed)
4. Create separate rows for different combinations/arms if applicable
5. Ensure all extracted data follows the specified format and rules

## REASONING PROCESS
1. First, identify all experimental arms and active comparators
2. Determine which drug is the primary investigational agent
3. Analyze the drug's mechanism and properties
4. Determine if it's evaluated as mono or combo therapy
5. Extract combination partners if applicable
6. Apply standardization rules consistently across all fields
7. Validate extracted data against the comprehensive specifications
"""
    
    # These methods are inherited from BaseAnalyzer
    
    def analyze_drug_fields_reasoning(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze drug-related fields using reasoning model with structured prompts
        
        Args:
            trial_data: Dictionary containing trial data
            
        Returns:
            Dict containing extracted drug fields
        """
        try:
            protocol = trial_data.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            description = protocol.get("descriptionModule", {})
            conditions = protocol.get("conditionsModule", {})
            arms = protocol.get("armsInterventionsModule", {})
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": self._create_drug_fields_prompt(trial_data)}],
                "temperature": 0.1,
                "max_tokens": 1500
            }
            
            # Add response_format only for supported models
            if self.model in ["gpt-4o", "gpt-4o-mini"]:
                request_params["response_format"] = {"type": "json_object"}
            
            # Make API request
            response = self.openai_client.chat.completions.create(**request_params)
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Response content: {content}")
                # Try to extract JSON using regex for older models
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid JSON response: {e}")
                else:
                    raise ValueError(f"Invalid JSON response: {e}")
            
            # Standardize field names
            standardized_result = {}
            for key, value in result.items():
                standardized_result[key] = value if value else "NA"
            
            return standardized_result
            
        except Exception as e:
            logger.error(f"Error in drug fields analysis: {e}")
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

    def analyze_clinical_fields_reasoning(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze clinical fields using reasoning model with structured prompts
        
        Args:
            trial_data: Dictionary containing trial data
            
        Returns:
            Dict containing extracted clinical fields
        """
        try:
            protocol = trial_data.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            description = protocol.get("descriptionModule", {})
            conditions = protocol.get("conditionsModule", {})
            eligibility = protocol.get("eligibilityModule", {})
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": self._create_clinical_fields_prompt(trial_data)}],
                "temperature": 0.1,
                "max_tokens": 1500
            }
            
            # Add response_format only for supported models
            if self.model in ["gpt-4o", "gpt-4o-mini"]:
                request_params["response_format"] = {"type": "json_object"}
            
            # Make API request
            response = self.openai_client.chat.completions.create(**request_params)
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Response content: {content}")
                # Try to extract JSON using regex for older models
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid JSON response: {e}")
                else:
                    raise ValueError(f"Invalid JSON response: {e}")
            
            # Standardize field names
            standardized_result = {}
            for key, value in result.items():
                standardized_result[key] = value if value else "NA"
            
            return standardized_result
            
        except Exception as e:
            logger.error(f"Error in clinical fields analysis: {e}")
            return {
                "Indication": "Error in analysis",
                "Line of Therapy": "Error in analysis",
                "Histology": "Error in analysis",
                "Prior Treatment": "Error in analysis",
                "Stage of Disease": "Error in analysis",
                "Patient Population": "Error in analysis",
                "Trial Name": "Error in analysis"
            }

    def analyze_biomarker_fields_reasoning(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze biomarker fields using reasoning model with structured prompts
        
        Args:
            trial_data: Dictionary containing trial data
            
        Returns:
            Dict containing extracted biomarker fields
        """
        try:
            protocol = trial_data.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            description = protocol.get("descriptionModule", {})
            conditions = protocol.get("conditionsModule", {})
            eligibility = protocol.get("eligibilityModule", {})
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": self._create_biomarker_fields_prompt(trial_data)}],
                "temperature": 0.1,
                "max_tokens": 1500
            }
            
            # Add response_format only for supported models
            if self.model in ["gpt-4o", "gpt-4o-mini"]:
                request_params["response_format"] = {"type": "json_object"}
            
            # Make API request
            response = self.openai_client.chat.completions.create(**request_params)
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Response content: {content}")
                # Try to extract JSON using regex for older models
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid JSON response: {e}")
                else:
                    raise ValueError(f"Invalid JSON response: {e}")
            
            # Standardize field names
            standardized_result = {}
            for key, value in result.items():
                standardized_result[key] = value if value else "NA"
            
            return standardized_result
            
        except Exception as e:
            logger.error(f"Error in biomarker analysis: {e}")
            return {
                "Biomarker (Mutations)": "Not Available",
                "Biomarker Stratification": "Not Available",
                "Biomarker (Wildtype)": "Not Available"
            }
    
    def analyze_trial(self, nct_id: str, json_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a clinical trial using o3 reasoning model with document attachment
        
        Args:
            nct_id: NCT ID of the trial
            json_file_path: Optional path to JSON file
            
        Returns:
            Dict containing extracted fields and analysis results
        """
        # Get trial data
        if json_file_path:
            trial_data = self.load_trial_data_from_file(json_file_path)
        else:
            trial_data = self.fetch_trial_data(nct_id)
            
        if not trial_data:
            return {"error": f"Could not load trial data for {nct_id}"}
        
        # Use comprehensive analysis with document attachment for o3 models
        if self.model in ["o3"]:
            return self._analyze_trial_with_document_attachment(nct_id, trial_data)
        else:
            # Fallback to existing method for non-o3 models
            return self._analyze_trial_legacy(nct_id, trial_data)
    
    def _analyze_trial_with_document_attachment(self, nct_id: str, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze clinical trial using o3 model with both clinical trial data and specification document as attachments
        Maximized for field extraction: all required fields are listed and must be included in output.
        """
        try:
            # List of all required fields (from your CSV header, deduplicated and cleaned for JSON keys)
            required_fields = [
                "nct_id", "trial_id", "trial_name", "trial_phase", "trial_status", "primary_drug", "primary_drug_moa", "primary_drug_target", "primary_drug_modality", "indication", "primary_drug_roa", "mono_combo", "combination_partner", "moa_of_combination", "experimental_regimen", "moa_of_experimental_regimen", "line_of_therapy", "biomarker_mutations", "biomarker_stratification", "biomarker_wildtype", "histology", "prior_treatment", "stage_of_disease", "patient_enrollment", "sponsor_type", "sponsor", "collaborator", "developer", "start_date", "primary_completion_date", "study_completion_date", "primary_endpoints", "secondary_endpoints", "patient_population", "inclusion_criteria", "exclusion_criteria", "trial_countries", "geography", "investigator_name", "investigator_designation", "investigator_qualification", "investigator_location", "history_of_changes", "analysis_timestamp", "model_used", "analysis_method"
            ]

            # Create the analysis prompt with explicit field list and strict instructions
            analysis_prompt = f"""
Please analyze the clinical trial data provided in the attached files according to the detailed specifications.

I have provided you with:
1. The complete clinical trial data for NCT ID: {nct_id}
2. The detailed clinical trial analysis specification document

**IMPORTANT:**
- Extract and return a JSON object with **ALL** of the following fields (even if the value is missing or not found, use null or 'N/A').
- Do **not** omit any field. If a field is not available, set its value to 'N/A'.
- Use the exact field names below as JSON keys:

{json.dumps(required_fields, indent=2)}

- Example Output:
{{
  "nct_id": "NCT12345678",
  "trial_id": "12345",
  "trial_name": "Study of Drug X",
  "trial_phase": "Phase 3",
  "trial_status": "Recruiting",
  "primary_drug": "Drug X",
  "primary_drug_moa": "Anti-PD-1",
  "primary_drug_target": "PD-1",
  "primary_drug_modality": "Monoclonal antibody",
  "indication": "Cancer",
  "primary_drug_roa": "Intravenous",
  "mono_combo": "Mono",
  "combination_partner": "N/A",
  "moa_of_combination": "N/A",
  "experimental_regimen": "Drug X",
  "moa_of_experimental_regimen": "Anti-PD-1",
  "line_of_therapy": "1L",
  "biomarker_mutations": "N/A",
  "biomarker_stratification": "N/A",
  "biomarker_wildtype": "N/A",
  "histology": "N/A",
  "prior_treatment": "N/A",
  "stage_of_disease": "Stage 3",
  "patient_enrollment": "100",
  "sponsor_type": "Industry",
  "sponsor": "Pharma Co",
  "collaborator": "N/A",
  "developer": "Pharma Co",
  "start_date": "2023-01-01",
  "primary_completion_date": "2024-01-01",
  "study_completion_date": "2025-01-01",
  "primary_endpoints": "Efficacy",
  "secondary_endpoints": "Safety",
  "patient_population": "Adults",
  "inclusion_criteria": "Criteria",
  "exclusion_criteria": "Criteria",
  "trial_countries": "USA",
  "geography": "Global",
  "investigator_name": "Dr. Smith",
  "investigator_designation": "Principal Investigator",
  "investigator_qualification": "MD",
  "investigator_location": "Hospital",
  "history_of_changes": "None",
  "analysis_timestamp": "2023-07-24T11:50:00",
  "model_used": "o3",
  "analysis_method": "dual_document_attachment"
}}

- Follow the standardization and extraction rules in the attached document for each field.
- If a field is not present in the input, still include it in the output as 'N/A'.
- Return only a single JSON object with all fields populated.
"""
            
            # Prepare the specification document attachment
            doc_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'GenAI_Case_Clinical_Trial_Analysis_PROMPT_ver1.00.docx.md')
            
            if os.path.exists(doc_path):
                # Read the specification document content
                with open(doc_path, 'r', encoding='utf-8') as f:
                    doc_content = f.read()
                
                # Upload both files
                spec_file_id = self._upload_document(doc_content, f"clinical_trial_analysis_specs.md")
                trial_file_id = self._upload_document(json.dumps(trial_data, indent=2), f"{nct_id}_trial_data.json")
                
                # Create the API call with both attachments
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": analysis_prompt
                                },
                                {
                                    "type": "file",
                                    "file_id": spec_file_id
                                },
                                {
                                    "type": "file",
                                    "file_id": trial_file_id
                                }
                            ]
                        }
                    ],
                    max_completion_tokens=4000,
                    response_format={"type": "json_object"}
                )
                
                # Clean up uploaded files
                try:
                    self.openai_client.files.delete(spec_file_id)
                    self.openai_client.files.delete(trial_file_id)
                except Exception as e:
                    logger.warning(f"Could not delete uploaded files: {e}")
                    
            else:
                # Fallback if document not found
                logger.warning(f"Document not found at {doc_path}, using text-based prompt")
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.analysis_prompt},
                        {"role": "user", "content": f"Analyze the following clinical trial data: {json.dumps(trial_data, indent=2)}"}
                    ],
                    max_completion_tokens=4000,
                    response_format={"type": "json_object"}
                )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            
            # Post-process: Ensure all required fields are present
            for field in required_fields:
                if field not in result or result[field] in [None, "", "null"]:
                    result[field] = "N/A"
            
            # Add metadata
            result.update({
                "nct_id": nct_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "model_used": self.model,
                "analysis_method": "dual_document_attachment"
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error in dual document attachment analysis: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "nct_id": nct_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "model_used": self.model
            }
    
    def _upload_document(self, content: str, filename: str) -> str:
        """
        Upload document content to OpenAI for attachment
        """
        try:
            # Create a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                f.write(content)
                temp_path = f.name
            
            # Upload the file
            with open(temp_path, 'rb') as f:
                file_response = self.openai_client.files.create(
                    file=f,
                    purpose="assistants"
                )
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return file_response.id
            
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            raise
    
    def _analyze_trial_legacy(self, nct_id: str, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy analysis method for non-o3 models
        """
        # Extract all fields using reasoning models
        result = {
            "nct_id": nct_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "model_used": self.model,
            "analysis_method": "legacy"
        }
        
        # Extract basic fields (pass nct_id for fallback)
        basic_fields = self.extract_basic_fields(trial_data, nct_id=nct_id)
        result.update(basic_fields)
        
        # Extract drug-related fields using reasoning
        drug_fields = self.analyze_drug_fields_reasoning(trial_data)
        result.update(drug_fields)
        
        # Extract clinical fields using reasoning
        clinical_fields = self.analyze_clinical_fields_reasoning(trial_data)
        result.update(clinical_fields)
        
        # Extract biomarker fields using reasoning
        biomarker_fields = self.analyze_biomarker_fields_reasoning(trial_data)
        result.update(biomarker_fields)
        
        return result
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a natural language query using reasoning models to extract structured filters and query intent
        
        Args:
            query: Natural language query string
            
        Returns:
            Dict containing extracted filters, query intent, and analysis
        """
        try:
            # Create a reasoning prompt for query analysis
            reasoning_prompt = f"""
            Analyze the following natural language query about clinical trials and extract structured information:
            
            Query: "{query}"
            
            Please extract:
            1. Structured filters (drug names, indications, phases, status, etc.)
            2. Query intent (what the user is looking for)
            3. Suggested search strategy
            4. Relevant fields to focus on
            
            Return your analysis as a JSON object with the following structure:
            {{
                "filters": {{
                    "primary_drug": "extracted drug name or null",
                    "indication": "extracted indication or null", 
                    "trial_phase": "extracted phase or null",
                    "trial_status": "extracted status or null",
                    "sponsor": "extracted sponsor or null",
                    "line_of_therapy": "extracted line of therapy or null",
                    "biomarker": "extracted biomarker or null"
                }},
                "query_intent": "description of what the user wants",
                "search_strategy": "how to approach this search",
                "relevant_fields": ["list", "of", "relevant", "fields"],
                "confidence_score": 0.0-1.0
            }}
            
            Focus on clinical trial terminology and be precise in your extraction.
            """
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": reasoning_prompt}],
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            # Add response_format only for supported models
            if self.model in ["gpt-4o", "gpt-4o-mini"]:
                request_params["response_format"] = {"type": "json_object"}
            
            # Make API request
            response = self.openai_client.chat.completions.create(**request_params)
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Response content: {content}")
                # Try to extract JSON using regex for older models
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid JSON response: {e}")
                else:
                    raise ValueError(f"Invalid JSON response: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in query analysis: {e}")
            return {
                "filters": {},
                "query_intent": f"Error analyzing query: {e}",
                "search_strategy": "Use basic keyword search",
                "relevant_fields": ["primary_drug", "indication"],
                "confidence_score": 0.0
            }
    
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
                time.sleep(2)  # Longer delay for reasoning model
        
        if results:
            df = pd.DataFrame(results)
            return df
        else:
            return pd.DataFrame()
    
    # Helper methods are inherited from BaseAnalyzer

def main():
    """Main function to test the reasoning analyzer"""
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
    
    # Initialize analyzer with reasoning model
    analyzer = ClinicalTrialAnalyzerReasoning(openai_api_key, model="gpt-4o")
    
    # Test with the provided JSON file
    json_file_path = "NCT07046273.json"
    nct_id = "NCT07046273"
    
    if not os.path.exists(json_file_path):
        print(f"Error: {json_file_path} not found!")
        return
    
    print(f"Analyzing clinical trial: {nct_id}")
    print(f"Using reasoning model: {analyzer.model}")
    
    result = analyzer.analyze_trial(nct_id, json_file_path)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    # Print results
    print("\n" + "="*80)
    print("CLINICAL TRIAL ANALYSIS RESULTS (Reasoning Model)")
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
    output_file = f"clinical_trial_analysis_reasoning_{nct_id}.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to {output_file}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Model used: {analyzer.model}")
    print(f"  Total fields extracted: {len(result)}")
    print(f"  Fields with data: {sum(1 for v in result.values() if v and v != 'NA')}")
    print(f"  Fields with 'NA': {sum(1 for v in result.values() if v == 'NA')}")
    
    # Show key insights
    print(f"\nKey Insights (Reasoning Model):")
    print(f"  Primary Drug: {result.get('Primary Drug', 'Unknown')}")
    print(f"  Primary Drug MoA: {result.get('Primary Drug MoA', 'Unknown')}")
    print(f"  Indication: {result.get('Indication', 'Unknown')}")
    print(f"  Line of Therapy: {result.get('Line of Therapy', 'Unknown')}")
    print(f"  Trial Phase: {result.get('Trial Phase', 'Unknown')}")

if __name__ == "__main__":
    main() 