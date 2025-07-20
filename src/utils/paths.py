#!/usr/bin/env python3
"""
Path Constants for Clinical Trial Analysis System
Standardizes path handling across the codebase
"""

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"

# Data paths
CACHE_DIR = DATA_DIR / "cache"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

# Database paths
CLINICAL_TRIALS_DB = PROCESSED_DIR / "clinical_trials.db"
RESULTS_DB = PROCESSED_DIR / "trial_analysis_results.db"

# Config paths
CONFIG_DIR = BASE_DIR / "config"
DOCS_DIR = BASE_DIR / "docs"
TESTS_DIR = BASE_DIR / "tests"

# Ensure directories exist
def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        CACHE_DIR,
        PROCESSED_DIR,
        RAW_DIR,
        CONFIG_DIR,
        DOCS_DIR,
        TESTS_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Initialize directories
ensure_directories()

# Path validation
def validate_paths():
    """Validate that all required paths exist and are accessible"""
    issues = []
    
    # Check if directories exist
    for name, path in [
        ("Cache Directory", CACHE_DIR),
        ("Processed Directory", PROCESSED_DIR),
        ("Raw Directory", RAW_DIR),
        ("Config Directory", CONFIG_DIR),
        ("Docs Directory", DOCS_DIR),
        ("Tests Directory", TESTS_DIR)
    ]:
        if not path.exists():
            issues.append(f"{name} does not exist: {path}")
        elif not path.is_dir():
            issues.append(f"{name} is not a directory: {path}")
    
    # Check if databases exist (optional)
    if not CLINICAL_TRIALS_DB.exists():
        issues.append(f"Clinical trials database not found: {CLINICAL_TRIALS_DB}")
    
    if not RESULTS_DB.exists():
        issues.append(f"Results database not found: {RESULTS_DB}")
    
    return issues

# Path utilities
def get_relative_path(from_file: str, to_path: Path) -> Path:
    """Get relative path from a file to a target path"""
    from_path = Path(from_file).parent
    return to_path.relative_to(from_path)

def get_cache_file(filename: str) -> Path:
    """Get path to a cache file"""
    return CACHE_DIR / filename

def get_processed_file(filename: str) -> Path:
    """Get path to a processed file"""
    return PROCESSED_DIR / filename

def get_raw_file(filename: str) -> Path:
    """Get path to a raw file"""
    return RAW_DIR / filename

# Export all paths for easy access
__all__ = [
    'BASE_DIR',
    'SRC_DIR', 
    'DATA_DIR',
    'CACHE_DIR',
    'PROCESSED_DIR',
    'RAW_DIR',
    'CLINICAL_TRIALS_DB',
    'RESULTS_DB',
    'CONFIG_DIR',
    'DOCS_DIR',
    'TESTS_DIR',
    'ensure_directories',
    'validate_paths',
    'get_relative_path',
    'get_cache_file',
    'get_processed_file',
    'get_raw_file'
] 