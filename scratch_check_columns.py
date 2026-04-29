import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        ALTER TABLE defenjur_app_derechopeticion ADD 
        fecha_notificacion DATETIME NULL,
        termino_dias INT NULL,
        termino_horas INT NULL,
        fecha_vencimiento DATETIME NULL,
        fecha_respuesta_real DATETIME NULL,
        radicado_respuesta_salida VARCHAR(255) NULL,
        medio_envio_respuesta VARCHAR(255) NULL,
        estado_peticion VARCHAR(50) NULL;
    """)
    print("Columns added successfully to defenjur_app_derechopeticion.")
