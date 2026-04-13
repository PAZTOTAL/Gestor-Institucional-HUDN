// Configuración de la API
// La URL base se obtiene desde config.js (AppConfig.API_BASE_URL)
// Asegúrate de que config.js se cargue antes que main.js en el HTML
const API_BASE_URL = (typeof AppConfig !== 'undefined' && AppConfig.API_BASE_URL)
    ? AppConfig.API_BASE_URL
    : 'http://localhost:8000/api'; // Fallback por seguridad

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

function obtenerDatosFormulario() {
    return {
        codigo: document.getElementById('codigo').value,
        version: document.getElementById('version').value,
        fecha_elabora: document.getElementById('fecha_elabora').value,
        num_hoja: document.getElementById('num_hoja').value,
        estado: document.getElementById('estado').value,
        diagnostico: document.getElementById('diagnostico').value,
        edad_snapshot: document.getElementById('edad_snapshot').value,
        edad_gestion: document.getElementById('edad_gestion').value,
        n_controles_prenatales: document.getElementById('n_controles_prenatales').value,
        responsable: document.getElementById('responsable').value,
        paciente: document.getElementById('paciente_id').value,
        aseguradora: document.getElementById('aseguradora_id').value
    };
}

// El event listener del formulario está en el bloque DOMContentLoaded principal (línea ~337)


async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        },
        credentials: 'omit', // Para peticiones cross-origin
    };

    const csrfToken = getCSRFToken();
    if (csrfToken) {
        options.headers['X-CSRFToken'] = csrfToken;
    }

    if (data) {
        options.body = JSON.stringify(data);
    }

    // Agregar timestamp si no está presente en la URL para evitar caché
    let url = `${API_BASE_URL}${endpoint}`;
    if (method === 'GET' && !url.includes('?_=')) {
        url += (url.includes('?') ? '&' : '?') + '_=' + new Date().getTime();
    }
    console.log(`🌐 Haciendo petición ${method} a: ${url}`);
    if (data) {
        console.log('📤 Datos enviados:', data);
    }

    const response = await fetch(url, options);

    console.log(`Respuesta recibida: ${response.status} ${response.statusText}`);

    if (response.ok) {
        // Log exitoso para respuestas 200 OK
        console.log(`Petición exitosa: ${method} ${url} - Status: ${response.status}`);
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


// Cargar aseguradoras
async function cargarAseguradoras() {
    try {
        const aseguradoras = await apiRequest('/aseguradoras/');
        const select = document.getElementById('aseguradora_id');

        if (!select) return;

        // Limpiar opciones existentes (excepto la primera)
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }

        // Agregar aseguradoras
        aseguradoras.forEach(aseguradora => {
            const option = document.createElement('option');
            option.value = aseguradora.id;
            option.textContent = aseguradora.nombre;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error al cargar aseguradoras:', error);
        mostrarMensaje('Error al cargar aseguradoras', 'error');
    }
}

// Buscar paciente por número de identificación
// Función auxiliar para llenar el formulario con datos del paciente (detalle)
function llenarFormularioConPacientes(paciente) {
    if (!paciente) return;

    // Campos básicos
    if (document.getElementById('num_historia_clinica')) {
        document.getElementById('num_historia_clinica').value = paciente.num_historia_clinica || paciente.num_identificacion || '';
    }
    if (document.getElementById('num_identificacion')) {
        document.getElementById('num_identificacion').value = (paciente.num_identificacion || paciente.numero_documento || '');
    }
    if (document.getElementById('nombres')) {
        document.getElementById('nombres').value = (paciente.nombre_completo || paciente.nombres_raw || '');
    }
    // Tipo de Sangre
    if (document.getElementById('tipo_sangre') && paciente.tipo_sangre) {
        document.getElementById('tipo_sangre').value = paciente.tipo_sangre;
        console.log(`✅ Tipo de sangre: ${paciente.tipo_sangre}`);
    }

    // Aseguradora
    if (document.getElementById('aseguradora') && paciente.aseguradora) {
        document.getElementById('aseguradora').value = paciente.aseguradora;
        console.log(`✅ Aseguradora: ${paciente.aseguradora}`);
    }



    // Fechas y Edades
    const fechaElaboraPaciente = document.getElementById('fecha_elabora_paciente');
    if (fechaElaboraPaciente) {
        // En parto, este campo suele ser la fecha de nacimiento O la fecha de ingreso
        // Usaremos fecha de nacimiento si existe
        if (paciente.fecha_nacimiento) {
            fechaElaboraPaciente.value = paciente.fecha_nacimiento;
        } else {
            fechaElaboraPaciente.value = obtenerFechaLocalColombia();
        }
    }

    if (paciente.fecha_nacimiento || paciente.edad) {
        const edadSnapshotField = document.getElementById('edad_snapshot');
        if (edadSnapshotField) {
            let edad = paciente.edad;
            if (!edad && paciente.fecha_nacimiento) {
                edad = calcularEdad(paciente.fecha_nacimiento);
            }
            edadSnapshotField.value = edad || 0;
            console.log('Edad asignada:', edad);
        }
    }

    // Diagnóstico
    if (document.getElementById('diagnostico') && paciente.diagnostico) {
        document.getElementById('diagnostico').value = paciente.diagnostico;
        console.log(`✅ Diagnóstico cargado: ${paciente.diagnostico}`);
    }

    mostrarMensaje('Datos de paciente cargados correctamente', 'success');
}


async function buscarPaciente() {
    const numIdentificacion = document.getElementById('documento').value.trim(); // ID principal de búsqueda

    // Si está vacío, ABRIR MODAL
    if (!numIdentificacion) {
        abrirModalPacientesActivos();
        return;
    }

    try {
        console.log(`Realizando búsqueda detalle por identificación: ${numIdentificacion}`);
        // Usar nueva API de detalle
        const response = await apiRequest(`/paciente-detalle/?documento=${encodeURIComponent(numIdentificacion)}`);

        if (response && response.success && response.paciente) {
            console.log('📦 Datos del paciente detalle encontrados:', response.paciente);
            llenarFormularioConPacientes(response.paciente);
        } else {
            // Fallback al endpoint antiguo por si acaso
            console.warn('API detalle falló o no encontró, reintentando búsqueda simple...');
            const responseOld = await apiRequest(`/pacientes/?num_identificacion=${encodeURIComponent(numIdentificacion)}`);
            const pacientes = responseOld?.results || responseOld || [];
            const paciente = (pacientes && pacientes.length > 0) ? pacientes[0] : null;

            if (paciente) {
                // Adaptar formato antiguo a nuevo llenado
                llenarFormularioConPacientes({
                    ...paciente,
                    nombre_completo: paciente.nombres || paciente.nombre_completo,
                    num_identificacion: paciente.num_identificacion
                });
            } else {
                mostrarMensaje('Paciente no encontrado', 'info');
                limpiarFormulario(false); // false = no limpiar todo, dejar campos búsqueda
            }
        }
    } catch (error) {
        console.error('Error al buscar paciente:', error);
        mostrarMensaje('Error al buscar paciente: ' + error.message, 'error');
    }
}

// Lógica del Modal
async function abrirModalPacientesActivos() {
    const modal = document.getElementById('modal-pacientes-activos');
    const lista = document.getElementById('lista-pacientes-activos');
    const loading = document.getElementById('modal-loading');

    if (!modal) return;

    modal.style.display = 'block';
    if (loading) loading.style.display = 'block';
    if (lista) lista.innerHTML = '';

    try {
        const response = await apiRequest('/pacientes-activos/');
        if (loading) loading.style.display = 'none';

        if (response && response.success && response.pacientes && response.pacientes.length > 0) {
            response.pacientes.forEach(p => {
                const item = document.createElement('div');
                item.className = 'patient-item';
                item.style.padding = '10px';
                item.style.borderBottom = '1px solid #eee';
                item.style.cursor = 'pointer';
                item.innerHTML = `
                    <strong>${p.nombre_completo}</strong><br>
                    <small>Doc: ${p.documento} | Cama: ${p.cama || 'Sin asignar'}</small>
                `;
                item.onclick = function () {
                    const docInput = document.getElementById('documento');
                    if (docInput) docInput.value = p.documento;
                    modal.style.display = 'none';
                    buscarPaciente(); // Ejecutar búsqueda específica
                };
                lista.appendChild(item);
            });
        } else {
            lista.innerHTML = '<div style="padding:10px;">No hay pacientes activos en GINECO/OBSTETRICIA recientes.</div>';
        }
    } catch (e) {
        if (loading) loading.style.display = 'none';
        console.error(e);
        lista.innerHTML = '<div style="color:red; padding:10px;">Error cargando pacientes.</div>';
    }
}

// Cerrar modal y configurar eventos de búsqueda
document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('modal-pacientes-activos');
    const closeBtn = document.querySelector('.close-modal');

    // Configurar cierre del modal
    if (modal) {
        if (closeBtn) {
            closeBtn.onclick = function () {
                modal.style.display = 'none';
            }
        }
        window.onclick = function (event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
    }

    // Configurar búsqueda de paciente
    const btnBuscarPaciente = document.getElementById('btnBuscarPaciente');
    const inputDocumento = document.getElementById('documento');

    if (btnBuscarPaciente) {
        btnBuscarPaciente.addEventListener('click', buscarPaciente);
    }

    if (inputDocumento) {
        inputDocumento.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault(); // Prevenir submit del form
                buscarPaciente();
            }
        });
    }
});

