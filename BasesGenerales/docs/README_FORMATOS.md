# Documentación: Sistema de Formatos HUDN

## Modelo Formatos_Hudn

### Ubicación
`BasesGenerales/models.py` (líneas 233-305)

### Descripción
Modelo para gestionar los formatos institucionales del hospital con código personalizado.

### Campos
- `codigo_formato` (PK): Formato FRXXX-NNN (ej: FRJUR-001)
- `nombre_formato`: Nombre del formato
- `version`: Versión del formato (default: "1.0")
- `fecha_creacion`: Auto-generada al crear
- `fecha_modificacion`: Auto-actualizada al modificar
- `elaborado_por`: Usuario que creó el formato
- `modificado_por`: Usuario que modificó (nullable)

### Validación
- Regex: `^FR[A-Z]{3}-\d{3}$`
- Auto-conversión a mayúsculas

### Acceso
- URL Modulo: `/modulo/BasesGenerales/tabla/Formatos_Hudn/`
- Django Admin: `/admin/BasesGenerales/formatos_hudn/`
- Menú: Home → Asistencial → "Formatos HUDN"

---

## Sistema de Plantillas HTML

### Plantilla Base
**Archivo:** `templates/BasesGenerales/formato_base.html`

Plantilla reutilizable con encabezado estandarizado del hospital.

### Bloques Principales
```django
{% block titulo_formato %}{% endblock %}
{% block codigo_formato %}{% endblock %}
{% block version %}{% endblock %}
{% block fecha_elaboracion %}{% endblock %}
{% block fecha_actualizacion %}{% endblock %}
{% block content %}{% endblock %}
```

### Ejemplo de Uso
```django
{% extends "BasesGenerales/formato_base.html" %}

{% block titulo_formato %}MI FORMATO{% endblock %}
{% block codigo_formato %}FRXXX-001{% endblock %}

{% block content %}
<div class="section-title">SECCIÓN</div>
<div class="form-group">
    <label class="form-label">Campo:</label>
    <input type="text" class="form-input">
</div>
{% endblock %}
```

### Clases CSS Disponibles
- `.section-title` - Títulos de sección
- `.form-group` - Grupos de formulario
- `.form-label` - Etiquetas
- `.form-input` - Campos de entrada
- `.data-table` - Tablas de datos

---

## Códigos de Área

| Área | Código | Ejemplo |
|------|--------|---------|
| Jurídica | FRJUR | FRJUR-001 |
| Administrativa | FRADM | FRADM-025 |
| Quirúrgica | FRQUI | FRQUI-032 |
| Médica | FRMED | FRMED-100 |
| Enfermería | FRENF | FRENF-050 |
| Finanzas | FRFIN | FRFIN-010 |

---

## Migraciones Aplicadas

- `0002_formatos_hudn.py` - Creación del modelo Formatos_Hudn

---

## Archivos del Sistema

```
BasesGenerales/
├── models.py                          # Modelo Formatos_Hudn
├── admin.py                           # Auto-registro en admin
├── templates/
│   └── BasesGenerales/
│       ├── formato_base.html          # Plantilla base
│       └── ejemplo_formato_anestesia.html  # Ejemplo
├── docs/
│   └── README_FORMATOS.md            # Esta documentación
└── migrations/
    └── 0002_formatos_hudn.py         # Migración del modelo
```

---

## Integración con Django

### Vista Ejemplo
```python
from django.shortcuts import render, get_object_or_404
from .models import Formatos_Hudn

def ver_formato(request, codigo):
    formato = get_object_or_404(Formatos_Hudn, codigo_formato=codigo)
    context = {
        'codigo': formato.codigo_formato,
        'nombre': formato.nombre_formato,
        'version': formato.version,
    }
    return render(request, 'BasesGenerales/mi_formato.html', context)
```

### URL Pattern
```python
path('formato/<str:codigo>/', views.ver_formato, name='ver_formato'),
```

---

## Notas de Implementación

### Fecha: 2026-01-22

**Implementado:**
- ✅ Modelo Formatos_Hudn con validación personalizada
- ✅ Migración de base de datos aplicada
- ✅ Registro automático en Django Admin
- ✅ Integración con modulo view personalizado
- ✅ Botón en menú Grupo Asistencial
- ✅ Sistema de plantillas HTML con encabezado estandarizado
- ✅ Ejemplo de formato (Registro de Anestesia)
- ✅ Clases CSS para formularios y tablas
- ✅ Optimización para impresión/PDF

**Pendiente:**
- [ ] Agregar logos reales del hospital
- [ ] Implementar generación de PDFs
- [ ] Crear más formatos específicos
- [ ] Sistema de aprobación de versiones

---

## Mantenimiento

Para crear un nuevo formato:

1. Crear archivo HTML en `templates/BasesGenerales/`
2. Extender `formato_base.html`
3. Personalizar bloques del encabezado
4. Agregar contenido en `{% block content %}`
5. Registrar en el modelo `Formatos_Hudn`

Para modificar la plantilla base:
- Editar `templates/BasesGenerales/formato_base.html`
- Los cambios se aplicarán a todos los formatos que la extiendan

---

## Contacto y Soporte

Para modificaciones o nuevos formatos, consultar esta documentación y los archivos de ejemplo en `templates/BasesGenerales/`.
