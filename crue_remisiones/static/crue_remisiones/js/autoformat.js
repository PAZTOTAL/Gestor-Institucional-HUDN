/**
 * autoformat.js — Autoformato de campos en el modal de remisión.
 *
 * Requisitos: 5.4, 5.5, 5.6, 5.7
 */

'use strict';

/**
 * Agrega '°' al campo Temperatura si el valor es numérico y no lo tiene ya.
 */
function autoformatTemperatura() {
  const campo = document.getElementById('id_T');
  if (!campo) return;
  campo.addEventListener('blur', function () {
    const val = this.value.trim();
    if (val && val !== 'NO REFIERE' && !val.endsWith('°')) {
      if (/^\d+(\.\d+)?$/.test(val)) {
        this.value = val + '°';
      }
    }
  });
}

/**
 * Agrega '%' al campo SPO2 si el valor es numérico y no lo tiene ya.
 */
function autoformatSpo2() {
  const campo = document.getElementById('id_SPO2');
  if (!campo) return;
  campo.addEventListener('blur', function () {
    const val = this.value.trim();
    if (val && val !== 'NO REFIERE' && !val.endsWith('%')) {
      if (/^\d+(\.\d+)?$/.test(val)) {
        this.value = val + '%';
      }
    }
  });
}

/**
 * Cuando GEST cambia a 'SI', fuerza SEXO='F' y deshabilita el campo.
 * Cuando GEST cambia a 'NO', habilita SEXO.
 */
function autoformatGest() {
  const gestCampo = document.getElementById('id_GEST');
  if (!gestCampo) return;
  gestCampo.addEventListener('change', function () {
    const sexoCampo = document.getElementById('id_SEXO');
    if (!sexoCampo) return;
    if (this.value === 'SI') {
      sexoCampo.value = 'F';
      sexoCampo.disabled = true;
    } else {
      sexoCampo.disabled = false;
    }
  });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function () {
  autoformatTemperatura();
  autoformatSpo2();
  autoformatGest();
});
