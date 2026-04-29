import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.core.cache import cache
from core.models import DashboardModule

# 1. Clear Cache
print("Limpiando caché...")
cache.clear()

# 2. Update Modules
print("Actualizando categorías de módulos...")

# Asegurar que los módulos DIAN estén en 'contabilidad'
dian_modules = DashboardModule.objects.filter(slug__startswith='CertificadosDIAN')
for m in dian_modules:
    m.category = 'contabilidad'
    m.save()
    print(f"Módulo {m.name} -> Categoría: {m.category}")

# Opcional: El módulo "Contabilidad" (ID 30) tal vez debería ser parte de la categoría 'contabilidad' 
# o quedarse en 'financiera'. Si el usuario quiere que esté "dentro" de Contabilidad, 
# entonces su categoría debe ser 'contabilidad'.
m30 = DashboardModule.objects.filter(slug='contabilidad').first()
if m30:
    m30.category = 'contabilidad'
    m30.save()
    print(f"Módulo {m30.name} -> Categoría: {m30.category}")

print("¡Listo!")
