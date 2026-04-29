# Diagramas de Arquitectura

---

## 1. Arquitectura general del sistema

```mermaid
graph TB
    subgraph Navegador
        UI[Interfaz de Usuario<br/>Tailwind CSS + Alpine.js]
        HTMX[HTMX 1.9<br/>Peticiones parciales]
    end

    subgraph "Servidor Django"
        URLs[config/urls.py<br/>traslados/urls.py]
        Views[traslados/views.py<br/>Vistas CBV + FBV]
        Forms[traslados/forms.py<br/>Formularios]
        Models[traslados/models.py<br/>Usuario, ControlMes,<br/>TrasladoPaciente]
        Services[traslados/services/<br/>report_excel.py]
        Templates[traslados/templates/<br/>Plantillas Django]
    end

    subgraph "Base de Datos"
        PG[(PostgreSQL)]
    end

    UI -->|Página completa| URLs
    HTMX -->|Fragmento HTML| URLs
    URLs --> Views
    Views --> Forms
    Views --> Models
    Views --> Services
    Views --> Templates
    Models --> PG
    Templates -->|HTML| UI
    Templates -->|Fragmento| HTMX
    Services -->|.xlsx| UI
```

---

## 2. Flujo de autenticación

```mermaid
sequenceDiagram
    actor U as Usuario
    participant L as /login/
    participant A as Django Auth
    participant M as / (Vista Principal)

    U->>L: GET /login/
    L-->>U: Formulario de login

    U->>L: POST (username, password)
    L->>A: authenticate()

    alt Credenciales válidas
        A-->>L: Usuario autenticado
        L-->>U: 302 Redirect → /
        U->>M: GET /
        M-->>U: Vista principal
    else Credenciales inválidas
        A-->>L: None
        L-->>U: 200 + mensaje de error
    end
```

---

## 3. Flujo CRUD de traslados (HTMX)

```mermaid
sequenceDiagram
    actor U as Usuario
    participant T as Tabla (partial)
    participant MF as Modal Form (partial)
    participant V as Vista Django
    participant DB as PostgreSQL

    Note over U,DB: CREAR REGISTRO

    U->>V: GET /traslados/nuevo/?mes=4
    V->>V: Verificar mes abierto
    V-->>MF: Formulario vacío (HTML)
    MF-->>U: Modal abierto

    U->>V: POST /traslados/nuevo/ (datos)
    V->>DB: TrasladoPaciente.save()
    V-->>T: Tabla actualizada (HTML)
    T-->>U: Tabla + modal cerrado

    Note over U,DB: EDITAR REGISTRO

    U->>V: GET /traslados/5/editar/
    V->>DB: get_object_or_404(pk=5)
    V-->>MF: Formulario precargado (HTML)
    MF-->>U: Modal abierto

    U->>V: POST /traslados/5/editar/ (datos)
    V->>DB: registro.save()
    V-->>T: Tabla actualizada (HTML)

    Note over U,DB: ELIMINAR REGISTRO

    U->>V: GET /traslados/5/confirmar-eliminar/
    V-->>U: Diálogo de confirmación (HTML)

    U->>V: DELETE /traslados/5/eliminar/
    V->>DB: registro.delete()
    V-->>T: Tabla actualizada (HTML)
```

---

## 4. Flujo de filtrado

```mermaid
sequenceDiagram
    actor U as Usuario
    participant F as Filtros (mes, días)
    participant V as VistaTablaTrasladosHTMX
    participant DB as PostgreSQL
    participant T as Tabla (partial)

    U->>F: Cambia selector de mes
    F->>V: GET /traslados/tabla/?mes=3&dia_desde=1&dia_hasta=31
    V->>DB: TrasladoPaciente.filter(mes=3, fecha__gte=..., fecha__lte=...)
    DB-->>V: QuerySet filtrado
    V-->>T: Renderiza table.html
    T-->>U: Tabla actualizada (sin recarga de página)
```

