import os, django, sys
sys.path.append(r"c:\Users\SISTEMAS\Documents\Gestor Institucional HUDN")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()
from django.apps import apps
from django.db.models import Q

models = [
    'AccionTutela', 'DerechoPeticion', 'PagoSentenciaJudicial', 
    'Peritaje', 'ProcesoJudicialActiva', 'ProcesoJudicialPasiva', 
    'ProcesoJudicialTerminado', 'RequerimientoEnteControl'
]

print("--- ANALYZING EMPTY FIELDS ---")
for m in models:
    try:
        model = apps.get_model('defenjur_app', m)
        count = model.objects.count()
        if count == 0:
            print(f"{m}: No records.")
            continue
            
        print(f"\n{m} (Total: {count})")
        # Only inspect non-primary-key CharFields and TextFields for empty strings
        fields = [f for f in model._meta.fields if not f.primary_key]
        for f in fields:
            name = f.name
            empty_count = 0
            # For strings, check null and empty
            if isinstance(f, (django.db.models.CharField, django.db.models.TextField)):
                empty_count = model.objects.filter(Q(**{f"{name}__exact": ""}) | Q(**{f"{name}__isnull": True})).count()
            else:
                empty_count = model.objects.filter(**{f"{name}__isnull": True}).count()
                
            if empty_count > 0:
                print(f"  - {name}: {empty_count} empty")
    except Exception as e:
        print(f"Error with {m}: {e}")
