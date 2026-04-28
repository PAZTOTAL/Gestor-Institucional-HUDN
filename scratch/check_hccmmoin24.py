import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    try:
        with connections['readonly'].cursor() as cursor:
            # Revisa si la tabla existe
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE UPPER(TABLE_NAME) = 'HCCMMOIN24'")
            table = cursor.fetchone()
            if table:
                print(f"TABLA ENCONTRADA: {table[0]}")
                
                # Obtener columnas
                cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE UPPER(TABLE_NAME) = 'HCCMMOIN24'")
                cols = [r[0] for r in cursor.fetchall()]
                print(f"Columnas: {cols}")
                
                # Buscar columnas relacionadas con Glasgow
                glasgow_cols = [c for c in cols if 'GLAS' in c.upper()]
                print(f"Columnas de Glasgow: {glasgow_cols}")
                
                # Obtener muestra de datos
                if glasgow_cols:
                    cols_to_select = ', '.join(glasgow_cols)
                    cursor.execute(f"SELECT TOP 5 {cols_to_select} FROM {table[0]} WHERE {glasgow_cols[0]} IS NOT NULL")
                    rows = cursor.fetchall()
                    print(f"Muestra de datos (Glasgow): {rows}")
                else:
                    cursor.execute(f"SELECT TOP 1 * FROM {table[0]}")
                    print(f"Muestra (1 fila): {cursor.fetchone()}")
            else:
                print("LA TABLA 'HCCMMOIN24' NO EXISTE en la base de datos.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
