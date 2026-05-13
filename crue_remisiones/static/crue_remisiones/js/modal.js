/**
 * modal.js — Lógica del modal de creación / edición / clonación de remisiones.
 *
 * Requisitos: 5.2, 5.3, 6.1, 8.1, 8.2, 8.3, 8.4
 */

'use strict';

// ─── Helpers ────────────────────────────────────────────────────────────────

/** Devuelve la fecha/hora actual en formato datetime-local (YYYY-MM-DDTHH:MM). */
function ahora() {
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Limpia todos los errores inline del formulario. */
function limpiarErrores() {
  document.querySelectorAll('#form-remision .invalid-feedback').forEach(el => {
    el.textContent = '';
  });
  document.querySelectorAll('#form-remision .is-invalid').forEach(el => {
    el.classList.remove('is-invalid');
  });
  const alertaErrores = document.getElementById('modal-errores');
  if (alertaErrores) {
    alertaErrores.classList.add('d-none');
    alertaErrores.textContent = '';
  }
}

/** Muestra errores de validación del servidor en los campos correspondientes. */
function mostrarErrores(errors) {
  const alertaErrores = document.getElementById('modal-errores');
  const mensajes = [];

  for (const [campo, lista] of Object.entries(errors)) {
    const errMsg = Array.isArray(lista) ? lista.join(' ') : String(lista);
    const inputEl = document.getElementById('id_' + campo);
    const errEl = document.getElementById('err-' + campo);
    if (inputEl) inputEl.classList.add('is-invalid');
    if (errEl) {
      errEl.textContent = errMsg;
    } else {
      mensajes.push(`${campo}: ${errMsg}`);
    }
  }

  if (mensajes.length && alertaErrores) {
    alertaErrores.textContent = mensajes.join(' | ');
    alertaErrores.classList.remove('d-none');
  }
}

/** Establece el modo del modal: 'crear', 'editar' o 'ver' (solo lectura). */
function setModoModal(modo) {
  const titulo = document.getElementById('modal-titulo');
  const btnGuardar = document.getElementById('btn-guardar-remision');
  const badge = document.getElementById('modal-readonly-badge');
  const campos = document.querySelectorAll('#form-remision input, #form-remision select, #form-remision textarea');

  const soloLectura = (modo === 'ver');

  campos.forEach(el => {
    if (el.id === 'modal-remision-id') return; // campo oculto, siempre habilitado
    el.disabled = soloLectura;
  });

  if (btnGuardar) btnGuardar.disabled = soloLectura;
  if (badge) badge.classList.toggle('d-none', !soloLectura);

  if (titulo) {
    if (modo === 'crear') titulo.textContent = 'Nueva Remisión';
    else if (modo === 'editar') titulo.textContent = 'Editar Remisión';
    else titulo.textContent = 'Ver Remisión (solo lectura)';
  }
}

/** Rellena el formulario del modal con los datos de una remisión. */
function rellenarFormulario(data) {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val !== null && val !== undefined ? val : '';
  };

  // fecha: actualizar usando el nuevo widget
  datetimeWidget.setValue(data.fecha || '', 'id_fecha_date', 'id_fecha_time', 'id_fecha');

  set('id_nombre', data.nombre || '');
  set('id_tipo_doc', data.tipo_doc || 'CC');
  set('id_doc', data.doc || '');
  set('id_sexo', data.sexo || 'M');
  set('id_edad', data.edad || '');
  // Especialidad: set select if value matches, otherwise set "OTRA" and fill text input
  const espSelect = document.getElementById('id_especialidad');
  const espOtraContainer = document.getElementById('especialidad_otra_container');
  const espOtraInput = document.getElementById('id_especialidad_otra');
  if (espSelect && data.especialidad) {
    const optionExists = Array.from(espSelect.options).some(opt => opt.value === data.especialidad);
    if (optionExists) {
      espSelect.value = data.especialidad;
      if (espOtraContainer) espOtraContainer.style.display = 'none';
      if (espOtraInput) espOtraInput.value = '';
    } else {
      // Custom value — select "OTRA" and show text input with the value
      espSelect.value = 'OTRA';
      if (espOtraContainer) espOtraContainer.style.display = '';
      if (espOtraInput) espOtraInput.value = data.especialidad;
    }
  } else {
    if (espSelect) espSelect.value = '';
    if (espOtraContainer) espOtraContainer.style.display = 'none';
    if (espOtraInput) espOtraInput.value = '';
  }
  set('id_gest', data.gest || 'NO');
  set('id_diagnostico', data.diagnostico || '');
  set('id_ta', data.ta || '');
  set('id_fc', data.fc || '');
  set('id_fr', data.fr || '');
  set('id_tm', data.tm || '');
  set('id_spo2', data.spo2 || '');
  set('id_glasg', data.glasg || '15/15');
  set('id_eps', data.eps || '');
  set('id_institucion_reporta', data.institucion_reporta || '');
  set('id_municipio', data.municipio || '');
  set('id_medico_refiere', data.medico_refiere || '');
  set('id_medico_hudn', data.medico_hudn || '');
  set('id_radio_operador', data.radio_operador || '');
  set('id_observacion', data.observacion || '');
  set('id_aceptado', data.aceptado || 'NO');

  // fecha_res: actualizar usando el nuevo widget
  datetimeWidget.setValue(data.fecha_res || '', 'id_fecha_res_date', 'id_fecha_res_time', 'id_fecha_res');

  set('modal-oportunidad', data.oportunidad || '');

  // Aplicar lógica GEST → SEXO
  const gestVal = data.gest || 'NO';
  const sexoCampo = document.getElementById('id_sexo');
  if (sexoCampo) {
    sexoCampo.disabled = (gestVal === 'SI');
  }
}

