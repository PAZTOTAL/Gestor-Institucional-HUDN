# Arquitectura — CRUE Remisiones Pacientes

## 1. Diagrama de capas

```mermaid
graph TB
    subgraph Frontend["Frontend (Navegador)"]
        HTML["Templates Django<br/>base.html, main.html, login.html"]
        CSS["CSS<br/>main.css + Bootstrap 5"]
        JS["JavaScript vanilla<br/>modal.js, tabla.js, filtros.js,<br/>datetime_widget.js, autoformat.js"]
    end

    subgraph Backend["Backend (Django 4.2)"]
        Views["Views<br/>views.py<br/>login_view, main_view,<br/>remision_create, remision_update,<br/>remision_delete, remision_detail,<br/>exportar_excel, importar_excel,<br/>usuarios_view, cambiar_password_view"]
        Forms["Forms<br/>forms.py<br/>RemisionForm, LoginForm,<br/>UsuarioForm, ImportarExcelForm,<br/>CambiarPasswordForm"]
        Services["Services<br/>services.py<br/>calcular_oportunidad,<br/>obtener_remisiones,<br/>importar_desde_excel_v2,<br/>exportar_a_excel,<br/>enviar_email_recuperacion"]
        Models["Models<br/>models.py<br/>UsuarioCrue, Remision"]
    end

    subgraph Data["Capa de datos"]
        DB["PostgreSQL 16+<br/>crue_remisiones_db"]
    end

    HTML -->|"HTTP GET/POST"| Views
    JS -->|"AJAX (fetch/XHR)"| Views
    Views --> Forms
    Views --> Services
    Forms --> Models
    Services --> Models
    Models -->|"Django ORM"| DB
```

## 2. Diagrama de flujo: Crear una remisión

```mermaid
sequenceDiagram
    actor U as Usuario
    participant JS as modal.js
    participant V as views.remision_create
    participant F as RemisionForm
    participant S as Services
    participant M as Remision (Model)
    participant DB as PostgreSQL

    U->>JS: Clic "Nuevo Registro"
    JS->>JS: Abrir modal vacío
    U->>JS: Completar campos y clic "Guardar"
    JS->>V: POST /remisiones/nueva/ (AJAX + CSRF)
    V->>F: RemisionForm(request.POST)
    F->>F: Validar campos (clean_edad, clean_ta, clean_glasg, clean_doc, clean)
    
    alt Validación exitosa
        F-->>V: form.is_valid() = True
        V->>V: remision.created_by = request.user
        V->>V: remision.radio_operador = user.get_full_name()
        V->>M: form.save()
        M->>DB: INSERT INTO remisiones_remision
        DB-->>M: OK
        V-->>JS: {"ok": true, "id": 123}
        JS->>JS: Cerrar modal, recargar tabla
    else Validación fallida
        F-->>V: form.is_valid() = False
        V-->>JS: {"ok": false, "errors": {...}} (HTTP 400)
        JS->>JS: Mostrar errores en modal
    end
```

## 3. Diagrama de flujo: Importar desde Excel

```mermaid
sequenceDiagram
    actor U as Usuario
    participant SB as Sidebar (form-importar)
    participant V as views.importar_excel
    participant F as ImportarExcelForm
    participant S as services.importar_desde_excel_v2
    participant UT as utils.excelToDataframe
    participant DB as PostgreSQL

    U->>SB: Seleccionar archivo .xlsx
    U->>SB: Clic "Importar Excel"
    SB->>V: POST /importar/excel/ (multipart/form-data)
    V->>F: ImportarExcelForm(request.POST, request.FILES)
    F->>F: Validar extensión (.xlsx/.xls)
    
    alt Archivo válido
        V->>V: Guardar en archivo temporal
        V->>S: importar_desde_excel_v2(temp_path, usuario)
        S->>UT: excelToDataframe(excel_path)
        UT-->>S: DataFrame con datos
        
        loop Por cada fila del DataFrame
            S->>S: Mapear campos exclusivos (sexo, gest, aceptado)
            S->>S: Combinar fecha + hora
            S->>S: Validar formatos (edad, TA, Glasgow)
            S->>S: Verificar duplicados en BD
        end
        
        alt Sin errores
            S->>DB: bulk_create (transacción atómica)
            DB-->>S: OK
            S-->>V: {"ok": true, "importados": N}
            V-->>SB: JSON 200
            SB->>SB: Mostrar mensaje de éxito
        else Error en alguna fila
            S-->>V: {"ok": false, "error": "Fila X: ..."}
            V-->>SB: JSON 400
            SB->>SB: Mostrar mensaje de error
        end
    else Archivo inválido
        F-->>V: Errores de formulario
        V-->>SB: {"ok": false, "errors": {...}} (HTTP 400)
    end
```

