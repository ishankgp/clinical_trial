#!/usr/bin/env python3
"""
Test Supabase Integration
Tests the complete Supabase integration for clinical trial data
"""

import requests
import json
import time

def test_supabase_integration():
    """Test the complete Supabase integration"""
    
    supabase_url = "https://hvmazsmkfzjwmrbdilfq.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2bWF6c21rZnpqd21yYmRpbGZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2OTI5OTMsImV4cCI6MjA2OTI2ODk5M30.rajuDXjG_KSQhL968L8FRXgxRFgzIIuwo25pZ6ndoSU"
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }

    # Pre-test cleanup
    print("🧹 Cleaning up any previous test data...")
    requests.delete(f"{supabase_url}/rest/v1/clinical_trials?nct_id=eq.NCT99999999", headers=headers)
    
    print("🏥 Testing Supabase Integration")
    print("=" * 50)
    
    # Test 1: Insert a test trial
    print("\n1. Testing trial insertion...")
    test_trial = {
        'nct_id': 'NCT99999999',
        'trial_name': 'Test Integration Trial',
        'trial_phase': 'Phase 1',
        'trial_status': 'Recruiting',
        'patient_enrollment': 50,
        'sponsor': 'Test Sponsor',
        'primary_endpoints': 'Safety assessment',
        'secondary_endpoints': 'Efficacy evaluation',
        'inclusion_criteria': 'Age 18-75',
        'exclusion_criteria': 'Pregnancy, severe illness'
    }
    
    response = requests.post(
        f"{supabase_url}/rest/v1/clinical_trials",
        headers=headers,
        json=test_trial
    )
    
    if response.status_code == 201:
        print("✅ Test trial inserted successfully")
        try:
            trial_data = response.json()
            if trial_data:
                trial_id = trial_data[0]['id']
            else:
                print("⚠️ No data returned on insert, which is acceptable.")
                trial_id = None # Can't get the ID, but that's okay for this test
        except requests.exceptions.JSONDecodeError:
            print("⚠️ Could not decode JSON from insert response, but proceeding.")
            trial_id = None
    else:
        print(f"❌ Failed to insert test trial: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Test 2: Query the trial
    print("\n2. Testing trial query...")
    response = requests.get(
        f"{supabase_url}/rest/v1/clinical_trials?nct_id=eq.NCT99999999",
        headers=headers
    )
    
    if response.status_code == 200:
        trials = response.json()
        if trials:
            print("✅ Test trial retrieved successfully")
            print(f"   Trial name: {trials[0].get('trial_name')}")
        else:
            print("❌ Test trial not found")
            return False
    else:
        print(f"❌ Failed to query trial: {response.status_code}")
        return False
    
    # Test 3: Search trials
    print("\n3. Testing trial search...")
    response = requests.get(
        f"{supabase_url}/rest/v1/clinical_trials?select=*&limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        trials = response.json()
        print(f"✅ Found {len(trials)} trials in database")
        for trial in trials:
            print(f"   - {trial.get('trial_name')} ({trial.get('nct_id')})")
    else:
        print(f"❌ Failed to search trials: {response.status_code}")
        return False
    
    # Test 4: Filter by phase
    print("\n4. Testing phase filter...")
    response = requests.get(
        f"{supabase_url}/rest/v1/clinical_trials?trial_phase=eq.Phase 1&select=*",
        headers=headers
    )
    
    if response.status_code == 200:
        trials = response.json()
        print(f"✅ Found {len(trials)} Phase 1 trials")
    else:
        print(f"❌ Failed to filter by phase: {response.status_code}")
        return False
    
    # Test 5: Get statistics
    print("\n5. Testing statistics...")
    response = requests.get(
        f"{supabase_url}/rest/v1/clinical_trials?select=count",
        headers=headers
    )
    
    if response.status_code == 200:
        total_trials = len(response.json())
        print(f"✅ Total trials in database: {total_trials}")
    else:
        print(f"❌ Failed to get statistics: {response.status_code}")
        return False
    
    # Test 6: Clean up test data
    print("\n6. Cleaning up test data...")
    response = requests.delete(
        f"{supabase_url}/rest/v1/clinical_trials?nct_id=eq.NCT99999999",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✅ Test data cleaned up successfully")
    else:
        print(f"⚠️  Failed to clean up test data: {response.status_code}")
    
    print("\n🎉 All integration tests passed!")
    return True

def run_migration_after_fix():
    """Run the migration after fixing RLS policies"""
    print("\n🔄 Running migration after RLS fix...")
    
    # First, let's create some sample data
    supabase_url = "https://hvmazsmkfzjwmrbdilfq.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2bWF6c21rZnpqd21yYmRpbGZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2OTI5OTMsImV4cCI6MjA2OTI2ODk5M30.rajuDXjG_KSQhL968L8FRXgxRFgzIIuwo25pZ6ndoSU"
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    # Sample trials for testing
    sample_trials = [
        {
            'nct_id': 'NCT12345678',
            'trial_name': 'Diabetes Treatment Study',
            'trial_phase': 'Phase 2',
            'trial_status': 'Recruiting',
            'patient_enrollment': 100,
            'sponsor': 'PharmaCorp',
            'primary_endpoints': 'HbA1c reduction',
            'secondary_endpoints': 'Quality of life',
            'inclusion_criteria': 'Type 2 diabetes, age 18-65',
            'exclusion_criteria': 'Pregnancy, severe complications'
        },
        {
            'nct_id': 'NCT87654321',
            'trial_name': 'Cancer Immunotherapy Trial',
            'trial_phase': 'Phase 3',
            'trial_status': 'Active',
            'patient_enrollment': 500,
            'sponsor': 'OncoPharma',
            'primary_endpoints': 'Overall survival',
            'secondary_endpoints': 'Progression-free survival',
            'inclusion_criteria': 'Advanced cancer, ECOG 0-1',
            'exclusion_criteria': 'Autoimmune disease, recent surgery'
        }
    ]
    
    print("📊 Creating sample trials...")
    for trial in sample_trials:
        response = requests.post(
            f"{supabase_url}/rest/v1/clinical_trials",
            headers=headers,
            json=trial
        )
        
        if response.status_code == 201:
            print(f"✅ Created trial: {trial['trial_name']}")
        else:
            print(f"❌ Failed to create trial {trial['trial_name']}: {response.status_code}")
    
    print("\n🎉 Sample data creation completed!")

if __name__ == "__main__":
    # Test the integration
    if test_supabase_integration():
        # If tests pass, run migration
        run_migration_after_fix()
    else:
        print("\n❌ Integration tests failed. Please fix RLS policies first.")
        print("Run the fix_supabase_rls.sql script in your Supabase SQL Editor.") 