// main.js — Comportamientos JavaScript mínimos de crue_traslados.

// ── Manejador de doble clic en filas de la tabla ──────────────────────────
document.addEventListener ('dblclick', function (evento) {
	var fila = evento.target.closest ('tr[data-mes-estado]');
	if (!fila) return;

	var estadoMes = fila.getAttribute ('data-mes-estado');
	if (estadoMes !== 'ABIERTO') return;

	var urlEditar = fila.getAttribute ('data-editar-url');
	if (!urlEditar) return;

	htmx.ajax ('GET', urlEditar, {
		target: '#modal-contenedor',
		swap: 'innerHTML',
	});
});


// ── Manejador de errores HTMX (toast de notificación) ────────────────────
document.addEventListener ('htmx:responseError', function (evento) {
	var codigoHttp = evento.detail.xhr.status;
	var mensajeError = evento.detail.xhr.responseText || 'Ocurrió un error inesperado.';

	if (mensajeError.length > 200) {
		mensajeError = mensajeError.substring (0, 200) + '…';
	}

	mostrarToast (codigoHttp + ': ' + mensajeError);
});


// ── Función auxiliar: mostrar toast ──────────────────────────────────────
function mostrarToast (mensaje) {
	var toast = document.createElement ('div');
	toast.setAttribute ('role', 'alert');
	toast.className = [
		'fixed', 'bottom-6', 'right-6', 'z-50',
		'max-w-sm', 'w-full',
		'bg-red-600', 'text-white',
		'px-5', 'py-4', 'rounded-lg', 'shadow-lg',
		'flex', 'items-start', 'gap-3',
		'transition-opacity', 'duration-300',
	].join (' ');

	toast.innerHTML =
		'<svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
			'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" ' +
				'd="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>' +
		'</svg>' +
		'<span class="text-sm leading-snug">' + _escaparHtml (mensaje) + '</span>';

	document.body.appendChild (toast);

	setTimeout (function () {
		toast.style.opacity = '0';
		setTimeout (function () {
			if (toast.parentNode) toast.parentNode.removeChild (toast);
		}, 300);
	}, 5000);
}


// ── Función auxiliar: escapar HTML para evitar XSS en el toast ───────────
function _escaparHtml (texto) {
	var div = document.createElement ('div');
	div.appendChild (document.createTextNode (texto));
	return div.innerHTML;
}
