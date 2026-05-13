# Referencia del Modelo de Datos

---

## 1. Usuario

Modelo de usuario personalizado que extiende `AbstractUser` de Django. Reemplaza el modelo `User` por defecto.

**Tabla**: `traslados_usuario`
**Configuración**: `AUTH_USER_MODEL = 'traslados.Usuario'`

### Campos propios

| Campo | Tipo | Requerido | Valor por defecto | Descripción |
|---|---|---|---|---|
| `nombre` | CharField (255) | No | `''` | Nombre completo del usuario |
| `correo` | EmailField | No | `''` | Correo electrónico |
| `rol` | CharField (20) | Sí | `'FUNCIONARIO'` | Rol del usuario en el sistema |

### Valores de `rol`

| Valor | Etiqueta | Descripción |
|---|---|---|
| `FUNCIONARIO` | Funcionario | Usuario estándar con permisos de CRUD y reportes |
| `DIRECTOR` | Director | Administrador con permisos completos |

### Campos heredados de AbstractUser (principales)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | BigAutoField (PK) | Identificador único |
| `username` | CharField (150, unique) | Nombre de usuario para login |
| `password` | CharField (128) | Contraseña hasheada |
| `is_active` | BooleanField | Si el usuario puede iniciar sesión |
| `is_staff` | BooleanField | Si puede acceder al panel admin |
| `is_superuser` | BooleanField | Si tiene todos los permisos |
| `date_joined` | DateTimeField | Fecha de creación |
| `last_login` | DateTimeField | Último inicio de sesión |

### Métodos

| Método | Retorna | Descripción |
|---|---|---|
| `__str__()` | str | `"username (ROL)"` |

---

## 2. ControlMes

Almacena el estado de apertura o cierre de cada mes del año (1–12). Se crean automáticamente las 12 filas tras cada migración.

**Tabla**: `traslados_controlmes`

### Campos

| Campo | Tipo | Requerido | Valor por defecto | Restricciones | Descripción |
|---|---|---|---|---|---|
| `id` | BigAutoField (PK) | Auto | — | — | Identificador único |
| `mes` | IntegerField | Sí | — | `unique=True` | Número del mes (1–12) |
| `estado` | CharField (10) | Sí | `'ABIERTO'` | choices | Estado del mes |
| `fecha_cierre` | DateTimeField | No | `None` | `null=True, blank=True` | Fecha y hora en que se cerró |
| `cerrado_por` | ForeignKey (Usuario) | No | `None` | `null=True, blank=True, on_delete=SET_NULL` | Usuario que cerró el mes |

### Valores de `estado`

| Valor | Etiqueta | Descripción |
|---|---|---|
| `ABIERTO` | Abierto | Se permiten operaciones CRUD en registros de este mes |
| `CERRADO` | Cerrado | Registros de este mes son de solo lectura |

### Relaciones

| Relación | Modelo destino | Tipo | related_name | on_delete |
|---|---|---|---|---|
| `cerrado_por` | Usuario | ForeignKey | `meses_cerrados` | SET_NULL |

### Métodos

| Método | Retorna | Descripción |
|---|---|---|
| `__str__()` | str | `"Mes {mes}: {estado}"` |
| `estaCerrado()` | bool | `True` si `estado == 'CERRADO'` |

### Meta

- `ordering`: `['mes']`
- `verbose_name`: `'Control de Mes'`
- `verbose_name_plural`: `'Control de Meses'`

### Inicialización automática

Las 12 filas de ControlMes se crean automáticamente mediante:
1. Señal `post_migrate` en `apps.py` (se ejecuta tras cada migración).
2. Comando de gestión `python manage.py inicializar_meses` (ejecución manual).

---

## 3. TrasladoPaciente

Entidad principal que representa un registro de servicio de traslado de paciente.

**Tabla**: `traslados_trasladopaciente`

### Campos

