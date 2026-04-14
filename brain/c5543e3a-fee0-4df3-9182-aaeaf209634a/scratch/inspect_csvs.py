import os
import csv
import glob

base_path = r"c:\Users\SISTEMAS\Documents\Gestor Institucional HUDN\temp_import\files_defenjur_2025"
files = glob.glob(os.path.join(base_path, "*-2026.csv"))

print(f"Found {len(files)} files to inspect.")

for file_path in files:
    filename = os.path.basename(file_path)
    print(f"\n--- {filename} ---")
    try:
        with open(file_path, 'r', encoding='latin1') as f:
            lines = [f.readline() for _ in range(5)]
            for i, line in enumerate(lines):
                print(f"Line {i+1}: {line.strip()}")
    except Exception as e:
        print(f"Error reading {filename}: {e}")
