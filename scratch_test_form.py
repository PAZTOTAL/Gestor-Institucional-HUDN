import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from defenjur_py.legal.forms import AccionTutelaForm

form = AccionTutelaForm(data={
    'accionado': ['Hospital', 'EPS'],
    'derechos_vulnerados': ['Derecho a la Vida', 'Derecho a la Salud'],
    # some mandatory fields if any
    'rol': 'administrador'
})

print("Is valid?", form.is_valid())
print("Errors:", form.errors)
if form.is_valid() or not form.errors.get('accionado') and not form.errors.get('derechos_vulnerados'):
    print("Cleaned accionado:", form.cleaned_data.get('accionado'))
    print("Cleaned derechos_vulnerados:", form.cleaned_data.get('derechos_vulnerados'))
