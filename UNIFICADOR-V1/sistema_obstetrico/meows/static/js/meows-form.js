/**
 * MEOWS Form - Validación y Cálculo en Tiempo Real
 * Calcula scores, sumatoria y riesgo automáticamente mientras el usuario ingresa valores
 * Conectado al backend Django para obtener rangos desde la base de datos
 */

// Rangos MEOWS - se cargan desde el backend
let MEOWS_RANGOS = {};
let activosRefreshInterval = null;
let busquedaPacienteController = null;
let busquedaPacienteEnCurso = false;
let ultimoDocumentoBuscado = '';
let busquedaPacienteRequestId = 0;
const cacheBusquedaPacientes = new Map();
const CACHE_BUSQUEDA_MS = 30000;

function getMeowsUrl(key, fallback = '') {
    const urls = window.MEOWS_URLS || {};
    return urls[key] || fallback;
}

function getApiGuardarBiometriaUrl() {
    const explicit = getMeowsUrl('apiGuardarHuella', '');
    if (explicit) return explicit;
    const buscar = getMeowsUrl('apiBuscarPaciente', '/fetal/meows/api/buscar-paciente/');
    if (buscar.includes('/api/buscar-paciente/')) {
        return buscar.replace('/api/buscar-paciente/', '/api/save-biometrics/');
    }
    return '/fetal/meows/api/save-biometrics/';
}

