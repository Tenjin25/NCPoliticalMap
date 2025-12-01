import pandas as pd

# Read the combined statistics file
df = pd.read_csv('all_full_statistics_combined.csv')

# Map short race names to full names for output filenames
race_map = {
    'Gov': 'Governor',
    'Pres': 'President',
    'Sen': 'Senate'
}

# Loop through each unique SourceFile
for source_file in df['SourceFile'].dropna().unique():
    # Try to extract year and race from the source file name
    parts = source_file.replace('.csv', '').split()
    if len(parts) >= 2:
        year = parts[0]
        race_short = parts[1]
        race = race_map.get(race_short, race_short)
        # Filter rows for this source file
        sub = df[df['SourceFile'] == source_file]
        # Keep only the relevant columns
        cols = [c for c in ['ID', 'Dem', 'Rep', 'Oth'] if c in sub.columns]
        out = sub[cols]
        # Remove rows with missing or zero Dem/Rep
        out = out.dropna(subset=['Dem', 'Rep'])
        out = out[(out['Dem'] != 0) | (out['Rep'] != 0)]
        # Save to new file
        outname = f"{year}_{race}_election_results_only.csv"
        out.to_csv(outname, index=False)
        print(f"Created {outname}")
