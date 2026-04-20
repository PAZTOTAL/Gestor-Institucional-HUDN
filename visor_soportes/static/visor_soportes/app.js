const form = document.getElementById("form-consulta");
const estado = document.getElementById("estado");
const resultados = document.getElementById("resultados");
const visorModal = document.getElementById("visor-modal");
const visorPdf = document.getElementById("visor-pdf");
const visorTitulo = document.getElementById("visor-titulo");
const descargarPdf = document.getElementById("descargar-pdf");
const cerrarModal = document.getElementById("cerrar-modal");
const selectorContrato = document.getElementById("selector-contrato");
const { PDFDocument } = window.PDFLib || {};

const MESES = {
  1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
  7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
};

const API_BASE = "/visor-soportes";
let soportesEnVisor = [];
let soportesPorContrato = new Map();
let pdfUnicoActualUrl = null;
let pdfCachePorContrato = new Map();

function setEstado(msg, isError = false) {
  estado.textContent = msg;
  estado.style.color = isError ? "#b91c1c" : "#0f766e";
}

function formatearFecha(fecha) {
  if (!fecha) return "-";
  try {
    return new Date(fecha).toLocaleDateString("es-CO");
  } catch {
    return String(fecha);
  }
}

async function getJson(url) {
  const resp = await fetch(url);
  const data = await resp.json().catch(() => null);
  if (!resp.ok) {
    const msg = data?.message || data?.error || `Error HTTP ${resp.status}`;
    throw new Error(msg);
  }
  return data;
}

function obtenerRangoMes(anio, mes) {
  const inicio = new Date(anio, mes - 1, 1);
  const fin = new Date(anio, mes, 0);
  return { inicio, fin };
}

function parsearFechaBackend(valor) {
  if (!valor) return null;
  if (valor instanceof Date && !Number.isNaN(valor.getTime())) return valor;
  const texto = String(valor).trim();

  const iso = new Date(texto);
  if (!Number.isNaN(iso.getTime())) return iso;

  const ddmmyyyy = /^(\d{2})-(\d{2})-(\d{4})$/.exec(texto);
  if (ddmmyyyy) {
    const d = Number(ddmmyyyy[1]);
    const m = Number(ddmmyyyy[2]) - 1;
    const y = Number(ddmmyyyy[3]);
    const fecha = new Date(y, m, d);
    return Number.isNaN(fecha.getTime()) ? null : fecha;
  }

  return null;
}

function limpiarCachePdfContratos() {
  for (const item of pdfCachePorContrato.values()) {
    if (item?.url) URL.revokeObjectURL(item.url);
  }
  pdfCachePorContrato = new Map();
}

async function mapConLimite(items, limite, worker) {
  const resultados = new Array(items.length);
  let index = 0;

  const runners = Array.from({ length: Math.min(limite, items.length) }, async () => {
    while (true) {
      const actual = index;
      index += 1;
      if (actual >= items.length) break;
      resultados[actual] = await worker(items[actual], actual);
    }
  });

  await Promise.all(runners);
  return resultados;
}

async function buscar(cedula, mesSeleccionado, anioSeleccionado) {
  const mes = Number(mesSeleccionado);
  const anio = Number(anioSeleccionado);

  if (!Number.isInteger(mes) || mes < 1 || mes > 12) {
    throw new Error("Mes inválido.");
  }
  if (!Number.isInteger(anio) || anio < 2000 || anio > 2100) {
    throw new Error("Año inválido.");
  }

  const { inicio: inicioMes, fin: finMes } = obtenerRangoMes(anio, mes);

  const apiBase = API_BASE;
  const contratosUrl = `${apiBase}/api/consulta/contratos/${encodeURIComponent(cedula)}`;
  const contratos = await getJson(contratosUrl);

  const contratosMes = (Array.isArray(contratos) ? contratos : []).filter((contrato) => {
    const inicio = parsearFechaBackend(contrato?.fecha_inicio);
    const fin = parsearFechaBackend(contrato?.fecha_terminacion);
    if (!inicio) return false;

    const inicioDia = new Date(inicio.getFullYear(), inicio.getMonth(), inicio.getDate());
    const finDia = fin
      ? new Date(fin.getFullYear(), fin.getMonth(), fin.getDate())
      : new Date(2100, 11, 31);

    return inicioDia <= finMes && finDia >= inicioMes;
  });

  if (!contratosMes.length) {
    return { contratos: [], documentosPorIde: new Map() };
  }

  const ides = Array.from(
    new Set(
      (contratosMes || [])
        .map((c) => Number(c.ide_contratista_int))
        .filter((n) => Number.isFinite(n))
    )
  );

  const docsEntries = await Promise.all(
    ides.map(async (ide) => {
      const docs = await getJson(`${apiBase}/api/consulta/documentos/${ide}`);
      return [ide, Array.isArray(docs) ? docs : []];
    })
  );

  const documentosPorIde = new Map(docsEntries);
  return { contratos: contratosMes, documentosPorIde };
}

