import os
import sys
import django

# Asegurar que se encuentre HospitalManagement
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from django.contrib.auth import get_user_model
from usuarios.models import PerfilUsuario, PermisoApp, PermisoModelo

User = get_user_model()
try:
    u = User.objects.get(pk=1011)
    print(f"Usuario: {u.username} (ID: {u.pk})")
    print(f"Rol en Usuario (attr): '{getattr(u, 'rol', 'N/A')}'")
    print(f"Is Superuser: {u.is_superuser}")
    print(f"Is Staff: {u.is_staff}")
    
    try:
        p = u.perfil
        print(f"Perfil legal_rol: '{p.legal_rol}'")
    except Exception as e:
        print(f"Error perfil: {e}")
        
    perms_app = PermisoApp.objects.filter(user=u, permitido=True)
    print(f"Permisos App activos: {[p.app_label for p in perms_app]}")
    
    perms_mod = PermisoModelo.objects.filter(user=u, permitido=True)
    print(f"Permisos Modelo activos: {[p.model_name for p in perms_mod]}")

except User.DoesNotExist:
    print("Usuario 1009 no encontrado")
