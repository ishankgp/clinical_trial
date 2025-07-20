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

class ClinicalTrialAnalyzerReasoning:
    """
    Clinical Trial Analysis System using Reasoning Models
    Based on detailed specifications in GenAI_Case_Clinical_Trial_Analysis_PROMPT_ver1.00.docx.md
    """
    
    def __init__(self, openai_api_key: str, model: str = "o3-mini"):
        """Initialize the analyzer with OpenAI API key and reasoning model"""
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
        # Validate model choice - focus on reasoning models
        available_models = ["o3", "o3-mini", "gpt-4o", "gpt-4o-mini", "gpt-4"]
        if model not in available_models:
            print(f"Warning: Model '{model}' not in available models. Using 'o3-mini' instead.")
            self.model = "o3-mini"
        else:
            self.model = model
            
        print(f"Using reasoning model: {self.model}")
        print("Enhanced prompts based on detailed specifications...")
        
        # Check if model is a reasoning model
        reasoning_models = ["o3", "o3-mini"]
        if self.model in reasoning_models:
            print(f"✓ {self.model} is a reasoning model - excellent for complex analysis")
        else:
            print(f"⚠ {self.model} is not a reasoning model - consider using o3 or o3-mini for better results")
            
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"
        # Import paths using dynamic path resolution
        import sys
        utils_path = os.path.join(os.path.dirname(__file__), '..', 'utils')
        if utils_path not in sys.path:
            sys.path.append(utils_path)
        from paths import CACHE_DIR
        self.cache_dir = CACHE_DIR
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
    
    def analyze_drug_fields_reasoning(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze drug-related fields using reasoning model with detailed specifications"""
        
        protocol = trial_data.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        description = protocol.get("descriptionModule", {})
        conditions = protocol.get("conditionsModule", {})
        arms = protocol.get("armsInterventionsModule", {})
        
        prompt = f"""
        You are an expert clinical trial analyst. Analyze the following clinical trial information and extract drug-related fields according to the detailed specifications.

        CLINICAL TRIAL DATA:
        BRIEF TITLE: {identification.get("briefTitle", "")}
        OFFICIAL TITLE: {identification.get("officialTitle", "")}
        BRIEF SUMMARY: {description.get("briefSummary", "")}
        CONDITIONS: {conditions.get("conditions", [])}
        ARM GROUPS: {json.dumps(arms.get("armGroups", []), indent=2)}
        INTERVENTIONS: {json.dumps(arms.get("interventions", []), indent=2)}

        ANALYSIS RULES (from GenAI_Case_Clinical_Trial_Analysis_PROMPT_ver1.00.docx.md):

        1. PRIMARY DRUG:
           - Identify the primary investigational drug being tested (NOT active comparators)
           - Focus on the trial's main objective and evaluation focus
           - Exclude drugs used as active comparators (e.g., "vs chemo" or "Active Comparator")
           - Do not consider background therapies or standard-of-care agents as primary
           - In novel combinations, consider both drugs as primary (separate rows)
           - Standardize to generic drug name (e.g., "pembrolizumab" not "Keytruda")

        2. PRIMARY DRUG MoA:
           - Use standardized format: "Anti-[Target]", "[Target] inhibitor", "[Target] agonist"
           - Examples: "Anti-PD-1", "PARP inhibitor", "GLP-1 Receptor Agonist"
           - For antibodies: "Anti-[Target]" (e.g., "Anti-Nectin-4")
           - For small molecules: "[Target] inhibitor" (e.g., "EGFR inhibitor")
           - For bispecifics: "Anti-[Target] × [Target]" (e.g., "Anti-PD-1 × CTLA-4")

        3. PRIMARY DRUG TARGET:
           - Molecular target (e.g., "PD-1", "PARP", "GLP-1 Receptor")
           - Align with MoA (e.g., MoA: "Anti-Nectin-4" → Target: "Nectin-4")
           - Use target name only (no prefixes like "Anti-" or suffixes like "-inhibitor")

        4. PRIMARY DRUG MODALITY:
           - Standardize terminology:
             * "Antibody-drug conjugate" → "ADC"
             * "T-cell redirecting bispecific" → "T-cell engager"
             * "Chimeric antigen receptor T cell" → "CAR-T"
           - Use naming rules:
             * Drugs ending in -mab → "Monoclonal antibody"
             * Drugs ending in -tinib → "Small molecule"
             * Gene-altering drugs → "Gene therapy"
             * Radiolabeled ligands → "Radiopharmaceutical"
             * Cell-based therapies → "Cell therapy"

        5. PRIMARY DRUG ROA:
           - Route of administration (e.g., "Intravenous (IV)", "Oral", "Subcutaneous (SC)")
           - Do not infer unless clearly stated or supported by secondary reference
           - If multiple ROAs, profile each separately

        6. MONO/COMBO:
           - "Mono": Drug evaluated alone (not in combination)
           - "Combo": Drug evaluated in combination with one or more drugs
           - If both mono and combo evaluated, profile each separately
           - Do not include active comparators as combination therapy

        7. COMBINATION PARTNER:
           - List combination partners (use "NA" for mono)
           - Exclude active comparators
           - If multiple partners, separate with "+"
           - Standardize drug names

        8. MoA OF COMBINATION:
           - Mechanism of combination partners (use "NA" for mono)
           - Use same standardization as primary drug MoA
           - If multiple partners, separate with "+"

        9. EXPERIMENTAL REGIMEN:
           - Primary drug + combination partners
           - For mono: just primary drug name
           - For combo: "Primary Drug + Combination Partner"

        10. MoA OF EXPERIMENTAL REGIMEN:
            - Combined MoA of primary drug + combination partners
            - For mono: just primary drug MoA
            - For combo: "Primary MoA + Combination MoA"

        REASONING PROCESS:
        1. First, identify all experimental arms and active comparators
        2. Determine which drug is the primary investigational agent
        3. Analyze the drug's mechanism and properties
        4. Determine if it's evaluated as mono or combo therapy
        5. Extract combination partners if applicable
        6. Apply standardization rules consistently

        Return a JSON object with these exact field names: "Primary Drug", "Primary Drug MoA", "Primary Drug Target", "Primary Drug Modality", "Primary Drug ROA", "Mono/Combo", "Combination Partner", "MoA of Combination", "Experimental Regimen", "MoA of Experimental Regimen"
        """
        
        try:
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            # Add temperature only for models that support it
            if self.model != "o4-mini":
                request_params["temperature"] = 0.1
            
            # Use correct token parameter based on model
            if self.model in ["o3", "o3-mini", "o4-mini"]:
                request_params["max_completion_tokens"] = 1500
            else:
                request_params["max_completion_tokens"] = 1500
            
            # Add response_format only for supported models
            if self.model in ["gpt-4o", "gpt-4o-mini", "o4-mini"]:
                request_params["response_format"] = {"type": "json_object"}
            
            response = self.openai_client.chat.completions.create(**request_params)
            
            content = response.choices[0].message.content.strip()
            
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
    
    def analyze_clinical_fields_reasoning(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze clinical fields using reasoning model with detailed specifications"""
        
        protocol = trial_data.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        description = protocol.get("descriptionModule", {})
        conditions = protocol.get("conditionsModule", {})
        eligibility = protocol.get("eligibilityModule", {})
        
        prompt = f"""
        You are an expert clinical trial analyst. Analyze the following clinical trial information and extract clinical fields according to the detailed specifications.

        CLINICAL TRIAL DATA:
        BRIEF TITLE: {identification.get("briefTitle", "")}
        OFFICIAL TITLE: {identification.get("officialTitle", "")}
        BRIEF SUMMARY: {description.get("briefSummary", "")}
        CONDITIONS: {conditions.get("conditions", [])}
        ELIGIBILITY CRITERIA: {eligibility.get("eligibilityCriteria", "")}

        ANALYSIS RULES (from GenAI_Case_Clinical_Trial_Analysis_PROMPT_ver1.00.docx.md):

        1. INDICATION:
           - Primary disease indication (e.g., "Type 2 Diabetes (T2DM)", "Bladder Cancer")
           - Extract from Title, Official Title, Brief Summary, Conditions, Inclusion Criteria
           - Classify into primary indication and other indications if multiple
           - Use exact or closely mapped disease names as described in trial record

        2. LINE OF THERAPY:
           - Classify based on eligibility criteria and trial description:
             * "1L": Treatment-naive or previously untreated patients or Newly diagnosed
             * "2L": Patients treated with no more than 1 prior therapy
             * "2L+": Patients treated with ≥1 prior therapy, refractory/intolerant to SOC
             * "Adjuvant": Treatment given after primary therapy (typically surgery)
             * "Neoadjuvant": Treatment given before primary therapy
             * "Maintenance": Ongoing treatment after initial successful therapy
           - Look for keywords: "previously untreated", "prior therapy", "adjuvant", "neoadjuvant", "maintenance"

        3. HISTOLOGY:
           - Disease histology if specified (e.g., "Urothelial carcinoma", "Adenocarcinoma")
           - Look for keywords: carcinomas, adenocarcinoma, squamous cell carcinoma, etc.
           - Correlate with disease if exact histology not given

        4. PRIOR TREATMENT:
           - Previous therapies that participants must have received
           - Look for keywords: "previously failed", "progressed on", "refractory to", "prior treatment"
           - If no prior therapy required, tag as "treatment naive"
           - If unclear, tag as "NA"

        5. STAGE OF DISEASE:
           - Disease stage based on trial descriptions:
             * "Stage 4": If trial mentions "metastatic" or "advanced cancer"
             * "Stage 3/4": If trial mentions "locally advanced" or "locally advanced/metastatic"
             * "Stage 1/2": If trial refers to early-stage disease
           - Can also capture TNM staging if available

        6. PATIENT POPULATION:
           - Detailed patient population description
           - Consider disease stage, type, mutations, prior therapies
           - Create comprehensive description from eligibility criteria
           - Be specific about inclusion/exclusion criteria

        7. TRIAL NAME:
           - Trial acronym from orgStudyIdInfo or title
           - Extract from "Other Study ID Numbers" or trial title
           - Do not include study codes

        REASONING PROCESS:
        1. First, identify the primary disease indication from multiple sources
        2. Analyze eligibility criteria for line of therapy indicators
        3. Determine patient population characteristics
        4. Extract any specific histology or staging information
        5. Identify prior treatment requirements
        6. Create comprehensive patient population description

        Return a JSON object with these exact field names: "Indication", "Line of Therapy", "Histology", "Prior Treatment", "Stage of Disease", "Patient Population", "Trial Name"
        """
        
        try:
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            # Add temperature only for models that support it
            if self.model != "o4-mini":
                request_params["temperature"] = 0.1
            
            # Use correct token parameter based on model
            if self.model in ["o3", "o3-mini", "o4-mini"]:
                request_params["max_completion_tokens"] = 1200
            else:
                request_params["max_completion_tokens"] = 1200
            
            # Add response_format only for supported models
            if self.model in ["gpt-4o", "gpt-4o-mini", "o4-mini"]:
                request_params["response_format"] = {"type": "json_object"}
            
            response = self.openai_client.chat.completions.create(**request_params)
            
            content = response.choices[0].message.content.strip()
            
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
    
    def analyze_biomarker_fields_reasoning(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze biomarker fields using reasoning model with detailed specifications"""
        
        protocol = trial_data.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        description = protocol.get("descriptionModule", {})
        eligibility = protocol.get("eligibilityModule", {})
        outcomes = protocol.get("outcomesModule", {})
        
        prompt = f"""
        You are an expert clinical trial analyst. Analyze the following clinical trial information and extract biomarker fields according to the detailed specifications.

        CLINICAL TRIAL DATA:
        BRIEF TITLE: {identification.get("briefTitle", "")}
        OFFICIAL TITLE: {identification.get("officialTitle", "")}
        BRIEF SUMMARY: {description.get("briefSummary", "")}
        ELIGIBILITY CRITERIA: {eligibility.get("eligibilityCriteria", "")}
        PRIMARY OUTCOMES: {json.dumps(outcomes.get("primaryOutcomes", []), indent=2)}
        SECONDARY OUTCOMES: {json.dumps(outcomes.get("secondaryOutcomes", []), indent=2)}

        ANALYSIS RULES (from GenAI_Case_Clinical_Trial_Analysis_PROMPT_ver1.00.docx.md):

        1. BIOMARKER (MUTATIONS):
           - Extract all biomarkers mentioned in clinical trial
           - Look for keywords: mutation, amplification, expression, fusion, biomarkers, actionable molecular alteration, gene deletion, expressing antigen, gene/target positive
           - Common biomarkers: HER2, PD-L1, EGFR, HLA-A*02:01, PIK3CA, TROP2, MAGE-A4, MSI-H/dMMR, ALK, ROS1, BRAF, RET, MET, KRAS, Nectin-4, TP53, 5T4, MTAP, CD39, CD103, CD8+, B7-H3
           - Standardize format:
             * HER2 → HER2 (not "ErbB2")
             * PD-L1 → PD-L1 (not "PDL1" or "PD L1")
             * EGFR → EGFR (not "Epidermal Growth Factor Receptor")
             * Maintain symbols and punctuation: HLA-A*02:01
             * Group related variations: dMMR/MSI-H

        2. BIOMARKER STRATIFICATION:
           - Expression levels/thresholds mentioned in inclusion criteria
           - Common formats: CPS (Combined Positive Score), IHC scores (0, 1+, 2+, 3+), TPS (Tumor Proportion Score)
           - Examples: "PD-L1 CPS ≥10", "HER2 IHC 2+ or 3+", "EGFR expression ≥1%"
           - Capture exact levels as mentioned in trial

        3. BIOMARKER (WILDTYPE):
           - Wildtype biomarkers if specified
           - Look for keywords: "wild type", "non-mutated", "mutation-negative", "negative for [mutation]", "genomically unaltered", "lacking [mutation]", "[gene] negative by NGS/IHC/FISH/PCR"
           - Standardized format: "[Gene] wild-type" or "[Gene] [mutation]-negative"
           - Examples: "KRAS wild-type", "EGFR T790M-negative", "BRAF V600E-negative", "ALK-negative"

        REASONING PROCESS:
        1. Scan all text sources for biomarker mentions
        2. Identify specific mutations, expressions, or alterations
        3. Extract stratification criteria and thresholds
        4. Look for wildtype requirements
        5. Apply standardization rules consistently
        6. Use "Not Available" if no biomarkers found

        Return a JSON object with these exact field names: "Biomarker (Mutations)", "Biomarker Stratification", "Biomarker (Wildtype)". Use "Not Available" if not found.
        """
        
        try:
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            # Add temperature only for models that support it
            if self.model != "o4-mini":
                request_params["temperature"] = 0.1
            
            # Use correct token parameter based on model
            if self.model in ["o3", "o3-mini", "o4-mini"]:
                request_params["max_completion_tokens"] = 1000
            else:
                request_params["max_completion_tokens"] = 1000
            
            # Add response_format only for supported models
            if self.model in ["gpt-4o", "gpt-4o-mini", "o4-mini"]:
                request_params["response_format"] = {"type": "json_object"}
            
            response = self.openai_client.chat.completions.create(**request_params)
            
            content = response.choices[0].message.content.strip()
            
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
            logger.error(f"Error in biomarker analysis: {e}")
            return {
                "Biomarker (Mutations)": "Not Available",
                "Biomarker Stratification": "Not Available",
                "Biomarker (Wildtype)": "Not Available"
            }
    
    def analyze_trial(self, nct_id: str, json_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a clinical trial using reasoning models
        
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
        
        # Extract all fields using reasoning models
        result = {
            "nct_id": nct_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "model_used": self.model
        }
        
        # Extract basic fields
        basic_fields = self.extract_basic_fields(trial_data)
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
            
            # Use the reasoning model to analyze the query
            # Reasoning models have different parameter requirements
            if self.model in ["o3", "o3-mini"]:
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert clinical trial analyst. Extract structured information from natural language queries about clinical trials."},
                        {"role": "user", "content": reasoning_prompt}
                    ],
                    max_completion_tokens=1000
                )
            else:
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert clinical trial analyst. Extract structured information from natural language queries about clinical trials."},
                        {"role": "user", "content": reasoning_prompt}
                    ],
                    temperature=0.1,
                    max_completion_tokens=1000
                )
            
            # Parse the response
            analysis_text = response.choices[0].message.content
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_match:
                    analysis_json = json.loads(json_match.group())
                else:
                    # Fallback: create a basic structure
                    analysis_json = {
                        "filters": {},
                        "query_intent": "unknown",
                        "search_strategy": "basic search",
                        "relevant_fields": [],
                        "confidence_score": 0.5
                    }
                    
                    # Try to extract basic filters using simple parsing
                    query_lower = query.lower()
                    
                    # Extract common patterns
                    if "diabetes" in query_lower:
                        analysis_json["filters"]["indication"] = "diabetes"
                    if "cancer" in query_lower:
                        analysis_json["filters"]["indication"] = "cancer"
                    if "phase 1" in query_lower or "phase i" in query_lower:
                        analysis_json["filters"]["trial_phase"] = "PHASE1"
                    if "phase 2" in query_lower or "phase ii" in query_lower:
                        analysis_json["filters"]["trial_phase"] = "PHASE2"
                    if "phase 3" in query_lower or "phase iii" in query_lower:
                        analysis_json["filters"]["trial_phase"] = "PHASE3"
                    if "recruiting" in query_lower:
                        analysis_json["filters"]["trial_status"] = "RECRUITING"
                    if "completed" in query_lower:
                        analysis_json["filters"]["trial_status"] = "COMPLETED"
                    
                    analysis_json["query_intent"] = query
                    
            except json.JSONDecodeError:
                # Fallback analysis
                analysis_json = {
                    "filters": {},
                    "query_intent": query,
                    "search_strategy": "fallback search",
                    "relevant_fields": ["nct_id", "trial_name", "primary_drug", "indication"],
                    "confidence_score": 0.3
                }
            
            return analysis_json
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            return {
                "filters": {},
                "query_intent": query,
                "search_strategy": "error fallback",
                "relevant_fields": ["nct_id", "trial_name"],
                "confidence_score": 0.0,
                "error": str(e)
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