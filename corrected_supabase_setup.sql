-- Corrected Supabase SQL Script for Clinical Trial Tables
-- Run this in your Supabase SQL Editor
-- This will DELETE existing tables and recreate them with the correct schema

-- Drop existing tables if they exist
DROP TABLE IF EXISTS analysis_metadata;
DROP TABLE IF EXISTS biomarker_info;
DROP TABLE IF EXISTS clinical_info;
DROP TABLE IF EXISTS drug_info;
DROP TABLE IF EXISTS clinical_trials;

-- Create clinical_trials table with the correct schema
CREATE TABLE IF NOT EXISTS clinical_trials (
    id BIGSERIAL PRIMARY KEY,
    nct_id TEXT UNIQUE NOT NULL,
    trial_id TEXT,
    trial_name TEXT,
    trial_phase TEXT,
    trial_status TEXT,
    patient_enrollment INTEGER,
    sponsor TEXT,
    sponsor_type TEXT,
    developer TEXT,
    start_date TEXT,
    primary_completion_date TEXT,
    study_completion_date TEXT,
    primary_endpoints TEXT,
    secondary_endpoints TEXT,
    inclusion_criteria TEXT,
    exclusion_criteria TEXT,
    trial_countries TEXT,
    geography TEXT,
    investigator_name TEXT,
    investigator_designation TEXT,
    investigator_location TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create drug_info table
CREATE TABLE IF NOT EXISTS drug_info (
    id BIGSERIAL PRIMARY KEY,
    nct_id TEXT NOT NULL,
    primary_drug TEXT,
    primary_drug_moa TEXT,
    primary_drug_target TEXT,
    primary_drug_modality TEXT,
    primary_drug_roa TEXT,
    mono_combo TEXT,
    combination_partner TEXT,
    moa_of_combination TEXT,
    experimental_regimen TEXT,
    moa_of_experimental_regimen TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create clinical_info table
CREATE TABLE IF NOT EXISTS clinical_info (
    id BIGSERIAL PRIMARY KEY,
    nct_id TEXT NOT NULL,
    indication TEXT,
    line_of_therapy TEXT,
    histology TEXT,
    prior_treatment TEXT,
    stage_of_disease TEXT,
    patient_population TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create biomarker_info table
CREATE TABLE IF NOT EXISTS biomarker_info (
    id BIGSERIAL PRIMARY KEY,
    nct_id TEXT NOT NULL,
    biomarker_mutations TEXT,
    biomarker_stratification TEXT,
    biomarker_wildtype TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create analysis_metadata table
CREATE TABLE IF NOT EXISTS analysis_metadata (
    id BIGSERIAL PRIMARY KEY,
    nct_id TEXT NOT NULL,
    analysis_model TEXT,
    analysis_time REAL,
    quality_score REAL,
    total_fields INTEGER,
    valid_fields INTEGER,
    error_fields INTEGER,
    na_fields INTEGER,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security (RLS) and set policies
-- This allows anonymous users to read and write for the migration
ALTER TABLE clinical_trials ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anonymous access" ON clinical_trials FOR ALL USING (true) WITH CHECK (true);

ALTER TABLE drug_info ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anonymous access" ON drug_info FOR ALL USING (true) WITH CHECK (true);

ALTER TABLE clinical_info ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anonymous access" ON clinical_info FOR ALL USING (true) WITH CHECK (true);

ALTER TABLE biomarker_info ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anonymous access" ON biomarker_info FOR ALL USING (true) WITH CHECK (true);

ALTER TABLE analysis_metadata ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anonymous access" ON analysis_metadata FOR ALL USING (true) WITH CHECK (true);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_nct_id ON clinical_trials(nct_id);
CREATE INDEX IF NOT EXISTS idx_drug_nct_id ON drug_info(nct_id);
CREATE INDEX IF NOT EXISTS idx_clinical_nct_id ON clinical_info(nct_id);

-- Verify creation
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
ORDER BY table_name, ordinal_position; 