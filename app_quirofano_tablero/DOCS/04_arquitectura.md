# Arquitectura — Quiroinfo

## Visión general

Quiroinfo es una aplicación web de **Server-Side Rendering (SSR)** construida con Django. No hay SPA ni API REST. Las interacciones dinámicas se manejan con HTMX (fragmentos HTML parciales) y Alpine.js (comportamientos ligeros de UI).

```mermaid
flowchart LR
    subgraph Cliente["Navegador / TV"]
        HTMX["HTMX 1.9"]
        Alpine["Alpine.js 3.x"]
        TW["Tailwind CSS CDN"]
    end

    subgraph Servidor["Django SSR"]
        Vistas["Vistas (CBV)"]
        Servicios["Servicios"]
        Modelos["Modelos ORM"]
    end

    subgraph Externo["Servicios externos"]
        Twilio["Twilio SMS"]
    end

    BD[("PostgreSQL")]

    HTMX -->|"HTTP GET/POST"| Vistas
    Vistas -->|"HTML fragments"| HTMX
    Vistas --> Servicios
    Servicios --> Modelos
    Modelos --> BD
    Servicios -->|"SMS"| Twilio
```

---

## Diagrama de componentes — Apps Django

El proyecto se compone de 3 apps Django, cada una con una responsabilidad clara:

```mermaid
flowchart TB
    subgraph app_autenticacion["app_autenticacion"]
        direction TB
        A1["LoginVista / LogoutVista"]
        A2["LoginRequeridoMixin"]
        A3["Validación email\n(whitelist / dominio)"]
    end

    subgraph app_core["app_core"]
        direction TB
        B1["Modelos\nPaciente · Sesion · EstadoQuirurgico"]
        B2["Servicios\nSesionServicio · obtenerSesionesVisibles"]
        B3["Vistas\nGestionVista · AplicarEstadoVista\nActualizarPacienteVista · AgregarPacienteVista\nCargarProgramadosVista\nTableroVista · TableroFragmentoVista"]
        B4["Utils\ncargarPacientesProgramadosCirugia"]
        B5["Templates\ngestion/ · tablero/"]
        B6["Template tags\nfiltros_gestion"]
    end

    subgraph app_notificaciones["app_notificaciones"]
        direction TB
        C1["NotificacionServicio"]
        C2["Integración Twilio\n_enviarSms"]
    end

    app_core -->|"usa"| app_autenticacion
    app_core -->|"usa"| app_notificaciones
    B3 --> A2
    B3 --> C1
```

### Responsabilidades por app

| App | Responsabilidad |
|---|---|
| `app_autenticacion` | Login/logout por email, mixin de protección de vistas, validación de whitelist/dominio |
| `app_core` | Modelos de datos, lógica de negocio (servicios), vistas del panel de gestión y tablero, templates, carga de pacientes |
| `app_notificaciones` | Envío de SMS vía Twilio ante cambios de estado quirúrgico |

---

## Flujo de datos: Cambio de estado quirúrgico

Cuando un funcionario hace clic en un botón de estado en la Tabla_Programados:

```mermaid
sequenceDiagram
    participant F as Funcionario (Navegador)
    participant HTMX as HTMX
    participant V as AplicarEstadoVista
    participant S as SesionServicio
    participant N as NotificacionServicio
    participant BD as PostgreSQL
    participant TW as Twilio

    F->>HTMX: Clic en botón de estado
    HTMX->>V: POST /gestion/sesiones/estado/<br>{pacienteId, estado}
    V->>S: aplicarEstado(paciente, estado)
    S->>BD: get_or_create Sesion / update estado
    BD-->>S: Sesion actualizada
    S-->>V: Sesion
    V->>N: notificarCambioEstado(paciente, estado)
    N->>N: ¿Paciente tiene teléfono?
    alt Tiene teléfono
        N->>TW: SMS a +57{telefono}
        TW-->>N: OK / Error (no bloquea)
    end
    V->>BD: _contextoGestion() → queries
    BD-->>V: Pacientes + Sesiones
    V-->>HTMX: HTML fragmento_tablas.html
    HTMX->>F: Swap outerHTML #fragmento-tablas
```

---

## Flujo de datos: Edición de paciente (Modal)

Cuando un funcionario edita un paciente desde el Modal_Edicion:

