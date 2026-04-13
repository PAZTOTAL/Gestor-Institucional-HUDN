/**
 * MEOWS Form - Validación y Cálculo en Tiempo Real
 * Calcula scores, sumatoria y riesgo automáticamente mientras el usuario ingresa valores
 * Conectado al backend Django para obtener rangos desde la base de datos
 */

// Rangos MEOWS - se cargan desde el backend
let MEOWS_RANGOS = {};

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
        const response = await fetch('/meows/api/rangos/');
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
    const campos = [
        'nombre_completo', 'numero_documento', 'fecha_nacimiento',
        'edad', 'aseguradora', 'cama', 'fecha_ingreso', 'responsable'
    ];

    campos.forEach(campo => {
        const input = document.getElementById(campo);
        const hidden = document.getElementById(`hidden-${campo}`);
        if (input && hidden) {
            // Sincronizar al cambiar
            input.addEventListener('input', function () {
                hidden.value = this.value;
            });
            input.addEventListener('change', function () {
                hidden.value = this.value;
            });
            // Sincronizar valor inicial
            hidden.value = input.value;
        }
    });
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

    // Insertar después del wrapper de búsqueda
    const searchWrapper = document.querySelector('.search-patient-wrapper');
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
        btnHistorial.href = `/meows/historial/${pacienteId}/`;
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

    // Limpiar campos ocultos también
    sincronizarCamposPaciente();
}

/**
 * Busca un paciente por número de documento y completa los campos del formulario
 */
/**
 * Busca un paciente por número de documento y completa los campos del formulario
 */
