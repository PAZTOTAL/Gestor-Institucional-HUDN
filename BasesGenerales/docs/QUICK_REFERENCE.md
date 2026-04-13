# Quick Reference - Formatos HUDN

## Crear Nuevo Formato

### 1. Registrar en Base de Datos
```python
# En Django Admin o shell
from BasesGenerales.models import Formatos_Hudn
from django.contrib.auth.models import User

formato = Formatos_Hudn.objects.create(
    codigo_formato='FRXXX-001',  # FR + 3 letras área + - + 3 dígitos
    nombre_formato='Nombre del Formato',
    version='1.0',
    elaborado_por=User.objects.get(username='admin')
)
```

### 2. Crear Template HTML
```django
{% extends "BasesGenerales/formato_base.html" %}

{% block titulo_formato %}NOMBRE DEL FORMATO{% endblock %}
{% block codigo_formato %}FRXXX-001{% endblock %}
{% block version %}01{% endblock %}

{% block content %}
<!-- Tu contenido aquí -->
{% endblock %}
```

## Códigos de Área Rápidos

- **FRJUR** - Jurídica
- **FRADM** - Administrativa  
- **FRQUI** - Quirúrgica
- **FRMED** - Médica
- **FRENF** - Enfermería
- **FRFIN** - Finanzas

## Clases CSS Útiles

```html
<!-- Título de sección -->
<div class="section-title">TÍTULO</div>

<!-- Campo de formulario -->
<div class="form-group">
    <label class="form-label">Etiqueta:</label>
    <input type="text" class="form-input">
</div>

<!-- Tabla -->
<table class="data-table">
    <thead><tr><th>Columna</th></tr></thead>
    <tbody><tr><td>Dato</td></tr></tbody>
</table>
```

## Acceso Rápido

- **Modulo View:** http://127.0.0.1:8000/modulo/BasesGenerales/tabla/Formatos_Hudn/
- **Django Admin:** http://127.0.0.1:8000/admin/BasesGenerales/formatos_hudn/
- **Menú:** Home → Asistencial → Formatos HUDN

## Archivos Importantes

```
BasesGenerales/
├── models.py                    # Modelo (líneas 233-305)
├── templates/BasesGenerales/
│   ├── formato_base.html       # Plantilla base
│   └── ejemplo_*.html          # Ejemplos
└── docs/
    ├── README_FORMATOS.md      # Documentación completa
    ├── CHANGELOG.md            # Historial de cambios
    └── QUICK_REFERENCE.md      # Esta guía
```

## Comandos Útiles

```bash
# Crear migración
python manage.py makemigrations BasesGenerales

# Aplicar migración
python manage.py migrate BasesGenerales

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

## Validación de Código

✅ Válidos:
- FRJUR-001
- FRADM-025
- FRQUI-032

❌ Inválidos:
- FR-001 (falta área)
- FRJU-001 (área muy corta)
- FRJUR001 (falta guion)
- frjur-001 (minúsculas - se auto-convierte)
