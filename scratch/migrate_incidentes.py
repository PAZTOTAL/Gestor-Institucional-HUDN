import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connection

def migrate_db():
    # 1. Create new table
    create_table = """
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[defenjur_app_incidentedesacato]') AND type in (N'U'))
    BEGIN
        CREATE TABLE defenjur_app_incidentedesacato (
            id BIGINT IDENTITY(1,1) PRIMARY KEY,
            tutela_id BIGINT NOT NULL,
            fecha_notificacion DATETIME NULL,
            termino_dias INT NULL,
            termino_horas INT NULL,
            fecha_vencimiento DATETIME NULL,
            fecha_respuesta DATETIME NULL,
            radicado_respuesta NVARCHAR(100) NULL,
            medio_envio NVARCHAR(100) NULL,
            observaciones NVARCHAR(MAX) NULL,
            fecha_registro DATETIME DEFAULT GETDATE(),
            CONSTRAINT FK_Incidente_Tutela FOREIGN KEY (tutela_id) REFERENCES defenjur_app_acciontutela(id) ON DELETE CASCADE
        );
    END
    """
    
    # 2. Drop old columns from AccionTutela
    drop_columns = [
        "desacato_fecha_notificacion",
        "desacato_termino_dias",
        "desacato_termino_horas",
        "desacato_fecha_vencimiento",
        "desacato_fecha_respuesta",
        "desacato_radicado_respuesta",
        "desacato_medio_envio"
    ]
    
    with connection.cursor() as cursor:
        print("Creating table defenjur_app_incidentedesacato...")
        cursor.execute(create_table)
        print("Success.")
        
        for col in drop_columns:
            try:
                print(f"Dropping column {col} from defenjur_app_acciontutela...")
                cursor.execute(f"ALTER TABLE defenjur_app_acciontutela DROP COLUMN {col}")
                print("Success.")
            except Exception as e:
                print(f"Skipping {col}: {e}")

if __name__ == "__main__":
    migrate_db()
