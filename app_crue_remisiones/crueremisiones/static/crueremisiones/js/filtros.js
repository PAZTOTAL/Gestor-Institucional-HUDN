/**
 * filtros.js — Lógica de controles de filtro en la vista principal.
 *
 * Filters: Por mes, Por documento o nombre.
 * Radio buttons select which filter is active.
 */

'use strict';

document.addEventListener('DOMContentLoaded', function () {

  // ── References ────────────────────────────────────────────────────────────
  const radios      = document.querySelectorAll('.filtro-radio');
  const formFiltros = document.getElementById('form-filtros');
  const errorFiltro = document.getElementById('filtro-error');

  const selectMes = document.getElementById('select-mes');
  const inputAnio = document.getElementById('input-anio');
  const docControl = document.getElementById('input-doc');

  // ── 1. Visual state: dim inactive filter controls ─────────────────────────

  function actualizarEstadoFiltros() {
    var filtroActivo = document.querySelector('.filtro-radio:checked');
    var valor = filtroActivo ? filtroActivo.value : 'mes';

    // Mes controls
    var mesActivo = (valor === 'mes');
    if (selectMes) selectMes.style.opacity = mesActivo ? '1' : '0.4';
    if (inputAnio) inputAnio.style.opacity = mesActivo ? '1' : '0.4';

    // Doc/nombre control
    var docActivo = (valor === 'documento');
    if (docControl) docControl.style.opacity = docActivo ? '1' : '0.4';
  }

  // Initialize
  actualizarEstadoFiltros();

  // Update on radio change
  radios.forEach(function (radio) {
    radio.addEventListener('change', function () {
      actualizarEstadoFiltros();
    });
  });

  // ── 1b. Auto-select radio when clicking on a filter widget ────────────────

  function selectRadio(value) {
    var radio = document.querySelector('.filtro-radio[value="' + value + '"]');
    if (radio && !radio.checked) {
      radio.checked = true;
      actualizarEstadoFiltros();
    }
  }

  // Mes widgets → select "mes" radio
  if (selectMes) selectMes.addEventListener('focus', function () { selectRadio('mes'); });
  if (inputAnio) inputAnio.addEventListener('focus', function () { selectRadio('mes'); });

  // Doc/nombre widget → select "documento" radio
  if (docControl) docControl.addEventListener('focus', function () { selectRadio('documento'); });

  // ── 2. Auto-submit on month/year change ───────────────────────────────────

  function actualizarMesesDisponibles() {
    if (!selectMes || !inputAnio) return;
    var anioVal = parseInt(inputAnio.value, 10);
    var hoy = new Date();
    var anioHoy = hoy.getFullYear();
    var mesHoy = hoy.getMonth() + 1;

    Array.from(selectMes.options).forEach(function (opt) {
      var mesVal = parseInt(opt.value, 10);
      opt.disabled = (anioVal === anioHoy && mesVal > mesHoy);
    });

    // If selected month is now disabled, select the latest valid month
    var selOpt = selectMes.options[selectMes.selectedIndex];
    if (selOpt && selOpt.disabled) {
      for (var i = selectMes.options.length - 1; i >= 0; i--) {
        if (!selectMes.options[i].disabled) {
          selectMes.selectedIndex = i;
          break;
        }
      }
    }
  }

  // When "Por mes" radio is selected, set to current month/year and auto-submit
  var radioMes = document.getElementById('radio-mes');
  if (radioMes && formFiltros && selectMes && inputAnio) {
    radioMes.addEventListener('change', function () {
      if (this.checked) {
        var hoy = new Date();
        var mesHoy = hoy.getMonth() + 1;
        var anioHoy = hoy.getFullYear();
        selectMes.value = String(mesHoy);
        inputAnio.value = String(anioHoy);
        actualizarMesesDisponibles();
        formFiltros.submit();
      }
    });
  }

  // Auto-submit when month changes (only if mes filter is active)
  if (selectMes && formFiltros) {
    selectMes.addEventListener('change', function () {
      var filtroActivo = document.querySelector('.filtro-radio:checked');
      if (filtroActivo && filtroActivo.value === 'mes') {
        formFiltros.submit();
      }
    });
  }

  // When year changes, update disabled months and auto-submit
  if (inputAnio && formFiltros) {
    inputAnio.addEventListener('change', function () {
      actualizarMesesDisponibles();
      var filtroActivo = document.querySelector('.filtro-radio:checked');
      if (filtroActivo && filtroActivo.value === 'mes') {
        formFiltros.submit();
      }
    });
  }

  // ── 3. Ordering toggle ────────────────────────────────────────────────────

  var btnOrden = document.getElementById('btn-orden');
  var inputOrden = document.getElementById('input-orden');
  var ordenLabel = document.getElementById('orden-label');

  if (btnOrden && inputOrden && formFiltros) {
    btnOrden.addEventListener('click', function () {
      var esDesc = inputOrden.value === 'desc';
      inputOrden.value = esDesc ? 'asc' : 'desc';

      var icon = btnOrden.querySelector('i');
      if (icon) {
        icon.className = esDesc ? 'bi bi-sort-up me-1' : 'bi bi-sort-down me-1';
      }
      if (ordenLabel) {
        ordenLabel.textContent = esDesc ? 'Antiguos' : 'Recientes';
      }
      btnOrden.title = esDesc ? 'Más antiguos primero' : 'Más recientes primero';

      formFiltros.submit();
    });
  }

  // ── 3b. Paginado checkbox auto-submit ─────────────────────────────────────

  var checkPaginado = document.getElementById('check-paginado');
  if (checkPaginado && formFiltros) {
    checkPaginado.addEventListener('change', function () {
      formFiltros.submit();
    });
  }

});
