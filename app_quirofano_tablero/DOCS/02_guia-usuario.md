# Guía de Usuario — Quiroinfo

## Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Acceso al Sistema](#2-acceso-al-sistema)
3. [Panel de Gestión](#3-panel-de-gestión)
4. [Gestión de Estados](#4-gestión-de-estados)
5. [Editar Paciente](#5-editar-paciente)
6. [Botón OTRO](#6-botón-otro)
7. [Agregar Paciente de Urgencias](#7-agregar-paciente-de-urgencias)
8. [Cargar Pacientes Programados](#8-cargar-pacientes-programados)
9. [Tablero Público](#9-tablero-público)
10. [Notificaciones SMS](#10-notificaciones-sms)
11. [Preguntas Frecuentes](#11-preguntas-frecuentes)

---

## 1. Introducción

Quiroinfo es un sistema de seguimiento de estado quirúrgico diseñado para hospitales. Permite al personal del hospital (Funcionarios) registrar y actualizar el estado de los pacientes durante su proceso quirúrgico, y muestra esa información en tiempo real en un tablero público visible para los familiares en la sala de espera.

### ¿Qué hace Quiroinfo?

- Muestra una lista de pacientes programados para cirugía.
- Permite cambiar el estado de cada paciente con un solo clic (En preparación, En cirugía, En recuperación, Finalizado, Otro).
- Proyecta un tablero en pantallas TV de la sala de espera con el estado actualizado de cada paciente.
- Envía notificaciones SMS automáticas a los familiares cuando el estado de un paciente cambia.

### ¿Quién lo usa?

- **Funcionarios**: Personal del hospital autorizado que opera el Panel de Gestión. Requieren inicio de sesión.
- **Familiares**: Consultan el Tablero Público en las pantallas de la sala de espera. No requieren inicio de sesión.

---

## 2. Acceso al Sistema

### Iniciar sesión

1. Abra el navegador y vaya a la dirección del sistema (por ejemplo: `https://quiroinfo.hospital.co/gestion/`).
2. El sistema mostrará la pantalla de **Iniciar sesión**.
3. Ingrese su **correo electrónico** institucional en el campo correspondiente.
4. Haga clic en **Entrar**.

### ¿Qué correos están autorizados?

El acceso está controlado de dos formas:

- **Lista blanca (whitelist)**: Si su correo aparece en la lista de correos autorizados configurada por el administrador, podrá ingresar directamente.
- **Dominio permitido**: Si no hay lista blanca, el sistema verifica que su correo pertenezca al dominio institucional autorizado (por ejemplo, `@hospital.gov.co`).

Si su correo no está autorizado, verá el mensaje: *"Correo electrónico no autorizado."*

> **Nota:** No se requiere contraseña. La autenticación se basa únicamente en el correo electrónico.

### Cierre de sesión

- En la esquina superior derecha del Panel de Gestión encontrará el enlace **Cerrar sesión**.
- Haga clic en él para salir del sistema.

### Expiración de sesión

La sesión se cierra automáticamente después de **120 minutos (2 horas) de inactividad**. Si esto ocurre, el sistema lo redirigirá a la pantalla de inicio de sesión la próxima vez que intente realizar una acción.

> **Tip:** Si trabaja turnos largos, simplemente vuelva a iniciar sesión cuando el sistema se lo solicite. No se pierde información de los pacientes.

---

## 3. Panel de Gestión

El Panel de Gestión es la vista principal de trabajo para los Funcionarios. Se accede desde `/gestion/` después de iniciar sesión.

### Estructura de la pantalla

La pantalla se divide en **dos tablas lado a lado**:

| Columna izquierda | Columna derecha |
|---|---|
| **Pacientes programados** | **Pacientes en sala** |
| Lista completa de pacientes con botones de estado y acciones | Resumen de pacientes con sesión activa (estilo oscuro) |

#### Tabla izquierda — Pacientes programados

Muestra **todos** los pacientes registrados en el sistema. Para cada paciente se ve:

- **Identificación**: Código o documento del paciente.
- **Nombre**: Nombre del paciente (si está disponible).
- **Estado**: Botones de colores para cambiar el estado quirúrgico.
- **Acciones**: Botón "Editar" para abrir el modal de edición.

Los pacientes que ya tienen un estado asignado aparecen primero, ordenados por la hora de su última actualización (más reciente arriba). Los pacientes sin estado aparecen al final, ordenados por identificación.

Debajo de la tabla se encuentran dos botones adicionales:
- **+ Adicionar paciente**: Para agregar pacientes de urgencias.
- **Cargar pacientes programados**: Para recargar la lista desde la fuente externa.

#### Tabla derecha — Pacientes en sala

Muestra únicamente los pacientes que tienen una sesión activa (es decir, que ya se les asignó un estado). Tiene fondo oscuro para diferenciarse visualmente. Muestra:

- **Identificación** del paciente.
- **Estado** actual con badge de color.
- **Última actualización**: Fecha y hora del último cambio de estado.

> **Nota:** Esta tabla es solo de lectura. Para cambiar estados, use la tabla izquierda.

---

## 4. Gestión de Estados

### Estados disponibles

Cada paciente puede tener uno de los siguientes estados:

| Estado | Color | Significado |
|---|---|---|
| **En preparación** | Amarillo | El paciente está siendo preparado para la cirugía. |
| **En cirugía** | Naranja | El paciente está en el quirófano. |
| **En recuperación** | Azul | La cirugía terminó y el paciente está en recuperación. |
| **Finalizado** | Gris | El proceso quirúrgico ha concluido completamente. |
| **Otro** | Morado | Estado personalizado definido por el Funcionario. |

### Cómo cambiar el estado de un paciente

1. En la tabla **Pacientes programados**, ubique la fila del paciente.
2. En la columna **Estado**, verá los cinco botones de estado.
3. Haga clic en el botón del estado deseado.
4. El sistema actualiza el estado **inmediatamente**, sin recargar la página.
5. El botón seleccionado se resalta con su color correspondiente y un borde (ring).
6. La tabla **Pacientes en sala** (derecha) se actualiza automáticamente para reflejar el cambio.

### ¿Qué pasa al cambiar un estado?

- Se crea o actualiza la sesión del paciente en la base de datos.
- El paciente aparece (o se actualiza) en la tabla **Pacientes en sala**.
- El **Tablero Público** reflejará el cambio en los próximos 15 segundos.
- Si el paciente tiene un **teléfono registrado**, se envía un SMS automático al familiar.

### Estado FINALIZADO

Cuando un paciente pasa a **Finalizado**, su sesión se marca como oculta. Esto significa que:

- El paciente **desaparece del Tablero Público** (los familiares ya no lo ven).
- El paciente **desaparece de la tabla Pacientes en sala**.
- El paciente **sigue visible** en la tabla Pacientes programados con el botón Finalizado resaltado.

> **Tip:** Use el estado Finalizado cuando el paciente ya fue entregado a sus familiares y no necesita seguimiento público.

---

## 5. Editar Paciente

### Cómo abrir el modal de edición

1. En la tabla **Pacientes programados**, ubique la fila del paciente que desea editar.
2. Haga clic en el botón **Editar** (texto azul, columna Acciones).
3. Se abrirá una ventana modal sobre la pantalla.

### Campos del modal

| Campo | Tipo | Descripción |
|---|---|---|
| **Identificación** | Editable (texto) | Código o documento del paciente. Obligatorio. Máximo 50 caracteres. |
| **Nombre** | Solo lectura | Nombre del paciente. No se puede modificar desde el modal. |
| **Teléfono para notificaciones** | Editable (texto) | Número de celular colombiano para enviar SMS al familiar. Opcional. |
| **Estado** | Editable (texto) | Label personalizado del estado. Se pre-carga con el estado actual. |

### Reglas de validación

- **Identificación**: No puede estar vacío. Si lo deja en blanco y presiona Guardar, verá un mensaje de error en rojo y el modal no se cerrará.
- **Teléfono**: Debe tener exactamente **10 dígitos numéricos** (formato celular colombiano, ejemplo: `3176753151`). Si ingresa letras o un número con más o menos de 10 dígitos, verá un mensaje de error. Puede dejarlo vacío si no desea enviar notificaciones SMS.
- **Estado**: Si modifica este campo, al guardar el sistema cambiará el estado del paciente a **OTRO** con el texto que usted escribió como etiqueta personalizada. Si no lo modifica, el estado del paciente no cambia.

### Cómo guardar

1. Realice los cambios deseados.
2. Haga clic en **Guardar**.
3. Si los datos son válidos, el modal se cierra y las tablas se actualizan automáticamente.
4. Si hay un error de validación, el modal permanece abierto con el mensaje de error visible.

### Cómo cancelar

- Haga clic en **Cancelar** para cerrar el modal sin guardar cambios.

---

## 6. Botón OTRO

El botón **Otro** (morado) permite asignar un estado personalizado a un paciente. Es útil para situaciones que no encajan en los cuatro estados estándar.

### Comportamiento del botón

- Al hacer clic en **Otro**, el sistema aplica el estado OTRO inmediatamente, igual que los demás botones. No se abre ningún formulario adicional.
- El texto visible en el botón se lee desde la base de datos. Por defecto muestra "Otro".

### Cómo personalizar la etiqueta

1. Haga clic en **Editar** en la fila del paciente.
2. En el campo **Estado** del modal, escriba el texto personalizado que desea mostrar (por ejemplo: "En espera de cama", "Pendiente de exámenes").
3. Haga clic en **Guardar**.
4. El botón OTRO ahora mostrará el texto personalizado en lugar de "Otro".
5. Este texto también se verá en la tabla **Pacientes en sala** y en el **Tablero Público**.

> **Nota:** El texto personalizado se guarda en la base de datos y se mantiene hasta que usted lo cambie nuevamente. Máximo 50 caracteres.

---

## 7. Agregar Paciente de Urgencias

Cuando llega un paciente de urgencias que no estaba en la lista de programados, puede agregarlo manualmente.

### Pasos

1. En la parte inferior de la tabla **Pacientes programados**, haga clic en **+ Adicionar paciente**.
2. Se desplegará un pequeño formulario con dos campos:
   - **Identificación** (obligatorio): Ingrese el código o documento del paciente.
   - **Nombre** (opcional): Ingrese el nombre del paciente.
3. Haga clic en **Agregar**.
4. El paciente aparecerá en la tabla de Pacientes programados, listo para asignarle un estado.

> **Nota:** Si ya existe un paciente con la misma identificación, el sistema no creará un duplicado.

---

## 8. Cargar Pacientes Programados

Este botón permite recargar la lista completa de pacientes programados desde la fuente de datos externa del hospital.

### Pasos

1. En la parte inferior de la tabla **Pacientes programados**, haga clic en el botón verde **Cargar pacientes programados**.
2. Aparecerá un mensaje de confirmación: **"Va a limpiar la tabla, ¿Está seguro?"**
3. Si hace clic en **Aceptar**:
   - El sistema **elimina todos los pacientes** y sus sesiones asociadas.
   - Carga los nuevos pacientes programados desde la fuente externa.
   - Las tablas se actualizan automáticamente.
   - Durante la carga, el botón muestra un spinner y el texto "Cargando..." y no se puede presionar de nuevo.
4. Si hace clic en **Cancelar**, no ocurre nada.

> **⚠ Importante:** Esta acción **elimina todos los datos actuales** (pacientes, estados, sesiones). Úsela solo al inicio de la jornada o cuando necesite recargar la programación completa. Los pacientes de urgencias agregados manualmente también se eliminarán.

---

## 9. Tablero Público

El Tablero Público es la pantalla que ven los familiares en la sala de espera. Está diseñado para proyectarse en televisores o pantallas grandes.

### Cómo acceder

- Abra un navegador y vaya a `/tablero/` (por ejemplo: `https://quiroinfo.hospital.co/tablero/`).
- **No requiere inicio de sesión.** Cualquier persona con acceso a la URL puede verlo.

### ¿Qué muestra?

Para cada paciente con sesión activa, el tablero muestra:

- **Identificación**: Código o documento del paciente.
- **Estado**: Badge de color con el nombre del estado (o el texto personalizado si es OTRO).
- **Hora**: Hora de la última actualización en formato de 12 horas (ejemplo: "3:05 pm").

### Características de la pantalla

- **Actualización automática**: El tablero consulta al servidor cada **15 segundos** y se actualiza sin intervención manual.
- **Sin scroll**: El contenido se ajusta al 100% de la pantalla. Las filas se distribuyen equitativamente en la altura disponible.
- **Fuentes escalables**: El tamaño del texto se adapta automáticamente al tamaño de la pantalla, usando unidades relativas al viewport.
- **Fondo oscuro**: Diseñado para buena legibilidad en pantallas grandes a distancia.
- **Indicador de conexión**: Si se pierde la conexión con el servidor, aparece un banner rojo con el texto "Sin conexión" en la esquina superior derecha.

### Pacientes que NO aparecen en el tablero

- Pacientes sin estado asignado (aún no se les ha hecho clic en ningún botón de estado).
- Pacientes con estado **Finalizado** (su sesión se oculta automáticamente).

### Configuración recomendada para TV

1. Abra el navegador en la TV o computador conectado a la TV.
2. Navegue a la URL del tablero.
3. Ponga el navegador en **pantalla completa** (generalmente con la tecla F11).
4. Deje la pantalla encendida. El tablero se actualiza solo.

---

## 10. Notificaciones SMS

Quiroinfo puede enviar mensajes de texto (SMS) automáticos a los familiares de los pacientes cada vez que su estado quirúrgico cambia.

### ¿Cuándo se envía un SMS?

Se envía un SMS **cada vez que se cambia el estado** de un paciente (al hacer clic en cualquier botón de estado o al cambiar el estado desde el modal de edición), **siempre y cuando** el paciente tenga un número de teléfono registrado.

### ¿Qué contiene el mensaje?

El SMS incluye:

- El nombre del paciente (o su identificación si no tiene nombre registrado).
- El nuevo estado quirúrgico.
- La hora del cambio.

Ejemplo de mensaje:
> *Quiroinfo: Paciente Juan Pérez pasa a: CIRUGIA. Hora: 3:05 pm*

### ¿Cómo registrar el teléfono?

1. Haga clic en **Editar** en la fila del paciente.
2. En el campo **Teléfono para notificaciones**, ingrese el número de celular colombiano de 10 dígitos (ejemplo: `3176753151`).
3. Haga clic en **Guardar**.

Para dejar de enviar SMS a un paciente, abra el modal de edición, borre el número de teléfono y guarde.

### Requisitos técnicos

- El envío de SMS requiere que el administrador del sistema haya configurado las credenciales del servicio **Twilio** (proveedor de mensajería).
- Si las credenciales no están configuradas, el sistema no enviará SMS pero seguirá funcionando normalmente en todas las demás funciones.
- Si ocurre un error al enviar un SMS, el cambio de estado del paciente **no se ve afectado**. El error se registra internamente en los logs del sistema.

---

## 11. Preguntas Frecuentes

### ¿Qué pasa si cierro el navegador?

No se pierde ninguna información. Todos los datos de pacientes y estados se guardan en la base de datos del servidor. Al volver a abrir el navegador e iniciar sesión, verá toda la información actualizada.

El Tablero Público tampoco se ve afectado: si alguien más tiene el tablero abierto en otra pantalla, seguirá funcionando normalmente.

---

### ¿Cómo cambio el intervalo de actualización del tablero?

El tablero se actualiza automáticamente cada **15 segundos**. Este intervalo está configurado en el código del sistema y no se puede cambiar desde la interfaz de usuario.

Si necesita un intervalo diferente, contacte al administrador del sistema para que modifique la configuración técnica.

---

### ¿Qué pasa si no hay conexión a internet?

- **Panel de Gestión**: Los botones de estado y las acciones no funcionarán hasta que se restablezca la conexión. Los cambios que intente hacer no se guardarán. Una vez recuperada la conexión, puede continuar operando normalmente.
- **Tablero Público**: Mostrará un banner rojo con el texto **"Sin conexión"** en la esquina superior derecha. La última información cargada permanecerá visible en pantalla. Cuando la conexión se restablezca, el tablero volverá a actualizarse automáticamente.

---

### ¿Puedo usar el sistema desde el celular?

Sí. El Panel de Gestión y el Tablero son accesibles desde cualquier navegador web, incluyendo dispositivos móviles. Sin embargo, el Panel de Gestión está optimizado para pantallas de escritorio debido a su diseño de dos columnas.

---

### ¿Qué pasa si dos Funcionarios cambian el estado del mismo paciente al mismo tiempo?

El último cambio es el que queda registrado. El sistema no bloquea ediciones simultáneas, pero ambas tablas y el tablero siempre reflejan el estado más reciente.

---

### ¿Por qué un paciente desapareció del tablero?

Probablemente se le asignó el estado **Finalizado**. Cuando un paciente pasa a Finalizado, se oculta del Tablero Público y de la tabla Pacientes en sala. Puede verificarlo en la tabla Pacientes programados: si el botón Finalizado está resaltado en gris, esa es la razón.

---

### ¿Puedo deshacer un cambio de estado?

Sí. Simplemente haga clic en el botón del estado anterior. Por ejemplo, si cambió un paciente a "En cirugía" por error, haga clic en "En preparación" para regresarlo.

---

### ¿Qué significa el spinner en el botón "Cargar pacientes programados"?

Significa que el sistema está descargando la lista de pacientes desde la fuente externa. Espere a que termine. No cierre el navegador ni haga clic en otros botones durante la carga.

---

### ¿El SMS se envía a todos los pacientes?

No. Solo se envía SMS a los pacientes que tienen un **número de teléfono registrado** en el campo "Teléfono para notificaciones". Si el campo está vacío, no se envía ningún mensaje.