function buildUrlFromTemplate(template, value, placeholder = '__PACIENTE_ID__') {
    if (!template) return '';
    const valor = encodeURIComponent(String(value ?? '').trim());
    if (!valor) return template;
    if (template.includes(placeholder)) {
        return template.replace(placeholder, valor);
    }
    // Plantillas construidas con ID 0 (rutas int)
    return template.replace('/0/', `/${valor}/`);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (const cookieRaw of cookies) {
            const cookie = cookieRaw.trim();
            if (cookie.startsWith(`${name}=`)) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Control de alertas sonoras - evita repetir el sonido para la misma alerta
let alertasNotificadas = new Set();
let riesgoAnterior = null;

// Rangos fallback (por si falla la carga desde el backend)
const MEOWS_RANGOS_FALLBACK = {
    'fc': [
        { min: 0, max: 49, score: 3 },
        { min: 50, max: 59, score: 3 },
        { min: 60, max: 109, score: 0 },
        { min: 110, max: 150, score: 2 },
        { min: 151, max: 999, score: 3 }
    ],
    'ta_sys': [
        { min: 0, max: 89, score: 3 },
        { min: 90, max: 99, score: 2 },
        { min: 100, max: 139, score: 0 },
        { min: 140, max: 149, score: 1 },
        { min: 150, max: 159, score: 2 },
        { min: 160, max: 999, score: 3 }
    ],
    'ta_dia': [
        { min: 0, max: 59, score: 0 },
        { min: 60, max: 89, score: 0 },
        { min: 90, max: 99, score: 1 },
        { min: 100, max: 109, score: 2 },
        { min: 110, max: 120, score: 3 },
        { min: 121, max: 999, score: 3 }
    ],
    'fr': [
        { min: 0, max: 4, score: 3 },
        { min: 5, max: 9, score: 3 },
        { min: 10, max: 17, score: 0 },
        { min: 18, max: 24, score: 1 },
        { min: 25, max: 29, score: 2 },
        { min: 30, max: 999, score: 3 }
    ],
    'temp': [
        { min: 0, max: 33.9, score: 3 },
        { min: 34.0, max: 34.9, score: 3 },
        { min: 35.0, max: 35.9, score: 1 },
        { min: 36.0, max: 37.4, score: 0 },
        { min: 37.5, max: 38.9, score: 1 },
        { min: 39.0, max: 39.9, score: 3 },
        { min: 40.0, max: 999, score: 3 }
    ],
    'spo2': [
        { min: 0, max: 89, score: 3 },
        { min: 90, max: 92, score: 2 },
        { min: 93, max: 94, score: 1 },
        { min: 95, max: 100, score: 0 }
    ],
    'glasgow': [
        { min: 0, max: 14, score: 3 },
        { min: 15, max: 15, score: 0 }
    ],
    'fcf': [
        { min: 0, max: 119, score: 0 },
        { min: 120, max: 129, score: 0 },
        { min: 130, max: 139, score: 0 },
        { min: 140, max: 160, score: 0 },
        { min: 161, max: 999, score: 0 }
    ]
};

// Mensajes de conducta por riesgo
const CONDUCTAS = {
    'BLANCO': 'RUTINA:  OBSERVACION -Minimo 12 horas de Observacion',
    'VERDE': 'RIESGO BAJO OBSERVACION: mínimo cada 4 horas. LLAMADO: Enfermera a cargo',
    'AMARILLO': 'RIESGO INTERMEDIO: OBSERVACION -Minnimo cada hora LLAMADO: Urgente al equipo medico al de la paciente con las competencias para manejo de la emergencia obstetrica',
    'ROJO': 'RIESGO ALTO: OBSERVACION Monitoreo continuo de signos vitales LLAMADO :Emergente al equipo con conpetencias en estado critico y habilidades para el diagnostico'
};

/**
 * Carga los rangos MEOWS desde el backend Django
 */
async function cargarRangosDesdeBackend() {
    try {
        const response = await fetch(getMeowsUrl('apiRangos', '/api/rangos/'));
        if (response.ok) {
            const rangos = await response.json();
            MEOWS_RANGOS = rangos;
            console.log('✅ Rangos MEOWS cargados desde el backend:', Object.keys(rangos).length, 'parámetros');
            return true;
        } else {
            console.warn('⚠️ No se pudieron cargar rangos desde el backend, usando fallback');
            MEOWS_RANGOS = MEOWS_RANGOS_FALLBACK;
            return false;
        }
    } catch (error) {
        console.error('❌ Error al cargar rangos desde el backend:', error);
        console.warn('⚠️ Usando rangos fallback');
        MEOWS_RANGOS = MEOWS_RANGOS_FALLBACK;
        return false;
    }
}

/**
 * Calcula el score MEOWS para un parámetro y valor dado
 */
function calcularScore(parametro, valor) {
    if (!valor || valor === '') return null;

    const valorNum = parseFloat(valor);
    if (isNaN(valorNum)) return null;

    // Validación especial para temperatura: valores fuera de 34-40 no tienen score
    if (parametro === 'temp') {
        if (valorNum < 34 || valorNum > 40) {
            return null; // Retorna null para indicar que está fuera de rango válido
        }
    }

    // Validación especial para frecuencia cardíaca
    if (parametro === 'fc') {
        // Valores fuera de 40-170 no tienen score
        if (valorNum < 40 || valorNum > 170) {
            return null; // Retorna null para indicar que está fuera de rango válido
        }
        // Valores mayores a 150 tienen score rojo (3)
        if (valorNum > 150) {
            return 3;
        }
    }

    // Validación especial para frecuencia cardíaca fetal: valores fuera de 110-190 no tienen score
    if (parametro === 'fcf') {
        if (valorNum < 110 || valorNum > 190) {
            return null; // Retorna null para indicar que está fuera de rango válido
        }
    }

    const rangos = MEOWS_RANGOS[parametro];
    if (!rangos) return null;

    for (const rango of rangos) {
        if (valorNum >= rango.min && valorNum <= rango.max) {
            return rango.score;
        }
    }

    return null;
}

/**
 * Calcula score consultando la API y usa fallback local
 * si hay error de red o respuesta inválida.
 */
async function calcularScoreDesdeApi(parametro, valor) {
    if (!valor || valor === '') return null;

    const urlApi = getMeowsUrl('apiCalcularScore', '/api/calcular-score/');
    try {
        const response = await fetch(urlApi, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            },
            body: JSON.stringify({
                parametro: parametro,
                valor: valor
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        if (data && data.success) {
            return data.score;
        }
    } catch (error) {
        console.warn('⚠️ Falló cálculo por API, usando cálculo local:', error);
    }

    return calcularScore(parametro, valor);
}

/**
 * Actualiza el feedback visual de un parámetro
 */
function actualizarFeedback(parametro, valor, score) {
    const input = document.getElementById(parametro);
    const scoreElement = document.getElementById(`score-${parametro}`);
    const fillElement = document.getElementById(`fill-${parametro}`);
    const messageElement = document.getElementById(`message-${parametro}`);
    const card = input.closest('.parameter-card');

    // Limpiar clases anteriores
    input.classList.remove('score-0', 'score-1', 'score-2', 'score-3');
    scoreElement.classList.remove('score-0', 'score-1', 'score-2', 'score-3');
    fillElement.classList.remove('score-0', 'score-1', 'score-2', 'score-3');
    messageElement.classList.remove('error', 'success', 'warning', 'success-green', 'error-purple');
    if (card) {
        card.classList.remove('card-score-0', 'card-score-1', 'card-score-2', 'card-score-3');
    }
    messageElement.textContent = '';

    if (score === null) {
        if (valor && valor !== '') {
            // Validación especial para temperatura
            if (parametro === 'temp') {
                const valorNum = parseFloat(valor);
                if (!isNaN(valorNum)) {
                    if (valorNum < 34 || valorNum > 40) {
                        messageElement.textContent = 'Dato fuera de rango';
                        messageElement.classList.add('error', 'error-purple');
                        return;
                    }
                }
            }
            // Para otros parámetros, mensaje genérico
            messageElement.textContent = 'Valor fuera de rango';
            messageElement.classList.add('error');
        }
        return;
    }

    // Aplicar clases de score
    input.classList.add(`score-${score}`);
    scoreElement.textContent = score;
    scoreElement.classList.add(`score-${score}`);
    fillElement.classList.add(`score-${score}`);
    if (card) {
        card.classList.add(`card-score-${score}`);
    }

    // Mensaje según score
    if (score === 0) {
        messageElement.textContent = '✓ Normal';
        messageElement.classList.add('success');
    } else if (score === 1) {
        messageElement.textContent = '⚠ Moderado';
        messageElement.classList.add('success-green');
    } else if (score === 2) {
        messageElement.textContent = '⚠⚠ Moderado-Alto';
        messageElement.classList.add('warning');
    } else if (score === 3) {
        messageElement.textContent = '🚨 CRÍTICO';
        messageElement.classList.add('error');
    }
}

/**
 * Reproduce el sonido de alerta suave si corresponde
 * Solo reproduce cuando:
 * - El riesgo es ALTO (ROJO)
 * - Es una nueva alerta (no se ha notificado antes)
 * - El riesgo cambió de otro nivel a ROJO
 */
function reproducirSonidoSiCorresponde(riesgoActual, riesgoAnterior) {
    // Crear un ID único para esta combinación de riesgo
    const alertaId = `riesgo-${riesgoActual}-${Date.now()}`;

    // Solo reproducir si:
    // 1. El riesgo actual es ROJO (RIESGO ALTO)
    // 2. No es el mismo riesgo que el anterior (es una nueva alerta)
    // 3. No se ha notificado antes (prevención adicional)
    if (riesgoActual === 'ROJO' && riesgoActual !== riesgoAnterior && !alertasNotificadas.has(alertaId)) {
        const alertSound = document.getElementById('alertSound');
        if (alertSound) {
            // Intentar reproducir el sonido
            alertSound.play().catch(error => {
                // Si falla la reproducción (por políticas del navegador), solo loguear
                console.warn('No se pudo reproducir la alerta sonora:', error);
            });

            // Marcar esta alerta como notificada
            alertasNotificadas.add(alertaId);

            // Limpiar alertas antiguas del Set para evitar acumulación (mantener solo las últimas 10)
            if (alertasNotificadas.size > 10) {
                const firstKey = alertasNotificadas.values().next().value;
                alertasNotificadas.delete(firstKey);
            }

            console.log('🔊 Alerta sonora activada: RIESGO ALTO detectado');
        }
    }
}

/**
 * Calcula y actualiza el resumen total
 */
function actualizarResumen() {
    const inputs = document.querySelectorAll('.parameter-input');
    let total = 0;
    const scores = {};

    inputs.forEach(input => {
        const parametro = input.dataset.param;
        const valor = input.value;
        const score = calcularScore(parametro, valor);

        if (score !== null) {
            scores[parametro] = score;
            total += score;
        }
    });

    // Actualizar total
    const totalElement = document.getElementById('total-score');
    totalElement.textContent = total;

    // Obtener el contenedor summary-item padre
    const summaryItem = totalElement.closest('.summary-item');

    // Remover clases de color anteriores del elemento y del contenedor
    totalElement.classList.remove('score-verde', 'score-amarillo', 'score-rojo', 'score-blanco');
    if (summaryItem) {
        summaryItem.classList.remove('item-score-verde', 'item-score-amarillo', 'item-score-rojo', 'item-score-blanco');
    }

    // Calcular riesgo y aplicar color al puntaje según las nuevas reglas:
    // - RIESGO BAJO (VERDE): total 1 a 3
    // - RIESGO INTERMEDIO (AMARILLO): tiene parámetro con score 3 O total >= 4
    // - RIESGO ALTO (ROJO): total >= 6
    let riesgo = 'VERDE';

    // Verificar si hay algún parámetro con score 3
    const tieneScore3 = Object.values(scores).some(score => score === 3);

    if (total === 0) {
        riesgo = 'BLANCO';
        totalElement.classList.add('score-blanco');
        if (summaryItem) summaryItem.classList.add('item-score-blanco');
    } else if (total >= 6) {
        riesgo = 'ROJO';
        totalElement.classList.add('score-rojo');
        if (summaryItem) summaryItem.classList.add('item-score-rojo');
    } else if (tieneScore3 || total >= 4) {
        riesgo = 'AMARILLO';
        totalElement.classList.add('score-amarillo');
        if (summaryItem) summaryItem.classList.add('item-score-amarillo');
    } else if (total >= 1 && total <= 3) {
        riesgo = 'VERDE';
        totalElement.classList.add('score-verde');
        if (summaryItem) summaryItem.classList.add('item-score-verde');
    } else {
        // Por defecto VERDE (no debería llegar aquí)
        riesgo = 'VERDE';
        totalElement.classList.add('score-verde');
        if (summaryItem) summaryItem.classList.add('item-score-verde');
    }

    // Reproducir sonido si corresponde (antes de actualizar el riesgo anterior)
    reproducirSonidoSiCorresponde(riesgo, riesgoAnterior);

    // Actualizar el riesgo anterior para la próxima comparación
    riesgoAnterior = riesgo;

    // Actualizar badge de riesgo
    const riskElement = document.getElementById('risk-level');
    riskElement.innerHTML = `<span class="risk-badge risk-${riesgo.toLowerCase()}">${riesgo}</span>`;

    // Actualizar conducta
    const conductaElement = document.getElementById('conducta-text');
    conductaElement.textContent = CONDUCTAS[riesgo];

    // Obtener el summary-item que contiene la conducta y aplicar la clase de color
    const conductaSummaryItem = conductaElement.closest('.summary-item');
    if (conductaSummaryItem) {
        // Remover clases anteriores
        conductaSummaryItem.classList.remove('item-score-verde', 'item-score-amarillo', 'item-score-rojo', 'item-score-blanco');
        // Aplicar la clase correspondiente al riesgo
        if (riesgo === 'BLANCO') {
            conductaSummaryItem.classList.add('item-score-blanco');
        } else if (riesgo === 'VERDE') {
            conductaSummaryItem.classList.add('item-score-verde');
        } else if (riesgo === 'AMARILLO') {
            conductaSummaryItem.classList.add('item-score-amarillo');
        } else if (riesgo === 'ROJO') {
            conductaSummaryItem.classList.add('item-score-rojo');
        }
    }
}

/**
 * Sincroniza los campos del paciente con los campos ocultos del formulario MEOWS
 */
function sincronizarCamposPaciente() {
    /* Demografía MEOWS va en inputs hidden (misma id que name); no hay espejo visible. */
}

/**
 * Muestra un mensaje de búsqueda de paciente como notificación profesional
 */
function mostrarMensajeBusqueda(mensaje, tipo = 'success') {
    // Eliminar mensaje anterior si existe
    const mensajeAnterior = document.getElementById('mensaje-busqueda-paciente');
    if (mensajeAnterior) {
        mensajeAnterior.style.opacity = '0';
        mensajeAnterior.style.transform = 'translateY(-20px) scale(0.95)';
        setTimeout(() => mensajeAnterior.remove(), 300);
    }

    // Crear contenedor de mensaje
    const mensajeDiv = document.createElement('div');
    mensajeDiv.id = 'mensaje-busqueda-paciente';
    mensajeDiv.className = `mensaje-busqueda mensaje-busqueda-${tipo}`;

    // Crear icono
    const iconoDiv = document.createElement('div');
    iconoDiv.className = 'mensaje-busqueda-icono';

    let iconoTexto = '✓';
    if (tipo === 'error') {
        iconoTexto = '⚠';
    } else if (tipo === 'info') {
        iconoTexto = '🔍';
    }

    iconoDiv.textContent = iconoTexto;

    // Crear contenido del mensaje
    const contenidoDiv = document.createElement('div');
    contenidoDiv.className = 'mensaje-busqueda-contenido';

    const textoMensaje = document.createElement('span');
    textoMensaje.className = 'mensaje-busqueda-texto';
    textoMensaje.textContent = mensaje;

    contenidoDiv.appendChild(textoMensaje);

    // Botón de cerrar
    const btnCerrar = document.createElement('button');
    btnCerrar.className = 'mensaje-busqueda-cerrar';
    btnCerrar.innerHTML = '×';
    btnCerrar.setAttribute('aria-label', 'Cerrar notificación');
    btnCerrar.addEventListener('click', () => {
        mensajeDiv.style.opacity = '0';
        mensajeDiv.style.transform = 'translateY(-20px) scale(0.95)';
        setTimeout(() => {
            if (mensajeDiv.parentElement) {
                mensajeDiv.remove();
            }
        }, 300);
    });

    // Ensamblar elementos
    mensajeDiv.appendChild(iconoDiv);
    mensajeDiv.appendChild(contenidoDiv);
    mensajeDiv.appendChild(btnCerrar);

    // Insertar después del toolbar de paciente / búsqueda
    const searchWrapper =
        document.querySelector('.patient-module-toolbar') || document.querySelector('.search-patient-wrapper');
    if (searchWrapper && searchWrapper.parentElement) {
        searchWrapper.parentElement.insertBefore(mensajeDiv, searchWrapper.nextSibling);

        // Auto-ocultar después de 8 segundos
        setTimeout(() => {
            if (mensajeDiv.parentElement) {
                mensajeDiv.style.opacity = '0';
                mensajeDiv.style.transform = 'translateY(-20px) scale(0.95)';
                setTimeout(() => {
                    if (mensajeDiv.parentElement) {
                        mensajeDiv.remove();
                    }
                }, 300);
            }
        }, 8000);
    }
}

/**
 * Actualiza el href del botón "Ver Historial" con el ID del paciente
 */
function actualizarBotonHistorial(pacienteId) {
    const btnHistorial = document.getElementById('btn-ver-historial') || document.querySelector('a.btn-info[href*="historial"]');
    if (btnHistorial && pacienteId) {
        const historialTemplate = getMeowsUrl('historialTemplate', '/historial/0/');
        btnHistorial.href = buildUrlFromTemplate(historialTemplate, pacienteId);
        // Hacer el botón visible/enable si estaba deshabilitado
        btnHistorial.style.display = 'inline-flex';
    }
}

/**
 * Limpia todos los campos del formulario de paciente
 */
function limpiarCamposPaciente() {
    const nombreCompletoInput = document.getElementById('nombre_completo');
    const numeroDocInput = document.getElementById('numero_documento');
    const fechaNacInput = document.getElementById('fecha_nacimiento');
    const edadInput = document.getElementById('edad');
    const aseguradoraSelect = document.getElementById('aseguradora');
    const camaInput = document.getElementById('cama');
    const fechaIngresoInput = document.getElementById('fecha_ingreso');
    const responsableInput = document.getElementById('responsable');

    if (nombreCompletoInput) nombreCompletoInput.value = '';
    if (numeroDocInput) numeroDocInput.value = '';
    if (fechaNacInput) fechaNacInput.value = '';
    if (edadInput) edadInput.value = '';
    if (aseguradoraSelect) aseguradoraSelect.value = '';
    if (camaInput) camaInput.value = '';
    if (fechaIngresoInput) fechaIngresoInput.value = '';
    if (responsableInput) responsableInput.value = '';
    
    // Limpiar nombre en firma
    const nombreFirmaSpan = document.getElementById('nombre-firma-paciente');
    if (nombreFirmaSpan) nombreFirmaSpan.textContent = '—';

    // Limpiar biometría
    const huellaContainer = document.getElementById("huella-container");
    const firmaContainer = document.getElementById("firma-container-preview");
    const firmaImg = document.getElementById("imgFirma");
    const estadoFirma = document.getElementById("estadoFirma");

    if (huellaContainer) huellaContainer.style.display = "none";
    if (firmaContainer) firmaContainer.style.display = "none";
    if (firmaImg) firmaImg.src = '';
    if (estadoFirma) estadoFirma.textContent = 'Sin firmar';

    // Limpiar campos ocultos también
    sincronizarCamposPaciente();
}

function actualizarVistaFirmaPaciente(imagenFirmaUrl, estadoTexto = "Firma registrada") {
    const firmaImg = document.getElementById("imgFirma");
    const firmaContainer = document.getElementById("firma-container-preview");
    const firmaEstado = document.getElementById("estadoFirma");

    if (!imagenFirmaUrl) {
        if (firmaContainer) firmaContainer.style.display = "none";
        if (firmaEstado) {
            firmaEstado.textContent = "Sin firmar";
            firmaEstado.style.color = "";
            firmaEstado.style.background = "";
        }
        return;
    }

    const timestampedUrl = `${imagenFirmaUrl}?t=${Date.now()}`;
    if (firmaImg) {
        firmaImg.src = timestampedUrl;
        firmaImg.style.setProperty('display', 'block', 'important');
    }
    if (firmaContainer) {
        firmaContainer.style.setProperty('display', 'flex', 'important');
        firmaContainer.classList.add('is-visible');
    }
    if (firmaEstado) {
        firmaEstado.textContent = estadoTexto;
        firmaEstado.style.color = "#27ae60";
        firmaEstado.style.background = "#e8f5e9";
    }

}

async function refrescarFirmaPaciente(documento, opts = {}) {
    const { silencioso = true, estado = "Firma registrada" } = opts;
    const pacienteDoc = (documento || '').trim();
    if (!pacienteDoc) return false;

    const btnRefrescar = document.getElementById('btn-refrescar-firma');
    const originalText = btnRefrescar ? btnRefrescar.innerHTML : '';
    if (btnRefrescar) {
        btnRefrescar.disabled = true;
        btnRefrescar.innerHTML = '<span class="btn-icon">⏳</span>Actualizando...';
    }

    try {
        // No dependemos del endpoint de huella: obtenemos solo la firma desde búsqueda de paciente.
        const apiBuscar = getMeowsUrl('apiBuscarPaciente', '/api/buscar-paciente/');
        const response = await fetch(`${apiBuscar}?documento=${encodeURIComponent(pacienteDoc)}&t=${Date.now()}`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            credentials: 'same-origin',
        });

        if (!response.ok) {
            actualizarVistaFirmaPaciente(null);
            if (!silencioso) alert("No hay firma guardada para este paciente.");
            return false;
        }

        const data = await response.json();
        const firmaUrl = data?.paciente?.biometria?.imagen_firma || null;
        if (data.success && firmaUrl) {
            actualizarVistaFirmaPaciente(firmaUrl, estado);
            return true;
        }

        actualizarVistaFirmaPaciente(null);
        if (!silencioso) alert("No hay firma guardada para este paciente.");
        return false;
    } catch (error) {
        if (!silencioso) alert("No fue posible refrescar la firma. Intente nuevamente.");
        return false;
    } finally {
        if (btnRefrescar) {
            btnRefrescar.disabled = false;
            btnRefrescar.innerHTML = originalText;
        }
    }
}

async function fetchDemografiaUnificada(doc) {
    const d = (doc || '').trim();
    if (!d) return null;
    if (window.ObstetriciaPacienteUnificado) {
        return await window.ObstetriciaPacienteUnificado.ensure(d);
    }
    try {
        const q = encodeURIComponent(d);
        const r = await fetch(
            `${window.location.origin}/atencion/api/datos-paciente-unificado/?num_identificacion=${q}&_=${Date.now()}`,
            { method: 'GET', headers: { Accept: 'application/json' }, credentials: 'same-origin' }
        );
        if (!r.ok) return null;
        const data = await r.json();
        if (data.ok && data.encontrado) return data;
    } catch (e) {
        console.warn('Demografía unificada:', e);
    }
    return null;
}

function nombreEsPlaceholderMeows(s) {
    const t = (s || '').trim();
    if (!t) return true;
    const u = t.toUpperCase();
    return u === 'N/A' || u === 'N/A N/A' || u === 'PACIENTE' || u === 'SIN NOMBRE' || u === '-';
}

function strVacioMeows(v) {
    return v == null || String(v).trim() === '';
}

function mergePacienteMeowsConUnificado(paciente, u) {
    if (!paciente || !u) return paciente;
    const out = { ...paciente };
    const nc = (u.nombre_completo || u.nombre_paciente || '').trim();
    if (nombreEsPlaceholderMeows(out.nombre_completo) && nc) {
        out.nombre_completo = nc;
    }
    const docU = (u.num_identificacion || u.identificacion || '').trim();
    if (docU && strVacioMeows(out.numero_documento)) {
        out.numero_documento = docU;
    }
    const fnU = (u.fecha_nacimiento || '').toString().trim();
    if (strVacioMeows(out.fecha_nacimiento) && fnU) {
        out.fecha_nacimiento = fnU.length >= 10 ? fnU.slice(0, 10) : fnU;
    }
    if ((out.edad == null || out.edad === '') && u.edad != null && u.edad !== '') {
        out.edad = u.edad;
    }
    if (strVacioMeows(out.aseguradora) && !strVacioMeows(u.aseguradora)) {
        out.aseguradora = String(u.aseguradora).trim();
    }
    if (strVacioMeows(out.cama) && !strVacioMeows(u.cama)) {
        out.cama = String(u.cama).trim();
    }
    if (strVacioMeows(out.fecha_ingreso) && !strVacioMeows(u.fecha_ingreso)) {
        out.fecha_ingreso = String(u.fecha_ingreso).slice(0, 10);
    }
    if (strVacioMeows(out.responsable) && !strVacioMeows(u.responsable)) {
        out.responsable = String(u.responsable).trim();
    }
    return out;
}

function construirPacienteSoloDesdeUnificado(documentoLimpio, u) {
    const m = window.location.pathname.match(/\/nuevo\/(\d+)\/?/);
    const pid = m ? parseInt(m[1], 10) : null;
    const fn = (u.fecha_nacimiento || '').toString().trim();
    return {
        id: Number.isFinite(pid) ? pid : null,
        nombre_completo: (u.nombre_completo || u.nombre_paciente || '').trim(),
        numero_documento: (u.num_identificacion || u.identificacion || documentoLimpio).trim(),
        fecha_nacimiento: fn.length >= 10 ? fn.slice(0, 10) : fn,
        edad: u.edad,
        aseguradora: (u.aseguradora || '').trim(),
        cama: (u.cama || '').trim(),
        fecha_ingreso: (u.fecha_ingreso || '').toString().slice(0, 10),
        responsable: (u.responsable || '').trim(),
        biometria: null,
    };
}

function aplicarDatosPacienteEnFormulario(paciente) {
    const nombreCompletoInput = document.getElementById('nombre_completo');
    const numeroDocInput = document.getElementById('numero_documento');
    const edadInput = document.getElementById('edad');
    const aseguradoraSelect = document.getElementById('aseguradora');
    const camaInput = document.getElementById('cama');
    const fechaIngresoInput = document.getElementById('fecha_ingreso');
    const responsableInput = document.getElementById('responsable');

    if (nombreCompletoInput) nombreCompletoInput.value = paciente.nombre_completo || '';
    if (numeroDocInput) numeroDocInput.value = paciente.numero_documento || '';
    if (aseguradoraSelect) {
        if (aseguradoraSelect.tagName === 'SELECT') {
            asignarValorSelectConFallback(aseguradoraSelect, paciente.aseguradora || '');
        } else {
            aseguradoraSelect.value = paciente.aseguradora || '';
        }
    }
    if (camaInput) camaInput.value = paciente.cama || '';
    if (fechaIngresoInput) fechaIngresoInput.value = paciente.fecha_ingreso || '';
    if (responsableInput) responsableInput.value = paciente.responsable || '';

    const nombreFirmaSpan = document.getElementById('nombre-firma-paciente');
    if (nombreFirmaSpan) nombreFirmaSpan.textContent = paciente.responsable || '—';

    const fechaNacimientoInput = document.getElementById('fecha_nacimiento');
    const fnApi = (paciente.fecha_nacimiento || '').trim();
    if (fechaNacimientoInput) {
        fechaNacimientoInput.value = fnApi;
    }
    if (edadInput) {
        if (fnApi) {
            const ec = calcularEdad(fnApi);
            edadInput.value = ec !== '' ? String(ec) : '';
        } else {
            const e = paciente.edad;
            edadInput.value = (e !== null && e !== undefined) ? String(e) : '';
        }
        edadInput.dispatchEvent(new Event('change'));
    }

    sincronizarCamposPaciente();
    actualizarBotonHistorial(paciente.id);

    // Reflejar biometría si existe
    if (paciente.biometria) {
        // Biometría en el pie del formulario (Original)
        const huellaImg = document.getElementById("imgHuella");
        const huellaContainer = document.getElementById("huella-container");
        const huellaEstado = document.getElementById("estadoHuella");
        if (paciente.biometria.imagen_huella && huellaImg && huellaContainer) {
            huellaImg.src = paciente.biometria.imagen_huella + "?t=" + Date.now();
            huellaContainer.style.display = "flex";
            if (huellaEstado) huellaEstado.textContent = "Registro Histórico";
        }

        if (paciente.biometria.imagen_firma) {
            actualizarVistaFirmaPaciente(paciente.biometria.imagen_firma, "Firma Histórica");
        }
    }

    // Garantiza que la firma se vea al consultar pacientes, incluso si viene desde otra sesión.
    if (paciente.numero_documento) {
        refrescarFirmaPaciente(paciente.numero_documento, { silencioso: true, estado: "Firma Histórica" });
    }
}

/**
 * Busca un paciente por número de documento y completa los campos del formulario
 */
async function buscarPacientePorDocumento(documento) {
    const documentoLimpio = (documento || '').trim();

    if (!documentoLimpio) {
        // Si el campo está vacío, limpiar los campos y deshabilitar botón de historial
        limpiarCamposPaciente();
        // Ocultar o deshabilitar el botón de historial si no hay paciente
        const btnHistorial = document.querySelector('a.btn-info[href*="historial"]');
        if (btnHistorial) {
            btnHistorial.style.display = 'none';
        }
        return;
    }

    // Evita tormenta de requests para el mismo documento mientras una búsqueda sigue en curso.
    if (busquedaPacienteEnCurso && ultimoDocumentoBuscado === documentoLimpio) {
        return;
    }

    const cacheHit = cacheBusquedaPacientes.get(documentoLimpio);
    const ahora = Date.now();
    if (cacheHit && (ahora - cacheHit.ts) < CACHE_BUSQUEDA_MS) {
        if (cacheHit.ok && cacheHit.paciente) {
            aplicarDatosPacienteEnFormulario(cacheHit.paciente);
            mostrarMensajeBusqueda(`✅ Paciente encontrado: ${cacheHit.paciente.nombre_completo || 'Sin nombre'}`, 'success');
        } else if (!cacheHit.ok) {
            limpiarCamposPaciente();
            mostrarMensajeBusqueda(`⚠️ ${cacheHit.error || 'Paciente no encontrado. Proceda a crearlo.'}`, 'error');
        }
        return;
    }

    // Mostrar mensaje de carga
    mostrarMensajeBusqueda('🔍 Buscando paciente...', 'info');
    ultimoDocumentoBuscado = documentoLimpio;
    busquedaPacienteEnCurso = true;
    const requestId = ++busquedaPacienteRequestId;

    const btnBuscarPaciente = document.getElementById('btn-buscar-paciente');
    if (btnBuscarPaciente) btnBuscarPaciente.disabled = true;

    if (busquedaPacienteController) {
        busquedaPacienteController.abort();
    }
    busquedaPacienteController = new AbortController();

    try {
        const documentoParam = encodeURIComponent(documentoLimpio);
        const baseBuscar = getMeowsUrl('apiBuscarPaciente', '/api/buscar-paciente/');
        const urlsBusqueda = [
            `${baseBuscar}?documento=${documentoParam}`
        ];
        console.log('📋 Documento buscado:', documentoLimpio);

        let response = null;
        let ultimoErrorRed = null;

        for (const url of urlsBusqueda) {
            console.log('🔍 Buscando paciente en:', url);
            try {
                const intento = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                    },
                    credentials: 'same-origin',
                    signal: busquedaPacienteController.signal,
                });

                // Si responde distinto a 404, usamos esta respuesta.
                if (intento.status !== 404) {
                    response = intento;
                    break;
                }
            } catch (error) {
                ultimoErrorRed = error;
            }
        }

        if (!response) {
            if (ultimoErrorRed) {
                console.error('❌ Error de red al hacer fetch:', ultimoErrorRed);
                throw new Error(`Error de conexión: ${ultimoErrorRed.message}. Verifique que el servidor esté corriendo.`);
            }
            throw new Error('Error 404: Not Found');
        }

        console.log('📡 Respuesta recibida, status:', response.status);

        if (!response.ok) {
            console.error('❌ Error HTTP:', response.status, response.statusText);
            let errorData;
            try {
                errorData = await response.json();
            } catch (e) {
                errorData = { error: `Error ${response.status}: ${response.statusText}` };
            }
            throw new Error(errorData.error || `Error ${response.status}`);
        }

        const data = await response.json();
        console.log('📦 Datos parseados:', data);

        if (data.success && data.paciente) {
            let paciente = data.paciente;
            const u = await fetchDemografiaUnificada(documentoLimpio);
            paciente = mergePacienteMeowsConUnificado(paciente, u);
            aplicarDatosPacienteEnFormulario(paciente);
            cacheBusquedaPacientes.set(documentoLimpio, { ts: Date.now(), ok: true, paciente });

            // Mostrar mensaje de éxito
            mostrarMensajeBusqueda(`✅ Paciente encontrado: ${paciente.nombre_completo || 'Sin nombre'}`, 'success');

            console.log('✅ Paciente encontrado:', paciente);
        } else {
            const u = await fetchDemografiaUnificada(documentoLimpio);
            if (u) {
                const paciente = construirPacienteSoloDesdeUnificado(documentoLimpio, u);
                aplicarDatosPacienteEnFormulario(paciente);
                cacheBusquedaPacientes.set(documentoLimpio, { ts: Date.now(), ok: true, paciente });
                mostrarMensajeBusqueda(
                    `✅ Datos cargados desde historial unificado: ${paciente.nombre_completo || documentoLimpio}`,
                    'success'
                );
                console.log('✅ Paciente desde API unificada:', paciente);
            } else {
                // Limpiar campos si no se encuentra
                limpiarCamposPaciente();
                // Deshabilitar botón de historial si no se encuentra paciente
                const btnHistorial = document.getElementById('btn-ver-historial') || document.querySelector('a.btn-info[href*="historial"]');
                if (btnHistorial) {
                    btnHistorial.style.display = 'none';
                }
                // Mostrar mensaje de error
                const errorMsg = data.error || 'Paciente no encontrado. Proceda a crearlo.';
                cacheBusquedaPacientes.set(documentoLimpio, { ts: Date.now(), ok: false, error: errorMsg });
                mostrarMensajeBusqueda(`⚠️ ${errorMsg}`, 'error');
                console.warn('⚠️ Paciente no encontrado:', data);
            }
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            return;
        }
        // Limpiar campos si hay error
        limpiarCamposPaciente();
        // Deshabilitar botón de historial si hay error
        const btnHistorial = document.getElementById('btn-ver-historial') || document.querySelector('a.btn-info[href*="historial"]');
        if (btnHistorial) {
            btnHistorial.style.display = 'none';
        }
        // Mostrar mensaje de error más detallado
        const errorMessage = error.message || 'Error desconocido al buscar paciente';
        mostrarMensajeBusqueda(`❌ ${errorMessage}`, 'error');
        console.error('❌ Error completo al buscar paciente:', {
            message: error.message,
            stack: error.stack,
            name: error.name,
            error: error
        });
    } finally {
        if (requestId === busquedaPacienteRequestId) {
            busquedaPacienteEnCurso = false;
            if (btnBuscarPaciente) btnBuscarPaciente.disabled = false;
        }
    }
}

