-- Clear All Supabase Data Script
-- Run this in your Supabase SQL Editor
-- This will DELETE all data from the tables

DELETE FROM analysis_metadata;
DELETE FROM biomarker_info;
DELETE FROM clinical_info;
DELETE FROM drug_info;
DELETE FROM clinical_trials;

-- Verify tables are empty
SELECT 'analysis_metadata' as table_name, count(*) FROM analysis_metadata
UNION ALL
SELECT 'biomarker_info', count(*) FROM biomarker_info
UNION ALL
SELECT 'clinical_info', count(*) FROM clinical_info
UNION ALL
SELECT 'drug_info', count(*) FROM drug_info
UNION ALL
SELECT 'clinical_trials', count(*) FROM clinical_trials; 