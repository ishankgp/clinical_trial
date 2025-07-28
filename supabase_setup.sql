-- Supabase SQL Script for Clinical Trial Tables
-- Run this in your Supabase SQL Editor

-- Create clinical_trials table
CREATE TABLE IF NOT EXISTS clinical_trials (
    id BIGSERIAL PRIMARY KEY,
    nct_id TEXT UNIQUE NOT NULL,
    trial_name TEXT,
    trial_phase TEXT,
    trial_status TEXT,
    patient_enrollment INTEGER,
    sponsor TEXT,
    primary_endpoints TEXT,
    secondary_endpoints TEXT,
    inclusion_criteria TEXT,
    exclusion_criteria TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create drug_info table
CREATE TABLE IF NOT EXISTS drug_info (
    id BIGSERIAL PRIMARY KEY,
    trial_id BIGINT REFERENCES clinical_trials(id) ON DELETE CASCADE,
    primary_drug TEXT,
    drug_class TEXT,
    mechanism_of_action TEXT,
    dosage_form TEXT,
    dosage_schedule TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create clinical_info table
CREATE TABLE IF NOT EXISTS clinical_info (
    id BIGSERIAL PRIMARY KEY,
    trial_id BIGINT REFERENCES clinical_trials(id) ON DELETE CASCADE,
    indication TEXT,
    disease_area TEXT,
    patient_population TEXT,
    age_range TEXT,
    gender_eligibility TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_nct_id ON clinical_trials(nct_id);
CREATE INDEX IF NOT EXISTS idx_trial_phase ON clinical_trials(trial_phase);
CREATE INDEX IF NOT EXISTS idx_trial_status ON clinical_trials(trial_status);
CREATE INDEX IF NOT EXISTS idx_sponsor ON clinical_trials(sponsor);
CREATE INDEX IF NOT EXISTS idx_primary_drug ON drug_info(primary_drug);
CREATE INDEX IF NOT EXISTS idx_indication ON clinical_info(indication);

-- Enable Row Level Security (RLS)
ALTER TABLE clinical_trials ENABLE ROW LEVEL SECURITY;
ALTER TABLE drug_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical_info ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (adjust based on your security needs)
CREATE POLICY "Allow read access to all users" ON clinical_trials
    FOR SELECT USING (true);
    
CREATE POLICY "Allow read access to all users" ON drug_info
    FOR SELECT USING (true);
    
CREATE POLICY "Allow read access to all users" ON clinical_info
    FOR SELECT USING (true);

-- Create a function to get schema information
CREATE OR REPLACE FUNCTION get_schema_info()
RETURNS TABLE(table_name text, column_name text, data_type text) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.table_name::text,
        c.column_name::text,
        c.data_type::text
    FROM information_schema.tables t
    JOIN information_schema.columns c ON t.table_name = c.table_name
    WHERE t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_name, c.ordinal_position;
END;
$$ LANGUAGE plpgsql;