/** Rellena los valores por defecto para un nuevo registro. */
function rellenarDefectos() {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val;
  };

  // Establecer fecha actual usando el nuevo widget
  const ahoraIso = ahora();
  datetimeWidget.setValue(ahoraIso, 'id_fecha_date', 'id_fecha_time', 'id_fecha');

  set('id_tipo_doc', 'CC');
  set('id_sexo', 'M');
  set('id_gest', 'NO');
  set('id_glasg', '15/15');
  set('id_aceptado', 'NO');
  set('modal-oportunidad', '');

  // Limpiar campos clínicos y de resultado
  ['id_nombre','id_doc','id_edad','id_ta','id_fc',
   'id_fr','id_tm','id_spo2','id_eps','id_institucion_reporta','id_municipio',
   'id_medico_refiere','id_radio_operador','id_observacion'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });

  // Pre-fill diagnostico and medico_hudn with default prefixes
  set('id_diagnostico', 'DX:');
  set('id_medico_hudn', 'Dr(a):');

  // Limpiar especialidad
  set('id_especialidad', '');
  const espOtraContainerDef = document.getElementById('especialidad_otra_container');
  if (espOtraContainerDef) espOtraContainerDef.style.display = 'none';
  const espOtraInputDef = document.getElementById('id_especialidad_otra');
  if (espOtraInputDef) espOtraInputDef.value = '';

  // Limpiar campos de fecha_res usando el nuevo widget
  datetimeWidget.setValue('', 'id_fecha_res_date', 'id_fecha_res_time', 'id_fecha_res');

  // Habilitar SEXO
  const sexoCampo = document.getElementById('id_sexo');
  if (sexoCampo) sexoCampo.disabled = false;

  // Prellenar radio_operador con el nombre del usuario autenticado
  if (typeof USUARIO_NOMBRE_COMPLETO !== 'undefined' && USUARIO_NOMBRE_COMPLETO !== '') {
    const radioOperadorEl = document.getElementById('id_radio_operador');
    if (radioOperadorEl) {
      radioOperadorEl.value = USUARIO_NOMBRE_COMPLETO;
      radioOperadorEl.readOnly = true;
    }
  }

  document.getElementById('modal-remision-id').value = '';
}

// ─── Apertura del modal ──────────────────────────────────────────────────────

/** Abre el modal en modo creación. */
function abrirModalNuevo() {
  limpiarErrores();
  rellenarDefectos();
  setModoModal('crear');
  const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('modal-remision'));
  modal.show();
}

/** Abre el modal en modo edición o solo lectura según editabilidad. */
function abrirModalEdicion(id) {
  console.log ("id:", id);
  //const url = URLS.remisionDetalle.replace('__ID__', id);
  const url = URLS.remisionDetalle.replace('999999', id);
  fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
      limpiarErrores();
      rellenarFormulario(data);
      document.getElementById('modal-remision-id').value = id;
      // Editable only if record is from today AND belongs to current user
      const canEdit = data.es_editable && data.es_propio;
      setModoModal(canEdit ? 'editar' : 'ver');
      // radio_operador is always read-only
      const radioEl = document.getElementById('id_radio_operador');
      if (radioEl) radioEl.readOnly = true;
      const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('modal-remision'));
      modal.show();
    })
    //.catch(() => alert('Error al cargar los datos del registro.'));
	.catch(err => {
      console.error("Error cargando remisión:");
      console.error(err);
      console.error(err.stack);

      alert('Error al cargar los datos del registro.');
    });
}