/**
 * Calcula la edad a partir de la fecha de nacimiento
 */
function calcularEdad(fechaNacimiento) {
    if (!fechaNacimiento) return '';
    const hoy = new Date();
    const nacimiento = new Date(fechaNacimiento);
    let edad = hoy.getFullYear() - nacimiento.getFullYear();
    const mes = hoy.getMonth() - nacimiento.getMonth();

    if (mes < 0 || (mes === 0 && hoy.getDate() < nacimiento.getDate())) {
        edad--;
    }
    return edad >= 0 ? edad : '';
}

/**
 * Asigna valor a un select aunque no exista en sus opciones.
 * Si no existe, agrega una opción dinámica para mostrar el dato consultado.
 */
function asignarValorSelectConFallback(selectElement, valor) {
    if (!selectElement) return;

    const valorLimpio = (valor || '').trim();
    if (!valorLimpio) {
        selectElement.value = '';
        return;
    }

    const opcionExistente = Array.from(selectElement.options).find(
        (opt) => (opt.value || '').trim().toLowerCase() === valorLimpio.toLowerCase()
    );

    if (opcionExistente) {
        selectElement.value = opcionExistente.value;
        return;
    }

    // Evita acumular opciones temporales cuando se consulta varias veces.
    const opcionDinamicaAnterior = selectElement.querySelector('option[data-dinamica="true"]');
    if (opcionDinamicaAnterior) {
        opcionDinamicaAnterior.remove();
    }

    const nuevaOpcion = document.createElement('option');
    nuevaOpcion.value = valorLimpio;
    nuevaOpcion.textContent = valorLimpio;
    nuevaOpcion.setAttribute('data-dinamica', 'true');
    selectElement.appendChild(nuevaOpcion);
    selectElement.value = valorLimpio;
}

