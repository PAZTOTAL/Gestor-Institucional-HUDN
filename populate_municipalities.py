import os
import django
import json
import urllib.request

# Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from BasesGenerales.models import Geo01Pais, Geo02Departamento, Geo03Municipio

def populate_municipalities():
    print("Iniciando descarga de datos DIVIPOLA...")
    url = "https://raw.githubusercontent.com/proyecto26/colombia/master/cities.json"
    
    try:
        response = urllib.request.urlopen(url)
        data = json.loads(response.read().decode('utf-8'))
        municipalities = data.get('data', [])
    except Exception as e:
        print(f"Error al descargar los datos: {e}")
        return

    # Asegurarnos de que Colombia existe
    try:
        pais_col = Geo01Pais.objects.get(codigo='COL')
    except Geo01Pais.DoesNotExist:
        print("Error: No se encontró el país 'COL'.")
        return

    # Cache de departamentos para evitar consultas repetitivas
    deptos_cache = {d.codigo: d for d in Geo02Departamento.objects.filter(Geo01Pais=pais_col)}
    
    print(f"Procesando {len(municipalities)} registros...")
    
    to_create = []
    to_update = []
    count_new = 0
    count_updated = 0
    
    # Mapeo de caracteres corruptos comunes en JSON
    replacements = {
        '': 'á', '': 'é', '': 'í', '': 'ó', '': 'ú',
        '': 'ñ', '': 'Á', '': 'É', '': 'Í', '': 'Ó',
        '': 'Ú', '': 'Ñ'
    }

    def clean_name(name):
        # Intentar corregir codificación si es necesario
        for search, replace in replacements.items():
            name = name.replace(search, replace)
        return name

    for muni in municipalities:
        full_id = str(muni['id']).zfill(5)
        depto_code = full_id[:2]
        muni_code = full_id[2:]
        name = clean_name(muni['name'])
        
        depto = deptos_cache.get(depto_code)
        if not depto:
            # Si no existe el depto, intentamos buscarlo de nuevo por si acaso
            try:
                depto = Geo02Departamento.objects.get(Geo01Pais=pais_col, codigo=depto_code)
                deptos_cache[depto_code] = depto
            except Geo02Departamento.DoesNotExist:
                print(f"Advertencia: Departamento {depto_code} no encontrado para municipio {name}")
                continue

        # Usamos get_or_create conceptualmente pero optimizado
        existing = Geo03Municipio.objects.filter(
            Geo01Pais=pais_col, 
            Geo02Departamento=depto, 
            codigo=muni_code
        ).first()

        if existing:
            if existing.nombre != name:
                existing.nombre = name
                existing.save()
                count_updated += 1
        else:
            to_create.append(Geo03Municipio(
                Geo01Pais=pais_col,
                Geo02Departamento=depto,
                codigo=muni_code,
                nombre=name,
                descripcion=f"Municipio de {name}"
            ))
            count_new += 1

    if to_create:
        Geo03Municipio.objects.bulk_create(to_create)
    
    print(f"\nProceso finalizado.")
    print(f"Municipios nuevos creados: {count_new}")
    print(f"Municipios actualizados: {count_updated}")
    print(f"Total en base de datos: {Geo03Municipio.objects.count()}")

if __name__ == "__main__":
    populate_municipalities()
