# Enhanced LLM-Based Query Processing

## Overview

The MCP implementation uses advanced LLM reasoning models for processing natural language queries instead of basic string matching. This provides much more intelligent and accurate query understanding for clinical trial searches.

## Key Improvements

### 1. **Advanced LLM Reasoning Integration**

**Before:** Basic string matching with limited patterns
```python
# Old approach - simple string matching
if "diabetes" in query.lower():
    filters["search_terms"] = ["diabetes"]
```

**After:** Sophisticated LLM reasoning with structured output
```python
# New approach - LLM reasoning with structured prompts
enhanced_prompt = f"""
You are an expert clinical trial search assistant. Analyze this natural language query and extract structured search parameters.

QUERY: "{query}"

DATABASE SCHEMA:
- nct_id: Trial identifier
- trial_name: Full trial name and description
- trial_phase: PHASE1, PHASE2, PHASE3, PHASE4
- trial_status: RECRUITING, COMPLETED, TERMINATED, etc.
- primary_drug: Main drug being tested
- indication: Disease or condition being treated
- line_of_therapy: First line, second line, etc.
- patient_enrollment: Number of participants
- sponsor: Company or institution name
- geography: Global, US, Europe, Asia, etc.

TASK: Extract search filters from the natural language query...

RESPONSE FORMAT: Return a JSON object with structured filters...
"""
```

### 2. **Comprehensive Query Understanding**

The enhanced system understands:

- **Disease/Indication Terms**: cancer, diabetes, heart disease, etc.
- **Drug Names**: semaglutide, pembrolizumab, checkpoint inhibitors, etc.
- **Trial Phases**: phase 1, phase 2, phase 3, etc.
- **Trial Status**: recruiting, completed, terminated, etc.
- **Sponsor Types**: industry, academic, government
- **Geographic Preferences**: US, Europe, Asia, global
- **Patient Population**: adults, children, specific age groups
- **Treatment Lines**: first line, second line, etc.
- **Enrollment Size**: large trials, small trials, specific numbers
- **Time Periods**: recent trials, ongoing trials, completed trials

### 3. **Structured Output Format**

The LLM returns structured JSON with:

```json
{
    "filters": {
        "primary_drug": "extracted drug name or null",
        "indication": "extracted disease/indication or null",
        "trial_phase": "PHASE1/PHASE2/PHASE3/PHASE4 or null",
        "trial_status": "RECRUITING/COMPLETED/etc or null",
        "sponsor": "extracted sponsor name or null",
        "line_of_therapy": "extracted therapy line or null",
        "biomarker": "extracted biomarker terms or null",
        "enrollment_min": number or null,
        "enrollment_max": number or null,
        "geography": "extracted geography or null"
    },
    "query_intent": "Brief description of what the user is looking for",
    "search_strategy": "How to approach this search",
    "confidence_score": 0.0-1.0
}
```

### 4. **Enhanced Fallback Processing**

When LLM processing fails, the system uses sophisticated string processing:

- **Pattern Matching**: 50+ disease patterns, 30+ drug patterns
- **Regex Extraction**: Numeric values, NCT IDs, enrollment numbers
- **Context Understanding**: "large trials" → enrollment_min: 100
- **Synonym Recognition**: "ozempic" → "semaglutide", "keytruda" → "pembrolizumab"

### 5. **Confidence Scoring**

The system provides confidence scores to help users understand query quality:

- **High Confidence (0.7-1.0)**: Clear, well-structured queries
- **Medium Confidence (0.5-0.7)**: Ambiguous or complex queries
- **Low Confidence (0.0-0.5)**: Unclear or incomplete queries

## Example Queries and Results

### Complex Multi-Criteria Query
**Input:** "Find Phase 3 trials for metastatic bladder cancer using checkpoint inhibitors"

**LLM Output:**
```json
{
    "filters": {
        "indication": "metastatic bladder cancer",
        "trial_phase": "PHASE3",
        "primary_drug": "checkpoint inhibitors"
    },
    "query_intent": "User wants Phase 3 clinical trials for metastatic bladder cancer that use checkpoint inhibitors",
    "confidence_score": 0.95
}
```

### Geographic and Status Query
**Input:** "Show me recruiting diabetes trials with semaglutide in the US"

**LLM Output:**
```json
{
    "filters": {
        "indication": "diabetes",
        "primary_drug": "semaglutide",
        "trial_status": "RECRUITING",
        "geography": "US"
    },
    "query_intent": "User wants currently recruiting diabetes trials using semaglutide in the United States",
    "confidence_score": 0.92
}
```

## Benefits

### 1. **Improved Accuracy**
- LLM reasoning understands context and intent
- Better handling of complex, multi-part queries
- Reduced false positives and negatives

### 2. **Enhanced User Experience**
- Natural language queries work more reliably
- Better search results with higher relevance
- Clear feedback on query understanding

### 3. **Robust Fallback**
- System works even when LLM is unavailable
- Sophisticated string processing as backup
- Graceful degradation of functionality

## Testing

Run the enhanced query processing test:

```bash
python tests/test_enhanced_query_processing.py
```

This test validates:
- LLM-based query parsing accuracy
- Fallback processing reliability
- Confidence scoring accuracy
- Filter extraction completeness

## Configuration

### Required Environment Variables
```bash
OPENAI_API_KEY=your-openai-api-key
```

### Model Selection
- **Default**: `o4-mini` (fast reasoning model)
- **High Accuracy**: `gpt-4o` (most powerful reasoning model)
- **Fallback**: `gpt-4o-mini` (standard model) 