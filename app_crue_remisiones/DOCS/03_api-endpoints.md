# Referencia de Endpoints — CRUE Remisiones Pacientes

Todos los endpoints están definidos en `remisiones/urls.py` bajo el namespace `remisiones`.

---

## Autenticación

### `GET/POST /login/` — Autenticación de usuario

| Propiedad | Valor |
|---|---|
| **Vista** | `login_view` |
| **Nombre** | `remisiones:login` |
| **Método** | GET (mostrar formulario), POST (autenticar) |
| **Autenticación** | No |
| **Permisos** | Público |
| **Parámetros POST** | `username` (str), `password` (str) |
| **Respuesta GET** | Renderiza `remisiones/login.html` |
| **Respuesta POST éxito** | Redirect a `/` |
| **Respuesta POST error** | Renderiza `login.html` con mensaje "Usuario o contraseña incorrectos." |
| **Notas** | Si el usuario ya está autenticado, redirige a `/` |

---

### `POST /logout/` — Cierre de sesión

| Propiedad | Valor |
|---|---|
| **Vista** | `logout_view` |
| **Nombre** | `remisiones:logout` |
| **Método** | POST |
| **Autenticación** | No (Django maneja la sesión) |
| **Permisos** | Público |
| **Parámetros** | Ninguno (requiere CSRF token) |
| **Respuesta** | Redirect a `/login/` |

---

### `GET/POST /recuperar-password/` — Recuperar contraseña

| Propiedad | Valor |
|---|---|
| **Vista** | `recuperar_password_view` |
| **Nombre** | `remisiones:recuperar_password` |
| **Método** | GET (mostrar formulario), POST (procesar) |
| **Autenticación** | No |
| **Permisos** | Público |
| **Parámetros POST** | `username` (str) |
| **Respuesta** | Renderiza `recuperar_password.html` con mensaje genérico |
| **Notas** | Genera contraseña temporal y envía por email. No revela si el usuario existe (seguridad). |

---

## Vista principal

### `GET /` — Vista principal con tabla de remisiones

| Propiedad | Valor |
|---|---|
| **Vista** | `main_view` |
| **Nombre** | `remisiones:main` |
| **Método** | GET |
| **Autenticación** | Sí (`@login_required`) |
| **Permisos** | Cualquier usuario autenticado |
| **Parámetros GET** | Ver tabla de parámetros abajo |
| **Respuesta** | Renderiza `remisiones/main.html` |

**Parámetros de filtro (query string):**

| Parámetro | Tipo | Descripción | Valor por defecto |
|---|---|---|---|
| `filtro` | str | Tipo de filtro: `mes`, `rango`, `documento` | `mes` |
| `mes` | int | Mes (1-12) | Mes actual |
| `anio` | int | Año | Año actual |
| `desde` | str | Fecha inicio (YYYY-MM-DD) para filtro rango | `""` |
| `hasta` | str | Fecha fin (YYYY-MM-DD) para filtro rango | `""` |
| `doc` | str | Número de documento para filtro documento | `""` |
| `paginado` | str | `"True"` para activar paginación (20 por página) | `""` |
| `page` | int | Número de página | `1` |

---

## CRUD de Remisiones

### `POST /remisiones/nueva/` — Crear remisión (AJAX)

| Propiedad | Valor |
|---|---|
| **Vista** | `remision_create` |
| **Nombre** | `remisiones:remision_create` |
| **Método** | POST |
| **Autenticación** | Sí (`@login_required`) |
| **Permisos** | Cualquier usuario autenticado |
| **Content-Type** | `application/x-www-form-urlencoded` |
| **Parámetros POST** | Todos los campos del formulario `RemisionForm` |
| **Respuesta éxito** | `{"ok": true, "id": <int>}` (HTTP 200) |
| **Respuesta error** | `{"ok": false, "errors": {...}}` (HTTP 400) |
| **Notas** | `radio_operador` se asigna automáticamente al nombre completo del usuario. `created_by` se asigna al usuario actual. |

**Campos del formulario:**

| Campo | Obligatorio | Descripción |
|---|---|---|
| `fecha` | Sí | Fecha/hora de ingreso (formato `YYYY-MM-DDTHH:MM`) |
| `nombre` | Sí | Nombre del paciente |
| `tipo_doc` | Sí | Tipo de documento (CC, TI, CE, RC, CN, OTRO) |
| `doc` | Sí | Número de documento (solo dígitos) |
| `sexo` | Sí | Sexo (M, F) |
| `edad` | Sí | Edad (formato: `N AÑOS`, `N MESES`, `N DIAS`) |
| `gest` | Sí | Gestante (SI, NO) |
| `especialidad` | No | Especialidad médica |
| `diagnostico` | No | Diagnóstico |
| `ta` | No | Tensión arterial (formato: `120/80` o `NO REFIERE`) |
| `fc` | No | Frecuencia cardíaca |
| `fr` | No | Frecuencia respiratoria |
| `tm` | No | Temperatura |
| `spo2` | No | Saturación O2 |
| `glasg` | No | Glasgow (formato: `15/15` o `NO REFIERE`) |
| `eps` | No | EPS |
| `institucion_reporta` | No | Institución que reporta |
| `municipio` | No | Municipio |
| `medico_refiere` | No | Médico que refiere |
| `medico_hudn` | No | Médico HUDN que confirma |
| `radio_operador` | No | Radio operador (se sobreescribe automáticamente) |
| `observacion` | No | Observación |
| `aceptado` | Sí | Aceptado (SI, NO, URG VITAL) |
| `fecha_res` | No | Fecha/hora de respuesta (formato `YYYY-MM-DDTHH:MM`) |

