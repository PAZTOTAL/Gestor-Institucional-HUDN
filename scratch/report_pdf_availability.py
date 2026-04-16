import os
import sys

# Ensure current directory is in path for Django modules
sys.path.append(os.getcwd())

import django
import ftplib
import re

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from defenjur_app.models import AccionTutela, DerechoPeticion

def test_pdf_availability(model_class, entity_type, folder_base, mapping_field):
    print(f"\n--- Testing {entity_type} ({model_class.__name__}) ---")
    
    host = '172.20.100.25'
    user = 'contratacion_admin'
    pwd = 'contratacionHUDN*01122025'
    base_path = '/web/defenjur_files'

    try:
        ftp = ftplib.FTP(host)
        ftp.login(user, pwd)
    except Exception as e:
        print(f"FTP Connection failed: {e}")
        return

    results = {'found': [], 'not_found': []}
    
    # Test all records
    records = model_class.objects.all()
    
    for obj in records:
        candidates = []
        # 1. Mapped field
        val = getattr(obj, mapping_field, None)
        if val:
            cv = str(val).strip()
            if '/' in cv: cv = cv.split('/')[-1]
            if cv: candidates.append(cv)
        
        # 2. ID
        candidates.append(str(obj.id))
        
        # 3. 2-prefix (for Tutelas)
        if entity_type == 'tutela':
            candidates.append(f"2{obj.id}")
            if hasattr(obj, 'num_reparto') and obj.num_reparto:
                candidates.append(f"2{str(obj.num_reparto).strip()}")

        # 4. Radicados
        for f in ['num_rad_arch_central', 'rad_interno_arch_central', 'rad_interno']:
            v = getattr(obj, f, None)
            if v:
                cv = str(v).strip()
                candidates.append(cv)
                num = "".join(re.findall(r'\d+', cv))
                if num: candidates.append(num)
        
        # 5. Num Proceso
        if hasattr(obj, 'num_proceso') and obj.num_proceso:
            np = str(obj.num_proceso).strip()
            candidates.append(np)
            if '-' in np: candidates.append(np.replace('-', ''))

        candidates = list(dict.fromkeys([c for c in candidates if c]))

        found = False
        for cand in candidates:
            temp_dir = f"{base_path}/{folder_base}/{cand}"
            try:
                ftp.cwd(temp_dir)
                files = ftp.nlst(".")
                if any(f.lower().endswith('.pdf') for f in files):
                    found = True
                    break
            except:
                continue
        
        if found:
            results['found'].append(obj.id)
        else:
            results['not_found'].append(obj.id)

    ftp.quit()
    import json
    with open(f'scratch/results_{entity_type}.json', 'w') as f:
        json.dump(results, f)
    
    print(f"Total tested: {len(records)}")
    print(f"Found: {len(results['found'])}")
    print(f"Not Found: {len(results['not_found'])}")

test_pdf_availability(AccionTutela, 'tutela', 'acciones_tutela', 'carpeta')
test_pdf_availability(DerechoPeticion, 'peticion', 'derechos_peticion', 'num_rad_arch_central')