/**
 * Renderiza la tabla de pacientes activas.
 */
function renderPacientesActivas(pacientes) {
    const tbody = document.getElementById('activos-tbody');
    if (!tbody) return;

    if (!pacientes || pacientes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8">No hay pacientes activas en este momento</td></tr>';
        return;
    }

    const esc = (s) => String(s ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');

    tbody.innerHTML = pacientes.map((p) => {
        const fnDisp = p.fecha_nacimiento_display || '';
        const edadTxt = (p.edad !== null && p.edad !== undefined && p.edad !== '') ? `${p.edad} años` : '—';
        return `
        <tr>
            <td>${esc(p.numero_documento)}</td>
            <td>${esc(p.nombre_completo)}</td>
            <td>${esc(fnDisp || '—')}</td>
            <td>${esc(edadTxt)}</td>
            <td>${esc(p.aseguradora)}</td>
            <td>${esc(p.cama)}</td>
            <td>${esc(p.fecha_ingreso)}</td>
            <td>
                <button type="button" class="btn-usar-activa" data-doc="${esc(p.numero_documento)}"
                    data-fecha-nac="${esc(p.fecha_nacimiento)}"
                    data-edad="${esc(p.edad !== null && p.edad !== undefined ? p.edad : '')}">
                    Cargar
                </button>
            </td>
        </tr>`;
    }).join('');

    tbody.querySelectorAll('.btn-usar-activa').forEach((btn) => {
        btn.addEventListener('click', () => {
            const doc = btn.getAttribute('data-doc');
            if (!doc) return;

            const buscarPacienteInput = document.getElementById('buscar-paciente-input');
            if (buscarPacienteInput) buscarPacienteInput.value = doc;

            const fnPre = btn.getAttribute('data-fecha-nac') || '';
            const edPre = btn.getAttribute('data-edad');
            const fechaNacEl = document.getElementById('fecha_nacimiento');
            const edadEl = document.getElementById('edad');
            if (fechaNacEl && fnPre) fechaNacEl.value = fnPre;
            if (edadEl && edPre !== null && edPre !== '') edadEl.value = String(edPre);

            buscarPacientePorDocumento(doc);
        });
    });
}

/**
 * Carga pacientes activas desde backend.
 */
async function cargarPacientesActivas() {
    try {
        const apiActivos = getMeowsUrl('apiPacientesActivos', '/api/pacientes-activos/');
        const response = await fetch(`${apiActivos}?limit=80`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            credentials: 'same-origin'
        });

        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Error consultando pacientes activas');
        }

        renderPacientesActivas(data.pacientes || []);
    } catch (error) {
        renderPacientesActivas([]);
        mostrarMensajeBusqueda(`❌ ${error.message}`, 'error');
    }
}

