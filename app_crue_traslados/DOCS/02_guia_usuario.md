# Guía de Usuario

---

## 1. Inicio de sesión

1. Acceder a la URL del sistema (ej. `http://localhost:8000/`).
2. Si no hay sesión activa, el sistema redirige a la pantalla de login.
3. Ingresar **Usuario** y **Contraseña**.
4. Hacer clic en **Ingresar**.
5. El botón **Cancelar** limpia los campos del formulario.
6. Si las credenciales son incorrectas, se muestra un mensaje de error.

### Recuperar contraseña

1. En la pantalla de login, hacer clic en **Recuperar Contraseña**.
2. Ingresar el nombre de usuario.
3. El sistema muestra un mensaje indicando que debe contactar al DIRECTOR para restablecer la contraseña.

---

## 2. Vista principal

Tras iniciar sesión, se muestra la vista principal con tres áreas:

### Panel lateral izquierdo (sidebar)

Visible para todos los usuarios:
- **Nombre de usuario** y **fecha actual**
- **Reportes** (menú colapsable): opción **Excel**
- **Gestión** (menú colapsable): opción **Contraseña**
- **Botón Salir**: cierra la sesión

Visible solo para DIRECTOR:
- **Gestión > Usuarios**: acceso a la gestión de usuarios
- **Limpiar datos del sistema**: limpieza anual

### Barra de título

- Logo del hospital
- Título: "REGISTRO DE SERVICIO DE TRASLADO DE PACIENTES"
- Fecha actual y nombre del usuario

### Barra de filtros

- **Selector de mes**: muestra los meses en español (Enero, Febrero, ...). Solo permite seleccionar meses hasta el mes actual.
- **Día Desde / Día Hasta**: rango de días dentro del mes seleccionado.
- **Botón Cerrar mes** (solo DIRECTOR): cierra el mes seleccionado.
- **Indicador de estado**: muestra si el mes está ABIERTO o CERRADO.

Al cambiar cualquier filtro, la tabla se actualiza automáticamente sin recargar la página.

### Tabla de registros

Columnas: Acciones | Fecha | Hora Reporte | Hora de Egreso | Hora de Ingreso | Nombre de Paciente | Documento | Servicio | Quien Reporta | Destino | Procedimiento | Médico | Conductor | Radio Operador | Ambulancia de Traslado | Observación

---

## 3. Operaciones CRUD (crear, editar, eliminar)

### Crear un registro

1. Hacer clic en el botón **[+] Adicionar** (encima de la tabla).
2. Se abre un modal con el formulario vacío.
3. Completar los campos. Los campos obligatorios están marcados con asterisco rojo (*): Fecha, Hora Reporte, Nombre de Paciente, Documento.
4. Hacer clic en **Guardar**.
5. Si hay errores de validación, se muestran debajo de cada campo.
6. Si los datos son válidos, el registro se guarda y la tabla se actualiza.

### Editar un registro

Opción A: Hacer clic en el botón de **editar** (ícono de lápiz) en la columna Acciones.
Opción B: Hacer **doble clic** sobre la fila del registro.

Se abre el modal con los datos precargados. Modificar los campos necesarios y hacer clic en **Guardar**.

### Eliminar un registro

1. Hacer clic en el botón de **eliminar** (ícono de papelera) en la columna Acciones.
2. Se muestra un diálogo de confirmación con el nombre del paciente y la fecha.
3. Hacer clic en **Eliminar** para confirmar, o **Cancelar** para abortar.

### Restricciones de mes cerrado

Cuando un mes está CERRADO:
- Los botones Adicionar, Editar y Eliminar se deshabilitan (aparecen en gris).
- El doble clic sobre filas se ignora silenciosamente.
- Cualquier intento de operación retorna un error 403.

---

## 4. Reportes

### Descargar reporte Excel

1. En el sidebar, abrir el menú **Reportes**.
2. Hacer clic en **Excel**.
3. Se descarga un archivo `traslados_<mes>.xlsx` con los registros del filtro activo.
4. El archivo contiene encabezados en español y una fila por registro.
5. Si no hay registros, el archivo contiene solo los encabezados.

---

## 5. Cambiar contraseña propia

1. En el sidebar, abrir el menú **Gestión**.
2. Hacer clic en **Contraseña**.
3. Ingresar la contraseña actual, la nueva contraseña y su confirmación.
4. Hacer clic en **Guardar contraseña**.
5. Si la contraseña actual es incorrecta o las nuevas no coinciden, se muestra un error.
6. Si los datos son válidos, la contraseña se actualiza y la sesión se mantiene activa.

---

## 6. Funciones exclusivas del DIRECTOR

### Cerrar un mes

1. Seleccionar el mes deseado en el selector de filtros.
2. Hacer clic en el botón **Cerrar mes** (en la barra de filtros).
3. El mes cambia a estado CERRADO. Los registros de ese mes quedan protegidos contra modificaciones.
4. No existe operación de "reabrir" un mes. Para restablecer todos los meses, usar la limpieza anual.

### Gestión de usuarios

1. En el sidebar, abrir **Gestión > Usuarios**.
2. Se muestra el formulario de creación y la tabla de usuarios existentes.

**Crear usuario:**
- Ingresar nombre de usuario, contraseña inicial y rol (FUNCIONARIO o DIRECTOR).
- Hacer clic en **Crear Usuario**.
- Si el nombre de usuario ya existe, se muestra un error.

**Cambiar contraseña de un usuario:**
- Hacer clic en **Cambiar contraseña** junto al usuario deseado.
- Ingresar la nueva contraseña y su confirmación (no se requiere la contraseña actual).
- Hacer clic en **Guardar contraseña**.

**Eliminar un usuario:**
- Hacer clic en **Eliminar** junto al usuario deseado.
- Confirmar en el diálogo de confirmación.
- El DIRECTOR no puede eliminarse a sí mismo.

### Limpieza anual de datos

1. En el sidebar, hacer clic en **Limpiar datos del sistema**.
2. El sistema sugiere descargar los reportes Excel antes de continuar.
3. Leer la advertencia de acción irreversible.
4. Hacer clic en **Sí, limpiar todos los datos** para confirmar, o **Cancelar** para abortar.
5. Al confirmar: se eliminan todos los registros de traslados y se restablecen todos los meses a ABIERTO.
