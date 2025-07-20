# Database components package
from .clinical_trial_database import ClinicalTrialDatabase

# Import populate function only if needed
try:
    from .populate_clinical_trials import populate_database
    __all__ = [
        'ClinicalTrialDatabase',
        'populate_database'
    ]
except ImportError:
    __all__ = [
        'ClinicalTrialDatabase'
    ] 