async function buscarPacientePorDocumento(documento) {
    if (!documento || documento.trim() === '') {
        // NUEVA LÓGICA: Si está vacío, abrir modal de pacientes activos
        abrirModalPacientesActivos();
        return;
    }

    // Mostrar mensaje de carga
    mostrarMensajeBusqueda('🔍 Buscando paciente...', 'info');

    try {
        // Construir URL de forma más robusta
        const baseUrl = window.location.origin;
        const url = `${baseUrl}/meows/api/buscar-paciente/?documento=${encodeURIComponent(documento)}`;
        console.log('🔍 Buscando paciente en:', url);

        const response = await fetch(url).catch(error => {
            throw new Error(`Error de conexión: ${error.message}`);
        });

        if (!response.ok) {
            throw new Error(`Error ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.paciente) {
            llenarFormularioPaciente(data.paciente);
            mostrarMensajeBusqueda(`✅ Paciente encontrado: ${data.paciente.nombre_completo || 'Sin nombre'}`, 'success');
        } else {
            limpiarCamposPaciente();
            const errorMsg = data.error || 'Paciente no encontrado. Proceda a crearlo.';
            mostrarMensajeBusqueda(`⚠️ ${errorMsg}`, 'error');
        }
    } catch (error) {
        limpiarCamposPaciente();
        mostrarMensajeBusqueda(`❌ ${error.message || 'Error desconocido'}`, 'error');
    }
}

/**
 * Llena los campos del formulario con los datos del paciente
 */
function llenarFormularioPaciente(paciente) {
    const nombreCompletoInput = document.getElementById('nombre_completo');
    const numeroDocInput = document.getElementById('numero_documento');
    const edadInput = document.getElementById('edad');
    const aseguradoraSelect = document.getElementById('aseguradora');
    const camaInput = document.getElementById('cama');
    const fechaIngresoInput = document.getElementById('fecha_ingreso');
    const responsableInput = document.getElementById('responsable');
    const fechaNacimientoInput = document.getElementById('fecha_nacimiento');

    if (nombreCompletoInput) nombreCompletoInput.value = paciente.nombre_completo || '';
    if (numeroDocInput) numeroDocInput.value = paciente.numero_documento || '';
    if (edadInput) edadInput.value = paciente.edad || '';
    if (aseguradoraSelect) aseguradoraSelect.value = paciente.aseguradora || '';
    if (camaInput) camaInput.value = paciente.cama || '';
    if (fechaIngresoInput) fechaIngresoInput.value = paciente.fecha_ingreso || '';
    if (responsableInput) responsableInput.value = paciente.responsable || '';

    if (fechaNacimientoInput) {
        fechaNacimientoInput.value = paciente.fecha_nacimiento || '';
        if (paciente.fecha_nacimiento) {
            const edadCalculada = calcularEdad(paciente.fecha_nacimiento);
            if (edadInput) {
                edadInput.value = edadCalculada;
                edadInput.dispatchEvent(new Event('change'));
            }
        }
    }

    sincronizarCamposPaciente();
    actualizarBotonHistorial(paciente.id);
}

/**
 * Abre el modal y carga la lista de pacientes activos
 */
async function abrirModalPacientesActivos() {
    const modal = document.getElementById('modal-pacientes-activos');
    const listaContainer = document.getElementById('lista-pacientes-activos');
    const loading = document.getElementById('modal-loading');

    if (!modal || !listaContainer) return;

    modal.style.display = 'block';
    listaContainer.innerHTML = '';

    if (loading) loading.style.display = 'block';

    try {
        const response = await fetch('/meows/api/pacientes-activos/');
        const data = await response.json();

        if (loading) loading.style.display = 'none';

        if (data.success && data.pacientes && data.pacientes.length > 0) {
            data.pacientes.forEach(p => {
                const item = document.createElement('div');
                item.className = 'patient-item';
                item.innerHTML = `
                    <h4>${p.nombre_completo}</h4>
                    <p><strong>Doc:</strong> ${p.documento} | <strong>Cama:</strong> ${p.cama || 'Sin asignar'}</p>
                    <p><strong>Ingreso:</strong> ${p.ingreso} (${p.fecha ? p.fecha.split('T')[0] : ''})</p>
                `;
                item.addEventListener('click', () => {
                    document.getElementById('numero_documento').value = p.documento;
                    buscarPacientePorDocumento(p.documento); // Disparar búsqueda completa
                    modal.style.display = 'none';
                });
                listaContainer.appendChild(item);
            });
        } else {
            listaContainer.innerHTML = '<p class="text-center p-3">No hay pacientes activos en Obstetricia.</p>';
        }

    } catch (error) {
        if (loading) loading.style.display = 'none';
        listaContainer.innerHTML = '<p class="error-text">Error cargando lista de pacientes.</p>';
        console.error(error);
    }
}

// Event Listeners para el Modal
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('modal-pacientes-activos');
    const closeBtn = document.querySelector('.close-modal');

    if (closeBtn && modal) {
        closeBtn.onclick = () => modal.style.display = 'none';
        window.onclick = (event) => {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        };
    }
});

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

// Event listener para calcular edad cuando cambia fecha de nacimiento
document.addEventListener('DOMContentLoaded', function () {
    const fechaNacInput = document.getElementById('fecha_nacimiento');
    const edadInput = document.getElementById('edad');

    if (fechaNacInput && edadInput) {
        fechaNacInput.addEventListener('change', function () {
            const edad = calcularEdad(this.value);
            edadInput.value = edad;
            // Disparar evento change para sincronizar campos ocultos
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

    // Sincronizar campos del paciente
    sincronizarCamposPaciente();

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

    // Event listener para cada input/select
    document.querySelectorAll('.parameter-input').forEach(input => {
        const esSelect = input.tagName === 'SELECT';

        if (esSelect) {
            // Para selects, solo usar 'change' (más eficiente)
            // Usar función directa sin requestAnimationFrame para máxima velocidad
            input.addEventListener('change', function () {
                const parametro = this.dataset.param;
                const valor = this.value;
                const score = calcularScore(parametro, valor);
                actualizarFeedback(parametro, valor, score);
                actualizarResumen();
            }, { passive: true, capture: false });
        } else {
            // Para inputs numéricos, usar 'input' para tiempo real
            input.addEventListener('input', function () {
                const parametro = this.dataset.param;
                const valor = this.value;
                const score = calcularScore(parametro, valor);

                actualizarFeedback(parametro, valor, score);
                actualizarResumen();
            }, { passive: true });

            // También 'change' para validación final
            input.addEventListener('change', function () {
                const parametro = this.dataset.param;
                const valor = this.value;
                const score = calcularScore(parametro, valor);

                actualizarFeedback(parametro, valor, score);
                actualizarResumen();
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
            // Obtener el número de documento del paciente
            const numeroDocInput = document.getElementById('numero_documento');
            const numeroDoc = numeroDocInput ? numeroDocInput.value.trim() : '';

            if (!numeroDoc) {
                alert('Por favor, ingrese el número de documento del paciente para generar el PDF.');
                return;
            }

            // Buscar el paciente primero para obtener su ID
            try {
                const response = await fetch(`/meows/api/buscar-paciente/?documento=${encodeURIComponent(numeroDoc)}`);
                const data = await response.json();

                if (data.success && data.paciente && data.paciente.id) {
                    // Redirigir a la URL que genera el PDF (se descargará automáticamente)
                    const urlPdf = `/meows/pdf/${data.paciente.id}/`;
                    window.location.href = urlPdf;
                } else {
                    alert('No se encontró el paciente. Por favor, guarde primero una medición para este paciente antes de generar el PDF.');
                }
            } catch (error) {
                console.error('Error al buscar paciente para PDF:', error);
                alert('Error al generar el PDF. Por favor, intente nuevamente.');
            }
        });
    }
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializar);
} else {
    inicializar();
}

