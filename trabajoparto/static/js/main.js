// Configuración de la API
// La URL base se obtiene desde config.js (AppConfig.API_BASE_URL)
// Asegúrate de que config.js se cargue antes que main.js en el HTML
// Misma máquina y puerto que la página → sin CORS (p. ej. http://127.0.0.1:8001/api)
const HOST_FALLBACK = (window.location.hostname && window.location.hostname !== '0.0.0.0')
    ? window.location.hostname
    : 'localhost';
const API_BASE_URL = (typeof AppConfig !== 'undefined' && AppConfig.API_BASE_URL)
    ? AppConfig.API_BASE_URL
    : `${window.location.origin}/api`;
const API_BASE = API_BASE_URL; // Alias: usar en fetch(`${API_BASE}/pacientes/...`)
const LAST_API_BASE_KEY = 'clinico:last_api_base_url';

function normalizarBaseApi(url) {
    return String(url || '').trim().replace(/\/$/, '');
}

function getApiBaseCandidates() {
    const host = (window.location.hostname && window.location.hostname !== '0.0.0.0')
        ? window.location.hostname
        : 'localhost';
    const proto = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const remembered = localStorage.getItem(LAST_API_BASE_KEY);
    const mismoOrigen = `${window.location.origin}/api`;

    const candidates = [
        mismoOrigen,
        API_BASE_URL,
        remembered,
        `${proto}//${host}:8000/api`,
        `${proto}//localhost:8000/api`,
        `${proto}//127.0.0.1:8000/api`,
    ]
        .map(normalizarBaseApi)
        .filter(Boolean);

    return [...new Set(candidates)];
}

async function fetchWithTimeout(url, options, timeoutMs) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
        const response = await fetch(url, { ...options, signal: controller.signal });
        return response;
    } finally {
        clearTimeout(timer);
    }
}

// Utilidades
function getCSRFToken() {
    return document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];
  }

function calcularEdad(fechaNacimiento) {
    if (!fechaNacimiento) {
        console.warn('⚠️ calcularEdad: No se proporcionó fecha de nacimiento');
        return null;
    }
    
    const hoy = new Date();
    const nacimiento = new Date(fechaNacimiento);
    
    // Validar que la fecha sea válida
    if (isNaN(nacimiento.getTime())) {
        console.error('❌ calcularEdad: Fecha de nacimiento inválida:', fechaNacimiento);
        return null;
    }
    
    // Si la fecha de nacimiento es futura, retornar 0 o null según prefieras
    if (nacimiento > hoy) {
        console.warn('⚠️ calcularEdad: Fecha de nacimiento es futura:', fechaNacimiento);
        return 0; // O podrías retornar null si prefieres
    }
    
    let edad = hoy.getFullYear() - nacimiento.getFullYear();
    const mes = hoy.getMonth() - nacimiento.getMonth();
    
    if (mes < 0 || (mes === 0 && hoy.getDate() < nacimiento.getDate())) {
        edad--;
    }
    
    // Asegurar que la edad no sea negativa
    return Math.max(0, edad);
}

function getLiveElementById(id) {
    const el = document.getElementById(id);
    return el && el.isConnected ? el : null;
}

function mostrarAutoGuardado() {
    const ahora = Date.now();
    // Evita mostrar múltiples toasts seguidos al escribir rápido.
    if (window._ultimoAutoGuardadoTs && (ahora - window._ultimoAutoGuardadoTs) < 1200) {
        return;
    }
    window._ultimoAutoGuardadoTs = ahora;
    mostrarMensaje('Dato guardado automáticamente', 'success');
}

function cerrarModalDesdeElemento(el, delayMs = 150) {
    const modal = el ? el.closest('.modal-parametro') : null;
    if (!modal || !modal.id) return;
    const match = modal.id.match(/^modal-parametro-(\d+)$/);
    if (!match || !match[1]) return;
    setTimeout(() => cerrarModalParametro(match[1]), delayMs);
}

function obtenerValorInput(id, fallback = '') {
    const el = getLiveElementById(id);
    if (!el || typeof el.value === 'undefined') return fallback;
    return el.value;
}

function setValorInput(id, value) {
    const el = getLiveElementById(id);
    if (!el || typeof el.value === 'undefined') return false;
    el.value = value;
    return true;
}

function obtenerDatosFormulario() {
    return {
        codigo: obtenerValorInput('codigo'),
        version: obtenerValorInput('version'),
        fecha_elabora: obtenerValorInput('fecha_elabora'),
        num_hoja: obtenerValorInput('num_hoja'),
        estado: obtenerValorInput('estado'),
        diagnostico: obtenerValorInput('diagnostico'),
        edad_snapshot: obtenerValorInput('edad_snapshot'),
        edad_gestion: obtenerValorInput('edad_gestion'),
        n_controles_prenatales: obtenerValorInput('n_controles_prenatales'),
        responsable: obtenerValorInput('responsable'),
        paciente: obtenerValorInput('paciente_id'),
        aseguradora_nombre: (obtenerValorInput('aseguradora_nombre') || '').trim()
    };
}
  
// El event listener del formulario está en el bloque DOMContentLoaded principal (línea ~337)
  

async function apiRequest(endpoint, method = 'GET', data = null) {
    const methodUpper = String(method || 'GET').toUpperCase();
    const options = {
        method: methodUpper,
        headers: {},
        credentials: 'same-origin',
    };

    // Evita preflight innecesario en GET: no enviar headers custom.
    if (methodUpper !== 'GET') {
        options.headers['Content-Type'] = 'application/json';
        options.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate';
        options.headers['Pragma'] = 'no-cache';
        options.headers['Expires'] = '0';
    }

    const csrfToken = getCSRFToken();
    if (csrfToken && methodUpper !== 'GET') {
        options.headers['X-CSRFToken'] = csrfToken;
    }

    if (data) {
        options.body = JSON.stringify(data);
    }

    const timeoutMs = (typeof AppConfig !== 'undefined' && AppConfig.REQUEST_TIMEOUT)
        ? AppConfig.REQUEST_TIMEOUT
        : 12000;
    const bases = getApiBaseCandidates();
    let ep = endpoint;
    let response = null;
    let url = '';
    let lastNetworkError = null;

    for (const base of bases) {
        // Evitar duplicar /api: si la base ya termina en /api y el endpoint empieza con /api/, quitar /api del endpoint
        ep = endpoint;
        if (base.endsWith('/api') && /^\/api(\/|$)/.test(ep)) {
            ep = ep.replace(/^\/api/, '') || '/';
        }

        // Agregar timestamp si no está presente en la URL para evitar caché
        url = `${base}${ep}`;
        if (methodUpper === 'GET' && !url.includes('?_=')) {
            url += (url.includes('?') ? '&' : '?') + '_=' + new Date().getTime();
        }

        console.log(`🌐 Haciendo petición ${method} a: ${url}`);
        if (data) {
            console.log('📤 Datos enviados:', data);
        }

        try {
            const cred =
                url.startsWith(window.location.origin) ? 'same-origin' : 'omit';
            response = await fetchWithTimeout(
                url,
                { ...options, credentials: cred },
                timeoutMs
            );
            console.log(`Respuesta recibida: ${response.status} ${response.statusText}`);
            localStorage.setItem(LAST_API_BASE_KEY, normalizarBaseApi(base));
            break;
        } catch (error) {
            lastNetworkError = error;
            console.warn(`⚠️ Error de red con base ${base}:`, error?.message || error);
            response = null;
        }
    }

    if (!response) {
        const networkMsg = 'No se pudo conectar al backend. Verifique IP/puerto o conectividad de red.';
        mostrarMensaje(networkMsg, 'error');
        throw new Error(lastNetworkError?.message || networkMsg);
    }

    if (!response.ok) {
        const text = await response.text();
        console.error(`Error en la respuesta:`, {
            status: response.status,
            statusText: response.statusText,
            body: text
        });
        
        // Intentar parsear como JSON si es posible
        let errorMessage = text || 'Error en la petición';
        let errorDetails = {};
        
        try {
            const errorJson = JSON.parse(text);
            errorDetails = errorJson;
            
            if (errorJson.detail) {
                errorMessage = errorJson.detail;
            } else if (errorJson.message) {
                errorMessage = errorJson.message;
            } else if (typeof errorJson === 'object') {
                // Si hay errores de validación, mostrarlos
                const validationErrors = Object.entries(errorJson)
                    .map(([key, value]) => {
                        const fieldName = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        const errorText = Array.isArray(value) ? value.join(', ') : value;
                        return `${fieldName}: ${errorText}`;
                    })
                    .join('\n');
                if (validationErrors) {
                    errorMessage = validationErrors;
                }
            }
        } catch (e) {
            // Si no es JSON, usar el texto tal cual
        }
        
        // Mostrar mensaje en la interfaz en lugar de alerta
        mostrarMensaje(errorMessage, 'error');
        
        throw new Error(errorMessage);
    }

    // Solo intentar JSON si hay contenido
    if (response.status === 204) {
        return null;
    }

    const jsonData = await response.json();
    
    // Log de datos recibidos para respuestas exitosas
    if (response.ok) {
        console.log(`📦 Datos recibidos:`, jsonData);
    }
    
    return jsonData;
}


// Cargar aseguradoras en datalist (sugerencias para input de texto)
async function cargarAseguradoras() {
    try {
        const aseguradoras = await apiRequest('/aseguradoras/');
        const datalist = document.getElementById('aseguradora-list');
        
        if (!datalist) return;
        
        datalist.innerHTML = '';
        aseguradoras.forEach(aseguradora => {
            const option = document.createElement('option');
            option.value = aseguradora.nombre;
            datalist.appendChild(option);
        });
    } catch (error) {
        console.error('Error al cargar aseguradoras:', error);
        mostrarMensaje('Error al cargar aseguradoras', 'error');
    }
}

// Buscar paciente por número de identificación
async function buscarPaciente() {
    const numIdentificacion = (obtenerValorInput('num_identificacion') || '').trim();
    const btnBuscar = getLiveElementById('btnBuscarPaciente');
    
    if (!numIdentificacion) {
        mostrarMensaje('Ingrese número de identificación', 'error');
        return;
    }
    
    // Estado de carga visual
    const originalText = btnBuscar ? btnBuscar.innerHTML : '';
    if (btnBuscar) {
        btnBuscar.disabled = true;
        btnBuscar.innerHTML = '⌛ Buscando...';
    }
    
    try {
        const data = await buscarPacienteCompleto(numIdentificacion);
        if (data && data.encontrado) {
            llenarFormularioDesdePaciente(data);
            mostrarMensaje('Paciente encontrado', 'success');
        } else {
            mostrarMensaje(data.mensaje || 'Paciente no encontrado', 'info');
            limpiarFormulario();
            const numIdentEl = getLiveElementById('num_identificacion');
            if (numIdentEl) numIdentEl.value = numIdentificacion;
        }
    } catch (error) {
        console.error('Error al buscar paciente:', error);
        mostrarMensaje('Error al buscar paciente: ' + error.message, 'error');
    } finally {
        // Restaurar estado del botón
        if (btnBuscar) {
            btnBuscar.disabled = false;
            btnBuscar.innerHTML = originalText;
        }
    }
}

// Función auxiliar para buscar datos obstétricos (reutilizable)
async function buscarDatosObstetricos(cedula) {
    if (!cedula) {
        const numIdentificacionField = document.getElementById("num_identificacion");
        cedula = numIdentificacionField?.value;
    }
    
    if (!cedula) return null;

    try {
        // REUTILIZAR buscarPacienteCompleto que ya tiene caché y lógica consolidada
        const data = await buscarPacienteCompleto(cedula);
        
        if (!data || !data.encontrado) return null;
        
        // Mapear campos para compatibilidad si el formato del backend cambió
        const p = data.paciente || {};
        
        // Llenar campos del formulario
        const nombreField = document.getElementById("nombre");
        if (nombreField) nombreField.value = p.nombre_completo || data.nombres || '';
        
        const nombresField = document.getElementById("nombres");
        if (nombresField) nombresField.value = p.nombre_completo || data.nombres || '';

        const edadGestacionalField = document.getElementById("edad_gestacional") || document.getElementById("edad_gestion");
        if (edadGestacionalField) edadGestacionalField.value = data.edad_gestacional || p.edad_gestacional || '';
        
        const gField = document.getElementById("g");
        if (gField) gField.value = data.g !== undefined ? data.g : (p.g || '');
        
        const pField = document.getElementById("p");
        if (pField) pField.value = data.p !== undefined ? data.p : (p.p || '');
        
        const cField = document.getElementById("c");
        if (cField) cField.value = data.c !== undefined ? data.c : (p.c || '');
        
        const aField = document.getElementById("a");
        if (aField) aField.value = data.a !== undefined ? data.a : (p.a || '');
        
        const grupoSanguineoField = document.getElementById("grupo_sanguineo") || document.getElementById("tipo_sangre");
        if (grupoSanguineoField) grupoSanguineoField.value = data.grupo_sanguineo || p.grupo_sanguineo || '';
        
        const controlesPrenatalesField = document.getElementById("controles_prenatales") || document.getElementById("n_controles_prenatales");
        if (controlesPrenatalesField) controlesPrenatalesField.value = data.n_controles_prenatales || p.n_controles_prenatales || '';
        
        const diagnosticoField = document.getElementById("diagnostico");
        if (diagnosticoField && data.diagnostico) diagnosticoField.value = data.diagnostico;

        const historiaField = document.getElementById("num_historia_clinica");
        if (historiaField) historiaField.value = p.num_historia_clinica || '';

        console.log('✅ Datos obstétricos cargados desde consolidado:', data);
        return data;
    } catch (error) {
        console.error("Error al buscar datos obstétricos:", error);
        throw error;
    }
}

// Buscar paciente obstétrico desde HCMWINGIN (función pública para el botón)
async function buscarPacienteObstetrico() {
    // Sincronizar campo cedula con num_identificacion
    const numIdentificacionField = document.getElementById("num_identificacion");
    const cedulaField = document.getElementById("cedula");
    
    if (numIdentificacionField && cedulaField) {
        cedulaField.value = numIdentificacionField.value;
    }
    
    const cedula = cedulaField?.value || numIdentificacionField?.value;

    if (!cedula) {
        mostrarMensaje("Ingrese la cédula", "error");
        return;
    }

    // Deshabilitar botón mientras busca
    const btnObstetrico = document.getElementById("btn-buscar-obstetrico");
    if (btnObstetrico) {
        btnObstetrico.disabled = true;
        btnObstetrico.textContent = "Buscando...";
    }

    try {
        const data = await buscarDatosObstetricos(cedula);
        
        if (data) {
            mostrarMensaje('Datos obstétricos cargados correctamente', 'success');
        } else {
            mostrarMensaje('Paciente sin datos obstétricos en HCMWINGIN', 'info');
        }
    } catch (error) {
        console.error("Error:", error);
        if (error.message !== "404") {
            mostrarMensaje("Error al buscar paciente obstétrico: " + error.message, "error");
        }
    } finally {
        // Rehabilitar botón
        if (btnObstetrico) {
            btnObstetrico.disabled = false;
            btnObstetrico.textContent = "👶 Obstétrico";
        }
    }
}

// Crear o actualizar paciente
async function guardarPaciente() {
    console.log('Iniciando guardarPaciente...');
    
    const numHistoriaClinica = obtenerValorInput('num_historia_clinica');
    const numIdentificacion = obtenerValorInput('num_identificacion');
    const nombres = obtenerValorInput('nombres');
    
    // Validar campos requeridos
    if (!numHistoriaClinica || !numIdentificacion || !nombres) {
        const camposFaltantes = [];
        if (!numHistoriaClinica) camposFaltantes.push('N° Historia Clínica');
        if (!numIdentificacion) camposFaltantes.push('Identificación');
        if (!nombres) camposFaltantes.push('Nombre');
        
        const errorMessage = `Campos de paciente requeridos faltantes: ${camposFaltantes.join(', ')}`;
        mostrarMensaje(errorMessage, 'error');
        throw new Error(errorMessage);
    }
    
    const pacienteData = {
        num_historia_clinica: numHistoriaClinica,
        num_identificacion: numIdentificacion,
        nombres: nombres,
        tipo_sangre: obtenerValorInput('tipo_sangre') || null,
        fecha_nacimiento: obtenerValorInput('fecha_elabora_paciente') || null,
    };
    
    console.log('Datos del paciente a guardar:', pacienteData);
    
    const pacienteId = obtenerValorInput('paciente_id');
    console.log('Paciente ID actual:', pacienteId || 'Nuevo paciente');
    
    try {
        let paciente;
        if (pacienteId) {
            console.log(`Actualizando paciente existente con ID: ${pacienteId}`);
            // Actualizar paciente existente
            paciente = await apiRequest(`/pacientes/${pacienteId}/`, 'PUT', pacienteData);
            console.log('Paciente actualizado:', paciente);
        } else {
            console.log('Creando nuevo paciente...');
            // Crear nuevo paciente
            paciente = await apiRequest('/pacientes/', 'POST', pacienteData);
            console.log('Paciente creado:', paciente);
            if (paciente && paciente.id) {
                setValorInput('paciente_id', paciente.id);
                console.log('ID del paciente guardado:', paciente.id);
            }
        }
        
        return paciente;
    } catch (error) {
        console.error('Error al guardar paciente:', error);
        console.error('Detalles del error:', {
            message: error.message,
            stack: error.stack
        });
        
        // Mostrar mensaje más descriptivo
        let mensajeError = 'Error al guardar paciente: ';
        let alertMessage = '';
        
        if (error.message.includes('num_historia_clinica') || error.message.includes('historia clínica')) {
            mensajeError = 'Error al guardar paciente';
        } else if (error.message.includes('num_identificacion') || error.message.includes('identificación')) {
            mensajeError = 'Error al guardar paciente';
        } else {
            mensajeError = 'Error al guardar paciente';
        }
        
        // Mostrar mensaje en la interfaz
        mostrarMensaje(mensajeError, 'error');
        throw error;
    }
}

