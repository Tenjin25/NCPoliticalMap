import csv

input_path = "results_pct_20141104.csv"
output_path = "results_pct_20141104_clean.csv"

with open(input_path, "r", encoding="utf-8") as infile, open(output_path, "w", newline='', encoding="utf-8") as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    header = next(reader)
    header = [h.replace('"', '').strip() for h in header]
    writer.writerow(header)
    for row in reader:
        clean_row = [v.replace('"', '').strip() for v in row]
        if len(clean_row) < len(header):
            clean_row += [''] * (len(header) - len(clean_row))
        elif len(clean_row) > len(header):
            clean_row = clean_row[:len(header)]
        writer.writerow(clean_row)

print(f"Cleaned CSV written to {output_path}")
