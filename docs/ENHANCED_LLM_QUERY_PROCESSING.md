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

### 3. **Advanced Semantic Search with Reasoning Models**

The system now includes three levels of search sophistication:

1. **Basic Search**: Simple keyword matching in the database
2. **Smart Search**: LLM-enhanced query understanding with structured filters
3. **Reasoning Query**: Advanced semantic analysis using reasoning models (o3, o3-mini)

The reasoning query capability provides:
- Deep semantic understanding of complex queries
- Extraction of implicit relationships and concepts
- Comprehensive analysis of search intent
- Suggested follow-up queries
- Detailed explanations of search strategies

Example reasoning query:
```python
result = await server._reasoning_query({
    "query": "Compare Phase 3 trials for metastatic bladder cancer using different checkpoint inhibitors",
    "reasoning_model": "o3",
    "include_analysis": True,
    "format": "detailed"
})
```

### 4. **AI-Powered Trial Comparison**

New comparison capabilities allow for:
- Comparing multiple trials based on natural language criteria
- Identifying key similarities and differences
- Analyzing methodological differences
- Evaluating patient populations across trials
- Comparing endpoints and outcomes

Example comparison:
```python
result = await server._compare_analysis({
    "comparison_criteria": "Compare checkpoint inhibitor trials in bladder cancer",
    "auto_find_similar": True,
    "analysis_depth": "expert"
})
```

### 5. **Trend Analysis with AI Insights**

The system can now analyze trends across trials:
- Identify patterns in trial design and outcomes
- Group trials by meaningful parameters
- Generate insights about evolving research focus
- Provide recommendations for further investigation

Example trend analysis:
```python
result = await server._trend_analysis({
    "trend_query": "Analyze trends in checkpoint inhibitor trials for bladder cancer",
    "time_period": "last 5 years",
    "group_by": "drug",
    "include_insights": True
})
```

## Implementation Details

### Enhanced Prompting Strategy

The system uses carefully designed prompts that:
- Provide detailed context about clinical trials
- Include database schema information
- Specify expected output formats
- Give examples of correct responses
- Encourage extraction of synonyms and related terms

### Multi-Model Approach

Different models are used based on query complexity:
- **o3-mini**: Default for most queries (balance of speed and accuracy)
- **o3**: Used for expert-level analysis and complex comparisons

### Document Attachment

For complex queries, the system can attach the clinical trial analysis document to provide additional context to the model:

```python
def _analyze_query_with_document_attachment(self, query: str, model: str) -> Dict[str, Any]:
    """Analyze query using o3 model with document attachment for enhanced understanding"""
    # Upload document and create API call with attachment
    file_id = self._upload_document(doc_content, "clinical_trial_analysis_specs.md")
    response = self.openai_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": analysis_prompt},
                    {"type": "file", "file_id": file_id}
                ]
            }
        ],
        response_format={"type": "json_object"}
    )
```

### Robust Fallback Mechanisms

The system includes multiple fallback strategies:
- JSON parsing error handling
- Basic search when LLM is unavailable
- Pattern matching for common query types
- Default filters when extraction fails

## Usage Examples

### Basic Smart Search
```
Query: "Find diabetes trials with semaglutide"
```

### Advanced Reasoning Query
```
Query: "What are the key differences between pembrolizumab and nivolumab trials in advanced NSCLC with PD-L1 expression?"
```

### Comparative Analysis
```
Query: "Compare the efficacy endpoints in Phase 3 trials of PARP inhibitors for ovarian cancer maintenance therapy"
```

### Trend Analysis
```
Query: "How have inclusion criteria for Alzheimer's disease trials evolved over the past decade?"
``` 