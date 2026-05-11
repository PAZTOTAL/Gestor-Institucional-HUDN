import os
import django

# Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from BasesGenerales.models import Geo01Pais, Geo02Departamento

def populate_departments():
    # Asegurarnos de que Colombia existe
    try:
        pais_col = Geo01Pais.objects.get(codigo='COL')
    except Geo01Pais.DoesNotExist:
        print("Error: No se encontró el país con código 'COL'. Por favor carga los países primero.")
        return

    departamentos = [
        ('05', 'Antioquia', 'Departamento de Antioquia'),
        ('08', 'Atlántico', 'Departamento del Atlántico'),
        ('11', 'Bogotá, D.C.', 'Bogotá, Distrito Capital'),
        ('13', 'Bolívar', 'Departamento de Bolívar'),
        ('15', 'Boyacá', 'Departamento de Boyacá'),
        ('17', 'Caldas', 'Departamento de Caldas'),
        ('18', 'Caquetá', 'Departamento del Caquetá'),
        ('19', 'Cauca', 'Departamento del Cauca'),
        ('20', 'Cesar', 'Departamento del Cesar'),
        ('23', 'Córdoba', 'Departamento de Córdoba'),
        ('25', 'Cundinamarca', 'Departamento de Cundinamarca'),
        ('27', 'Chocó', 'Departamento del Chocó'),
        ('41', 'Huila', 'Departamento del Huila'),
        ('44', 'La Guajira', 'Departamento de La Guajira'),
        ('47', 'Magdalena', 'Departamento del Magdalena'),
        ('50', 'Meta', 'Departamento del Meta'),
        ('52', 'Nariño', 'Departamento de Nariño'),
        ('54', 'Norte de Santander', 'Departamento de Norte de Santander'),
        ('63', 'Quindío', 'Departamento del Quindío'),
        ('66', 'Risaralda', 'Departamento de Risaralda'),
        ('68', 'Santander', 'Departamento de Santander'),
        ('70', 'Sucre', 'Departamento de Sucre'),
        ('73', 'Tolima', 'Departamento del Tolima'),
        ('76', 'Valle del Cauca', 'Departamento del Valle del Cauca'),
        ('81', 'Arauca', 'Departamento de Arauca'),
        ('85', 'Casanare', 'Departamento de Casanare'),
        ('86', 'Putumayo', 'Departamento del Putumayo'),
        ('88', 'Archipiélago de San Andrés, Providencia y Santa Catalina', 'Archipiélago de San Andrés, Providencia y Santa Catalina'),
        ('91', 'Amazonas', 'Departamento del Amazonas'),
        ('94', 'Guainía', 'Departamento del Guainía'),
        ('95', 'Guaviare', 'Departamento del Guaviare'),
        ('97', 'Vaupés', 'Departamento del Vaupés'),
        ('99', 'Vichada', 'Departamento del Vichada'),
    ]

    count = 0
    for codigo, nombre, descripcion in departamentos:
        obj, created = Geo02Departamento.objects.get_or_create(
            Geo01Pais=pais_col,
            codigo=codigo,
            defaults={'nombre': nombre, 'descripcion': descripcion}
        )
        if created:
            count += 1
            print(f"Añadido: {nombre} ({codigo})")
        else:
            obj.nombre = nombre
            obj.descripcion = descripcion
            obj.save()
            print(f"Actualizado: {nombre} ({codigo})")
    
    print(f"\nProceso finalizado. Se cargaron {count} departamentos para Colombia.")

if __name__ == "__main__":
    populate_departments()
