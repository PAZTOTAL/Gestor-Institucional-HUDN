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

  // Helper to get CSRF token from cookies
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const setMessage = (text, type = "info") => {
    message.textContent = text || "";
    message.className = "mt-4 text-center font-bold text-sm";
    if (type === "error") {
      message.classList.add("text-red-600");
    } else {
      message.classList.add("text-blue-600");
    }
  };

  const setLoading = (value, actionText) => {
    loading = value;
    const disabled = loading || !cedulaInput.value.trim();
    btnBuscar.disabled = disabled;
    btnGenerar.disabled = disabled;
    
    if (loading) {
        if (actionText === "buscar") btnBuscar.textContent = "Buscando...";
        if (actionText === "generar") btnGenerar.textContent = "Generando...";
    } else {
        btnBuscar.textContent = "Visualizar Datos";
        btnGenerar.textContent = "Generar documento";
    }
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
      tr.className = "hover:bg-slate-50 transition-colors";
      const columns = [
        item.no_contrato || item.contratoNo || "",
        item.fecha_firma || item.firmaContrato || "",
        item.fecha_inicio || item.fechaInicio || "",
        item.fecha_terminacion || item.fechaTerminacion || "",
        item.valor_cto || item.valor || "",
      ];
      tr.innerHTML = columns.map((col) => `<td class="px-4 py-3 text-slate-700 font-medium">${String(col)}</td>`).join("");
      resContratos.appendChild(tr);
    });
    results.classList.remove("hidden");
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
    setMessage("Consultando base de datos...", "info");
    
    try {
      const response = await fetch("./api/consultar-contratos/", {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie('csrftoken')
        },
        body: JSON.stringify({ cedula }),
      });
      
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "No se encontró la cédula o NIT");
      }
      data = payload;
      renderResults(data);
      setMessage("Datos cargados correctamente. Ahora puede generar el documento.", "info");
    } catch (error) {
      data = null;
      renderResults(null);
      setMessage(error.message || "Error en la consulta.", "error");
    } finally {
      setLoading(false);
    }
  };

  const generarCertificado = async () => {
    const cedula = cedulaInput.value.trim();
    if (!cedula) return;
    
    setLoading(true, "generar");
    setMessage("Generando documento...", "info");
    
    // Usar un formulario oculto para una descarga más robusta (estilo clásico MVP)
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "./api/generar-certificado/";
    form.style.display = "none";

    const fields = {
        "cedula": cedula,
        "genero": genero,
        "csrfmiddlewaretoken": getCookie("csrftoken")
    };

    for (const [name, value] of Object.entries(fields)) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = name;
        input.value = value;
        form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
    
    setTimeout(() => {
        setLoading(false);
        setMessage("Documento generado.", "success");
    }, 2000);
  };

  cedulaInput.addEventListener("input", () => setLoading(false));
  btnBuscar.addEventListener("click", buscar);
  btnGenerar.addEventListener("click", generarCertificado);
  btnMasculino.addEventListener("click", () => selectGenero("masculino"));
  btnFemenino.addEventListener("click", () => selectGenero("femenino"));
  
  // Enter key support
  cedulaInput.addEventListener("keypress", (e) => {
    if (e.key === 'Enter') buscar();
  });

  setLoading(false);
})();
