# Guía de Usuario — CRUE Remisiones Pacientes

## 1. Inicio de sesión

1. Acceda a la URL del sistema (ej: `http://localhost:8000/login/`).
2. Ingrese su **nombre de usuario** y **contraseña**.
3. Haga clic en **Iniciar sesión**.
4. Si olvidó su contraseña, use el enlace **"Recuperar contraseña"** para recibir una contraseña temporal por correo electrónico.

---

## 2. Vista principal

Al iniciar sesión, se muestra la vista principal compuesta por tres áreas:

### 2.1 Sidebar izquierdo (panel lateral)

El sidebar es colapsable y contiene las siguientes secciones:

| Sección | Descripción |
|---|---|
| **Información del usuario** | Muestra nombre de usuario, nombre completo, fecha actual y botón "Salir" |
| **Exportar** | Enlace para exportar a Excel (PDF próximamente) |
| **Gestión** | Cambiar contraseña propia. Si el usuario es DIRECTOR, también aparece "Usuarios" |
| **Importar** | Formulario para importar registros desde un archivo Excel (.xlsx o .xls) |

### 2.2 Filtros

En la barra superior del contenido principal se encuentran tres modos de filtrado:

- **Por mes**: Seleccione mes y año. Opción de paginado (20 registros por página). Es el filtro por defecto.
- **Por rango de fechas**: Ingrese fecha "Desde" y fecha "Hasta".
- **Por documento**: Ingrese el número de documento del paciente.

Haga clic en **Buscar** para aplicar el filtro seleccionado.

### 2.3 Tabla de registros (Vista Rápida)

La tabla muestra los registros filtrados con las siguientes columnas:

| Columna | Descripción |
|---|---|
| Acciones | Botones de eliminar, editar, clonar y detalle |
| No | Número de fila |
| FECHA | Fecha y hora de ingreso (DD/MM/YYYY HH:MM) |
| NOMBRE PACIENTE | Nombre completo del paciente |
| TIPO DOC | Tipo de documento (CC, TI, CE, RC, CN, OTRO) |
| DOC | Número de documento |
| SEXO | M o F |
| EDAD | Edad con unidad (ej: 25 AÑOS) |
| GEST | Gestante (SI/NO) |
| TA | Tensión arterial |
| FC | Frecuencia cardíaca |
| FR | Frecuencia respiratoria |
| T | Temperatura |
| SPO2 | Saturación de oxígeno |
| GLASG | Escala de Glasgow |
| ACEPTADO | SI, NO o URG VITAL |

#### Colores de las filas

- **Verde**: Registro con ACEPTADO = SI
- **Rojo**: Registro con ACEPTADO = URG VITAL
- **Sin color**: Registro con ACEPTADO = NO

#### Botones de acción

| Botón | Icono | Descripción |
|---|---|---|
| Eliminar | 🗑️ Papelera roja | Elimina el registro (solo registros del día actual y propios) |
| Editar | ✏️ Lápiz | Abre el modal de edición (solo registros del día actual y propios) |
| Clonar | 📋 Copiar | Crea una copia del registro |
| Detalle | 👁️ Ojo | Expande/colapsa la fila de detalle con campos adicionales |

Al hacer clic en el botón **Detalle** (ojo), se expande una fila adicional que muestra: diagnóstico, especialidad, EPS, institución que reporta, municipio, médico refiere, médico HUDN, radio operador, observación, fecha de respuesta y oportunidad.

---

## 3. Crear nuevo registro

1. Haga clic en el botón **"Nuevo Registro"** (verde, con icono +) en la barra de filtros.
2. Se abre un modal con el formulario de remisión.
3. Complete los campos obligatorios (marcados con *):
   - **Fecha**: Fecha y hora de ingreso
   - **Nombre paciente**
   - **Tipo de documento** y **Documento**
   - **Sexo**, **Edad**, **Gestante**
4. Complete los campos opcionales según corresponda (signos vitales, diagnóstico, especialidad, EPS, etc.).
5. Haga clic en **Guardar**.
6. El registro se crea vía AJAX y la tabla se actualiza automáticamente.

---

## 4. Editar registro

- Solo se pueden editar registros **del día actual** y que hayan sido **creados por usted**.
- Los registros históricos (de días anteriores) son de **solo lectura**.
- Haga clic en el botón de **editar** (lápiz) en la fila del registro.
- Se abre el modal con los datos precargados.
- Modifique los campos necesarios y haga clic en **Guardar**.
- El campo **Radio Operador** es de solo lectura y se preserva del registro original.

---

## 5. Clonar registro

