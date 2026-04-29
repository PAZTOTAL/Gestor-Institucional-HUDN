# Endpoints de la Aplicación

Referencia completa de todas las URLs del sistema Quiroinfo.

Las rutas se definen en tres archivos:
- `quiroinfo/urls.py` — URL root (incluye las apps y admin)
- `app_core/urls.py` — Rutas principales (tablero, gestión)
- `app_autenticacion/urls.py` — Rutas de autenticación

---

## Redirección raíz

| Propiedad | Valor |
|---|---|
| **URL** | `/` |
| **Método** | GET |
| **Vista** | `RedirectView` (Django genérica) |
| **Auth** | No |
| **Respuesta** | Redirect 302 → `/tablero/` |
| **Notas** | Redirección no permanente (`permanent=False`) |

---

## Tablero público

### GET `/tablero/`

| Propiedad | Valor |
|---|---|
| **Vista** | `TableroVista` |
| **Auth** | No |
| **Parámetros** | Ninguno |
| **Respuesta** | HTML completo — `tablero/tablero.html` con layout TV (100vh, flex). Incluye sesiones visibles ordenadas por `-actualizadoEn`. |
| **Notas** | Pantalla pública para proyectar en sala de espera. Incluye polling HTMX cada 15s al fragmento. |

### GET `/tablero/fragmento/`

| Propiedad | Valor |
|---|---|
| **Vista** | `TableroFragmentoVista` |
| **Auth** | No |
| **Parámetros** | Ninguno |
| **Respuesta** | Fragmento HTML — `tablero/fragmento.html` con la lista de sesiones visibles. |
| **Notas** | Endpoint consumido por el polling HTMX del tablero (`hx-get`, cada 15s). Retorna solo el contenido interno, no la página completa. |

---

## Autenticación

### GET/POST `/login/`

| Propiedad | Valor |
|---|---|
| **Vista** | `LoginVista` |
| **Auth** | No |
| **Método GET** | Muestra el formulario de login (`autenticacion/login.html`). |
| **Método POST** | Valida el email y crea sesión si está autorizado. |
| **Parámetros POST** | `email` (string, requerido) — Correo electrónico del funcionario. |
| **Respuesta POST exitosa** | Redirect 302 → `/gestion/` |
| **Respuesta POST error** | Re-render del formulario con mensaje de error: "Correo electrónico no válido." o "Correo electrónico no autorizado." |
| **Notas** | La autorización se valida contra `EMAIL_WHITELIST` (lista de correos) o `EMAIL_DOMINIO_PERMITIDO` (dominio) en `settings.py`. No usa contraseña. |

### POST `/logout/`

| Propiedad | Valor |
|---|---|
| **Vista** | `LogoutVista` |
| **Auth** | No (pero solo tiene sentido con sesión activa) |
| **Parámetros** | Ninguno (solo CSRF token) |
| **Respuesta** | Redirect 302 → `/login/` |
| **Notas** | Limpia la sesión completa con `request.session.flush()`. |

---

## Panel de gestión

### GET `/gestion/`

| Propiedad | Valor |
|---|---|
| **Vista** | `GestionVista` |
| **Auth** | Sí (`LoginRequeridoMixin`) |
| **Parámetros** | Ninguno |
| **Respuesta** | HTML completo — `gestion/gestion.html` con ambas tablas (Programados + En Sala). |
| **Contexto** | `pacientes` (ordenados: con sesión por `-actualizadoEn`, sin sesión por `identificacion`), `sesionesActivas`, `estados` (enum), `sesionPorPaciente` (dict). |
| **Notas** | Si no hay sesión activa, redirige a `/login/`. |

### POST `/gestion/sesiones/estado/`

