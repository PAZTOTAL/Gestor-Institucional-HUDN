from django.urls import path
from . import views
from . import api_entities

urlpatterns = [
    # ─── Dashboard ────────────────────────────────────────────────────────────
    path('', views.HomeView.as_view(), name='home'),
    path('ayuda/', views.AyudaView.as_view(), name='ayuda'),
    path('reportes/', views.ReportesView.as_view(), name='reportes'),
    path('usuarios/', views.UsuarioListView.as_view(), name='usuarios'),
    path('usuarios/nuevo/', views.UsuarioCreateView.as_view(), name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_editar'),
    path('usuarios/<int:pk>/eliminar/', views.usuario_eliminar, name='usuario_eliminar'),

    path('api/totales/', views.api_consultas_totales, name='api_consultas_totales'),
    path('api/rango-fechas/', views.api_estadisticas_rango, name='api_estadisticas_rango'),

    # API REST JSON (getAll / getDetail por entidad, mismo criterio de rol que listas web)
    path('api/entities/<slug:slug>/', api_entities.api_entity_list_view, name='api_entity_list'),
    path('api/entities/<slug:slug>/<int:pk>/', api_entities.api_entity_detail_view, name='api_entity_detail'),

    # ─── Comunes / Utilidades ──────────────────────────────────────────────────
    path('exportar/<slug:modulo>/', views.exportar_modulo_excel, name='exportar_excel'),
    path('archivos/<str:tipo>/<int:id_obj>/', views.lista_archivos_view, name='lista_archivos'),
    path('eliminar/<str:tipo>/<int:id_obj>/', views.eliminar_registro, name='eliminar_registro'),

    # ─── Extrajudicial ─────────────────────────────────────────────────────────
    path('extrajudiciales/', views.ExtrajudicialListView.as_view(), name='extrajudiciales'),
    path('extrajudiciales/conciliados/', views.ExtrajudicialConciliadosListView.as_view(), name='extrajudiciales_conciliados'),
    path('extrajudiciales/no-conciliados/', views.ExtrajudicialNoConciliadosListView.as_view(), name='extrajudiciales_no_conciliados'),
    path('extrajudiciales/nuevo/', views.ExtrajudicialCreateView.as_view(), name='extrajudicial_crear'),
    path('extrajudiciales/<int:pk>/editar/', views.ExtrajudicialUpdateView.as_view(), name='extrajudicial_editar'),

    # ─── Tutelas ──────────────────────────────────────────────────────────────
    path('tutelas/', views.TutelaListView.as_view(), name='tutelas'),
    path('tutelas/nuevo/', views.TutelaCreateView.as_view(), name='tutela_crear'),
    path('tutelas/<int:pk>/editar/', views.TutelaUpdateView.as_view(), name='tutela_editar'),

    # ─── Derechos de Petición ─────────────────────────────────────────────────
    path('peticiones/', views.PeticionListView.as_view(), name='peticiones'),
    path('peticiones/nuevo/', views.PeticionCreateView.as_view(), name='peticion_crear'),
    path('peticiones/<int:pk>/editar/', views.PeticionUpdateView.as_view(), name='peticion_editar'),

    # ─── Procesos Judiciales ──────────────────────────────────────────────────
    path('procesos/activos/', views.ProcesoActivaListView.as_view(), name='procesos_activos'),
    path('procesos/activos/nuevo/', views.ProcesoActivaCreateView.as_view(), name='proceso_activa_crear'),
    path('procesos/activos/<int:pk>/editar/', views.ProcesoActivaUpdateView.as_view(), name='proceso_activa_editar'),
    path('procesos/pasivos/', views.ProcesoPasivaListView.as_view(), name='procesos_pasivos'),
    path('procesos/pasivos/nuevo/', views.ProcesoPasivaCreateView.as_view(), name='proceso_pasiva_crear'),
    path('procesos/pasivos/<int:pk>/editar/', views.ProcesoPasivaUpdateView.as_view(), name='proceso_pasiva_editar'),
    path('procesos/terminados/', views.ProcesoTerminadoListView.as_view(), name='procesos_terminados'),
    path('procesos/terminados/nuevo/', views.ProcesoTerminadoCreateView.as_view(), name='proceso_terminado_crear'),
    path('procesos/terminados/<int:pk>/editar/', views.ProcesoTerminadoUpdateView.as_view(), name='proceso_terminado_editar'),

    # ─── Peritajes ────────────────────────────────────────────────────────────
    path('peritajes/', views.PeritajeListView.as_view(), name='peritajes'),
    path('peritajes/nuevo/', views.PeritajeCreateView.as_view(), name='peritaje_crear'),
    path('peritajes/<int:pk>/editar/', views.PeritajeUpdateView.as_view(), name='peritaje_editar'),

    # ─── Pagos de Sentencias ──────────────────────────────────────────────────
    path('pagos/', views.PagoListView.as_view(), name='pagos'),
    path('pagos/nuevo/', views.PagoCreateView.as_view(), name='pago_crear'),
    path('pagos/<int:pk>/editar/', views.PagoUpdateView.as_view(), name='pago_editar'),

    # ─── Procesos Administrativos Sancionatorios ──────────────────────────────
    path('sancionatorios/', views.SancionatorioListView.as_view(), name='sancionatorios'),
    path('sancionatorios/nuevo/', views.SancionatorioCreateView.as_view(), name='sancionatorio_crear'),
    path('sancionatorios/<int:pk>/editar/', views.SancionatorioUpdateView.as_view(), name='sancionatorio_editar'),

    # ─── Requerimientos Entes de Control ──────────────────────────────────────
    path('requerimientos/', views.RequerimientoListView.as_view(), name='requerimientos'),
    path('requerimientos/nuevo/', views.RequerimientoCreateView.as_view(), name='requerimiento_crear'),
    path('requerimientos/<int:pk>/editar/', views.RequerimientoUpdateView.as_view(), name='requerimiento_editar'),
]