```mermaid
sequenceDiagram
    participant F as Funcionario (Navegador)
    participant A as Alpine.js
    participant HTMX as HTMX
    participant V as ActualizarPacienteVista
    participant S as SesionServicio
    participant BD as PostgreSQL

    F->>A: Clic "Editar" → abrirModal()
    A->>F: Muestra modal con datos precargados
    F->>A: Modifica campos, clic "Guardar"
    A->>A: Validación cliente (identificación no vacía, teléfono 10 dígitos)
    alt Validación falla
        A->>F: Muestra errorEdicion en modal
    else Validación OK
        A->>A: ¿Estado cambió vs editEstadoOriginal?
        A->>HTMX: htmx.ajax POST /gestion/pacientes/actualizar/<br>{pacienteId, nuevaIdentificacion, telefono, [labelOtro, estadoOtro]}
        HTMX->>V: POST con datos
        V->>BD: Paciente.save() (identificacion, telefono)
        alt Estado fue modificado
            V->>S: aplicarEstado(paciente, 'OTRO', labelOtro)
            S->>BD: Update Sesion
        end
        V->>BD: _contextoGestion() → queries
        BD-->>V: Datos actualizados
        V-->>HTMX: HTML fragmento_tablas.html
        HTMX->>F: Swap outerHTML #fragmento-tablas
        A->>F: Cierra modal
    end
```

---

## Flujo de datos: Polling del tablero

El tablero público se actualiza automáticamente cada 15 segundos:

```mermaid
sequenceDiagram
    participant TV as Tablero (TV/Navegador)
    participant HTMX as HTMX
    participant V as TableroFragmentoVista
    participant S as obtenerSesionesVisibles
    participant BD as PostgreSQL

    loop Cada 15 segundos
        HTMX->>V: GET /tablero/fragmento/
        V->>S: obtenerSesionesVisibles()
        S->>BD: SELECT sesiones WHERE oculto=False<br>ORDER BY -actualizadoEn
        BD-->>S: Sesiones con paciente (select_related)
        S-->>V: QuerySet de sesiones
        V-->>HTMX: HTML fragmento.html
        HTMX->>TV: Swap innerHTML #lista-sesiones
    end

    Note over TV: Si hay error de conexión,<br>Alpine.js muestra banner "Sin conexión"
```

---

## Flujo de notificación SMS

```mermaid
flowchart TD
    A["Cambio de estado quirúrgico"] --> B["AplicarEstadoVista / ActualizarPacienteVista"]
    B --> C["NotificacionServicio.notificarCambioEstado()"]
    C --> D{"¿Paciente tiene teléfono?"}
    D -->|No| E["No hacer nada"]
    D -->|Sí| F{"¿Credenciales Twilio configuradas?"}
    F -->|No| G["Log warning, no enviar"]
    F -->|Sí| H["Construir mensaje:\nQuiroinfo: Paciente {nombre}\npasa a: {estado}. Hora: {hora}"]
    H --> I["Twilio Client.messages.create()\nDestino: +57{telefono}"]
    I --> J{"¿Éxito?"}
    J -->|Sí| K["Log info"]
    J -->|Error| L["Log error\n(no bloquea operación principal)"]
```

---

## Flujo de renderizado de templates

```mermaid
flowchart TD
    subgraph Tablero["Tablero (público)"]
        T1["tablero.html\n(HTML completo, 100vh)"]
        T2["tablero/fragmento.html\n(lista de sesiones, flex layout)"]
        T1 -->|"include"| T2
    end

    subgraph Gestion["Panel de gestión (privado)"]
        G1["gestion.html\n(HTML completo, header + logout)"]
        G2["gestion/fragmento_tablas.html\n(grid 2 columnas: Programados + En Sala)"]
        G1 -->|"include"| G2
    end

    subgraph Base["Template base"]
        B1["templates/base.html\n(CDN: Tailwind + Alpine + HTMX)"]
    end

    subgraph Auth["Autenticación"]
        L1["autenticacion/login.html\n(formulario email, standalone)"]
    end

    Note over T1: No extiende base.html<br>(layout TV independiente)
    Note over G1: No extiende base.html<br>(incluye CDNs directamente)
    Note over L1: Standalone, solo Tailwind CDN
```

### Notas sobre templates

- **`tablero.html`** y **`gestion.html`** son páginas completas independientes que incluyen sus propios CDN scripts. No extienden `base.html`.
- **`base.html`** existe como template base disponible pero no se usa actualmente en las vistas principales.
- Los **fragmentos** (`fragmento_tablas.html`, `tablero/fragmento.html`) son parciales HTML sin `<html>/<body>`, diseñados para swap HTMX.
- El token CSRF se inyecta vía JavaScript en `gestion.html` para todas las peticiones HTMX.
- Alpine.js maneja estado local por fila (`x-data` en cada `<tr>`) en la tabla de programados.
