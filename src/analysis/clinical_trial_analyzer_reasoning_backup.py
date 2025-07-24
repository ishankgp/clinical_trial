import json
import requests
import pandas as pd
from typing import List, Dict, Any, Optional, Union, Literal
import openai
from datetime import datetime
import re
import logging
import os
import time
from pathlib import Path
from pydantic import BaseModel, Field
from src.analysis.base_analyzer import BaseAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Pydantic models for structured output
class DrugFields(BaseModel):
    """Pydantic model for drug-related fields"""
    primary_drug: str = Field(default="N/A", description="Primary investigational drug being tested")
    primary_drug_moa: str = Field(default="N/A", description="Mechanism of action of primary drug")
    primary_drug_target: str = Field(default="N/A", description="Molecular target of primary drug")
    primary_drug_modality: str = Field(default="N/A", description="Drug modality (e.g., ADC, Small molecule)")
    primary_drug_roa: str = Field(default="N/A", description="Route of administration")
    mono_combo: str = Field(default="N/A", description="Mono or combination therapy")
    combination_partner: str = Field(default="N/A", description="Combination partner drugs")
    moa_of_combination: str = Field(default="N/A", description="Mechanism of action of combination partners")
    experimental_regimen: str = Field(default="N/A", description="Primary drug + combination partners")
    moa_of_experimental_regimen: str = Field(default="N/A", description="Combined MoA")

class ClinicalFields(BaseModel):
    """Pydantic model for clinical fields"""
    indication: str = Field(default="N/A", description="Primary disease indication")
    line_of_therapy: str = Field(default="N/A", description="Line of therapy (e.g., 1L, 2L+)")
    histology: str = Field(default="N/A", description="Disease histology")
    prior_treatment: str = Field(default="N/A", description="Previous therapies required")
    stage_of_disease: str = Field(default="N/A", description="Disease stage")
    patient_population: str = Field(default="N/A", description="Detailed patient population description")
    trial_name: str = Field(default="N/A", description="Trial acronym")

class BiomarkerFields(BaseModel):
    """Pydantic model for biomarker fields"""
    biomarker_mutations: str = Field(default="Not Available", description="Biomarker mutations required")
    biomarker_stratification: str = Field(default="Not Available", description="Biomarker expression levels")
    biomarker_wildtype: str = Field(default="Not Available", description="Wildtype biomarkers")

class BasicFields(BaseModel):
    """Pydantic model for basic trial fields"""
    nct_id: str = Field(..., description="NCT ID of the trial")
    trial_id: str = Field(default="N/A", description="Trial ID")
    trial_phase: str = Field(default="N/A", description="Trial phase")
    trial_status: str = Field(default="N/A", description="Trial status")
    patient_enrollment: str = Field(default="N/A", description="Number of patients enrolled")
    sponsor: str = Field(default="N/A", description="Trial sponsor")
    sponsor_type: str = Field(default="N/A", description="Sponsor type")
    developer: str = Field(default="N/A", description="Drug developer")
    start_date: str = Field(default="N/A", description="Trial start date (YY-MM-DD)")
    primary_completion_date: str = Field(default="N/A", description="Primary completion date (YY-MM-DD)")
    study_completion_date: str = Field(default="N/A", description="Study completion date (YY-MM-DD)")
    primary_endpoints: str = Field(default="N/A", description="Primary endpoints")
    secondary_endpoints: str = Field(default="N/A", description="Secondary endpoints")
    inclusion_criteria: str = Field(default="N/A", description="Inclusion criteria")
    exclusion_criteria: str = Field(default="N/A", description="Exclusion criteria")
    trial_countries: str = Field(default="N/A", description="Countries where trial is conducted")
    geography: str = Field(default="N/A", description="Geography classification")
    investigator_name: str = Field(default="N/A", description="Investigator name")
    investigator_designation: str = Field(default="N/A", description="Investigator designation")
    investigator_qualification: str = Field(default="N/A", description="Investigator qualification")
    investigator_location: str = Field(default="N/A", description="Investigator location")
    history_of_changes: str = Field(default="N/A", description="History of changes")

class AnalysisResult(BaseModel):
    """Complete clinical trial analysis result"""
    # Basic fields
    nct_id: str
    trial_id: str = "N/A"
    trial_phase: str = "N/A"
    trial_status: str = "N/A"
    patient_enrollment: str = "N/A"
    sponsor: str = "N/A"
    sponsor_type: str = "N/A"
    developer: str = "N/A"
    start_date: str = "N/A"
    primary_completion_date: str = "N/A"
    study_completion_date: str = "N/A"
    primary_endpoints: str = "N/A"
    secondary_endpoints: str = "N/A"
    inclusion_criteria: str = "N/A"
    exclusion_criteria: str = "N/A"
    trial_countries: str = "N/A"
    geography: str = "N/A"
    investigator_name: str = "N/A"
    investigator_designation: str = "N/A"
    investigator_qualification: str = "N/A"
    investigator_location: str = "N/A"
    history_of_changes: str = "N/A"
    
    # Drug fields
    primary_drug: str = "N/A"
    primary_drug_moa: str = "N/A"
    primary_drug_target: str = "N/A"
    primary_drug_modality: str = "N/A"
    primary_drug_roa: str = "N/A"
    mono_combo: str = "N/A"
    combination_partner: str = "N/A"
    moa_of_combination: str = "N/A"
    experimental_regimen: str = "N/A"
    moa_of_experimental_regimen: str = "N/A"
    
    # Clinical fields
    indication: str = "N/A"
    line_of_therapy: str = "N/A"
    histology: str = "N/A"
    prior_treatment: str = "N/A"
    stage_of_disease: str = "N/A"
    patient_population: str = "N/A"
    trial_name: str = "N/A"
    
    # Biomarker fields
    biomarker_mutations: str = "Not Available"
    biomarker_stratification: str = "Not Available"
    biomarker_wildtype: str = "Not Available"
    
    # Metadata
    analysis_timestamp: str
    model_used: str
    analysis_method: str
    
    class Config:
        schema_extra = {
            "example": {
                "nct_id": "NCT12345678",
                "primary_drug": "pembrolizumab",
                "indication": "Bladder Cancer",
                "line_of_therapy": "1L",
                "analysis_timestamp": "2025-07-24T11:50:00",
                "model_used": "o3",
                "analysis_method": "reasoning"
            }
        }

