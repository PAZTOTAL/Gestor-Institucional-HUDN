import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from core.models import DashboardModule

def create_module():
    # Category should match 'bienes_servicios'
    module, created = DashboardModule.objects.get_or_create(
        slug='inventarios_nexus',
        defaults={
            'name': 'Inventarios Nexus',
            'description': 'Consulta de Documentos e Inventario',
            'url': '/inventarios/documentos/',
            'icon': 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4',
            'category': 'bienes_servicios',
            'is_active': True
        }
    )
    if not created:
        module.category = 'bienes_servicios'
        module.save()
    print(f"Module {'created' if created else 'updated'}")

if __name__ == "__main__":
    create_module()