---

## 5. Flujo de cierre de mes

```mermaid
sequenceDiagram
    actor D as DIRECTOR
    participant V as vistaCerrarMes
    participant DB as PostgreSQL

    D->>V: POST /mes/4/cerrar/
    V->>V: Verificar rol DIRECTOR
    V->>DB: ControlMes.objects.get(mes=4)
    V->>DB: estado='CERRADO', fecha_cierre=now(), cerrado_por=user
    DB-->>V: OK
    V-->>D: 302 Redirect → /

    Note over D,DB: Tras el cierre, cualquier CRUD en mes 4 retorna 403
```

---

## 6. Flujo de generación de reporte Excel

```mermaid
sequenceDiagram
    actor U as Usuario
    participant V as VistaReporteExcel
    participant S as report_excel.py
    participant DB as PostgreSQL

    U->>V: GET /reportes/excel/?mes=4&dia_desde=1&dia_hasta=30
    V->>DB: TrasladoPaciente.filter(mes=4, ...)
    DB-->>V: QuerySet
    V->>S: generarExcel(queryset, 4)
    S->>S: Crear Workbook con openpyxl
    S->>S: Escribir encabezados + filas
    S-->>V: (bytes, "traslados_4.xlsx")
    V-->>U: HttpResponse (attachment, .xlsx)
```

---

## 7. Flujo de limpieza anual

```mermaid
sequenceDiagram
    actor D as DIRECTOR
    participant V as vistaLimpiarSistema
    participant DB as PostgreSQL

    D->>V: GET /sistema/limpiar/
    V-->>D: Página con sugerencia de reportes + confirmación

    D->>V: POST (accion=confirmar)
    V->>DB: TrasladoPaciente.objects.all().delete()
    V->>DB: ControlMes.objects.all().update(estado='ABIERTO')
    V-->>D: 302 Redirect → / + mensaje de éxito
```

---

## 8. Relación de componentes (templates)

```mermaid
graph TD
    BASE[base.html<br/>CDN: Tailwind, HTMX, Alpine.js<br/>CSRF token injection]

    BASE --> MAIN[main.html]
    BASE --> LOGIN[login.html]
    BASE --> USERS[user_management.html]
    BASE --> PWSELF[cambiar_contrasena.html]
    BASE --> PWUSER[cambiar_contrasena_usuario.html]
    BASE --> CLEAN[limpiar_sistema.html]
    BASE --> RECOV[password_recovery.html]
    BASE --> ERROR[error_reporte.html]

    MAIN -->|include| SIDEBAR[main_sidebar.html]
    MAIN -->|include| TITLE[main_title.html]
    MAIN -->|HTMX load| TABLE[partials/table.html]

    TABLE -->|HTMX get| MODAL[partials/modal_form.html]
    TABLE -->|HTMX get| CONFIRM[partials/confirmar_eliminar.html]
    USERS -->|HTMX get| CONFUSER[partials/confirmar_eliminar_usuario.html]
```

---

## 9. Modelo de datos (relaciones)

```mermaid
erDiagram
    Usuario {
        int id PK
        string username UK
        string password
        string nombre
        string correo
        string rol "FUNCIONARIO | DIRECTOR"
        boolean is_active
    }

    ControlMes {
        int id PK
        int mes UK "1-12"
        string estado "ABIERTO | CERRADO"
        datetime fecha_cierre
        int cerrado_por_id FK
    }

    TrasladoPaciente {
        int id PK
        date fecha
        time hora_reporte
        time hora_egreso
        time hora_ingreso
        string nombre_paciente
        string documento
        string servicio
        string quien_reporta
        string destino
        string procedimiento
        string medico
        string conductor
        string radio_operador
        string ambulancia
        text observacion
        int mes "derivado de fecha"
    }

    Usuario ||--o{ ControlMes : "cerrado_por"
```