/**
 * Obtiene el ID del paciente disponible en la vista actual
 */
function obtenerPacienteIdActual() {
    // 1) Prioridad: botón de historial ya sincronizado con el paciente activo
    const btnHistorial = document.getElementById('btn-ver-historial');
    if (btnHistorial && btnHistorial.href) {
        const matchHistorial = btnHistorial.href.match(/\/historial\/(\d+)\/?/);
        if (matchHistorial) return matchHistorial[1];
    }

    // 2) Fallback: URL actual /nuevo/<id>/
    const matchPath = window.location.pathname.match(/\/nuevo\/(\d+)\/?/);
    if (matchPath) return matchPath[1];

    return null;
}

// Event listener para calcular edad cuando cambia fecha de nacimiento
document.addEventListener('DOMContentLoaded', function () {
    const fechaNacInput = document.getElementById('fecha_nacimiento');
    const edadInput = document.getElementById('edad');

    if (fechaNacInput && edadInput) {
        fechaNacInput.addEventListener('change', function () {
            const edad = calcularEdad(this.value);
            edadInput.value = edad;
            edadInput.dispatchEvent(new Event('change'));
        });
    }
});

/**
 * Convierte el input de temperatura a select con valores válidos (34-40)
 */
function convertirTempASelect() {
    const tempInput = document.getElementById('temp');
    if (!tempInput || tempInput.tagName === 'SELECT') {
        return; // Ya es select o no existe
    }

    const valorActual = tempInput.value;
    const unidad = tempInput.dataset.unidad || '°C';

    // Generar opciones desde 34 hasta 40 con incrementos de 1 (valores enteros)
    let opciones = '<option value="">seleccione</option>';
    for (let valor = 34; valor <= 40; valor++) {
        opciones += `<option value="${valor}">${valor}</option>`;
    }

    // Crear el select
    const select = document.createElement('select');
    select.id = tempInput.id;
    select.name = tempInput.name;
    select.className = tempInput.className + ' parameter-select';
    select.required = tempInput.required;
    select.setAttribute('data-param', 'temp');
    select.setAttribute('data-unidad', unidad);
    select.innerHTML = opciones;

    // Seleccionar el valor actual si existe y está en el rango válido
    if (valorActual) {
        const valorNum = parseFloat(valorActual);
        if (!isNaN(valorNum) && valorNum >= 34 && valorNum <= 40) {
            // Redondear al entero más cercano
            select.value = Math.round(valorNum).toString();
        }
    }

    // Reemplazar el input con el select
    tempInput.parentNode.replaceChild(select, tempInput);
}

