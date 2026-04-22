import pyodbc

# Cadena de conexión basada en lo que vi en settings.py y check_db.py
# SERVER=172.20.100.209;DATABASE=DGEMPRES_NEXUS;UID=apantoja;PWD=... (según settings)
# Pero check_db.py usaba localhost\SQLEXPRESS y FENJUR_BD_ORG. 
# Reusaré la lógica de check_db.py pero para GENTERCER.

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=FENJUR_BD_ORG;Trusted_Connection=yes;"

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Ver columnas de GENTERCER
    cursor.execute("SELECT TOP 1 * FROM GENTERCER")
    columns = [column[0] for column in cursor.description]
    print(f"Columnas en GENTERCER: {columns}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
