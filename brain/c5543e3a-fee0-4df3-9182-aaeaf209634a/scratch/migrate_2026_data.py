import os
import django
import sys
from django.apps import apps
from django.conf import settings

# Setup Django environment
sys.path.append(r"c:\Users\SISTEMAS\Documents\Gestor Institucional HUDN")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from core.utils_excel import process_excel_import
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()

class MockRequest:
    def __init__(self, user):
        self.user = user

request = MockRequest(admin_user)

base_path = r"c:\Users\SISTEMAS\Documents\Gestor Institucional HUDN\temp_import\files_defenjur_2025"

# Mapping of filename fragments to model labels (defenjur_app.ModelName)
mappings = [
    ("Accione de tuetela-2026.csv", "defenjur_app.AccionTutela"),
    ("Derechos de Peticin-2026.csv", "defenjur_app.DerechoPeticion"),
    ("Pagos de Sentencias Judiciales-2026.csv", "defenjur_app.PagoSentenciaJudicial"),
    ("Peritajes-2026.csv", "defenjur_app.Peritaje"),
    ("Procesos Judiciales por Activa-2026.csv", "defenjur_app.ProcesoJudicialActiva"),
    ("Procesos Judiciales por Pasiva-2026.csv", "defenjur_app.ProcesoJudicialPasiva"),
    ("Procesos Judiciales Terminados-2026.csv", "defenjur_app.ProcesoJudicialTerminado"),
    ("Requerimientos Entes de Control-2026.csv", "defenjur_app.RequerimientoEnteControl"),
]

print("Starting bulk data migration for 2026...")

for filename, model_label in mappings:
    file_path = os.path.join(base_path, filename)
    if not os.path.exists(file_path):
        # Handle encoding issues in filename if necessary
        # Search by wildcard
        import glob
        pattern = os.path.join(base_path, filename.replace('', '*'))
        found = glob.glob(pattern)
        if found:
            file_path = found[0]
        else:
            print(f"File not found: {filename}")
            continue

    model = apps.get_model(model_label)
    print(f"\nImporting {model_label} from {os.path.basename(file_path)}...")
    
    with open(file_path, 'rb') as f:
        # We need to pass a File-like object that has a 'name' attribute for the extension detection
        class NamedBytesIO:
            def __init__(self, buffer, name):
                self.buffer = buffer
                self.name = name
            def read(self, *args): return self.buffer.read(*args)
            def seek(self, *args): return self.buffer.seek(*args)
            def __getattr__(self, attr): return getattr(self.buffer, attr)

        file_obj = NamedBytesIO(f, file_path)
        result = process_excel_import(request, model, file_obj, preview=False)
        
        if result['success']:
            print(f"Success: {result['message']}")
        else:
            print(f"Partial/Failure: {result['message']}")
            if 'errors' in result and result['errors']:
                print(f"First 5 errors: {result['errors'][:5]}")

print("\nMigration complete.")
