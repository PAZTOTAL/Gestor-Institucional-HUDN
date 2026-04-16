import pymysql

SRC_CONFIG = {
    'host': '179.1.196.50',
    'port': 25469,
    'user': 'webmaster',
    'password': '24010242',
    'database': 'defenjur2'
}

def analyze_mapping(table, folder_samples):
    print(f"\n--- Analyzing {table} ---")
    conn = pymysql.connect(**SRC_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Get all fields
        cursor.execute(f"DESCRIBE {table}")
        fields = [f['Field'] for f in cursor.fetchall()]
        
        for folder in folder_samples:
            print(f"Searching for record corresponding to folder: {folder}")
            for field in fields:
                # Search for exact value
                cursor.execute(f"SELECT id, num_proceso FROM {table} WHERE CAST({field} AS CHAR) = %s", (folder,))
                row = cursor.fetchone()
                if row:
                    print(f"  MATCH FOUND! Folder '{folder}' matches field '{field}' (ID: {row['id']}, Proceso: {row['num_proceso']})")
                
                # Search for partial match (like within a path)
                if not row:
                    cursor.execute(f"SELECT id, num_proceso FROM {table} WHERE {field} LIKE %s", (f"%{folder}%",))
                    row = cursor.fetchone()
                    if row:
                        print(f"  PARTIAL MATCH FOUND! Folder '{folder}' in field '{field}' (ID: {row['id']}, Proceso: {row['num_proceso']})")
        
    finally:
        conn.close()

analyze_mapping('acciones_tutela', ['479', '787', '791', '2815'])
analyze_mapping('derechos_peticion', ['3555', '3400'])
analyze_mapping('procs_judiciales_pasiva', []) 
