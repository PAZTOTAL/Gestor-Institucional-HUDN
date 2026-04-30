import os
import sys
import django

sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from defenjur_py.legal.models import AccionTutela

try:
    qs = AccionTutela.objects.all()
    print(str(qs.query))
    # Try to execute it
    list(qs[:1])
    print("Query executed successfully")
except Exception as e:
    print(f"Query failed: {e}")
