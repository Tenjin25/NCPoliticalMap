import os
import pandas as pd

folder = '.'

for filename in os.listdir(folder):
    if filename.endswith('_election_only.csv'):
        path = os.path.join(folder, filename)
        try:
            df = pd.read_csv(path)
            # Use the correct column for district
            district_col = None
            for col in df.columns:
                if col.strip().lower() in ['id', 'district']:
                    district_col = col
                    break
            if not district_col:
                print(f"Error: No district column in {filename}")
                continue
            valid_rows = df[district_col].astype(str).str.strip().str.lower().isin([str(i) for i in range(1, 15)])
            if valid_rows.sum() == 0:
                os.remove(path)
                print(f"Deleted empty or duplicate file: {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")
