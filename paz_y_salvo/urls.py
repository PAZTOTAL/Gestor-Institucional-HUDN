from django.urls import path
from .views.template_views import paz_y_salvo_landing, paz_y_salvo_panel, validar_por_token_page, pys_logout_view, solicitud_publica_page
from .views.auth_views import LoginView, LogoutView, MeView
from .views.paz_salvos_views import (
    PazSalvoListCreateView,
    PazSalvoEstadisticasView,
    PazSalvoDetailView,
    PazSalvoArchivarView,
    PazSalvoEstadoView,
)
from .views.validaciones_views import (
    ValidarView,
    RechazarView,
    RevalidarView,
    MisPendientesView,
    MisValidacionesView,
    ValidarPorTokenView,
)
from .views.solicitudes_views import (
    SolicitudPSCreateView,
    SolicitudPSListView,
    SolicitudPSProcesarView,
    ArchivoSolicitudView,
    EncuestaRetiroExisteView,
    EncuestaRetiroCreateView,
    EncuestaRetiroListView,
    EncuestaRetiroExportView,
)
from .views.admin_views import (
    ListaBlancaListCreateView,
    ListaBlancaDetailView,
    AreaListView,
    AreaDetailView,
    FirmanteConfigListCreateView,
    FirmanteConfigDetailView,
    CatalogoCargosView,
    CatalogoDependenciasView,
    CatalogoCoordinadoresView,
    BuscarFuncionarioPYSView,
)
from .views.logs_views import LogAccesosView, LogCorreosView, LogEstadisticasView

urlpatterns = [
    # Auth
    path('auth/login', LoginView.as_view(), name='pys_login'),
    path('auth/logout', LogoutView.as_view(), name='pys_logout'),
    path('auth/me', MeView.as_view(), name='pys_me'),

    # Paz y Salvos
    path('paz-salvos', PazSalvoListCreateView.as_view(), name='pys_list_create'),
    path('paz-salvos/estadisticas/resumen', PazSalvoEstadisticasView.as_view(), name='pys_estadisticas'),
    path('paz-salvos/<int:ps_id>', PazSalvoDetailView.as_view(), name='pys_detail'),
    path('paz-salvos/<int:ps_id>/archivar', PazSalvoArchivarView.as_view(), name='pys_archivar'),
    path('paz-salvos/<int:ps_id>/estado', PazSalvoEstadoView.as_view(), name='pys_estado'),

    # Validaciones
    path('validar/mis-pendientes', MisPendientesView.as_view(), name='pys_mis_pendientes'),
    path('validar/mis-validaciones', MisValidacionesView.as_view(), name='pys_mis_validaciones'),
    path('validar/por-token', ValidarPorTokenView.as_view(), name='pys_por_token'),
    path('validar/<int:ps_id>', ValidarView.as_view(), name='pys_validar'),
    path('validar/<int:ps_id>/rechazar', RechazarView.as_view(), name='pys_rechazar'),
    path('validar/<int:ps_id>/revalidar', RevalidarView.as_view(), name='pys_revalidar'),

    # Solicitudes públicas
    path('solicitudes/paz-salvo', SolicitudPSCreateView.as_view(), name='pys_sol_create'),
    path('solicitudes', SolicitudPSListView.as_view(), name='pys_sol_list'),
    path('solicitudes/<int:sol_id>/procesar', SolicitudPSProcesarView.as_view(), name='pys_sol_procesar'),
    path('solicitudes/archivo/<int:archivo_id>', ArchivoSolicitudView.as_view(), name='pys_archivo'),
    path('solicitudes/encuesta-retiro/existe/<str:identificacion>', EncuestaRetiroExisteView.as_view(), name='pys_enc_existe'),
    path('solicitudes/encuesta-retiro', EncuestaRetiroCreateView.as_view(), name='pys_enc_create'),
    path('encuestas', EncuestaRetiroListView.as_view(), name='pys_enc_list'),
    path('encuestas/exportar', EncuestaRetiroExportView.as_view(), name='pys_enc_export'),

    # Búsqueda de funcionario por cédula (público)
    path('funcionario/buscar', BuscarFuncionarioPYSView.as_view(), name='pys_buscar_func'),

    # Admin
    path('admin/lista-blanca', ListaBlancaListCreateView.as_view(), name='pys_admin_lb_list'),
    path('admin/lista-blanca/<int:lb_id>', ListaBlancaDetailView.as_view(), name='pys_admin_lb_detail'),
    path('admin/areas', AreaListView.as_view(), name='pys_admin_areas'),
    path('admin/areas/<int:area_id>', AreaDetailView.as_view(), name='pys_admin_area_detail'),
    path('admin/firmantes-config', FirmanteConfigListCreateView.as_view(), name='pys_firmantes_list'),
    path('admin/firmantes-config/<int:cfg_id>', FirmanteConfigDetailView.as_view(), name='pys_firmantes_detail'),
    path('admin/catalogos/cargos', CatalogoCargosView.as_view(), name='pys_catalogos_cargos'),
    path('admin/catalogos/dependencias', CatalogoDependenciasView.as_view(), name='pys_catalogos_dep'),
    path('admin/catalogos/coordinadores', CatalogoCoordinadoresView.as_view(), name='pys_catalogos_coord'),

    # Logs
    path('logs/accesos', LogAccesosView.as_view(), name='pys_logs_accesos'),
    path('logs/correos', LogCorreosView.as_view(), name='pys_logs_correos'),
    path('logs/estadisticas', LogEstadisticasView.as_view(), name='pys_logs_stats'),
]

# Template (HTML) views — registered separately in main urls.py under paz-y-salvo/
template_urlpatterns = [
    path('', paz_y_salvo_landing, name='pys_landing'),
    path('panel/', paz_y_salvo_panel, name='pys_panel'),
    path('solicitud/', solicitud_publica_page, name='pys_solicitud_publica'),
    path('validar/', validar_por_token_page, name='pys_validar_page'),
    path('logout/', pys_logout_view, name='pys_logout_view'),
]