## 4. Diagrama Entidad-Relación

```mermaid
erDiagram
    UsuarioCrue {
        int id PK
        string username UK
        string first_name
        string last_name
        string email
        string password
        string rol "DIRECTOR | RADIOOPERADOR"
        boolean is_active
        boolean is_staff
        boolean is_superuser
        datetime date_joined
        datetime last_login
    }

    Remision {
        int id PK
        datetime fecha "Fecha y hora de ingreso"
        string nombre "Nombre del paciente"
        string tipo_doc "CC|TI|CE|RC|CN|OTRO"
        string doc "Número de documento"
        string sexo "M|F"
        string edad "Ej: 25 AÑOS"
        string gest "SI|NO"
        string especialidad "Especialidad médica"
        text diagnostico
        string ta "Tensión arterial"
        string fc "Frecuencia cardíaca"
        string fr "Frecuencia respiratoria"
        string tm "Temperatura"
        string spo2 "Saturación O2"
        string glasg "Glasgow"
        string eps
        string institucion_reporta
        string municipio
        string medico_refiere
        text medico_hudn
        string radio_operador
        text observacion
        string aceptado "SI|NO|URG VITAL"
        datetime fecha_res "Fecha de respuesta (nullable)"
        datetime created_at "Auto"
        datetime updated_at "Auto"
        int created_by_id FK "Nullable (SET_NULL)"
    }

    UsuarioCrue ||--o{ Remision : "crea (created_by)"
```

## 5. Diagrama de componentes Frontend

```mermaid
graph TB
    subgraph Templates["Templates Django"]
        base["base.html<br/>─────────<br/>• Bootstrap 5 CSS/JS (CDN)<br/>• Bootstrap Icons<br/>• main.css<br/>• Barra de título superior<br/>• Logo HUDN + fecha + usuario"]
        main["main.html<br/>─────────<br/>• Extiende base.html<br/>• Sidebar (inline)<br/>• Barra de filtros<br/>• Tabla de remisiones<br/>• Modal de creación/edición<br/>• Paginación"]
        login["login.html<br/>─────────<br/>• Formulario de login"]
        cambiar_pw["cambiar_password.html"]
        recuperar_pw["recuperar_password.html"]
        usuarios["usuarios.html<br/>─────────<br/>• Lista de usuarios<br/>• Formulario crear usuario"]
        usuario_edit["usuario_editar.html"]
        usuario_pw["usuario_cambiar_password.html"]
    end

    subgraph JS["JavaScript (vanilla)"]
        modal_js["modal.js<br/>─────────<br/>• Abrir/cerrar modal<br/>• Enviar formulario AJAX<br/>• Cargar datos para edición<br/>• Clonar registro<br/>• Manejar especialidad OTRA<br/>• Auto-llenar fecha_res"]
        tabla_js["tabla.js<br/>─────────<br/>• Expandir/colapsar detalle<br/>• Botones eliminar (AJAX)<br/>• Interacciones de fila"]
        filtros_js["filtros.js<br/>─────────<br/>• Cambiar tipo de filtro<br/>• Mostrar/ocultar controles<br/>• Validar rango de fechas"]
        datetime_js["datetime_widget.js<br/>─────────<br/>• Widget fecha + hora separados<br/>• Combinar en datetime-local<br/>• Autoformato HH:MM"]
        autoformat_js["autoformat.js<br/>─────────<br/>• Autoformato temperatura (°)<br/>• Autoformato SPO2 (%)<br/>• Uppercase automático"]
    end

    subgraph CSS["Estilos"]
        main_css["main.css<br/>─────────<br/>• Layout sidebar + contenido<br/>• Estilos de tabla<br/>• Colores de filas (verde/rojo)<br/>• Modal responsive<br/>• Barra de título"]
        bootstrap["Bootstrap 5 (CDN)"]
        icons["Bootstrap Icons (CDN)"]
    end

    base --> main
    base --> login
    base --> cambiar_pw
    base --> recuperar_pw
    base --> usuarios
    base --> usuario_edit
    base --> usuario_pw

    main --> modal_js
    main --> tabla_js
    main --> filtros_js
    main --> datetime_js
    main --> autoformat_js

    base --> main_css
    base --> bootstrap
    base --> icons
```
