-- Fix Supabase RLS Policies for Data Insertion
-- Run this in your Supabase SQL Editor

-- Drop existing policies
DROP POLICY IF EXISTS "Allow read access to all users" ON clinical_trials;
DROP POLICY IF EXISTS "Allow read access to all users" ON drug_info;
DROP POLICY IF EXISTS "Allow read access to all users" ON clinical_info;

-- Create new policies that allow both read and insert
CREATE POLICY "Allow all operations for authenticated users" ON clinical_trials
    FOR ALL USING (true) WITH CHECK (true);
    
CREATE POLICY "Allow all operations for authenticated users" ON drug_info
    FOR ALL USING (true) WITH CHECK (true);
    
CREATE POLICY "Allow all operations for authenticated users" ON clinical_info
    FOR ALL USING (true) WITH CHECK (true);

-- Alternative: Create policies for anonymous access (for testing)
CREATE POLICY "Allow anonymous access" ON clinical_trials
    FOR ALL USING (true) WITH CHECK (true);
    
CREATE POLICY "Allow anonymous access" ON drug_info
    FOR ALL USING (true) WITH CHECK (true);
    
CREATE POLICY "Allow anonymous access" ON clinical_info
    FOR ALL USING (true) WITH CHECK (true);

-- Verify the policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check 
FROM pg_policies 
WHERE tablename IN ('clinical_trials', 'drug_info', 'clinical_info'); 