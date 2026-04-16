import os, django, sys
sys.path.append(r"c:\Users\SISTEMAS\Documents\Gestor Institucional HUDN")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()
from django.apps import apps
from django.db import transaction

def populate_gaps():
    print("--- STARTING DATA POPULATION (SMART FALLBACKS) ---")
    
    # 1. AccionTutela
    try:
        AccionTutela = apps.get_model('defenjur_app', 'AccionTutela')
        tutelas = AccionTutela.objects.filter(solicitante__exact="") | AccionTutela.objects.filter(solicitante__isnull=True)
        count = 0
        with transaction.atomic():
            for t in tutelas:
                if t.accionante:
                    t.solicitante = t.accionante
                if not t.peticionario and t.accionante:
                    t.peticionario = t.accionante
                if (not t.fecha_correo or t.fecha_correo == "") and t.fecha_llegada:
                    t.fecha_correo = t.fecha_llegada
                if (not t.fecha_reparto or t.fecha_reparto == "") and t.fecha_llegada:
                    t.fecha_reparto = t.fecha_llegada
                t.save()
                count += 1
        print(f"AccionTutela: Updated {count} records with fallbacks.")
    except Exception as e:
        print(f"Error in AccionTutela: {e}")

    # 2. DerechoPeticion
    try:
        DerechoPeticion = apps.get_model('defenjur_app', 'DerechoPeticion')
        peticiones = DerechoPeticion.objects.filter(peticionario__exact="") | DerechoPeticion.objects.filter(peticionario__isnull=True)
        count = 0
        with transaction.atomic():
            for p in peticiones:
                if p.nombre_persona_solicitante:
                    p.peticionario = p.nombre_persona_solicitante
                if (not p.fecha_reparto or p.fecha_reparto == "") and p.fecha_correo:
                    p.fecha_reparto = p.fecha_correo
                p.save()
                count += 1
        print(f"DerechoPeticion: Updated {count} records with fallbacks.")
    except Exception as e:
        print(f"Error in DerechoPeticion: {e}")

    # 3. Procesos Judiciales (Syncing despacho)
    models_proc = ['ProcesoJudicialActiva', 'ProcesoJudicialPasiva', 'ProcesoJudicialTerminado']
    for m_name in models_proc:
        try:
            model = apps.get_model('defenjur_app', m_name)
            # Find records where despacho_actual is empty but maybe we can find it?
            # Actually, our import logic already tries the best. 
            # We'll just ensure 'estado_actual' for Terminados.
            if m_name == 'ProcesoJudicialTerminado':
                terms = model.objects.filter(estado_actual__exact="") | model.objects.filter(estado_actual__isnull=True)
                with transaction.atomic():
                    updated = terms.update(estado_actual="Cerrado / Terminado (Importación 2026)")
                print(f"{m_name}: Updated {updated} records with status fallback.")
        except Exception as e:
            print(f"Error in {m_name}: {e}")

if __name__ == "__main__":
    populate_gaps()
    print("--- POPULATION COMPLETE ---")
