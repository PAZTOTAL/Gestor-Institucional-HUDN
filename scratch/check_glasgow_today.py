import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.db import connections

def run():
    with connections['readonly'].cursor() as cursor:
        print("--- REVISANDO REGISTROS DE GLASGOW HOY ---")
        
        # 1. HCNINTERR (Interconsultas/Evaluaciones)
        cursor.execute("""
            SELECT COUNT(*) FROM HCNINTERR i
            INNER JOIN HCNFOLIO f ON i.HCNFOLIO = f.OID
            WHERE CAST(f.HCFECFOL AS DATE) = CAST(GETDATE() AS DATE)
        """)
        tot_interr = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM HCNINTERR i
            INNER JOIN HCNFOLIO f ON i.HCNFOLIO = f.OID
            WHERE CAST(f.HCFECFOL AS DATE) = CAST(GETDATE() AS DATE)
            AND i.HCIGLASGOW IS NOT NULL AND i.HCIGLASGOW > 0
        """)
        glas_interr = cursor.fetchone()[0]
        print(f"HCNINTERR (Evaluaciones): {glas_interr} con Glasgow de {tot_interr} totales hoy.")

        # 2. HCNTCENTURED (Triage)
        cursor.execute("""
            SELECT COUNT(*) FROM HCNTCENTURED 
            WHERE CAST(HCETFECHAING AS DATE) = CAST(GETDATE() AS DATE)
        """)
        tot_triage = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM HCNTCENTURED 
            WHERE CAST(HCETFECHAING AS DATE) = CAST(GETDATE() AS DATE)
            AND HCNGLASGOW IS NOT NULL AND HCNGLASGOW > 0
        """)
        glas_triage = cursor.fetchone()[0]
        print(f"HCNTCENTURED (Triage): {glas_triage} con Glasgow de {tot_triage} totales hoy.")

        # 3. HCNTRIAGE (Triage general)
        cursor.execute("""
            SELECT COUNT(*) FROM HCNTRIAGE 
            WHERE CAST(HCTFECTRI AS DATE) = CAST(GETDATE() AS DATE)
        """)
        tot_triage_g = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM HCNTRIAGE 
            WHERE CAST(HCTFECTRI AS DATE) = CAST(GETDATE() AS DATE)
            AND (HCTNOGLASA IS NOT NULL OR HCTNOGLASP IS NOT NULL)
        """)
        glas_triage_g = cursor.fetchone()[0]
        print(f"HCNTRIAGE (Triage gral): {glas_triage_g} con Glasgow de {tot_triage_g} totales hoy.")
        
        # 4. HCNCTATEMED (Notas)
        cursor.execute("""
            SELECT COUNT(*) FROM HCNCTATEMED i
            INNER JOIN HCNFOLIO f ON i.HCNFOLIO = f.OID
            WHERE CAST(f.HCFECFOL AS DATE) = CAST(GETDATE() AS DATE)
        """)
        tot_cta = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM HCNCTATEMED i
            INNER JOIN HCNFOLIO f ON i.HCNFOLIO = f.OID
            WHERE CAST(f.HCFECFOL AS DATE) = CAST(GETDATE() AS DATE)
            AND (i.HCCGLAS1 IS NOT NULL OR i.HCCGLAS2 IS NOT NULL)
        """)
        glas_cta = cursor.fetchone()[0]
        print(f"HCNCTATEMED (Notas): {glas_cta} con Glasgow de {tot_cta} totales hoy.")

if __name__ == "__main__":
    run()
