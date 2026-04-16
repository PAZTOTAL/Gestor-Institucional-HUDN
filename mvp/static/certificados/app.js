(() => {
  const cedulaInput = document.getElementById("cedula");
  const btnBuscar = document.getElementById("btn-buscar");
  const btnGenerar = document.getElementById("btn-generar");
  const btnMasculino = document.getElementById("btn-masculino");
  const btnFemenino = document.getElementById("btn-femenino");
  const message = document.getElementById("message");
  const results = document.getElementById("results");
  const resNombre = document.getElementById("res-nombre");
  const resCedula = document.getElementById("res-cedula");
  const resTotal = document.getElementById("res-total");
  const resContratos = document.getElementById("res-contratos");

  let genero = "masculino";
  let loading = false;
  let data = null;

  const setMessage = (text) => {
    message.textContent = text || "";
  };

  const setLoading = (value, actionText) => {
    loading = value;
    const disabled = loading || !cedulaInput.value.trim();
    btnBuscar.disabled = disabled;
    btnGenerar.disabled = disabled;
    btnBuscar.textContent = loading && actionText === "buscar" ? "Buscando..." : "Buscar";
    btnGenerar.textContent = loading && actionText === "generar" ? "Generando..." : "Generar";
  };

  const renderResults = (payload) => {
    if (!payload) {
      results.classList.add("hidden");
      resContratos.innerHTML = "";
      return;
    }

    const contratos = payload.contratos || [];
    resNombre.textContent = payload.nombre || "";
    resCedula.textContent = payload.cedula || "";
    resTotal.textContent = String(contratos.length);
    resContratos.innerHTML = "";
    contratos.forEach((item, index) => {
      const tr = document.createElement("tr");
      const columns = [
        item.no_contrato || item.contratoNo || "",
        item.fecha_firma || item.firmaContrato || "",
        item.fecha_inicio || item.fechaInicio || "",
        item.fecha_terminacion || item.fechaTerminacion || "",
        item.valor_cto || item.valor || "",
      ];
      tr.innerHTML = columns.map((col) => `<td>${String(col)}</td>`).join("");
      tr.dataset.key = `${item.no_contrato || item.contratoNo || "c"}-${index}`;
      resContratos.appendChild(tr);
    });
    results.classList.remove("hidden");
  };

  const selectGenero = (value) => {
    genero = value;
    btnMasculino.classList.toggle("active", genero === "masculino");
    btnFemenino.classList.toggle("active", genero === "femenino");
  };

  const buscar = async () => {
    const cedula = cedulaInput.value.trim();
    if (!cedula) return;
    setLoading(true, "buscar");
    setMessage("");
    try {
      const response = await fetch(`/api/empleados/${encodeURIComponent(cedula)}`);
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.message || "No se encontró la cédula o NIT");
      }
      data = payload;
      renderResults(data);
      setMessage("Consulta exitosa.");
    } catch (error) {
      data = null;
      renderResults(null);
      setMessage(error.message || "Error en la consulta.");
    } finally {
      setLoading(false);
    }
  };

  const generarCertificado = async () => {
    const cedula = cedulaInput.value.trim();
    if (!cedula) return;
    setLoading(true, "generar");
    setMessage("");
    try {
      const response = await fetch("/api/certificados", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cedula, genero }),
      });
      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload.message || "No fue posible generar el certificado");
      }
      const blob = await response.blob();
      const disposition = response.headers.get("content-disposition") || "";
      const match = disposition.match(/filename=\"?([^\";]+)\"?/i);
      const filename = match ? match[1] : `certificado_${cedula}.docx`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.style.display = "none";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 2000);
      setMessage("Certificado generado correctamente.");
    } catch (error) {
      setMessage(error.message || "No fue posible generar el certificado");
    } finally {
      setLoading(false);
    }
  };

  cedulaInput.addEventListener("input", () => setLoading(false));
  btnBuscar.addEventListener("click", buscar);
  btnGenerar.addEventListener("click", generarCertificado);
  btnMasculino.addEventListener("click", () => selectGenero("masculino"));
  btnFemenino.addEventListener("click", () => selectGenero("femenino"));
  setLoading(false);
})();
