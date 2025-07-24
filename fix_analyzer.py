import re

# Read the backup file
with open('src/analysis/clinical_trial_analyzer_reasoning_backup.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix indentation issues in analyze_clinical_fields_reasoning and analyze_biomarker_fields_reasoning methods
content = content.replace('    def analyze_clinical_fields_reasoning', 'def analyze_clinical_fields_reasoning')
content = content.replace('    def analyze_biomarker_fields_reasoning', 'def analyze_biomarker_fields_reasoning')

# Make sure the _validate_analysis_result method is present
validate_method = '''
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
                if not re.match(r'\\d{2}-\\d{2}-\\d{2}', date_value):
                    # Try to extract and reformat the date
                    date_match = re.search(r'(\\d{1,2})[/-](\\d{1,2})[/-](\\d{2,4})', date_value)
                    if date_match:
                        month, day, year = date_match.groups()
                        if len(year) == 4:
                            year = year[2:4]  # Extract last two digits for YY format
                        validated[date_field] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return validated
'''

# Check if _validate_analysis_result is already in the content
if '_validate_analysis_result' not in content:
    # Find a good place to insert it (after _standardize_biomarker_fields method)
    insert_pos = content.find('def _extract_geography')
    if insert_pos > 0:
        content = content[:insert_pos] + validate_method + content[insert_pos:]

# Write the fixed content to the new file
with open('src/analysis/clinical_trial_analyzer_reasoning.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed file created successfully!") 