| Propiedad | Valor |
|---|---|
| **Vista** | `AplicarEstadoVista` |
| **Auth** | Sí (`LoginRequeridoMixin`) |
| **Parámetros POST** | `pacienteId` (int, requerido) — PK del paciente. `estado` (string, requerido) — Valor del enum `EstadoQuirurgico` (`EN_PREPARACION`, `EN_CIRUGIA`, `EN_RECUPERACION`, `FINALIZADO`, `OTRO`). |
| **Respuesta exitosa** | Fragmento HTML — `gestion/fragmento_tablas.html` (swap HTMX). |
| **Respuesta error** | 400 "Datos incompletos." · 400 ValidationError · 500 "Error interno al actualizar el estado." |
| **Notas** | Crea la sesión si no existe, o actualiza el estado. Si el estado es `FINALIZADO`, marca la sesión como oculta. Envía SMS vía `NotificacionServicio` si el paciente tiene teléfono registrado. |

### POST `/gestion/pacientes/agregar/`

| Propiedad | Valor |
|---|---|
| **Vista** | `AgregarPacienteVista` |
| **Auth** | Sí (`LoginRequeridoMixin`) |
| **Parámetros POST** | `identificacion` (string, requerido) — Identificación del paciente. `nombre` (string, opcional) — Nombre completo. |
| **Respuesta exitosa** | Fragmento HTML — `gestion/fragmento_tablas.html`. |
| **Respuesta error** | 400 "La identificación es requerida." |
| **Notas** | Crea el paciente con `origen='URGENCIAS'`. Usa `get_or_create` para evitar duplicados por identificación. |

### POST `/gestion/pacientes/actualizar/`

| Propiedad | Valor |
|---|---|
| **Vista** | `ActualizarPacienteVista` |
| **Auth** | Sí (`LoginRequeridoMixin`) |
| **Parámetros POST** | `pacienteId` (int, requerido) — PK del paciente. `nuevaIdentificacion` (string, requerido) — Nueva identificación. `telefono` (string, opcional) — Teléfono de 10 dígitos. `labelOtro` (string, opcional) — Label personalizado para estado OTRO. `estadoOtro` (string, opcional) — Si presente junto con `labelOtro`, aplica estado OTRO. |
| **Respuesta exitosa** | Fragmento HTML — `gestion/fragmento_tablas.html`. |
| **Respuesta error** | 400 "Datos incompletos." · 400 "El teléfono debe tener exactamente 10 dígitos numéricos." |
| **Notas** | Actualiza identificación y teléfono del paciente. Si `estadoOtro` y `labelOtro` están presentes, aplica estado OTRO con el label personalizado y envía SMS. |

### POST `/gestion/programados/cargar/`

| Propiedad | Valor |
|---|---|
| **Vista** | `CargarProgramadosVista` |
| **Auth** | Sí (`LoginRequeridoMixin`) |
| **Parámetros POST** | Ninguno (solo CSRF token) |
| **Respuesta exitosa** | Fragmento HTML — `gestion/fragmento_tablas.html`. |
| **Respuesta error** | 409 "Carga en progreso, espere." · 500 "Error al cargar pacientes programados." |
| **Notas** | Elimina todos los pacientes existentes (CASCADE elimina sesiones) y carga los pacientes programados predefinidos. Usa lock de clase `_ejecutando` para prevenir ejecuciones concurrentes. |

---

## Admin Django

### `/admin/`

| Propiedad | Valor |
|---|---|
| **Vista** | Admin de Django (estándar) |
| **Auth** | Sí (superusuario Django) |
| **Notas** | Interfaz administrativa estándar de Django. Incluida en `quiroinfo/urls.py`. |

---

## Resumen de endpoints

| Método | URL | Vista | Auth |
|---|---|---|---|
| GET | `/` | `RedirectView` → `/tablero/` | No |
| GET | `/tablero/` | `TableroVista` | No |
| GET | `/tablero/fragmento/` | `TableroFragmentoVista` | No |
| GET/POST | `/login/` | `LoginVista` | No |
| POST | `/logout/` | `LogoutVista` | No |
| GET | `/gestion/` | `GestionVista` | Sí |
| POST | `/gestion/sesiones/estado/` | `AplicarEstadoVista` | Sí |
| POST | `/gestion/pacientes/agregar/` | `AgregarPacienteVista` | Sí |
| POST | `/gestion/pacientes/actualizar/` | `ActualizarPacienteVista` | Sí |
| POST | `/gestion/programados/cargar/` | `CargarProgramadosVista` | Sí |
| — | `/admin/` | Admin Django | Sí (superusuario) |
