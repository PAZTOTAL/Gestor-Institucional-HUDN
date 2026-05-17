# Guía de Despliegue — CRUE Remisiones Pacientes

## 1. Variables de entorno requeridas

| Variable | Descripción | Ejemplo | Obligatoria |
|---|---|---|---|
| `DB_NAME` | Nombre de la base de datos PostgreSQL | `crue_remisiones_db` | Sí |
| `DB_USER` | Usuario de PostgreSQL | `postgres` | Sí |
| `DB_PASSWORD` | Contraseña de PostgreSQL | `contraseña_segura` | Sí |
| `DB_HOST` | Host de PostgreSQL | `localhost` | Sí |
| `DB_PORT` | Puerto de PostgreSQL | `5432` | Sí |
| `SECRET_KEY` | Clave secreta de Django (mínimo 50 caracteres) | `django-insecure-...` | Sí (producción) |
| `DEBUG` | Modo debug (`True`/`False`) | `False` | Sí (producción) |
| `ALLOWED_HOSTS` | Hosts permitidos (separados por coma) | `midominio.com,172.20.10.250` | Sí (producción) |
| `CSRF_TRUSTED_ORIGINS` | Orígenes confiables para CSRF | `https://midominio.com` | Sí (producción) |

---

## 2. Configuración de PostgreSQL

### Crear base de datos y usuario

```sql
-- Conectar como superusuario de PostgreSQL
sudo -u postgres psql

-- Crear la base de datos
CREATE DATABASE crue_remisiones_db
    ENCODING 'UTF8'
    LC_COLLATE 'es_CO.UTF-8'
    LC_CTYPE 'es_CO.UTF-8';

-- Crear usuario dedicado
CREATE USER crue_user WITH PASSWORD 'contraseña_segura';

-- Configurar parámetros recomendados por Django
ALTER ROLE crue_user SET client_encoding TO 'utf8';
ALTER ROLE crue_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE crue_user SET timezone TO 'America/Bogota';

-- Otorgar permisos
GRANT ALL PRIVILEGES ON DATABASE crue_remisiones_db TO crue_user;

-- Salir
\q
```

### Verificar conexión

```bash
psql -h localhost -U crue_user -d crue_remisiones_db
```

---

## 3. Configuración de email

### Desarrollo (consola)

La configuración por defecto usa el backend de consola, que imprime los correos en la terminal:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Producción (SMTP)

Para producción, configure un servidor SMTP real en `settings.py` o mediante variables de entorno:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.ejemplo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'noreply@hudn.gov.co'
EMAIL_HOST_PASSWORD = 'contraseña_smtp'
DEFAULT_FROM_EMAIL = 'noreply@hudn.gov.co'
```

El sistema envía correos para la funcionalidad de **recuperación de contraseña** (`/recuperar-password/`).

---

## 4. Checklist de producción

Antes de desplegar en producción, verifique los siguientes puntos:

- [ ] **`DEBUG = False`** — Nunca dejar `True` en producción
- [ ] **`SECRET_KEY`** — Generar una clave secreta única y segura (no usar la de desarrollo)
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- [ ] **`ALLOWED_HOSTS`** — Configurar con los dominios/IPs reales del servidor
- [ ] **`CSRF_TRUSTED_ORIGINS`** — Configurar con los orígenes confiables (incluyendo protocolo)
- [ ] **Archivos estáticos** — Ejecutar `collectstatic` (ver sección 7)
- [ ] **Servidor WSGI** — Usar gunicorn o uwsgi (no `runserver`)
- [ ] **Proxy inverso** — Configurar nginx o Apache como proxy
- [ ] **HTTPS** — Configurar certificado SSL/TLS
- [ ] **Base de datos** — Usar usuario dedicado con permisos mínimos
- [ ] **Email SMTP** — Configurar servidor SMTP real
- [ ] **Backups** — Configurar respaldos automáticos de la base de datos
- [ ] **Logs** — Configurar logging de Django para producción

---

## 5. Servidor WSGI (gunicorn)

### Instalar gunicorn

```bash
pip install gunicorn
```

### Ejecutar con gunicorn

```bash
gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120
```

### Configuración con nginx (proxy inverso)

```nginx
server {
    listen 80;
    server_name midominio.com;

    location /static/ {
        alias /ruta/al/proyecto/staticfiles/;
    }

    location /media/ {
        alias /ruta/al/proyecto/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 6. Docker

El proyecto incluye un `Dockerfile` en el directorio `docker/`.

### Dockerfile existente

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/
```

### docker-compose.yml (ejemplo)

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: crue_remisiones_db
      POSTGRES_USER: crue_user
      POSTGRES_PASSWORD: contraseña_segura
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  web:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
    environment:
      - DB_NAME=crue_remisiones_db
      - DB_USER=crue_user
      - DB_PASSWORD=contraseña_segura
      - DB_HOST=db
      - DB_PORT=5432
      - SECRET_KEY=su-clave-secreta-de-produccion
      - DEBUG=False
      - ALLOWED_HOSTS=localhost,midominio.com
    ports:
      - "8000:8000"
    depends_on:
      - db

volumes:
  postgres_data:
```

### Ejecutar con Docker Compose

```bash
# Construir e iniciar
docker-compose up -d --build

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Recopilar archivos estáticos
docker-compose exec web python manage.py collectstatic --noinput
```

---

## 7. Migraciones

```bash
# Aplicar todas las migraciones pendientes
python manage.py migrate

# Ver estado de las migraciones
python manage.py showmigrations
```

Las migraciones existentes incluyen:
- `0001_initial.py` — Creación de modelos UsuarioCrue y Remision
- `0002_remision_especialidad_remision_especialidad_otra.py` — Agregar campo especialidad
- `0003_remove_especialidad_otra.py` — Eliminar campo especialidad_otra
- `0004_remove_especialidad_otra_field.py` — Limpieza del campo

---

## 8. Crear usuario administrador inicial

```bash
python manage.py createsuperuser
```

Después de crear el superusuario, acceda al admin de Django (`/admin/`) y asigne el rol **DIRECTOR** al usuario para que pueda gestionar otros usuarios desde la interfaz de la aplicación.

Alternativamente, puede hacerlo desde el shell de Django:

```bash
python manage.py shell
```

```python
from remisiones.models import UsuarioCrue
user = UsuarioCrue.objects.get(username='admin')
user.rol = 'DIRECTOR'
user.save()
```

---

## 9. Archivos estáticos

```bash
# Recopilar archivos estáticos en STATIC_ROOT (staticfiles/)
python manage.py collectstatic --noinput
```

La configuración de archivos estáticos en `settings.py`:

| Variable | Valor | Descripción |
|---|---|---|
| `STATIC_URL` | `/static/` | URL pública para archivos estáticos |
| `STATIC_ROOT` | `BASE_DIR / 'staticfiles'` | Directorio destino de `collectstatic` |
| `STATICFILES_DIRS` | `[BASE_DIR / 'static']` | Directorios adicionales de archivos estáticos |
| `MEDIA_URL` | `/media/` | URL pública para archivos subidos |
| `MEDIA_ROOT` | `BASE_DIR / 'media'` | Directorio de archivos subidos |

En producción, configure nginx para servir los archivos estáticos directamente (ver sección 5).
