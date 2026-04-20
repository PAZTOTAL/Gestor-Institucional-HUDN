import pymysql

SRC_CONFIG = {
    'host': '179.1.196.50',
    'port': 25469,
    'user': 'webmaster',
    'password': '24010242',
    'database': 'defenjur2'
}

TABLE_CONFIG = {
    'acciones_tutela': ['479', '787', '791', '2815'],
    'derechos_peticion': ['3555', '3400'],
    'procs_judiciales_pasiva': ['2023-00001', '789'], # Just guessing
    'pagos_sentencias_judiciales': ['1', '2']
}

def analyze_mapping():
    conn = pymysql.connect(**SRC_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        for table, samples in TABLE_CONFIG.items():
            print(f"\n--- Analyzing {table} ---")
            cursor.execute(f"DESCRIBE {table}")
            fields = [f['Field'] for f in cursor.fetchall()]
            
            for folder in samples:
                found = False
                for field in fields:
                    query = f"SELECT * FROM {table} WHERE CAST({field} AS CHAR) = %s"
                    cursor.execute(query, (folder,))
                    row = cursor.fetchone()
                    if row:
                        print(f"  MATCH: Folder '{folder}' == Field '{field}' (ID: {row['id']})")
                        found = True
                        break
                    
                    query = f"SELECT * FROM {table} WHERE {field} LIKE %s"
                    cursor.execute(query, (f"%{folder}%",))
                    row = cursor.fetchone()
                    if row:
                        print(f"  PARTIAL: Folder '{folder}' in Field '{field}' (ID: {row['id']})")
                        found = True
                        break
                if not found:
                    print(f"  NO MATCH for folder '{folder}' in any field.")
        
    finally:
        conn.close()

analyze_mapping()
