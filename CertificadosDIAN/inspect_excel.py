import pandas as pd

excel_path = r'C:\Users\SISTEMAS\Documents\Gestor Institucional HUDN\CertificadoIngresos2025.xlsm'

try:
    xl = pd.ExcelFile(excel_path)
    print(f"Sheet names: {xl.sheet_names}")

    for sheet in xl.sheet_names:
        print(f"\n--- Sheet: {sheet} ---")
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet, nrows=20)
            print("Columns:")
            print(df.columns.tolist())
            print("\nData (First 10 rows):")
            print(df.head(10))
        except Exception as e_sheet:
            print(f"Error reading sheet {sheet}: {e_sheet}")

except Exception as e:
    print(f"Error reading excel: {e}")