/**
 * Convierte el input de tensión arterial sistólica a select con valores válidos (70-200, de 10 en 10)
 */
function convertirTaSysASelect() {
    const taSysInput = document.getElementById('ta_sys');
    if (!taSysInput || taSysInput.tagName === 'SELECT') {
        return; // Ya es select o no existe
    }

    const valorActual = taSysInput.value;
    const unidad = taSysInput.dataset.unidad || 'mmHg';

    // Generar opciones desde 70 hasta 200 con incrementos de 10
    let opciones = '<option value="">seleccione</option>';
    for (let valor = 70; valor <= 200; valor += 10) {
        opciones += `<option value="${valor}">${valor}</option>`;
    }

    // Crear el select
    const select = document.createElement('select');
    select.id = taSysInput.id;
    select.name = taSysInput.name;
    select.className = taSysInput.className + ' parameter-select';
    select.required = taSysInput.required;
    select.setAttribute('data-param', 'ta_sys');
    select.setAttribute('data-unidad', unidad);
    select.innerHTML = opciones;

    // Seleccionar el valor actual si existe y está en el rango válido
    if (valorActual) {
        const valorNum = parseFloat(valorActual);
        if (!isNaN(valorNum) && valorNum >= 70 && valorNum <= 200) {
            // Redondear al múltiplo de 10 más cercano
            const valorRedondeado = Math.round(valorNum / 10) * 10;
            if (valorRedondeado >= 70 && valorRedondeado <= 200) {
                select.value = valorRedondeado.toString();
            }
        }
    }

    // Reemplazar el input con el select
    taSysInput.parentNode.replaceChild(select, taSysInput);
}

/**
 * Convierte el input de tensión arterial diastólica a select con valores válidos (60-120, de 10 en 10)
 */
function convertirTaDiaASelect() {
    const taDiaInput = document.getElementById('ta_dia');
    if (!taDiaInput || taDiaInput.tagName === 'SELECT') {
        return; // Ya es select o no existe
    }

    const valorActual = taDiaInput.value;
    const unidad = taDiaInput.dataset.unidad || 'mmHg';

    // Generar opciones desde 60 hasta 120 con incrementos de 10
    let opciones = '<option value="">seleccione</option>';
    for (let valor = 60; valor <= 120; valor += 10) {
        opciones += `<option value="${valor}">${valor}</option>`;
    }

    // Crear el select
    const select = document.createElement('select');
    select.id = taDiaInput.id;
    select.name = taDiaInput.name;
    select.className = taDiaInput.className + ' parameter-select';
    select.required = taDiaInput.required;
    select.setAttribute('data-param', 'ta_dia');
    select.setAttribute('data-unidad', unidad);
    select.innerHTML = opciones;

    // Seleccionar el valor actual si existe y está en el rango válido
    if (valorActual) {
        const valorNum = parseFloat(valorActual);
        if (!isNaN(valorNum) && valorNum >= 60 && valorNum <= 120) {
            // Redondear al múltiplo de 10 más cercano
            const valorRedondeado = Math.round(valorNum / 10) * 10;
            if (valorRedondeado >= 60 && valorRedondeado <= 120) {
                select.value = valorRedondeado.toString();
            }
        }
    }

    // Reemplazar el input con el select
    taDiaInput.parentNode.replaceChild(select, taDiaInput);
}

/**
 * Convierte el input de frecuencia cardíaca a select con valores válidos (40-170, de 10 en 10)
 */
function convertirFcASelect() {
    const fcInput = document.getElementById('fc');
    if (!fcInput || fcInput.tagName === 'SELECT') {
        return; // Ya es select o no existe
    }

    const valorActual = fcInput.value;
    const unidad = fcInput.dataset.unidad || 'lpm';

    // Generar opciones desde 40 hasta 170 con incrementos de 10
    let opciones = '<option value="">seleccione</option>';
    for (let valor = 40; valor <= 170; valor += 10) {
        opciones += `<option value="${valor}">${valor}</option>`;
    }

    // Crear el select
    const select = document.createElement('select');
    select.id = fcInput.id;
    select.name = fcInput.name;
    select.className = fcInput.className + ' parameter-select';
    select.required = fcInput.required;
    select.setAttribute('data-param', 'fc');
    select.setAttribute('data-unidad', unidad);
    select.innerHTML = opciones;

    // Seleccionar el valor actual si existe y está en el rango válido
    if (valorActual) {
        const valorNum = parseFloat(valorActual);
        if (!isNaN(valorNum) && valorNum >= 40 && valorNum <= 170) {
            // Redondear al múltiplo de 10 más cercano
            const valorRedondeado = Math.round(valorNum / 10) * 10;
            if (valorRedondeado >= 40 && valorRedondeado <= 170) {
                select.value = valorRedondeado.toString();
            }
        }
    }

    // Reemplazar el input con el select
    fcInput.parentNode.replaceChild(select, fcInput);
}

/**
 * Convierte el input de frecuencia cardíaca fetal a select con valores válidos (110-190, de 10 en 10)
 */
function convertirFcfASelect() {
    const fcfInput = document.getElementById('fcf');
    if (!fcfInput || fcfInput.tagName === 'SELECT') {
        return; // Ya es select o no existe
    }

    const valorActual = fcfInput.value;
    const unidad = fcfInput.dataset.unidad || 'lpm';

    // Generar opciones desde 110 hasta 190 con incrementos de 10
    let opciones = '<option value="">seleccione</option>';
    for (let valor = 110; valor <= 190; valor += 10) {
        opciones += `<option value="${valor}">${valor}</option>`;
    }

    // Crear el select
    const select = document.createElement('select');
    select.id = fcfInput.id;
    select.name = fcfInput.name;
    select.className = fcfInput.className + ' parameter-select';
    select.required = fcfInput.required;
    select.setAttribute('data-param', 'fcf');
    select.setAttribute('data-unidad', unidad);
    select.innerHTML = opciones;

    // Seleccionar el valor actual si existe y está en el rango válido
    if (valorActual) {
        const valorNum = parseFloat(valorActual);
        if (!isNaN(valorNum) && valorNum >= 110 && valorNum <= 190) {
            // Redondear al múltiplo de 10 más cercano
            const valorRedondeado = Math.round(valorNum / 10) * 10;
            if (valorRedondeado >= 110 && valorRedondeado <= 190) {
                select.value = valorRedondeado.toString();
            }
        }
    }

    // Reemplazar el input con el select
    fcfInput.parentNode.replaceChild(select, fcfInput);
}

/**
 * Convierte el input de SpO2 a select con valores válidos (80-100, de 1 en 1)
 */
function convertirSpo2ASelect() {
    const spo2Input = document.getElementById('spo2');
    if (!spo2Input || spo2Input.tagName === 'SELECT') {
        return; // Ya es select o no existe
    }

    const valorActual = spo2Input.value;
    const unidad = spo2Input.dataset.unidad || '%';

    // Generar opciones desde 80 hasta 100
    let opciones = '<option value="">seleccione</option>';
    for (let valor = 80; valor <= 100; valor++) {
        opciones += `<option value="${valor}">${valor}</option>`;
    }

    // Crear el select
    const select = document.createElement('select');
    select.id = spo2Input.id;
    select.name = spo2Input.name;
    select.className = spo2Input.className + ' parameter-select';
    select.required = spo2Input.required;
    select.setAttribute('data-param', 'spo2');
    select.setAttribute('data-unidad', unidad);
    select.innerHTML = opciones;

    // Seleccionar el valor actual si existe y está en el rango válido
    if (valorActual) {
        const valorNum = parseFloat(valorActual);
        if (!isNaN(valorNum) && valorNum >= 80 && valorNum <= 100) {
            select.value = Math.round(valorNum).toString();
        }
    }

    // Reemplazar el input con el select
    spo2Input.parentNode.replaceChild(select, spo2Input);
}

/**
 * CLASE PARA MANEJO DE FIRMA DIGITAL
 */
class FirmaDigital {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.dibujando = false;
        this.hayFirma = false;
        
        // Ajustar resolución para pantallas retina
        const ratio = window.devicePixelRatio || 1;
        this.canvas.width = 400 * ratio;
        this.canvas.height = 200 * ratio;
        this.ctx.scale(ratio, ratio);
        
        this.ctx.lineWidth = 2;
        this.ctx.lineJoin = 'round';
        this.ctx.lineCap = 'round';
        this.ctx.strokeStyle = '#182848';

