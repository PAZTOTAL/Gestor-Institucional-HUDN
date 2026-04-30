import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from inventarios.views import DocumentoInventarioListView

def test_view():
    factory = RequestFactory()
    user = User.objects.filter(is_superuser=True).first()
    request = factory.get('/inventarios/documentos/')
    request.user = user
    
    view = DocumentoInventarioListView.as_view()
    try:
        response = view(request)
        print(f"Status Code: {response.status_code}")
        if hasattr(response, 'render'):
            response.render()
        print("View: OK")
    except Exception as e:
        import traceback
        print(f"View: ERROR - {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_view()
