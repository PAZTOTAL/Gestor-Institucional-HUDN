# Modelo de Datos — CRUE Remisiones Pacientes

## Resumen

El sistema utiliza dos modelos principales:

- **UsuarioCrue**: Modelo de usuario personalizado que extiende `AbstractUser` de Django.
- **Remision**: Registro de remisión de un paciente comentado por CRUE, ESE, SAS o EPS.

El modelo de usuario personalizado está configurado en `settings.py`:

```python
AUTH_USER_MODEL = 'remisiones.UsuarioCrue'
```

---

## UsuarioCrue

Extiende `django.contrib.auth.models.AbstractUser`. Hereda todos los campos estándar de Django (username, password, email, first_name, last_name, is_active, is_staff, is_superuser, date_joined, last_login) y agrega el campo `rol`.

### Campos

| Campo | Tipo | Max Length | Restricciones | Valor por defecto | Descripción |
|---|---|---|---|---|---|
| `id` | BigAutoField | — | PK, auto-generado | — | Identificador único |
| `username` | CharField | 150 | Unique, obligatorio | — | Nombre de usuario para login (heredado) |
| `first_name` | CharField | 150 | Opcional | `""` | Nombre (heredado) |
| `last_name` | CharField | 150 | Opcional | `""` | Apellido (heredado) |
| `email` | EmailField | 254 | Opcional | `""` | Correo electrónico (heredado) |
| `password` | CharField | 128 | Obligatorio | — | Contraseña hasheada (heredado) |
| `is_active` | BooleanField | — | — | `True` | Usuario activo (heredado) |
| `is_staff` | BooleanField | — | — | `False` | Acceso al admin (heredado) |
| `is_superuser` | BooleanField | — | — | `False` | Superusuario (heredado) |
| `date_joined` | DateTimeField | — | Auto | — | Fecha de registro (heredado) |
| `last_login` | DateTimeField | — | Nullable | `None` | Último inicio de sesión (heredado) |
| `rol` | CharField | 15 | choices: `ROL_CHOICES` | `'RADIOOPERADOR'` | Rol del usuario en el sistema |

### Choices: ROL_CHOICES

| Valor almacenado | Etiqueta visible |
|---|---|
| `DIRECTOR` | Director |
| `RADIOOPERADOR` | Radiooperador |

### Meta

```python
class Meta:
    verbose_name = 'Usuario CRUE'
    verbose_name_plural = 'Usuarios CRUE'
```

### Métodos

| Método | Retorno | Descripción |
|---|---|---|
| `__str__()` | `str` | Retorna `"username (rol)"` |

---

## Remision

Registro de remisión de un paciente. Contiene información de identificación, datos clínicos, información institucional, resultado y campos de auditoría.

### Campos — Identificación y tiempo de ingreso

| Campo | Tipo | Max Length | Restricciones | Valor por defecto | Descripción |
|---|---|---|---|---|---|
| `id` | BigAutoField | — | PK, auto-generado | — | Identificador único |
| `fecha` | DateTimeField | — | Obligatorio | — | Fecha y hora de ingreso. `help_text`: "DD/MM/YYYY HH:MM" |

### Campos — Identificación del paciente

| Campo | Tipo | Max Length | Restricciones | Valor por defecto | Descripción |
|---|---|---|---|---|---|
| `nombre` | CharField | 100 | Obligatorio | — | Nombre del paciente |
| `tipo_doc` | CharField | 5 | choices: `TIPO_DOC_CHOICES` | `'CC'` | Tipo de documento |
| `doc` | CharField | 20 | Obligatorio | — | Número de documento (solo dígitos, validado en formulario) |
| `sexo` | CharField | 1 | choices: `SEXO_CHOICES` | `'M'` | Sexo del paciente |
| `edad` | CharField | 20 | Obligatorio | — | Edad con unidad. `help_text`: "Ej: 25 AÑOS, 3 MESES, 10 DIAS" |
| `gest` | CharField | 2 | choices: `GEST_CHOICES` | `'NO'` | Gestante |
| `especialidad` | CharField | 100 | blank=True | `''` | Especialidad médica requerida. `help_text`: "Especialidad requerida por el paciente" |

### Campos — Información clínica (signos vitales)