/** Abre el modal en modo clonación: copia TODOS los campos excepto fecha, radio_operador, aceptado, fecha_res y oportunidad. */
function abrirModalClonacion(id) {
  console.log ("id:", id);
  //const url = URLS.remisionDetalle.replace('__ID__', id);
  const url = URLS.remisionDetalle.replace('999999', id);
  fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
      limpiarErrores();

      // Fill form with source data
      rellenarFormulario(data);

      // Set new fecha to now
      const ahoraIso = ahora();
      datetimeWidget.setValue(ahoraIso, 'id_fecha_date', 'id_fecha_time', 'id_fecha');

      // Clear only medico_hudn and observacion
      const medHudnEl = document.getElementById('id_medico_hudn');
      if (medHudnEl) medHudnEl.value = 'Dr(a):';
      const obsEl = document.getElementById('id_observacion');
      if (obsEl) obsEl.value = '';

      // Reset aceptado, fecha_res, oportunidad
      const aceptadoEl = document.getElementById('id_aceptado');
      if (aceptadoEl) aceptadoEl.value = 'NO';
      datetimeWidget.setValue('', 'id_fecha_res_date', 'id_fecha_res_time', 'id_fecha_res');
      const oportunidadEl = document.getElementById('modal-oportunidad');
      if (oportunidadEl) oportunidadEl.value = '';

      // Set radio_operador to current user
      if (typeof USUARIO_NOMBRE_COMPLETO !== 'undefined' && USUARIO_NOMBRE_COMPLETO !== '') {
        const radioOperadorEl = document.getElementById('id_radio_operador');
        if (radioOperadorEl) {
          radioOperadorEl.value = USUARIO_NOMBRE_COMPLETO;
          radioOperadorEl.readOnly = true;
        }
      }

      document.getElementById('modal-remision-id').value = '';

      setModoModal('crear');

      const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('modal-remision'));
      modal.show();
    })
    .catch(() => alert('Error al cargar los datos para clonar.'));
}

// ─── Guardado ────────────────────────────────────────────────────────────────

/** Recoge los datos del formulario como objeto plano. */
function recogerDatosFormulario() {
  const ids = [
    'fecha','nombre','tipo_doc','doc','sexo','edad','especialidad','gest',
    'diagnostico','ta','fc','fr','tm','spo2','glasg','eps',
    'institucion_reporta','municipio','medico_refiere','medico_hudn',
    'radio_operador','observacion','aceptado','fecha_res',
  ];
  // Campos que NO se convierten a mayúsculas (fechas, selects, campos calculados)
  const noUppercase = new Set(['fecha', 'fecha_res', 'tipo_doc', 'sexo', 'gest', 'aceptado', 'especialidad']);
  const data = {};
  ids.forEach(name => {
    const el = document.getElementById('id_' + name);
    let val = el ? el.value : '';
    if (val && !noUppercase.has(name)) {
      val = val.toUpperCase();
    }
    data[name] = val;
  });
  // If especialidad is "OTRA", use the custom text input value
  if (data.especialidad === 'OTRA') {
    const otraEl = document.getElementById('id_especialidad_otra');
    if (otraEl && otraEl.value.trim()) {
      data.especialidad = otraEl.value.trim().toUpperCase();
    }
  }
  return data;
}

/** Envía el formulario al servidor vía AJAX. */
function guardarRemision() {
  const remisionId = document.getElementById('modal-remision-id').value;
  const esEdicion = !!remisionId;

  limpiarErrores();

  // Validación cliente: fecha_res debe ser posterior a fecha (si ambas están presentes)
  const fechaVal = document.getElementById('id_fecha').value;
  const fechaResVal = document.getElementById('id_fecha_res').value;
  if (fechaVal && fechaResVal) {
    const fecha = new Date(fechaVal);
    const fechaRes = new Date(fechaResVal);
    if (fechaRes <= fecha) {
      const msg = 'La fecha de respuesta debe ser posterior a la fecha de ingreso.';
      const alertaErrores = document.getElementById('modal-errores');
      if (alertaErrores) {
        alertaErrores.textContent = msg;
        alertaErrores.classList.remove('d-none');
      }
      const fechaResDateEl = document.getElementById('id_fecha_res_date');
      if (fechaResDateEl) fechaResDateEl.classList.add('is-invalid');
      return; // No enviar al servidor
    }
  }

  const url = esEdicion
    ? URLS.remisionEditar.replace('999999', remisionId)
    : URLS.remisionNueva;

  const body = new URLSearchParams(recogerDatosFormulario());
  body.append('csrfmiddlewaretoken', CSRF_TOKEN);

  limpiarErrores();

  fetch(url, {
    method: 'POST',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: body.toString(),
  })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        // Cerrar modal y navegar a la vista correcta
        const modal = bootstrap.Modal.getInstance(document.getElementById('modal-remision'));
        if (modal) modal.hide();

        if (esEdicion) {
          // Editing: stay on the current view
          window.location.reload();
        } else {
          // Creating/cloning: always navigate to current month
          var hoy = new Date();
          var mesHoy = hoy.getMonth() + 1;
          var anioHoy = hoy.getFullYear();
          var params = new URLSearchParams(window.location.search);
          var orden = params.get('orden') || 'desc';
          window.location.href = '?filtro=mes&mes=' + mesHoy + '&anio=' + anioHoy + '&orden=' + orden;
        }
      } else {
        if (data.errors) {
          mostrarErrores(data.errors);
        } else if (data.error) {
          const alertaErrores = document.getElementById('modal-errores');
          if (alertaErrores) {
            alertaErrores.textContent = data.error;
            alertaErrores.classList.remove('d-none');
          }
        }
      }
    })
    .catch(() => alert('Error de red al guardar el registro.'));
}

