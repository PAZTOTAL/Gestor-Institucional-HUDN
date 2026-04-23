"""
Script de carga: ListaTipoDocumento
Ejecutar con: python manage.py shell < load_tipo_documento.py
"""
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HospitalManagement.settings")

from BasesGenerales.models import ListaTipoDocumento

datos = [
    # (codigo, nombre/abreviatura, descripcion/nombre completo)
    ("11", "RC",   "Registro Civil de Nacimiento"),
    ("12", "TI",   "Tarjeta de Identidad"),
    ("13", "CC",   "Cédula de Ciudadanía"),
    ("21", "TE",   "Tarjeta de Extranjería"),
    ("22", "CE",   "Cédula de Extranjería"),
    ("31", "NIT",  "Número de Identificación Tributaria"),
    ("41", "PAS",  "Pasaporte"),
    ("42", "DIE",  "Documento de Identificación Extranjero"),
    ("47", "PEP",  "Permiso Especial de Permanencia"),
    ("48", "PPT",  "Permiso por Protección Temporal"),
    ("50", "NIT",  "NIT de otro país"),
    ("91", "NUIP", "Número Único de Identificación Personal"),
]

creados = 0
actualizados = 0
errores = []

for codigo, nombre, descripcion in datos:
    try:
        obj, created = ListaTipoDocumento.objects.get_or_create(
            codigo=codigo,
            defaults={"nombre": nombre, "descripcion": descripcion},
        )
        if not created:
            # Si ya existe, actualizar por si acaso
            obj.nombre = nombre
            obj.descripcion = descripcion
            obj.save()
            actualizados += 1
        else:
            creados += 1
        print(f"  {'[NUEVO]' if created else '[OK]  '} {codigo} - {nombre} - {descripcion}")
    except Exception as e:
        errores.append((codigo, str(e)))
        print(f"  [ERROR] {codigo}: {e}")

print("\n" + "="*60)
print(f"  Registros creados   : {creados}")
print(f"  Registros existentes: {actualizados}")
print(f"  Errores             : {len(errores)}")
print("="*60)

if errores:
    print("\nDetalle de errores:")
    for cod, msg in errores:
        print(f"  - Código {cod}: {msg}")
else:
    print("\n✓ Carga completada sin errores.")