| Campo | Tipo | Max Length | Restricciones | Valor por defecto | Descripción |
|---|---|---|---|---|---|
| `diagnostico` | TextField | — | blank=True | `''` | Diagnóstico del paciente |
| `ta` | CharField | 20 | blank=True | `''` | Tensión arterial. Formato: `120/80` o `NO REFIERE` |
| `fc` | CharField | 20 | blank=True | `''` | Frecuencia cardíaca. Valor numérico o `NO REFIERE` |
| `fr` | CharField | 20 | blank=True | `''` | Frecuencia respiratoria. Valor numérico o `NO REFIERE` |
| `tm` | CharField | 10 | blank=True | `''` | Temperatura. Formato: `36°` o `NO REFIERE` |
| `spo2` | CharField | 10 | blank=True | `''` | Saturación de oxígeno. Formato: `98%` o `NO REFIERE` |
| `glasg` | CharField | 10 | blank=True | `'15/15'` | Escala de Glasgow. Formato: `15/15` o `NO REFIERE` |

### Campos — Información institucional

| Campo | Tipo | Max Length | Restricciones | Valor por defecto | Descripción |
|---|---|---|---|---|---|
| `eps` | CharField | 100 | blank=True | `''` | EPS del paciente |
| `institucion_reporta` | CharField | 100 | blank=True | `''` | Institución que reporta la remisión |
| `municipio` | CharField | 100 | blank=True | `''` | Municipio de origen |
| `medico_refiere` | CharField | 100 | blank=True | `''` | Médico que refiere al paciente |
| `medico_hudn` | TextField | — | blank=True | `''` | Médico del HUDN que confirma |
| `radio_operador` | CharField | 100 | blank=True | `''` | Radio operador (asignado automáticamente al crear) |
| `observacion` | TextField | — | blank=True | `''` | Observaciones adicionales |

### Campos — Resultado

| Campo | Tipo | Max Length | Restricciones | Valor por defecto | Descripción |
|---|---|---|---|---|---|
| `aceptado` | CharField | 10 | choices: `ACEPTADO_CHOICES` | `'NO'` | Estado de aceptación de la remisión |
| `fecha_res` | DateTimeField | — | null=True, blank=True | `None` | Fecha y hora de respuesta. `help_text`: "DD/MM/YYYY HH:MM" |

### Campos — Auditoría

| Campo | Tipo | Restricciones | Valor por defecto | Descripción |
|---|---|---|---|---|
| `created_at` | DateTimeField | auto_now_add=True | — | Fecha y hora de creación del registro |
| `updated_at` | DateTimeField | auto_now=True | — | Fecha y hora de última actualización |
| `created_by` | ForeignKey → UsuarioCrue | null=True, blank=True, on_delete=SET_NULL | `None` | Usuario que creó el registro. `related_name`: `remisiones_creadas` |

---

### Choices

#### TIPO_DOC_CHOICES

| Valor almacenado | Etiqueta visible | Descripción |
|---|---|---|
| `CC` | CC | Cédula de Ciudadanía |
| `TI` | TI | Tarjeta de Identidad |
| `CE` | CE | Cédula de Extranjería |
| `RC` | RC | Registro Civil |
| `CN` | CN | Certificado de Nacido Vivo |
| `OTRO` | OTRO | Otro tipo de documento |

#### SEXO_CHOICES

| Valor almacenado | Etiqueta visible |
|---|---|
| `M` | M (Masculino) |
| `F` | F (Femenino) |

#### GEST_CHOICES

| Valor almacenado | Etiqueta visible |
|---|---|
| `SI` | SI |
| `NO` | NO |

#### ACEPTADO_CHOICES

| Valor almacenado | Etiqueta visible | Color en tabla |
|---|---|---|
| `SI` | SI | Verde |
| `NO` | NO | Sin color |
| `URG VITAL` | URG VITAL | Rojo |

#### ESPECIALIDAD_CHOICES

