import os
import django

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections

def check_gentercer():
    try:
        with connections['readonly'].cursor() as cursor:
            # Obtener nombres de columnas de GENTERCER
            cursor.execute("SELECT TOP 1 * FROM GENTERCER")
            columns = [column[0] for column in cursor.description]
            print(f"Columnas encontradas en GENTERCER: {columns}")
            
            # Probar una búsqueda con una cédula que sepamos que existe (opcional)
            # O simplemente ver si TERNOM y TERIDN existen
            target_fields = ['TERIDN', 'TERIDEN', 'TERNOM']
            for field in target_fields:
                if field in columns:
                    print(f"Campo detectado: {field}")
                else:
                    print(f"Campo NO detectado: {field}")
                    
    except Exception as e:
        print(f"Error conectando a Nexus: {e}")

if __name__ == "__main__":
    check_gentercer()