class QueryAnalysisResult(BaseModel):
    """Structured result of query analysis"""
    filters: Dict[str, Optional[str]] = Field(default_factory=dict)
    query_intent: str
    search_strategy: str
    relevant_fields: List[str]
    confidence_score: float

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
    
    def _make_api_call(self, prompt: str, max_tokens: int = 2000, background: bool = False, webhook_url: Optional[str] = None, tools: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Make an API call to either the Responses API (for o3) or Chat Completions API (for other models)
        
        Args:
            prompt: The prompt to send to the API
            max_tokens: Maximum number of tokens in the response
            background: Whether to run the API call in the background
            webhook_url: URL to send webhook notification when background job completes
            tools: List of tools to use with the API call
            
        Returns:
            String containing the API response content
        """
        try:
            # For o3 model, use the reasoning API
            if self.model == "o3":
                # Use the new reasoning API format
                request_params = {
                    "model": self.model,
                    "input": prompt,
                    "reasoning": {"effort": "high"},  # Use high effort for complex analysis
                    "max_output_tokens": max_tokens
                }
                
                # Add tools if specified
                if tools:
                    request_params["tools"] = tools
                
                # Add background and webhook if specified
                if background:
                    request_params["background"] = background
                    if webhook_url:
                        request_params["webhook_url"] = webhook_url
                
                response = self.openai_client.responses.create(**request_params)
                
                # If running in background, return the job ID
                if background:
                    return f"Background job started with ID: {response.id}"
                
                return response.output
            else:
                # For other models, use the chat completions API
                request_params = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": max_tokens
                }
                
                # Add response_format only for supported models
                if self.model in ["gpt-4o", "gpt-4o-mini"]:
                    request_params["response_format"] = {"type": "json_object"}
                    
                    # Add tools if specified (only for supported models)
                    if tools and self.model == "gpt-4o":
                        request_params["tools"] = tools
                
                # Make API request
                response = self.openai_client.chat.completions.create(**request_params)
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"API call error: {e}")
            raise

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON response from API call
        
        Args:
            content: String containing JSON response
            
        Returns:
            Dictionary parsed from JSON response
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response content: {content}")
            # Try to extract JSON using regex for older models
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON response: {e}")
            else:
                raise ValueError(f"Invalid JSON response: {e}")
    
    def analyze_drug_fields_reasoning(self, trial_data: Dict[str, Any]) -> Union[Dict[str, Any], DrugFields]:
        """
        Analyze drug-related fields using reasoning model with structured prompts
        
        Args:
            trial_data: Dictionary containing trial data
            
        Returns:
            DrugFields model or dictionary containing extracted drug fields
        """
        try:
            protocol = trial_data.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            description = protocol.get("descriptionModule", {})
            conditions = protocol.get("conditionsModule", {})
            arms = protocol.get("armsInterventionsModule", {})
            
            # Create a more detailed prompt with specific rules and examples from the specification document
            prompt = f"""
            Analyze the following clinical trial information and extract drug-related fields according to the specified rules:

            TRIAL INFORMATION:
            NCT ID: {identification.get("nctId", "")}
            BRIEF TITLE: {identification.get("briefTitle", "")}
            OFFICIAL TITLE: {identification.get("officialTitle", "")}
            BRIEF SUMMARY: {description.get("briefSummary", "")}
            CONDITIONS: {conditions.get("conditions", [])}
            ARM GROUPS: {json.dumps(arms.get("armGroups", []), indent=2)}
            INTERVENTIONS: {json.dumps(arms.get("interventions", []), indent=2)}

            EXTRACTION RULES WITH EXAMPLES:

            1. PRIMARY DRUG:
               - Source: Brief Title, Brief Summary, Description, Official Title, Intervention sections
               - Identify the primary investigational drug being tested in the trial
               - Focus on the trial's main objective and evaluation focus
               - EXCLUDE active comparators (e.g., "vs chemo" or "Active Comparator: Chemo")
               - DO NOT consider background therapies or standard-of-care agents as primary unless part of novel investigational combination
               - For novel combinations of two investigational agents, consider both drugs as primary
               - Standardize to generic drug name (e.g., "pembrolizumab" not "Keytruda")
               - Use code name if generic name unavailable
               
               EXAMPLE 1:
               NCT ID: NCT06592326
               Title: 9MW2821 in Combination with Toripalimab vs Standard Chemotherapy in Locally Advanced or Metastatic Urothelial Cancer
               PRIMARY DRUG OUTPUT: 9MW2821
               JUSTIFICATION: Toripalimab is a combination partner; standard chemo is a comparator
               
               EXAMPLE 2:
               NCT ID: NCT06225596
               Title: Study BT8009-230 in Participants with Locally Advanced or Metastatic Urothelial Cancer (Duravelo-2)
               PRIMARY DRUG OUTPUT: BT8009-230
               JUSTIFICATION: The drug is evaluated in mono arm and is primary focus

            2. PRIMARY DRUG MOA (Mechanism of Action):
               - Standardize using these formats:
                 * Antibodies: "Anti-[Target]" (e.g., "Anti-Nectin-4", "Anti-PD-1")
                 * Small molecules: "[Target] inhibitor" (e.g., "PARP inhibitor", "EGFR inhibitor")
                 * Bispecifics: "Anti-[Target] × [Target]" (e.g., "Anti-PD-1 × CTLA-4")
                 * Trispecifics: "Anti-[Target] × [Target] × [Target]"
                 * Agonists: "[Target] agonist" (e.g., "TLR9 agonist")
                 * Antagonists: "[Target] antagonist" (e.g., "CCR4 antagonist")
                 
               EXAMPLE 1:
               NCT ID: NCT05827614
               Brief Summary: BBI-355 is an oral, potent, selective checkpoint kinase 1 (or CHK1) small molecule inhibitor
               MOA OUTPUT: Anti-CHK1
               JUSTIFICATION: BBI-355 is the primary drug and its mechanism given in the summary
               
               EXAMPLE 2:
               NCT ID: NCT03557918
               Title: Trial of Tremelimumab in Patients With Previously Treated Metastatic Urothelial Cancer
               MOA OUTPUT: Anti-CTLA-4
               JUSTIFICATION: Tremelimumab is the primary drug and its mechanism is Anti-CTLA-4

            3. PRIMARY DRUG TARGET:
               - Extract the molecular or biological target of the primary drug
               - Align with the MoA (e.g., MoA: Anti-Nectin-4 → Target: Nectin-4)
               - Use the target name only (e.g., Nectin-4, PD-1, c-MET)
               - Do not include prefixes like "Anti-" or suffixes like "-inhibitor"
               
               EXAMPLE 1:
               NCT ID: NCT05827614
               Brief Summary: BBI-355 is an oral, potent, selective checkpoint kinase 1 (or CHK1) small molecule inhibitor
               TARGET OUTPUT: CHK1
               JUSTIFICATION: BBI-355 is the primary drug and its target is CHK1
               
               EXAMPLE 2:
               NCT ID: NCT06592326
               Title: 9MW2821 in Combination With Toripalimab vs Standard Chemotherapy in Locally Advanced or Metastatic Urothelial Cancer
               TARGET OUTPUT: Nectin-4
               JUSTIFICATION: 9MW2821 is an Anti-Nectin-4 drug, so the target is Nectin-4

            4. PRIMARY DRUG MODALITY:
               - Standardize terminology:
                 * "Antibody-drug conjugate" → ADC
                 * "T-cell redirecting bispecific" → T-cell engager
                 * "Chimeric antigen receptor T cell" → CAR-T
               - Tagging Rules:
                 * Drugs ending in -mab → Monoclonal antibody
                 * Drugs ending in -tinib → Small molecule
                 * Gene-altering/encoding drugs → Gene therapy
                 * Radiolabeled ligands → Radiopharmaceutical
                 * Cell-based therapies (NK, T-cell) → Cell therapy
                 
               EXAMPLE 1:
               NCT ID: NCT07012031
               Brief Summary: Trastuzumab deruxtecan is in a class of medications called antibody-drug conjugates
               MODALITY OUTPUT: ADC
               JUSTIFICATION: Trastuzumab deruxtecan is the primary drug and its modality given in the summary
               
               EXAMPLE 2:
               NCT ID: NCT06592326
               Title: 9MW2821 in Combination With Toripalimab vs Standard Chemotherapy in Locally Advanced or Metastatic Urothelial Cancer
               MODALITY OUTPUT: ADC
               JUSTIFICATION: 9MW2821 is an antibody-drug conjugate

            5. PRIMARY DRUG ROA (Route of Administration):
               - Standardized formats:
                 * Intravenous (IV)
                 * Subcutaneous (SC)
                 * Oral
                 * Intratumoral (IT)
               - Do not infer ROA unless clearly stated
               
               EXAMPLE:
               NCT ID: NCT06592326
               Intervention: Drug: 9MW2821, 1.25mg/kg, intravenous (IV) infusion
               ROA OUTPUT: Intravenous (IV)
               JUSTIFICATION: Primary drug is 9MW2821 and ROA is intravenous

            6. MONO/COMBO CLASSIFICATION:
               - Mono: Drug evaluated alone (not in combination)
               - Combo: Drug evaluated in combination with one or more drugs
               - Special Cases: Profile mono and combo separately if both evaluated
               
               EXAMPLE 1:
               NCT ID: NCT06592326
               Arm: Experimental: 9MW2821+Toripalimab
               MONO/COMBO OUTPUT: Combo
               JUSTIFICATION: 9MW2821 is evaluated in combination with Toripalimab
               
               EXAMPLE 2:
               NCT ID: NCT05253053
               Arms: Arm A: TT-00420 Tablet Monotherapy; Arm B: TT-00420 tablet in combination with Atezolizumab
               MONO/COMBO OUTPUT: Both Mono and Combo (separate rows)
               JUSTIFICATION: TT-00420 is evaluated in different arms with multiple combination regimens

            7. COMBINATION PARTNER:
               - Extract combination partners evaluated with the primary drug
               - Do not consider active comparators as combination partners
               - If multiple combination partners in a single arm, separate with "+"
               
               EXAMPLE:
               NCT ID: NCT06592326
               Arm: Experimental: 9MW2821+Toripalimab
               COMBINATION PARTNER OUTPUT: Toripalimab
               JUSTIFICATION: 9MW2821 is the primary drug of evaluation; Toripalimab is the combination partner

            8. MOA OF COMBINATION:
               - Extract MoAs for all combination partners (not primary drug)
               - Use the same standardization rules as for primary drug MoA
               - For multiple partners, separate MoAs with "+"
               
               EXAMPLE:
               NCT ID: NCT05827614
               Arms: Combination therapy of BBI-355 and EGFR inhibitor erlotinib
               MOA OF COMBINATION OUTPUT: Anti-EGFR
               JUSTIFICATION: Erlotinib is an EGFR inhibitor, so its MoA is Anti-EGFR

            9. EXPERIMENTAL REGIMEN:
               - For mono: Name of primary drug
               - For combo: Name of primary drug + combination partners
               
               EXAMPLE:
               NCT ID: NCT05827614
               Arms: Combination therapy of BBI-355 and EGFR inhibitor erlotinib
               EXPERIMENTAL REGIMEN OUTPUT: BBI-355 + Erlotinib
               JUSTIFICATION: Primary drug + Combination partner

            10. MOA OF EXPERIMENTAL REGIMEN:
                - For mono: MoA of primary drug
                - For combo: MoA of primary drug + MoA of combination partners
                
                EXAMPLE:
                NCT ID: NCT05827614
                Arms: Combination therapy of BBI-355 and EGFR inhibitor erlotinib
                MOA OF EXPERIMENTAL REGIMEN OUTPUT: CHK1 Inh + Anti-EGFR
                JUSTIFICATION: MOA of Primary drug + MOA of Combination partner

            Return a JSON object with these fields. If information is not available, use "NA".
            """
            
            # Make API call
            content = self._make_api_call(prompt, 2000)
            
            # Parse JSON response
            result = self._parse_json_response(content)
            
            # Apply standardization rules
            standardized_result = self._standardize_drug_fields(result)
            
            # Return as Pydantic model
            return DrugFields(**standardized_result)
            
        except Exception as e:
            logger.error(f"Error in drug fields analysis: {e}")
            return DrugFields(
                primary_drug="Error in analysis",
                primary_drug_moa="Error in analysis",
                primary_drug_target="Error in analysis",
                primary_drug_modality="Error in analysis",
                primary_drug_roa="Error in analysis",
                mono_combo="Error in analysis",
                combination_partner="Error in analysis",
                moa_of_combination="Error in analysis",
                experimental_regimen="Error in analysis",
                moa_of_experimental_regimen="Error in analysis"
            )
    
        def analyze_clinical_fields_reasoning(self, trial_data: Dict[str, Any]) -> Union[Dict[str, Any], ClinicalFields]:
        """
        Analyze clinical fields using reasoning model with structured prompts
        
        Args:
            trial_data: Dictionary containing trial data
            
        Returns:
            ClinicalFields model or dictionary containing extracted clinical fields
        """
        try:
            protocol = trial_data.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            description = protocol.get("descriptionModule", {})
            conditions = protocol.get("conditionsModule", {})
            eligibility = protocol.get("eligibilityModule", {})
            design = protocol.get("designModule", {})
        
            # Create enhanced prompt with specific rules and examples from the specification document
            prompt = f"""
            Analyze the following clinical trial information and extract clinical fields according to the specified rules:

            TRIAL INFORMATION:
            NCT ID: {identification.get("nctId", "")}
            BRIEF TITLE: {identification.get("briefTitle", "")}
            OFFICIAL TITLE: {identification.get("officialTitle", "")}
            BRIEF SUMMARY: {description.get("briefSummary", "")}
            DETAILED DESCRIPTION: {description.get("detailedDescription", "")}
            CONDITIONS: {conditions.get("conditions", [])}
            ELIGIBILITY CRITERIA: {eligibility.get("eligibilityCriteria", "")}
            STUDY DESIGN: {json.dumps(design, indent=2)[:1000]}

            EXTRACTION RULES WITH EXAMPLES:

            1. INDICATION:
               - Source: Title, official title, brief summary, detailed description, conditions, inclusion criteria
               - Extract all disease indications studied in the clinical trial
               - Classify indications into:
                 * Primary disease of interest/scope (e.g., Bladder Cancer)
                 * All other disease indications studied in the trial
               - Use exact or closely mapped disease names as described in the trial record
               - Group and deduplicate disease names logically
               - If general terms like "advanced solid tumors" are listed, extract all specific disease names
               
               EXAMPLE:
               NCT ID: NCT05253053
               Conditions: Advanced Solid Tumor, Cholangiocarcinoma, Biliary Tract Cancer, HER2-negative Breast Cancer, Triple Negative Breast Cancer, Small-cell Lung Cancer, Bladder Cancer, Prostate Cancer, Thyroid Cancer, Gastric Cancer, Gallbladder Cancer
               INDICATION OUTPUT: Bladder Cancer + Solid tumors
               JUSTIFICATION: For a trial with focus indication = Bladder Cancer, and listing other tumors

            2. LINE OF THERAPY (LOT):
               - Source: Brief summary, study description, official title, inclusion criteria, study title
               - Rules to map line of treatment:
                 * 1L: Treatment-naive or previously untreated patients or newly diagnosed
                 * 2L: Patients treated with no more than 1 prior therapy
                 * 2L+: Patients treated with ≥1 prior therapy, or who have no standard of care options left, or are refractory/intolerant to SOC
                 * Adjuvant: Treatment given after the primary therapy (typically surgery)
                 * Neoadjuvant: Treatment given before the primary therapy
                 * Maintenance: Ongoing treatment given after initial successful therapy
                 * 1L-Maintenance: Given after 1st-line treatment
                 * 2L-Maintenance: Given after completing 2nd line treatment
               
               EXAMPLE 1:
               NCT ID: NCT02451423
               Title: Neoadjuvant Atezolizumab in Localized Bladder Cancer
               LOT OUTPUT: Neoadjuvant
               JUSTIFICATION: Neoadjuvant therapy as denoted by title itself
               
               EXAMPLE 2:
               NCT ID: NCT06592326
               Inclusion criteria: Previously untreated with local advanced or metastatic urothelial cancer
               LOT OUTPUT: 1L
               JUSTIFICATION: Previously untreated as per definition is 1L

            3. HISTOLOGY:
               - Source: Official Title, Brief Summary, Study Description and Inclusion Criteria, intervention
               - Extract the disease histology described in the trial (e.g., urothelial carcinoma, adenocarcinoma)
               - Histology should be co-related with disease if the exact histology is not given
               
               EXAMPLE:
               NCT ID: NCT05203913
               Inclusion criteria: Histologic diagnosis of predominantly urothelial carcinoma of the bladder. Focal differentiation allowed other than small cell histology.
               HISTOLOGY OUTPUT: Urothelial carcinoma
               JUSTIFICATION: Histology type of the indication of interest mentioned in inclusion criteria

            4. PRIOR TREATMENT:
               - Source: Inclusion criteria, Brief Summary, Study Description, Official Title
               - List all therapies that participants must have received prior to enrolling
               - If specific prior therapies are mentioned, list them explicitly
               - If the trial states that participants have not received any prior therapy, tag as "treatment naive"
               - Use "NA" if no information is available regarding prior treatment
               
               EXAMPLE 1:
               NCT ID: NCT03871036
               Brief summary: This trial will include metastatic urothelial carcinoma patients who progressed during or after treatment with anti-PD(L)1 therapy and have been treated by a platinum-containing regimen or are cisplatin-ineligible.
               PRIOR TREATMENT OUTPUT: Anti-PD-L1 or Platinum based chemotherapy
               JUSTIFICATION: Prior therapy progression information given in brief summary
               
               EXAMPLE 2:
               NCT ID: NCT04165317
               Inclusion criteria: Histological confirmed diagnosis of BCG-unresponsive high-risk, non-muscle invasive TCC of the urothelium within 12 months (CIS only) or 6 months (recurrent Ta/T1 disease) of completion of adequate BCG therapy.
               PRIOR TREATMENT OUTPUT: BCG
               JUSTIFICATION: Prior therapy progression information given in Inclusion criteria

            5. STAGE OF DISEASE:
               - Source: Official Title, Brief Summary, Detailed Description, Eligibility Criteria
               - Tag as Stage 4 if the trial mentions "metastatic" or "advanced cancer"
               - Tag as Stage 3/Stage 4 if the trial mentions "locally advanced" or "locally advanced/metastatic"
               - Tag as Stage 1/2 if the trial refers to early-stage disease
               - If not evident, include any TNM staging information
               
               EXAMPLE 1:
               NCT ID: NCT05911295
               Official title: An Open-label, Randomized, Controlled Phase 3 Study of Disitamab Vedotin in Combination With Pembrolizumab Versus Chemotherapy in Subjects With Previously Untreated Locally Advanced or Metastatic Urothelial Carcinoma That Expresses HER2 (IHC 1+ and Greater)
               STAGE OUTPUT: Stage 3/4
               JUSTIFICATION: Locally advanced or metastatic disease
               
               EXAMPLE 2:
               NCT ID: NCT04486781
               Brief summary: sEphB-HSA may prevent tumor cells from multiplying and blocks several compounds that promote the growth of blood vessels that bring nutrients to the tumor. The purpose of this study is to evaluate the combination of Pembrolizumab + sEphB4-HSA in the population of patients with previously untreated advanced (metastatic or recurrent) urothelial carcinoma who are chemotherapy ineligible or who refuse chemotherapy.
               STAGE OUTPUT: Stage 4
               JUSTIFICATION: Metastatic disease

            6. PATIENT POPULATION:
               - Source: Brief summary, official title, and inclusion criteria
               - Consider disease stage, type of disease, mutations, prior therapies
               - Capture patient population for each arm/cohort specifically
               
               EXAMPLE:
               NCT ID: NCT06592326
               Inclusion criteria: Previously untreated local advanced or metastatic urothelial cancer suitable for cisplatin/carboplatin-based chemotherapy
               PATIENT POPULATION OUTPUT: Previously untreated local advanced or metastatic urothelial cancer suitable for cisplatin/carboplatin-based chemotherapy
               JUSTIFICATION: Patient population specified from inclusion criteria considering type of cancer and previous treatment

            7. TRIAL NAME:
               - Source: Trial title, official title, or "Other Study ID Numbers"
               - Capture the trial acronym if available
               
               EXAMPLE:
               NCT ID: NCT05243550
               Title: A Phase 3 Single-Arm Study of UGN-102 for Treatment of Low-Grade Intermediate-Risk Non-Muscle Invasive Bladder Cancer (ENVISION)
               TRIAL NAME OUTPUT: ENVISION
               JUSTIFICATION: Trial acronym from the title

            Return a JSON object with these fields. If information is not available, use "NA".
            """
            
            # Make API call
            content = self._make_api_call(prompt, 2000)
            
            # Parse JSON response
            result = self._parse_json_response(content)
            
            # Apply standardization rules
            standardized_result = self._standardize_clinical_fields(result)
            
            # Return as Pydantic model
            return ClinicalFields(**standardized_result)
            
        except Exception as e:
            logger.error(f"Error in clinical fields analysis: {e}")
            return ClinicalFields(
                indication="Error in analysis",
                line_of_therapy="Error in analysis",
                histology="Error in analysis",
                prior_treatment="Error in analysis",
                stage_of_disease="Error in analysis",
                patient_population="Error in analysis",
                trial_name="Error in analysis"
            )
    
        def analyze_biomarker_fields_reasoning(self, trial_data: Dict[str, Any]) -> Union[Dict[str, Any], BiomarkerFields]:
        """
        Analyze biomarker fields using reasoning model with structured prompts
        
        Args:
            trial_data: Dictionary containing trial data
            
        Returns:
            BiomarkerFields model or dictionary containing extracted biomarker fields
        """
        try:
            protocol = trial_data.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            description = protocol.get("descriptionModule", {})
            conditions = protocol.get("conditionsModule", {})
            eligibility = protocol.get("eligibilityModule", {})
            outcomes = protocol.get("outcomesModule", {})
            
            # Create enhanced prompt with specific rules and examples from the specification document
            prompt = f"""
            Analyze the following clinical trial information and extract biomarker-related fields according to the specified rules:

            TRIAL INFORMATION:
            NCT ID: {identification.get("nctId", "")}
            BRIEF TITLE: {identification.get("briefTitle", "")}
            OFFICIAL TITLE: {identification.get("officialTitle", "")}
            BRIEF SUMMARY: {description.get("briefSummary", "")}
            DETAILED DESCRIPTION: {description.get("detailedDescription", "")}
            CONDITIONS: {conditions.get("conditions", [])}
            ELIGIBILITY CRITERIA: {eligibility.get("eligibilityCriteria", "")}
            OUTCOME MEASURES: {json.dumps(outcomes.get("primaryOutcomes", []) + outcomes.get("secondaryOutcomes", []), indent=2)[:1000]}

            EXTRACTION RULES WITH EXAMPLES:

            1. BIOMARKER (MUTATIONS):
               - Source: Official title, brief summary, study description, inclusion criteria, outcome measures
               - Extract all biomarkers mentioned in the clinical trial
               - Look for keywords: mutation, amplification, expression, fusion, biomarkers, actionable molecular alteration
               - Do NOT consider biomarkers mentioned in the background or exclusion criteria
               - Most common biomarkers include: HER2, PD-L1, EGFR, HLA-A*02:01, PIK3CA, TROP2, MAGE-A4, MSI-H/dMMR, ALK, ROS1, BRAF, RET, MET, KRAS, Nectin-4, TP53, 5T4, MTAP, CD39, CD103, CD8+, B7-H3
               - Standardization:
                 * Use standard gene symbols (e.g., HER2, not ErbB2)
                 * Maintain proper formatting (e.g., PD-L1, not PDL1 or PD L1)
                 * Preserve special characters and numbering (e.g., HLA-A*02:01)
                 * Group related variations (e.g., dMMR and MSI-H → dMMR/MSI-H)
               
               EXAMPLE 1:
               NCT ID: NCT06319820
               Official title: A Phase 3, Randomized Study Evaluating the Efficacy and Safety of TAR-210 Erdafitinib Intravesical Delivery System Versus Single Agent Intravesical Chemotherapy in Participants With Intermediate-risk Non-muscle Invasive Bladder Cancer (IR-NMIBC) and Susceptible FGFR Alterations
               BIOMARKER OUTPUT: FGFR
               JUSTIFICATION: Patients with FGFR mutations as specified in title
               
               EXAMPLE 2:
               NCT ID: NCT05203913
               Outcome Measure: Median Disease Free Survival by PD-L1 expression and by PI3KCA mutations
               BIOMARKER OUTPUT: PI3KCA, PD-L1
               JUSTIFICATION: Patients with PI3KCA mutations and PD-L1 expression comparisons as mentioned in outcome measures

            2. BIOMARKER STRATIFICATION:
               - Source: Study description, inclusion criteria
               - Extract biomarker expression levels mentioned in the inclusion criteria
               - Capture levels as mentioned in the trial (e.g., CPS ≥ 10, IHC 3+, TPS ≥ 1%)
               - Include scoring systems: Combined Positive Score (CPS), Immunohistochemistry (IHC), Tumor Proportion Score (TPS)
               - Example formats: "PD-L1 CPS ≥ 10", "HER2 expression (IHC3+, IHC2+/FISH+)"
               
               EXAMPLE 1:
               NCT ID: NCT05940896
               Inclusion criteria: HER2 expression is confirmed by the site: IHC 1+, 2+ or 3+
               STRATIFICATION OUTPUT: IHC 1+, 2+or 3+
               JUSTIFICATION: The expression levels for HER biomarker as given in inclusion criteria include IHC 1+, 2+or 3+
               
               EXAMPLE 2:
               NCT ID: NCT02256436
               Detailed Description: For the purposes of this study, participants with a programmed cell death-ligand 1 (PD-L1) combined positive score (CPS) ≥10% were considered to have a strongly PD-L1 positive tumor status and participants with PD-L1 CPS ≥1% were considered to have a PD-L1 positive tumor status.
               STRATIFICATION OUTPUT: CPS ≥1% or CPS ≥10%
               JUSTIFICATION: The expression levels for PD-L1 biomarker as given in the trial description as PD-L1 positive score

            3. BIOMARKER (WILDTYPE):
               - Source: Official title, brief summary, study description, inclusion criteria, outcome measures
               - Extract all wild type biomarkers mentioned in the clinical trial
               - Look for keywords: "Wild type", "non mutated", "Mutation-negative", "Negative for [specific mutation]", "Lacking [specific mutation]", "[Gene] negative by NGS/IHC/FISH/PCR", "WT" mutation, "Biomarker-negative"
               - Standardized format: Always use the gene name followed by the status
                 * Examples: "KRAS wild-type", "EGFR T790M-negative", "BRAF V600E-negative", "ALK-negative"
               
               EXAMPLE 1:
               NCT ID: NCT05512377
               Official title: Brightline-2: A Phase IIa/IIb, Open-label, Single-arm, Multi-centre Trial of BI 907828 (Brigimadlin) for Treatment of Patients With Locally Advanced / Metastatic, MDM2 Amplified, TP53 Wild-type Biliary Tract Adenocarcinoma, Pancreatic Ductal Adenocarcinoma, or Other Selected Solid Tumours
               WILDTYPE BIOMARKER OUTPUT: TP53
               JUSTIFICATION: Wild type TP53 biomarker mentioned in title itself
               
               EXAMPLE 2:
               NCT ID: NCT05827614
               Inclusion criteria: BBI-355 combination with erlotinib arm: Evidence of amplification of wildtype EGFR; BBI-355 combination with futibatinib arm: Evidence of amplification of wildtype FGFR1, FGFR2, FGFR3, or FGFR4
               WILDTYPE BIOMARKER OUTPUT: EGFR (Row 2), FGFR1, FGFR2, FGFR3, or FGFR4 (Row 3)
               JUSTIFICATION: Specific wild type mutations for each combination arm separately mentioned in the inclusion criteria

            Return a JSON object with these three biomarker fields. If information is not available, use "NA".
            """
            
            # Make API call
            content = self._make_api_call(prompt, 2000)
            
            # Parse JSON response
            result = self._parse_json_response(content)
            
            # Apply standardization rules
            standardized_result = self._standardize_biomarker_fields(result)
            
            # Return as Pydantic model
            return BiomarkerFields(**standardized_result)
            
        except Exception as e:
            logger.error(f"Error in biomarker analysis: {e}")
            return BiomarkerFields(
                biomarker_mutations="Not Available",
                biomarker_stratification="Not Available",
                biomarker_wildtype="Not Available"
            )
    
    def analyze_trial(self, nct_id: str, json_file_path: Optional[str] = None, use_pydantic: bool = True) -> Union[Dict[str, Any], AnalysisResult]:
        """
        Analyze a clinical trial using o3 reasoning model
        
        Args:
            nct_id: NCT ID of the trial
            json_file_path: Optional path to JSON file
            use_pydantic: Whether to return result as Pydantic model
            
        Returns:
            AnalysisResult or Dict containing extracted fields and analysis results
        """
        # Get trial data
        if json_file_path:
            trial_data = self.load_trial_data_from_file(json_file_path)
        else:
            trial_data = self.fetch_trial_data(nct_id)
            
        if not trial_data:
            if use_pydantic:
                return AnalysisResult(
                    nct_id=nct_id,
                    analysis_timestamp=datetime.now().isoformat(),
                    model_used=self.model,
                    analysis_method="error",
                    primary_drug=f"Error: Could not load trial data for {nct_id}"
                )
            else:
                return {"error": f"Could not load trial data for {nct_id}"}
        
        # Use legacy method for all models since document attachment is failing for o3
        result_dict = self._analyze_trial_legacy(nct_id, trial_data)
        
        # Check if the trial should be split into multiple rows
        if self._should_split_into_multiple_rows(trial_data, result_dict):
            # Return the first row of the split results
            # The full set of rows can be retrieved using analyze_trial_multi_row
            logger.info(f"Trial {nct_id} can be split into multiple rows. Use analyze_trial_multi_row for all rows.")
        
        if use_pydantic:
            try:
                return AnalysisResult(**result_dict)
            except Exception as e:
                logger.error(f"Error creating Pydantic model: {e}")
                # Fall back to dictionary
                return result_dict
        else:
            return result_dict
    
    def analyze_trial_multi_row(self, nct_id: str, json_file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Analyze a clinical trial and return multiple rows if needed based on splitting criteria
        
        Args:
            nct_id: NCT ID of the trial
            json_file_path: Optional path to JSON file
            
        Returns:
            List of dictionaries, each representing a row in the analysis
        """
        # Get trial data
        if json_file_path:
            trial_data = self.load_trial_data_from_file(json_file_path)
        else:
            trial_data = self.fetch_trial_data(nct_id)
            
        if not trial_data:
            return [{"error": f"Could not load trial data for {nct_id}"}]
        
        # Use legacy method for all models since document attachment is failing for o3
        result = self._analyze_trial_legacy(nct_id, trial_data)
        
        # Check if the trial should be split into multiple rows
        if self._should_split_into_multiple_rows(trial_data, result):
            # Split the result into multiple rows
            rows = self._split_into_multiple_rows(trial_data, result)
            logger.info(f"Trial {nct_id} split into {len(rows)} rows.")
            return rows
        
        # Return the single result as a list for consistency
        return [result]
    
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
    
    def _validate_analysis_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the analysis result against expected formats and rules
        
        Args:
            result: Dictionary containing analysis results
            
        Returns:
            Dictionary with validated and corrected fields
        """
        validated = result.copy()
        
        # Required fields from the specification
        required_fields = [
            "nct_id", "trial_id", "trial_name", "trial_phase", "trial_status", 
            "primary_drug", "primary_drug_moa", "primary_drug_target", "primary_drug_modality", 
            "indication", "primary_drug_roa", "mono_combo", "combination_partner", 
            "moa_of_combination", "experimental_regimen", "moa_of_experimental_regimen", 
            "line_of_therapy", "biomarker_mutations", "biomarker_stratification", 
            "biomarker_wildtype", "histology", "prior_treatment", "stage_of_disease", 
            "patient_enrollment", "sponsor_type", "sponsor", "collaborator", "developer", 
            "start_date", "primary_completion_date", "study_completion_date", 
            "primary_endpoints", "secondary_endpoints", "patient_population", 
            "inclusion_criteria", "exclusion_criteria", "trial_countries", "geography", 
            "investigator_name", "investigator_designation", "investigator_qualification", 
            "investigator_location", "history_of_changes"
        ]
        
        # Ensure all required fields are present
        for field in required_fields:
            if field not in validated or not validated[field]:
                validated[field] = "N/A"
        
        # Validate Mono/Combo field
        if "mono_combo" in validated:
            mono_combo = validated["mono_combo"].lower()
            if "mono" in mono_combo:
                validated["mono_combo"] = "Mono"
            elif "combo" in mono_combo or "combination" in mono_combo:
                validated["mono_combo"] = "Combo"
            else:
                # Default to Mono if unclear
                validated["mono_combo"] = "Mono"
        
        # Validate Line of Therapy field
        if "line_of_therapy" in validated:
            lot = validated["line_of_therapy"]
            valid_lots = ["1L", "2L", "2L+", "Adjuvant", "Neoadjuvant", "Maintenance", "1L-Maintenance", "2L-Maintenance"]
            
            # Check if the LOT is already in a valid format
            if lot not in valid_lots:
                # Try to standardize common variations
                lot_lower = lot.lower()
                if "first" in lot_lower or "1st" in lot_lower or "naive" in lot_lower or "untreated" in lot_lower:
                    validated["line_of_therapy"] = "1L"
                elif "second" in lot_lower or "2nd" in lot_lower:
                    validated["line_of_therapy"] = "2L"
                elif "third" in lot_lower or "3rd" in lot_lower or "refractory" in lot_lower or "relapsed" in lot_lower:
                    validated["line_of_therapy"] = "2L+"
                elif "adjuvant" in lot_lower:
                    validated["line_of_therapy"] = "Adjuvant"
                elif "neoadjuvant" in lot_lower:
                    validated["line_of_therapy"] = "Neoadjuvant"
                elif "maintenance" in lot_lower:
                    if "1l" in lot_lower or "first" in lot_lower:
                        validated["line_of_therapy"] = "1L-Maintenance"
                    elif "2l" in lot_lower or "second" in lot_lower:
                        validated["line_of_therapy"] = "2L-Maintenance"
                    else:
                        validated["line_of_therapy"] = "Maintenance"
        
        # Validate Geography field
        if "geography" in validated:
            geo = validated["geography"]
            valid_geos = ["Global", "International", "China only"]
            
            if geo not in valid_geos and "," in geo:
                # Try to apply classification rules
                countries = [c.strip() for c in geo.split(",")]
                us_present = any("united states" in c.lower() or "usa" in c.lower() for c in countries)
                eu_countries = ["austria", "belgium", "bulgaria", "croatia", "cyprus", "czechia", "czech republic", 
                               "denmark", "estonia", "finland", "france", "germany", "greece", "hungary", 
                               "ireland", "italy", "latvia", "lithuania", "luxembourg", "malta", "netherlands", 
                               "poland", "portugal", "romania", "slovakia", "slovenia", "spain", "sweden"]
                eu_present = any(any(eu in c.lower() for eu in eu_countries) for c in countries)
                japan_present = any("japan" in c.lower() for c in countries)
                china_present = any("china" in c.lower() or "taiwan" in c.lower() for c in countries)
                
                if us_present and eu_present and japan_present and china_present:
                    validated["geography"] = "Global"
                elif eu_present and len(countries) > 1:
                    validated["geography"] = "International"
                elif china_present and len(countries) <= 2 and all("china" in c.lower() or "taiwan" in c.lower() for c in countries):
                    validated["geography"] = "China only"
        
        # Validate Sponsor Type field
        if "sponsor_type" in validated:
            sponsor_type = validated["sponsor_type"]
            valid_types = ["Industry Only", "Academic Only", "Industry-Academic Collaboration"]
            
            if sponsor_type not in valid_types:
                # Default to "Not Determined" if unclear
                validated["sponsor_type"] = "Not Determined"
        
        # Validate date formats
        date_fields = ["start_date", "primary_completion_date", "study_completion_date"]
        for date_field in date_fields:
            if date_field in validated:
                date_value = validated[date_field]
                # Check if it's already in YY-MM-DD format
                if not re.match(r'\d{2}-\d{2}-\d{2}', date_value):
                    # Try to extract and reformat the date
                    date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_value)
                    if date_match:
                        month, day, year = date_match.groups()
                        if len(year) == 4:
                            year = year[2:4]  # Extract last two digits for YY format
                        validated[date_field] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return validated
    
    def _analyze_trial_legacy(self, nct_id: str, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy analysis method for all models
        Enhanced to better handle o3 model with more structured prompting
        """
        try:
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
            
            # For o3 model, use a more structured approach with a single API call
            if self.model == "o3":
                try:
                    # Create a structured prompt with clear instructions
                    structured_prompt = f"""
                    Analyze the following clinical trial data and extract key information:
                    
                    NCT ID: {nct_id}
                    
                    Trial Data:
                    {json.dumps(trial_data, indent=2)[:10000]}
                    
                    Extract the following fields (use 'N/A' if not available):
                    1. Primary Drug: The main investigational drug being tested
                    2. Primary Drug MoA: Mechanism of action (e.g., "Anti-PD-1", "PARP inhibitor")
                    3. Primary Drug Target: Target molecule or pathway
                    4. Primary Drug Modality: Type of drug (e.g., "Monoclonal antibody", "Small molecule")
                    5. Indication: Disease or condition being treated
                    6. Line of Therapy: Treatment line (e.g., "1L", "2L+")
                    7. Biomarker (Mutations): Any biomarker mutations relevant to the trial
                    8. Biomarker Stratification: How biomarkers are used for stratification
                    9. Biomarker (Wildtype): Any wildtype biomarkers relevant to the trial
                    10. Histology: Tissue type or histological classification
                    11. Prior Treatment: Required previous treatments
                    12. Stage of Disease: Disease stage for eligibility
                    
                    Return your analysis as a JSON object with these field names.
                    """
                    
                    # Make API call
                    content = self._make_api_call(structured_prompt, 2000)
                    
                    # Parse JSON response
                    additional_fields = self._parse_json_response(content)
                    
                    # Update result with extracted fields
                    result.update(additional_fields)
                    
                except Exception as e:
                    logger.error(f"Error in o3 structured analysis: {e}")
                    # Continue with standard field extraction methods
            
            # Extract drug-related fields using reasoning
            drug_fields = self.analyze_drug_fields_reasoning(trial_data)
            result.update(drug_fields)
            
            # Extract clinical fields using reasoning
            clinical_fields = self.analyze_clinical_fields_reasoning(trial_data)
            result.update(clinical_fields)
            
            # Extract biomarker fields using reasoning
            biomarker_fields = self.analyze_biomarker_fields_reasoning(trial_data)
            result.update(biomarker_fields)
                
            # Use specialized extractors for complex fields
            result["Geography"] = self._extract_geography(trial_data)
            result["Sponsor Type"] = self._extract_sponsor_type(trial_data)
            result["Developer"] = self._extract_developer(trial_data)
            result["History of Changes"] = self._extract_history_of_changes(trial_data)
            
            # Apply standardization to ensure consistent output
            result = self._standardize_drug_fields(result)
            result = self._standardize_clinical_fields(result)
            result = self._standardize_biomarker_fields(result)
            
            # Apply validation rules
            result = self._validate_analysis_result(result)
        
            return result
            
        except Exception as e:
            logger.error(f"Error in legacy analysis: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "nct_id": nct_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "model_used": self.model
            }
    
    def analyze_query(self, query: str) -> QueryAnalysisResult:
        """
        Analyze a natural language query using reasoning models to extract structured filters and query intent
        
        Args:
            query: Natural language query string
            
        Returns:
            QueryAnalysisResult containing extracted filters, query intent, and analysis
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
            
            # Make API call
            content = self._make_api_call(reasoning_prompt, 1500)
            
            # Parse JSON response
            result_dict = self._parse_json_response(content)
            
            # Return as Pydantic model
            return QueryAnalysisResult(**result_dict)
            
        except Exception as e:
            logger.error(f"Error in query analysis: {e}")
            return QueryAnalysisResult(
                filters={},
                query_intent=f"Error analyzing query: {e}",
                search_strategy="Use basic keyword search",
                relevant_fields=["primary_drug", "indication"],
                confidence_score=0.0
            )
    
    def analyze_multiple_trials(self, nct_ids: List[str], json_file_paths: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Analyze multiple clinical trials and return as DataFrame
        
        Args:
            nct_ids: List of NCT IDs to analyze
            json_file_paths: Optional list of paths to JSON files
            
        Returns:
            DataFrame containing analysis results with one or more rows per trial
        """
        results = []
        
        for i, nct_id in enumerate(nct_ids):
            try:
                json_file_path = json_file_paths[i] if json_file_paths and i < len(json_file_paths) else None
                
                # Use the multi-row analysis method to get all possible rows
                trial_results = self.analyze_trial_multi_row(nct_id, json_file_path)
                
                # Add all rows to the results list
                for result in trial_results:
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

    def _standardize_drug_fields(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize drug-related fields according to specification rules
        
        Args:
            result: Dictionary containing extracted drug fields
            
        Returns:
            Dict containing standardized drug fields
        """
        standardized = {}
        
        # Standardize Primary Drug
        if "Primary Drug" in result:
            drug = result["Primary Drug"]
            # Remove brand name references
            drug_patterns = {
                r'(\w+)\s+\(.*?\)': r'\1',  # Remove parenthetical content
                r'(.*?)\s+\(.*?known as.*?\)': r'\1',  # Remove "known as" references
                r'(\w+).*?\((\w+)\)': r'\1',  # Keep first part before parentheses
            }
            for pattern, replacement in drug_patterns.items():
                drug = re.sub(pattern, replacement, drug)
            standardized["Primary Drug"] = drug.strip()
        
        # Standardize Primary Drug MoA
        if "Primary Drug MoA" in result:
            moa = result["Primary Drug MoA"]
            # Apply MoA standardization rules
            moa_patterns = {
                r'(?i)PARPi': 'PARP inhibitor',
                r'(?i)PD-?L?1\s+inhibitor': 'Anti-PD-L1',
                r'(?i)PD-?1\s+inhibitor': 'Anti-PD-1',
                r'(?i)nectin-?4\s+directed\s+ADC': 'Anti-Nectin-4',
                r'(?i)nectin-?4\s+inhibitor': 'Anti-Nectin-4',
                r'(?i)nectin-?4\s+antibody': 'Anti-Nectin-4',
                r'(?i)HER2\s+inhibitor': 'Anti-HER2',
                r'(?i)CTLA-?4\s+inhibitor': 'Anti-CTLA-4',
            }
            for pattern, replacement in moa_patterns.items():
                moa = re.sub(pattern, replacement, moa)
            standardized["Primary Drug MoA"] = moa
        
        # Standardize Primary Drug Modality
        if "Primary Drug Modality" in result:
            modality = result["Primary Drug Modality"]
            # Apply modality standardization rules
            modality_patterns = {
                r'(?i)antibody.?drug\s+conjugate': 'ADC',
                r'(?i)chimeric\s+antigen\s+receptor\s+T\s+cell': 'CAR-T',
                r'(?i)T-?cell\s+redirecting\s+bispecific': 'T-cell engager',
            }
            for pattern, replacement in modality_patterns.items():
                modality = re.sub(pattern, replacement, modality)
                
            # Apply suffix-based rules
            if re.search(r'(?i)\w+mab\b', result.get("Primary Drug", "")):
                modality = "Monoclonal antibody"
            elif re.search(r'(?i)\w+tinib\b', result.get("Primary Drug", "")):
                modality = "Small molecule"
                
            standardized["Primary Drug Modality"] = modality
        
        # Standardize Primary Drug ROA
        if "Primary Drug ROA" in result:
            roa = result["Primary Drug ROA"]
            # Apply ROA standardization rules
            roa_patterns = {
                r'(?i)intravenous': 'Intravenous (IV)',
                r'(?i)IV\b': 'Intravenous (IV)',
                r'(?i)subcutaneous': 'Subcutaneous (SC)',
                r'(?i)SC\b': 'Subcutaneous (SC)',
                r'(?i)oral': 'Oral',
                r'(?i)intratumoral': 'Intratumoral (IT)',
                r'(?i)IT\b': 'Intratumoral (IT)',
            }
            for pattern, replacement in roa_patterns.items():
                roa = re.sub(pattern, replacement, roa)
            standardized["Primary Drug ROA"] = roa
        
        # Copy other fields as is
        for key in result:
            if key not in standardized:
                standardized[key] = result[key]
                
        return standardized
    
    def _standardize_clinical_fields(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize clinical fields according to specification rules
        
        Args:
            result: Dictionary containing extracted clinical fields
            
        Returns:
            Dict containing standardized clinical fields
        """
        standardized = {}
        
        # Standardize Line of Therapy
        if "Line of Therapy" in result:
            lot = result["Line of Therapy"]
            # Apply LOT standardization rules
            lot_patterns = {
                r'(?i)first[\s-]?line': '1L',
                r'(?i)1st[\s-]?line': '1L',
                r'(?i)treatment[\s-]?na[iï]ve': '1L',
                r'(?i)previously[\s-]?untreated': '1L',
                r'(?i)newly[\s-]?diagnosed': '1L',
                r'(?i)second[\s-]?line': '2L',
                r'(?i)2nd[\s-]?line': '2L',
                r'(?i)third[\s-]?line': '2L+',
                r'(?i)3rd[\s-]?line': '2L+',
                r'(?i)relapsed.*?refractory': '2L+',
                r'(?i)refractory': '2L+',
                r'(?i)relapsed': '2L+',
                r'(?i)previously[\s-]?treated': '2L+',
                r'(?i)maintenance': 'Maintenance',
                r'(?i)adjuvant': 'Adjuvant',
                r'(?i)neoadjuvant': 'Neoadjuvant',
            }
            for pattern, replacement in lot_patterns.items():
                if re.search(pattern, lot):
                    lot = replacement
                    break
            standardized["Line of Therapy"] = lot
        
        # Standardize Stage of Disease
        if "Stage of Disease" in result:
            stage = result["Stage of Disease"]
            # Apply stage standardization rules
            if re.search(r'(?i)metastatic|stage\s+4|stage\s+IV', stage):
                standardized["Stage of Disease"] = "Stage 4"
            elif re.search(r'(?i)locally\s+advanced', stage):
                standardized["Stage of Disease"] = "Stage 3/4"
            elif re.search(r'(?i)early[\s-]?stage|stage\s+1|stage\s+I|stage\s+2|stage\s+II', stage):
                standardized["Stage of Disease"] = "Stage 1/2"
            else:
                standardized["Stage of Disease"] = stage
        
        # Copy other fields as is
        for key in result:
            if key not in standardized:
                standardized[key] = result[key]
                
        return standardized
    
    def _standardize_biomarker_fields(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize biomarker fields according to specification rules
        
        Args:
            result: Dictionary containing extracted biomarker fields
            
        Returns:
            Dict containing standardized biomarker fields
        """
        standardized = {}
        
        # Standardize Biomarker (Mutations)
        if "Biomarker (Mutations)" in result:
            biomarkers = result["Biomarker (Mutations)"]
            # Apply biomarker standardization rules
            biomarker_patterns = {
                r'(?i)ErbB2': 'HER2',
                r'(?i)PDL1': 'PD-L1',
                r'(?i)PD\s+L1': 'PD-L1',
                r'(?i)EGFR': 'EGFR',
                r'(?i)MSI-H\s+and\s+dMMR': 'dMMR/MSI-H',
                r'(?i)dMMR\s+and\s+MSI-H': 'dMMR/MSI-H',
                r'(?i)MSI-H/dMMR': 'dMMR/MSI-H',
                r'(?i)dMMR/MSI-H': 'dMMR/MSI-H',
            }
            for pattern, replacement in biomarker_patterns.items():
                biomarkers = re.sub(pattern, replacement, biomarkers)
            standardized["Biomarker (Mutations)"] = biomarkers
        
        # Copy other fields as is
        for key in result:
            if key not in standardized:
                standardized[key] = result[key]
                
        return standardized

    def _should_split_into_multiple_rows(self, trial_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> bool:
        """
        Determine if the trial should be split into multiple rows based on specific criteria
        
        Args:
            trial_data: Dictionary containing trial data
            analysis_result: Dictionary containing analysis results
            
        Returns:
            Boolean indicating whether the trial should be split into multiple rows
        """
        # Check for criteria that would require splitting
        
        # 1. Based on Combination Partners
        # If both mono and combo regimens are evaluated in the same trial
        if "Mono/Combo" in analysis_result:
            arms = trial_data.get("protocolSection", {}).get("armsInterventionsModule", {}).get("armGroups", [])
            has_mono = False
            has_combo = False
            
            # Check if there are explicit mono and combo arms
            for arm in arms:
                arm_title = arm.get("title", "").lower()
                arm_desc = arm.get("description", "").lower()
                
                if "monotherapy" in arm_title or "monotherapy" in arm_desc or "single agent" in arm_title or "single agent" in arm_desc:
                    has_mono = True
                
                if "combination" in arm_title or "combination" in arm_desc or " + " in arm_title or " plus " in arm_title:
                    has_combo = True
            
            if has_mono and has_combo:
                return True
                
            # Check if multiple combination partners are mentioned
            if analysis_result.get("Mono/Combo") == "Combo" and "," in analysis_result.get("Combination Partner", ""):
                return True
        
        # 2. Based on Line of Therapy (LOT)
        # If different LOTs are evaluated within the same trial
        eligibility = trial_data.get("protocolSection", {}).get("eligibilityModule", {}).get("eligibilityCriteria", "")
        
        # Check for multiple LOT mentions
        lot_patterns = {
            "1L": r"(?i)treatment[\s-]?na[iï]ve|previously[\s-]?untreated|newly[\s-]?diagnosed|first[\s-]?line",
            "2L": r"(?i)second[\s-]?line|one\s+prior\s+therapy|1\s+prior\s+therapy",
            "2L+": r"(?i)third[\s-]?line|multiple\s+prior\s+therapies|refractory|relapsed|previously[\s-]?treated",
            "Adjuvant": r"(?i)adjuvant|post[\s-]?operative|post[\s-]?surgical",
            "Neoadjuvant": r"(?i)neoadjuvant|pre[\s-]?operative|pre[\s-]?surgical",
            "Maintenance": r"(?i)maintenance"
        }
        
        lot_mentions = []
        for lot, pattern in lot_patterns.items():
            if re.search(pattern, eligibility):
                lot_mentions.append(lot)
        
        if len(lot_mentions) > 1:
            return True
        
        # 3. Based on Patient Subgroup
        # If there are different sub-indications or cohorts
        if "cohort" in eligibility.lower() and ":" in eligibility:
            return True
        
        # 4. Based on ROA (Route of Administration)
        # If the same drug has been evaluated for different routes of administration
        interventions = trial_data.get("protocolSection", {}).get("armsInterventionsModule", {}).get("interventions", [])
        roa_set = set()
        
        for intervention in interventions:
            desc = intervention.get("description", "").lower()
            
            if "intravenous" in desc or "iv" in desc.split():
                roa_set.add("IV")
            if "subcutaneous" in desc or "sc" in desc.split():
                roa_set.add("SC")
            if "oral" in desc:
                roa_set.add("Oral")
            if "intratumoral" in desc or "it" in desc.split():
                roa_set.add("IT")
        
        if len(roa_set) > 1:
            return True
        
        return False
    
    def _split_into_multiple_rows(self, trial_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split the trial analysis into multiple rows based on specific criteria
        
        Args:
            trial_data: Dictionary containing trial data
            analysis_result: Dictionary containing analysis results
            
        Returns:
            List of dictionaries, each representing a row in the analysis
        """
        rows = []
        
        # 1. Based on Combination Partners
        if "Mono/Combo" in analysis_result:
            arms = trial_data.get("protocolSection", {}).get("armsInterventionsModule", {}).get("armGroups", [])
            has_mono = False
            has_combo = False
            combo_partners = []
            
            # Check for mono and combo arms
            for arm in arms:
                arm_title = arm.get("title", "").lower()
                arm_desc = arm.get("description", "").lower()
                
                if "monotherapy" in arm_title or "monotherapy" in arm_desc or "single agent" in arm_title or "single agent" in arm_desc:
                    has_mono = True
                
                if "combination" in arm_title or "combination" in arm_desc:
                    has_combo = True
                    # Extract potential combination partners
                    if "+" in arm_title:
                        parts = arm_title.split("+")
                        if len(parts) > 1:
                            combo_partners.append(parts[1].strip())
            
            # If both mono and combo are present, create separate rows
            if has_mono and has_combo:
                # Create mono row
                mono_row = analysis_result.copy()
                mono_row["Mono/Combo"] = "Mono"
                mono_row["Combination Partner"] = "NA"
                mono_row["MoA of Combination"] = "NA"
                mono_row["Experimental Regimen"] = mono_row.get("Primary Drug", "")
                mono_row["MoA of Experimental Regimen"] = mono_row.get("Primary Drug MoA", "")
                rows.append(mono_row)
                
                # Create combo row(s)
                if combo_partners:
                    for partner in combo_partners:
                        combo_row = analysis_result.copy()
                        combo_row["Mono/Combo"] = "Combo"
                        combo_row["Combination Partner"] = partner
                        # For simplicity, we're not determining the MoA of the combination partner here
                        combo_row["Experimental Regimen"] = f"{combo_row.get('Primary Drug', '')} + {partner}"
                        rows.append(combo_row)
                else:
                    # Generic combo row if we couldn't extract specific partners
                    combo_row = analysis_result.copy()
                    combo_row["Mono/Combo"] = "Combo"
                    rows.append(combo_row)
                
                return rows
            
            # Check for multiple combination partners
            if analysis_result.get("Mono/Combo") == "Combo" and "," in analysis_result.get("Combination Partner", ""):
                partners = [p.strip() for p in analysis_result.get("Combination Partner", "").split(",")]
                for partner in partners:
                    combo_row = analysis_result.copy()
                    combo_row["Combination Partner"] = partner
                    combo_row["Experimental Regimen"] = f"{combo_row.get('Primary Drug', '')} + {partner}"
                    rows.append(combo_row)
                return rows
        
        # 2. Based on Line of Therapy (LOT)
        eligibility = trial_data.get("protocolSection", {}).get("eligibilityModule", {}).get("eligibilityCriteria", "")
        
        # Check for multiple LOT mentions
        lot_patterns = {
            "1L": r"(?i)treatment[\s-]?na[iï]ve|previously[\s-]?untreated|newly[\s-]?diagnosed|first[\s-]?line",
            "2L": r"(?i)second[\s-]?line|one\s+prior\s+therapy|1\s+prior\s+therapy",
            "2L+": r"(?i)third[\s-]?line|multiple\s+prior\s+therapies|refractory|relapsed|previously[\s-]?treated",
            "Adjuvant": r"(?i)adjuvant|post[\s-]?operative|post[\s-]?surgical",
            "Neoadjuvant": r"(?i)neoadjuvant|pre[\s-]?operative|pre[\s-]?surgical",
            "Maintenance": r"(?i)maintenance"
        }
        
        lot_mentions = []
        for lot, pattern in lot_patterns.items():
            if re.search(pattern, eligibility):
                lot_mentions.append(lot)
        
        if len(lot_mentions) > 1:
            for lot in lot_mentions:
                lot_row = analysis_result.copy()
                lot_row["Line of Therapy"] = lot
                rows.append(lot_row)
            return rows
        
        # 3. Based on ROA (Route of Administration)
        interventions = trial_data.get("protocolSection", {}).get("armsInterventionsModule", {}).get("interventions", [])
        roa_map = {}
        
        for intervention in interventions:
            desc = intervention.get("description", "").lower()
            name = intervention.get("name", "")
            
            if "intravenous" in desc or "iv" in desc.split():
                roa_map["Intravenous (IV)"] = name
            if "subcutaneous" in desc or "sc" in desc.split():
                roa_map["Subcutaneous (SC)"] = name
            if "oral" in desc:
                roa_map["Oral"] = name
            if "intratumoral" in desc or "it" in desc.split():
                roa_map["Intratumoral (IT)"] = name
        
        if len(roa_map) > 1:
            for roa, drug in roa_map.items():
                roa_row = analysis_result.copy()
                roa_row["Primary Drug ROA"] = roa
                rows.append(roa_row)
            return rows
        
        # If no splitting criteria matched, return the original row
        if not rows:
            rows.append(analysis_result)
        
        return rows

    def _extract_geography(self, trial_data: Dict[str, Any]) -> str:
        """
        Extract and classify the trial geography based on location countries
        
        Args:
            trial_data: Dictionary containing trial data
            
        Returns:
            String representing the geography classification
        """
        # Get location countries
        locations = trial_data.get("protocolSection", {}).get("contactsLocationsModule", {}).get("locations", [])
        countries = set()
        
        for location in locations:
            country = location.get("country", "")
            if country:
                countries.add(country)
        
        # Classify geography according to rules
        us_present = any(country in ["United States", "USA", "U.S.A."] for country in countries)
        
        eu_countries = {
            "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czechia", "Czech Republic", 
            "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary", 
            "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands", 
            "Poland", "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden"
        }
        eu_present = any(country in eu_countries for country in countries)
        
        japan_present = "Japan" in countries
        china_present = any(country in ["China", "Taiwan"] for country in countries)
        
        # Apply classification rules
        if us_present and eu_present and japan_present and china_present:
            return "Global"
        elif eu_present and (len(countries) > 1):
            return "International"
        elif china_present and len(countries) <= 2 and all("china" in c.lower() or "taiwan" in c.lower() for c in countries):
            return "China only"
        else:
            # Default to listing the countries
            return ", ".join(sorted(countries)) if countries else "Not Available"
    
    def _extract_sponsor_type(self, trial_data: Dict[str, Any]) -> str:
        """
        Classify the sponsor type based on sponsor and collaborator information
        
        Args:
            trial_data: Dictionary containing trial data
            
        Returns:
            String representing the sponsor type classification
        """
        # Get sponsor and collaborator information
        sponsor_info = trial_data.get("protocolSection", {}).get("identificationModule", {})
        sponsor = sponsor_info.get("organization", {}).get("fullName", "")
        collaborators = sponsor_info.get("collaborators", [])
        collaborator_names = [c.get("name", "") for c in collaborators]
        
        # Define patterns for industry vs academic
        industry_patterns = [
            r'(?i)pharma', r'(?i)therapeutics', r'(?i)biotech', r'(?i)inc\.?', 
            r'(?i)corp\.?', r'(?i)ltd\.?', r'(?i)limited', r'(?i)gmbh', 
            r'(?i)biosciences', r'(?i)medicines', r'(?i)labs'
        ]
        
        academic_patterns = [
            r'(?i)university', r'(?i)college', r'(?i)institute', r'(?i)hospital', 
            r'(?i)medical center', r'(?i)clinic', r'(?i)foundation', r'(?i)society', 
            r'(?i)association', r'(?i)center for', r'(?i)ministry of', r'(?i)department of'
        ]
        
        # Check if sponsor is industry
        sponsor_is_industry = any(re.search(pattern, sponsor) for pattern in industry_patterns)
        sponsor_is_academic = any(re.search(pattern, sponsor) for pattern in academic_patterns)
        
        # Check if any collaborator is industry
        collab_is_industry = any(
            any(re.search(pattern, collab) for pattern in industry_patterns) 
            for collab in collaborator_names
        )
        
        # Check if any collaborator is academic
        collab_is_academic = any(
            any(re.search(pattern, collab) for pattern in academic_patterns) 
            for collab in collaborator_names
        )
        
        # Apply classification rules
        if (sponsor_is_industry and not sponsor_is_academic) and (not collab_is_academic):
            return "Industry Only"
        elif (sponsor_is_academic and not sponsor_is_industry) and (not collab_is_industry):
            return "Academic Only"
        elif (sponsor_is_industry and collab_is_academic) or (sponsor_is_academic and collab_is_industry):
            return "Industry-Academic Collaboration"
        else:
            # Default case
            if sponsor_is_industry:
                return "Industry Only"
            elif sponsor_is_academic:
                return "Academic Only"
            else:
                return "Not Determined"
    
    def _extract_developer(self, trial_data: Dict[str, Any]) -> str:
        """
        Extract the developer of the primary drug based on sponsor and collaborator information
        
        Args:
            trial_data: Dictionary containing trial data
            
        Returns:
            String representing the developer
        """
        # Get sponsor and collaborator information
        sponsor_info = trial_data.get("protocolSection", {}).get("identificationModule", {})
        sponsor = sponsor_info.get("organization", {}).get("fullName", "")
        collaborators = sponsor_info.get("collaborators", [])
        collaborator_names = [c.get("name", "") for c in collaborators]
        
        # Define patterns for pharma companies
        pharma_patterns = [
            r'(?i)pharma', r'(?i)therapeutics', r'(?i)biotech', r'(?i)biosciences', 
            r'(?i)medicines', r'(?i)labs'
        ]
        
        # Check if sponsor is a pharma company
        sponsor_is_pharma = any(re.search(pattern, sponsor) for pattern in pharma_patterns)
        
        # Check if any collaborator is a pharma company
        collab_is_pharma = any(
            any(re.search(pattern, collab) for pattern in pharma_patterns) 
            for collab in collaborator_names
        )
        
        # Apply acquisition mapping
        acquisition_map = {
            "Seagen": "Pfizer",
            "Mirati Therapeutics": "BMS",
            "BioNTech SE": "BMS",
            "Fusion Pharma": "AstraZeneca",
            "Genentech": "Roche"
        }
        
        # Check for acquisitions in sponsor
        for original, acquired_by in acquisition_map.items():
            if original.lower() in sponsor.lower():
                return acquired_by
        
        # Check for acquisitions in collaborators
        for collab in collaborator_names:
            for original, acquired_by in acquisition_map.items():
                if original.lower() in collab.lower():
                    return acquired_by
        
        # Return sponsor if it's a pharma company
        if sponsor_is_pharma:
            return sponsor
        
        # Return first pharma collaborator
        for collab in collaborator_names:
            if any(re.search(pattern, collab) for pattern in pharma_patterns):
                return collab
        
        # Default
        return "Not Determined"
    
    def _extract_history_of_changes(self, trial_data: Dict[str, Any]) -> str:
        """
        Extract and summarize the history of changes for the trial
        
        Args:
            trial_data: Dictionary containing trial data
            
        Returns:
            String summarizing the history of changes
        """
        # Get study history information
        protocol_section = trial_data.get("protocolSection", {})
        status_module = trial_data.get("statusModule", {})
        
        # Check for status changes
        status_history = status_module.get("statusVerifiedDate", "")
        status = status_module.get("overallStatus", "")
        
        # Check for date changes
        start_date = protocol_section.get("datesSection", {}).get("startDate", "")
        completion_date = protocol_section.get("datesSection", {}).get("primaryCompletionDate", "")
        
        # Look for changes in study design
        design_changes = []
        
        # Check for changes in eligibility criteria
        eligibility = protocol_section.get("eligibilityModule", {}).get("eligibilityCriteria", "")
        if "amended" in eligibility.lower() or "revised" in eligibility.lower() or "modified" in eligibility.lower():
            design_changes.append("Eligibility criteria modified")
        
        # Check for changes in outcome measures
        outcomes = protocol_section.get("outcomesModule", {})
        if outcomes:
            primary_outcomes = outcomes.get("primaryOutcomes", [])
            for outcome in primary_outcomes:
                if "changed" in outcome.get("description", "").lower() or "modified" in outcome.get("description", "").lower():
                    design_changes.append("Primary outcome measures modified")
                    break
        
        # Compile the history of changes
        changes = []
        if status_history:
            changes.append(f"Status verified on {status_history} as '{status}'")
        
        if start_date:
            changes.append(f"Study start date: {start_date}")
        
        if completion_date:
            changes.append(f"Primary completion date: {completion_date}")
        
        changes.extend(design_changes)
        
        return "; ".join(changes) if changes else "No significant changes documented"

    def analyze_trial_with_web_search(self, nct_id: str, json_file_path: Optional[str] = None) -> AnalysisResult:
        """
        Analyze a clinical trial using o3 reasoning model with web search integration
        
        Args:
            nct_id: NCT ID of the trial
            json_file_path: Optional path to JSON file
            
        Returns:
            AnalysisResult containing extracted fields and analysis results
        """
        # Get trial data
        if json_file_path:
            trial_data = self.load_trial_data_from_file(json_file_path)
        else:
            trial_data = self.fetch_trial_data(nct_id)
            
        if not trial_data:
            return AnalysisResult(
                nct_id=nct_id,
                analysis_timestamp=datetime.now().isoformat(),
                model_used=self.model,
                analysis_method="web_search_error",
                primary_drug="Error: Could not load trial data"
            )
        
        # Create a structured prompt with clear instructions
        structured_prompt = f"""
        Analyze the following clinical trial data and extract key information.
        Use web search to find additional context about the drugs, mechanisms, and indications.
        
        NCT ID: {nct_id}
        
        Trial Data:
        {json.dumps(trial_data, indent=2)[:5000]}
        
        Extract comprehensive information about:
        1. Primary Drug and its properties (MoA, target, modality, ROA)
        2. Clinical aspects (indication, line of therapy, histology)
        3. Biomarkers (mutations, stratification, wildtype)
        4. Trial design and status
        
        Return your analysis as a detailed JSON object with all fields from the specification.
        """
        
        # Make API call with web search tool
        try:
            content = self._make_api_call(
                prompt=structured_prompt, 
                max_tokens=3000,
                tools=[{"type": "web_search_preview"}]
            )
            
            # Parse response
            result_dict = self._parse_json_response(content)
            
            # Add metadata
            result_dict.update({
                "nct_id": nct_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "model_used": self.model,
                "analysis_method": "web_search_enhanced"
            })
            
            # Return as Pydantic model
            return AnalysisResult(**result_dict)
            
        except Exception as e:
            logger.error(f"Error in web search analysis: {e}")
            return AnalysisResult(
                nct_id=nct_id,
                analysis_timestamp=datetime.now().isoformat(),
                model_used=self.model,
                analysis_method="web_search_error",
                primary_drug=f"Error: {str(e)}"
            )

    def analyze_trial_async(self, nct_id: str, webhook_url: str, json_file_path: Optional[str] = None) -> str:
        """
        Analyze a clinical trial asynchronously using background processing and webhooks
        
        Args:
            nct_id: NCT ID of the trial
            webhook_url: URL to send webhook notification when analysis completes
            json_file_path: Optional path to JSON file
            
        Returns:
            String with job ID for tracking
        """
        # Get trial data
        if json_file_path:
            trial_data = self.load_trial_data_from_file(json_file_path)
        else:
            trial_data = self.fetch_trial_data(nct_id)
            
        if not trial_data:
            return f"Error: Could not load trial data for {nct_id}"
        
        # Create a structured prompt with clear instructions
        structured_prompt = f"""
        Analyze the following clinical trial data and extract key information:
        
        NCT ID: {nct_id}
        
        Trial Data:
        {json.dumps(trial_data, indent=2)[:10000]}
        
        Extract the following fields (use 'N/A' if not available):
        1. Primary Drug: The main investigational drug being tested
        2. Primary Drug MoA: Mechanism of action (e.g., "Anti-PD-1", "PARP inhibitor")
        3. Primary Drug Target: Target molecule or pathway
        4. Primary Drug Modality: Type of drug (e.g., "Monoclonal antibody", "Small molecule")
        5. Indication: Disease or condition being treated
        6. Line of Therapy: Treatment line (e.g., "1L", "2L+")
        7. Biomarker (Mutations): Any biomarker mutations relevant to the trial
        8. Biomarker Stratification: How biomarkers are used for stratification
        9. Biomarker (Wildtype): Any wildtype biomarkers relevant to the trial
        10. Histology: Tissue type or histological classification
        11. Prior Treatment: Required previous treatments
        12. Stage of Disease: Disease stage for eligibility
        
        Return your analysis as a JSON object with these field names.
        """
        
        # Make API call with background processing and webhook
        try:
            job_id = self._make_api_call(
                prompt=structured_prompt,
                max_tokens=2000,
                background=True,
                webhook_url=webhook_url
            )
            
            return job_id
            
        except Exception as e:
            logger.error(f"Error in async analysis: {e}")
            return f"Error starting async analysis: {str(e)}"

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