/**
 * Caché en sessionStorage para /atencion/api/datos-paciente-unificado/
 * Evita repetir la misma consulta al cambiar entre MEOWS, fetal y parto.
 */
(function (global) {
    var STORAGE_KEY = 'obstetricia_paciente_unificado_v1';
    var TTL_MS = 8 * 60 * 1000;

    function now() {
        return Date.now();
    }

    function save(doc, payload) {
        var d = String(doc || '').trim();
        if (!d || !payload) return;
        try {
            sessionStorage.setItem(
                STORAGE_KEY,
                JSON.stringify({ doc: d, payload: payload, ts: now() })
            );
        } catch (e) {
            console.warn('paciente_unificado_cache: no se pudo guardar', e);
        }
    }

    function loadForDoc(doc) {
        var d = String(doc || '').trim();
        if (!d) return null;
        try {
            var raw = sessionStorage.getItem(STORAGE_KEY);
            if (!raw) return null;
            var st = JSON.parse(raw);
            if (!st || st.doc !== d || !st.payload) return null;
            if (now() - (st.ts || 0) > TTL_MS) return null;
            return st.payload;
        } catch (e) {
            return null;
        }
    }

    function invalidate() {
        try {
            sessionStorage.removeItem(STORAGE_KEY);
        } catch (e) {}
    }

    async function fetchUnificado(doc) {
        var d = String(doc || '').trim();
        if (!d) return null;
        var url =
            global.location.origin +
            '/atencion/api/datos-paciente-unificado/?num_identificacion=' +
            encodeURIComponent(d) +
            '&_=' +
            now();
        var r = await fetch(url, {
            method: 'GET',
            headers: { Accept: 'application/json' },
            credentials: 'same-origin',
        });
        if (!r.ok) return null;
        var data = await r.json();
        if (data.ok && data.encontrado) {
            save(d, data);
            return data;
        }
        return null;
    }

    async function ensure(doc, opts) {
        opts = opts || {};
        var d = String(doc || '').trim();
        if (!d) return null;
        if (!opts.forceRefresh) {
            var cached = loadForDoc(d);
            if (cached) return cached;
        }
        return await fetchUnificado(d);
    }

    /**
     * Último paciente guardado en sesión (misma pestaña), si sigue vigente por TTL.
     * Sirve para volver a Sala de Partos desde MEOWS/Fetal/Parto sin pasar otra vez por la búsqueda.
     */
    function getValidCached() {
        try {
            var raw = sessionStorage.getItem(STORAGE_KEY);
            if (!raw) return null;
            var st = JSON.parse(raw);
            if (!st || !st.doc || !st.payload) return null;
            if (now() - (st.ts || 0) > TTL_MS) return null;
            return { doc: String(st.doc).trim(), payload: st.payload };
        } catch (e) {
            return null;
        }
    }

    global.ObstetriciaPacienteUnificado = {
        STORAGE_KEY: STORAGE_KEY,
        TTL_MS: TTL_MS,
        save: save,
        loadForDoc: loadForDoc,
        getValidCached: getValidCached,
        invalidate: invalidate,
        fetchUnificado: fetchUnificado,
        ensure: ensure,
    };
})(window);