---

### `GET /remisiones/<pk>/detalle/` — Detalle de remisión (AJAX)

| Propiedad | Valor |
|---|---|
| **Vista** | `remision_detail` |
| **Nombre** | `remisiones:remision_detail` |
| **Método** | GET |
| **Autenticación** | Sí (`@login_required`) |
| **Permisos** | Cualquier usuario autenticado |
| **Parámetros URL** | `pk` (int) — ID de la remisión |
| **Respuesta** | JSON con todos los campos de la remisión |

**Respuesta JSON:**

```json
{
  "id": 1,
  "fecha": "2025-01-15T08:30",
  "nombre": "JUAN PEREZ",
  "tipo_doc": "CC",
  "doc": "12345678",
  "sexo": "M",
  "especialidad": "MEDICINA INTERNA",
  "edad": "45 AÑOS",
  "gest": "NO",
  "diagnostico": "...",
  "ta": "120/80",
  "fc": "72",
  "fr": "18",
  "tm": "36°",
  "spo2": "98%",
  "glasg": "15/15",
  "eps": "NUEVA EPS",
  "institucion_reporta": "...",
  "municipio": "PASTO",
  "medico_refiere": "...",
  "medico_hudn": "...",
  "radio_operador": "...",
  "observacion": "...",
  "aceptado": "SI",
  "fecha_res": "2025-01-15T09:00",
  "oportunidad": "00:30",
  "es_editable": true,
  "es_propio": true
}
```

---

### `POST /remisiones/<pk>/editar/` — Editar remisión (AJAX)

| Propiedad | Valor |
|---|---|
| **Vista** | `remision_update` |
| **Nombre** | `remisiones:remision_update` |
| **Método** | POST |
| **Autenticación** | Sí (`@login_required`) |
| **Permisos** | Solo el propietario del registro (`created_by == request.user`) |
| **Parámetros URL** | `pk` (int) — ID de la remisión |
| **Parámetros POST** | Mismos campos que crear remisión |
| **Respuesta éxito** | `{"ok": true}` (HTTP 200) |
| **Respuesta error validación** | `{"ok": false, "errors": {...}}` (HTTP 400) |
| **Respuesta error permisos** | `{"ok": false, "error": "..."}` (HTTP 403) |
| **Restricciones** | Solo registros del día actual. Solo registros propios. `radio_operador` se preserva del original. |

---

### `POST /remisiones/<pk>/eliminar/` — Eliminar remisión (AJAX)

| Propiedad | Valor |
|---|---|
| **Vista** | `remision_delete` |
| **Nombre** | `remisiones:remision_delete` |
| **Método** | POST |
| **Autenticación** | Sí (`@login_required`) |
| **Permisos** | Solo el propietario del registro (`created_by == request.user`) |
| **Parámetros URL** | `pk` (int) — ID de la remisión |
| **Respuesta éxito** | `{"ok": true}` (HTTP 200) |
| **Respuesta error permisos** | `{"ok": false, "error": "..."}` (HTTP 403) |
| **Restricciones** | Solo registros del día actual. Solo registros propios. |

---

## Exportación e Importación

### `GET /exportar/excel/` — Exportar remisiones a Excel

| Propiedad | Valor |
|---|---|
| **Vista** | `exportar_excel` |
| **Nombre** | `remisiones:exportar_excel` |
| **Método** | GET |
| **Autenticación** | Sí (`@login_required`) |
| **Permisos** | Cualquier usuario autenticado |
| **Parámetros GET** | Mismos parámetros de filtro que la vista principal (`filtro`, `mes`, `anio`, `desde`, `hasta`, `doc`) |
| **Respuesta éxito** | Archivo `.xlsx` (Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) |
| **Respuesta error** | `{"ok": false, "error": "No hay registros..."}` (HTTP 400) |
| **Notas** | Incluye columna calculada OPORTUNIDAD. Nombre del archivo: `remisiones_YYYY-MM-DD.xlsx` |

---

### `POST /importar/excel/` — Importar remisiones desde Excel

