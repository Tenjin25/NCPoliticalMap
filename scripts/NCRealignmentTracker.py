import os
import pandas as pd
import matplotlib.pyplot as plt

race_years = {
    "Pres": [2008, 2012, 2016, 2020, 2024],
    "Gov":  [2008, 2012, 2016, 2020, 2024],
    "Sen":  [2008, 2010, 2014, 2016, 2020, 2022],
}
races = list(race_years.keys())

def plot_trends(years, dem_percents, rep_percents, title, filename):
    plt.figure(figsize=(8, 5))
    plt.plot(years, dem_percents, marker='o', label="Democrat", color='blue', linewidth=2)
    plt.plot(years, rep_percents, marker='o', label="Republican", color='red', linewidth=2)
    plt.title(title, fontsize=14)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Vote %", fontsize=12)
    plt.ylim(0, 1)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"Saved {filename}")

def find_election_file(year, race, missing_files_reported):
    variants = [race]
    if race == 'Sen':
        variants.append('Senate')
    if race == 'Pres':
        variants.append('President')
    if race == 'Gov':
        variants.append('Governor')
    for variant in variants:
        filename = f"{year}_{variant}_Statistics_election_only.csv"
        if os.path.exists(filename):
            return filename
    # Only print if not already reported
    key = f"{year}_{race}"
    if key not in missing_files_reported:
        print(f"Missing file: {year}_{race}_Statistics_election_only.csv (tried variants: {variants})")
        missing_files_reported.add(key)
    return None

def standardize_columns(df):
    # Standardize the first column to 'ID' if needed
    if df.columns[0].lower() in ['district', 'districts']:
        df = df.rename(columns={df.columns[0]: 'ID'})
    # Standardize Dem/Rep/Oth columns if they have % in the name
    col_map = {}
    for col in df.columns:
        if col.strip().lower() in ['dem %', 'dem']:
            col_map[col] = 'Dem'
        if col.strip().lower() in ['rep %', 'rep']:
            col_map[col] = 'Rep'
        if col.strip().lower() in ['oth %', 'oth']:
            col_map[col] = 'Oth'
    if col_map:
        df = df.rename(columns=col_map)
    # Drop duplicate columns, keep only one for each party
    for party in ['Dem', 'Rep', 'Oth']:
        party_cols = [col for col in df.columns if col == party]
        if len(party_cols) > 1:
            # Keep the first, drop the rest
            df = df.drop(columns=party_cols[1:])
    # Convert party columns to numeric
    for party in ['Dem', 'Rep', 'Oth']:
        if party in df.columns:
            df[party] = pd.to_numeric(df[party], errors='coerce')
    return df

missing_files_reported = set()
for race in races:
    years = race_years[race]
    for district_num in range(1, 15):
        dem_percents = []
        rep_percents = []
        for year in years:
            filename = find_election_file(year, race, missing_files_reported)
            if not filename:
                dem_percents.append(None)
                rep_percents.append(None)
                continue
            df = pd.read_csv(filename)
            df = standardize_columns(df)
            row = df[df["ID"].astype(str) == str(district_num)]
            if not row.empty:
                dem_percents.append(row["Dem"].values[0])
                rep_percents.append(row["Rep"].values[0])
            else:
                dem_percents.append(None)
                rep_percents.append(None)
        plot_trends(years, dem_percents, rep_percents, f"NC-{district_num} {race} Results", f"NC-{district_num}_{race}_trend.png")