| Campo | Tipo | Requerido | Valor por defecto | Restricciones | Descripción |
|---|---|---|---|---|---|
| `id` | BigAutoField (PK) | Auto | — | — | Identificador único |
| `fecha` | DateField | Sí | — | No puede ser futura | Fecha del traslado |
| `hora_reporte` | TimeField | Sí | — | — | Hora en que se reportó el traslado |
| `hora_egreso` | TimeField | No | `None` | `null=True, blank=True` | Hora de egreso del paciente |
| `hora_ingreso` | TimeField | No | `None` | `null=True, blank=True` | Hora de ingreso del paciente |
| `nombre_paciente` | CharField (255) | Sí | — | — | Nombre completo del paciente |
| `documento` | CharField (50) | Sí | — | — | Documento de identidad |
| `servicio` | CharField (100) | Sí | — | — | Servicio de origen |
| `quien_reporta` | CharField (100) | Sí | — | — | Persona que reporta el traslado |
| `destino` | CharField (100) | Sí | — | — | Destino del traslado |
| `procedimiento` | CharField (255) | Sí | — | — | Procedimiento o motivo |
| `medico` | CharField (100) | Sí | — | — | Médico responsable |
| `conductor` | CharField (100) | Sí | — | — | Conductor de la ambulancia |
| `radio_operador` | CharField (100) | Sí | — | — | Radio operador |
| `ambulancia` | CharField (100) | Sí | — | — | Identificación de la ambulancia |
| `observacion` | TextField | No | `''` | `blank=True` | Observaciones adicionales |
| `mes` | IntegerField | Auto | — | `editable=False` | Derivado automáticamente de `fecha.month` |

### Campos obligatorios en formulario

Los siguientes campos son validados como obligatorios en el formulario (`FormularioTraslado`):
- `fecha`
- `hora_reporte`
- `nombre_paciente`
- `documento`

### Índices

| Campos | Tipo |
|---|---|
| `mes` | Index |
| `fecha` | Index |

### Validaciones (método `clean()`)

1. **Fecha futura**: Si `fecha > hoy`, lanza `ValidationError` en el campo `fecha`.
2. **Mes cerrado**: Si `ControlMes.estado == 'CERRADO'` para el mes de la fecha, lanza `ValidationError` general.

### Derivación automática del campo `mes`

El campo `mes` se calcula automáticamente a partir de `fecha.month` en dos puntos:
- En `clean()`: para validar contra el estado del mes.
- En `save()`: antes de llamar a `full_clean()` y `super().save()`.

### Métodos

| Método | Retorna | Descripción |
|---|---|---|
| `__str__()` | str | `"{fecha} – {nombre_paciente}"` |
| `clean()` | None | Valida fecha no futura y mes no cerrado |
| `save()` | None | Deriva `mes`, ejecuta `full_clean()`, persiste |

### Meta

- `ordering`: `['fecha', 'hora_reporte']`
- `verbose_name`: `'Traslado de Paciente'`
- `verbose_name_plural`: `'Traslados de Pacientes'`

---

## 4. Resumen de tablas

| Tabla | Campos clave |
|---|---|
| `traslados_usuario` | id, username (UK), password, nombre, correo, rol, is_active |
| `traslados_controlmes` | id, mes (UK), estado, fecha_cierre, cerrado_por_id (FK) |
| `traslados_trasladopaciente` | id, fecha, hora_reporte, hora_egreso, hora_ingreso, nombre_paciente, documento, servicio, quien_reporta, destino, procedimiento, medico, conductor, radio_operador, ambulancia, observacion, mes |

---

## 5. Diagrama entidad-relación

```
┌─────────────────────┐
│      Usuario         │
├─────────────────────┤
│ id (PK)             │
│ username (UK)       │
│ password            │
│ nombre              │
│ correo              │
│ rol                 │
│ is_active           │
└────────┬────────────┘
         │ 1
         │
         │ cerrado_por (FK, SET_NULL)
         │
         │ 0..*
┌────────┴────────────┐
│    ControlMes        │
├─────────────────────┤
│ id (PK)             │
│ mes (UK, 1–12)      │
│ estado              │
│ fecha_cierre        │
│ cerrado_por_id (FK) │
└─────────────────────┘


┌─────────────────────────┐
│   TrasladoPaciente       │
├─────────────────────────┤
│ id (PK)                 │
│ fecha (idx)             │
│ hora_reporte            │
│ hora_egreso             │
│ hora_ingreso            │
│ nombre_paciente         │
│ documento               │
│ servicio                │
│ quien_reporta           │
│ destino                 │
│ procedimiento           │
│ medico                  │
│ conductor               │
│ radio_operador          │
│ ambulancia              │
│ observacion             │
│ mes (idx, auto)         │
└─────────────────────────┘
```

`TrasladoPaciente` no tiene relación directa con `Usuario` ni con `ControlMes`. La relación con el mes es lógica: el campo `mes` (derivado de `fecha`) se usa para consultar `ControlMes` y verificar si el mes está cerrado.