// Crear o actualizar paciente
async function guardarPaciente() {
    console.log('Iniciando guardarPaciente...');

    const numHistoriaClinica = document.getElementById('num_historia_clinica')?.value;
    const numIdentificacion = document.getElementById('num_identificacion')?.value;
    const nombres = document.getElementById('nombres')?.value;

    // Validar campos requeridos
    if (!numHistoriaClinica || !numIdentificacion || !nombres) {
        const camposFaltantes = [];
        if (!numHistoriaClinica) camposFaltantes.push('N° Historia Clínica');
        if (!numIdentificacion) camposFaltantes.push('Identificación');
        if (!nombres) camposFaltantes.push('Nombre');
        throw new Error(`Campos de paciente requeridos faltantes: ${camposFaltantes.join(', ')}`);
    }

    const pacienteData = {
        num_historia_clinica: numHistoriaClinica,
        num_identificacion: numIdentificacion,
        nombres: nombres,
        tipo_sangre: document.getElementById('tipo_sangre')?.value || null,
        fecha_nacimiento: document.getElementById('fecha_elabora_paciente')?.value || null,
    };

    console.log('Datos del paciente a guardar:', pacienteData);

    const pacienteId = document.getElementById('paciente_id')?.value;
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
                document.getElementById('paciente_id').value = paciente.id;
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
    const formularioId = document.getElementById('formulario_id').value;

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

        const pacienteId = document.getElementById('paciente_id').value;
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
        const codigoInput = document.getElementById('codigo');
        const codigo = (codigoInput && codigoInput.value) ? codigoInput.value : 'FRSPA-022';

        const version = document.getElementById('version')?.value;
        const estado = document.getElementById('estado')?.value;
        const responsable = document.getElementById('responsable')?.value;

        // Validar campos requeridos
        // Nota: CÓDIGO ya se fuerza a un valor por defecto (FRSPA-022), por eso
        // solo validamos que versión, estado y responsable estén diligenciados.
        if (!version || !estado || !responsable) {
            const camposFaltantes = [];
            if (!version) camposFaltantes.push('Versión');
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
            fecha_elabora: document.getElementById('fecha_elabora')?.value || obtenerFechaLocalColombia(),
            num_hoja: parseInt(document.getElementById('num_hoja')?.value || '1'),
            paciente: pacienteId,
            aseguradora: document.getElementById('aseguradora_id')?.value || null,
            diagnostico: document.getElementById('diagnostico')?.value || null,
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
                document.getElementById('formulario_id').value = formulario.id;
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

        // Actualizar el ID del formulario en el campo oculto
        document.getElementById('formulario_id').value = formulario.id;

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

// Función para actualizar el formulario informativo (colapsable) con los datos guardados
// Ahora acepta datos directamente (datosCompletos) para evitar múltiples peticiones HTTP
async function actualizarFormularioInformativo(formularioId, datosCompletos = null) {
    try {
        console.log(`Actualizando formulario informativo para el formulario ${formularioId}...`);

        let formulario, mediciones, paciente;

        if (datosCompletos) {
            // Usar datos proporcionados directamente (desde endpoint consolidado)
            console.log('Usando datos consolidados proporcionados');
            formulario = datosCompletos.formulario;
            mediciones = datosCompletos.mediciones || [];
            paciente = datosCompletos.paciente;

            if (!formulario) {
                console.log('No se proporcionó formulario en los datos consolidados.');
                return;
            }
        } else {
            // Hacer peticiones HTTP individuales (compatibilidad retroativa)
            console.log('Obteniendo datos desde API individual');

            // Agregar timestamp para evitar caché del navegador
            const timestamp = new Date().getTime();

            // Obtener datos del formulario completo desde la API (sin caché)
            formulario = await apiRequest(`/formularios/${formularioId}/?_=${timestamp}`);
            console.log('Formulario recibido desde la API:', formulario);

            if (!formulario) {
                console.log('No se encontró el formulario.');
                return;
            }

            // Obtener mediciones desde la API (sin caché)
            mediciones = await apiRequest(`/formularios/${formularioId}/mediciones/?_=${timestamp}`);
            console.log('Mediciones recibidas desde la API:', mediciones);

            // Obtener datos completos del paciente desde la API (no usar caché)
            const pacienteId = formulario.paciente ? formulario.paciente.id : null;

            if (pacienteId) {
                try {
                    // Obtener datos completos del paciente desde la API (sin caché)
                    paciente = await apiRequest(`/pacientes/${pacienteId}/?_=${timestamp}`);
                    if (paciente) {
                        console.log('Datos completos del paciente obtenidos desde la API:', paciente);
                    } else {
                        // Fallback: usar datos del formulario si no se puede obtener el paciente
                        paciente = formulario.paciente;
                        console.warn('No se pudieron obtener los datos completos del paciente, usando datos del formulario');
                    }
                } catch (error) {
                    console.error('Error al obtener datos del paciente:', error);
                    // Fallback: usar datos del formulario
                    paciente = formulario.paciente;
                }
            } else {
                // Si no hay ID de paciente, usar los datos del formulario
                paciente = formulario.paciente;
            }
        }

        // Obtener el contenedor del formulario informativo
        const collapsibleBody = document.querySelector('.collapsible-body');
        if (!collapsibleBody) {
            console.log('No se encontró el contenedor del formulario informativo.');
            return;
        }

        if (paciente) {
            const patientTable = collapsibleBody.querySelector('.patient-table');

            if (patientTable) {
                const rows = patientTable.querySelectorAll('tr');

                // Primera fila: DD/MM/AA, ASEGURADORA, N° HISTORIA CLÍNICA
                if (rows.length > 0) {
                    const cells = rows[0].querySelectorAll('td');
                    if (cells.length > 1) {
                        // DD/MM/AA - Usar fecha_elabora del formulario o fecha_nacimiento del paciente
                        const fechaSpan = cells[1].querySelector('.info-value');
                        if (fechaSpan) {
                            const fecha = formulario.fecha_elabora || paciente.fecha_nacimiento || new Date();
                            const fechaObj = new Date(fecha);
                            fechaSpan.textContent = fechaObj.toLocaleDateString('es-ES', {
                                day: '2-digit',
                                month: '2-digit',
                                year: 'numeric'
                            });
                        }
                    }
                    if (cells.length > 3) {
                        // ASEGURADORA
                        const aseguradoraSpan = cells[3].querySelector('.info-value');
                        if (aseguradoraSpan) {
                            aseguradoraSpan.textContent = formulario.aseguradora ? (formulario.aseguradora.nombre || '-') : '-';
                        }
                    }
                    if (cells.length > 5) {
                        // N° HISTORIA CLÍNICA
                        const historiaSpan = cells[5].querySelector('.info-value');
                        if (historiaSpan) {
                            historiaSpan.textContent = paciente.num_historia_clinica || '-';
                        }
                    }
                }

                // Segunda fila: CC. IDENTIFICACIÓN, NOMBRE Y APELLIDO
                if (rows.length > 1) {
                    const cells = rows[1].querySelectorAll('td');
                    if (cells.length > 1) {
                        // CC. IDENTIFICACIÓN
                        const identSpan = cells[1].querySelector('.info-value');
                        if (identSpan) {
                            identSpan.textContent = paciente.num_identificacion || '-';
                        }
                    }
                    if (cells.length > 3) {
                        // NOMBRE Y APELLIDO
                        const nombreSpan = cells[3].querySelector('.info-value');
                        if (nombreSpan) {
                            nombreSpan.textContent = paciente.nombres || '-';
                        }
                    }
                }

                // Tercera fila: DIAGNÓSTICO, EDAD, GRUPO SANGUÍNEO
                if (rows.length > 2) {
                    const cells = rows[2].querySelectorAll('td');
                    if (cells.length > 1) {
                        // DIAGNÓSTICO
                        const diagSpan = cells[1].querySelector('.info-value');
                        if (diagSpan) {
                            diagSpan.textContent = formulario.diagnostico || '-';
                        }
                    }
                    if (cells.length > 3) {
                        // EDAD - Calcular desde fecha_nacimiento si está disponible
                        const edadSpan = cells[3].querySelector('.info-value');
                        if (edadSpan) {
                            let edad = formulario.edad_snapshot;
                            if (!edad && paciente.fecha_nacimiento) {
                                edad = calcularEdad(paciente.fecha_nacimiento);
                            }
                            edadSpan.textContent = edad || '-';
                        }
                    }
                    if (cells.length > 5) {
                        // GRUPO SANGUÍNEO
                        const sangreSpan = cells[5].querySelector('.info-value');
                        if (sangreSpan) {
                            sangreSpan.textContent = paciente.tipo_sangre || '-';
                        }
                    }
                }

                // Cuarta fila: EDAD GESTACIONAL, G_P_C_A_V_M_, N° CONTROLES PRENATALES
                if (rows.length > 3) {
                    const cells = rows[3].querySelectorAll('td');
                    if (cells.length > 1) {
                        // EDAD GESTACIONAL
                        const edadGestSpan = cells[1].querySelector('.info-value');
                        if (edadGestSpan) {
                            edadGestSpan.textContent = (formulario.edad_gestion !== null && formulario.edad_gestion !== undefined) ? formulario.edad_gestion : '-';
                        }
                    }
                    if (cells.length > 3) {
                        // G_P_C_A_V_M_
                        const estadoSpan = cells[3].querySelector('.info-value');
                        if (estadoSpan) {
                            estadoSpan.textContent = formulario.estado_display || formulario.estado || '-';
                        }
                    }
                    if (cells.length > 5) {
                        // N° CONTROLES PRENATALES
                        const controlesSpan = cells[5].querySelector('.info-value');
                        if (controlesSpan) {
                            controlesSpan.textContent = (formulario.n_controles_prenatales !== null && formulario.n_controles_prenatales !== undefined) ? formulario.n_controles_prenatales : '-';
                        }
                    }
                }
            }
        }

        // Actualizar responsable
        if (formulario.responsable) {
            const responsableInfo = collapsibleBody.querySelector('.form-footer .info-value');
            if (responsableInfo) {
                responsableInfo.textContent = formulario.responsable;
            }
        }

        // Actualizar tabla de mediciones en el formulario informativo
        if (mediciones && mediciones.length > 0) {
            // 1. Identificar todas las horas únicas y ordenarlas
            const horasUnicas = [...new Set(mediciones.map(m => m.tomada_en))].sort();
            console.log('Horas detectadas:', horasUnicas);

            // 2. Llenar los spans de tiempo en el encabezado del grid informativo
            const timeSpans = collapsibleBody.querySelectorAll('.info-time');
            const horaToIndexMap = {};

            // Primero limpiar todas las fechas predeterminadas
            timeSpans.forEach(span => {
                span.textContent = '';
            });

            // Luego llenar solo las fechas que tienen datos guardados desde la base de datos
            horasUnicas.forEach((hora, index) => {
                if (index < timeSpans.length) {
                    const date = new Date(hora);
                    const fechaHora = date.toLocaleString('es-ES', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: true
                    });
                    timeSpans[index].textContent = fechaHora;
                    horaToIndexMap[hora] = index;
                }
            });

            // 2.5. Generar dinámicamente las filas de la tabla de mediciones si no existen
            const medicionesBody = collapsibleBody.querySelector('#mediciones-informativa-body');
            if (medicionesBody) {
                // Obtener parámetros únicos de las mediciones
                const parametrosMap = new Map();

                mediciones.forEach(medicion => {
                    const parametroId = medicion.parametro ? medicion.parametro.id : null;
                    const parametroNombre = medicion.parametro ? medicion.parametro.nombre : 'PARÁMETRO DESCONOCIDO';

                    if (parametroId && !parametrosMap.has(parametroId)) {
                        // Agrupar campos por parámetro
                        const camposMap = new Map();
                        medicion.valores.forEach(v => {
                            const campoId = v.campo ? v.campo.id : null;
                            const campoNombre = v.campo ? v.campo.nombre : '';
                            if (campoId && !camposMap.has(campoId)) {
                                camposMap.set(campoId, campoNombre);
                            }
                        });

                        parametrosMap.set(parametroId, {
                            nombre: parametroNombre,
                            campos: Array.from(camposMap.entries()).map(([id, nombre]) => ({ id, nombre }))
                        });
                    }
                });

                // Si no hay filas, generarlas dinámicamente
                if (medicionesBody.children.length === 0) {
                    parametrosMap.forEach((parametro, parametroId) => {
                        parametro.campos.forEach((campo, campoIndex) => {
                            const row = document.createElement('tr');

                            // Columna de parámetro (solo en la primera fila de cada parámetro)
                            if (campoIndex === 0) {
                                const paramCell = document.createElement('td');
                                paramCell.className = 'param-name';
                                paramCell.setAttribute('data-parametro-id', parametroId);
                                paramCell.textContent = parametro.nombre.toUpperCase();
                                if (parametro.campos.length > 1) {
                                    paramCell.setAttribute('rowspan', parametro.campos.length);
                                }
                                row.appendChild(paramCell);
                            }

                            // Columna de campo (si hay múltiples campos)
                            if (parametro.campos.length > 1) {
                                const campoCell = document.createElement('td');
                                campoCell.className = 'campo-name';
                                campoCell.textContent = campo.nombre;
                                row.appendChild(campoCell);
                            }

                            // Celdas de datos para cada hora (12 columnas)
                            for (let horaIndex = 0; horaIndex < 12; horaIndex++) {
                                const dataCell = document.createElement('td');
                                dataCell.className = 'data-cell';

                                const valueSpan = document.createElement('span');
                                valueSpan.className = 'info-value';
                                valueSpan.setAttribute('data-parametro-id', parametroId);
                                valueSpan.setAttribute('data-campo-id', campo.id);
                                valueSpan.setAttribute('data-hora-index', horaIndex);
                                valueSpan.textContent = '-';

                                dataCell.appendChild(valueSpan);
                                row.appendChild(dataCell);
                            }

                            medicionesBody.appendChild(row);
                        });
                    });
                }
            }

            // 3. Limpiar valores informativos antes de cargar
            collapsibleBody.querySelectorAll('.data-cell .info-value').forEach(span => {
                span.textContent = '-';
            });

            // 4. Llenar los valores en las celdas informativas
            mediciones.forEach(medicion => {
                const horaIndex = horaToIndexMap[medicion.tomada_en];
                if (horaIndex === undefined) return;

                const parametroId = medicion.parametro ? medicion.parametro.id : null;
                if (!parametroId) return;

                medicion.valores.forEach(v => {
                    const campoId = v.campo ? v.campo.id : null;
                    if (!campoId) return;

                    const selector = `.info-value[data-parametro-id="${parametroId}"][data-campo-id="${campoId}"][data-hora-index="${horaIndex}"]`;
                    const span = collapsibleBody.querySelector(selector);

                    if (span) {
                        // Obtener el valor no nulo y formatearlo
                        // Priorizar valor_text sobre valor_number (para compatibilidad con datos antiguos)
                        let valor = '-';
                        let valorAsignado = false;

                        if (v.valor_text !== null && v.valor_text !== undefined) {
                            valor = v.valor_text;

                            // Si es un campo de tiempo (parametro-id="17", campo-id="19" o parametro-id="14", campo-id="18"), convertir a formato 12 horas
                            if ((parametroId == 17 && campoId == 19) || (parametroId == 14 && campoId == 18)) {
                                // El valor viene en formato "HH:MM" (24 horas), convertir a formato 12 horas
                                const horaMatch = valor.match(/^(\d{1,2}):(\d{2})$/);
                                if (horaMatch) {
                                    let horas = parseInt(horaMatch[1]);
                                    const minutos = horaMatch[2];
                                    const ampm = horas >= 12 ? 'p. m.' : 'a. m.';
                                    horas = horas % 12;
                                    horas = horas ? horas : 12; // Si es 0, mostrar 12
                                    valor = `${horas.toString().padStart(2, '0')}:${minutos} ${ampm}`;
                                }
                            }
                        } else if (v.valor_number !== null && v.valor_number !== undefined) {
                            // Compatibilidad con datos antiguos que puedan estar en valor_number
                            valor = parseFloat(v.valor_number);
                            if (Number.isInteger(valor)) valor = parseInt(valor);
                            valor = valor.toString();
                        } else if (v.valor_boolean !== null && v.valor_boolean !== undefined) {
                            // Para campos booleanos, convertir a texto
                            valor = v.valor_boolean ? 'SÍ' : 'NO';
                        } else if (v.valor_json !== null && v.valor_json !== undefined) {
                            valor = JSON.stringify(v.valor_json);
                        }

                        // Buscar el select correspondiente en el formulario principal para obtener el texto de la opción
                        // Esto asegura que se muestre el mismo valor que en el grid principal
                        const selectSelector = `.data-input[data-parametro-id="${parametroId}"][data-campo-id="${campoId}"][data-hora-index="${horaIndex}"]`;
                        const selectInput = document.querySelector(selectSelector);

                        if (selectInput && selectInput.tagName === 'SELECT' && valor !== '' && valor !== '-') {
                            const opciones = Array.from(selectInput.options);

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
                                    valor = opcionEncontrada.textContent || opcionEncontrada.value;
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
                                    // Usar el texto de la opción en lugar del valor
                                    valor = opcionEncontrada.textContent || opcionEncontrada.value;
                                    valorAsignado = true;
                                }
                            }
                        }

                        // Asegurar que el valor no esté vacío
                        if (valor === '' || valor === null || valor === undefined) {
                            valor = '-';
                        }

                        span.textContent = valor;
                    }
                });
            });
        }

        console.log('Formulario informativo actualizado con éxito.');
    } catch (error) {
        console.error('Error al actualizar formulario informativo:', error);
        // No mostrar mensaje de error al usuario, solo log
    }
}

