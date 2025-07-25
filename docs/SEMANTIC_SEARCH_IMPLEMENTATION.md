# Semantic Search Implementation

## Overview

The clinical trial analyzer now features advanced semantic search capabilities using reasoning models. This implementation enables users to query the clinical trial database using natural language and receive highly relevant results with rich analysis.

## Key Features

### 1. Advanced Reasoning Query

The `reasoning_query` tool provides deep semantic understanding of complex queries about clinical trials. It uses OpenAI's reasoning models (o3 and o3-mini) to:

- Extract structured search parameters from natural language
- Analyze the intent and meaning behind queries
- Generate insights about search results
- Provide suggested follow-up questions
- Explain search strategies and relevance

Example usage:
```python
result = await server._reasoning_query({
    "query": "What are the key differences between pembrolizumab and nivolumab trials in advanced NSCLC with PD-L1 expression?",
    "reasoning_model": "o3",
    "include_analysis": True,
    "format": "detailed"
})
```

### 2. AI-Powered Trial Comparison

The `compare_analysis` tool allows users to compare multiple clinical trials based on natural language criteria. It:

- Finds relevant trials based on comparison criteria
- Identifies key similarities and differences
- Analyzes methodological approaches
- Evaluates patient populations
- Compares endpoints and outcomes
- Provides expert insights on trial design

Example usage:
```python
result = await server._compare_analysis({
    "comparison_criteria": "Compare checkpoint inhibitor trials in bladder cancer",
    "auto_find_similar": True,
    "analysis_depth": "expert"
})
```

### 3. Trend Analysis

The `trend_analysis` tool analyzes patterns and trends across clinical trials. It:

- Identifies emerging research patterns
- Groups trials by meaningful parameters
- Generates insights about evolving research focus
- Provides recommendations for further investigation
- Visualizes trends in trial design and outcomes

Example usage:
```python
result = await server._trend_analysis({
    "trend_query": "Analyze trends in checkpoint inhibitor trials for bladder cancer",
    "time_period": "last 5 years",
    "group_by": "drug",
    "include_insights": True
})
```

## Implementation Details

### Multi-Level Search Architecture

The system now implements a three-tiered search approach:

1. **Basic Search**: Simple keyword matching in the database
2. **Smart Search**: LLM-enhanced query understanding with structured filters
3. **Reasoning Query**: Advanced semantic analysis using reasoning models

### Enhanced Prompting Strategy

The implementation uses carefully designed prompts that:

- Provide detailed context about clinical trials
- Include database schema information
- Specify expected output formats
- Give examples of correct responses
- Encourage extraction of synonyms and related terms

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

### Multi-Model Approach

Different models are used based on query complexity:

- **o3-mini**: Default for most queries (balance of speed and accuracy)
- **o3**: Used for expert-level analysis and complex comparisons

### Robust Fallback Mechanisms

The system includes multiple fallback strategies:

- JSON parsing error handling
- Basic search when LLM is unavailable
- Pattern matching for common query types
- Default filters when extraction fails

## Usage Examples

### Basic Semantic Search

```
Query: "Find diabetes trials with semaglutide"
```

Response includes:
- Extracted search parameters
- Query intent analysis
- Confidence score
- Matching trials with details

### Complex Comparative Query

```
Query: "What are the key differences between pembrolizumab and nivolumab trials in advanced NSCLC with PD-L1 expression?"
```

Response includes:
- Detailed comparison of trial designs
- Analysis of patient populations
- Endpoint differences
- Efficacy and safety comparison
- Expert insights on trial differences

### Trend Analysis Query

```
Query: "How have inclusion criteria for Alzheimer's disease trials evolved over the past decade?"
```

Response includes:
- Trend analysis of inclusion criteria changes
- Identification of key shifts in trial design
- Biomarker adoption patterns
- Patient population evolution
- Recommendations for future research

## Testing

The semantic search functionality can be tested using:

```bash
python tests/test_semantic_search.py
```

This test validates:
- Basic and complex query handling
- Comparison analysis functionality
- Trend analysis capabilities
- Response quality and relevance

## Configuration

### Required Environment Variables

```bash
OPENAI_API_KEY=your-openai-api-key
```

### Model Selection

- **Default**: `o3-mini` (fast reasoning model)
- **High Accuracy**: `o3` (most powerful reasoning model)

## Future Enhancements

1. **Vector Search Integration**: Implement embedding-based vector search for even more accurate semantic matching
2. **Multi-Document Context**: Allow attaching multiple documents for enhanced context
3. **Interactive Refinement**: Enable interactive query refinement based on initial results
4. **Custom Domain Adaptation**: Fine-tune models on clinical trial terminology
5. **Visualization Integration**: Add automatic visualization generation for trend analysis 