- Haga clic en el botón de **clonar** (copiar) en la fila del registro.
- Se abre el modal de creación con todos los campos copiados del registro original, **excepto**:
  - `fecha` (se deja vacía para ingresar la nueva)
  - `radio_operador` (se asigna automáticamente al guardar)
  - `aceptado` (se resetea)
  - `fecha_res` (se deja vacía)

---

## 6. Campo Especialidad

- Seleccione una especialidad de la lista desplegable.
- Si la especialidad no está en la lista, seleccione **"Otra (escribir)"**.
- Aparecerá un campo de texto adicional donde puede escribir la especialidad manualmente.

Especialidades disponibles: Cirugía de Columna, Cirugía General, Cirugía Plástica, Cirugía del Tórax, Cirugía Maxilofacial, Cirugía Vascular, Dermatología, Endocrinología, Epileptología, Genética Humana, Ginecología, Hematología, Infectología, Medicina Interna, Nefrología, Nefrología Pediátrica, Neurocirugía, Neurología, Neurología Pediátrica, Nutrición Clínica, Oculoplastia, Oftalmología, Ortopedia, Otorrinolaringología, Pediatría, Perinatología, Reumatología, Toxicología Clínica.

---

## 7. Campo Radio Operador

- Este campo es de **solo lectura** en el formulario.
- Se asigna automáticamente con el nombre completo del usuario que crea el registro.
- No se puede modificar al editar.

---

## 8. Validación de fechas

- La **fecha de respuesta** (`fecha_res`) debe ser **posterior** a la **fecha de ingreso** (`fecha`).
- Si se ingresa una fecha de respuesta anterior o igual a la fecha de ingreso, el sistema mostrará un error de validación.

---

## 9. Auto-llenado de fecha de respuesta

- Cuando el usuario escribe en el campo **Observación**, el sistema auto-llena automáticamente la **fecha de respuesta** con la fecha y hora actual si el campo estaba vacío.

---

## 10. Exportar a Excel

1. En el sidebar, sección **Exportar**, haga clic en **Excel**.
2. Se descarga un archivo `.xlsx` con los registros del filtro activo.
3. El archivo incluye todas las columnas de la remisión más la columna calculada **OPORTUNIDAD** (diferencia entre fecha de respuesta y fecha de ingreso en formato HH:MM).
4. Si no hay registros para el período seleccionado, se muestra un mensaje de error.

---

## 11. Importar desde Excel

1. En el sidebar, sección **Importar**, seleccione un archivo Excel (`.xlsx` o `.xls`).
2. El archivo debe seguir el formato **FRALG-062** con las columnas esperadas.
3. Haga clic en **Importar Excel**.
4. El sistema valida:
   - Estructura del archivo y encabezados
   - Formato de campos (edad, tensión arterial, Glasgow)
   - Duplicados (documento + fecha ya existentes en la base de datos)
   - Campos exclusivos (sexo, gestante, aceptado)
5. Si hay errores, se muestra el detalle del error con el número de fila.
6. La importación es **atómica**: si falla una fila, no se importa ninguna.

---

## 12. Gestión de usuarios (solo DIRECTOR)

Solo los usuarios con rol **DIRECTOR** pueden acceder a esta sección.

### Crear usuario
1. Vaya a **Gestión → Usuarios** en el sidebar.
2. Complete el formulario: nombre de usuario, nombre, apellido, correo, contraseña inicial y rol.
3. Haga clic en **Crear**.

### Editar usuario
1. En la lista de usuarios, haga clic en **Editar**.
2. Modifique nombre, apellido, correo o rol.
3. Haga clic en **Guardar**.

### Cambiar contraseña de un usuario
1. En la lista de usuarios, haga clic en **Cambiar contraseña**.
2. Ingrese la nueva contraseña y confírmela.
3. Haga clic en **Guardar**.

### Eliminar usuario
1. En la lista de usuarios, haga clic en **Eliminar**.
2. Confirme la eliminación.
3. No es posible eliminar su propio usuario.

---

## 13. Cambiar contraseña propia

1. Vaya a **Gestión → Contraseña** en el sidebar.
2. Ingrese su contraseña actual.
3. Ingrese la nueva contraseña (mínimo 8 caracteres) y confírmela.
4. Haga clic en **Cambiar**.
5. La sesión se mantiene activa después del cambio.

---

## 14. Registros históricos

- Los registros cuya fecha de ingreso corresponde a un **día anterior al actual** son considerados **históricos**.
- Los registros históricos son de **solo lectura**: no se pueden editar ni eliminar.
- El botón de eliminar aparece deshabilitado (gris) para registros históricos.
- Al intentar editar un registro histórico, el sistema muestra un mensaje de error.
