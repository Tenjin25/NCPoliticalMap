import json
import pandas as pd

# Load the fixed JSON
json_path = r"C:\Users\Shama\OneDrive\Documents\Course_Materials\CPT-236\Side_Projects\NCRealignment\county_level_election_results_2000_2024.json"
csv_path = r"C:\Users\Shama\OneDrive\Documents\Course_Materials\CPT-236\Side_Projects\NCRealignment\results_pct_20101102_clean.csv"

print("Loading fixed JSON file...")
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Loading CSV file...")
df = pd.read_csv(csv_path)

# Clean up column names and data
df.columns = df.columns.str.strip()
df['county'] = df['county'].str.strip()
df['contest'] = df['contest'].str.strip()
df['choice'] = df['choice'].str.strip()
df['party'] = df['party'].str.strip()

# Filter for US Senate race
senate_df = df[df['contest'] == 'US SENATE'].copy()

print("\n" + "="*80)
print("CROSS-REFERENCE: 2010 US Senate - JSON vs CSV")
print("="*80)

# Get JSON data
senate_2010 = data['results_by_year']['2010']['us_senate']['us_senate_2010']['results']

# Check a few key counties
test_counties = ['MECKLENBURG', 'WAKE', 'GUILFORD', 'ALAMANCE', 'DURHAM']

all_match = True
for county_name in test_counties:
    print(f"\n{county_name} County:")
    print("-" * 60)
    
    # Get CSV totals by candidate
    county_csv = senate_df[senate_df['county'] == county_name]
    
    marshall_csv = county_csv[county_csv['choice'].str.contains('Elaine Marshall', na=False)]['total votes'].sum()
    burr_csv = county_csv[county_csv['choice'].str.contains('Richard Burr', na=False)]['total votes'].sum()
    lib_csv = county_csv[(county_csv['party'] == 'LIB') & (county_csv['choice'].str.contains('Michael Beitler', na=False))]['total votes'].sum()
    
    # Get JSON data
    json_data = senate_2010[county_name]
    marshall_json = json_data['dem_votes']
    burr_json = json_data['rep_votes']
    lib_json = json_data['all_parties'].get('LIB', 0)
    
    # Compare
    marshall_match = marshall_csv == marshall_json
    burr_match = burr_csv == burr_json
    lib_match = lib_csv == lib_json
    
    print(f"  Elaine Marshall (DEM):")
    print(f"    CSV:  {marshall_csv:>10,}")
    print(f"    JSON: {marshall_json:>10,}  {'✓ MATCH' if marshall_match else '✗ MISMATCH'}")
    
    print(f"  Richard Burr (REP):")
    print(f"    CSV:  {burr_csv:>10,}")
    print(f"    JSON: {burr_json:>10,}  {'✓ MATCH' if burr_match else '✗ MISMATCH'}")
    
    print(f"  Michael Beitler (LIB):")
    print(f"    CSV:  {lib_csv:>10,}")
    print(f"    JSON: {lib_json:>10,}  {'✓ MATCH' if lib_match else '✗ MISMATCH'}")
    
    total_csv = marshall_csv + burr_csv + lib_csv
    total_json = json_data['total_votes']
    
    print(f"  Total Votes:")
    print(f"    CSV:  {total_csv:>10,}")
    print(f"    JSON: {total_json:>10,}  {'✓ MATCH' if abs(total_csv - total_json) <= 100 else '✗ MISMATCH'}")
    
    if not (marshall_match and burr_match and lib_match):
        all_match = False

print("\n" + "="*80)
if all_match:
    print("✓ ALL TESTED COUNTIES MATCH!")
    print("The 2010 fix was successful - JSON data now matches CSV source.")
else:
    print("✗ SOME MISMATCHES FOUND")
    print("Review the differences above.")
print("="*80)

# Statewide totals
print("\nSTATEWIDE TOTALS:")
print("-" * 60)
csv_marshall_total = senate_df[senate_df['choice'].str.contains('Elaine Marshall', na=False)]['total votes'].sum()
csv_burr_total = senate_df[senate_df['choice'].str.contains('Richard Burr', na=False)]['total votes'].sum()

json_marshall_total = sum(c['dem_votes'] for c in senate_2010.values())
json_burr_total = sum(c['rep_votes'] for c in senate_2010.values())

print(f"Elaine Marshall (DEM):  CSV: {csv_marshall_total:>10,}  JSON: {json_marshall_total:>10,}")
print(f"Richard Burr (REP):     CSV: {csv_burr_total:>10,}  JSON: {json_burr_total:>10,}")
print(f"Total:                  CSV: {csv_marshall_total + csv_burr_total:>10,}  JSON: {json_marshall_total + json_burr_total:>10,}")
