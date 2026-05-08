'use strict';

const datetimeWidget = (function () {

  function isoToParts(iso) {
    if (!iso) return { date: '', time: '' };
    const m = iso.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})$/);
    return m ? { date: m[1], time: m[2] } : { date: '', time: '' };
  }

  function partsToIso(date, time) {
    if (!date || !time) return '';
    if (!/^\d{2}:\d{2}$/.test(time)) return '';
    return date + 'T' + time;
  }

  function actualizarOculto(dateInputId, timeInputId, hiddenInputId) {
    const dateEl = document.getElementById(dateInputId);
    const timeEl = document.getElementById(timeInputId);
    const hiddenEl = document.getElementById(hiddenInputId);
    if (!dateEl || !timeEl || !hiddenEl) return;
    hiddenEl.value = partsToIso(dateEl.value, timeEl.value);
    hiddenEl.dispatchEvent(new CustomEvent('datetimeChanged', { bubbles: true }));
  }

  function aplicarMascaraHora(timeEl) {
    timeEl.addEventListener('input', function () {
      let val = this.value.replace(/[^\d]/g, '');
      let resultado = '';
      if (val.length > 0) resultado += val.substring(0, 2);
      if (val.length >= 3) resultado += ':' + val.substring(2, 4);
      this.value = resultado;
    });
  }

  function init(dateInputId, timeInputId, hiddenInputId) {
    const dateEl = document.getElementById(dateInputId);
    const timeEl = document.getElementById(timeInputId);
    if (dateEl) {
      dateEl.addEventListener('change', function () {
        actualizarOculto(dateInputId, timeInputId, hiddenInputId);
      });
    }
    if (timeEl) {
      aplicarMascaraHora(timeEl);
      timeEl.addEventListener('input', function () {
        actualizarOculto(dateInputId, timeInputId, hiddenInputId);
      });
    }
  }

  function setValue(iso, dateInputId, timeInputId, hiddenInputId) {
    const { date, time } = isoToParts(iso);
    const dateEl = document.getElementById(dateInputId);
    const timeEl = document.getElementById(timeInputId);
    const hiddenEl = document.getElementById(hiddenInputId);
    if (dateEl) dateEl.value = date;
    if (timeEl) timeEl.value = time;
    if (hiddenEl) hiddenEl.value = iso || '';
  }

  return { init, setValue, isoToParts, partsToIso };
})();
