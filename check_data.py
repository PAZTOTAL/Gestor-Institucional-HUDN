import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=172.20.100.209;DATABASE=GestorInstitucional;UID=apantoja;PWD=ConsultasPantojaHUDN_2026$;"

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    table_name = 'defenjur_app_acciontutela'
    cursor.execute(f"SELECT TOP 1 * FROM {table_name}")
    row = cursor.fetchone()
    if row:
        columns = [column[0] for column in cursor.description]
        data = dict(zip(columns, row))
        print(f"Columns: {columns}")
        print(f"Sample data: {data}")
    else:
        print("Table is empty.")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
