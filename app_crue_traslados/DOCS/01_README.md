# Sistema de Registro de Traslado de Pacientes

Sistema web Django para el registro y gestión de servicios de traslado de pacientes del Hospital Universitario Departamental de Nariño (HUDN). Reemplaza el proceso basado en hojas de cálculo Excel.

---

## Descripción general

El sistema permite a los usuarios registrar, consultar, editar y eliminar registros de traslados de pacientes, generar reportes en Excel y controlar el cierre mensual de registros. Soporta dos roles de usuario: **FUNCIONARIO** (operador estándar) y **DIRECTOR** (administrador).

### Funcionalidades principales

- Autenticación con roles (FUNCIONARIO / DIRECTOR)
- CRUD de registros de traslado con validación en tiempo real
- Filtrado por mes y rango de días
- Control de cierre mensual (solo DIRECTOR)
- Generación de reportes Excel
- Gestión de usuarios (solo DIRECTOR)
- Cambio de contraseña propia
- Limpieza anual de datos (solo DIRECTOR)

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Django 5.2.4 |
| Base de datos | PostgreSQL |
| Frontend | Tailwind CSS (CDN), HTMX 1.9, Alpine.js 3.x |
| Reportes | openpyxl (Excel) |
| Autenticación | django.contrib.auth (modelo Usuario personalizado) |

---

## Estructura del proyecto

```
app_crue_traslados/
├── manage.py
├── requirements.txt
├── .env                         ← Variables de entorno (no versionado)
├── .env.example                 ← Plantilla de variables de entorno
├── config/                      ← Configuración del proyecto Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── traslados/                   ← Aplicación principal
    ├── models.py                ← Usuario, ControlMes, TrasladoPaciente
    ├── views.py                 ← Vistas (auth, CRUD, reportes, admin)
    ├── forms.py                 ← Formularios Django
    ├── urls.py                  ← Rutas de la aplicación
    ├── admin.py                 ← Configuración del panel admin
    ├── apps.py                  ← Configuración de la app + post_migrate
    ├── services/
    │   └── report_excel.py      ← Generación de reportes Excel
    ├── management/commands/
    │   └── inicializar_meses.py ← Comando para crear ControlMes
    ├── templates/traslados/
    │   ├── base.html            ← Plantilla base (CDN, CSRF, bloques)
    │   ├── main.html            ← Vista principal (sidebar + tabla)
    │   ├── main_sidebar.html    ← Panel lateral
    │   ├── main_title.html      ← Barra de título con logo
    │   ├── login.html           ← Inicio de sesión
    │   ├── partials/
    │   │   ├── table.html       ← Tabla de registros (HTMX)
    │   │   ├── modal_form.html  ← Modal crear/editar (HTMX)
    │   │   └── confirmar_eliminar.html
    │   └── ...                  ← Otras plantillas
    ├── static/traslados/
    │   ├── css/estilos.css
    │   ├── js/main.js           ← Doble clic, toast de errores
    │   └── img/logos/            ← Logos del hospital
    └── tests/                   ← Tests unitarios y de propiedad
```

---

## Instalación y configuración

### Prerrequisitos

- Python 3.12+
- PostgreSQL 14+
- pip

### Pasos

1. **Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd app_crue_traslados
```

2. **Crear y activar entorno virtual**
```bash
python -m venv venv
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Crear la base de datos PostgreSQL**
```bash
sudo -u postgres psql -c "CREATE DATABASE crue_traslados_db;"
```

5. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con las credenciales de la base de datos
```

Contenido del archivo `.env`:
```
DB_NAME=crue_traslados_db
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=127.0.0.1
DB_PORT=5432
```

6. **Aplicar migraciones**
```bash
python manage.py migrate
```

7. **Inicializar los meses** (se ejecuta automáticamente tras migrate, pero también disponible como comando)
```bash
python manage.py inicializar_meses
```

8. **Crear superusuario**
```bash
python manage.py createsuperuser
```

9. **Ejecutar el servidor de desarrollo**
```bash
python manage.py runserver
```

10. **Acceder al sistema**
- Aplicación: http://localhost:8000/
- Panel admin: http://localhost:8000/admin/

---

## Ejecución de tests

```bash
python manage.py test traslados --verbosity=2
```

---

## Arquitectura

El sistema sigue el patrón **MVT (Model-View-Template)** de Django con actualizaciones parciales vía HTMX:

```
Navegador
  │
  ├─ Petición de página completa ──► Vista Django ──► Template ──► HTML completo
  │
  └─ Petición HTMX (parcial) ──► Vista Django ──► Template parcial ──► Fragmento HTML
                                                                        (inyectado en el DOM)
```

### Decisiones de diseño

- **Renderizado servidor + HTMX**: Sin frameworks JS pesados. HTMX maneja actualizaciones parciales (tabla, modales) sin recargar la página.
- **Alpine.js**: Solo para comportamientos ligeros de UI (menús colapsables, modales).
- **Tailwind CSS por CDN**: Estilizado rápido sin proceso de build.
- **PostgreSQL**: Base de datos relacional para despliegue hospitalario.
- **Modelo Usuario personalizado**: Extiende `AbstractUser` con campos `nombre`, `correo` y `rol`.
- **Validación en capa de modelo**: El método `clean()` de `TrasladoPaciente` valida fechas futuras y meses cerrados, independiente de la UI.
