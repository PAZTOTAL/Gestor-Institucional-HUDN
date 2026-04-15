import os
import django
import pymysql

import sys
# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from defenjur_app.models import (
    AccionTutela, DerechoPeticion, ProcesoJudicialActiva, ProcesoJudicialPasiva,
    ProcesoJudicialTerminado, Peritaje, PagoSentenciaJudicial,
    ProcesoAdministrativoSancionatorio, RequerimientoEnteControl, ProcesoExtrajudicial
)

# Source MySQL Configuration
SRC_CONFIG = {
    'host': '179.1.196.50',
    'port': 25469,
    'user': 'webmaster',
    'password': '24010242',
    'database': 'defenjur2'
}

def migrate():
    try:
        conn = pymysql.connect(**SRC_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        print("Connected to Source MySQL.")
    except Exception as e:
        print(f"Error connecting to MySQL: {e}")
        return

    mapping = [
        ('acciones_tutela', AccionTutela),
        ('derechos_peticion', DerechoPeticion),
        ('procs_judiciales_activa', ProcesoJudicialActiva),
        ('procs_judiciales_pasiva', ProcesoJudicialPasiva),
        ('procs_judiciales_terminados', ProcesoJudicialTerminado),
        ('peritajes', Peritaje),
        ('pagos_sentencias_judiciales', PagoSentenciaJudicial),
        ('procesos_administrativos_sancionatorios', ProcesoAdministrativoSancionatorio),
        ('requerimientos_entes_control', RequerimientoEnteControl),
        ('procs_extrajudiciales', ProcesoExtrajudicial),
    ]

    for table_src, ModelDest in mapping:
        print(f"Migrating {table_src}...")
        cursor.execute(f"SELECT * FROM {table_src}")
        rows = cursor.fetchall()
        
        # Clear existing data in target
        ModelDest.objects.all().delete()
        
        objects = []
        for row in rows:
            # Prepare data: handle field mapping if names differ
            data = {}
            for key, value in row.items():
                if hasattr(ModelDest, key):
                    data[key] = value
                # Special cases for slightly different field names if any
                if table_src == 'acciones_tutela' and key == 'fecha_llegada':
                    data['fecha_llegada'] = value
            
            # The id is usually PK, let's keep it if possible
            # But Django might auto-assign it. Better to keep it to preserve NAS folder links.
            objects.append(ModelDest(**data))
        
        ModelDest.objects.bulk_create(objects)
        print(f"Done: {len(objects)} records migrated for {table_src}.")

    conn.close()
    print("Migration finished successfully.")

if __name__ == "__main__":
    migrate()