// Guardar mediciones con envío anidado
async function guardarMediciones(formularioId) {
    const timeInputs = document.querySelectorAll('.time-input');
    const dataInputs = document.querySelectorAll('.data-input');
    const horas = Array.from(timeInputs).map(input => input.value);

    const medicionesMap = new Map();

    dataInputs.forEach(input => {
        const parametroId = input.getAttribute('data-parametro-id');
        const campoId = input.getAttribute('data-campo-id');
        const horaIndex = parseInt(input.getAttribute('data-hora-index'));
        const tipoValor = input.getAttribute('data-tipo-valor');
        const valor = input.value.trim();

        if (!valor || !parametroId || !horas[horaIndex]) return;

        const key = `${parametroId}-${horaIndex}`;
        if (!medicionesMap.has(key)) {
            medicionesMap.set(key, {
                formulario: formularioId,
                parametro: parseInt(parametroId),
                tomada_en: new Date(horas[horaIndex]).toISOString(),
                valores: []
            });
        }

        const payloadValor = { campo_id: parseInt(campoId) };
        if (tipoValor === 'number') {
            // Guardar todos los valores numéricos como texto en valor_text
            payloadValor.valor_text = valor;
        }
        else if (tipoValor === 'text') payloadValor.valor_text = valor;
        else if (tipoValor === 'boolean') {
            // Manejar valores booleanos que pueden ser "Sí", "SÍ", o valores que comienzan con "Sí" o "No"
            const valorUpper = valor.toUpperCase().trim();
            payloadValor.valor_boolean = valorUpper.startsWith('SÍ') || valorUpper.startsWith('SI');
        }

        medicionesMap.get(key).valores.push(payloadValor);
    });

    // Enviar todas las mediciones (cada una con sus valores anidados)
    const promesas = Array.from(medicionesMap.values()).map(data =>
        apiRequest('/mediciones/', 'POST', data)
    );

    await Promise.all(promesas);
    console.log('Todas las mediciones anidadas se han procesado.');
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

        // Verificar si hay datos en caché para este paciente
        if (usarCache) {
            try {
                const cacheData = localStorage.getItem(cacheKey);
                if (cacheData) {
                    const parsedCache = JSON.parse(cacheData);
                    // Verificar si la caché es para el mismo paciente
                    if (parsedCache.paciente && parsedCache.paciente.num_identificacion === cedula) {
                        console.log(`✅ Datos encontrados en caché para paciente: ${cedula}`);
                        console.log('Usando datos de caché (evitando petición HTTP)');
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

        if (!data || !data.paciente) {
            console.log('Paciente no encontrado');
            // Si no se encuentra, limpiar la caché
            localStorage.removeItem(cacheKey);
            return null;
        }

        // Guardar TODA la data completa en caché
        try {
            const cacheData = {
                paciente: data.paciente,
                formulario: data.formulario,
                mediciones: data.mediciones || [],
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
                    paciente: data.paciente,
                    formulario: null, // No guardar formulario si es muy grande
                    mediciones: [], // No guardar mediciones si es muy grande
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

        console.log('Datos completos recibidos desde API:', data);
        return data;
    } catch (error) {
        console.error('Error al buscar paciente completo:', error);
        // En caso de error, limpiar caché
        localStorage.removeItem('paciente_completo_data_cache');
        throw error;
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

// Limpiar todos los campos del formulario y el grid
function limpiarFormulario() {
    console.log('🧹 Limpiando campos del formulario...');

    // Limpiar caché del paciente al limpiar el formulario
    limpiarPacienteCache();

    // IDs de campos a limpiar (excluyendo el de búsqueda si se desea)
    const camposALimpiar = [
        'paciente_id', 'formulario_id', 'num_historia_clinica',
        'nombres', 'tipo_sangre', 'fecha_elabora_paciente',
        'diagnostico', 'edad_snapshot', 'edad_gestion',
        'n_controles_prenatales', 'responsable', 'aseguradora_id'
    ];

    camposALimpiar.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });

    // Restablecer fecha actual en fecha_elabora_paciente después de limpiar
    const fechaElaboraPaciente = document.getElementById('fecha_elabora_paciente');
    if (fechaElaboraPaciente) {
        const hoy = obtenerFechaLocalColombia();
        fechaElaboraPaciente.value = hoy;
    }

    // Desbloquear todas las columnas antes de limpiar
    desbloquearTodasLasColumnas();

    // Limpiar el grid de datos
    document.querySelectorAll('.data-input').forEach(input => {
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

// Inicialización
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM cargado, inicializando aplicación...');

    // Cargar aseguradoras al iniciar
    cargarAseguradoras();

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
        fechaNacimientoInput.addEventListener('change', function () {
            if (this.value) {
                edadInput.value = calcularEdad(this.value);
                console.log(`🎂 Edad recalculada manualmente: ${edadInput.value}`);
            }
        });
    }

    // Búsqueda de paciente por número de identificación con botón
    const btnBuscarPacienteCedula = document.getElementById('btn-buscar-paciente-cedula');
    const numIdentificacionInput = document.getElementById('num_identificacion');

    if (btnBuscarPacienteCedula && numIdentificacionInput) {
        btnBuscarPacienteCedula.addEventListener('click', async function () {
            const cedula = numIdentificacionInput.value.trim();
            if (!cedula) {
                mostrarMensaje('Por favor ingrese un número de identificación', 'error');
                return;
            }

            // Deshabilitar el botón mientras se busca
            btnBuscarPacienteCedula.disabled = true;
            btnBuscarPacienteCedula.textContent = 'Buscando...';

            // Limpiar el formulario antes de la nueva búsqueda
            limpiarFormulario();
            // Restaurar el valor de búsqueda
            numIdentificacionInput.value = cedula;

            console.log(`Iniciando búsqueda consolidada para identificación: ${cedula}`);
            try {
                // Usar endpoint consolidado que trae paciente, formulario y mediciones en una sola petición
                const data = await buscarPacienteCompleto(cedula);

                if (!data || !data.paciente) {
                    mostrarMensaje('Paciente no encontrado', 'info');
                    console.log('No se encontró paciente con ese número de identificación');

                    // Limpiar formulario excepto el campo de búsqueda
                    limpiarFormulario();
                    document.getElementById('num_identificacion').value = cedula;
                    return;
                }

                const paciente = data.paciente;
                console.log('Paciente encontrado:', paciente);
                console.log('Campos del paciente:', {
                    id: paciente.id,
                    num_identificacion: paciente.num_identificacion,
                    num_historia_clinica: paciente.num_historia_clinica,
                    nombres: paciente.nombres,
                    fecha_nacimiento: paciente.fecha_nacimiento,
                    tipo_sangre: paciente.tipo_sangre
                });

                // Guardar el ID del paciente en un campo oculto
                let pacienteIdField = document.getElementById('paciente_id');
                if (!pacienteIdField) {
                    pacienteIdField = document.createElement('input');
                    pacienteIdField.type = 'hidden';
                    pacienteIdField.id = 'paciente_id';
                    pacienteIdField.name = 'paciente_id';
                    document.getElementById('formulario-clinico').appendChild(pacienteIdField);
                }
                pacienteIdField.value = paciente.id;

                // Completar campos del formulario (solo los que existen en el modelo Paciente)
                if (document.getElementById('num_identificacion')) {
                    document.getElementById('num_identificacion').value = paciente.num_identificacion || '';
                    console.log('Campo num_identificacion llenado:', paciente.num_identificacion);
                }
                if (document.getElementById('num_historia_clinica')) {
                    document.getElementById('num_historia_clinica').value = paciente.num_historia_clinica || '';
                    console.log('Campo num_historia_clinica llenado:', paciente.num_historia_clinica);
                }
                if (document.getElementById('nombres')) {
                    document.getElementById('nombres').value = paciente.nombres || '';
                    console.log('Campo nombres llenado:', paciente.nombres);
                }
                if (document.getElementById('tipo_sangre') && paciente.tipo_sangre) {
                    document.getElementById('tipo_sangre').value = paciente.tipo_sangre;
                    console.log('Campo tipo_sangre llenado:', paciente.tipo_sangre);
                }
                const fechaElaboraPaciente = document.getElementById('fecha_elabora_paciente');
                if (fechaElaboraPaciente) {
                    const hoy = obtenerFechaLocalColombia();
                    // Usar fecha_nacimiento del paciente si existe, sino usar fecha actual
                    fechaElaboraPaciente.value = paciente.fecha_nacimiento || hoy;
                    console.log('Campo fecha_elabora_paciente llenado:', fechaElaboraPaciente.value);
                }
                if (document.getElementById('edad_snapshot') && paciente.fecha_nacimiento) {
                    const edad = calcularEdad(paciente.fecha_nacimiento);
                    document.getElementById('edad_snapshot').value = edad;
                    console.log('Campo edad_snapshot calculado y llenado:', edad);
                }

                // Procesar formulario si existe (datos ya vienen en la respuesta consolidada)
                if (data.formulario) {
                    const formulario = data.formulario;
                    console.log('Formulario existente encontrado:', formulario);

                    // Guardar ID del formulario
                    document.getElementById('formulario_id').value = formulario.id;

                    // Llenar campos del formulario
                    if (document.getElementById('codigo')) {
                        document.getElementById('codigo').value = formulario.codigo || '';
                    }
                    if (document.getElementById('num_hoja')) {
                        document.getElementById('num_hoja').value = formulario.num_hoja || '';
                    }
                    if (document.getElementById('estado')) {
                        document.getElementById('estado').value = formulario.estado || '';
                    }
                    if (document.getElementById('diagnostico')) {
                        document.getElementById('diagnostico').value = formulario.diagnostico || '';
                    }
                    if (document.getElementById('edad_gestion')) {
                        document.getElementById('edad_gestion').value = formulario.edad_gestion || '';
                    }
                    if (document.getElementById('n_controles_prenatales')) {
                        document.getElementById('n_controles_prenatales').value = formulario.n_controles_prenatales || '';
                    }
                    if (document.getElementById('responsable')) {
                        document.getElementById('responsable').value = formulario.responsable || '';
                    }
                    if (document.getElementById('aseguradora_id') && formulario.aseguradora) {
                        document.getElementById('aseguradora_id').value = formulario.aseguradora.id || '';
                    }

                    // Cargar mediciones en el grid usando datos consolidados (evita petición HTTP)
                    await cargarMedicionesEnGrid(formulario.id, data.mediciones || []);

                    // Actualizar formulario informativo usando datos consolidados (evita múltiples peticiones HTTP)
                    await actualizarFormularioInformativo(formulario.id, data);

                    // Cambiar botón a "Actualizar"
                    actualizarTextoBoton(true);
                    mostrarMensaje('Datos encontrados', 'success');
                } else {
                    // No hay formulario, mantener botón en "Guardar"
                    actualizarTextoBoton(false);
                    mostrarMensaje('Paciente encontrado', 'success');
                }

                console.log(`Paciente encontrado:`, paciente);
            } catch (error) {
                console.error('Error al buscar paciente:', error);
                mostrarMensaje('Error al buscar paciente: ' + error.message, 'error');
            } finally {
                // Rehabilitar el botón
                btnBuscarPacienteCedula.disabled = false;
                btnBuscarPacienteCedula.textContent = '🔍 Buscar';
            }
        });

        // También permitir búsqueda con Enter en el campo
        numIdentificacionInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                btnBuscarPacienteCedula.click();
            }
        });
    }

    // Búsqueda automática de paciente por número de identificación (al perder foco)
    if (numIdentificacionInput) {
        numIdentificacionInput.addEventListener('blur', async function () {
            const cedula = this.value.trim();
            if (!cedula) return;

            // Limpiar formulario antes de la búsqueda automática
            // pero mantenemos el valor del input que lanzó el blur
            const currentCedula = this.value;
            limpiarFormulario();
            this.value = currentCedula;

            console.log(`Iniciando petición de búsqueda para identificación: ${cedula}`);
            try {
                const pacientes = await apiRequest(`/pacientes/?num_identificacion=${cedula}`);
                console.log('Respuesta de búsqueda por identificación:', pacientes);

                if (pacientes && pacientes.length > 0) {
                    const paciente = pacientes[0];
                    console.log('Paciente cargado:', paciente);

                    // Guardar el ID del paciente en un campo oculto
                    let pacienteIdField = document.getElementById('paciente_id');
                    if (!pacienteIdField) {
                        pacienteIdField = document.createElement('input');
                        pacienteIdField.type = 'hidden';
                        pacienteIdField.id = 'paciente_id';
                        pacienteIdField.name = 'paciente_id';
                        document.getElementById('formulario-clinico').appendChild(pacienteIdField);
                    }
                    pacienteIdField.value = paciente.id;

                    // Completar campos del formulario
                    if (document.getElementById('num_historia_clinica')) {
                        document.getElementById('num_historia_clinica').value = paciente.num_historia_clinica || '';
                    }
                    if (document.getElementById('nombres')) {
                        document.getElementById('nombres').value = paciente.nombres || '';
                    }
                    if (document.getElementById('tipo_sangre')) {
                        document.getElementById('tipo_sangre').value = paciente.tipo_sangre || '';
                    }
                    const fechaElaboraPaciente = document.getElementById('fecha_elabora_paciente');
                    if (fechaElaboraPaciente) {
                        const hoy = obtenerFechaLocalColombia();
                        fechaElaboraPaciente.value = paciente.fecha_nacimiento || hoy;
                    }
                    if (document.getElementById('edad_snapshot') && paciente.fecha_nacimiento) {
                        const edad = calcularEdad(paciente.fecha_nacimiento);
                        document.getElementById('edad_snapshot').value = edad;
                    }

                    // Buscar formulario existente para este paciente
                    const formularioExistente = await buscarFormularioExistente(paciente.id, cedula);
                    if (formularioExistente) {
                        console.log('Formulario existente encontrado:', formularioExistente);
                        document.getElementById('formulario_id').value = formularioExistente.id;
                        // Cargar datos del formulario
                        await cargarMedicionesEnGrid(formularioExistente.id);
                        // Actualizar el formulario informativo con los datos cargados
                        await actualizarFormularioInformativo(formularioExistente.id);
                        // Cambiar botón a "Actualizar"
                        actualizarTextoBoton(true);
                        mostrarMensaje('Datos encontrados', 'info');
                    } else {
                        // No hay formulario, mantener botón en "Guardar"
                        actualizarTextoBoton(false);
                    }

                    console.log(`Paciente encontrado: ${paciente.nombres}`);
                } else {
                    console.log('No se encontró paciente con ese número de identificación');
                    // Limpiar formulario excepto el campo de búsqueda
                    limpiarFormulario();
                    document.getElementById('num_identificacion').value = cedula;
                }
            } catch (error) {
                console.error('Error al buscar paciente:', error);
            }
        });
    }

    // Event listeners
    const btnBuscarPacienteOld = document.getElementById('btn-buscar-paciente');
    if (btnBuscarPacienteOld) {
        btnBuscarPacienteOld.addEventListener('click', buscarPaciente);
    }

    const formulario = document.getElementById('formulario-clinico');
    if (formulario) {
        console.log('Formulario encontrado, registrando event listener para submit...');

        formulario.addEventListener('submit', async function (e) {
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
                    const formularioId = document.getElementById('formulario_id').value;
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
        btnGuardar.addEventListener('click', async function (e) {
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
                const formularioId = document.getElementById('formulario_id').value;
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
    // Función compartida para buscar por documento
    async function buscarPorDocumento(documento) {
        if (!documento) return; // Retorno silencioso si está vacío

        // Limpiar formulario antes de buscar (opcional, dependiendo del flujo deseado)
        // limpiarFormulario(); 

        const documentoInput = document.getElementById('documento');
        if (documentoInput && documentoInput.value !== documento) {
            documentoInput.value = documento;
        }

        try {
            console.log(`Buscando por documento: ${documento}`);
            // Usar el endpoint robusto que busca en externa y local
            const response = await apiRequest(`/paciente-detalle/?documento=${encodeURIComponent(documento)}`);

            if (response && response.success && response.paciente) {
                console.log("Paciente encontrado:", response.paciente);
                llenarFormularioConPacientes(response.paciente);
                mostrarMensaje("Datos del paciente cargados", "success");
            } else {
                mostrarMensaje("Paciente no encontrado", "info");
                // limpiarFormulario(false);
            }
        } catch (error) {
            console.error("Error al buscar por documento:", error);
            // El mensaje de error detallado ya lo muestra apiRequest si falla, 
            // pero si queremos uno genérico aquí:
            // mostrarMensaje("Error al buscar datos", "error");
        }
    }

    // Función auxiliar para llenar el formulario con datos del paciente
    function llenarFormularioConPacientes(paciente) {
        if (!paciente) return;

        console.log("Llenando formulario con:", paciente);

        if (document.getElementById('paciente_id')) {
            document.getElementById('paciente_id').value = paciente.id || '';
        }
        if (document.getElementById('num_historia_clinica')) {
            document.getElementById('num_historia_clinica').value = paciente.num_historia_clinica || paciente.num_identificacion || '';
        }
        if (document.getElementById('num_identificacion')) {
            document.getElementById('num_identificacion').value = paciente.num_identificacion || '';
        }
        if (document.getElementById('nombres')) {
            // Unificar nombres si vienen separados o juntos
            let nombreCompleto = paciente.nombre_completo || ((paciente.nombres || '') + ' ' + (paciente.apellidos || '')).trim();
            document.getElementById('nombres').value = nombreCompleto;
        }
        if (document.getElementById('tipo_sangre') && paciente.tipo_sangre) {
            document.getElementById('tipo_sangre').value = paciente.tipo_sangre;
        }

        // Diagnóstico (Validar que exista el campo)
        if (document.getElementById('diagnostico')) {
            document.getElementById('diagnostico').value = paciente.diagnostico || '';
        }

        // Aseguradora
        if (document.getElementById('aseguradora_id') && paciente.aseguradora) {
            // Si es un select, habría que ver si el valor coincide, o si es un input text
            // Asumimos input text por ahora o asignamos valor si hace match
            document.getElementById('aseguradora_id').value = paciente.aseguradora;
        }

        // Fecha Nacimiento / Elabora Paciente
        const fechaElaboraPaciente = document.getElementById('fecha_elabora_paciente');
        if (fechaElaboraPaciente) {
            fechaElaboraPaciente.value = paciente.fecha_nacimiento || obtenerFechaLocalColombia();
        }

        // Calcular Edad Gestacional si hay datos (snapshot)
        // ... (logica adicional si se requiere)
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
            const numIdentificacion = document.getElementById('num_identificacion')?.value;
            if (!numIdentificacion) {
                mostrarMensaje('No hay paciente seleccionado para generar PDF', 'error');
                return null;
            }

            const cacheData = obtenerPacienteCache(numIdentificacion);
            if (!cacheData || !cacheData.paciente) {
                console.log('No hay datos en caché, obteniendo desde API...');
                // Si no hay caché, obtener datos
                const data = await buscarPacienteCompleto(numIdentificacion, false);
                if (!data || !data.paciente) {
                    mostrarMensaje('No se encontraron datos del paciente', 'error');
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
            // Intentar cargar el template desde el servidor frontend
            // Probar diferentes rutas posibles
            const rutasPosibles = [
                '/templates/clinico/impresion_formulario.html',
                'templates/clinico/impresion_formulario.html',
                '../templates/clinico/impresion_formulario.html',
                './templates/clinico/impresion_formulario.html'
            ];

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

            throw new Error('No se pudo cargar el template desde ninguna ruta');
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
            'LOGO_ACREDITACION': '/static/img/logo_acreditacion.png'
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
    </div>
</body>
</html>
        `;

        return html;
    }

    // Función para descargar PDF usando datos de caché
    async function descargarPDF(pacienteId, formularioId) {
        console.log('Preparando vista de impresión desde caché...');

        try {
            // Obtener datos desde caché
            const data = await generarHTMLPDFDesdeCache();

            if (!data || !data.paciente) {
                mostrarMensaje('No hay datos del paciente disponibles', 'error');
                return;
            }

            if (!data.formulario) {
                mostrarMensaje('No hay formulario para imprimir. Debe guardar un formulario primero.', 'error');
                return;
            }

            // Generar HTML del PDF
            const htmlPDF = await generarHTMLPDF(data);

            if (!htmlPDF) {
                mostrarMensaje('Error al generar HTML del PDF', 'error');
                return;
            }

            // Abrir nueva ventana con el HTML
            const ventanaPDF = window.open('', '_blank');
            if (!ventanaPDF) {
                mostrarMensaje('Por favor, permite ventanas emergentes para generar el PDF', 'error');
                return;
            }

            ventanaPDF.document.write(htmlPDF);
            ventanaPDF.document.close();

            console.log('✅ PDF generado desde caché y abierto en nueva ventana');

        } catch (error) {
            console.error('Error al generar PDF desde caché:', error);
            mostrarMensaje('Error al generar PDF: ' + error.message, 'error');

            // Fallback: usar método anterior si falla
            console.log('Intentando método alternativo...');
            const formularioIdEl = document.getElementById('formulario_id');
            const formularioId = formularioIdEl ? formularioIdEl.value : null;

            if (formularioId) {
                window.open(`/formulario/${formularioId}/impresion/`, '_blank');
            } else {
                const pacienteIdEl = document.getElementById('paciente_id');
                const pacienteId = pacienteIdEl ? pacienteIdEl.value : null;
                if (pacienteId) {
                    window.open(`/pacientes/${pacienteId}/pdf/`, '_blank');
                }
            }
        }
    }

    // Hacer la función disponible globalmente para el botón del HTML
    window.descargarPDF = descargarPDF;

    console.log('Inicialización finalizada correctamente');
});