| Propiedad | Valor |
|---|---|
| **Vista** | `importar_excel` |
| **Nombre** | `remisiones:importar_excel` |
| **Método** | POST |
| **Autenticación** | Sí (`@login_required`) |
| **Permisos** | Cualquier usuario autenticado |
| **Content-Type** | `multipart/form-data` |
| **Parámetros POST** | `archivo` (File — .xlsx o .xls) |
| **Respuesta éxito** | `{"ok": true, "importados": <int>}` (HTTP 200) |
| **Respuesta error** | `{"ok": false, "error": "..."}` (HTTP 400) |
| **Notas** | Formato FRALG-062. Importación atómica. Valida duplicados, formatos y campos exclusivos. |

---

## Gestión de usuarios

### `GET/POST /usuarios/` — Gestión de usuarios

| Propiedad | Valor |
|---|---|
| **Vista** | `usuarios_view` |
| **Nombre** | `remisiones:usuarios` |
| **Método** | GET (listar), POST (crear usuario) |
| **Autenticación** | Sí (`@login_required`) |
| **Permisos** | Solo DIRECTOR |
| **Parámetros POST** | `username`, `first_name`, `last_name`, `email`, `password`, `rol` |
| **Respuesta GET** | Renderiza `remisiones/usuarios.html` con lista de usuarios y formulario |
| **Respuesta POST éxito** | Redirect a `/usuarios/` con mensaje de éxito |
| **Respuesta POST error** | Renderiza formulario con errores |
| **Notas** | Usuarios no DIRECTOR son redirigidos a `/` con mensaje de error |

---

### `GET/POST /usuarios/<pk>/editar/` — Editar usuario

| Propiedad | Valor |
|---|---|
| **Vista** | `usuario_edit` |
| **Nombre** | `remisiones:usuario_edit` |
| **Método** | GET (mostrar formulario), POST (guardar cambios) |
| **Autenticación** | Sí (`@login_required`) |
| **Permisos** | Solo DIRECTOR |
| **Parámetros URL** | `pk` (int) — ID del usuario |
| **Parámetros POST** | `first_name`, `last_name`, `email`, `rol` |
| **Respuesta GET** | Renderiza `remisiones/usuario_editar.html` |
| **Respuesta POST éxito** | Redirect a `/usuarios/` |

---

### `GET/POST /usuarios/<pk>/cambiar-password/` — Cambiar contraseña de usuario

| Propiedad | Valor |
|---|---|
| **Vista** | `usuario_cambiar_password` |
| **Nombre** | `remisiones:usuario_cambiar_password` |
| **Método** | GET (mostrar formulario), POST (cambiar contraseña) |
| **Autenticación** | Sí (`@login_required`) |
| **Permisos** | Solo DIRECTOR |
| **Parámetros URL** | `pk` (int) — ID del usuario |
| **Parámetros POST** | `password_nueva`, `password_confirmacion` |
| **Respuesta GET** | Renderiza `remisiones/usuario_cambiar_password.html` |
| **Respuesta POST éxito** | Redirect a `/usuarios/` |
| **Validación** | La nueva contraseña y su confirmación deben coincidir. Mínimo 8 caracteres. |

---

### `POST /usuarios/<pk>/eliminar/` — Eliminar usuario

| Propiedad | Valor |
|---|---|
| **Vista** | `usuario_delete` |
| **Nombre** | `remisiones:usuario_delete` |
| **Método** | POST |
| **Autenticación** | Sí (`@login_required`) |
| **Permisos** | Solo DIRECTOR |
| **Parámetros URL** | `pk` (int) — ID del usuario |
| **Respuesta éxito** | `{"ok": true}` (HTTP 200) |
| **Respuesta error permisos** | `{"ok": false, "error": "No tiene permisos..."}` (HTTP 403) |
| **Respuesta error propio** | `{"ok": false, "error": "No puede eliminar su propio usuario."}` (HTTP 400) |

---

## Cambio de contraseña propia

### `GET/POST /cambiar-password/` — Cambiar contraseña propia

| Propiedad | Valor |
|---|---|
| **Vista** | `cambiar_password_view` |
| **Nombre** | `remisiones:cambiar_password` |
| **Método** | GET (mostrar formulario), POST (cambiar contraseña) |
| **Autenticación** | Sí (`@login_required`) |
| **Permisos** | Cualquier usuario autenticado |
| **Parámetros POST** | `password_actual`, `password_nueva`, `password_confirmacion` |
| **Respuesta GET** | Renderiza `remisiones/cambiar_password.html` |
| **Respuesta POST éxito** | Renderiza con mensaje "Contraseña cambiada correctamente." |
| **Respuesta POST error** | Renderiza con mensaje de error |
| **Validación** | Contraseña actual correcta. Nueva contraseña mínimo 8 caracteres. Confirmación debe coincidir. |
| **Notas** | La sesión se mantiene activa después del cambio (`update_session_auth_hash`). |
