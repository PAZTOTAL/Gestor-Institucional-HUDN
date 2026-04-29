# Guía de Despliegue — Quiroinfo

## Prerrequisitos

- Python 3.12+
- PostgreSQL 14+
- pip
- Acceso a una cuenta Twilio (opcional, para SMS)

---

## 1. Entorno y dependencias

```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd quiroinfo

# Crear entorno virtual
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

# Instalar dependencias
pip install -r requirements.txt
```

Dependencias principales (`requirements.txt`):

| Paquete | Propósito |
|---|---|
| `django` | Framework web |
| `psycopg2-binary` | Driver PostgreSQL |
| `twilio` | SDK para envío de SMS |
| `pytest-django` | Testing con pytest |
| `factory-boy` | Factories para tests |

---

## 2. Configuración de base de datos

Crear la base de datos en PostgreSQL:

```sql
CREATE DATABASE quiroinfo;
```

Configurar las credenciales en `quiroinfo/settings.py`:

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

Para entornos con `DATABASE_URL` (ej. Railway), la clase `Utils` en `app_core/utils.py` incluye `getVarsFromDBUrl()` para parsear la URL, aunque la configuración principal usa el diccionario `DATABASES` estándar de Django.

---

## 3. Configuración de Twilio (SMS)

Las notificaciones SMS son opcionales. Si no se configuran las credenciales, el sistema funciona normalmente sin enviar SMS.

En `quiroinfo/settings.py`:

```python
# Opción 1: Variables de entorno (recomendado para producción)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN  = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')

# Opción 2: Valores directos (solo desarrollo)
TWILIO_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_AUTH_TOKEN  = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
TWILIO_FROM_NUMBER = '+1XXXXXXXXXX'
```

| Variable | Descripción |
|---|---|
| `TWILIO_ACCOUNT_SID` | Account SID de Twilio |
| `TWILIO_AUTH_TOKEN` | Auth Token de Twilio |
| `TWILIO_FROM_NUMBER` | Número de teléfono Twilio (formato internacional, ej. `+19382046901`) |

El servicio `NotificacionServicio` transforma el teléfono del paciente a formato internacional colombiano (`+57XXXXXXXXXX`) antes del envío. Si las credenciales no están configuradas, registra un warning en logs y continúa sin error.

---

## 4. Configuración de autenticación por email

El sistema usa autenticación por email sin contraseña. Se configura mediante whitelist o dominio permitido en `quiroinfo/settings.py`:

```python
# Lista de correos autorizados (tiene prioridad sobre dominio)
EMAIL_WHITELIST = ["usuario1@hospital.com", "usuario2@hospital.com"]

# Dominio permitido (se usa si EMAIL_WHITELIST está vacío)
EMAIL_DOMINIO_PERMITIDO = 'hospital.gov.co'
```

| Variable | Descripción |
|---|---|
| `EMAIL_WHITELIST` | Lista de correos electrónicos autorizados. Si no está vacía, solo estos correos pueden acceder. |
| `EMAIL_DOMINIO_PERMITIDO` | Dominio permitido. Si `EMAIL_WHITELIST` está vacía, cualquier correo con este dominio puede acceder. |

Si ambos están vacíos, el login deniega acceso a todos los usuarios.

---

## 5. Migraciones

```bash
python manage.py migrate
```

Las migraciones incluyen:

| Migración | Descripción |
|---|---|
| `0001_initial` | Creación de tablas `pacientes` y `sesiones` |
| `0002_remove_sesion_descripcionotro` | Eliminación del campo `descripcionOtro` |
| `0003_sesion_labelotro` | Adición del campo `labelOtro` (default `'Otro'`) |
| `0004_alter_sesion_paciente` | Ajuste de FK paciente |
| `0005_eliminar_registroestado` | Eliminación del modelo `RegistroEstado` |
| `0006_alter_sesion_paciente` | Ajuste de FK paciente |
| `0007_sesion_paciente_cascade` | Cambio de FK a `on_delete=CASCADE` |
| `0008_paciente_telefono` | Adición del campo `telefono` en Paciente |

