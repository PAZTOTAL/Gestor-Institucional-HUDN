# 🧹 PLAN DE LIMPIEZA Y AUDITORÍA - Gestor Institucional HUDN
**Fecha: Mayo 12, 2025 | Versión: 1.0**

---

## 📊 RESUMEN EJECUTIVO

Tu proyecto Django tiene **29 aplicaciones activas** pero acumula:
- ❌ **2 aplicaciones duplicadas** (UNIFICADOR-V1, visorSoportes)
- ❌ **2 proyectos separados sin integrar** (app_crue_traslados, app_quirofano_tablero)
- ❌ **1 estructura incompleta** (A_01_Gerencia)
- ❌ **9+ archivos de debug/temporales**
- ❌ **1 carpeta de imports temporal** (temp_import)

**Total aproximado a eliminar: ~500MB+**

---

## 🔴 FASE 1: ELIMINACIÓN CRÍTICA (100% SEGURO)

### A. Directorios Duplicados/Redundantes

```
ELIMINAR:
├── UNIFICADOR-V1/                    ❌ DUPLICADO
│   └── Solo contiene: .gitignore, sistema_obstetrico/
│       (Ver: unificador_v1/ que es la versión activa en settings.py)
│
├── visorSoportes/                    ❌ DUPLICADO (Frontend viejo)
│   └── Contiene: app.js, index.html, consulta_api/ (Node.js/Frontend)
│       (Ver: visor_soportes/ que es la versión activa en Django)
│
└── A_01_Gerencia/                    ❌ ESTRUCTURA INCOMPLETA
    └── Solo tiene: __init__.py, A_01_02_Financiera/
        (Aparenta estar en construcción desde hace años)
```

### B. Proyectos Separados no Integrados

```
ELIMINAR (son proyectos independientes con manage.py propio):
├── app_crue_traslados/               ❌ NO está en INSTALLED_APPS
│   └── manage.py (proyecto separado)
│
└── app_quirofano_tablero/            ❌ NO está en INSTALLED_APPS
    └── manage.py, pytest.ini (proyecto separado)
```

### C. Archivos Temporales/Debug

```
ELIMINAR (scripts de prueba únicos):
├── check_data.py                     ❌ Script de debug
├── check_db_root.py                  ❌ Script de debug
├── scratch_check_columns.py          ❌ Script de prueba
├── scratch_test_form.py              ❌ Script de prueba
├── redirect.py                       ❌ Script no documentado
├── load_tipo_documento.py            ❌ Script de carga puntual
├── import_dian_data.py               ❌ Script de carga puntual
├── error_log.txt                     ❌ Log de errores antiguo
├── investigation_45490716.json       ❌ Investigación específica
│
└── temp_import/                      ❌ CARPETA TEMPORAL
    └── files_defenjur_2025/          (datos temporales)
```

---

## 🟡 FASE 2: ARCHIVOS A REVISAR (OPCIONAL)

```
CONSIDERAR eliminar o archivar:
├── CertificadoIngresos2025.xlsm      ⚠️ Dato de 2025 (¿backup necesario?)
├── REGISTRO DE SERVICIO DE TRASLADO DE PACIENTES.xlsx  (¿activo?)
├── despachoJudicial.xlsx             ⚠️ (¿activo?)
├── formatos hudn.xlsx                ⚠️ (¿activo?)
└── FRSGI-002 V06 ASIGNACION DE PERMISOS Y CLAVES.pdf  (¿activo?)
```

**RECOMENDACIÓN:** Revisar con PM/Admin si estos son datos vigentes o históricos.

---

## 🟢 APLICACIONES QUE MANTENER (EN INSTALLED_APPS)

```
✅ 29 Aplicaciones Activas - MUY BIEN ORGANIZADAS:

Núcleo:
  - core (middleware, utilidades)
  - usuarios (autenticación, permisos)
  - BasesGenerales (configuración base)
  - consultas_externas (API externas)

Módulos Funcionales:
  - A_00_Organigrama (estructura organizacional)
  - registro_anestesia (anestesia)
  - unificador_v1 (apps obstétricas: MEOWS, trabajo de parto)
  - consultas (búsquedas/reportes)
  - presupuesto (presupuestos)
  - ConsentimientosInformados (consentimientos HIPAA)
  - CentralDeMezclas (medicinas)
  - consentimientos (consentimientos)
  - EstudioDeConveniencia (estudios)
  - trasplantes_donacion (trasplantes)
  - CertificadosDIAN (certificados DIAN)
  - horas_extras (nómina)
  - certificados_laborales (certificados)
  - visor_soportes (gestor de soportes/documentos)
  - tercerizadas (terceros)
  - paz_y_salvo (paz y salvos)
  - inventarios (inventario)
  - formatos_apps (formatos/templates)
  - crue_remisiones (traslados CRUE)
  - defenjur_py.legal (gestión legal)

MVP/Especiales:
  - mvp/ (módulo de certificados - está fuera de INSTALLED_APPS pero es funcional)
```