// Guardar formulario
async function guardarFormulario() {
    console.log('Iniciando guardarFormulario...');
    
    // Verificar si es una actualización y mostrar confirmación
    const btnGuardar = document.getElementById('btn-guardar');
    const esActualizacion = btnGuardar && btnGuardar.getAttribute('data-es-actualizacion') === 'true';
    const formularioId = obtenerValorInput('formulario_id');
    
    if (esActualizacion || formularioId) {
        const confirmar = confirm('¿En verdad desea modificar la información?');
        if (!confirmar) {
            console.log('Actualización cancelada por el usuario');
            return;
        }
    }
    
    try {
        console.log('Guardando paciente...');
        // Primero guardar/actualizar paciente
        await guardarPaciente();
        
        const pacienteId = obtenerValorInput('paciente_id');
        console.log('Paciente ID después de guardar:', pacienteId);
        if (!pacienteId) {
            console.error('No se pudo obtener el ID del paciente');
            mostrarMensaje('Complete los campos del paciente', 'error');
            return;
        }
        
        console.log('Preparando datos del formulario...');
        
        // Preparar datos del formulario
        console.log('Obteniendo valores de los campos...');

        // Campo CÓDIGO ahora es visual/estático en el encabezado.
        // Si no hay input o viene vacío, usamos el código fijo del formato: FRSPA-022
        const codigo = obtenerValorInput('codigo') || 'FRSPA-022';
        // "version" puede no existir en UI (campo ocultado/retirado).
        // Mantener compatibilidad enviando una versión por defecto.
        const version = obtenerValorInput('version') || '1';
        const estado = obtenerValorInput('estado');
        const responsable = obtenerValorInput('responsable');
        
        // Validar campos requeridos
        // Nota: CÓDIGO ya se fuerza a un valor por defecto (FRSPA-022), por eso
        // solo validamos estado y responsable; versión usa fallback "1".
        if (!estado || !responsable) {
            const camposFaltantes = [];
            if (!estado) camposFaltantes.push('Estado');
            if (!responsable) camposFaltantes.push('Responsable');
            throw new Error(`Campos requeridos faltantes: ${camposFaltantes.join(', ')}`);
        }
        
        // Obtener edad_snapshot - verificar si tiene valor (incluyendo 0)
        const edadSnapshotInput = document.getElementById('edad_snapshot');
        const edadSnapshotValue = edadSnapshotInput?.value?.trim();
        const edadSnapshot = (edadSnapshotValue !== '' && edadSnapshotValue !== undefined && edadSnapshotValue !== null) ? 
                            parseInt(edadSnapshotValue) : null;
        console.log('🔍 edad_snapshot - Input value:', edadSnapshotValue, 'Parsed:', edadSnapshot);
        
        // Obtener edad_gestion - verificar si tiene valor (incluyendo 0)
        const edadGestionInput = document.getElementById('edad_gestion');
        const edadGestionValue = edadGestionInput?.value?.trim();
        const edadGestion = (edadGestionValue !== '' && edadGestionValue !== undefined && edadGestionValue !== null) ? 
                           parseInt(edadGestionValue) : null;
        
        // Obtener n_controles_prenatales - verificar si tiene valor (incluyendo 0)
        const nControlesInput = document.getElementById('n_controles_prenatales');
        const nControlesValue = nControlesInput?.value?.trim();
        const nControles = (nControlesValue !== '' && nControlesValue !== undefined && nControlesValue !== null) ? 
                          parseInt(nControlesValue) : null;
        
        const formularioData = {
            codigo: codigo,
            version: version,
            fecha_elabora: obtenerValorInput('fecha_elabora') || obtenerFechaLocalColombia(),
            num_hoja: parseInt(obtenerValorInput('num_hoja') || '1'),
            paciente: pacienteId,
            aseguradora_nombre: (obtenerValorInput('aseguradora_nombre') || '').trim(),
            diagnostico: obtenerValorInput('diagnostico') || null,
            edad_snapshot: edadSnapshot,
            edad_gestion: edadGestion,
            estado: estado,
            n_controles_prenatales: nControles,
            responsable: responsable,
        };
        
        console.log('Datos del formulario preparados:', formularioData);
        
        let formulario;
        
        if (formularioId) {
            console.log('Actualizando formulario existente con ID:', formularioId);
            // Actualizar formulario existente
            formulario = await apiRequest(`/formularios/${formularioId}/`, 'PUT', formularioData);
        } else {
            console.log('Creando nuevo formulario...');
            // Crear nuevo formulario
            formulario = await apiRequest('/formularios/', 'POST', formularioData);
            console.log('Formulario creado:', formulario);
            if (formulario && formulario.id) {
                setValorInput('formulario_id', formulario.id);
            }
        }
        if (!formulario || !formulario.id) {
            console.error('Formulario no creado correctamente:', formulario);
            throw new Error('Formulario no creado correctamente');
        }
        
        console.log('Guardando mediciones para formulario ID:', formulario.id);
        // Guardar mediciones
        await guardarMediciones(formulario.id);
        console.log('Mediciones guardadas exitosamente');

        // Vincular biometría (huella/firma) al formulario actual
        try {
            console.log('Vinculando biometría al formulario...');
            const vincularRes = await fetch(`${API_BASE_URL}/vincular-huella/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    paciente_id: pacienteId,
                    formulario_id: formulario.id
                })
            });
            if (vincularRes.ok) console.log('✅ Biometría vinculada correctamente');
        } catch (vincularError) {
            console.warn('No se pudo vincular la biometría:', vincularError);
        }
        
        // Actualizar el ID del formulario en el campo oculto
        setValorInput('formulario_id', formulario.id);
        
        // Actualizar el formulario informativo con los datos guardados
        // Esto asegura que el acordeón muestre los datos más recientes
        try {
            await actualizarFormularioInformativo(formulario.id);
            console.log('Formulario informativo actualizado correctamente');
        } catch (error) {
            console.error('Error al actualizar formulario informativo:', error);
            // No fallar el guardado si hay error en la actualización del informativo
        }
        
        const mensaje = esActualizacion ? 'Datos actualizados correctamente' : 'Datos guardados correctamente';
        mostrarMensaje(mensaje, 'success');
        
        // Limpiar el formulario después de un breve delay para que vean el mensaje
        // Nota: El formulario informativo (acordeón) NO se limpia, solo el formulario principal
        setTimeout(() => {
            limpiarFormulario();
            console.log('Formulario reseteado tras guardado exitoso.');
        }, 1500);
        
    } catch (error) {
        console.error('Error al guardar formulario:', error);
        
        // Mensaje de error genérico
        let alertMessage = 'Error al guardar formulario';
        
        if (error.message.includes('Campos requeridos')) {
            alertMessage = 'Complete los campos requeridos';
        }
        
        mostrarMensaje(alertMessage, 'error');
    }
}

/**
 * Crea una card de medición para mostrar en la vista previa horizontal.
 * Corregido para mostrar TODOS los parámetros y usar los estilos premium.
 */
function normalizarTextoVistaPrevia(valor) {
    if (valor === null || valor === undefined) return '';
    let text = String(valor);
    try {
        text = decodeURIComponent(escape(text));
    } catch (e) {
        // Mantener texto original cuando no aplica transcodificación.
    }
    return text
        .replace(/Ý/g, 'í')
        .replace(/ß/g, 'á')
        .replace(/¾/g, 'ó')
        .replace(/·/g, 'ú')
        .replace(/Ð/g, 'Ñ')
        .replace(/`/g, "'");
}

function crearCardMedicionPreview(horaIso, medicionesEnHora) {
    console.log(`🛠️ Generando card para hora: ${horaIso}`, medicionesEnHora);
    const date = new Date(horaIso);
    const timeStr = date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', hour12: true });
    const dateStr = date.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' });

    // Definición de Categorías para agrupar en la Card
    const categorias = [
        { nombre: "🤰 CONTROLES MATERNOS", ids: [1, 2, 3, 4] },
        { nombre: "🔄 CONTRACCIONES UC", ids: [5, 6, 7] },
        { nombre: "👶 CONTROL FETAL", ids: [8, 9, 10] },
        { nombre: "🛡️ TACTO VAGINAL", ids: [11, 12, 13, 14, 15, 16] },
        { nombre: "⏰ MONITOREO / OXITOCINA", ids: [17, 18, 19, 20] }
    ];

    const paramNamesFallback = {
        1: "TENSIÓN ARTERIAL", 2: "FREC. CARDIACA", 3: "FREC. RESPIRATORIA", 4: "TEMPERATURA",
        5: "FRECUENCIA UC", 6: "DURACIÓN UC", 7: "INTENSIDAD UC",
        8: "F.C. FETAL", 9: "MOVIMIENTOS FETALES", 10: "PRESENTACIÓN",
        11: "M. INTEGRAS", 12: "M. ROTAS", 13: "LÍQUIDO AMNIÓTICO", 14: "HORA RUPTURA",
        15: "DILATACIÓN", 16: "BORRAMIENTO",
        17: "MONITOREO (HORA)", 18: "MONITOREO (CATEGORÍA)",
        19: "OXITOCINA (MILIUNID)", 20: "OXITOCINA (CC/H)"
    };

    // Preparar objeto indexado por parametro_id para fácil acceso
    const datosPorId = {};
    medicionesEnHora.forEach(m => {
        const pid = parseInt(m.parametro_id || (m.parametro?.id) || m.parametro);
        if (isNaN(pid)) return;

        let pName = paramNamesFallback[pid] || (m.parametro?.nombre) || `PARÁMETRO ${pid}`;
        pName = pName.toUpperCase();

        if (!datosPorId[pid]) datosPorId[pid] = { nombre: pName, valores: [] };

        (m.valores || []).forEach(v => {
            let valor = v.valor_text || (v.valor_number !== null ? v.valor_number.toString() : null) || (v.valor_boolean !== null ? (v.valor_boolean ? 'SÍ' : 'NO') : null);
            if (valor) datosPorId[pid].valores.push(normalizarTextoVistaPrevia(valor));
        });
    });

    let html = `
        <div class="medicion-card">
            <div class="card-time">
                <span>🕒 ${timeStr}</span>
                <span class="card-time-date">${dateStr}</span>
            </div>
            <div class="card-params">`;

    let totalItemsMostrados = 0;

    // Renderizar por categorías
    categorias.forEach(cat => {
        // Filtrar qué parámetros de esta categoría tienen datos
        const paramsConDatos = cat.ids.filter(id => datosPorId[id] && datosPorId[id].valores.length > 0);
        
        if (paramsConDatos.length > 0) {
            html += `<div class="card-category-title">${cat.nombre}</div>`;
            
            paramsConDatos.forEach(id => {
                totalItemsMostrados++;
                const p = datosPorId[id];
                const valStr = p.valores.join(' / ');
                html += `
                    <div class="param-item">
                        <span class="param-name-tag">${p.nombre}</span>
                        <span class="param-value-tag">${valStr}</span>
                    </div>`;
            });
        }
    });

    // Parámetros huérfanos (que no están en las categorías definidas)
    const idsEnCategorias = categorias.flatMap(c => c.ids);
    const huerfanos = Object.keys(datosPorId).filter(id => !idsEnCategorias.includes(parseInt(id)) && datosPorId[id].valores.length > 0);
    
    if (huerfanos.length > 0) {
        html += `<div class="card-category-title neutral">OTROS PARÁMETROS</div>`;
        huerfanos.forEach(id => {
            totalItemsMostrados++;
            const p = datosPorId[id];
            html += `
                <div class="param-item">
                    <span class="param-name-tag">${p.nombre}</span>
                    <span class="param-value-tag">${p.valores.join(' / ')}</span>
                </div>`;
        });
    }

    if (totalItemsMostrados === 0) {
        html += `<div class="medicion-empty">Sin datos</div>`;
    }

    html += `
            </div>
        </div>`;
    return html;
}

/**
 * Limpia y oculta la vista previa del paciente.
 */
function limpiarFormularioInformativo() {
    const previewContainer = document.getElementById('vista-previa-paciente');
    if (previewContainer) {
        previewContainer.style.display = 'none';
    }
    const btnPdf = document.getElementById('btn-descargar-pdf');
    if (btnPdf) {
        btnPdf.style.display = 'none';
    }
    const medicionesScroll = document.getElementById('preview-mediciones-scroll');
    if (medicionesScroll) {
        medicionesScroll.innerHTML = '';
    }
}


// Función para actualizar el formulario informativo (Vista Previa) con los datos guardados
// Ahora usa la nueva interfaz premium "card-preview"
async function actualizarFormularioInformativo(formularioId, datosCompletos = null) {
    try {
        console.log(`🚀 Actualizando Dashboard de Vista Previa para el formulario ${formularioId}...`);
        
        let formulario, mediciones, paciente;

        

        if (datosCompletos) {
            formulario = datosCompletos.formulario;
            mediciones = datosCompletos.mediciones || [];
            paciente = datosCompletos.paciente;
        } else {
            const timestamp = new Date().getTime();
            formulario = await apiRequest(`/formularios/${formularioId}/?_=${timestamp}`);
            if (!formulario) return;
            
            mediciones = await apiRequest(`/formularios/${formularioId}/mediciones/?_=${timestamp}`);
            
            const pacienteId = formulario.paciente ? (formulario.paciente.id || formulario.paciente) : null;
            if (pacienteId) {
                paciente = await apiRequest(`/pacientes/${pacienteId}/?_=${timestamp}`);
                
                // Cargar biometría
                try {
                    const huellaData = await apiRequest(`/huella/${pacienteId}/?_=${timestamp}`);
                    if (huellaData && typeof actualizarUIHuella === 'function') {
                        actualizarUIHuella(huellaData);
                    }
                } catch (e) {
                    console.warn('No se pudo cargar biometría para el dashboard:', e);
                }
            }
        }
        
        // Mostrar el contenedor de vista previa
        const previewContainer = document.getElementById('vista-previa-paciente');
        if (previewContainer) previewContainer.style.display = 'block';

        // Mostrar botón de PDF si existe formulario
        const btnPdf = document.getElementById('btn-descargar-pdf');
        if (btnPdf && formularioId) {
            btnPdf.style.display = 'inline-block';
        }

        // 1. Actualizar Datos Personales
        if (paciente) {
            const nombreDisplay = document.getElementById('preview-nombre-display');
            if (nombreDisplay) nombreDisplay.textContent = (paciente.nombres || 'SIN NOMBRE').toUpperCase();
            
            const identDisplay = document.getElementById('preview-identificacion-display');
            if (identDisplay) identDisplay.textContent = paciente.num_identificacion || '-';
            
            const aseguradoraDisplay = document.getElementById('preview-aseguradora');
            if (aseguradoraDisplay) aseguradoraDisplay.textContent = (formulario.aseguradora_nombre || (formulario.aseguradora ? formulario.aseguradora.nombre : (paciente.aseguradora || '-')));
            
            const historiaDisplay = document.getElementById('preview-historia');
            if (historiaDisplay) historiaDisplay.textContent = paciente.num_historia_clinica || '-';
            
            let edad = formulario.edad_snapshot;
            if (!edad && paciente.fecha_nacimiento) edad = calcularEdad(paciente.fecha_nacimiento);
            const edadDisplay = document.getElementById('preview-edad');
            if (edadDisplay) edadDisplay.textContent = edad || '-';
            
            const sangreDisplay = document.getElementById('preview-sangre');
            if (sangreDisplay) sangreDisplay.textContent = paciente.tipo_sangre || '-';
            
            const controlesDisplay = document.getElementById('preview-controles');
            if (controlesDisplay) controlesDisplay.textContent = formulario.n_controles_prenatales || '0';
            
            const gestionDisplay = document.getElementById('preview-gestion');
            if (gestionDisplay) gestionDisplay.textContent = formulario.edad_gestion || '-';

            // Antecedentes
            const setPreview = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.textContent = (val !== null && val !== undefined) ? val : '-';
            };
            setPreview('preview-g', paciente.g);
            setPreview('preview-p', paciente.p);
            setPreview('preview-c', paciente.c);
            setPreview('preview-a', paciente.a);
            setPreview('preview-v', paciente.v);
        }

        const respDisplay = document.getElementById('preview-responsable');
        if (respDisplay && formulario.responsable) {
            respDisplay.textContent = formulario.responsable.toUpperCase();
        }

        // 2. Actualizar Dashboard de Mediciones
        const medicionesScroll = document.getElementById('preview-mediciones-scroll');
        if (medicionesScroll) {
            if (mediciones && mediciones.length > 0) {
                // Identificar todas las horas únicas y ordenarlas
                const horasUnicas = [...new Set(mediciones.map(m => m.tomada_en))].sort();
                const totalControlesDisplay = document.getElementById('preview-total-controles');
                if (totalControlesDisplay) totalControlesDisplay.textContent = `${horasUnicas.length} REGISTROS`;
                
                // Limpiar scroll y generar cards
                medicionesScroll.innerHTML = '';
                horasUnicas.forEach(hora => {
                    const medicionesEnHora = mediciones.filter(m => m.tomada_en === hora);
                    medicionesScroll.innerHTML += crearCardMedicionPreview(hora, medicionesEnHora);
                });

                // Sincronizar también con el grid principal (hidden columns/inputs) si es necesario
                const mainTimeInputs = document.querySelectorAll('.time-input');
                horasUnicas.forEach((hora, index) => {
                    if (index < mainTimeInputs.length) {
                        const date = new Date(hora);
                        const year = date.getFullYear();
                        const month = (date.getMonth() + 1).toString().padStart(2, '0');
                        const day = date.getDate().toString().padStart(2, '0');
                        const hours = date.getHours().toString().padStart(2, '0');
                        const minutes = date.getMinutes().toString().padStart(2, '0');
                        mainTimeInputs[index].value = `${year}-${month}-${day}T${hours}:${minutes}`;
                    }
                });

                mediciones.forEach(medicion => {
                    const horaIndex = horasUnicas.indexOf(medicion.tomada_en);
                    if (horaIndex === -1) return;
                    
                    const parametroId = medicion.parametro ? medicion.parametro.id : null;
                    if (!parametroId) return;
                    
                    medicion.valores.forEach(v => {
                        const campoId = v.campo ? v.campo.id : null;
                        if (!campoId) return;
                        
                        const mainSelector = `.data-input[data-parametro-id="${parametroId}"][data-campo-id="${campoId}"][data-hora-index="${horaIndex}"]`;
                        const input = document.querySelector(mainSelector);
                        
                        let valor = '';
                        if (v.valor_text !== null && v.valor_text !== undefined) valor = v.valor_text;
                        else if (v.valor_number !== null && v.valor_number !== undefined) valor = v.valor_number.toString();
                        else if (v.valor_boolean !== null && v.valor_boolean !== undefined) valor = v.valor_boolean ? 'SÍ' : 'NO';
                        
                        if (input) {
                            input.value = valor;
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    });
                });

                if (typeof updateProgressiveColumns === 'function') updateProgressiveColumns();
                
                // Hacer scroll al final para ver lo más reciente
                setTimeout(() => {
                    const liveMedicionesScroll = getLiveElementById('preview-mediciones-scroll');
                    if (!liveMedicionesScroll) return;
                    liveMedicionesScroll.scrollLeft = liveMedicionesScroll.scrollWidth;
                }, 300);

            } else {
                const totalControlesDisplay = document.getElementById('preview-total-controles');
                if (totalControlesDisplay) totalControlesDisplay.textContent = `0 REGISTROS`;
                medicionesScroll.innerHTML = `
                    <div id="preview-empty-state" class="preview-empty-state">
                        <span class="preview-empty-icon">📋</span>
                        <p class="preview-empty-text">No se registran mediciones previas para este paciente todavía.</p>
                        <p class="preview-empty-subtext">Los nuevos registros aparecerán aquí automáticamente.</p>
                    </div>`;
            }
            console.log('✅ Dashboard de Vista Previa actualizado con éxito.');
        }
    } catch (error) {
        console.error('❌ Error al actualizar Dashboard de Vista Previa:', error);
    }
}

/**
 * Abre/actualiza manualmente la vista previa de mediciones.
 */
async function abrirVistaPreviaMediciones() {
    const previewContainer = document.getElementById('vista-previa-paciente');
    const btnPreview = document.getElementById('btn-vista-previa');

    // Si ya está visible, ocultar (toggle).
    if (previewContainer && previewContainer.style.display !== 'none' && previewContainer.style.display !== '') {
        previewContainer.style.display = 'none';
        if (btnPreview) btnPreview.textContent = 'Vista Previa';
        return;
    }

    const formularioId = obtenerValorInput('formulario_id');
    if (!formularioId) {
        mostrarMensaje('Primero guarde el formulario para ver la vista previa de mediciones.', 'warning');
        return;
    }

    await actualizarFormularioInformativo(formularioId);

    if (previewContainer) {
        previewContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    if (btnPreview) btnPreview.textContent = 'Ocultar Vista Previa';
}
        

// Guardar mediciones con envío anidado
/**
 * Guarda TODAS las mediciones pendientes para la hora seleccionada actualmente.
 * Botón Universal para agilizar el registro.
 */
async function guardarTodoElControl() {
    const timeInput = getLiveElementById('hora_registro_actual');
    if (!timeInput || !timeInput.value) {
        mostrarMensaje('Debe fijar la "Hora del Control Actual" antes de guardar', 'error');
        if(timeInput) timeInput.focus();
        return;
    }

    const horaRegistro = obtenerValorInput('hora_registro_actual');
    const medicionesAGuardar = window.medicionesPendientes.filter(m => m.hora === horaRegistro);

    if (medicionesAGuardar.length === 0) {
        mostrarMensaje('No hay nuevos datos registrados para guardar en esta hora', 'warning');
        return;
    }

    const btnSave = getLiveElementById('btn-guardar-todo');
    const originalContent = btnSave ? btnSave.innerHTML : '';
    
    if (btnSave) {
        btnSave.disabled = true;
        btnSave.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> GUARDANDO...';
    }

    try {
        // Asegurar paciente y formulario base
        await guardarPaciente();
        
        const pacienteId = obtenerValorInput('paciente_id');
        let formularioId = obtenerValorInput('formulario_id');

        // Si no hay formulario, creamos uno base con los datos disponibles
        if (!formularioId) {
            console.log('Creando formulario base para las mediciones...');
            const codigo = obtenerValorInput('codigo') || 'FRSPA-022';
            
            const formularioData = {
                codigo: codigo,
                version: obtenerValorInput('version') || '1',
                fecha_elabora: obtenerValorInput('fecha_elabora') || obtenerFechaLocalColombia(),
                num_hoja: parseInt(obtenerValorInput('num_hoja') || '1'),
                paciente: pacienteId,
                aseguradora_nombre: (obtenerValorInput('aseguradora_nombre') || '').trim(),
                diagnostico: obtenerValorInput('diagnostico') || null,
                estado: obtenerValorInput('estado') || 'ACTIVO',
                responsable: obtenerValorInput('responsable') || 'SISTEMA'
            };
            
            const formulario = await apiRequest('/formularios/', 'POST', formularioData);
            if (formulario && formulario.id) {
                formularioId = formulario.id;
                setValorInput('formulario_id', formularioId);
            }
        }

        if (!formularioId) throw new Error('No se pudo establecer un ID de formulario para el guardado');

        // Agrupar mediciones por parámetro
        const medicionesMap = new Map();
        medicionesAGuardar.forEach(med => {
            const key = `${med.parametro_id}`;
            if (!medicionesMap.has(key)) {
                medicionesMap.set(key, {
                    formulario: formularioId,
                    parametro: parseInt(med.parametro_id),
                    tomada_en: new Date(med.hora).toISOString(),
                    valores: []
                });
            }
            const payloadValor = { campo_id: parseInt(med.campo_id) };
            if (med.tipo_valor === 'boolean') {
                const v = (med.valor || "").toString().toUpperCase().trim();
                payloadValor.valor_boolean = v.startsWith('SÍ') || v.startsWith('SI');
            } else if (med.valor !== "" && !isNaN(med.valor) && typeof med.valor !== 'boolean') {
                payloadValor.valor_number = parseFloat(med.valor);
            } else {
                payloadValor.valor_text = med.valor;
            }
            medicionesMap.get(key).valores.push(payloadValor);
        });

        const promesas = Array.from(medicionesMap.values()).map(data => 
            apiRequest('/mediciones/', 'POST', data)
        );

        await Promise.all(promesas);

        // Limpiar pendientes de esta hora
        window.medicionesPendientes = window.medicionesPendientes.filter(m => m.hora !== horaRegistro);

        // Actualizar UI de botones
        document.querySelectorAll('.btn-parametro-premium').forEach(btn => {
            const id = btn.getAttribute('data-parametro-id');
            if (id) actualizarBotonUI(id);
        });

        const horaFormateada = new Date(horaRegistro).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        mostrarMensaje(`✅ ¡Los datos de las ${horaFormateada} se han guardado con éxito!`, 'success');
        
        // Actualizar vista informativa
        await actualizarFormularioInformativo(formularioId);

    } catch (error) {
        console.error('Error al guardar todo el control:', error);
        mostrarMensaje('Error al guardar: ' + error.message, 'error');
    } finally {
        const liveBtnSave = getLiveElementById('btn-guardar-todo');
        if (liveBtnSave) {
            liveBtnSave.disabled = false;
            liveBtnSave.innerHTML = originalContent;
        }
    }
}

// Variable global para almacenar las mediciones que se van a guardar
window.medicionesPendientes = [];

/**
 * Mapa global: { [parametro_id]: { [campo_codigo]: campo_id } }
 * Cargado desde la API al inicio para resolver campo_id cuando no está en el HTML.
 */
window.paramCamposMap = {};

/**
 * Carga el mapa de parámetros→campos desde la API.
 * Se llama una sola vez al cargar la página.
 */
async function loadParamCamposMap() {
    try {
        console.log('🔄 Cargando mapa de campos desde /api/campos-parametro/...');
        const response = await apiRequest('/campos-parametro/');
        // DRF puede devolver el array directo o dentro de .results
        const campos = Array.isArray(response) ? response : (response?.results || []);
        
        // Reset del mapa
        window.paramCamposMap = {};
        
        campos.forEach(campo => {
            const param = campo.parametro;
            if (!param) return;
            
            const paramId = (typeof param === 'object') ? param.id : param;
            if (!window.paramCamposMap[paramId]) {
                window.paramCamposMap[paramId] = {};
            }
            
            // Indexar por código (mayúsculas y minúsculas para robustez)
            if (campo.codigo) {
                const code = campo.codigo.toLowerCase();
                window.paramCamposMap[paramId][code] = campo.id;
                // Si el código es 'VALOR', también registrarlo como clave por defecto
                if (code === 'valor') window.paramCamposMap[paramId]['valor'] = campo.id;
            }
            
            // Indexar también por nombre por si acaso
            if (campo.nombre) {
                window.paramCamposMap[paramId][campo.nombre.toLowerCase()] = campo.id;
            }
        });
        
        console.log('✅ Mapa de campos cargado exitosamente:', window.paramCamposMap);
    } catch (e) {
        console.warn('⚠️ No se pudo cargar el mapa de campos:', e);
    }
}

/**
 * Resuelve el campo_id dado el parametro_id y el campo_codigo.
 * Si ya hay campo_id definido, lo usa directamente.
 */
function resolverCampoId(parametroId, campoId, campoCodigo) {
    if (campoId && campoId !== 'null' && campoId !== 'undefined') return parseInt(campoId);
    
    const pid = parseInt(parametroId);
    const mapa = window.paramCamposMap[pid] || {};
    
    // Intentar por código (en minúsculas por consistencia con loadParamCamposMap)
    const code = (campoCodigo || 'valor').toLowerCase();
    if (mapa[code] !== undefined) return mapa[code];
    
    // Fallback: tomar el primer campo disponible si no se encuentra por código
    const valores = Object.values(mapa);
    if (valores.length > 0) return valores[0];

    // Fallbacks defensivos para parámetros críticos automáticos.
    if (pid === 14) return 18; // Hora Ruptura -> campo TIEMPO
    if (pid === 17) return 19; // Monitoreo Hora -> campo TIEMPO
    
    return null;
}

function obtenerFechaHoraLocalInput() {
    const ahora = new Date();
    const año = ahora.getFullYear();
    const mes = String(ahora.getMonth() + 1).padStart(2, '0');
    const dia = String(ahora.getDate()).padStart(2, '0');
    const horas = String(ahora.getHours()).padStart(2, '0');
    const minutos = String(ahora.getMinutes()).padStart(2, '0');
    return `${año}-${mes}-${dia}T${horas}:${minutos}`;
}

function inicializarHoraRegistroAutomatica() {
    const timeInput = getLiveElementById('hora_registro_actual');
    if (!timeInput) return;
    // Siempre usar hora actual por defecto y evitar digitación manual.
    timeInput.value = obtenerFechaHoraLocalInput();
    timeInput.readOnly = true;
}


function establecerHoraActual() {
    const timeInput = getLiveElementById('hora_registro_actual');
    if (!timeInput) return;
    timeInput.value = obtenerFechaHoraLocalInput();
    const feedback = document.getElementById('hora-seleccionada-feedback');
    if (feedback) {
        feedback.style.display = 'inline';
        setTimeout(() => { feedback.style.display = 'none'; }, 2000);
    }
}

function abrirModalParametro(button) {
    const timeInput = getLiveElementById('hora_registro_actual');
    if (!timeInput || !timeInput.value) {
        inicializarHoraRegistroAutomatica();
    }
    if (!timeInput || !timeInput.value) {
        mostrarMensaje('No se pudo establecer la hora del control actual', 'warning');
        if(timeInput) timeInput.focus();
        return;
    }
    const parametroId = button.getAttribute('data-parametro-id');
    const modal = document.getElementById(`modal-parametro-${parametroId}`);
    if (modal) {
        modal.style.display = 'flex';
        const horaRegistro = timeInput.value;
        const esParametroHoraMonitoreo = String(parametroId) === '17';
        // Limpiar intervalo previo para evitar múltiples timers abiertos.
        if (window._autoHoraModal17Interval) {
            clearInterval(window._autoHoraModal17Interval);
            window._autoHoraModal17Interval = null;
        }
        
        // Pre-llenar con datos pendientes si existen para esta hora
        modal.querySelectorAll('.data-input-modal').forEach(input => {
            const campoId = input.getAttribute('data-campo-id');
            const medicion = window.medicionesPendientes.find(m => 
                m.parametro_id == parametroId && 
                m.campo_id == campoId && 
                m.hora == horaRegistro
            );
            // Parametro 14 (HORA RUPTURA): valor automático, no editable.
            if (String(parametroId) === '14') {
                let valorAutomatico = medicion ? medicion.valor : horaRegistro;
                if (input.type === 'time') {
                    const source = horaRegistro || obtenerFechaHoraLocalInput();
                    const hhmm = source.includes('T') ? source.split('T')[1].slice(0, 5) : source.slice(0, 5);
                    valorAutomatico = medicion ? medicion.valor : hhmm;
                }
                input.value = valorAutomatico;
                input.readOnly = true;
                registrarCambioDatoModal(input);
                return;
            }
            // Parámetro 17 (HORA MONITOREO): siempre automático en tiempo real.
            if (esParametroHoraMonitoreo && input.type === 'datetime-local') {
                input.value = obtenerFechaHoraLocalInput();
                input.readOnly = true;
                registrarCambioDatoModal(input);
                return;
            }
            input.readOnly = false;
            input.value = medicion ? medicion.valor : '';
        });

        // Mantener hora actualizada en tiempo real mientras el modal esté abierto.
        if (esParametroHoraMonitoreo) {
            window._autoHoraModal17Interval = setInterval(() => {
                if (!modal || modal.style.display === 'none') {
                    clearInterval(window._autoHoraModal17Interval);
                    window._autoHoraModal17Interval = null;
                    return;
                }
                const inputHora = modal.querySelector('.data-input-modal[type="datetime-local"]');
                if (inputHora) {
                    inputHora.value = obtenerFechaHoraLocalInput();
                    registrarCambioDatoModal(inputHora);
                }
            }, 1000);
        }
    }
}

/**
 * Actualiza la información visual en el botón del parámetro para mostrar el valor ingresado.
 */
function actualizarBotonUI(parametroId) {
    const btn = document.getElementById(`btn-parametro-${parametroId}`);
    if (!btn) return;

    const valPreview = document.getElementById(`val-preview-${parametroId}`);
    const timeInput = document.getElementById('hora_registro_actual');
    if (!timeInput || !timeInput.value) return;
    const horaRegistro = timeInput.value;

    const mediciones = window.medicionesPendientes.filter(m => 
        m.parametro_id == parametroId && m.hora == horaRegistro
    );

    if (mediciones.length > 0) {
        btn.classList.add('tiene-datos');
        
        // Unir valores (ej: 120/80)
        let valStr = mediciones.map(m => m.valor).join(' / ');
        
        // Truncar si es muy largo para la vista previa
        if (valStr.length > 25) valStr = valStr.substring(0, 22) + '...';
        
        if (valPreview) {
            valPreview.textContent = valStr;
            valPreview.style.color = 'var(--success)';
        }
    } else {
        btn.classList.remove('tiene-datos');
        if (valPreview) {
            valPreview.textContent = '-';
            valPreview.style.color = 'var(--text-main)';
        }
    }
}

/**
 * Captura el cambio en un input de modal y actualiza los pendientes y la UI.
 */
function registrarCambioDatoModal(input) {
    const parametroId = input.getAttribute('data-parametro-id');
    const rawCampoId = input.getAttribute('data-campo-id');
    const campoCodigo = input.getAttribute('data-campo-codigo');
    const tipoValor = input.getAttribute('data-tipo-valor');
    const valor = input.value.trim();
    
    // Resolver campo_id usando helper (usa rawCampoId si existe, sino busca en el mapa por campoCodigo)
    const campoId = resolverCampoId(parametroId, rawCampoId, campoCodigo);

    const timeInput = document.getElementById('hora_registro_actual');
    if (!timeInput || !timeInput.value) return;
    const horaRegistro = timeInput.value;

    const indiceExistente = window.medicionesPendientes.findIndex(m => 
        m.parametro_id == parametroId && 
        m.campo_id == campoId && 
        m.hora == horaRegistro
    );

    if (valor) {
        const nuevaMedicion = {
            parametro_id: parametroId,
            campo_id: campoId,
            tipo_valor: tipoValor,
            valor: valor,
            hora: horaRegistro
        };
        
        if (indiceExistente >= 0) {
            window.medicionesPendientes[indiceExistente] = nuevaMedicion;
        } else {
            window.medicionesPendientes.push(nuevaMedicion);
        }
    } else {
        if (indiceExistente >= 0) {
            window.medicionesPendientes.splice(indiceExistente, 1);
        }
    }

    actualizarBotonUI(parametroId);
}

function cerrarModalParametro(parametroId) {
    const modal = document.getElementById(`modal-parametro-${parametroId}`);
    if (modal) {
        modal.style.display = 'none';
    }
    if (String(parametroId) === '17' && window._autoHoraModal17Interval) {
        clearInterval(window._autoHoraModal17Interval);
        window._autoHoraModal17Interval = null;
    }
}

function guardarTemporalParametro(parametroId) {
    const modal = document.getElementById(`modal-parametro-${parametroId}`);
    const timeInput = document.getElementById('hora_registro_actual');
    const horaRegistro = timeInput.value;
    
    if (!modal) return;
    
    let tieneValores = false;
    const inputs = modal.querySelectorAll('.data-input-modal');
    
    inputs.forEach(input => {
        const rawCampoId = input.getAttribute('data-campo-id');
        const campoCodigo = input.getAttribute('data-campo-codigo');
        const tipoValor = input.getAttribute('data-tipo-valor');
        const valor = input.value.trim();
        
        // Resolver campo_id usando helper
        const campoId = resolverCampoId(parametroId, rawCampoId, campoCodigo);
        
        if (valor) {
            tieneValores = true;
            const indiceExistente = window.medicionesPendientes.findIndex(m => 
                m.parametro_id == parametroId && 
                m.campo_id == campoId && 
                m.hora == horaRegistro
            );
            
            const nuevaMedicion = {
                parametro_id: parametroId,
                campo_id: campoId,
                tipo_valor: tipoValor,
                valor: valor,
                hora: horaRegistro
            };
            
            if (indiceExistente >= 0) {
                window.medicionesPendientes[indiceExistente] = nuevaMedicion;
            } else {
                window.medicionesPendientes.push(nuevaMedicion);
            }
        }
    });
    
    if (tieneValores) {
        const btn = document.getElementById(`btn-parametro-${parametroId}`);
        if (btn) btn.classList.add('tiene-datos');
        cerrarModalParametro(parametroId);
        mostrarMensaje('Dato guardado temporalmente. Pulse "Guardar Formulario" al final.', 'success');
    } else {
        mostrarMensaje('No se ingresaron valores', 'warning');
    }
}

async function guardarMediciones(formularioId) {
    const medicionesMap = new Map();
    
    // 1. Extraer horas válidas definidas en el encabezado de la cuadrícula
    const timeInputs = document.querySelectorAll('.time-input');
    const horaMap = {};
    timeInputs.forEach((input, index) => {
        if (input.value) {
            // Asumimos que el input es datetime-local (YYYY-MM-DDTHH:MM)
            horaMap[index] = new Date(input.value).toISOString();
        }
    });

    // 2. Extraer todos los valores digitados en la cuadrícula
    const dataInputs = document.querySelectorAll('.data-input');
    dataInputs.forEach(input => {
        const valor = input.value.trim();
        if (valor === '') return; // Ignorar celdas vacías
        
        const parametroId = input.getAttribute('data-parametro-id');
        const campoId = input.getAttribute('data-campo-id');
        // El atributo puede llamarse data-hora-index dependiendo de cómo fue renderizado
        let horaIndexAttr = input.getAttribute('data-hora-index');
        
        // Si no lo encuentra, a veces index lo manejan implícitamente, pero en la carga usan data-hora-index
        if (horaIndexAttr === null) return;
        
        const horaIndex = parseInt(horaIndexAttr);
        const tipoValor = input.getAttribute('data-tipo-valor') || 'number';
        
        // Si no hay hora definida para esta columna, se omite (notificamos en consola)
        const horaIso = horaMap[horaIndex];
        if (!horaIso) {
            console.warn(`Valor omitido: Hay datos en la columna ${horaIndex + 1} pero no se definió la hora en el encabezado.`);
            return; 
        }

        const key = `${parametroId}-${horaIso}`;
        if (!medicionesMap.has(key)) {
            medicionesMap.set(key, {
                formulario: formularioId,
                parametro: parseInt(parametroId),
                tomada_en: horaIso,
                valores: []
            });
        }
        
        const payloadValor = { campo_id: parseInt(campoId) };
        if (tipoValor === 'number') {
            payloadValor.valor_text = valor; // Para compatibilidad usamos valor_text 
        } else if (tipoValor === 'text') {
            payloadValor.valor_text = valor;
        } else if (tipoValor === 'boolean') {
            const valorUpper = valor.toUpperCase();
            payloadValor.valor_boolean = valorUpper.startsWith('SÍ') || valorUpper.startsWith('SI');
        } else {
            payloadValor.valor_text = valor;
        }
        
        medicionesMap.get(key).valores.push(payloadValor);
    });

    // 3. Incluir las mediciones que vengan del modal (por si se sigue usando)
    if (window.medicionesPendientes && window.medicionesPendientes.length > 0) {
        window.medicionesPendientes.forEach(med => {
            const horaIso = new Date(med.hora).toISOString();
            const key = `${med.parametro_id}-${horaIso}`;
            
            if (!medicionesMap.has(key)) {
                medicionesMap.set(key, {
                    formulario: formularioId,
                    parametro: parseInt(med.parametro_id),
                    tomada_en: horaIso,
                    valores: []
                });
            }
            
            const payloadValor = { campo_id: parseInt(med.campo_id) };
            if (med.tipo_valor === 'number') {
                payloadValor.valor_text = med.valor;
            } else if (med.tipo_valor === 'text') {
                payloadValor.valor_text = med.valor;
            } else if (med.tipo_valor === 'boolean') {
                const valorUpper = med.valor.toUpperCase().trim();
                payloadValor.valor_boolean = valorUpper.startsWith('SÍ') || valorUpper.startsWith('SI');
            }
            
            // Evitar duplicados si existe en cuadrícula y modal
            const existingCampoIndex = medicionesMap.get(key).valores.findIndex(v => v.campo_id === payloadValor.campo_id);
            if (existingCampoIndex >= 0) {
                medicionesMap.get(key).valores[existingCampoIndex] = payloadValor; // Sobrescribir con modal
            } else {
                medicionesMap.get(key).valores.push(payloadValor);
            }
        });
    }
    
    // Si no hay nada para guardar, salir temprano
    if (medicionesMap.size === 0) {
        console.log('No hay mediciones en la cuadrícula ni pendientes para guardar.');
        return;
    }

    const promesas = Array.from(medicionesMap.values()).map(data => 
        apiRequest('/mediciones/', 'POST', data)
    );
    
    try {
        await Promise.all(promesas);
        console.log('Todas las mediciones se han procesado exitosamente.');
    } catch (error) {
        console.error('Error al enviar mediciones al backend:', error);
        throw error;
    }
    
    // Limpieza post-guardado
    window.medicionesPendientes = [];
    document.querySelectorAll('.btn-parametro.tiene-datos').forEach(btn => btn.classList.remove('tiene-datos'));
}

// Mostrar mensajes usando Toastify
function mostrarMensaje(mensaje, tipo = 'info') {
    let backgroundColor = "#3b82f6"; // Info (Blue)
    if (tipo === 'success') backgroundColor = "#10b981"; // Success (Green)
    if (tipo === 'error') backgroundColor = "#ef4444"; // Error (Red)
    if (tipo === 'warning') backgroundColor = "#f59e0b"; // Warning (Orange)

    if (typeof Toastify !== 'undefined') {
        Toastify({
            text: mensaje,
            duration: 5000,
            close: true,
            gravity: "top", 
            position: "right", 
            stopOnFocus: true, 
            style: {
                background: backgroundColor,
                borderRadius: "8px",
                fontWeight: "500",
                boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)"
            }
        }).showToast();
    } else {
        // Fallback si Toastify no carga
        console.log(`[${tipo.toUpperCase()}] ${mensaje}`);
    }
}

// Función para cambiar el texto del botón entre "Guardar" y "Actualizar"
function actualizarTextoBoton(esActualizacion) {
    const btnGuardar = document.getElementById('btn-guardar');
    if (btnGuardar) {
        if (esActualizacion) {
            btnGuardar.textContent = 'Actualizar Formulario';
            btnGuardar.setAttribute('data-es-actualizacion', 'true');
        } else {
            btnGuardar.textContent = 'Guardar Formulario';
            btnGuardar.removeAttribute('data-es-actualizacion');
        }
    }
}

// Función consolidada para buscar paciente completo con formulario y mediciones
// Implementa caché completa de todos los datos del paciente
async function buscarPacienteCompleto(cedula, usarCache = true) {
    try {
        console.log(`Buscando paciente completo para identificación: ${cedula}`);
        
        const cacheKey = 'paciente_completo_data_cache';
        const CACHE_VERSION = 5; // Incrementar si cambia estructura (ej. diagnostico, aseguradora, edad_gestacional, n_controles, estado)
        
        // Verificar si hay datos en caché para este paciente
        if (usarCache) {
            try {
                const cacheData = localStorage.getItem(cacheKey);
                if (cacheData) {
                    const parsedCache = JSON.parse(cacheData);
                    if (parsedCache._cacheVersion !== CACHE_VERSION) {
                        localStorage.removeItem(cacheKey);
                    } else if (parsedCache.paciente && parsedCache.paciente.num_identificacion === cedula) {
                        console.log(`✅ Datos encontrados en caché para paciente: ${cedula}`);
                        console.log('Usando datos de caché (evitando petición HTTP)');
                        if (parsedCache.encontrado === undefined) {
                            parsedCache.encontrado = true;
                        }
                        return parsedCache;
                    } else {
                        // Es un paciente diferente, limpiar caché anterior
                        console.log(`Limpiando caché del paciente anterior (${parsedCache.paciente?.num_identificacion || 'desconocido'})`);
                        localStorage.removeItem(cacheKey);
                    }
                }
            } catch (e) {
                console.warn('Error al leer caché, continuando con petición HTTP:', e);
                localStorage.removeItem(cacheKey);
            }
        }
        
        // Buscar datos del paciente desde la API
        console.log('Realizando petición HTTP al servidor...');
        const data = await apiRequest(`/pacientes/buscar-completo/?num_identificacion=${encodeURIComponent(cedula)}`);
        
        // Verificar si el paciente fue encontrado (nuevo formato sin errores 404)
        if (!data || data.encontrado === false || !data.paciente) {
            console.log('Paciente no encontrado:', data?.mensaje || 'Sin mensaje');
            // Si no se encuentra, limpiar la caché
            localStorage.removeItem(cacheKey);
            return { encontrado: false, mensaje: data?.mensaje || 'Paciente no encontrado' };
        }
        
        // Guardar TODA la data completa en caché
        try {
            const cacheData = {
                _cacheVersion: CACHE_VERSION,
                paciente: data.paciente,
                formulario: data.formulario,
                mediciones: data.mediciones || [],
                huella: data.huella || null,
                num_identificacion: data.paciente.num_identificacion,
                timestamp: new Date().getTime(),
                paciente_id: data.paciente.id
            };
            
            localStorage.setItem(cacheKey, JSON.stringify(cacheData));
            console.log(`✅ Caché guardada completa para paciente: ${data.paciente.num_identificacion}`);
            console.log(`   - Paciente: ${data.paciente.nombres}`);
            console.log(`   - Formulario: ${data.formulario ? 'Sí' : 'No'}`);
            console.log(`   - Mediciones: ${data.mediciones?.length || 0}`);
        } catch (e) {
            console.warn('No se pudo guardar caché completa (datos muy grandes):', e);
            // Si los datos son muy grandes, intentar guardar solo información básica
            try {
                localStorage.setItem('paciente_completo_data_cache', JSON.stringify({
                    _cacheVersion: CACHE_VERSION,
                    paciente: data.paciente,
                    formulario: null,
                    mediciones: [],
                    huella: null,
                    num_identificacion: data.paciente.num_identificacion,
                    timestamp: new Date().getTime(),
                    paciente_id: data.paciente.id,
                    cache_incompleto: true
                }));
                console.log('Caché básica guardada (sin formulario/mediciones por tamaño)');
            } catch (e2) {
                console.error('No se pudo guardar ningún tipo de caché:', e2);
            }
        }
        
        console.log('📦 Datos completos recibidos desde API:', data);
        console.log('📋 Estructura de datos recibidos:');
        console.log('   - encontrado:', data?.encontrado);
        console.log('   - paciente:', data?.paciente ? {
            id: data.paciente.id,
            num_identificacion: data.paciente.num_identificacion,
            nombres: data.paciente.nombres,
            edad_gestacional: data.paciente.edad_gestacional,
            n_controles_prenatales: data.paciente.n_controles_prenatales
        } : 'No disponible');
        console.log('   - formulario:', data?.formulario ? 'Sí' : 'No');
        console.log('   - mediciones:', data?.mediciones?.length || 0);
        return data;
    } catch (error) {
        console.error('Error al buscar paciente completo:', error);
        // En caso de error, limpiar caché
        localStorage.removeItem('paciente_completo_data_cache');
        throw error;
    }
}

/**
 * Llena el formulario con datos de paciente (y formulario si existe).
 * Usa edad_gestacional / n_controles_prenatales de la API cuando vienen en buscar-completo (DGEMPRES03).
 */
async function llenarFormularioDesdePaciente(data) {
    if (!data || !data.paciente) return;
    const p = data.paciente;
    const f = data.formulario || null;

    const set = (id, val) => {
        const el = document.getElementById(id);
        if (el && (val !== undefined && val !== null)) el.value = String(val);
    };

    /** Siempre asigna valor a inputs numéricos; usa '' si no hay dato (incluye 0 como válido). */
    const setNum = (id, val) => {
        const el = document.getElementById(id);
        if (!el) return;
        const ok = val !== undefined && val !== null && val !== '';
        el.value = ok ? String(val) : '';
    };

    set('paciente_id', p.id);
    set('num_historia_clinica', p.num_historia_clinica);
    set('num_identificacion', p.num_identificacion);
    set('nombres', p.nombres);
    set('tipo_sangre', p.tipo_sangre);

    const fechaElabora = document.getElementById('fecha_elabora_paciente');
    if (fechaElabora) fechaElabora.value = p.fecha_nacimiento || obtenerFechaLocalColombia();

    if (p.fecha_nacimiento && typeof calcularEdad === 'function') {
        const edad = calcularEdad(p.fecha_nacimiento);
        set('edad_snapshot', edad);
    }

    const edadGestion = f?.edad_gestion ?? p.edad_gestacional ?? p.edad_gestion;
    const nControles = f?.n_controles_prenatales ?? p.n_controles_prenatales ?? p.controles_prenatales;
    setNum('edad_gestion', edadGestion);
    setNum('n_controles_prenatales', nControles);
    setNum('controles_prenatales', nControles);
    setNum('g', p.g);
    setNum('p', p.p);
    setNum('c', p.c);
    setNum('a', p.a);
    if (typeof console !== 'undefined' && console.log) {
        console.log('📋 [llenarFormulario] edad_gestion:', edadGestion, 'n_controles_prenatales:', nControles,
            '| paciente:', { edad_gestacional: p.edad_gestacional, edad_gestion: p.edad_gestion, n_controles_prenatales: p.n_controles_prenatales, controles_prenatales: p.controles_prenatales },
            '| formulario:', f ? { edad_gestion: f.edad_gestion, n_controles_prenatales: f.n_controles_prenatales } : 'N/A');
    }

    if (document.getElementById('edad_gestacional')) set('edad_gestacional', p.edad_gestacional ?? edadGestion);
    if (document.getElementById('controles_prenatales')) set('controles_prenatales', nControles);

    if (f) {
        set('formulario_id', f.id);
        set('codigo', f.codigo);
        set('num_hoja', f.num_hoja);
        const estadoFormulario = (f.estado || '').toString().toLowerCase();
        set('estado', estadoFormulario || 'g');
        set('diagnostico', f.diagnostico || p.diagnostico || '');
        set('responsable', f.responsable);
        const ase = document.getElementById('aseguradora_nombre');
        if (ase && f.aseguradora && f.aseguradora.nombre) ase.value = f.aseguradora.nombre;
        
        // Cargar vista informativa con los datos consolidados si existen mediciones
        if (typeof actualizarFormularioInformativo === 'function' && data.mediciones) {
            await actualizarFormularioInformativo(f.id, data);
        }
    } else {
        // Limpiar la vista informativa si el paciente no tiene formulario
        if (typeof limpiarFormularioInformativo === 'function') {
            limpiarFormularioInformativo();
        }
        
        if (p.diagnostico) set('diagnostico', p.diagnostico);
        const estadoPaciente = (p.estado || '').toString().toLowerCase();
        set('estado', estadoPaciente || 'g');
        const ase = document.getElementById('aseguradora_nombre');
        if (ase && (p.aseguradora || p.aseguradora_nombre)) {
            ase.value = p.aseguradora || p.aseguradora_nombre || '';
        }
    }

    // Actualizar sección de biometría si existe data
    if (data.huella && typeof actualizarUIHuella === 'function') {
        console.log('🔐 Cargando biometría guardada en la interfaz...');
        actualizarUIHuella(data.huella);
    } else {
        // Limpiar UI de biometría si no hay datos
        const imgH = document.getElementById('imgHuella');
        const imgF = document.getElementById('imgFirma');
        if (imgH) { imgH.src = ''; imgH.style.display = 'none'; }
        if (imgF) { imgF.src = ''; imgF.style.display = 'none'; }
        const estH = document.getElementById('estadoHuella');
        const estF = document.getElementById('estadoFirma');
        if (estH) { estH.innerHTML = 'No capturada'; estH.style.display = 'block'; }
        if (estF) { estF.innerHTML = 'No capturada'; estF.style.display = 'block'; }
    }
}

// Función para obtener los datos completos del paciente en caché
function obtenerPacienteCache(numIdentificacion = null) {
    try {
        const cacheKey = 'paciente_completo_data_cache';
        const cacheData = localStorage.getItem(cacheKey);
        
        if (cacheData) {
            const parsedCache = JSON.parse(cacheData);
            
            // Si se especifica un num_identificacion, verificar que coincida
            if (numIdentificacion && parsedCache.num_identificacion !== numIdentificacion) {
                console.log(`Caché encontrada pero para otro paciente (${parsedCache.num_identificacion} vs ${numIdentificacion})`);
                return null;
            }
            
            // Verificar que la caché no sea muy antigua (opcional: más de 1 hora)
            const ahora = new Date().getTime();
            const unaHora = 60 * 60 * 1000; // 1 hora en milisegundos
            if (parsedCache.timestamp && (ahora - parsedCache.timestamp) > unaHora) {
                console.log('Caché expirada (más de 1 hora), limpiando...');
                localStorage.removeItem(cacheKey);
                return null;
            }
            
            return parsedCache;
        }
        return null;
    } catch (error) {
        console.error('Error al obtener caché del paciente:', error);
        return null;
    }
}

// Función para limpiar la caché del paciente
function limpiarPacienteCache() {
    localStorage.removeItem('paciente_completo_data_cache');
    // Mantener compatibilidad con caché antigua
    localStorage.removeItem('paciente_actual_cache');
    localStorage.removeItem('paciente_completo_cache');
    console.log('✅ Caché del paciente limpiada completamente');
}

// Función para buscar formularios existentes del paciente (mantenida para compatibilidad)
async function buscarFormularioExistente(pacienteId, numIdentificacion) {
    try {
        // Buscar formularios por paciente o por num_identificacion
        let formularios = null;
        if (pacienteId) {
            formularios = await apiRequest(`/formularios/?paciente=${pacienteId}`);
        } else if (numIdentificacion) {
            formularios = await apiRequest(`/formularios/?paciente__num_identificacion=${numIdentificacion}`);
        }
        
        if (!formularios) return null;
        
        // DRF devuelve resultados paginados con formato {results: [...]}
        const listaFormularios = formularios?.results || formularios || [];
        
        if (listaFormularios.length > 0) {
            // Retornar el formulario más reciente
            return listaFormularios[0];
        }
        return null;
    } catch (error) {
        console.error('Error al buscar formulario existente:', error);
        return null;
    }
}

// Función para bloquear/desbloquear una columna completa
function bloquearColumna(horaIndex, bloquear = true) {
    // Bloquear todos los inputs de datos de esa columna
    const dataInputs = document.querySelectorAll(`.data-input[data-hora-index="${horaIndex}"]`);
    dataInputs.forEach(input => {
        if (bloquear) {
            input.disabled = true;
            input.readOnly = true;
            input.style.backgroundColor = '#f0f0f0';
            input.style.cursor = 'not-allowed';
            input.setAttribute('data-bloqueado', 'true');
        } else {
            input.disabled = false;
            input.readOnly = false;
            input.style.backgroundColor = '';
            input.style.cursor = '';
            input.removeAttribute('data-bloqueado');
        }
    });
    
    // Bloquear el input de tiempo de esa columna
    const timeInput = document.querySelector(`.time-input[data-hora-index="${horaIndex}"]`);
    if (timeInput) {
        if (bloquear) {
            timeInput.disabled = true;
            timeInput.readOnly = true;
            timeInput.style.backgroundColor = '#f0f0f0';
            timeInput.style.cursor = 'not-allowed';
            timeInput.setAttribute('data-bloqueado', 'true');
        } else {
            timeInput.disabled = false;
            timeInput.readOnly = false;
            timeInput.style.backgroundColor = '';
            timeInput.style.cursor = '';
            timeInput.removeAttribute('data-bloqueado');
        }
    }
}

// Función para desbloquear todas las columnas
function desbloquearTodasLasColumnas() {
    const timeInputs = document.querySelectorAll('.time-input');
    timeInputs.forEach((input, index) => {
        bloquearColumna(index, false);
    });
}

// Función para limpiar la tabla de mediciones informativa (acordeón superior)
function limpiarFormularioInformativo() {
    // 0. Limpiar/ocultar nueva vista previa clínica si existe
    const previewContainer = document.getElementById('vista-previa-paciente');
    if (previewContainer) previewContainer.style.display = 'none';
    const btnPreview = document.getElementById('btn-vista-previa');
    if (btnPreview) btnPreview.textContent = 'Vista Previa';
    const previewScroll = document.getElementById('preview-mediciones-scroll');
    if (previewScroll) {
        previewScroll.innerHTML = '';
    }
    const totalControles = document.getElementById('preview-total-controles');
    if (totalControles) totalControles.textContent = '0 REGISTROS';

    const collapsibleBody = document.querySelector('.collapsible-body');
    if (!collapsibleBody) return;

    // 1. Limpiar fechas/horas del encabezado
    collapsibleBody.querySelectorAll('.info-time').forEach(span => {
        span.textContent = '';
    });

    // 2. Limpiar todos los valores de datos
    collapsibleBody.querySelectorAll('.data-cell .info-value').forEach(span => {
        span.textContent = '-';
    });

    // 3. Limpiar datos del paciente en el encabezado
    collapsibleBody.querySelectorAll('.patient-table .info-value, .form-footer .info-value').forEach(span => {
        span.textContent = '-';
    });

    // 4. Vaciar el cuerpo de la tabla de mediciones para forzar regeneración
    const medicionesBody = collapsibleBody.querySelector('#mediciones-informativa-body');
    if (medicionesBody) {
        medicionesBody.innerHTML = '';
    }
}

// Limpiar todos los campos del formulario y el grid
function limpiarFormulario() {
    console.log('🧹 Limpiando campos del formulario y reiniciando grid...');
    
    // Limpiar vista informativa superior
    limpiarFormularioInformativo();
    
    // Limpiar caché del paciente al limpiar el formulario
    limpiarPacienteCache();
    
    // IDs de campos a limpiar
    const camposALimpiar = [
        'paciente_id', 'formulario_id', 'num_historia_clinica', 
        'nombres', 'tipo_sangre', 'fecha_elabora_paciente', 
        'diagnostico', 'edad_snapshot', 'edad_gestion', 
        'n_controles_prenatales', 'responsable', 'aseguradora_nombre'
    ];

    camposALimpiar.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    
    // Restablecer fecha actual en fecha_elabora_paciente
    const fechaElaboraPaciente = document.getElementById('fecha_elabora_paciente');
    if (fechaElaboraPaciente) {
        fechaElaboraPaciente.value = obtenerFechaLocalColombia();
    }

    // Desbloquear todas las columnas antes de limpiar
    desbloquearTodasLasColumnas();

    // Limpiar variables de mediciones para la nueva interfaz
    if (window.medicionesPendientes) {
        window.medicionesPendientes = [];
    }
    
    // Limpiar el estado visual de los botones de parámetros
    document.querySelectorAll('.btn-parametro').forEach(btn => {
        const id = btn.getAttribute('data-parametro-id');
        if (id) actualizarBotonUI(id);
    });

    const timeGlobal = document.getElementById('hora_registro_actual');
    if (timeGlobal) timeGlobal.value = '';

    // Limpiar el grid original (por si queda algo en la interfaz colapsable o DOM viejo)
    document.querySelectorAll('.data-input, .data-input-modal').forEach(input => {
        input.value = '';
        input.disabled = false;
        input.readOnly = false;
        input.style.backgroundColor = '';
        input.style.cursor = '';
    });
    
    // Limpiar los inputs de tiempo
    document.querySelectorAll('.time-input').forEach(input => {
        input.value = '';
        input.disabled = false;
        input.readOnly = false;
        input.style.backgroundColor = '';
        input.style.cursor = '';
    });

    // REINICIAR COLUMNAS PROGRESIVAS: Ocultar todas excepto la Hora 0
    const tables = document.querySelectorAll('table.control-grid[data-progressive-hours]');
    tables.forEach(table => {
        table.setAttribute('data-progressive-last-visible', '0');
        // Ocultar todas las celdas de horas 1-9
        for (let h = 1; h <= 9; h++) {
            table.querySelectorAll('.col-hour-' + h).forEach(el => {
                el.classList.add('progressive-hours-hidden');
            });
        }
    });
    
    // Limpiar biometría
    const imgH = document.getElementById('imgHuella');
    const imgF = document.getElementById('imgFirma');
    if (imgH) { imgH.src = ''; imgH.style.display = 'none'; }
    if (imgF) { imgF.src = ''; imgF.style.display = 'none'; }
    const estH = document.getElementById('estadoHuella');
    const estF = document.getElementById('estadoFirma');
    if (estH) { estH.innerHTML = 'No capturada'; estH.style.display = 'block'; }
    if (estF) { estF.innerHTML = 'Firma pendiente'; estF.style.display = 'block'; }
    const btnVerH = document.getElementById('btnVerHuella');
    if (btnVerH) btnVerH.style.display = 'none';

    // Restablecer el botón a "Guardar"
    actualizarTextoBoton(false);
}

// Función para obtener la fecha local de Colombia (UTC-5) en formato YYYY-MM-DD
// Esta función usa la zona horaria local del navegador en lugar de UTC
function obtenerFechaLocalColombia() {
    const ahora = new Date();
    // Obtener la fecha local considerando la zona horaria del navegador
    // Esto evita problemas cuando el servidor está en UTC y el cliente en otra zona horaria
    const año = ahora.getFullYear();
    const mes = String(ahora.getMonth() + 1).padStart(2, '0');
    const dia = String(ahora.getDate()).padStart(2, '0');
    return `${año}-${mes}-${dia}`;
}

// Columnas progresivas: solo Hora 0 visible; al llenar una celda de la última columna visible, aparece la siguiente
function initProgressiveHours() {
    var tables = document.querySelectorAll('table.control-grid[data-progressive-hours]');
    tables.forEach(function (table) {
        if (table.classList.contains('progressive-hours')) return;
        table.classList.add('progressive-hours');

        var timeRow = table.querySelector('thead tr.time-row');
        var timeCells = timeRow ? timeRow.querySelectorAll('th.time-cell') : [];
        var numHours = timeCells.length;
        if (numHours < 2) return;

        timeCells.forEach(function (th, i) {
            var inp = th.querySelector('input.time-input');
            var idx = inp ? parseInt(inp.getAttribute('data-hora-index'), 10) : i;
            if (isNaN(idx)) idx = i;
            th.classList.add('col-hour-' + idx);
            if (idx >= 1) th.classList.add('progressive-hours-hidden');
        });

        table.querySelectorAll('tbody tr').forEach(function (tr) {
            if (tr.classList.contains('section-header')) return;
            var cells = tr.querySelectorAll('td.data-cell');
            cells.forEach(function (td, i) {
                var first = td.querySelector('.data-input');
                var idx = first ? parseInt(first.getAttribute('data-hora-index'), 10) : i;
                if (isNaN(idx)) idx = i;
                td.classList.add('col-hour-' + idx);
                if (idx >= 1) td.classList.add('progressive-hours-hidden');
            });
        });

        table.setAttribute('data-progressive-last-visible', '0');

        table.addEventListener('change', function (e) {
            var input = e.target;
            if (!input.classList.contains('data-input')) return;
            var table = input.closest('table.control-grid[data-progressive-hours]');
            if (!table) return;
            var last = parseInt(table.getAttribute('data-progressive-last-visible'), 10);
            if (isNaN(last)) last = 0;
            var hi = parseInt(input.getAttribute('data-hora-index'), 10);
            if (isNaN(hi)) return;
            var val = (input.value || '').trim();
            if (hi !== last || !val) return;
            var next = last + 1;
            if (next >= numHours) return;

            var nextCells = table.querySelectorAll('.col-hour-' + next);
            nextCells.forEach(function (el) { el.classList.remove('progressive-hours-hidden'); });
            table.setAttribute('data-progressive-last-visible', String(next));
        });
    });
}

function revealProgressiveHoursUpTo(maxHour) {
    if (maxHour == null || maxHour < 0) return;
    var tables = document.querySelectorAll('table.control-grid[data-progressive-hours]');
    tables.forEach(function (table) {
        var last = parseInt(table.getAttribute('data-progressive-last-visible'), 10);
        if (isNaN(last)) last = 0;
        var to = Math.max(last, maxHour);
        for (var h = 1; h <= to; h++) {
            table.querySelectorAll('.col-hour-' + h).forEach(function (el) {
                el.classList.remove('progressive-hours-hidden');
            });
        }
        table.setAttribute('data-progressive-last-visible', String(to));
    });
}

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado, inicializando aplicación...');
    
    // Cargar aseguradoras al iniciar
    cargarAseguradoras();

    // Cargar mapa de campos por parámetro (para resolver campo_id en modales sin data-campo-id)
    loadParamCamposMap();

    initProgressiveHours();
    
    // Asegurar que los campos de fecha del grid estén vacíos (sin valores por defecto)
    document.querySelectorAll('.time-input').forEach(input => {
        input.value = '';
    });
    
    // Establecer fecha actual por defecto
    const hoy = obtenerFechaLocalColombia();
    const fechaElabora = document.getElementById('fecha_elabora');
    if (fechaElabora && !fechaElabora.value) {
        fechaElabora.value = hoy;
    }
    
    // Establecer fecha actual por defecto en fecha_elabora_paciente
    const fechaElaboraPaciente = document.getElementById('fecha_elabora_paciente');
    if (fechaElaboraPaciente) {
        fechaElaboraPaciente.value = hoy;
    }

    // Recalcular edad cuando cambie la fecha de nacimiento (fecha_elabora_paciente)
    const fechaNacimientoInput = document.getElementById('fecha_elabora_paciente');
    const edadInput = document.getElementById('edad_snapshot');
    if (fechaNacimientoInput && edadInput) {
        fechaNacimientoInput.addEventListener('change', function() {
            if (this.value) {
                edadInput.value = calcularEdad(this.value);
                console.log(`🎂 Edad recalculada manualmente: ${edadInput.value}`);
            }
        });
    }
    
    // Búsqueda automática deshabilitada por petición del usuario para evitar interrupciones 
    // en el registro de pacientes nuevos. Los flujos se separan:
    // 1. Consulta: Exclusivamente por botones de búsqueda.
    // 2. Registro: Flujo manual sin interferencias.
    const numIdentificacionInput = document.getElementById('num_identificacion');
    if (numIdentificacionInput) {
        console.log('Búsqueda automática por blur deshabilitada para mejorar flujo de ingreso.');
    }

    // Listener para cambios en la hora del control actual (actualiza todos los botones)
    const horaRegistroInput = document.getElementById('hora_registro_actual');
    if (horaRegistroInput) {
        inicializarHoraRegistroAutomatica();
        horaRegistroInput.addEventListener('change', function() {
            console.log('Cambio de hora detectado, actualizando botones...');
            document.querySelectorAll('.btn-parametro-premium').forEach(btn => {
                const id = btn.getAttribute('data-parametro-id');
                if (id) actualizarBotonUI(id);
            });
        });
    }

    // Listener delegado para los inputs de los modales (Captura en tiempo real)
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('data-input-modal')) {
            registrarCambioDatoModal(e.target);
        }
    });

    // Detectar también cambios en selects de modales
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('data-input-modal') && e.target.tagName === 'SELECT') {
            registrarCambioDatoModal(e.target);
            mostrarAutoGuardado();
            // Cerrar automáticamente el modal de medición tras seleccionar un valor.
            cerrarModalDesdeElemento(e.target);
        }
    });

    // Para inputs/fechas/horas: guardar en blur y cerrar automáticamente.
    document.addEventListener('blur', function(e) {
        const target = e.target;
        if (!target || !target.classList || !target.classList.contains('data-input-modal')) return;
        if (target.tagName === 'SELECT') return;

        registrarCambioDatoModal(target);
        const valor = (target.value || '').trim();
        if (valor) {
            mostrarAutoGuardado();
            cerrarModalDesdeElemento(target);
        }
    }, true);

    // Permitir cerrar tocando/clickeando fuera del contenido del modal.
    document.addEventListener('click', function(e) {
        const overlay = e.target;
        if (!overlay || !overlay.classList || !overlay.classList.contains('modal-parametro')) return;
        const match = overlay.id ? overlay.id.match(/^modal-parametro-(\d+)$/) : null;
        if (match && match[1]) cerrarModalParametro(match[1]);
    });
    
    // Event listeners
    const btnBuscarPacienteOld = document.getElementById('btn-buscar-paciente');
    if (btnBuscarPacienteOld) {
        btnBuscarPacienteOld.addEventListener('click', buscarPaciente);
    }
    
    const formulario = document.getElementById('formulario-clinico');
    if (formulario) {
        console.log('Formulario encontrado, registrando event listener para submit...');
        
        formulario.addEventListener('submit', async function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Submit del formulario detectado, iniciando guardado...');
            
            // Deshabilitar el botón para evitar doble envío
            const btnGuardar = document.getElementById('btn-guardar');
            if (btnGuardar) {
                btnGuardar.disabled = true;
                btnGuardar.textContent = 'Guardando...';
            }
            
            try {
                await guardarFormulario();
                console.log('Formulario guardado exitosamente');
            } catch (error) {
                console.error('Error en guardarFormulario:', error);
                mostrarMensaje('Error al guardar formulario', 'error');
            } finally {
                // Rehabilitar el botón y restaurar texto según si es actualización
                if (btnGuardar) {
                    btnGuardar.disabled = false;
                    const formularioId = obtenerValorInput('formulario_id');
                    if (formularioId) {
                        btnGuardar.textContent = 'Actualizar Formulario';
                    } else {
                        btnGuardar.textContent = 'Guardar Formulario';
                    }
                }
            }
        });
        
        console.log('Event listener registrado correctamente');
    } else {
        console.error('ERROR: No se encontró el formulario con id "formulario-clinico"');
    }
    
    // Listener directo al botón como respaldo
    const btnGuardar = document.getElementById('btn-guardar');
    if (btnGuardar) {
        console.log('Botón de guardar encontrado, agregando listener directo...');
        btnGuardar.addEventListener('click', async function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Click en botón Guardar detectado');
            
            // Deshabilitar el botón
            btnGuardar.disabled = true;
            btnGuardar.textContent = 'Guardando...';
            
            try {
                await guardarFormulario();
                console.log('Formulario guardado exitosamente desde botón');
            } catch (error) {
                console.error('Error al guardar desde botón:', error);
                mostrarMensaje('Error al guardar formulario', 'error');
            } finally {
                // Rehabilitar el botón y restaurar texto según si es actualización
                btnGuardar.disabled = false;
                const formularioId = obtenerValorInput('formulario_id');
                if (formularioId) {
                    btnGuardar.textContent = 'Actualizar Formulario';
                } else {
                    btnGuardar.textContent = 'Guardar Formulario';
                }
            }
        });
    } else {
        console.error('ERROR: No se encontró el botón con id "btn-guardar"');
    }
    
    // Función compartida para buscar por documento
    async function buscarPorDocumento(documento) {
        if (!documento) {
            mostrarMensaje("Ingrese el documento del paciente", "error");
            return;
        }

        // Limpiar formulario antes de buscar
        limpiarFormulario();
        // Restaurar el valor del documento buscado
        const documentoInput = document.getElementById('documento');
        if (documentoInput) {
            documentoInput.value = documento;
        }

        try {
            // Usar endpoint consolidado que trae paciente, formulario y mediciones en una sola petición
            const data = await buscarPacienteCompleto(documento);
            
            // Verificar si el paciente fue encontrado (nuevo formato sin errores 404)
            if (!data || data.encontrado === false || !data.paciente) {
                const mensaje = data?.mensaje || "No se encontró ningún formulario ni paciente para este documento. Puede crear uno nuevo.";
                mostrarMensaje(mensaje, "info");
                limpiarFormulario();
                const documentoInput = document.getElementById('documento');
                if (documentoInput) {
                    documentoInput.value = documento;
                }
                return;
            }
            
            const paciente = data.paciente;
            console.log("Paciente encontrado:", paciente);
            
            // Si hay formulario, procesarlo
            if (data.formulario) {
                const formulario = data.formulario;
                
                console.log("Formulario seleccionado:", formulario);
                console.log("Paciente asociado al formulario:", paciente);
                
                // Llenar campos del paciente
                if (document.getElementById('paciente_id')) {
                    setValorInput('paciente_id', paciente.id);
                }
                if (document.getElementById('formulario_id')) {
                    setValorInput('formulario_id', formulario.id);
                }
                if (document.getElementById('num_historia_clinica')) {
                    setValorInput('num_historia_clinica', paciente.num_historia_clinica || '');
                }
                if (document.getElementById('num_identificacion')) {
                    setValorInput('num_identificacion', paciente.num_identificacion || '');
                }
                if (document.getElementById('nombres')) {
                    setValorInput('nombres', paciente.nombres || '');
                }
                if (document.getElementById('tipo_sangre') && paciente.tipo_sangre) {
                    setValorInput('tipo_sangre', paciente.tipo_sangre || '');
                }
                const fechaElaboraPaciente = document.getElementById('fecha_elabora_paciente');
                if (fechaElaboraPaciente) {
                    const hoy = obtenerFechaLocalColombia();
                    // Priorizar fecha de nacimiento del paciente, luego fecha del formulario, finalmente fecha actual
                    fechaElaboraPaciente.value = paciente.fecha_nacimiento || formulario.fecha_elabora || hoy;
                }
                
                // Llenar campos del formulario
                if (document.getElementById('codigo')) {
                    setValorInput('codigo', formulario.codigo || '');
                }
                if (document.getElementById('num_hoja')) {
                    setValorInput('num_hoja', formulario.num_hoja || '');
                }
                if (document.getElementById('estado')) {
                    const estadoFormulario = (formulario.estado || '').toString().toLowerCase();
                    setValorInput('estado', estadoFormulario);
                }
                if (document.getElementById('diagnostico')) {
                    setValorInput('diagnostico', formulario.diagnostico || paciente.diagnostico || '');
                }
                if (document.getElementById('edad_snapshot')) {
                    setValorInput('edad_snapshot', formulario.edad_snapshot || '');
                }
                const eg = formulario.edad_gestion ?? paciente.edad_gestacional ?? paciente.edad_gestion;
                const nc = formulario.n_controles_prenatales ?? paciente.n_controles_prenatales ?? paciente.controles_prenatales;
                if (document.getElementById('edad_gestion')) {
                    setValorInput('edad_gestion', (eg != null && eg !== '') ? String(eg) : '');
                }
                if (document.getElementById('n_controles_prenatales')) {
                    setValorInput('n_controles_prenatales', (nc != null && nc !== '') ? String(nc) : '');
                }
                if (document.getElementById('controles_prenatales')) {
                    setValorInput('controles_prenatales', (nc != null && nc !== '') ? String(nc) : '');
                }
                if (document.getElementById('responsable')) {
                    setValorInput('responsable', formulario.responsable || '');
                }
                const aseInput = document.getElementById('aseguradora_nombre');
                if (aseInput && formulario.aseguradora && formulario.aseguradora.nombre) {
                    aseInput.value = formulario.aseguradora.nombre;
                }
                
                // Calcular la edad usando la fecha de nacimiento del paciente
                if (document.getElementById('edad_snapshot') && paciente.fecha_nacimiento) {
                    setValorInput('edad_snapshot', calcularEdad(paciente.fecha_nacimiento));
                }
                
                // Cargar las mediciones en el grid usando datos consolidados (evita petición HTTP)
                await cargarMedicionesEnGrid(formulario.id, data.mediciones || []);
                
                // Actualizar el formulario informativo usando datos consolidados (evita múltiples peticiones HTTP)
                await actualizarFormularioInformativo(formulario.id, data);
                
                // Actualizar sección de biometría si existe data
                if (data.huella && typeof actualizarUIHuella === 'function') {
                    console.log('🔐 Cargando biometría guardada en la interfaz (desde buscarPorDocumento)...');
                    actualizarUIHuella(data.huella);
                } else {
                    // Limpiar UI de biometría si no hay datos
                    actualizarUIHuella({ imagen_huella: null, imagen_firma: null });
                }
                
                // Cambiar botón a "Actualizar" ya que se encontró un formulario
                actualizarTextoBoton(true);
                
                mostrarMensaje('Datos encontrados', "success");
            } else {
                // No hay formulario, pero sí paciente - llenar solo datos del paciente
                    if (document.getElementById('paciente_id')) {
                        setValorInput('paciente_id', paciente.id);
                    }
                    if (document.getElementById('num_historia_clinica')) {
                        setValorInput('num_historia_clinica', paciente.num_historia_clinica || '');
                    }
                    if (document.getElementById('num_identificacion')) {
                        setValorInput('num_identificacion', paciente.num_identificacion || '');
                    }
                    if (document.getElementById('nombres')) {
                        setValorInput('nombres', paciente.nombres || '');
                    }
                    if (document.getElementById('tipo_sangre')) {
                        setValorInput('tipo_sangre', paciente.tipo_sangre || '');
                    }
                    const fechaElaboraPaciente = document.getElementById('fecha_elabora_paciente');
                    if (fechaElaboraPaciente) {
                        const hoy = obtenerFechaLocalColombia();
                        fechaElaboraPaciente.value = paciente.fecha_nacimiento || hoy;
                    }
                    if (document.getElementById('edad_snapshot') && paciente.fecha_nacimiento) {
                        const edad = calcularEdad(paciente.fecha_nacimiento);
                        setValorInput('edad_snapshot', edad);
                    }
                    const eg = paciente.edad_gestacional ?? paciente.edad_gestion;
                    const nc = paciente.n_controles_prenatales ?? paciente.controles_prenatales;
                    if (document.getElementById('edad_gestion') && (eg != null || eg === 0)) {
                        setValorInput('edad_gestion', eg);
                    }
                    if (document.getElementById('n_controles_prenatales') && (nc != null || nc === 0)) {
                        setValorInput('n_controles_prenatales', nc);
                    }
                    if (document.getElementById('controles_prenatales') && (nc != null || nc === 0)) {
                        setValorInput('controles_prenatales', nc);
                    }
                    if (document.getElementById('diagnostico')) {
                        setValorInput('diagnostico', paciente.diagnostico || '');
                    }
                    if (document.getElementById('estado')) {
                        const estadoPaciente = (paciente.estado || '').toString().toLowerCase();
                        setValorInput('estado', estadoPaciente || 'g');
                    }
                    for (const key of ['g', 'p', 'c', 'a']) {
                        const v = paciente[key];
                        const el = document.getElementById(key);
                        if (el && (v != null || v === 0)) el.value = v;
                    }
                    const aseEl = document.getElementById('aseguradora_nombre');
                    if (aseEl && (paciente.aseguradora || paciente.aseguradora_nombre)) {
                        aseEl.value = paciente.aseguradora || paciente.aseguradora_nombre || '';
                    }
                    // Mantener botón en "Guardar" ya que no hay formulario
                    actualizarTextoBoton(false);
                    
                    // Actualizar biometría del paciente aunque no tenga formulario
                    if (data.huella && typeof actualizarUIHuella === 'function') {
                        console.log('🔐 Cargando biometría del paciente...');
                        actualizarUIHuella(data.huella);
                    } else {
                        actualizarUIHuella({ imagen_huella: null, imagen_firma: null });
                    }
                    
                    mostrarMensaje("Paciente encontrado. No se encontró formulario existente. Puede crear uno nuevo.", "info");
            }
        } catch (error) {
            console.error("Error al buscar formulario:", error);
            mostrarMensaje("Error al buscar datos", "error");
        }
    }

    // Función para detectar si el valor es una cédula/folio (numérico) o un diagnóstico (texto)
    function esCedulaOFolio(valor) {
        // Si es solo números, es una cédula o un folio
        return /^\d+$/.test(valor.trim());
    }
    
    // Función para detectar si es un número de folio (números muy grandes, típicamente > 100000)
    // Event listener para buscar pacientes (por cédula o diagnóstico)
    const btnBuscarPaciente = document.getElementById("btnBuscarPaciente");
    if (btnBuscarPaciente) {
        btnBuscarPaciente.addEventListener("click", async function () {
            // Buscar en ambos campos posibles
            const busquedaInput = document.getElementById("busqueda_paciente");
            const filtroDiagnosticoInput = document.getElementById("filtro_diagnostico");
            const documentoInput = document.getElementById("documento");
            
            let valorBusqueda = "";
            
            // Priorizar el campo de búsqueda unificado
            if (busquedaInput) {
                valorBusqueda = busquedaInput.value.trim();
            } else if (filtroDiagnosticoInput) {
                valorBusqueda = filtroDiagnosticoInput.value.trim();
            } else if (documentoInput) {
                valorBusqueda = documentoInput.value.trim();
            }
            
            if (!valorBusqueda) {
                mostrarMensaje('Ingrese un número de cédula o un diagnóstico para buscar', 'warning');
                return;
            }
            
            // Detectar si es cédula o diagnóstico
            if (esCedulaOFolio(valorBusqueda)) {
                // Es una cédula, buscar paciente individual
                console.log(`Buscando paciente por cédula: ${valorBusqueda}`);
                await buscarPacientePorCedula(valorBusqueda);
            } else {
                // Es un diagnóstico, buscar lista de pacientes en embarazo
                console.log(`Buscando pacientes en embarazo por diagnóstico: ${valorBusqueda}`);
                await buscarPacientesEmbarazadas(valorBusqueda);
            }
        });
    }

    // Botón "Embarazos activos": solo actualmente internas (listar-embarazadas con HESFECSAL IS NULL)
    const btnEmbarazosActivos = document.getElementById("btnEmbarazosActivos");
    if (btnEmbarazosActivos) {
        btnEmbarazosActivos.addEventListener("click", function () {
            buscarPacientesEmbarazadas("", btnEmbarazosActivos, true);
        });
    }
    
    // Función para buscar paciente individual por número de folio
    async function buscarPacientePorFolio(folio) {
        const resultadoDiv = getLiveElementById("resultadoPaciente");
        const btnBuscarPaciente = getLiveElementById("btnBuscarPaciente");
        
        if (!resultadoDiv) {
            console.error("No se encontró el div resultadoPaciente");
            return;
        }
        
        // Mostrar loading
        resultadoDiv.innerHTML = '<p style="text-align: center; padding: 20px;">Buscando paciente por folio...</p>';
        if (btnBuscarPaciente) {
            btnBuscarPaciente.disabled = true;
            btnBuscarPaciente.textContent = 'Buscando...';
        }
        
        try {
            // Buscar usando el endpoint buscar-completo con parámetro folio
            const url = `/pacientes/buscar-completo/?folio=${encodeURIComponent(folio)}`;
            console.log(`Buscando paciente por folio: ${url}`);
            const data = await apiRequest(url);
            
            if (data && data.paciente) {
                await llenarFormularioDesdePaciente(data);
                resultadoDiv.innerHTML = `
                    <div style="text-align: center; padding: 20px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px;">
                        <p style="margin: 0; color: #155724; font-weight: bold;">✅ Paciente encontrado y cargado en el formulario</p>
                        <p style="margin: 5px 0 0 0; color: #155724;">Folio: ${folio} - Cédula: ${data.paciente.num_identificacion} - ${data.paciente.nombres}</p>
                    </div>
                `;
                mostrarMensaje('Paciente encontrado y cargado correctamente', 'success');
            } else {
                resultadoDiv.innerHTML = `
                    <div style="text-align: center; padding: 20px; background: #e7f3ff; border: 1px solid #b8daff; border-radius: 4px;">
                        <p style="margin: 0; color: #004085; font-weight: bold;">ℹ️ Paciente Nuevo</p>
                        <p style="margin: 5px 0 0 0; color: #004085;">No se encontró registro con el folio: ${folio}. Puede proceder con el registro manual.</p>
                    </div>
                `;
                // No mostrar mensaje de advertencia emergente para pacientes nuevos
            }
        } catch (error) {
            console.error("Error al buscar paciente por folio:", error);
            resultadoDiv.innerHTML = `
                <div style="text-align: center; padding: 20px; background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px;">
                    <p style="margin: 0; color: #721c24;">Error al buscar paciente: ${error.message}</p>
                </div>
            `;
            mostrarMensaje('Error al buscar paciente: ' + error.message, 'error');
        } finally {
            const liveBtnBuscarPaciente = getLiveElementById("btnBuscarPaciente");
            if (liveBtnBuscarPaciente) {
                liveBtnBuscarPaciente.disabled = false;
                liveBtnBuscarPaciente.textContent = 'BUSCAR PACIENTE';
            }
        }
    }
    
    // Función para buscar paciente individual por cédula
    async function buscarPacientePorCedula(cedula) {
        const resultadoDiv = getLiveElementById("resultadoPaciente");
        const btnBuscarPaciente = getLiveElementById("btnBuscarPaciente");
        
        if (!resultadoDiv) {
            console.error("No se encontró el div resultadoPaciente");
            return;
        }
        
        // Mostrar loading
        resultadoDiv.innerHTML = '<p style="text-align: center; padding: 20px;">Buscando paciente...</p>';
        if (btnBuscarPaciente) {
            btnBuscarPaciente.disabled = true;
            btnBuscarPaciente.textContent = 'Buscando...';
        }
        
        try {
            // Llenar el campo de identificación
            const numIdentificacionInput = document.getElementById('num_identificacion');
            if (numIdentificacionInput) {
                numIdentificacionInput.value = cedula;
            }
            
            // Buscar el paciente completo usando el endpoint existente
            const data = await buscarPacienteCompleto(cedula);
            
            if (data && data.paciente) {
                await llenarFormularioDesdePaciente(data);
                resultadoDiv.innerHTML = `
                    <div style="text-align: center; padding: 20px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px;">
                        <p style="margin: 0; color: #155724; font-weight: bold;">✅ Paciente encontrado y cargado en el formulario</p>
                        <p style="margin: 5px 0 0 0; color: #155724;">Cédula: ${data.paciente.num_identificacion} - ${data.paciente.nombres}</p>
                    </div>
                `;
                mostrarMensaje('Paciente encontrado y cargado correctamente', 'success');
            } else {
                resultadoDiv.innerHTML = `
                    <div style="text-align: center; padding: 20px; background: #e7f3ff; border: 1px solid #b8daff; border-radius: 4px;">
                        <p style="margin: 0; color: #004085; font-weight: bold;">ℹ️ Paciente Nuevo</p>
                        <p style="margin: 5px 0 0 0; color: #004085;">Cédula: ${cedula} no registrada. Por favor, complete los datos del formulario.</p>
                    </div>
                `;
                // No mostrar mensaje de warning emergente
            }
        } catch (error) {
            console.error("Error al buscar paciente:", error);
            resultadoDiv.innerHTML = `
                <div style="text-align: center; padding: 20px; background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px;">
                    <p style="margin: 0; color: #721c24;">Error al buscar paciente: ${error.message}</p>
                </div>
            `;
            mostrarMensaje('Error al buscar paciente: ' + error.message, 'error');
        } finally {
            const liveBtnBuscarPaciente = getLiveElementById("btnBuscarPaciente");
            if (liveBtnBuscarPaciente) {
                liveBtnBuscarPaciente.disabled = false;
                liveBtnBuscarPaciente.textContent = 'BUSCAR PACIENTE';
            }
        }
    }
    
    // Permitir búsqueda con Enter en el campo de búsqueda
    const busquedaInput = document.getElementById("busqueda_paciente");
    if (busquedaInput) {
        busquedaInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const valor = this.value.trim();
                if (!valor) {
                    mostrarMensaje('Ingrese un número de cédula o un diagnóstico para buscar', 'warning');
                    return;
                }
                
                if (esCedulaOFolio(valor)) {
                    buscarPacientePorCedula(valor);
                } else {
                    buscarPacientesEmbarazadas(valor);
                }
            }
        });
    }
    
    // Mantener compatibilidad con campos antiguos
    const filtroDiagnosticoInput = document.getElementById("filtro_diagnostico");
    if (filtroDiagnosticoInput && !busquedaInput) {
        filtroDiagnosticoInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const valor = this.value.trim() || "";
                if (esCedulaOFolio(valor)) {
                    buscarPacientePorCedula(valor);
                } else {
                    buscarPacientesEmbarazadas(valor);
                }
            }
        });
    }
    
    const documentoInput = document.getElementById("documento");
    if (documentoInput && !busquedaInput && !filtroDiagnosticoInput) {
        documentoInput.addEventListener('blur', async function() {
            const documento = this.value.trim();
            if (!documento) return;
            await buscarPorDocumento(documento);
        });
        
        documentoInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                buscarPorDocumento(this.value.trim());
            }
        });
    }
    
    // Función para buscar pacientes en embarazo (solo actualmente internas). loadingButton: botón a deshabilitar. soloInternas: mostrar etiqueta "solo actualmente internas".
    async function buscarPacientesEmbarazadas(diagnosticoFiltro = "", loadingButton = null, soloInternas = false) {
        const resultadoDiv = getLiveElementById("resultadoPaciente");
        const btn = loadingButton || getLiveElementById("btnBuscarPaciente");
        const originalText = btn ? btn.textContent : '';
        
        if (!resultadoDiv) {
            console.error("No se encontró el div resultadoPaciente");
            return;
        }
        
        resultadoDiv.innerHTML = '<p style="text-align: center; padding: 20px;">Buscando pacientes...</p>';
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Buscando...';
        }
        
        try {
            const params = new URLSearchParams();
            if (diagnosticoFiltro) params.append('diagnostico', diagnosticoFiltro);
            params.append('limit', '100');
            const query = params.toString();
            const endpoint = `/pacientes/listar-embarazadas/${query ? '?' + query : ''}`;
            
            console.log(`Buscando pacientes en embarazo (actualmente internas): ${API_BASE}${endpoint}`);
            const response = await apiRequest(endpoint);
            
            if (response && response.pacientes) {
                mostrarResultadosPacientes(response.pacientes, response.total, diagnosticoFiltro, soloInternas);
            } else {
                resultadoDiv.innerHTML = '<div class="resultados-pacientes resultados-pacientes-empty"><p>No se encontraron pacientes.</p></div>';
            }
        } catch (error) {
            console.error("Error al buscar pacientes:", error);
            resultadoDiv.innerHTML = `<p style="text-align: center; padding: 20px; color: #d32f2f;">Error al buscar pacientes: ${error.message}</p>`;
            mostrarMensaje('Error al buscar pacientes: ' + error.message, 'error');
        } finally {
            const liveBtn = loadingButton || getLiveElementById("btnBuscarPaciente");
            if (liveBtn) {
                liveBtn.disabled = false;
                liveBtn.textContent = originalText;
            }
        }
    }
    
    // Función para mostrar los resultados en una tabla. soloInternas: mostrar "solo actualmente internas" en el encabezado.
    function mostrarResultadosPacientes(pacientes, total, diagnosticoFiltro, soloInternas = false) {
        const resultadoDiv = document.getElementById("resultadoPaciente");
        if (!resultadoDiv) return;
        
        const etiqInternas = soloInternas ? ' (solo actualmente internas)' : '';
        const filtroText = diagnosticoFiltro ? ` · Filtro: "${diagnosticoFiltro}"` : '';
        
        function esc(s) {
            if (s == null || s === undefined) return '';
            return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }
        
        if (pacientes.length === 0) {
            resultadoDiv.innerHTML = `
                <div class="resultados-pacientes resultados-pacientes-empty">
                    <p>No se encontraron pacientes en embarazo${diagnosticoFiltro ? ` con diagnóstico que contenga "${esc(diagnosticoFiltro)}"` : ''}${soloInternas ? ' actualmente internas' : ''}.</p>
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="resultados-pacientes">
                <div class="resultados-pacientes-header">
                    <h3>Resultados${etiqInternas}${filtroText}</h3>
                    <span class="resultados-pacientes-badge">${total} paciente${total !== 1 ? 's' : ''}</span>
                </div>
                <div class="resultados-pacientes-tabla-wrap">
                    <table class="resultados-pacientes-tabla">
                        <thead>
                            <tr>
                                <th>Cédula</th>
                                <th>Folio</th>
                                <th>Nombre</th>
                                <th>H. Clínica</th>
                                <th>Edad</th>
                                <th>Diagnóstico</th>
                                <th>Edad gest.</th>
                                <th>G-P-C-A</th>
                                <th>Gr. sang.</th>
                                <th>Controles</th>
                                <th>Aseguradora</th>
                                <th>Acción</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        pacientes.forEach((paciente) => {
            const g_p_c_a = `${paciente.g ?? 0}-${paciente.p ?? 0}-${paciente.c ?? 0}-${paciente.a ?? 0}`;
            const identificador = paciente.num_identificacion || paciente.num_folio;
            const tipoIdentificador = paciente.num_identificacion ? 'cedula' : 'folio';
            const idEsc = esc(identificador);
            const diagEsc = esc(paciente.diagnostico || '');
            const diagDisplay = paciente.diagnostico ? paciente.diagnostico.trim() : '—';
            const edadGest = paciente.edad_gestacional ? paciente.edad_gestacional + ' sem' : '—';
            
            html += `
                <tr onclick="seleccionarPacienteDesdeLista('${idEsc}', '${tipoIdentificador}')">
                    <td>${esc(paciente.num_identificacion) || '—'}</td>
                    <td>${esc(paciente.num_folio) || '—'}</td>
                    <td>${esc(paciente.nombres_completos) || '—'}</td>
                    <td>${esc(paciente.num_historia_clinica) || '—'}</td>
                    <td>${paciente.edad != null ? esc(paciente.edad) : '—'}</td>
                    <td class="cell-diagnostico" title="${diagEsc}">${diagDisplay || '—'}</td>
                    <td>${edadGest}</td>
                    <td>${esc(g_p_c_a)}</td>
                    <td>${esc(paciente.grupo_sanguineo) || '—'}</td>
                    <td>${paciente.n_controles_prenatales != null ? esc(paciente.n_controles_prenatales) : '—'}</td>
                    <td class="cell-aseguradora" title="${esc(paciente.aseguradora || '')}">${esc(paciente.aseguradora) || '—'}</td>
                    <td>
                        <button type="button" class="resultados-pacientes-btn" onclick="event.stopPropagation(); seleccionarPacienteDesdeLista('${idEsc}', '${tipoIdentificador}')">Seleccionar</button>
                    </td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        resultadoDiv.innerHTML = html;
    }
    
    // Función para seleccionar un paciente de la lista y cargar sus datos
    window.seleccionarPacienteDesdeLista = async function(identificador, tipo = 'cedula') {
        if (!identificador) {
            mostrarMensaje('Identificador no válido', 'error');
            return;
        }
        
        // Llenar el campo de identificación si es cédula
        if (tipo === 'cedula') {
            const numIdentificacionInput = document.getElementById('num_identificacion');
            if (numIdentificacionInput) {
                numIdentificacionInput.value = identificador;
            }
        }
        
        // Buscar el paciente completo usando el endpoint existente
        try {
            let data;
            if (tipo === 'folio') {
                // Buscar por folio
                const url = `/pacientes/buscar-completo/?folio=${encodeURIComponent(identificador)}`;
                data = await apiRequest(url);
            } else {
                // Buscar por cédula
                data = await buscarPacienteCompleto(identificador);
            }
            
            if (data && data.paciente) {
                await llenarFormularioDesdePaciente(data);
                mostrarMensaje('Paciente seleccionado correctamente', 'success');
            } else {
                mostrarMensaje('No se pudo cargar la información completa del paciente', 'warning');
            }
        } catch (error) {
            console.error('Error al cargar paciente:', error);
            mostrarMensaje('Error al cargar información del paciente: ' + error.message, 'error');
        }
    }
    
    // Función para cargar mediciones guardadas en el grid
    // Ahora acepta datos directamente (medicionesData) para evitar petición HTTP adicional
    async function cargarMedicionesEnGrid(formularioId, medicionesData = null) {
        try {
            let mediciones;
            
            if (medicionesData) {
                // Usar datos proporcionados directamente (desde endpoint consolidado)
                console.log(`Cargando mediciones desde datos proporcionados para el formulario ${formularioId}...`);
                mediciones = medicionesData;
            } else {
                // Hacer petición HTTP (compatibilidad retroativa)
            console.log(`Cargando mediciones para el formulario ${formularioId}...`);
                mediciones = await apiRequest(`/formularios/${formularioId}/mediciones/`);
            }
            
            console.log('Mediciones recibidas:', mediciones);

            if (!mediciones || mediciones.length === 0) {
                console.log('No hay mediciones guardadas para este formulario.');
                return;
            }

            // 1. Identificar todas las horas únicas y ordenarlas
            const horasUnicas = [...new Set(mediciones.map(m => m.tomada_en))].sort();
            console.log('Horas detectadas:', horasUnicas);

            // 2. Llenar los inputs de tiempo (encabezado del grid)
            const timeInputs = document.querySelectorAll('.time-input');
            const horaToIndexMap = {};
            const columnasConDatos = new Set(); // Para rastrear qué columnas tienen datos

            horasUnicas.forEach((hora, index) => {
                if (index < timeInputs.length) {
                    // Convertir a formato local para datetime-local input (YYYY-MM-DDTHH:MM)
                    const date = new Date(hora);
                    const localISO = new Date(date.getTime() - (date.getTimezoneOffset() * 60000))
                                        .toISOString().slice(0, 16);
                    
                    timeInputs[index].value = localISO;
                    horaToIndexMap[hora] = index;
                }
            });

            // 3. Limpiar grid antes de cargar (opcional, pero recomendado)
            document.querySelectorAll('.data-input').forEach(input => input.value = '');

            // 4. Llenar los valores en las celdas y rastrear columnas con datos
            mediciones.forEach(medicion => {
                const horaIndex = horaToIndexMap[medicion.tomada_en];
                if (horaIndex === undefined) return; // Superó las 12 columnas

                // Usamos el ID del parámetro desde el objeto anidado (parametro.id)
                const parametroId = medicion.parametro ? medicion.parametro.id : null;
                if (!parametroId) return;

                medicion.valores.forEach(v => {
                    // Usamos el ID del campo desde el objeto anidado (v.campo.id)
                    const campoId = v.campo ? v.campo.id : null;
                    if (!campoId) return;

                    const selector = `.data-input[data-parametro-id="${parametroId}"][data-campo-id="${campoId}"][data-hora-index="${horaIndex}"]`;
                    const input = document.querySelector(selector);
                    
                    if (input) {
                        // Obtener el valor no nulo y formatearlo
                        // Priorizar valor_text sobre valor_number (para compatibilidad con datos antiguos)
                        let valor = '';
                        let valorAsignado = false;
                        
                        if (v.valor_text !== null && v.valor_text !== undefined) {
                            valor = v.valor_text;
                        } else if (v.valor_number !== null && v.valor_number !== undefined) {
                            // Compatibilidad con datos antiguos que puedan estar en valor_number
                            valor = parseFloat(v.valor_number);
                            if (Number.isInteger(valor)) valor = parseInt(valor);
                            valor = valor.toString();
                        } else if (v.valor_boolean !== null) {
                            // Para campos booleanos, convertir a texto
                            valor = v.valor_boolean ? 'SÍ' : 'NO';
                        } else if (v.valor_json !== null) {
                            valor = JSON.stringify(v.valor_json);
                        }
                        
                        // Si es un select, buscar la opción que coincida
                        if (input.tagName === 'SELECT' && valor !== '') {
                            const opciones = Array.from(input.options);
                            
                            // Para campos booleanos, buscar opción que comience con "Sí" o "No"
                            if (v.valor_boolean !== null) {
                                const opcionEncontrada = opciones.find(opt => {
                                    const texto = opt.value.toUpperCase();
                                    if (v.valor_boolean) {
                                        return texto.startsWith('SÍ') || texto.startsWith('SI');
                                    } else {
                                        return texto.startsWith('NO');
                                    }
                                });
                                if (opcionEncontrada) {
                                    input.value = opcionEncontrada.value;
                                    valorAsignado = true;
                                }
                            }
                            
                            // Si aún no se asignó, buscar coincidencia exacta
                            if (!valorAsignado) {
                                let opcionEncontrada = opciones.find(opt => opt.value === valor);
                                // Si no hay coincidencia exacta, buscar por coincidencia parcial
                                if (!opcionEncontrada) {
                                    opcionEncontrada = opciones.find(opt => 
                                        opt.value.includes(valor) || valor.includes(opt.value)
                                    );
                                }
                                if (opcionEncontrada) {
                                    input.value = opcionEncontrada.value;
                                    valorAsignado = true;
                                }
                            }
                            
                            // Si no se encuentra ninguna opción, asignar el valor directamente
                            if (!valorAsignado) {
                                input.value = valor;
                            }
                        } else {
                            // Para inputs normales, asignar el valor directamente
                            input.value = valor;
                        }
                        
                        // Si el valor no está vacío, marcar esta columna como con datos
                        if (valor !== '' && valor !== null && valor !== undefined) {
                            columnasConDatos.add(horaIndex);
                        }
                    }
                });
            });

            // 5. Bloquear todas las columnas que tienen al menos un dato
            columnasConDatos.forEach(horaIndex => {
                bloquearColumna(horaIndex, true);
                console.log(`Columna ${horaIndex} bloqueada (tiene datos)`);
            });

            // 6. Revelar columnas progresivas hasta la última con datos
            var maxHora = columnasConDatos.size ? Math.max.apply(null, Array.from(columnasConDatos)) : -1;
            if (typeof revealProgressiveHoursUpTo === 'function') revealProgressiveHoursUpTo(maxHora);

            console.log('Grid poblado con éxito. Columnas con datos bloqueadas:', Array.from(columnasConDatos));
        } catch (error) {
            console.error('Error al cargar mediciones en el grid:', error);
            mostrarMensaje('Error al cargar mediciones guardadas', 'error');
        }
    }
    
    // Función para generar HTML del PDF desde datos de caché
    async function generarHTMLPDFDesdeCache() {
        try {
            // Obtener datos de la caché
            const numIdentificacion = obtenerValorInput('num_identificacion');
            if (!numIdentificacion) {
                mostrarMensaje('No hay paciente seleccionado para generar PDF', 'error');
                return null;
            }
            
            const cacheData = obtenerPacienteCache(numIdentificacion);
            if (!cacheData || !cacheData.paciente) {
                console.log('No hay datos en caché, obteniendo desde API...');
                // Si no hay caché, obtener datos
                const data = await buscarPacienteCompleto(numIdentificacion, false);
                // Verificar si el paciente fue encontrado (nuevo formato sin errores 404)
                if (!data || data.encontrado === false || !data.paciente) {
                    const mensaje = data?.mensaje || 'No se encontraron datos del paciente';
                    mostrarMensaje(mensaje, 'error');
                    return null;
                }
                return data;
            }
            
            console.log('✅ Usando datos de caché para generar PDF');
            return cacheData;
        } catch (error) {
            console.error('Error al obtener datos para PDF:', error);
            mostrarMensaje('Error al obtener datos para PDF: ' + error.message, 'error');
            return null;
        }
    }
    
    // Función para formatear hora a formato 12 horas
    function formatearHora12h(fechaISO) {
        try {
            const date = new Date(fechaISO);
            let horas = date.getHours();
            const minutos = date.getMinutes();
            const ampm = horas >= 12 ? 'p. m.' : 'a. m.';
            horas = horas % 12;
            horas = horas ? horas : 12;
            return `${horas.toString().padStart(2, '0')}:${minutos.toString().padStart(2, '0')} ${ampm}`;
        } catch (e) {
            return fechaISO;
        }
    }
    
    // Función para formatear fecha
    function formatearFecha(fecha) {
        if (!fecha) return '—';
        try {
            const date = new Date(fecha);
            return date.toLocaleDateString('es-ES', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        } catch (e) {
            return fecha;
        }
    }
    
    // Función para construir grid_data desde mediciones
    function construirGridData(mediciones) {
        const gridData = {};
        
        if (!mediciones || mediciones.length === 0) {
            return gridData;
        }
        
        mediciones.forEach(medicion => {
            const parametroId = medicion.parametro ? medicion.parametro.id : null;
            if (!parametroId) return;
            
            // Usar ISO format para la hora
            const horaISO = medicion.tomada_en;
            
            if (!gridData[parametroId]) {
                gridData[parametroId] = {};
            }
            if (!gridData[parametroId][horaISO]) {
                gridData[parametroId][horaISO] = {};
            }
            
            // Procesar valores
            if (medicion.valores && medicion.valores.length > 0) {
                medicion.valores.forEach(v => {
                    const campoId = v.campo ? v.campo.id : null;
                    if (!campoId) return;
                    
                    let valor = '—';
                    
                    if (v.valor_text !== null && v.valor_text !== undefined) {
                        valor = v.valor_text;
                        // Convertir tiempo a formato 12 horas si es necesario
                        const parametroIdNum = parseInt(parametroId);
                        const campoIdNum = parseInt(campoId);
                        if ((parametroIdNum === 17 && campoIdNum === 19) || (parametroIdNum === 14 && campoIdNum === 18)) {
                            const horaMatch = valor.match(/^(\d{1,2}):(\d{2})$/);
                            if (horaMatch) {
                                let horas = parseInt(horaMatch[1]);
                                const minutos = horaMatch[2];
                                const ampm = horas >= 12 ? 'p. m.' : 'a. m.';
                                horas = horas % 12;
                                horas = horas ? horas : 12;
                                valor = `${horas.toString().padStart(2, '0')}:${minutos} ${ampm}`;
                            }
                        }
                    } else if (v.valor_number !== null && v.valor_number !== undefined) {
                        valor = parseFloat(v.valor_number);
                        if (Number.isInteger(valor)) valor = parseInt(valor);
                        valor = valor.toString();
                    } else if (v.valor_boolean !== null && v.valor_boolean !== undefined) {
                        valor = v.valor_boolean ? 'SÍ' : 'NO';
                        // Casos especiales para booleanos
                        if (parametroIdNum === 11 && campoIdNum === 14) {
                            valor = v.valor_boolean ? 'Sí - Bolsa amniótica íntegra' : 'No - Ya hubo ruptura';
                        } else if (parametroIdNum === 12 && campoIdNum === 15) {
                            valor = v.valor_boolean ? 'Sí – Espontánea o artificial' : 'No - Membranas aún íntegras';
                        }
                    } else if (v.valor_json !== null && v.valor_json !== undefined) {
                        valor = JSON.stringify(v.valor_json);
                    }
                    
                    gridData[parametroId][horaISO][campoId] = valor;
                });
            }
        });
        
        return gridData;
    }
    
    // Función para cargar el template HTML del PDF
    async function cargarTemplatePDF() {
        try {
            // Este proyecto actualmente no expone un template HTML de impresión
            // en el frontend estático. Para evitar 404 repetidos en consola,
            // sólo intentamos cargarlo si se define explícitamente una ruta.
            const appConfig = (typeof window !== 'undefined')
                ? (window.APP_CONFIG || window.AppConfig || null)
                : null;
            const rutaTemplateConfig =
                (appConfig && appConfig.PDF_TEMPLATE_PATH)
                    ? String(appConfig.PDF_TEMPLATE_PATH).trim()
                    : '';
            
            if (!rutaTemplateConfig) {
                return null;
            }
            
            const rutasPosibles = [rutaTemplateConfig];
            
            for (const ruta of rutasPosibles) {
                try {
                    const response = await fetch(ruta);
                    if (response.ok) {
                        const htmlTemplate = await response.text();
                        console.log(`✅ Template HTML cargado correctamente desde: ${ruta}`);
                        return htmlTemplate;
                    }
                } catch (e) {
                    // Continuar con la siguiente ruta
                    continue;
                }
            }
            
            throw new Error(`No se pudo cargar el template PDF configurado: ${rutaTemplateConfig}`);
        } catch (error) {
            console.error('Error al cargar template HTML:', error);
            // Si falla, retornar null para usar el método anterior
            return null;
        }
    }
    
    // Función para reemplazar placeholders en el template
    function reemplazarPlaceholders(template, replacements) {
        let html = template;
        for (const [key, value] of Object.entries(replacements)) {
            const regex = new RegExp(`{{${key}}}`, 'g');
            html = html.replace(regex, value || '—');
        }
        return html;
    }
    
    // Función para generar el grid de mediciones dinámicamente
    // Ahora incluye items y parámetros vacíos (sin mediciones)
    function generarGridMediciones(items, horasUnicas, gridData, mediciones) {
        let gridHTML = '';
        
        items.forEach(item => {
            // Incluir el item incluso si no tiene parámetros (mostrará vacío)
            if (!item.parametros || item.parametros.length === 0) {
                // Si el item no tiene parámetros, mostrar solo la fila del item
                gridHTML += `
                    <tr class="section-row">
                        <td colspan="11">${item.nombre || 'ITEM'}</td>
                    </tr>`;
            return;
        }

            gridHTML += `
                    <tr class="section-row">
                        <td colspan="11">${item.nombre || 'ITEM'}</td>
                    </tr>`;
            
            item.parametros.forEach(param => {
                // Obtener campos del parámetro desde las mediciones
                const camposMap = new Map();
                mediciones.forEach(m => {
                    if (m.parametro && m.parametro.id === param.id) {
                        if (m.valores) {
                            m.valores.forEach(v => {
                                if (v.campo && !camposMap.has(v.campo.id)) {
                                    camposMap.set(v.campo.id, v.campo);
                                }
                            });
                        }
                    }
                });
                
                // Si no hay campos en mediciones, obtenerlos del parámetro directamente (desde BD)
                if (camposMap.size === 0 && param.campos && param.campos.length > 0) {
                    param.campos.forEach(campo => {
                        camposMap.set(campo.id, campo);
                    });
                }
                
                const campos = Array.from(camposMap.values());
                
                gridHTML += `
                        <tr>
                            <td class="param-name">${param.nombre || 'PARÁMETRO'}</td>`;
                
                // Si hay horas únicas, mostrar valores para cada hora
                if (horasUnicas.length > 0) {
                    horasUnicas.forEach(horaISO => {
                        const paramData = gridData[param.id] || {};
                        const horaData = paramData[horaISO] || {};
                        
                        if (campos.length === 0) {
                            // Si no hay campos, mostrar celda vacía
                            gridHTML += `<td class="valor-celda">—</td>`;
                        } else {
                            // Mostrar valores de los campos
                            const valores = campos.map(campo => {
                                const valor = horaData[campo.id] || '—';
                                return `<div class="${campos.length > 1 ? 'multi-campo' : ''}">${valor}</div>`;
                            }).join('');
                            gridHTML += `<td class="valor-celda">${valores}</td>`;
                        }
                    });
                    
                    // Celdas vacías para completar las 10 columnas
                    const celdasVacias = 10 - horasUnicas.length;
                    for (let i = 0; i < celdasVacias; i++) {
                        gridHTML += '<td></td>';
                    }
                } else {
                    // Si no hay horas, mostrar 10 celdas vacías
                    for (let i = 0; i < 10; i++) {
                        gridHTML += '<td class="valor-celda">—</td>';
                    }
                }
                
                gridHTML += `
                        </tr>`;
            });
        });
        
        return gridHTML;
    }
    
    // Función para obtener todos los items y parámetros desde la base de datos
    async function obtenerTodosItemsParametros() {
        try {
            console.log('Obteniendo todos los items y parámetros desde la API...');
            
            // Obtener todos los items
            const itemsResponse = await apiRequest('/items/');
            const items = itemsResponse?.results || itemsResponse || [];
            
            console.log(`✅ Obtenidos ${items.length} items desde la API`);
            
            // Para cada item, obtener sus parámetros
            const itemsCompletos = await Promise.all(
                items.map(async (item) => {
                    try {
                        // Obtener parámetros del item
                        const parametrosResponse = await apiRequest(`/items/${item.id}/parametros/`);
                        const parametros = parametrosResponse?.results || parametrosResponse || [];
                        
                        // Para cada parámetro, obtener sus campos
                        const parametrosCompletos = await Promise.all(
                            parametros.map(async (param) => {
                                try {
                                    const camposResponse = await apiRequest(`/parametros/${param.id}/campos/`);
                                    const campos = camposResponse?.results || camposResponse || [];
                                    return {
                                        ...param,
                                        campos: campos
                                    };
                                } catch (error) {
                                    console.warn(`Error al obtener campos del parámetro ${param.id}:`, error);
                                    return {
                                        ...param,
                                        campos: []
                                    };
                                }
                            })
                        );
                        
                        return {
                            ...item,
                            parametros: parametrosCompletos
                        };
                    } catch (error) {
                        console.warn(`Error al obtener parámetros del item ${item.id}:`, error);
                        return {
                            ...item,
                            parametros: []
                        };
                    }
                })
            );
            
            console.log('✅ Items y parámetros completos obtenidos:', itemsCompletos);
            return itemsCompletos;
        } catch (error) {
            console.error('Error al obtener items y parámetros desde la API:', error);
            return [];
        }
    }
    
    // Función para generar HTML completo del PDF usando el template
    async function generarHTMLPDF(data) {
        if (!data || !data.paciente || !data.formulario) {
            mostrarMensaje('No hay formulario para imprimir', 'error');
            return null;
        }
        
        const paciente = data.paciente;
        const formulario = data.formulario;
        const mediciones = data.mediciones || [];

        // Convierte rutas relativas (/media/...) a URLs absolutas del backend (http://host:puerto)
        function normalizarURLMedia(url, versionToken = '') {
            if (!url || typeof url !== 'string') return '';
            if (url.startsWith('data:')) return url;

            const agregarVersion = (urlBase) => {
                if (!versionToken) return urlBase;
                const sep = urlBase.includes('?') ? '&' : '?';
                return `${urlBase}${sep}v=${encodeURIComponent(versionToken)}`;
            };

            if (/^(https?:)?\/\//i.test(url)) return agregarVersion(url);
            try {
                const cfg = window.APP_CONFIG || window.AppConfig || {};
                const apiBase = cfg.API_BASE_URL || '';
                const backendOrigin = apiBase ? new URL(apiBase).origin : window.location.origin;
                return agregarVersion(`${backendOrigin}${url.startsWith('/') ? '' : '/'}${url}`);
            } catch (e) {
                return agregarVersion(url);
            }
        }
        
        // Fetch biometrics
        let huellaUrl = '';
        let firmaUrl = '';
        if (paciente && paciente.id) {
            try {
                // Usar apiRequest en lugar de fetch directo para asegurar la URL del backend correcta
                const huellaData = await apiRequest(`/huella/${paciente.id}/`);
                // Compatibilidad con ambas respuestas: legacy y actual del backend
                if (huellaData && (huellaData.encontrado || huellaData.status === 'ok')) {
                    const versionToken = huellaData.fecha || Date.now();
                    huellaUrl = normalizarURLMedia(huellaData.imagen_huella || huellaData.imagen_url || '', versionToken);
                    firmaUrl = normalizarURLMedia(huellaData.imagen_firma || huellaData.firma_url || '', versionToken);
                }
            } catch (error) {
                console.error('Error fetching biometrics for PDF:', error);
            }
        }
        
        // Agregar biometrias a la respuesta para el fallback
        data.huella = huellaUrl;
        data.firma = firmaUrl;

        // Cargar el template HTML
        let htmlTemplate = await cargarTemplatePDF();
        
        // Si no se puede cargar el template, usar el método anterior (fallback)
        if (!htmlTemplate) {
            console.log('⚠️ No se pudo cargar el template, usando generación dinámica...');
            return await generarHTMLPDFFallback(data);
        }
        
        // Obtener TODOS los items y parámetros desde la base de datos
        const todosItems = await obtenerTodosItemsParametros();
        
        // Construir estructura de items y parámetros desde las mediciones (para tener datos)
        const itemsMapDesdeMediciones = new Map();
        
        mediciones.forEach(medicion => {
            if (!medicion.parametro || !medicion.parametro.item) return;
            
            const item = medicion.parametro.item;
            const parametro = medicion.parametro;
            
            if (!itemsMapDesdeMediciones.has(item.id)) {
                itemsMapDesdeMediciones.set(item.id, {
                    item: item,
                    parametros: new Map()
                });
            }
            
            const itemData = itemsMapDesdeMediciones.get(item.id);
            if (!itemData.parametros.has(parametro.id)) {
                itemData.parametros.set(parametro.id, parametro);
            }
        });
        
        // Combinar items de la base de datos con los de las mediciones
        // Priorizar los datos de las mediciones (tienen más información), pero incluir todos los items
        const itemsMapCompleto = new Map();
        
        // Primero agregar todos los items de la base de datos
        todosItems.forEach(itemDB => {
            itemsMapCompleto.set(itemDB.id, {
                item: itemDB,
                parametros: new Map()
            });
            
            // Agregar todos los parámetros del item desde la base de datos
            if (itemDB.parametros && itemDB.parametros.length > 0) {
                itemDB.parametros.forEach(param => {
                    const itemData = itemsMapCompleto.get(itemDB.id);
                    itemData.parametros.set(param.id, param);
                });
            }
        });
        
        // Luego, actualizar con los datos de las mediciones (si existen)
        itemsMapDesdeMediciones.forEach((itemDataMedicion, itemId) => {
            if (itemsMapCompleto.has(itemId)) {
                const itemDataCompleto = itemsMapCompleto.get(itemId);
                
                // Actualizar parámetros con datos de mediciones (tienen más info como campos)
                itemDataMedicion.parametros.forEach((paramMedicion, paramId) => {
                    itemDataCompleto.parametros.set(paramId, paramMedicion);
                });
            }
        });
        
        // Convertir Map a Array ordenado
        const items = Array.from(itemsMapCompleto.values())
            .map(itemData => ({
                id: itemData.item.id,
                nombre: itemData.item.nombre,
                codigo: itemData.item.codigo,
                parametros: Array.from(itemData.parametros.values())
                    .sort((a, b) => (a.orden || a.id || 0) - (b.orden || b.id || 0))
            }))
            .sort((a, b) => (a.id || 0) - (b.id || 0));
        
        console.log('Items completos (con vacíos):', items);
        
        // Construir grid_data desde mediciones
        const gridData = construirGridData(mediciones);
        
        // Obtener horas únicas y ordenarlas
        const horasUnicas = [...new Set(mediciones.map(m => m.tomada_en))].sort().slice(0, 10);
        
        // Preparar replacements para el template
        const replacements = {
            'CODIGO': formulario.codigo || '—',
            'VERSION': formulario.version || '—',
            'NUM_HOJA': formulario.num_hoja || 1,
            'FECHA_ELABORA': formatearFecha(formulario.fecha_elabora),
            'PACIENTE_NOMBRES': paciente.nombres || '—',
            'PACIENTE_TIPO_SANGRE': paciente.tipo_sangre_display || paciente.tipo_sangre || '—',
            'PACIENTE_NUM_IDENTIFICACION': paciente.num_identificacion || '—',
            'PACIENTE_NUM_HISTORIA_CLINICA': paciente.num_historia_clinica || '—',
            'FORMULARIO_ASEGURADORA': formulario.aseguradora ? (formulario.aseguradora.nombre || 'N/A') : 'N/A',
            'FORMULARIO_EDAD_SNAPSHOT': formulario.edad_snapshot ? `${formulario.edad_snapshot} años` : '—',
            'FORMULARIO_EDAD_GESTION': formulario.edad_gestion ? `${formulario.edad_gestion} semanas` : '—',
            'FORMULARIO_ESTADO': formulario.estado_display || formulario.estado || '—',
            'FORMULARIO_N_CONTROLES_PRENATALES': formulario.n_controles_prenatales || '—',
            'FORMULARIO_DIAGNOSTICO': formulario.diagnostico || '—',
            'FORMULARIO_RESPONSABLE': formulario.responsable || '—',
            'LOGO_HOSPITAL': '/static/img/logo_hospital.png',
            'LOGO_ACREDITACION': '/static/img/logo_acreditacion.png',
            'HUELLA_IMG': huellaUrl || '',
            'HUELLA_DISPLAY': huellaUrl ? 'inline-block' : 'none',
            'NO_HUELLA_DISPLAY': huellaUrl ? 'none' : 'block',
            'FIRMA_IMG': firmaUrl || '',
            'FIRMA_DISPLAY': firmaUrl ? 'inline-block' : 'none',
            'NO_FIRMA_DISPLAY': firmaUrl ? 'none' : 'block'
        };
        
        // Reemplazar placeholders básicos
        let html = reemplazarPlaceholders(htmlTemplate, replacements);
        
        // Generar y reemplazar el header de horas
        const horasHeaderHTML = horasUnicas.map(h => 
            `<th class="time-col">${formatearHora12h(h)}</th>`
        ).join('') + Array(10 - horasUnicas.length).fill(0).map(() => '<th class="time-col"></th>').join('');
        html = html.replace('<tr id="horas-header">', `<tr id="horas-header">${horasHeaderHTML}`);
        html = html.replace('<!-- Las horas se insertan dinámicamente aquí -->', '');
        
        // Generar y reemplazar el grid de mediciones
        const gridHTML = generarGridMediciones(items, horasUnicas, gridData, mediciones);
        html = html.replace('<tbody id="grid-body">', `<tbody id="grid-body">${gridHTML}`);
        html = html.replace('<!-- El grid se inserta dinámicamente aquí -->', '');
        
        return html;
    }
    
    // Función fallback: generar HTML dinámicamente (método anterior)
    async function generarHTMLPDFFallback(data) {
        if (!data || !data.paciente || !data.formulario) {
            return null;
        }
        
        const paciente = data.paciente;
        const formulario = data.formulario;
        const mediciones = data.mediciones || [];
        
        // Construir estructura de items y parámetros desde las mediciones
        const itemsMap = new Map();
        
        mediciones.forEach(medicion => {
            if (!medicion.parametro || !medicion.parametro.item) return;
            
            const item = medicion.parametro.item;
            const parametro = medicion.parametro;
            
            if (!itemsMap.has(item.id)) {
                itemsMap.set(item.id, {
                    item: item,
                    parametros: new Map()
                });
            }
            
            const itemData = itemsMap.get(item.id);
            if (!itemData.parametros.has(parametro.id)) {
                itemData.parametros.set(parametro.id, parametro);
            }
        });
        
        const items = Array.from(itemsMap.values())
            .map(itemData => ({
                id: itemData.item.id,
                nombre: itemData.item.nombre,
                codigo: itemData.item.codigo,
                parametros: Array.from(itemData.parametros.values())
            }))
            .sort((a, b) => (a.id || 0) - (b.id || 0));
        
        const gridData = construirGridData(mediciones);
        const horasUnicas = [...new Set(mediciones.map(m => m.tomada_en))].sort().slice(0, 10);
        
        // Construir HTML (método anterior)
        const html = `
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>IMPRESIÓN - ${formulario.codigo || 'FORMULARIO'}</title>
    <style>
        @page {
            size: A4 portrait;
            margin: 1cm;
        }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 9pt;
            color: #333;
            margin: 0;
            padding: 0;
        }
        .container {
            width: 100%;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 8px;
        }
        th, td {
            border: 1px solid #000;
            padding: 4px 6px;
        }
        .header-table td {
            padding: 10px;
        }
        .info-label {
            font-weight: bold;
            background-color: #f3f4f6;
            width: 15%;
            padding: 1px 4px !important;
            vertical-align: middle;
            font-size: 8pt;
            line-height: 1.2;
        }
        .info-value {
            width: 35%;
            padding: 1px 4px !important;
            vertical-align: middle;
            font-size: 8pt;
            line-height: 1.2;
        }
        .logo-cell {
            width: 150px;
            text-align: center;
        }
        .title-cell {
            text-align: center;
        }
        .title-cell h1 {
            margin: 0;
            font-size: 14pt;
            color: #444;
        }
        .meta-cell {
            width: 180px;
            font-size: 8pt;
        }
        .grid-table {
            table-layout: fixed;
        }
        .grid-table th {
            background-color: #3b82f6;
            color: white;
            font-size: 7pt;
            text-align: center;
        }
        .grid-table .time-col {
            width: 8.4%;
            font-size: 6pt;
        }
        .grid-table .item-col {
            width: 16%;
        }
        .section-row {
            background-color: #e5e7eb;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 7pt;
        }
        .param-name {
            font-weight: 500;
            font-size: 7pt;
        }
        .valor-celda {
            text-align: center;
            font-size: 7pt;
            height: 25px;
            vertical-align: middle;
        }
        .multi-campo {
            font-size: 6pt;
            border-bottom: 1px solid #eee;
        }
        .multi-campo:last-child {
            border-bottom: none;
        }
        @media print {
            .no-print {
                display: none;
            }
            body {
                -webkit-print-color-adjust: exact;
            }
        }
    </style>
</head>
<body onload="window.print(); setTimeout(() => window.close(), 500);">
    <div class="container">
        <!-- Encabezado Institucional -->
        <table class="header-table">
            <tr>
                <td class="logo-cell">
                    <!-- Logo placeholder -->
                </td>
                <td class="title-cell">
                    <h1>CONTROL DE TRABAJO DE PARTO</h1>
                </td>
                <td class="meta-cell">
                    <b>CÓDIGO:</b> ${formulario.codigo || '—'}<br>
                    <b>VERSIÓN:</b> ${formulario.version || '—'}<br>
                    <b>HOJA:</b> ${formulario.num_hoja || 1} DE 1<br>
                    <b>FECHA:</b> ${formatearFecha(formulario.fecha_elabora)}
                </td>
                <td class="accreditation-cell">
                    <!-- Logo acreditación placeholder -->
                </td>
            </tr>
        </table>

        <!-- Datos del Paciente -->
        <table>
            <tr>
                <td class="info-label">PACIENTE:</td>
                <td class="info-value">${paciente.nombres || '—'}</td>
                <td class="info-label">GRUPO SANGUÍNEO:</td>
                <td class="info-value">${paciente.tipo_sangre_display || paciente.tipo_sangre || '—'}</td>
            </tr>
            <tr>
                <td class="info-label">IDENTIFICACIÓN:</td>
                <td class="info-value">${paciente.num_identificacion || '—'}</td>
                <td class="info-label">H. CLÍNICA:</td>
                <td class="info-value">${paciente.num_historia_clinica || '—'}</td>
            </tr>
            <tr>
                <td class="info-label">ASEGURADORA:</td>
                <td class="info-value">${formulario.aseguradora ? (formulario.aseguradora.nombre || 'N/A') : 'N/A'}</td>
                <td class="info-label">EDAD:</td>
                <td class="info-value">${formulario.edad_snapshot || '—'} años</td>
            </tr>
            <tr>
                <td class="info-label">EDAD GESTACIONAL:</td>
                <td class="info-value">${formulario.edad_gestion || '—'} semanas</td>
                <td class="info-label">G_P_C_A_V_M:</td>
                <td class="info-value">${formulario.estado_display || formulario.estado || '—'}</td>
            </tr>
            <tr>
                <td class="info-label">N° CONTROLES PRENATALES:</td>
                <td class="info-value">${formulario.n_controles_prenatales || '—'}</td>
                <td class="info-label">DIAGNÓSTICO:</td>
                <td class="info-value">${formulario.diagnostico || '—'}</td>
            </tr>
        </table>

        <!-- Grid Principal -->
        <table class="grid-table">
            <thead>
                <tr>
                    <th class="item-col" rowspan="2">ÍTEM / PARÁMETRO</th>
                    <th colspan="10">HORA DE CONTROL</th>
                </tr>
                <tr>
                    ${horasUnicas.map(h => `<th class="time-col">${formatearHora12h(h)}</th>`).join('')}
                    ${Array(10 - horasUnicas.length).fill(0).map(() => '<th class="time-col"></th>').join('')}
                </tr>
            </thead>
            <tbody>
                ${items.map(item => {
                    if (!item.parametros || item.parametros.length === 0) return '';
                    
                    return `
                    <tr class="section-row">
                        <td colspan="11">${item.nombre || 'ITEM'}</td>
                    </tr>
                    ${item.parametros.map(param => {
                        // Obtener campos del parámetro desde las mediciones
                        const camposMap = new Map();
                        mediciones.forEach(m => {
                            if (m.parametro && m.parametro.id === param.id) {
                                if (m.valores) {
                                    m.valores.forEach(v => {
                                        if (v.campo && !camposMap.has(v.campo.id)) {
                                            camposMap.set(v.campo.id, v.campo);
                                        }
                                    });
                                }
                            }
                        });
                        
                        // Si no hay campos en mediciones, intentar obtenerlos del parámetro directamente
                        if (camposMap.size === 0 && param.campos) {
                            param.campos.forEach(campo => {
                                camposMap.set(campo.id, campo);
                            });
                        }
                        
                        const campos = Array.from(camposMap.values());
                        
                        return `
                        <tr>
                            <td class="param-name">${param.nombre || 'PARÁMETRO'}</td>
                            ${horasUnicas.map(horaISO => {
                                const paramData = gridData[param.id] || {};
                                const horaData = paramData[horaISO] || {};
                                
                                if (campos.length === 0) {
                                    return `<td class="valor-celda">—</td>`;
                                }
                                
                                const valores = campos.map(campo => {
                                    const valor = horaData[campo.id] || '—';
                                    return `<div class="${campos.length > 1 ? 'multi-campo' : ''}">${valor}</div>`;
                                }).join('');
                                
                                return `<td class="valor-celda">${valores}</td>`;
                            }).join('')}
                            ${Array(10 - horasUnicas.length).fill(0).map(() => '<td></td>').join('')}
                        </tr>
                        `;
                    }).join('')}
                    `;
                }).filter(html => html !== '').join('')}
            </tbody>
        </table>

        <!-- Responsable -->
        <table style="margin-top: 20px; border: none;">
            <tr>
                <td style="border: none;">
                    <b>RESPONSABLE:</b> ${formulario.responsable || '—'}
                </td>
            </tr>
        </table>
        
        <!-- Biometría -->
        <table style="margin-top: 30px; border: none; width: 100%;">
            <tr>
                <td style="border: none; width: 50%; text-align: center; vertical-align: bottom; height: 150px;">
                    <div style="min-height: 100px; margin-bottom: 10px;">
                        <img src="\${data.huella || ''}" alt="Huella" style="max-height: 100px; max-width: 150px; display: \${data.huella ? 'inline-block' : 'none'};">
                        <div style="display: \${data.huella ? 'none' : 'block'}; color: #999; font-style: italic; margin-top: 40px;">Sin huella registrada</div>
                    </div>
                    <div style="border-top: 1px solid #000; display: inline-block; width: 80%; padding-top: 5px;">
                        <b>HUELLA DACTILAR</b>
                    </div>
                    <div style="margin-top: 3px; font-size: 8pt;">\${paciente.nombres || '—'}</div>
                </td>
                <td style="border: none; width: 50%; text-align: center; vertical-align: bottom; height: 150px;">
                    <div style="min-height: 100px; margin-bottom: 10px;">
                        <img src="\${data.firma || ''}" alt="Firma" style="max-height: 100px; max-width: 250px; display: \${data.firma ? 'inline-block' : 'none'};">
                        <div style="display: \${data.firma ? 'none' : 'block'}; color: #999; font-style: italic; margin-top: 40px;">Sin firma registrada</div>
                    </div>
                    <div style="border-top: 1px solid #000; display: inline-block; width: 80%; padding-top: 5px;">
                        <b>FIRMA DEL PACIENTE</b>
                    </div>
                    <div style="margin-top: 3px; font-size: 8pt;">\${paciente.nombres || '—'}</div>
                </td>
            </tr>
            <tr>
                <td colspan="2" style="border: none; text-align: center; padding-top: 10px; font-size: 8pt; color: #666;">
                    Documento firmado biométricamente
                </td>
            </tr>
        </table>
    </div>
</body>
</html>
        `;
        
        return html;
    }

    /**
     * Descarga el PDF profesional generado por el backend.
     * @param {number} formularioId - ID opcional, si no se provee se busca en el DOM.
     */
    async function descargarPDF(formularioId = null) {
        console.log('🚀 Iniciando descarga de PDF (vía backend)...');
        
        // 1. Obtener ID del formulario
        if (!formularioId) {
            const el = document.getElementById('formulario_id');
            formularioId = el ? el.value : null;
        }
        
        if (!formularioId) {
            mostrarMensaje('Debe guardar el formulario antes de generar el PDF', 'warning');
            return;
        }

        try {
            // 2. Construir URL (prefijo /parto/ según urls.py global)
            const url = `/parto/formulario/${formularioId}/pdf/`;
            console.log(`📂 Abriendo reporte: ${url}`);
            
            // 3. Abrir en pestaña nueva (el navegador manejará la descarga/visualización)
            const win = window.open(url, '_blank');
            if (!win) {
                mostrarMensaje('Por favor habilite las ventanas emergentes', 'error');
            }
        } catch (error) {
            console.error('❌ Error al abrir PDF:', error);
            mostrarMensaje('Error al abrir el reporte profesional', 'error');
        }
    }

    // Exponer al ámbito global
    window.descargarPDF = descargarPDF;
});

// --- LÓGICA DE BIOMETRÍA Y FIRMA (GLOBAL) ---
let pollingHuellaInterval = null;
let signaturePad = null;

// Inicialización de Biometría al cargar el documento
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('signature-pad');
    if (canvas) {
        signaturePad = new SignaturePad(canvas, {
            backgroundColor: 'rgb(255, 255, 255)'
        });
        
        // Ajustar tamaño del canvas al abrir el modal o cambiar tamaño
        window.addEventListener('resize', resizeCanvas);
    }
});