        this.initEvents();
    }

    initEvents() {
        const getPos = (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            
            // Factor de escala entre el tamaño visual (rect) y el lógico (400x200)
            const scaleX = 400 / rect.width;
            const scaleY = 200 / rect.height;
            
            return {
                x: (clientX - rect.left) * scaleX,
                y: (clientY - rect.top) * scaleY
            };
        };

        const start = (e) => {
            this.dibujando = true;
            this.hayFirma = true;
            const pos = getPos(e);
            this.ctx.beginPath();
            this.ctx.moveTo(pos.x, pos.y);
            e.preventDefault();
        };

        const move = (e) => {
            if (!this.dibujando) return;
            const pos = getPos(e);
            this.ctx.lineTo(pos.x, pos.y);
            this.ctx.stroke();
            e.preventDefault();
        };

        const stop = () => {
            this.dibujando = false;
        };

        this.canvas.addEventListener('mousedown', start);
        this.canvas.addEventListener('mousemove', move);
        window.addEventListener('mouseup', stop);

        this.canvas.addEventListener('touchstart', start, { passive: false });
        this.canvas.addEventListener('touchmove', move, { passive: false });
        this.canvas.addEventListener('touchend', stop);
    }

    limpiar() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.hayFirma = false;
    }

    obtenerBase64() {
        if (!this.hayFirma) return null;
        return this.canvas.toDataURL('image/png');
    }
}

let firmaPad = null;

/**
 * Lanza el modal de biometría en lugar del deep link directo
 * AHORA: Se comporta como un popover posicionado sobre el botón
 */
function abrirModalBiometria() {
    const pacienteDoc = document.getElementById("numero_documento").value;
    if (!pacienteDoc) {
        alert("Por favor, ingrese el número de documento del paciente.");
        return;
    }

    const btnTrigger = document.getElementById('btn-capturar-huella');
    const modal = document.getElementById('modal-biometria');
    
    if (!btnTrigger || !modal) return;

    // Activar modo popover
    modal.classList.add('is-popover');
    
    // Calcular posición
    const rect = btnTrigger.getBoundingClientRect();
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    // Posicionar encima del botón (850px es el ancho en el CSS)
    const popoverWidth = 850;
    let left = rect.left + scrollLeft - (popoverWidth / 2) + (rect.width / 2);
    let top = rect.top + scrollTop - 480; // Ajuste para que quede arriba del botón
    
    // Validar bordes de pantalla
    if (left < 10) left = 10;
    if (left + popoverWidth > window.innerWidth - 10) {
        left = window.innerWidth - popoverWidth - 10;
    }
    if (top < 10) top = rect.bottom + scrollTop + 20; // Si no cabe arriba, poner abajo

    modal.style.left = `${left}px`;
    modal.style.top = `${top}px`;
    modal.style.display = 'block';
    
    // Inicializar Firma si no existe
    if (!firmaPad) {
        firmaPad = new FirmaDigital('firma-canvas');
    } else {
        firmaPad.limpiar();
    }

    // Limpiar previews de huella en el modal
    const preview = document.getElementById('huella-modal-preview');
    const status = document.getElementById('huella-modal-status');
    if (preview) preview.innerHTML = '<span class="placeholder-icon">🖱️</span>';
    if (status) status.innerHTML = 'Esperando captura...';

    // Cerrar al hacer clic fuera
    const closeOnOutsideClick = (e) => {
        if (!modal.contains(e.target) && e.target !== btnTrigger && !btnTrigger.contains(e.target)) {
            modal.style.display = 'none';
            document.removeEventListener('mousedown', closeOnOutsideClick);
        }
    };
    
    setTimeout(() => {
        document.addEventListener('mousedown', closeOnOutsideClick);
    }, 100);
}

/**
 * Guarda la firma digital vía API
 */
