import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from consultas_externas.models import Adningreso, Hcnfolio, Hcninterr
from django.utils import timezone

def test_query():
    print("Iniciando prueba de consulta al Hospital...")
    try:
        # Intentamos obtener al menos una admisión activa
        activas = Adningreso.objects.filter(ainfecegre__isnull=True).count()
        print(f"Admisiones activas encontradas: {activas}")
        
        # Intentamos buscar pacientes con Glasgow 3-5
        evaluaciones = Hcninterr.objects.filter(hciglasgow__in=[3, 4, 5]).order_by('-oid')[:10]
        print(f"Evaluaciones con Glasgow 3-5 (últimas 10): {evaluaciones.count()}")
        
        for ev in evaluaciones:
            print(f" - Evaluación OID: {ev.oid}, Glasgow: {ev.hciglasgow}")
            
    except Exception as e:
        print(f"Error en la consulta: {e}")

if __name__ == "__main__":
    test_query()
