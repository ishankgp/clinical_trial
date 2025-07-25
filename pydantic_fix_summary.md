# Pydantic Model Compatibility Fix

## Issue

The UI code in `src/ui/app.py` was trying to access Pydantic model objects as if they were dictionaries, leading to the following error:

```
AttributeError: 'AnalysisResult' object has no attribute 'keys'
```

This occurred because we updated the `clinical_trial_analyzer_reasoning.py` to use Pydantic models for structured output, but didn't update the UI code to handle these models.

## Initial Solution

Our first approach was to convert Pydantic models to dictionaries using `model_dump()` or `dict()` methods:

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

However, this approach had issues with field processing and data loss during conversion.

## Improved Solution

We improved the solution by directly accessing Pydantic model attributes instead of converting to dictionaries:

1. Added a helper function to get all fields from a Pydantic model:

```python
def get_fields_from_pydantic(obj):
    """Get all fields from a Pydantic model or dictionary"""
    if hasattr(obj, "__fields__"):
        # Pydantic v1
        return list(obj.__fields__.keys())
    elif hasattr(obj, "model_fields"):
        # Pydantic v2
        return list(obj.model_fields.keys())
    elif isinstance(obj, dict):
        # Dictionary
        return list(obj.keys())
    else:
        # Fallback
        return []
```

2. Added a helper function to get values from either Pydantic models or dictionaries:

```python
def get_value_from_obj(obj, field):
    """Get a value from either a Pydantic model or dictionary"""
    if hasattr(obj, field):
        # Pydantic model attribute
        return getattr(obj, field)
    elif isinstance(obj, dict) and field in obj:
        # Dictionary key
        return obj[field]
    else:
        # Not found
        return "N/A"
```

3. Updated the UI functions to use these helpers:
   - `display_analysis_results` now uses `get_fields_from_pydantic` and `get_value_from_obj`
   - `create_comparison_table` now uses the same approach for field discovery and value retrieval

## Benefits

1. **Direct Access**: Accesses Pydantic model attributes directly without conversion
2. **No Data Loss**: Preserves all field values without potential data loss during conversion
3. **Backward Compatibility**: Works with both Pydantic models and dictionaries
4. **Version Agnostic**: Compatible with both Pydantic v1 and v2
5. **Robust Field Discovery**: Uses internal Pydantic metadata to discover all fields

## Testing

The UI now successfully handles the Pydantic model objects returned by the `ClinicalTrialAnalyzerReasoning` class, properly displaying all fields and values without data loss or format issues. 