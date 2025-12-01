import os

folder = '.'

for filename in os.listdir(folder):
    if filename.endswith('.csv') and ' ' in filename:
        new_filename = filename.replace(' ', '_')
        os.rename(os.path.join(folder, filename), os.path.join(folder, new_filename))
        print(f"Renamed: {filename} -> {new_filename}")
