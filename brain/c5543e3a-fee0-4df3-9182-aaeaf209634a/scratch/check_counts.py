import os, django, sys
sys.path.append(r"c:\Users\SISTEMAS\Documents\Gestor Institucional HUDN")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()
from django.apps import apps
models = [
    'AccionTutela', 'DerechoPeticion', 'PagoSentenciaJudicial', 
    'Peritaje', 'ProcesoJudicialActiva', 'ProcesoJudicialPasiva', 
    'ProcesoJudicialTerminado', 'RequerimientoEnteControl'
]
print("--- DATABASE COUNTS ---")
for m in models:
    try:
        model = apps.get_model('defenjur_app', m)
        print(f'{m}: {model.objects.count()}')
    except Exception as e:
        print(f'Error with {m}: {e}')
