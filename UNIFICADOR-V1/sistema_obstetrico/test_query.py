import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_obstetrico.settings')
django.setup()
from unificador_v1.models import AtencionParto
doc = '1234567890'
try:
    res = AtencionParto.objects.filter(paciente=doc).order_by("-fecha_inicio").values_list("id", flat=True).first()
    print(f"RESULT: {res}")
except Exception as e:
    print(f"ERROR: {e}")



