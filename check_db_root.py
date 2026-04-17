import pyodbc

# Usando los datos de HospitalManagement/settings.py
conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=172.20.100.209;DATABASE=GestorInstitucional;UID=apantoja;PWD=ConsultasPantojaHUDN_2026$;"

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    table_name = 'defenjur_app_acciontutela'
    cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
    columns = [row.COLUMN_NAME for row in cursor.fetchall()]
    
    print(f"Columns in {table_name}: {columns}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
