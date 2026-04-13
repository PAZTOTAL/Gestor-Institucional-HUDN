# MVP - Generador de Certificados Laborales (Django)

Este proyecto genera certificados Word (`.docx`) usando SQL Server y plantillas locales.

## 1) Configurar variables (.env)

Crea `mvp\.env` (puedes copiar desde `mvp\.env.example`):

```env
DB_HOST=localhost
DB_PORT=1433
DB_USER=sa
DB_PASSWORD=tu_password
DB_NAME=contratos
DB_SCHEMA=dbo
DB_MAX_CONTRACT_YEAR=2026
DB_ENCRYPT=false
DB_TRUST_SERVER_CERTIFICATE=true
DB_CONNECTION_TIMEOUT_MS=30000
DB_REQUEST_TIMEOUT_MS=120000
DB_METADATA_CACHE_TTL_MS=300000
DB_INDEX_RETRIES=4

DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=*
DJANGO_SECRET_KEY=change-me
```

## 2) Estructura de base de datos esperada

La aplicación consulta automáticamente tablas con patrón `contratos_YYYY` (hasta `DB_MAX_CONTRACT_YEAR`).

Columnas mínimas por tabla:

- `razon_social`
- `cedula_nit`
- `no_contrato`
- `valor_cto`

Columnas opcionales:

- `objeto_ctto`
- `tipo_vinculacion`
- `fecha_firma`
- `fecha_inicio`
- `fecha_term`
- `valorejecutado`

## 3) Instalar dependencias

```bash
cd mvp
py -m pip install -r requirements.txt
```

## 4) Probar conexión e índices

```bash
cd mvp
py manage.py db_test
py manage.py db_index_cedula
```

## 5) Ejecutar aplicación

```bash
cd mvp
py manage.py runserver 0.0.0.0:3001
```

Abrir en navegador:

- `http://localhost:3001/`

## 6) API

- `GET /api/health`
- `GET /api/empleados/<cedula>`
- `POST /api/certificados`

## 7) Variables de plantilla Word

### Encabezado

- `{{nombre}}`
- `{{cedula}}`
- `{{cargo}}`
- `{{objeto_ctto}}`

### Fecha

- `{{dia}}`
- `{{mes}}`
- `{{anio}}`

### Tabla de contratos

- Col 1: `{{#contratos}}{{contratoNo}}`
- Col 2: `{{firmaContrato}}`
- Col 3: `{{fechaInicio}}`
- Col 4: `{{fechaTerminacion}}`
- Col 5: `{{valor}}{{/contratos}}`