// ─── Inicialización ──────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {

  // Botón "Nuevo Registro"
  const btnNuevo = document.getElementById('btn-nuevo-registro');
  if (btnNuevo) btnNuevo.addEventListener('click', abrirModalNuevo);

  // Botón "Guardar" del modal
  const btnGuardar = document.getElementById('btn-guardar-remision');
  if (btnGuardar) btnGuardar.addEventListener('click', guardarRemision);

  // Calcular OPORTUNIDAD en tiempo real cuando se confirma fecha_res
  const fechaResHidden = document.getElementById('id_fecha_res');
  if (fechaResHidden) {
    fechaResHidden.addEventListener('datetimeChanged', function () {
      const fechaVal = document.getElementById('id_fecha').value;
      const fechaResVal = this.value;
      const oportunidadEl = document.getElementById('modal-oportunidad');

      // Limpiar error previo de fecha_res
      const alertaErroresRT = document.getElementById('modal-errores');
      if (alertaErroresRT) { alertaErroresRT.classList.add('d-none'); alertaErroresRT.textContent = ''; }
      const fechaResDateEl = document.getElementById('id_fecha_res_date');
      if (fechaResDateEl) fechaResDateEl.classList.remove('is-invalid');

      if (fechaVal && fechaResVal) {
        const fecha = new Date(fechaVal);
        const fechaRes = new Date(fechaResVal);
        if (fechaRes > fecha) {
          const diffMin = Math.floor((fechaRes - fecha) / 60000);
          const hh = String(Math.floor(diffMin / 60)).padStart(2, '0');
          const mm = String(diffMin % 60).padStart(2, '0');
          if (oportunidadEl) oportunidadEl.value = `${hh}:${mm}`;
        } else {
          if (oportunidadEl) oportunidadEl.value = '';
          // Mostrar error en la alerta del modal (visible siempre)
          const alertaErrores = document.getElementById('modal-errores');
          if (alertaErrores) {
            alertaErrores.textContent = 'La fecha de respuesta debe ser posterior a la fecha de ingreso.';
            alertaErrores.classList.remove('d-none');
          }
          if (fechaResDateEl) fechaResDateEl.classList.add('is-invalid');
        }
      } else {
        if (oportunidadEl) oportunidadEl.value = '';
      }
    });
  }

  // Especialidad: show/hide "otra" text input
  const especialidadSelect = document.getElementById('id_especialidad');
  const otraContainer = document.getElementById('especialidad_otra_container');
  const otraInput = document.getElementById('id_especialidad_otra');

  if (especialidadSelect && otraContainer) {
    especialidadSelect.addEventListener('change', function() {
      if (this.value === 'OTRA') {
        otraContainer.style.display = '';
        if (otraInput) otraInput.focus();
      } else {
        otraContainer.style.display = 'none';
        if (otraInput) otraInput.value = '';
      }
    });
  }

  // Observación: auto-fill fecha_res with current date/time when user types
  const observacionEl = document.getElementById('id_observacion');
  if (observacionEl) {
    observacionEl.addEventListener('input', function() {
      // Every time observacion changes, update fecha_res to now and recalculate oportunidad
      const fechaResHiddenEl = document.getElementById('id_fecha_res');
      if (this.value.trim() !== '' && fechaResHiddenEl) {
        const now = ahora();
        datetimeWidget.setValue(now, 'id_fecha_res_date', 'id_fecha_res_time', 'id_fecha_res');
        // Trigger oportunidad calculation
        fechaResHiddenEl.dispatchEvent(new CustomEvent('datetimeChanged', { bubbles: true }));
      }
    });
  }

  // Importar Excel — sheet selection and AJAX import
  const formImportar = document.getElementById('form-importar');
  const fileInput = document.getElementById('id_archivo_importar');
  const sheetSelector = document.getElementById('id_sheet_selector');
  const resultadoDiv = document.getElementById('importar-resultado');

  // When file is selected, fetch sheet names
  if (fileInput && sheetSelector) {
    fileInput.addEventListener('change', function () {
      // Reset sheet selector
      sheetSelector.style.display = 'none';
      sheetSelector.innerHTML = '';
      if (resultadoDiv) { resultadoDiv.textContent = ''; resultadoDiv.className = 'mt-1 small sidebar-text sidebar-sub-content'; }

      if (!this.files || !this.files[0]) return;

      const formData = new FormData();
      formData.append('archivo', this.files[0]);
      formData.append('csrfmiddlewaretoken', CSRF_TOKEN);

      fetch(URLS.importarExcelHojas, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData,
      })
        .then(r => r.json())
        .then(data => {
          if (data.ok && data.hojas && data.hojas.length > 1) {
            // Multiple sheets — show selector
            sheetSelector.innerHTML = '';
            data.hojas.forEach(function (nombre) {
              const opt = document.createElement('option');
              opt.value = nombre;
              opt.textContent = nombre;
              sheetSelector.appendChild(opt);
            });
            sheetSelector.style.display = '';
          } else {
            // Single sheet or error — hide selector
            sheetSelector.style.display = 'none';
          }
        })
        .catch(() => {
          sheetSelector.style.display = 'none';
        });
    });
  }

  // Handle import form submit — show modal dialog
  if (formImportar) {
    formImportar.addEventListener('submit', function (e) {
      e.preventDefault();
      const formData = new FormData(this);

      // Show processing modal
      let importModal = document.getElementById('modal-importar-estado');
      if (!importModal) {
        importModal = document.createElement('div');
        importModal.id = 'modal-importar-estado';
        importModal.className = 'modal fade';
        importModal.tabIndex = -1;
        importModal.setAttribute('data-bs-backdrop', 'static');
        importModal.setAttribute('data-bs-keyboard', 'false');
        importModal.innerHTML = `
          <div class="modal-dialog modal-sm modal-dialog-centered">
            <div class="modal-content">
              <div class="modal-body text-center py-4">
                <div id="importar-modal-spinner" class="mb-3">
                  <div class="spinner-border text-primary" role="status"></div>
                </div>
                <p id="importar-modal-msg" class="mb-0 fw-semibold">Importando...</p>
              </div>
              <div id="importar-modal-footer" class="modal-footer d-none justify-content-center">
                <button type="button" class="btn btn-primary btn-sm" data-bs-dismiss="modal">Aceptar</button>
              </div>
            </div>
          </div>`;
        document.body.appendChild(importModal);
      }

      const modalMsg = importModal.querySelector('#importar-modal-msg');
      const modalSpinner = importModal.querySelector('#importar-modal-spinner');
      const modalFooter = importModal.querySelector('#importar-modal-footer');

      // Reset modal state
      modalMsg.textContent = 'Importando...';
      modalMsg.className = 'mb-0 fw-semibold';
      modalSpinner.classList.remove('d-none');
      modalFooter.classList.add('d-none');

      const bsModal = bootstrap.Modal.getOrCreateInstance(importModal);
      bsModal.show();

      fetch(this.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData,
      })
        .then(r => r.json())
        .then(data => {
          modalSpinner.classList.add('d-none');
          modalFooter.classList.remove('d-none');
          modalFooter.classList.add('d-flex');

          if (data.ok) {
            modalMsg.textContent = `✓ ${data.importados} registros importados correctamente.`;
            modalMsg.className = 'mb-0 fw-semibold text-success';
            // Reload after user closes modal
            importModal.addEventListener('hidden.bs.modal', function () {
              window.location.reload();
            }, { once: true });
          } else {
            modalMsg.textContent = data.error || 'Error al importar.';
            modalMsg.className = 'mb-0 fw-semibold text-danger';
          }
        })
        .catch(() => {
          modalSpinner.classList.add('d-none');
          modalFooter.classList.remove('d-none');
          modalFooter.classList.add('d-flex');
          modalMsg.textContent = 'Error de red al importar.';
          modalMsg.className = 'mb-0 fw-semibold text-danger';
        });
    });
  }

});

// Exponer funciones para uso desde tabla.js
window.abrirModalEdicion = abrirModalEdicion;
window.abrirModalClonacion = abrirModalClonacion;
