import pandas as pd
excel_path = r'C:\Users\SISTEMAS\Documents\Gestor Institucional HUDN\CertificadoIngresos2025.xlsm'
df = pd.read_excel(excel_path, sheet_name='Hoja1', header=None, skiprows=2, nrows=5)
print("Columns count:", len(df.columns))
for index, row in df.iterrows():
    print(f"Row {index}, Col 1: '{row[1]}'")
