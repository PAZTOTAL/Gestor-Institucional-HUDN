from django.urls import path
from . import views

app_name = 'mezclas'

urlpatterns = [
    # Selector Principal
    path('', views.CentralDeMezclasMainView.as_view(), name='main'),
    # Medicamentos Estériles
    path('esteriles/', views.EsterilesDashboardView.as_view(), name='esteriles_panel'),
    path('esteriles/medicamentos/', views.MedicamentoEsterilListView.as_view(), name='esteriles_med_list'),
    path('esteriles/medicamentos/nuevo/', views.MedicamentoEsterilCreateView.as_view(), name='esteriles_med_crear'),
    path('esteriles/medicamentos/editar/<int:pk>/', views.MedicamentoEsterilUpdateView.as_view(), name='esteriles_med_editar'),
    path('esteriles/medicamentos/eliminar/<int:pk>/', views.MedicamentoEsterilDeleteView.as_view(), name='esteriles_med_eliminar'),
    
    # Matriz Unidosis Adultos
    path('esteriles/unidosis/', views.UnidosisPeriodoListView.as_view(), name='unidosis_list'),
    path('esteriles/unidosis/nuevo-periodo/', views.UnidosisPeriodoCreateView.as_view(), name='unidosis_periodo_crear'),
    path('esteriles/unidosis/matriz/<int:pk>/', views.UnidosisMatrizView.as_view(), name='unidosis_matriz'),
    path('esteriles/unidosis/nueva-preparacion/<int:periodo_id>/', views.UnidosisOrdenCreateView.as_view(), name='unidosis_orden_crear'),

    # Panel de Operaciones (Reempaque y Reenvase)
    path('reempaque/', views.ReempaquePanelView.as_view(), name='reempaque_panel'),
    
    # Mezclas Magistrales
    path('orden/nueva/', views.MezclaOrdenCreateView.as_view(), name='orden_crear'),
    path('orden/<int:pk>/', views.MezclaOrdenDetailView.as_view(), name='orden_detalle'),
    
    # Reempaque y Reenvase (RV-RS)
    path('reempaque/medicamentos/', views.ReempaqueMedicamentoListView.as_view(), name='reempaque_med_list'),
    path('reempaque/medicamentos/nuevo/', views.ReempaqueMedicamentoCreateView.as_view(), name='reempaque_med_crear'),
    path('reempaque/medicamentos/editar/<int:pk>/', views.ReempaqueMedicamentoUpdateView.as_view(), name='reempaque_med_editar'),
    path('reempaque/medicamentos/eliminar/<int:pk>/', views.ReempaqueMedicamentoDeleteView.as_view(), name='reempaque_med_eliminar'),
    path('reempaque/orden/nueva/', views.ReempaqueOrdenCreateView.as_view(), name='reempaque_orden_crear'),
    path('reempaque/orden/editar/<int:pk>/', views.ReempaqueOrdenUpdateView.as_view(), name='reempaque_orden_editar'),
    path('reempaque/orden/eliminar/<int:pk>/', views.ReempaqueOrdenDeleteView.as_view(), name='reempaque_orden_eliminar'),
    path('reempaque/matriz/', views.ReempaqueMatrizView.as_view(), name='reempaque_matriz'),
    path('reempaque/etiqueta/<int:pk>/', views.ReempaqueEtiquetaView.as_view(), name='reempaque_etiqueta'),
    path('reempaque/control/<int:orden_id>/', views.ReempaqueControlCreateView.as_view(), name='reempaque_control'),
    path('reempaque/alistamiento/', views.ReempaqueAlistamientoView.as_view(), name='reempaque_alistamiento'),
    path('reempaque/muestreo/', views.ReempaqueMuestreoView.as_view(), name='reempaque_muestreo'),
    path('reempaque/norma/', views.ReempaqueNormaView.as_view(), name='reempaque_norma'),
    
    # Exportaciones (XLS/PDF)
    path('export/catalogo/xls/', views.export_reempaque_xls, name='export_catalogo_xls'),
    path('export/matriz/xls/', views.export_matriz_xls, name='export_matriz_xls'),
    path('export/matriz/pdf/', views.export_matriz_pdf, name='export_matriz_pdf'),
    
    # API para búsqueda de pacientes y personal (HUDN)
    path('api/buscar-tercero-hudn/', views.api_buscar_tercero_hudn, name='api_buscar_tercero_hudn'),
    path('api/buscar-personal-hudn/', views.api_buscar_personal_hudn, name='api_buscar_personal_hudn'),

    # API para búsqueda de pacientes y medicamentos
    path('api/buscar-pacientes/', views.buscar_pacientes, name='api_buscar_pacientes'),
    path('api/medicamento/<int:pk>/', views.api_get_medicamento, name='api_get_medicamento'),
    path('api/cargar-matriz-unidosis/', views.api_cargar_matriz_unidosis, name='api_cargar_matriz'),
    path('formulas-area/', views.ConsultaFormulasAreaView.as_view(), name='formulas_area'),
    path('api/formulas-area/<str:area_id>/', views.api_formulas_por_area, name='api_formulas_area'),

    # Convenciones y Alertas
    path('config/convenciones/', views.ConvencionListView.as_view(), name='convencion_list'),
    path('config/convenciones/nueva/', views.ConvencionCreateView.as_view(), name='convencion_crear'),
    path('config/convenciones/editar/<int:pk>/', views.ConvencionUpdateView.as_view(), name='convencion_editar'),
    path('config/convenciones/eliminar/<int:pk>/', views.ConvencionDeleteView.as_view(), name='convencion_eliminar'),
    
    path('config/alertas/', views.AlertaListView.as_view(), name='alerta_list'),
    path('config/alertas/nueva/', views.AlertaCreateView.as_view(), name='alerta_crear'),
    path('config/alertas/editar/<int:pk>/', views.AlertaUpdateView.as_view(), name='alerta_editar'),
    path('config/alertas/eliminar/<int:pk>/', views.AlertaDeleteView.as_view(), name='alerta_eliminar'),

    # ─── Panel Oncológicos ───
    path('oncologicos/', views.OncologicoPanelView.as_view(), name='onco_panel'),

    # FRFAR-126 Base de Datos
    path('oncologicos/base-datos/', views.MedicamentoOncologicoListView.as_view(), name='oncologicos_list'),
    path('oncologicos/base-datos/nuevo/', views.MedicamentoOncologicoCreateView.as_view(), name='oncologicos_nuevo'),
    path('oncologicos/base-datos/editar/<int:pk>/', views.MedicamentoOncologicoUpdateView.as_view(), name='oncologicos_editar'),
    path('oncologicos/base-datos/eliminar/<int:pk>/', views.MedicamentoOncologicoDeleteView.as_view(), name='oncologicos_eliminar'),
    path('oncologicos/base-datos/export/xls/', views.export_oncologicos_xls, name='oncologicos_export_xls'),

    # FRFAR-127 Matriz Oncológica
    path('oncologicos/matriz/', views.OncologicoMatrizListView.as_view(), name='onco_matriz_list'),
    path('oncologicos/matriz/crear/', views.OncologicoMatrizCreateView.as_view(), name='onco_matriz_crear'),
    path('oncologicos/matriz/<int:pk>/', views.OncologicoMatrizDetailView.as_view(), name='onco_matriz_detalle'),
    path('oncologicos/matriz/<int:pk>/eliminar/', views.OncologicoMatrizDeleteView.as_view(), name='onco_matriz_eliminar'),
    path('oncologicos/matriz/<int:matriz_pk>/item/crear/', views.OncologicoMatrizItemCreateView.as_view(), name='onco_matriz_item_crear'),
    path('oncologicos/matriz/item/<int:pk>/eliminar/', views.OncologicoMatrizItemDeleteView.as_view(), name='onco_matriz_item_eliminar'),

    # FRFAR-178 Orden de Producción Oncológica
    path('oncologicos/orden-produccion/', views.OncologicoOrdenListView.as_view(), name='onco_orden_list'),
    path('oncologicos/orden-produccion/crear/', views.OncologicoOrdenCreateView.as_view(), name='onco_orden_crear'),
    path('oncologicos/orden-produccion/<int:pk>/', views.OncologicoOrdenDetailView.as_view(), name='onco_orden_detalle'),
    path('oncologicos/orden-produccion/<int:pk>/eliminar/', views.OncologicoOrdenDeleteView.as_view(), name='onco_orden_eliminar'),
    path('oncologicos/orden-produccion/<int:orden_pk>/item/crear/', views.OncologicoOrdenItemCreateView.as_view(), name='onco_orden_item_crear'),
    path('oncologicos/orden-produccion/item/<int:pk>/eliminar/', views.OncologicoOrdenItemDeleteView.as_view(), name='onco_orden_item_eliminar'),

    # FRFAR-162 Alistamiento y Conciliación
    path('oncologicos/alistamiento/', views.OncologicoAlistamientoListView.as_view(), name='onco_alistamiento_list'),
    path('oncologicos/alistamiento/crear/', views.OncologicoAlistamientoCreateView.as_view(), name='onco_alistamiento_crear'),
    path('oncologicos/alistamiento/<int:pk>/', views.OncologicoAlistamientoDetailView.as_view(), name='onco_alistamiento_detalle'),
    path('oncologicos/alistamiento/<int:pk>/eliminar/', views.OncologicoAlistamientoDeleteView.as_view(), name='onco_alistamiento_eliminar'),
    path('oncologicos/alistamiento/<int:alistamiento_pk>/item/crear/', views.OncologicoAlistamientoItemCreateView.as_view(), name='onco_alistamiento_item_crear'),
    path('oncologicos/alistamiento/item/<int:pk>/eliminar/', views.OncologicoAlistamientoItemDeleteView.as_view(), name='onco_alistamiento_item_eliminar'),

    # Neonatos Rediseñado
    path('neonatos/', views.NeonatosPanelView.as_view(), name='neonatos_panel'),
    path('neonatos/matrices/', views.NeonatosListView.as_view(), name='neonatos_list'),
    path('neonatos/nueva/', views.NeonatosCreateView.as_view(), name='neonatos_crear'),
    path('neonatos/base-datos/', views.NeonatosMedicamentoListView.as_view(), name='neonatos_med_list'),
    path('neonatos/base-datos/nuevo/', views.NeonatosMedicamentoCreateView.as_view(), name='neonatos_med_nuevo'),
    path('neonatos/base-datos/editar/<int:pk>/', views.NeonatosMedicamentoUpdateView.as_view(), name='neonatos_med_editar'),
    path('neonatos/base-datos/eliminar/<int:pk>/', views.NeonatosMedicamentoDeleteView.as_view(), name='neonatos_med_eliminar'),
    path('neonatos/pacientes-activos/', views.NeonatosPacientesActivosView.as_view(), name='neonatos_pacientes_activos'),
    path('api/formulas-neonatos/', views.api_formulas_neonatos, name='api_formulas_neonatos'),

    # Unidosis Producción (Ex-Magistrales)
    path('unidosis-prod/', views.UnidosisProduccionListView.as_view(), name='unidosis_prod_list'),
    path('unidosis-prod/nueva/', views.UnidosisProduccionCreateView.as_view(), name='unidosis_prod_crear'),

    # Nutriciones Parenterales
    path('nutricion/', views.NptPanelView.as_view(), name='nutricion_panel'),
    path('nutricion/matrices/', views.NptListView.as_view(), name='nutricion_list'),
    path('nutricion/nueva/', views.NptCreateView.as_view(), name='nutricion_crear'),

    # Procesos Diarios y Reportes
    path('procesos-diarios/', views.ProcesosDiariosView.as_view(), name='procesos_diarios'),
    path('procesos-diarios/pdf/', views.generar_informe_diario_pdf, name='informe_diario_pdf'),

]
