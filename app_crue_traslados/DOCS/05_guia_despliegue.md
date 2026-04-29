# Guía de Despliegue

---

## 1. Variables de entorno

El sistema lee las credenciales de base de datos desde un archivo `.env` ubicado en la raíz del proyecto (`app_crue_traslados/.env`). Se usa `python-dotenv` para cargarlas.

| Variable | Requerida | Valor por defecto | Descripción |
|---|---|---|---|
| `DB_NAME` | Sí | `traslados_db` | Nombre de la base de datos PostgreSQL |
| `DB_USER` | Sí | `postgres` | Usuario de PostgreSQL |
| `DB_PASSWORD` | Sí | (vacío) | Contraseña del usuario de PostgreSQL |
| `DB_HOST` | No | `127.0.0.1` | Host del servidor PostgreSQL |
| `DB_PORT` | No | `5432` | Puerto del servidor PostgreSQL |

Ejemplo de archivo `.env`:
```
DB_NAME=crue_traslados_db
DB_USER=postgres
DB_PASSWORD=mi_contraseña_segura
DB_HOST=127.0.0.1
DB_PORT=5432
```

El archivo `.env` está incluido en `.gitignore` y no debe versionarse. Se proporciona `.env.example` como plantilla.

---

## 2. Configuración de la base de datos PostgreSQL

### Crear la base de datos y el usuario

```bash
# Conectar como superusuario de PostgreSQL
sudo -u postgres psql

# Crear la base de datos
CREATE DATABASE crue_traslados_db;

# (Opcional) Crear un usuario dedicado
CREATE USER traslados_user WITH PASSWORD 'contraseña_segura';
GRANT ALL PRIVILEGES ON DATABASE crue_traslados_db TO traslados_user;
ALTER DATABASE crue_traslados_db OWNER TO traslados_user;

\q
```

### Aplicar migraciones

```bash
cd app_crue_traslados
python manage.py migrate
```

Las 12 filas de `ControlMes` se crean automáticamente tras la migración (señal `post_migrate` en `apps.py`). También se puede ejecutar manualmente:

```bash
python manage.py inicializar_meses
```

### Crear el superusuario inicial

```bash
python manage.py createsuperuser
```

Asignar el rol DIRECTOR al superusuario desde el panel admin (`/admin/`) o directamente en la base de datos.

---

## 3. Checklist de producción

### Configuración de Django (settings.py)

- [ ] **DEBUG = False**: Cambiar `DEBUG = True` a `DEBUG = False`.
- [ ] **SECRET_KEY**: Reemplazar la clave insegura por una clave secreta generada. Moverla a una variable de entorno:
  ```python
  SECRET_KEY = os.environ.get ('SECRET_KEY', '')
  ```
- [ ] **ALLOWED_HOSTS**: Restringir a los dominios/IPs del servidor:
  ```python
  ALLOWED_HOSTS = ['mi-dominio.com', '192.168.1.100']
  ```
- [ ] **PASSWORD_HASHERS**: Eliminar o condicionar el hasher MD5 (solo para tests):
  ```python
  # Ya está condicionado: solo se activa si 'test' está en sys.argv
  ```

### Archivos estáticos

```bash
python manage.py collectstatic
```

Configurar el servidor web (Nginx, Apache) para servir archivos desde `STATIC_ROOT` (`staticfiles/`).

### Servidor WSGI

Usar Gunicorn como servidor WSGI en producción:

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Servidor web (Nginx)

Ejemplo de configuración Nginx como proxy reverso:

```nginx
server {
    listen 80;
    server_name mi-dominio.com;

    location /static/ {
        alias /ruta/al/proyecto/app_crue_traslados/staticfiles/;
    }

    location /media/ {
        alias /ruta/al/proyecto/app_crue_traslados/media/;
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

### Seguridad adicional

- [ ] Configurar HTTPS (certificado SSL/TLS).
- [ ] Agregar headers de seguridad en settings.py:
  ```python
  SECURE_BROWSER_XSS_FILTER = True
  SECURE_CONTENT_TYPE_NOSNIFF = True
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  X_FRAME_OPTIONS = 'DENY'
  ```
- [ ] Configurar backups periódicos de la base de datos PostgreSQL:
  ```bash
  pg_dump -U postgres crue_traslados_db > backup_$(date +%Y%m%d).sql
  ```

### Monitoreo

- [ ] Configurar logging de Django para producción (archivo o servicio externo).
- [ ] Monitorear el proceso Gunicorn (systemd, supervisor, o similar).

---

## 4. Dependencias del sistema

### Python (requirements.txt)

```
django==5.2.4
openpyxl==3.1.5
psycopg2-binary==2.9.10
python-dotenv==1.1.0
```

Para producción, considerar reemplazar `psycopg2-binary` por `psycopg2` (compilado desde fuente, más estable en producción).

### Sistema operativo

- Python 3.12+
- PostgreSQL 14+
- Nginx (o Apache) como proxy reverso

### CDN (cargados en el navegador)

- Tailwind CSS (cdn.tailwindcss.com)
- HTMX 1.9.12 (unpkg.com)
- Alpine.js 3.x (cdn.jsdelivr.net)
- Bootstrap Icons 1.11.3 (cdn.jsdelivr.net)

Para producción sin acceso a internet, descargar estos archivos y servirlos como estáticos locales.
