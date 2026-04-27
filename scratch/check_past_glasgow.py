import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    with connections['readonly'].cursor() as cursor:
        print("--- REVISANDO REGISTROS DE GLASGOW EL 4 DE MARZO ---")
        
        cursor.execute("""
            SELECT COUNT(*) FROM HCNINTERR i
            INNER JOIN HCNFOLIO f ON i.HCNFOLIO = f.OID
            WHERE CAST(f.HCFECFOL AS DATE) = '2026-03-04'
            AND i.HCIGLASGOW IS NOT NULL AND i.HCIGLASGOW > 0
        """)
        glas_interr = cursor.fetchone()[0]
        print(f"HCNINTERR (Evaluaciones): {glas_interr} con Glasgow.")

        cursor.execute("""
            SELECT COUNT(*) FROM HCNTRIAGE 
            WHERE CAST(HCTFECTRI AS DATE) = '2026-03-04'
            AND (HCTNOGLASA IS NOT NULL OR HCTNOGLASP IS NOT NULL)
        """)
        glas_triage_g = cursor.fetchone()[0]
        print(f"HCNTRIAGE (Triage gral): {glas_triage_g} con Glasgow.")
        
if __name__ == "__main__":
    run()
