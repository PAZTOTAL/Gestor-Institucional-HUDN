# Referencia de Endpoints (URLs)

---

## URLs del proyecto (config/urls.py)

| Ruta | Nombre | Método | Descripción |
|---|---|---|---|
| `/admin/` | — | GET | Panel de administración de Django |
| `/login/` | `login` | GET, POST | Inicio de sesión (LoginView de Django) |
| `/logout/` | `logout` | POST | Cierre de sesión (LogoutView de Django) |

---

## URLs de la aplicación traslados (traslados/urls.py)

### Vistas principales

| Ruta | Nombre | Método | Acceso | Descripción |
|---|---|---|---|---|
| `/` | `principal` | GET | Autenticado | Vista principal con sidebar, filtros y tabla |
| `/recuperar-contrasena/` | `recuperar-contrasena` | GET, POST | Público | Formulario de recuperación de contraseña |

**Parámetros de query string de `/`:**

| Parámetro | Tipo | Valor por defecto | Descripción |
|---|---|---|---|
| `mes` | int (1–12) | Mes actual | Mes a filtrar |
| `dia_desde` | int (1–31) | 1 | Día inicial del rango |
| `dia_hasta` | int (1–31) | Último día del mes | Día final del rango |

---

### CRUD de traslados (HTMX)

| Ruta | Nombre | Método | Acceso | Descripción |
|---|---|---|---|---|
| `/traslados/tabla/` | `tabla-traslados` | GET | Autenticado | Partial HTMX: tabla filtrada de registros |
| `/traslados/nuevo/` | `traslado-nuevo` | GET | Autenticado | Partial HTMX: modal con formulario vacío |
| `/traslados/nuevo/` | `traslado-nuevo` | POST | Autenticado | Crea registro; retorna tabla actualizada o modal con errores |
| `/traslados/<pk>/editar/` | `traslado-editar` | GET | Autenticado | Partial HTMX: modal con formulario precargado |
| `/traslados/<pk>/editar/` | `traslado-editar` | POST | Autenticado | Actualiza registro; retorna tabla actualizada o modal con errores |
| `/traslados/<pk>/confirmar-eliminar/` | `traslado-confirmar-eliminar` | GET | Autenticado | Partial HTMX: diálogo de confirmación de eliminación |
| `/traslados/<pk>/eliminar/` | `traslado-eliminar` | DELETE | Autenticado | Elimina registro; retorna tabla actualizada |

**Parámetros de `/traslados/tabla/`:** mismos que la vista principal (`mes`, `dia_desde`, `dia_hasta`).

**Parámetros de `/traslados/nuevo/` (GET):**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `mes` | int | Mes activo (para verificar si está cerrado) |

**Respuestas especiales:**
- **403**: El mes está cerrado (aplica a crear, editar y eliminar).
- **404**: Registro no encontrado (aplica a editar y eliminar).
- **Header `HX-Trigger: cerrarModal`**: Enviado tras guardar/eliminar exitosamente para cerrar el modal.

---

### Reportes

| Ruta | Nombre | Método | Acceso | Descripción |
|---|---|---|---|---|
| `/reportes/excel/` | `reporte-excel` | GET | Autenticado | Genera y descarga archivo Excel (.xlsx) |

**Parámetros de query string:**

| Parámetro | Tipo | Valor por defecto | Descripción |
|---|---|---|---|
| `mes` | int (1–12) | Mes actual | Mes a incluir en el reporte |
| `dia_desde` | int (1–31) | 1 | Día inicial del rango |
| `dia_hasta` | int (1–31) | Último día del mes | Día final del rango |

**Respuesta exitosa:**
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="traslados_<mes>.xlsx"`

**Respuesta de error (500):** Renderiza `error_reporte.html` con mensaje de error.

---

### Gestión de contraseñas

| Ruta | Nombre | Método | Acceso | Descripción |
|---|---|---|---|---|
| `/perfil/contrasena/` | `cambiar-contrasena` | GET | Autenticado | Formulario de cambio de contraseña propia |
| `/perfil/contrasena/` | `cambiar-contrasena` | POST | Autenticado | Procesa el cambio de contraseña propia |

**Campos del formulario POST:**

| Campo | Requerido | Descripción |
|---|---|---|
| `contrasena_actual` | Sí | Contraseña actual del usuario |
| `nueva_contrasena` | Sí | Nueva contraseña |
| `confirmar_contrasena` | Sí | Confirmación de la nueva contraseña |

---

### Gestión de usuarios (solo DIRECTOR)

| Ruta | Nombre | Método | Acceso | Descripción |
|---|---|---|---|---|
| `/usuarios/` | `usuarios` | GET | DIRECTOR | Listado de todos los usuarios |
| `/usuarios/nuevo/` | `usuario-nuevo` | GET, POST | DIRECTOR | Formulario y creación de usuario |
| `/usuarios/<pk>/contrasena/` | `usuario-contrasena` | GET, POST | DIRECTOR | Cambiar contraseña de otro usuario |
| `/usuarios/<pk>/eliminar/` | `usuario-eliminar` | GET, POST | DIRECTOR | Confirmación y eliminación de usuario |

**Campos de creación de usuario (POST `/usuarios/nuevo/`):**

| Campo | Requerido | Descripción |
|---|---|---|
| `username` | Sí | Nombre de usuario (único) |
| `password` | Sí | Contraseña inicial |
| `rol` | Sí | FUNCIONARIO o DIRECTOR |

**Respuesta 403:** Usuario autenticado no tiene rol DIRECTOR.

---

### Control de mes (solo DIRECTOR)

| Ruta | Nombre | Método | Acceso | Descripción |
|---|---|---|---|---|
| `/mes/<mes>/cerrar/` | `cerrar-mes` | POST | DIRECTOR | Cierra el mes indicado |

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `mes` | int (1–12) | Número del mes a cerrar |

**Respuestas:**
- **302**: Redirección a vista principal tras cerrar exitosamente.
- **403**: Usuario no es DIRECTOR.
- **404**: No existe ControlMes para el mes dado.
- **405**: Método no permitido (solo acepta POST).

---

### Limpieza del sistema (solo DIRECTOR)

| Ruta | Nombre | Método | Acceso | Descripción |
|---|---|---|---|---|
| `/sistema/limpiar/` | `limpiar-sistema` | GET | DIRECTOR | Muestra página de confirmación |
| `/sistema/limpiar/` | `limpiar-sistema` | POST | DIRECTOR | Ejecuta o cancela la limpieza |

**Campos del formulario POST:**

| Campo | Valor | Descripción |
|---|---|---|
| `accion` | `confirmar` | Ejecuta la limpieza (elimina todos los registros, restablece meses) |
| `accion` | `cancelar` | Redirige sin modificar datos |