---

## 6. Archivos estáticos

El MVP usa **Tailwind CSS por CDN** directamente en los templates. No se requiere `collectstatic` ni build de assets.

Los CDN se cargan en cada template principal:

```html
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
<script src="https://unpkg.com/htmx.org@1.9.12"></script>
```

Para producción, considerar reemplazar los CDN por archivos locales o un build de Tailwind para mejor rendimiento y disponibilidad offline.

---

## 7. Iniciar el servidor

### Desarrollo

```bash
python manage.py runserver
```

### Producción

Usar un servidor WSGI como Gunicorn:

```bash
pip install gunicorn
gunicorn quiroinfo.wsgi:application --bind 0.0.0.0:8000
```

---

## 8. Checklist de producción

Antes de desplegar en producción, verificar los siguientes puntos:

| Item | Acción |
|---|---|
| `DEBUG` | Cambiar a `False` en `settings.py` |
| `SECRET_KEY` | Generar una clave secreta única y segura. No usar la clave por defecto. |
| `ALLOWED_HOSTS` | Restringir a los dominios/IPs del servidor. No dejar `['*']`. |
| HTTPS | Configurar SSL/TLS. Usar `SECURE_SSL_REDIRECT = True`. |
| CSRF | Configurar `CSRF_TRUSTED_ORIGINS` con los dominios permitidos. |
| Sesión | `SESSION_COOKIE_AGE = 7200` (120 min de inactividad, ya configurado). Considerar `SESSION_COOKIE_SECURE = True` con HTTPS. |
| Twilio | Mover credenciales a variables de entorno, no hardcodear en settings. |
| Email whitelist | Configurar `EMAIL_WHITELIST` o `EMAIL_DOMINIO_PERMITIDO` con los correos/dominio reales del hospital. |
| Base de datos | Usar credenciales seguras. Considerar conexión SSL a PostgreSQL. |
| Logging | Configurar logging a archivo o servicio externo para producción. |
| Tailwind CDN | Considerar reemplazar por build local para disponibilidad offline. |

---

## 9. Problemas comunes y solución

### Error de conexión a PostgreSQL

```
django.db.utils.OperationalError: could not connect to server
```

Verificar que PostgreSQL esté corriendo y que las credenciales en `DATABASES` sean correctas. Verificar que la base de datos `quiroinfo` exista.

### Migraciones pendientes

```
django.db.utils.ProgrammingError: relation "pacientes" does not exist
```

Ejecutar `python manage.py migrate` para aplicar todas las migraciones.

### SMS no se envían

1. Verificar que `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` y `TWILIO_FROM_NUMBER` estén configurados en `settings.py`.
2. Verificar que el paciente tenga un número de teléfono registrado (10 dígitos).
3. Revisar los logs del servidor — el servicio registra warnings si las credenciales faltan y errores si el envío falla.
4. Verificar que el paquete `twilio` esté instalado (`pip install twilio`).

### Login rechaza todos los correos

Verificar que `EMAIL_WHITELIST` o `EMAIL_DOMINIO_PERMITIDO` estén configurados en `settings.py`. Si ambos están vacíos, ningún correo será autorizado.

### El tablero no se actualiza

El tablero usa polling HTMX cada 15 segundos a `/tablero/fragmento/`. Si no se actualiza:
1. Verificar que el servidor esté corriendo.
2. Abrir la consola del navegador y verificar que las peticiones HTMX se estén ejecutando.
3. Si aparece el banner "Sin conexión" (rojo), hay un problema de red entre el navegador y el servidor.

### Error 409 al cargar pacientes programados

```
Carga en progreso, espere.
```

Otra carga está en ejecución. Esperar a que termine. El lock se libera automáticamente al finalizar (incluso si hay error).
