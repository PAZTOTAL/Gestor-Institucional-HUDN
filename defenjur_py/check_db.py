import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=FENJUR_BD_ORG;Trusted_Connection=yes;"

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
