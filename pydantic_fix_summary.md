# Pydantic Model Compatibility Fix

## Issue

The UI code in `src/ui/app.py` was trying to access Pydantic model objects as if they were dictionaries, leading to the following error:

```
AttributeError: 'AnalysisResult' object has no attribute 'keys'
```

This occurred because we updated the `clinical_trial_analyzer_reasoning.py` to use Pydantic models for structured output, but didn't update the UI code to handle these models.

## Solution

1. Added a helper function to convert Pydantic models to dictionaries:

```python
def get_dict_from_pydantic(obj):
    """Convert a Pydantic model to a dictionary, handling both v1 and v2 versions"""
    if hasattr(obj, "model_dump"):
        # Pydantic v2
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        # Pydantic v1
        return obj.dict()
    else:
        # Not a Pydantic model
        return obj
```

2. Updated the `display_analysis_results` function to use this helper:

```python
# Convert Pydantic model to dict if needed
result_dict = get_dict_from_pydantic(result)
```

3. Updated the `create_comparison_table` function to use this helper:

```python
# Convert Pydantic model to dict if needed
result_dict = get_dict_from_pydantic(result["result"])
```

## Benefits

1. **Backward Compatibility**: The code now works with both Pydantic v1 and v2 models
2. **Forward Compatibility**: The code will continue to work with dictionary results from other analyzers
3. **Error Handling**: Gracefully handles non-Pydantic objects

## Testing

The UI now successfully handles the Pydantic model objects returned by the `ClinicalTrialAnalyzerReasoning` class, allowing for:

1. Displaying individual analysis results
2. Creating comparison tables across multiple models
3. Downloading results as CSV files 