function resizeCanvas() {
    const canvas = document.getElementById('signature-pad');
    if (!canvas) return;
    const ratio = Math.max(window.devicePixelRatio || 1, 1);
    canvas.width = canvas.offsetWidth * ratio;
    canvas.height = canvas.offsetHeight * ratio;
    canvas.getContext("2d").scale(ratio, ratio);
    if (signaturePad) signaturePad.clear(); // Limpiar al redimensionar para evitar artifacts
}

function abrirModalFirma() {
    const modal = document.getElementById('modalFirma');
    if (modal) {
        modal.style.display = 'flex';
        // Ajustar tamaño del canvas después de mostrar el modal (importante para offsetWidth)
        setTimeout(resizeCanvas, 100);
    }
}

function cerrarModalFirma() {
    const modal = document.getElementById('modalFirma');
    if (modal) modal.style.display = 'none';
}

function limpiarFirma() {
    if (signaturePad) signaturePad.clear();
}

async function guardarFirmaDigital() {
    const pacienteId = obtenerValorInput('paciente_id');
    const formularioId = obtenerValorInput('formulario_id');
    
    if (!pacienteId) {
        mostrarMensaje("Seleccione un paciente primero", "error");
        return;
    }

    if (!signaturePad || signaturePad.isEmpty()) {
        mostrarMensaje("Por favor, realice la firma antes de guardar", "error");
        return;
    }

    const firmaB64 = signaturePad.toDataURL(); // Obtiene PNG base64

    try {
        mostrarMensaje("Guardando firma...", "info");
        const baseUrl = API_BASE_URL;
        
        const data = {
            paciente_id: pacienteId,
            formulario_id: formularioId || null,
            firma: firmaB64,
            usuario: obtenerValorInput('responsable') || "Sistema"
        };

        const response = await fetch(`${baseUrl}/guardar-huella/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            mostrarMensaje("✅ Firma guardada con éxito", "success");
            cerrarModalFirma();
            // Disparar una actualización inmediata de la UI
            const resData = await response.json();
            // Forzamos un fetch de la última captura para actualizar la tarjeta
            const updateRes = await fetch(`${baseUrl}/huella/${pacienteId}/?_=${new Date().getTime()}`);
            if (updateRes.ok) {
                const updatedInfo = await updateRes.json();
                actualizarUIHuella(updatedInfo);
            }
        } else {
            throw new Error("Error al guardar en el servidor");
        }
    } catch (error) {
        console.error("Error al guardar firma:", error);
        mostrarMensaje("Error al guardar la firma: " + error.message, "error");
    }
}

function iniciarPollingHuella(pacienteId) {
    if (!pacienteId) return;
    
    console.log(`🔍 Iniciando polling de huella para paciente: ${pacienteId}`);
    
    if (pollingHuellaInterval) clearInterval(pollingHuellaInterval);
    
    const consultarHuellaUnaVez = async () => {
        try {
            const baseUrl = API_BASE_URL;
            const response = await fetch(`${baseUrl}/huella/${pacienteId}/?_=${new Date().getTime()}`);
            if (response.ok) {
                const data = await response.json();
                if (data && (data.imagen_huella || data.imagen_firma)) {
                    actualizarUIHuella(data);
                    // Si ya tenemos lo que buscábamos, paramos el polling
                    // Nota: Podríamos dejarlo si queremos capturar ambos, 
                    // pero usualmente se hace uno por uno.
                }
            }
        } catch (error) {
            console.error("Error en polling de huella:", error);
        }
    };

    // Primera consulta inmediata para evitar esperar el primer intervalo
    consultarHuellaUnaVez();
    pollingHuellaInterval = setInterval(consultarHuellaUnaVez, 3000);
}

function actualizarUIHuella(data) {
    if (!data) return;
    
    const imgHuella = document.getElementById('imgHuella');
    const imgFirma = document.getElementById('imgFirma');
    const estadoHuella = document.getElementById('estadoHuella');
    const estadoFirma = document.getElementById('estadoFirma');
    const btnVerHuella = document.getElementById('btnVerHuella');
    
    let baseUrl = API_BASE_URL.replace('/api', '');
    
    // Forzar refresco visual cuando backend devuelve misma ruta de archivo
    const versionToken = encodeURIComponent(data.fecha || Date.now());

    // Actualizar Huella
    if (imgHuella && data.imagen_huella) {
        const urlAbsoluta = data.imagen_huella.startsWith('http') ? data.imagen_huella : `${baseUrl}${data.imagen_huella}`;
        imgHuella.src = `${urlAbsoluta}${urlAbsoluta.includes('?') ? '&' : '?'}v=${versionToken}`;
        imgHuella.style.display = 'block';
        if (estadoHuella) estadoHuella.style.display = 'none';
        if (btnVerHuella) btnVerHuella.style.display = 'inline-block';
    } else if (imgHuella) {
        imgHuella.src = '';
        imgHuella.style.display = 'none';
        if (estadoHuella) {
            estadoHuella.innerHTML = 'No capturada';
            estadoHuella.style.display = 'block';
        }
        if (btnVerHuella) btnVerHuella.style.display = 'none';
    }

    // Actualizar Firma
    const previewFirmaImg = document.getElementById('preview-firma-img');
    const previewFirmaWrapper = document.getElementById('preview-firma-wrapper');
    const previewFirmaStatus = document.getElementById('preview-firma-status');

    if (imgFirma && data.imagen_firma) {
        const urlAbsolutaFirma = data.imagen_firma.startsWith('http') ? data.imagen_firma : `${baseUrl}${data.imagen_firma}`;
        imgFirma.src = `${urlAbsolutaFirma}${urlAbsolutaFirma.includes('?') ? '&' : '?'}v=${versionToken}`;
        imgFirma.style.display = 'block';
        if (estadoFirma) estadoFirma.style.display = 'none';
        
        // Sincronizar con Dashboard de Vista Previa
        if (previewFirmaStatus) {
            previewFirmaStatus.textContent = 'FIRMA: ✅';
            previewFirmaStatus.className = 'badge-tag badge-normal';
        }
        if (previewFirmaImg) {
            previewFirmaImg.src = `${urlAbsolutaFirma}${urlAbsolutaFirma.includes('?') ? '&' : '?'}v=${versionToken}`;
            if (previewFirmaWrapper) previewFirmaWrapper.style.display = 'block';
        }
    } else if (imgFirma) {
        imgFirma.src = '';
        imgFirma.style.display = 'none';
        if (estadoFirma) {
            estadoFirma.innerHTML = 'No capturada';
            estadoFirma.style.display = 'block';
        }

        if (previewFirmaStatus) {
            previewFirmaStatus.textContent = 'FIRMA: ❌';
            previewFirmaStatus.className = 'badge-tag badge-alert';
        }
        if (previewFirmaWrapper) previewFirmaWrapper.style.display = 'none';
    }

    // Sincronizar Huella con Dashboard de Vista Previa
    const previewHuellaStatus = document.getElementById('preview-huella-status');
    const previewHuellaImg = document.getElementById('preview-huella-img');
    const previewHuellaWrapper = document.getElementById('preview-huella-wrapper');

    if (previewHuellaStatus) {
        if (data.imagen_huella) {
            const urlAbsolutaHuella = data.imagen_huella.startsWith('http') ? data.imagen_huella : `${baseUrl}${data.imagen_huella}`;
            previewHuellaStatus.textContent = 'HUELLA: ✅';
            previewHuellaStatus.className = 'badge-tag badge-normal';
            if (previewHuellaImg) {
                previewHuellaImg.src = `${urlAbsolutaHuella}${urlAbsolutaHuella.includes('?') ? '&' : '?'}v=${versionToken}`;
                if (previewHuellaWrapper) previewHuellaWrapper.style.display = 'block';
            }
        } else {
            previewHuellaStatus.textContent = 'HUELLA: ❌';
            previewHuellaStatus.className = 'badge-tag badge-alert';
            if (previewHuellaWrapper) previewHuellaWrapper.style.display = 'none';
        }
    }
}

function abrirDetalleHuella() {
    const pacienteId = obtenerValorInput('paciente_id');
    if (!pacienteId) {
        mostrarMensaje("Seleccione un paciente primero", "error");
        return;
    }
    const baseUrlFrontend = window.location.origin;
    const url = `${baseUrlFrontend}/parto/huella/ver/${encodeURIComponent(pacienteId)}`;
    window.open(url, 'DetalleHuella', 'width=600,height=800,scrollbars=yes');
}

async function refrescarBiometriaAhora() {
    const pacienteId = obtenerValorInput('paciente_id');
    if (!pacienteId) {
        mostrarMensaje("Seleccione un paciente primero", "warning");
        return;
    }

    try {
        mostrarMensaje("Actualizando biometría...", "info");
        const baseUrl = API_BASE_URL;
        const response = await fetch(`${baseUrl}/huella/${pacienteId}/?_=${new Date().getTime()}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        actualizarUIHuella(data);

        if (data && (data.imagen_huella || data.imagen_firma)) {
            mostrarMensaje("✅ Biometría actualizada", "success");
        } else {
            mostrarMensaje("No hay nueva biometría para este paciente", "info");
        }
    } catch (error) {
        console.error("Error al refrescar biometría:", error);
        mostrarMensaje("Error al refrescar biometría", "error");
    }
}

async function activarCapturaTablet(tipo) {
    let pacienteId = obtenerValorInput('paciente_id');
    const formularioId = obtenerValorInput('formulario_id') || "";
    
    // Si no hay ID de paciente, intentar guardar el paciente primero (para pacientes nuevos)
    if (!pacienteId) {
        console.log("📝 Paciente nuevo detectado, intentando guardar antes de captura...");
        try {
            // Intentar guardar el paciente (esto validará nombres, identificación, etc.)
            const paciente = await guardarPaciente();
            if (paciente && paciente.id) {
                pacienteId = paciente.id;
                console.log("✅ Paciente guardado exitosamente con ID:", pacienteId);
            } else {
                console.error("❌ No se pudo obtener el ID del paciente tras guardar");
                return; // guardarPaciente ya muestra los mensajes de error
            }
        } catch (error) {
            console.error("❌ Error al guardar paciente previo a captura:", error);
            mostrarMensaje(error.message || "Guarde los datos del paciente primero.", "warning");
            return;
        }
    }

    if (tipo === 'huella') {
        mostrarMensaje("Iniciando captura de huella en la tablet...", "info");
        const estadoHuella = document.getElementById('estadoHuella');
        if (estadoHuella) {
            estadoHuella.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"></div> Esperando huella...';
        }
        
        // Disparar Intent corregido para la App de Veneve/Fingerprint
        const intentUrl = `fingerprint://capture?paciente_id=${pacienteId}&formulario_id=${formularioId}`;
        console.log("🚀 Disparando captura de huella:", intentUrl);
        
        // Intentar abrir el deep link
        setTimeout(() => {
            window.location.href = intentUrl;
        }, 100);
        
        iniciarPollingHuella(pacienteId);
    } else if (tipo === 'firma') {
        setTimeout(abrirModalFirma, 100);
    }
}

// Globalizar
window.activarCapturaTablet = activarCapturaTablet;
window.abrirDetalleHuella = abrirDetalleHuella;
window.refrescarBiometriaAhora = refrescarBiometriaAhora;
window.iniciarPollingHuella = iniciarPollingHuella;
window.cerrarModalFirma = cerrarModalFirma;
window.limpiarFirma = limpiarFirma;
window.guardarFirmaDigital = guardarFirmaDigital;

