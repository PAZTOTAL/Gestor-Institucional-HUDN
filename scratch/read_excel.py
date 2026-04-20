import pandas as pd

def read_excel():
    path = r'C:\Users\SISTEMAS\Documents\BASE ACTUALIZADA CON CARGOS Y AREAS  04- 2026.xlsx'
    try:
        df = pd.read_excel(path)
        print("Columns:", df.columns.tolist())
        print("\nFirst 5 rows:")
        print(df.head())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    read_excel()
