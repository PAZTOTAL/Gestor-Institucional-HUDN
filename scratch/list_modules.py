import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from core.models import DashboardModule

print("--- Módulos de Dashboard ---")
for m in DashboardModule.objects.all():
    print(f"ID: {m.id} | Name: {m.name} | Slug: {m.slug} | Category: {m.category}")
