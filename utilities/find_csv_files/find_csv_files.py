import os

def find_csv_files(directory, folder_name, year):
    csv_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))

    return csv_files