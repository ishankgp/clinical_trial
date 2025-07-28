-- Final Supabase SQL Correction
-- Run this in your Supabase SQL Editor
-- This will add the missing 'investigator_qualification' column

ALTER TABLE clinical_trials
ADD COLUMN investigator_qualification TEXT;

-- Verify the column was added
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'clinical_trials'
ORDER BY ordinal_position; 