async function guardarFirmaDigital() {
    const b64 = firmaPad.obtenerBase64();
    if (!b64) {
        alert("Por favor, el paciente debe firmar primero.");
        return;
    }

    const pacienteDoc = document.getElementById("numero_documento").value;
    const btn = document.getElementById('btn-guardar-firma');
    const originalText = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = "Guardando...";

    try {
        const response = await fetch(getApiGuardarBiometriaUrl(), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                paciente_id: pacienteDoc,
                firma: b64,
                usuario: "Sistema"
            })
        });

        if (response.ok) {
            const data = await response.json();
            alert("✅ Firma guardada con éxito");
            btn.innerHTML = "✓ Guardada";
            btn.classList.replace('btn-success', 'btn-secondary');
            
            if (data.imagen_firma) {
                actualizarVistaFirmaPaciente(data.imagen_firma, "Firma Capturada");
                await refrescarFirmaPaciente(pacienteDoc, { silencioso: true, estado: "Firma Guardada" });

                // Cerrar modal automáticamente después de un pequeño delay
                setTimeout(() => {
                    const modal = document.getElementById('modal-biometria');
                    if (modal) modal.style.display = 'none';
                }, 1500);
            }
        } else {
            throw new Error("Error al guardar");
        }
    } catch (err) {
        alert("❌ Error al conectar con el servidor");
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

/**
 * Polling mejorado para el modal y la vista principal
 */
function iniciarPollingHuellaModal(pacienteDoc) {
    // Huella deshabilitada en este desarrollo.
    // Se mantiene la función para compatibilidad con llamadas legacy.
    if (pacienteDoc) {
        refrescarFirmaPaciente(pacienteDoc, { silencioso: true, estado: "Firma actualizada" });
    }
}

/**
 * Lanza la captura de huella vía Deep Link
 */
function capturarHuella() {
    const pacienteDoc = document.getElementById("numero_documento").value;
    
    if (!pacienteDoc) {
        alert("Por favor, ingrese el número de documento del paciente.");
        return;
    }
    refrescarFirmaPaciente(pacienteDoc, { silencioso: false, estado: "Firma actualizada" });
}

/**
 * Redirige a la función de polling unificada
 */
function iniciarPollingHuella(pacienteDoc) {
    iniciarPollingHuellaModal(pacienteDoc);
}

/**
 * Inicializa los event listeners
 */
async function inicializar() {
    // Cargar rangos desde el backend primero
    await cargarRangosDesdeBackend();

    // Convertir temperatura a select
    convertirTempASelect();

    // Convertir tensión arterial sistólica a select
    convertirTaSysASelect();

    // Convertir tensión arterial diastólica a select
    convertirTaDiaASelect();

    // Convertir frecuencia cardíaca a select
    convertirFcASelect();

    // Convertir frecuencia cardíaca fetal a select
    convertirFcfASelect();

    // Convertir saturación de oxígeno (SpO2) a select
    convertirSpo2ASelect();

    // Sincronizar campos del paciente
    sincronizarCamposPaciente();

    const btnRefUni = document.getElementById('btn-meows-refrescar-unificado');
    if (btnRefUni) {
        btnRefUni.addEventListener('click', async () => {
            const doc = (
                document.getElementById('numero_documento')?.value ||
                document.getElementById('buscar-paciente-input')?.value ||
                ''
            ).trim();
            if (!doc) {
                mostrarMensajeBusqueda('Ingrese documento en el buscador para actualizar desde la consulta unificada.', 'error');
                return;
            }
            if (window.ObstetriciaPacienteUnificado) {
                window.ObstetriciaPacienteUnificado.invalidate();
            }
            await buscarPacientePorDocumento(doc);
        });
    }

    // Configurar búsqueda de paciente
    const buscarPacienteInput = document.getElementById('buscar-paciente-input');
    const btnBuscarPaciente = document.getElementById('btn-buscar-paciente');

    // Función para ejecutar la búsqueda
    function ejecutarBusqueda() {
        if (buscarPacienteInput) {
            const documento = buscarPacienteInput.value.trim();
            // Si está vacío, limpiar campos. Si tiene valor, buscar
            buscarPacientePorDocumento(documento);
        }
    }

    // Buscar al hacer clic en el botón
    if (btnBuscarPaciente) {
        btnBuscarPaciente.addEventListener('click', ejecutarBusqueda);
    }

    // También buscar al hacer Enter en el input
    if (buscarPacienteInput) {
        buscarPacienteInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                ejecutarBusqueda();
            }
        });
    }

    // Mostrar/actualizar usuario responsable en la card de firma
    const responsableInput = document.getElementById('responsable');
    if (responsableInput) {
        const nombreFirmaSpan = document.getElementById('nombre-firma-paciente');
        if (nombreFirmaSpan) {
            nombreFirmaSpan.textContent = responsableInput.value || '—';
        }
        responsableInput.addEventListener('input', function() {
            const nombreFirmaSpan = document.getElementById('nombre-firma-paciente');
            if (nombreFirmaSpan) {
                nombreFirmaSpan.textContent = this.value || '—';
            }
        });
    }

    // Botón para ver pacientes activas en tiempo real
    const btnActivosTiempoReal = document.getElementById('btn-ver-activos-tiempo-real');
    const panelActivos = document.getElementById('activos-tiempo-real-panel');
    const btnActualizarActivos = document.getElementById('btn-actualizar-activos');

    if (btnActivosTiempoReal && panelActivos) {
        btnActivosTiempoReal.addEventListener('click', async () => {
            const panelVisible = panelActivos.style.display !== 'none';
            if (panelVisible) {
                panelActivos.style.display = 'none';
                btnActivosTiempoReal.innerHTML = '<span class="btn-icon">🟢</span>Mirar personas activas tiempo real';
                if (activosRefreshInterval) {
                    clearInterval(activosRefreshInterval);
                    activosRefreshInterval = null;
                }
                return;
            }

            panelActivos.style.display = 'block';
            btnActivosTiempoReal.innerHTML = '<span class="btn-icon">🛑</span>Ocultar personas activas';
            await cargarPacientesActivas();

            if (activosRefreshInterval) clearInterval(activosRefreshInterval);
            activosRefreshInterval = setInterval(() => {
                cargarPacientesActivas();
            }, 15000);
        });
    }

    if (btnActualizarActivos) {
        btnActualizarActivos.addEventListener('click', () => {
            cargarPacientesActivas();
        });
    }

    async function procesarCambioParametro(input, usarApi = false) {
        const parametro = input.dataset.param;
        const valor = input.value;
        const score = usarApi
            ? await calcularScoreDesdeApi(parametro, valor)
            : calcularScore(parametro, valor);

        actualizarFeedback(parametro, valor, score);
        actualizarResumen();
    }

    // Event listener para cada input/select
    document.querySelectorAll('.parameter-input').forEach(input => {
        const esSelect = input.tagName === 'SELECT';

        if (esSelect) {
            // En selects usamos API al confirmar cambio
            input.addEventListener('change', function () {
                procesarCambioParametro(this, true);
            }, { passive: true, capture: false });
        } else {
            // Para inputs numéricos, mantener feedback inmediato local
            input.addEventListener('input', function () {
                procesarCambioParametro(this, false);
            }, { passive: true });

            // Al confirmar el cambio, recalcular contra API
            input.addEventListener('change', function () {
                procesarCambioParametro(this, true);
            }, { passive: true });
        }

        // Validar al perder foco
        input.addEventListener('blur', function () {
            const parametro = this.dataset.param;
            const valor = this.value;

            if (valor && valor !== '') {
                const score = calcularScore(parametro, valor);
                if (score === null) {
                    this.setCustomValidity('Valor fuera del rango esperado');
                } else {
                    this.setCustomValidity('');
                }
            }
        });
    });

    // Botón limpiar
    const btnLimpiar = document.getElementById('btn-limpiar');
    if (btnLimpiar) {
        btnLimpiar.addEventListener('click', function () {
            if (confirm('¿Está seguro de limpiar todos los campos?')) {
                document.querySelectorAll('.parameter-input').forEach(input => {
                    input.value = '';
                    const parametro = input.dataset.param;
                    actualizarFeedback(parametro, '', null);
                });
                actualizarResumen();
            }
        });
    }

    // Validación del formulario antes de enviar
    const form = document.getElementById('meows-form');
    if (form) {
        form.addEventListener('submit', function (e) {
            let isValid = true;
            const inputs = document.querySelectorAll('.parameter-input[required]');

            inputs.forEach(input => {
                if (!input.value || input.value === '') {
                    isValid = false;
                    input.classList.add('error');
                } else {
                    const score = calcularScore(input.dataset.param, input.value);
                    if (score === null) {
                        isValid = false;
                        input.classList.add('error');
                    }
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Por favor complete todos los campos requeridos con valores válidos.');
                return false;
            }
        });
    }

    // Calcular resumen inicial
    actualizarResumen();

    // Botón generar PDF
    const btnGenerarPDF = document.getElementById('btn-generar-pdf');
    if (btnGenerarPDF) {
        btnGenerarPDF.addEventListener('click', async function () {
            const textoOriginal = btnGenerarPDF.innerHTML;
            btnGenerarPDF.disabled = true;
            btnGenerarPDF.innerHTML = '<span class="btn-icon">⏳</span>Generando PDF...';

            try {
                // Ir directo al PDF si ya tenemos el id en la vista (evita una consulta extra)
                const pacienteIdActual = obtenerPacienteIdActual();
                if (pacienteIdActual) {
                    const pdfTemplate = getMeowsUrl('pdfTemplate', '/pdf/0/');
                    window.location.href = buildUrlFromTemplate(pdfTemplate, pacienteIdActual);
                    return;
                }

                // Fallback: buscar por documento solo si no hay id disponible
                const numeroDocInput = document.getElementById('numero_documento');
                const numeroDoc = numeroDocInput ? numeroDocInput.value.trim() : '';

                if (!numeroDoc) {
                    alert('Por favor, ingrese el número de documento del paciente para generar el PDF.');
                    return;
                }

                const apiBuscar = getMeowsUrl('apiBuscarPaciente', '/api/buscar-paciente/');
                const response = await fetch(`${apiBuscar}?documento=${encodeURIComponent(numeroDoc)}`);
                const data = await response.json();

                if (data.success && data.paciente && data.paciente.id) {
                    const pdfTemplate = getMeowsUrl('pdfTemplate', '/pdf/0/');
                    window.location.href = buildUrlFromTemplate(pdfTemplate, data.paciente.id);
                } else {
                    alert('No se encontró el paciente. Por favor, guarde primero una medición para este paciente antes de generar el PDF.');
                }
            } catch (error) {
                console.error('Error al buscar paciente para PDF:', error);
                alert('Error al generar el PDF. Por favor, intente nuevamente.');
            } finally {
                // Si no hubo navegación, restaurar botón
                btnGenerarPDF.disabled = false;
                btnGenerarPDF.innerHTML = textoOriginal;
            }
        });
    }

    // Botón capturar huella (ahora abre modal)
    const btnCapturarHuella = document.getElementById('btn-capturar-huella');
    if (btnCapturarHuella) {
        btnCapturarHuella.removeEventListener('click', capturarHuella); // Limpiar anterior
        btnCapturarHuella.addEventListener('click', abrirModalBiometria);
    }

    const btnRefrescarFirma = document.getElementById('btn-refrescar-firma');
    if (btnRefrescarFirma) {
        btnRefrescarFirma.addEventListener('click', async () => {
            const doc = (document.getElementById("numero_documento")?.value || '').trim();
            if (!doc) {
                alert("Ingrese el documento del paciente para refrescar la firma.");
                return;
            }
            await refrescarFirmaPaciente(doc, { silencioso: false, estado: "Firma actualizada" });
        });
    }

    // Eventos del Modal
    const btnCerrarModal = document.getElementById('btn-cerrar-modal-biometria');
    if (btnCerrarModal) {
        btnCerrarModal.addEventListener('click', () => {
            document.getElementById('modal-biometria').style.display = 'none';
        });
    }

    const btnFinalizar = document.getElementById('btn-finalizar-biometria');
    if (btnFinalizar) {
        btnFinalizar.addEventListener('click', () => {
            document.getElementById('modal-biometria').style.display = 'none';
        });
    }

    const btnGuardarFirma = document.getElementById('btn-guardar-firma');
    if (btnGuardarFirma) {
        btnGuardarFirma.addEventListener('click', guardarFirmaDigital);
    }

    const btnLimpiarFirma = document.getElementById('btn-limpiar-firma');
    if (btnLimpiarFirma) {
        btnLimpiarFirma.addEventListener('click', () => {
            if (firmaPad) firmaPad.limpiar();
            const btnG = document.getElementById('btn-guardar-firma');
            btnG.disabled = false;
            btnG.innerHTML = "Guardar Firma";
            btnG.classList.replace('btn-secondary', 'btn-success');
        });
    }

    const btnTriggerHuellaModal = document.getElementById('btn-trigger-huella-modal');
    if (btnTriggerHuellaModal) {
        btnTriggerHuellaModal.addEventListener('click', capturarHuella);
    }

    // Si la vista abre con un paciente ya cargado, mostrar su firma guardada.
    const docInicial = (document.getElementById("numero_documento")?.value || '').trim();
    if (docInicial) {
        refrescarFirmaPaciente(docInicial, { silencioso: true, estado: "Firma Histórica" });
    }

    const params = new URLSearchParams(window.location.search);
    const docQuery = (params.get('doc') || params.get('num_identificacion') || '').trim();
    const docParaAutocargar = docQuery || docInicial;
    if (docParaAutocargar) {
        const inpBuscar = document.getElementById('buscar-paciente-input');
        if (inpBuscar && !inpBuscar.value.trim()) {
            inpBuscar.value = docParaAutocargar;
        }
        buscarPacientePorDocumento(docParaAutocargar);
    }
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializar);
} else {
    inicializar();
}