| Valor almacenado | Etiqueta visible |
|---|---|
| `CIRUGIA DE COLUMNA` | Cirugía de Columna |
| `CIRUGIA GENERAL` | Cirugía General |
| `CIRUGIA PLASTICA` | Cirugía Plástica |
| `CIRUGIA DEL TORAX` | Cirugía del Tórax |
| `CIRUGIA MAXILOFACIAL` | Cirugía Maxilofacial |
| `CIRUGIA VASCULAR` | Cirugía Vascular |
| `DERMATOLOGIA` | Dermatología |
| `ENDOCRINOLOGIA` | Endocrinología |
| `EPILEPTOLOGIA` | Epileptología |
| `GENETICA HUMANA` | Genética Humana |
| `GINECOLOGIA` | Ginecología |
| `HEMATOLOGIA` | Hematología |
| `INFECTOLOGIA` | Infectología |
| `MEDICINA INTERNA` | Medicina Interna |
| `NEFROLOGIA` | Nefrología |
| `NEFROLOGIA PEDIATRICA` | Nefrología Pediátrica |
| `NEUROCIRUGIA` | Neurocirugía |
| `NEUROLOGIA` | Neurología |
| `NEUROLOGIA PEDIATRICA` | Neurología Pediátrica |
| `NUTRICION CLINICA` | Nutrición Clínica |
| `OCULOPLASTIA` | Oculoplastia |
| `OFTALMOLOGIA` | Oftalmología |
| `ORTOPEDIA` | Ortopedia |
| `OTORRINOLARINGOLOGIA` | Otorrinolaringología |
| `PEDIATRIA` | Pediatría |
| `PERINATOLOGIA` | Perinatología |
| `REUMATOLOGIA` | Reumatología |
| `TOXICOLOGIA CLINICA` | Toxicología Clínica |
| `OTRA` | Otra |

---

### Índices

El modelo define los siguientes índices para optimizar consultas frecuentes:

| Campos | Propósito |
|---|---|
| `fecha` | Filtrado y ordenamiento por fecha de ingreso (filtro por mes, rango) |
| `doc` | Búsqueda por número de documento del paciente |

```python
class Meta:
    ordering = ['fecha']
    indexes = [
        models.Index(fields=['fecha']),
        models.Index(fields=['doc']),
    ]
```

---

### Propiedad calculada: `es_editable`

```python
@property
def es_editable(self) -> bool
```

Retorna `True` si la fecha del registro (`fecha.date()`) es igual a la fecha de hoy en la zona horaria local configurada en Django (`America/Bogota`).

Los registros históricos (cuya fecha corresponde a un día anterior) son de **solo lectura** y no pueden ser editados ni eliminados.

**Lógica:**

```python
return self.fecha.astimezone(timezone.get_current_timezone()).date() == timezone.localdate()
```

---

### Campo calculado dinámicamente: `oportunidad`

El campo **oportunidad** no se almacena en la base de datos. Se calcula dinámicamente en la capa de servicios como la diferencia entre `fecha_res` y `fecha`, expresada en formato `HH:MM`.

**Función:** `services.calcular_oportunidad(fecha, fecha_res) → str`

| Condición | Resultado |
|---|---|
| `fecha_res` es `None` | `""` (cadena vacía) |
| `fecha_res < fecha` | `""` (cadena vacía) |
| `fecha_res >= fecha` | `"HH:MM"` (ej: `"02:30"`) |

**Ejemplo:**
- `fecha` = 2025-01-15 08:00
- `fecha_res` = 2025-01-15 10:30
- `oportunidad` = `"02:30"`

---

### Relación: `created_by` → UsuarioCrue

| Propiedad | Valor |
|---|---|
| Tipo | ForeignKey |
| Modelo referenciado | `settings.AUTH_USER_MODEL` (UsuarioCrue) |
| on_delete | `SET_NULL` — Si se elimina el usuario, el campo queda en `NULL` |
| null | `True` |
| blank | `True` |
| related_name | `remisiones_creadas` |

Esto permite:
- Saber qué usuario creó cada remisión.
- Restringir edición/eliminación solo al propietario del registro.
- Asignar automáticamente `radio_operador` con el nombre del creador.
- Consultar todas las remisiones de un usuario: `usuario.remisiones_creadas.all()`

---

### Métodos

| Método | Retorno | Descripción |
|---|---|---|
| `__str__()` | `str` | Retorna `"fecha - nombre (doc)"` |
| `es_editable` (property) | `bool` | `True` si la fecha del registro es hoy |

---

### Meta

```python
class Meta:
    ordering = ['fecha']
    indexes = [
        models.Index(fields=['fecha']),
        models.Index(fields=['doc']),
    ]
    verbose_name = 'Remisión'
    verbose_name_plural = 'Remisiones'
```