function renderResultados(cedula, contratos, documentosPorIde) {
  if (!contratos.length) {
    resultados.innerHTML = "<div class='card'><strong>No se encontraron contratos/soportes para el mes y año elegidos.</strong></div>";
    return;
  }

  const soportes = [];
  for (const contrato of contratos) {
    const docs = documentosPorIde.get(Number(contrato.ide_contratista_int)) || [];
    const numeroContrato = contrato.numero_contrato || "Sin número";
    for (const doc of docs) {
      soportes.push({
        cedula,
        ide: Number(contrato.ide_contratista_int),
        idDoc: Number(doc.id_documento_contratista),
        archivo: doc.nombre_archivo || `documento-${doc.id_documento_contratista}.pdf`,
        contrato: numeroContrato,
      });
    }
  }

  if (!soportes.length) {
    resultados.innerHTML = "<div class='card'><strong>Se encontró contrato, pero no hay soportes existentes para ese mes y año.</strong></div>";
    return;
  }

  soportesEnVisor = soportes;
  limpiarCachePdfContratos();
  soportesPorContrato = new Map();
  for (const soporte of soportes) {
    const key = String(soporte.contrato);
    if (!soportesPorContrato.has(key)) {
      soportesPorContrato.set(key, []);
    }
    soportesPorContrato.get(key).push(soporte);
  }

  const contratosUnicos = Array.from(
    new Set(contratos.map((c) => c.numero_contrato || "Sin número"))
  );
  const listaContratos = contratosUnicos.join(", ");

  resultados.innerHTML = `
    <article class="card">
      <h3>Contratos encontrados</h3>
      <div class="meta">
        <div><strong>Total contratos:</strong> ${contratosUnicos.length}</div>
        <div><strong>Números:</strong> ${listaContratos}</div>
        <div><strong>Total soportes:</strong> ${soportes.length}</div>
      </div>
      <button class="btn-link" data-action="ver-todos-soportes">Ver soportes</button>
    </article>
  `;
}

function dataUrlToBytes(dataUrl) {
  const base64 = String(dataUrl).split(",")[1] || "";
  const bin = atob(base64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i += 1) {
    bytes[i] = bin.charCodeAt(i);
  }
  return bytes;
}

async function generarPdfUnico(soportes) {
  if (!PDFDocument) throw new Error("No se pudo cargar la librería de PDF.");
  const merged = await PDFDocument.create();
  const omitidos = [];
  let agregados = 0;

  const cargas = await mapConLimite(soportes, 8, async (soporte) => {
    try {
      const url = `${API_BASE}/api/consulta/documento?ide=${soporte.ide}&idDoc=${soporte.idDoc}`;
      const data = await getJson(url);
      const base64 = data?.archivo_base64;
      if (!base64) {
        return {
          ok: false,
          archivo: soporte.archivo || `documento-${soporte.idDoc}.pdf`,
          motivo: "Documento sin contenido base64",
        };
      }

      const srcBytes = dataUrlToBytes(base64);
      const srcDoc = await PDFDocument.load(srcBytes, { ignoreEncryption: true });
      return { ok: true, srcDoc };
    } catch (error) {
      return {
        ok: false,
        archivo: soporte.archivo || `documento-${soporte.idDoc}.pdf`,
        motivo: error?.message || "Error al leer PDF",
      };
    }
  });

  for (const carga of cargas) {
    if (!carga?.ok) {
      omitidos.push({
        archivo: carga?.archivo || "Documento",
        motivo: carga?.motivo || "Error al leer PDF",
      });
      continue;
    }
    const pages = await merged.copyPages(carga.srcDoc, carga.srcDoc.getPageIndices());
    pages.forEach((p) => merged.addPage(p));
    agregados += 1;
  }

  if (merged.getPageCount() === 0) {
    const detalle = omitidos[0]?.motivo ? ` Detalle: ${omitidos[0].motivo}` : "";
    throw new Error(`No se pudo unir ningún soporte.${detalle}`);
  }

  const mergedBytes = await merged.save();
  const blob = new Blob([mergedBytes], { type: "application/pdf" });
  return { url: URL.createObjectURL(blob), agregados, omitidos };
}

