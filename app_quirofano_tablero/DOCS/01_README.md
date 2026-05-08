# Quiroinfo

Sistema de seguimiento de estado quirúrgico para familiares de pacientes en hospitales. Permite al personal del hospital actualizar el estado de cada paciente durante el proceso quirúrgico, y a los familiares visualizar el progreso en un tablero público proyectado en la sala de espera.

## Características principales

- **Tablero público** — Pantalla TV en sala de espera con actualización automática cada 15 segundos (polling HTMX). Sin autenticación.
- **Panel de gestión** — Vista privada para funcionarios del hospital. Permite gestionar pacientes, aplicar estados quirúrgicos, editar datos y cargar pacientes programados.
- **Estados quirúrgicos** — En preparación, En cirugía, En recuperación, Finalizado, Otro (con label personalizable).
- **Notificaciones SMS** — Envío automático de SMS vía Twilio al familiar del paciente cuando cambia el estado quirúrgico.
- **Autenticación por email** — Login basado en whitelist de correos o dominio permitido, sin contraseña.

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Django (SSR con templates) |
| Interacciones dinámicas | HTMX 1.9 |
| UI ligera (modales, toggles) | Alpine.js 3.x |
| Estilos | Tailwind CSS (CDN) |
| Base de datos | PostgreSQL |
| SMS | Twilio |
| Testing | pytest + pytest-django + factory-boy + Hypothesis |

## Estructura del proyecto

```
quiroinfo/
├── app_autenticacion/       # App de autenticación por email
│   ├── mixins.py            # LoginRequeridoMixin
│   ├── vistas.py            # LoginVista, LogoutVista
│   ├── urls.py              # /login/, /logout/
│   └── templates/autenticacion/
│       └── login.html
├── app_core/                # App principal: modelos, vistas, servicios
│   ├── models.py            # Paciente, Sesion, EstadoQuirurgico
│   ├── servicios.py         # SesionServicio, obtenerSesionesVisibles
│   ├── vistas.py            # Vistas de gestión y tablero
│   ├── utils.py             # Utils (carga de pacientes programados)
│   ├── urls.py              # Rutas principales
│   ├── templatetags/
│   │   └── filtros_gestion.py  # Filtro get_item para templates
│   ├── templates/gestion/
│   │   ├── gestion.html           # Panel de gestión completo
│   │   └── fragmento_tablas.html  # Fragmento HTMX con ambas tablas
│   └── templates/tablero/
│       ├── tablero.html           # Tablero TV completo
│       └── fragmento.html         # Fragmento HTMX del tablero
├── app_notificaciones/      # App de notificaciones SMS
│   └── servicios.py         # NotificacionServicio (Twilio)
├── quiroinfo/               # Configuración del proyecto Django
│   ├── settings.py          # Settings principal
│   ├── settings_test.py     # Settings para pytest
│   ├── urls.py              # URL root (incluye apps)
│   └── wsgi.py / asgi.py
├── templates/
│   └── base.html            # Template base con CDN imports
├── docs/                    # Documentación
├── requirements.txt
├── pytest.ini
└── manage.py
```

## Instalación y configuración

### Prerrequisitos

- Python 3.12+
- PostgreSQL
- pip

### Pasos

1. **Clonar el repositorio**

```bash
git clone <url-del-repositorio>
cd quiroinfo
```

2. **Crear y activar entorno virtual**

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Configurar la base de datos**

Crear la base de datos PostgreSQL `quiroinfo` y ajustar las credenciales en `quiroinfo/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'quiroinfo',
        'USER': 'postgres',
        'PASSWORD': '<tu-password>',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

5. **Ejecutar migraciones**

```bash
python manage.py migrate
```

6. **Iniciar el servidor**

```bash
python manage.py runserver
```

La aplicación estará disponible en `http://localhost:8000/`. La raíz (`/`) redirige automáticamente al tablero (`/tablero/`).

## Ejecutar tests

```bash
pytest
```

Los tests usan `quiroinfo/settings_test.py` como configuración (definido en `pytest.ini`). Incluyen tests unitarios y tests basados en propiedades con Hypothesis.

## Arquitectura (resumen)

Quiroinfo sigue una arquitectura **SSR (Server-Side Rendering)** con Django Templates. No hay SPA ni API REST.

- **HTMX** maneja las interacciones dinámicas: cambios de estado, edición de pacientes, carga de programados y polling del tablero. Las respuestas son fragmentos HTML que reemplazan secciones del DOM.
- **Alpine.js** gestiona comportamientos ligeros de UI: modales, confirmaciones, spinners y estado local de componentes.
- **Tailwind CSS por CDN** proporciona los estilos sin necesidad de build step ni `collectstatic` para el MVP.
- **PostgreSQL** almacena pacientes y sesiones quirúrgicas con integridad referencial (CASCADE).
- **Twilio** envía SMS de notificación al familiar cuando cambia el estado quirúrgico de un paciente.
