import os

def delete_election_only_files(directory):
    count = 0
    for filename in os.listdir(directory):
        if filename.endswith('_election_only.csv'):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
                count += 1
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
    print(f"Total files deleted: {count}")

if __name__ == "__main__":
    # Change this to the directory where your data files are stored
    data_dir = os.path.dirname(os.path.abspath(__file__))
    delete_election_only_files(data_dir)