async function generarYMostrarContrato(contratoSeleccionado) {
  const soportesContrato = soportesPorContrato.get(String(contratoSeleccionado)) || [];
  if (!soportesContrato.length) {
    throw new Error("No hay soportes para el contrato seleccionado.");
  }

  const cacheKey = String(contratoSeleccionado);
  let cache = pdfCachePorContrato.get(cacheKey);

  if (!cache) {
    setEstado(`Uniendo soportes del contrato ${contratoSeleccionado}...`);
    const generado = await generarPdfUnico(soportesContrato);
    cache = {
      url: generado.url,
      agregados: generado.agregados,
      omitidos: generado.omitidos,
    };
    pdfCachePorContrato.set(cacheKey, cache);
  } else {
    setEstado(`Mostrando contrato ${contratoSeleccionado} desde caché...`);
  }
  pdfUnicoActualUrl = cache.url;

  visorTitulo.textContent = `Soportes unificados - Contrato ${contratoSeleccionado}`;
  visorPdf.src = cache.url;
  descargarPdf.href = cache.url;
  descargarPdf.download = `soportes-contrato-${contratoSeleccionado}.pdf`;

  if (cache.omitidos.length > 0) {
    setEstado(`PDF generado con ${cache.agregados} soporte(s). Omitidos: ${cache.omitidos.length}.`, true);
  } else {
    setEstado(`PDF único generado con ${cache.agregados} soporte(s).`);
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  resultados.innerHTML = "";
  limpiarCachePdfContratos();
  const cedula = document.getElementById("cedula").value.trim();
  const mes = document.getElementById("mes").value;
  const anio = document.getElementById("anio").value;
  if (!cedula || !mes || !anio) {
    setEstado("Debes ingresar cédula, mes y año.", true);
    return;
  }

  setEstado("Consultando contratos y soportes...");

  try {
    const { contratos, documentosPorIde } = await buscar(cedula, mes, anio);
    renderResultados(cedula, contratos, documentosPorIde);
    setEstado("Consulta completada.");
  } catch (err) {
    setEstado(`Error: ${err.message}`, true);
  }
});

resultados.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-action='ver-todos-soportes']");
  if (!btn) return;

  try {
    if (!soportesEnVisor.length) throw new Error("No hay soportes para visualizar.");

    const contratosDisponibles = Array.from(soportesPorContrato.keys());
    selectorContrato.innerHTML = contratosDisponibles
      .map((numero) => `<option value="${numero}">${numero}</option>`)
      .join("");

    // Reinicializar Select2 para asegurar que tome los nuevos datos y funcione dentro del modal
    if (window.jQuery) {
        const $sel = jQuery(selectorContrato);
        if ($sel.data('select2')) { $sel.select2('destroy'); }
        $sel.select2({
            dropdownParent: jQuery('#visor-modal'),
            width: '100%',
            placeholder: "Seleccione un contrato..."
        });
        $sel.trigger('change');
    }

    if (contratosDisponibles.length === 0) {
      throw new Error("No se encontraron contratos para visualizar.");
    }

    await generarYMostrarContrato(contratosDisponibles[0]);
    visorModal.showModal();
  } catch (err) {
    setEstado(`Error al abrir soporte: ${err.message}`, true);
  }
});

// Listener definitivo para el cambio de contrato (manejando tanto Select2 como nativo)
if (window.jQuery) {
    jQuery(selectorContrato).on('select2:select', async function(e) {
        const contratoSeleccionado = e.params.data.id;
        try {
            await generarYMostrarContrato(contratoSeleccionado);
        } catch (err) {
            setEstado(`Error al cambiar contrato: ${err.message}`, true);
        }
    });
}

selectorContrato.addEventListener("change", async (e) => {
    // Solo actuar si no hay jQuery/Select2 manejando esto ya
    if (window.jQuery && jQuery(selectorContrato).data('select2')) return;
    
    const contratoSeleccionado = e.target.value;
    if (!contratoSeleccionado) return;
    try {
        await generarYMostrarContrato(contratoSeleccionado);
    } catch (err) {
        setEstado(`Error al cambiar contrato: ${err.message}`, true);
    }
});

cerrarModal.addEventListener("click", () => {
  visorModal.close();
  visorPdf.src = "";
  selectorContrato.innerHTML = "";
  pdfUnicoActualUrl = null;
});