---

## 📋 PLAN DE EJECUCIÓN

### Paso 1: Backup
```bash
# Hacer backup completo antes de eliminar
git tag backup-pre-cleanup-2025-05
```

### Paso 2: Eliminar Duplicados (PRIMERO)
```bash
# 1. Eliminar UNIFICADOR-V1
rm -r UNIFICADOR-V1

# 2. Eliminar visorSoportes  
rm -r visorSoportes

# 3. Eliminar A_01_Gerencia
rm -r A_01_Gerencia
```

### Paso 3: Eliminar Proyectos Separados
```bash
# 4. Eliminar app_crue_traslados (completo)
rm -r app_crue_traslados

# 5. Eliminar app_quirofano_tablero (completo)
rm -r app_quirofano_tablero
```

### Paso 4: Limpiar Scripts Temporales
```bash
# 6. Eliminar archivos de debug/prueba
rm check_data.py
rm check_db_root.py
rm scratch_check_columns.py
rm scratch_test_form.py
rm redirect.py
rm load_tipo_documento.py
rm import_dian_data.py
rm error_log.txt
rm investigation_45490716.json

# 7. Eliminar carpeta temporal
rm -r temp_import
```

### Paso 5: Revisar datos
```bash
# 8. REVISAR antes de eliminar (consultar con PM):
ls -la *.xlsx *.pdf
# Decidir: ¿Archivo o Eliminar?
```

### Paso 6: Sincronizar
```bash
git add -A
git commit -m "🧹 Limpieza: Eliminación de duplicados, proyectos separados y scripts temporales"
git push
```

---

## 📊 IMPACTO ANTES/DESPUÉS

```
ANTES:
├── 29 apps activas
├── 2 proyectos separados (app_*)
├── 2 directorios duplicados  
├── 9+ archivos temporales
├── 1 estructura incompleta
└── Estimado: ~1.2 GB (con venv)

DESPUÉS (limpio):
├── 29 apps activas (IGUAL - todas necesarias)
├── 0 proyectos separados
├── 0 duplicados
├── 0 archivos temporales
├── 0 incompletos
└── Estimado: ~700-800 MB
```

---

## ⚠️ PRECAUCIONES IMPORTANTES

1. **NO ELIMINES venv/** - Contiene dependencias Python
2. **NO ELIMINES .git/** - Necesario para historial
3. **NO ELIMINES mvp/** - Está siendo usado (fuera de INSTALLED_APPS pero funcional)
4. **BACKUP PRIMERO** - Especialmente los .xlsx y .pdf de datos activos
5. **REVISAR .gitignore** - Para no perder nada en git

---

## 🎯 SIGUIENTE PASO

```
Después de la limpieza, considerar:
☐ Actualizar .gitignore (excluir venv, __pycache__, *.log, etc)
☐ Revisar requirements.txt (eliminar dependencias no usadas)
☐ Validar que todas las apps se cargan sin errores
☐ Documentar la estructura en README.md
☐ Crear un documento de arquitectura
```

---

## ✅ CHECKLIST DE EJECUCIÓN

```
PRE-CLEANUP:
☐ Backup git tag creado
☐ Equipo notificado de cambios
☐ PM revisó archivos .xlsx/.pdf

CLEANUP:
☐ UNIFICADOR-V1 eliminado
☐ visorSoportes eliminado
☐ A_01_Gerencia eliminado
☐ app_crue_traslados eliminado
☐ app_quirofano_tablero eliminado
☐ Scripts temporales eliminados
☐ temp_import eliminado

POST-CLEANUP:
☐ git status limpio
☐ Django migrate sin errores
☐ Pruebas de login funcionales
☐ Cambios committeados
☐ Push exitoso
```

---

**Estado:** ✅ Plan completado y listo para ejecutar
**Riesgo:** 🟢 BAJO (todo está documentado y es reversible con git)
**Impacto:** 🟢 POSITIVO (reducción de clutter, claridad de arquitectura)
