
import django
import os
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connection, transaction

def fix_migration():
    try:
        with connection.cursor() as cursor:
            # First, check if unificador_v1.0001_initial is already there
            cursor.execute("SELECT name FROM django_migrations WHERE app = 'unificador_v1' AND name = '0001_initial'")
            if not cursor.fetchone():
                print("Inserting unificador_v1 initial migration...")
                cursor.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('unificador_v1', '0001_initial', CURRENT_TIMESTAMP)")
            
            # Now, check if we need to add the PerfilUsuario fields manually if the last attempt failed
            cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'usuarios_perfilusuario' AND COLUMN_NAME = 'cedula'")
            if not cursor.fetchone():
                print("Adding missing columns to usuarios_perfilusuario...")
                cursor.execute("ALTER TABLE usuarios_perfilusuario ADD cedula nvarchar(20) NULL")
                cursor.execute("ALTER TABLE usuarios_perfilusuario ADD direccion nvarchar(255) NULL")
                cursor.execute("ALTER TABLE usuarios_perfilusuario ADD fecha_nacimiento date NULL")
            else:
                print("Columns already exist.")

        print("Fix complete.")
    except Exception as e:
        print(f"Error during fix: {str(e)}")

if __name__ == "__main__":
    fix_migration()
