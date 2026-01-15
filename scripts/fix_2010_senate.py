import json
import os

# Read the JSON file
json_path = r"C:\Users\Shama\OneDrive\Documents\Course_Materials\CPT-236\Side_Projects\NCRealignment\county_level_election_results_2000_2024.json"

print("Loading JSON file...")
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Fixing 2010 US Senate vote counts (dividing by 2)...")

# Navigate to 2010 US Senate results
if '2010' in data['results_by_year'] and 'us_senate' in data['results_by_year']['2010']:
    senate_2010 = data['results_by_year']['2010']['us_senate']['us_senate_2010']['results']
    
    counties_fixed = 0
    for county_name, county_data in senate_2010.items():
        # Divide all vote counts by 2
        county_data['dem_votes'] = int(county_data['dem_votes'] / 2)
        county_data['rep_votes'] = int(county_data['rep_votes'] / 2)
        county_data['other_votes'] = int(county_data['other_votes'] / 2)
        county_data['total_votes'] = int(county_data['total_votes'] / 2)
        county_data['two_party_total'] = int(county_data['two_party_total'] / 2)
        county_data['margin'] = int(county_data['margin'] / 2)
        
        # Fix all_parties dict
        if 'all_parties' in county_data:
            for party, votes in county_data['all_parties'].items():
                county_data['all_parties'][party] = int(votes / 2)
        
        counties_fixed += 1
    
    print(f"Fixed {counties_fixed} counties")
    
    # Create backup
    backup_path = json_path.replace('.json', '_backup_before_2010_fix.json')
    print(f"Creating backup at: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    # Write fixed data
    print("Writing fixed data...")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print("\n✓ Successfully fixed 2010 US Senate data!")
    print(f"  - {counties_fixed} counties updated")
    print(f"  - All vote counts divided by 2")
    print(f"  - Backup saved as: {os.path.basename(backup_path)}")
    
    # Show example for verification
    print("\nExample - Mecklenburg County:")
    meck = senate_2010['MECKLENBURG']
    print(f"  DEM: {meck['dem_votes']:,} | REP: {meck['rep_votes']:,} | Total: {meck['total_votes']:,}")
    
else:
    print("ERROR: Could not find 2010 US Senate data in JSON structure")
