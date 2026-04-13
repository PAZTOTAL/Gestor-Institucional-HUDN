Consulta externa de contratos - App independiente (Django)

Este software ya no depende del back/front principal.
Incluye:
- Frontend (index.html, app.js, styles.css)
- API propia (Django 5.2.10)
- Conexión propia a SQL Server y FTP/NAS

Instalación:
1. Copiar .env.example a .env y completar credenciales.
2. Tener Python 3.13+ instalado.
3. En esta carpeta ejecutar: py -m pip install -r requirements.txt
4. Ejecutar: py manage.py runserver 0.0.0.0:3030
5. Abrir: http://localhost:3030

Despliegue rápido (copiar carpeta):
1. Copiar toda la carpeta a la máquina destino.
2. Crear/ajustar archivo `.env` en la raíz.
3. Ejecutar `start.bat`.
4. Abrir en navegador: `http://IP_DEL_EQUIPO:3030`

Portabilidad (mover a otra carpeta/servidor):
- Esta carpeta se puede mover completa y seguirá funcionando.
- No usa rutas absolutas.
- Para llevarla a otro equipo, copia esta carpeta e instala dependencias Python.
- La librería de PDF se sirve localmente desde `assets/pdf-lib.min.js` (sin CDN).

Uso:
1. Ingresar cédula, mes y año.
2. Clic en "Ver soportes".
3. En el modal, escoger contrato.
4. Se genera un PDF único con los soportes del contrato elegido.

Endpoints internos de esta app:
- GET /api/consulta/contratos/:identificacion
- GET /api/consulta/documentos/:ide_contratista_int
- GET /api/consulta/documento?ide=:ide&idDoc=:idDoc
