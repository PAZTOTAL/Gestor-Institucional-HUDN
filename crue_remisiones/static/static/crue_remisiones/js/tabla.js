/**
 * tabla.js — Lógica de la tabla interactiva de remisiones.
 *
 * Requisitos: 4.1, 9.1, 9.3, 9.4, 6.2
 */

'use strict';

document.addEventListener('DOMContentLoaded', function () {

  // ─── Expansión de fila detallada [d] ──────────────────────────────────────

  document.querySelectorAll('.btn-detalle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const fila = this.closest('tr.fila-remision');
      const id = fila ? fila.dataset.id : null;
      if (!id) return;

      const filaDetalle = document.getElementById('detalle-' + id);
      if (!filaDetalle) return;

      // Colapsar todas las demás filas de detalle
      document.querySelectorAll('.fila-detalle').forEach(function (fd) {
        if (fd.id !== 'detalle-' + id) {
          fd.style.display = 'none';
        }
      });

      // Toggle de la fila actual
      const estaVisible = filaDetalle.style.display !== 'none';
      filaDetalle.style.display = estaVisible ? 'none' : 'table-row';

      // Preservar estado en localStorage
      if (!estaVisible) {
        localStorage.setItem('filaExpandida', id);
        fila.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        localStorage.removeItem('filaExpandida');
      }
    });
  });

  // ─── Restaurar fila expandida al recargar ─────────────────────────────────

  const idExpandido = localStorage.getItem('filaExpandida');
  if (idExpandido) {
    const filaDetalle = document.getElementById('detalle-' + idExpandido);
    if (filaDetalle) {
      filaDetalle.style.display = 'table-row';
      setTimeout(function () {
        filaDetalle.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 100);
    } else {
      // El registro ya no está en la vista actual; limpiar
      localStorage.removeItem('filaExpandida');
    }
  }

  // ─── Doble clic en fila → abrir modal de edición ──────────────────────────

  document.querySelectorAll('.fila-remision').forEach(function (fila) {
    fila.addEventListener('dblclick', function () {
      const id = this.dataset.id;
      if (id && typeof window.abrirModalEdicion === 'function') {
        window.abrirModalEdicion(id);
      }
    });
  });

  // ─── Botón [e] → abrir modal de edición ───────────────────────────────────

  document.querySelectorAll('.btn-editar').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const id = this.dataset.id;
      if (id && typeof window.abrirModalEdicion === 'function') {
        window.abrirModalEdicion(id);
      }
    });
  });

  // ─── Botón [c] → abrir modal de clonación ─────────────────────────────────

  document.querySelectorAll('.btn-clonar').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const id = this.dataset.id;
      if (id && typeof window.abrirModalClonacion === 'function') {
        window.abrirModalClonacion(id);
      }
    });
  });

  // ─── Botón [x] → confirmar eliminación ────────────────────────────────────

  let idAEliminar = null;

  document.querySelectorAll('.btn-eliminar').forEach(function (btn) {
    btn.addEventListener('click', function () {
      idAEliminar = this.dataset.id;
      const modal = bootstrap.Modal.getOrCreateInstance(
        document.getElementById('modal-confirmar-eliminar')
      );
      modal.show();
    });
  });

  const btnConfirmarEliminar = document.getElementById('btn-confirmar-eliminar');
  if (btnConfirmarEliminar) {
    btnConfirmarEliminar.addEventListener('click', function () {
      if (!idAEliminar) return;

      //const url = URLS.remisionEliminar.replace('__ID__', idAEliminar);
      const url = URLS.remisionEliminar.replace('999999', idAEliminar);
      const body = new URLSearchParams({ csrfmiddlewaretoken: CSRF_TOKEN });

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
          const modal = bootstrap.Modal.getInstance(
            document.getElementById('modal-confirmar-eliminar')
          );
          if (modal) modal.hide();

          if (data.ok) {
            // Limpiar localStorage si era la fila expandida
            if (localStorage.getItem('filaExpandida') === idAEliminar) {
              localStorage.removeItem('filaExpandida');
            }
            window.location.reload();
          } else {
            alert(data.error || 'No se pudo eliminar el registro.');
          }
          idAEliminar = null;
        })
        .catch(() => {
          alert('Error de red al eliminar el registro.');
          idAEliminar = null;
        });
    });
  }

  // ─── Numeración dinámica de filas (columna "No") ─────────────────────────
  // Req 4.1: el campo "No" es un índice calculado en el frontend como la
  // posición de la fila en el resultado de la consulta actual.
  function renumerarFilas() {
    let contador = 1;
    document.querySelectorAll('#tabla-body .fila-remision').forEach(function (fila) {
      const tdNo = fila.querySelector('.col-no');
      if (tdNo) tdNo.textContent = contador++;
    });
  }

  // Ejecutar numeración al cargar para garantizar consistencia con el DOM
  renumerarFilas();

  // Exponer para uso externo (e.g. tras actualizaciones dinámicas de la tabla)
  window.renumerarFilas = renumerarFilas;

  // ─── Toggle del sidebar ───────────────────────────────────────────────────

  const sidebarToggle = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('main-content');

  if (sidebarToggle && sidebar) {
    // Restaurar estado del sidebar desde localStorage
    const sidebarColapsado = localStorage.getItem('sidebarColapsado') === 'true';
    if (sidebarColapsado) {
      sidebar.classList.add('sidebar-collapsed');
      if (mainContent) mainContent.classList.add('main-content-expanded');
    }

    sidebarToggle.addEventListener('click', function () {
      const colapsado = sidebar.classList.toggle('sidebar-collapsed');
      if (mainContent) mainContent.classList.toggle('main-content-expanded', colapsado);
      localStorage.setItem('sidebarColapsado', colapsado);
    });
  }

  // ─── Collapsible sidebar menu sections ──────────────────────────────────

  document.querySelectorAll('.sidebar-menu-toggle').forEach(function (btn) {
    const targetId = btn.getAttribute('data-target');
    const target = document.getElementById(targetId);
    if (!target) return;

    // Restore state from localStorage
    const key = 'sidebarMenu_' + targetId;
    const savedState = localStorage.getItem(key);
    if (savedState === 'open') {
      target.classList.remove('collapsed');
      btn.setAttribute('aria-expanded', 'true');
    }

    btn.addEventListener('click', function () {
      const isCollapsed = target.classList.toggle('collapsed');
      btn.setAttribute('aria-expanded', !isCollapsed);
      localStorage.setItem(key, isCollapsed ? 'closed' : 'open');
    });
  });

});
