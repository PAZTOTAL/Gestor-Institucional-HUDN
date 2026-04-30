import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from inventarios.views import DocumentoInventarioListView

def test_queryset():
    view = DocumentoInventarioListView()
    try:
        qs = view.get_queryset()
        print(f"Queryset size: {len(qs)}")
        if len(qs) > 0:
            print(f"First item: {qs[0]}")
        print("Queryset: OK")
    except Exception as e:
        import traceback
        print(f"Queryset: ERROR - {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_queryset()
