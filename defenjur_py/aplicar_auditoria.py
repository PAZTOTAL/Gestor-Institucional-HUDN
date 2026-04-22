"""
Script para agregar columnas de auditoría a defenjur_app_acciontutela.
Usar las credenciales del settings.py de defenjur_py (FENJUR_BD_ORG, localhost\SQLEXPRESS)
"""
import pyodbc

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=FENJUR_BD_ORG;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

sqls = [
    ("fecha_registro", "ALTER TABLE defenjur_app_acciontutela ADD fecha_registro DATETIME2 NULL"),
    ("usuario_carga",  "ALTER TABLE defenjur_app_acciontutela ADD usuario_carga NVARCHAR(150) NULL"),
]

try:
    conn = pyodbc.connect(CONN_STR)
    cursor = conn.cursor()
    print("Conexion exitosa a FENJUR_BD_ORG")

    for col, sql in sqls:
        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME='defenjur_app_acciontutela' AND COLUMN_NAME='{col}'
            )
            BEGIN
                EXEC('{sql}')
                PRINT 'Columna {col} creada.'
            END
            ELSE
                PRINT 'Columna {col} ya existe.'
        """)
        print(f"  Columna '{col}': procesada")

    conn.commit()
    print("Listo. Columnas aplicadas correctamente.")
    cursor.close()
    conn.close()

except Exception as e:
    print(f"ERROR: {e}")
