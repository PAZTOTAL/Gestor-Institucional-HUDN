import os
import django
import sys

# Add the project root to sys.path
sys.path.append('d:\\HospitalManagement')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
django.setup()

from parto.models import Item, Parametro

def list_items_and_params():
    # Item does not have 'orden', relies on 'codigo'
    items = Item.objects.all() 
    print("Current Items and Parameters:")
    for item in items:
        print(f"Item: '{item.nombre}' | Code: '{item.codigo}' | ID: {item.id}")
        params = item.parametros.all().order_by('orden', 'id')
        for p in params:
             print(f"  - Param: '{p.nombre}' | Code: '{p.codigo}' | Orden: {p.orden} | ID: {p.id}")

if __name__ == '__main__':
    list_items_and_params()
