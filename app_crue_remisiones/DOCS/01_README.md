# CRUE Remisiones Pacientes — Sistema de Gestión de Remisiones

## Descripción

Sistema web para el **Hospital Universitario Departamental de Nariño (HUDN)** que gestiona las remisiones de pacientes comentados por CRUE, ESE, SAS y EPS. Permite registrar, consultar, editar, exportar e importar remisiones de pacientes, con control de acceso basado en roles (Director y Radiooperador).

## Tecnologías

| Componente | Tecnología |
|---|---|
| Backend | Django 4.2 |
| Base de datos | PostgreSQL 16+ |
| Frontend | Bootstrap 5, JavaScript vanilla |
| Exportación/Importación | openpyxl, pandas |
| Servidor WSGI | gunicorn (producción) |
| Lenguaje | Python 3.12+ |

## Estructura del proyecto

```
app_crue_remisiones/
├── config/                          # Configuración del proyecto Django
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py                  # Configuración principal
│   ├── settings_test.py             # Configuración para tests
│   ├── urls.py                      # URLs raíz del proyecto
│   └── wsgi.py
├── remisiones/                      # Aplicación principal
│   ├── admin.py                     # Configuración del admin de Django
│   ├── apps.py                      # Configuración de la app
│   ├── forms.py                     # Formularios Django
│   ├── models.py                    # Modelos: UsuarioCrue, Remision
│   ├── services.py                  # Lógica de negocio desacoplada
│   ├── urls.py                      # URLs de la aplicación
│   ├── utils.py                     # Utilidades (excelToDataframe)
│   ├── views.py                     # Vistas (controladores)
│   ├── migrations/                  # Migraciones de base de datos
│   ├── static/remisiones/
│   │   ├── css/main.css             # Estilos principales
│   │   ├── img/logos/               # Logos del HUDN
│   │   └── js/
│   │       ├── autoformat.js        # Autoformato de signos vitales
│   │       ├── datetime_widget.js   # Widget de fecha/hora
│   │       ├── filtros.js           # Lógica de filtros
│   │       ├── modal.js             # Modal de creación/edición
│   │       └── tabla.js             # Interacciones de la tabla
│   ├── templates/remisiones/
│   │   ├── base.html                # Plantilla base
│   │   ├── main.html                # Vista principal con tabla
│   │   ├── login.html               # Inicio de sesión
│   │   ├── sidebar.html             # Panel lateral
│   │   ├── cambiar_password.html    # Cambio de contraseña propia
│   │   ├── recuperar_password.html  # Recuperación de contraseña
│   │   ├── usuarios.html            # Gestión de usuarios
│   │   ├── usuario_editar.html      # Editar usuario
│   │   └── usuario_cambiar_password.html
│   └── templatetags/                # Tags personalizados de plantilla
├── docs/                            # Documentación del proyecto
├── manage.py                        # Script de gestión de Django
├── pytest.ini                       # Configuración de pytest
└── requirements.txt                 # Dependencias de Python
```

## Requisitos previos

- **Python** 3.12+
- **PostgreSQL** 16+
- **pip** (gestor de paquetes de Python)

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd app_crue_remisiones
```

### 2. Crear entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Cree un archivo `.env` o exporte las siguientes variables:

```bash
export DB_NAME=crue_remisiones_db
export DB_USER=postgres
export DB_PASSWORD=su_contraseña_segura
export DB_HOST=localhost
export DB_PORT=5432
```

### 5. Ejecutar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

La aplicación estará disponible en `http://localhost:8000/`.

## Cómo ejecutar tests

```bash
pytest
```

La configuración de pytest se encuentra en `pytest.ini` y utiliza `config.settings_test` como módulo de configuración.

## Arquitectura resumida

El sistema sigue el patrón **Django MVT** (Model-View-Template) con comunicación **AJAX** para las operaciones CRUD de remisiones:

- **Models** (`models.py`): `UsuarioCrue` (usuario personalizado) y `Remision` (registro de paciente).
- **Views** (`views.py`): Controladores que manejan peticiones HTTP y respuestas JSON/HTML.
- **Services** (`services.py`): Lógica de negocio desacoplada (cálculos, validaciones, importación/exportación).
- **Templates**: Interfaz con sidebar izquierdo colapsable, tabla principal de registros y modal de edición/creación.
- **Frontend JS**: Módulos vanilla JS para filtros, tabla interactiva, modal AJAX, autoformato de campos y widget de fecha/hora.
