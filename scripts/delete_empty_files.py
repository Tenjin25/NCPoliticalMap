import os

folder = '.'

for filename in os.listdir(folder):
    if filename.endswith('.csv'):
        path = os.path.join(folder, filename)
        if os.path.getsize(path) == 0:
            os.remove(path)
            print(f"Deleted empty file: {filename}")
