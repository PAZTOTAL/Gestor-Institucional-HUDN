from django.urls import path
from .views.template_views import (
    apc_landing, apc_panel, apc_solicitud_publica, apc_firmar, apc_logout,
    apc_coordinador, apc_coordinador_guardar_firma,
)
from .views.auth_views import LoginAdminView, MeView
from .views.solicitud_views import (
    ConfigPermisosView, ConfigSeccionesView, AreasView,
    BuscarFuncionarioView, BuscarCargosView,
    SolicitudCreateView, SolicitudListView, SolicitudDetailView,
    EmpresasTercerizadasView,
)
from .views.firma_views import FirmaDetailView, FirmarView
from .views.admin_views import (
    ListaBlancaAdminListView, ListaBlancaAdminDetailView,
    CoordinadorAreaListView, CoordinadorAreaDetailView,
    FirmantesFijosListView, FirmantesFijosDetailView,
    DestinatarioRolListView, DestinatarioRolDetailView,
    PermisoAccesoConfigListView, PermisoAccesoConfigDetailView,
    SeccionConfigListView, SeccionConfigDetailView,
    EncabezadoConfigView,
    CampoConfigListView, CampoConfigDetailView,
    CoordinadorRecargosListView, CoordinadorRecargosDetailView,
)

# API routes (JWT Bearer)
urlpatterns = [
    # Auth admin
    path('auth/login', LoginAdminView.as_view(), name='apc_login'),
    path('auth/me', MeView.as_view(), name='apc_me'),

    # Config pública del formulario
    path('config/permisos', ConfigPermisosView.as_view(), name='apc_config_permisos'),
    path('config/secciones', ConfigSeccionesView.as_view(), name='apc_config_secciones'),
    path('areas', AreasView.as_view(), name='apc_areas'),
    path('tercerizadas/empresas', EmpresasTercerizadasView.as_view(), name='apc_tercerizadas_empresas'),

    # Búsqueda de funcionario (pública)
    path('funcionario/buscar', BuscarFuncionarioView.as_view(), name='apc_buscar_func'),
    path('cargos/buscar', BuscarCargosView.as_view(), name='apc_buscar_cargos'),

    # Solicitudes
    path('solicitudes', SolicitudListView.as_view(), name='apc_sol_list'),
    path('solicitudes/crear', SolicitudCreateView.as_view(), name='apc_sol_create'),
    path('solicitudes/<int:sol_id>', SolicitudDetailView.as_view(), name='apc_sol_detail'),

    # Firma
    path('firmar', FirmaDetailView.as_view(), name='apc_firma_detail'),
    path('firmar/submit', FirmarView.as_view(), name='apc_firmar_submit'),

    # Admin — Lista blanca
    path('admin/lista-blanca', ListaBlancaAdminListView.as_view(), name='apc_admin_lb_list'),
    path('admin/lista-blanca/<int:lb_id>', ListaBlancaAdminDetailView.as_view(), name='apc_admin_lb_detail'),

    # Admin — Coordinadores por área
    path('admin/coordinadores', CoordinadorAreaListView.as_view(), name='apc_admin_coord_list'),
    path('admin/coordinadores/<int:coord_id>', CoordinadorAreaDetailView.as_view(), name='apc_admin_coord_detail'),

    # Admin — Firmantes fijos
    path('admin/firmantes-fijos', FirmantesFijosListView.as_view(), name='apc_admin_ff_list'),
    path('admin/firmantes-fijos/<int:fijo_id>', FirmantesFijosDetailView.as_view(), name='apc_admin_ff_detail'),

    # Admin — Destinatarios por rol
    path('admin/destinatarios', DestinatarioRolListView.as_view(), name='apc_admin_dest_list'),
    path('admin/destinatarios/<int:dest_id>', DestinatarioRolDetailView.as_view(), name='apc_admin_dest_detail'),

    # Admin — Config formulario
    path('admin/permisos-config', PermisoAccesoConfigListView.as_view(), name='apc_admin_perm_list'),
    path('admin/permisos-config/<int:perm_id>', PermisoAccesoConfigDetailView.as_view(), name='apc_admin_perm_detail'),
    path('admin/secciones-config', SeccionConfigListView.as_view(), name='apc_admin_sec_list'),
    path('admin/secciones-config/<int:sec_id>', SeccionConfigDetailView.as_view(), name='apc_admin_sec_detail'),
    path('admin/encabezado', EncabezadoConfigView.as_view(), name='apc_admin_encabezado'),

    # Campos de secciones 1, 2 y 4
    path('admin/campos', CampoConfigListView.as_view(), name='apc_admin_campos_list'),
    path('admin/campos/<int:campo_id>', CampoConfigDetailView.as_view(), name='apc_admin_campos_detail'),

    # Admin — Coordinadores desde horas_extras (solo gmail editable)
    path('admin/coordinadores-recargos', CoordinadorRecargosListView.as_view(), name='apc_admin_coord_recargos_list'),
    path('admin/coordinadores-recargos/<int:coord_id>', CoordinadorRecargosDetailView.as_view(), name='apc_admin_coord_recargos_detail'),
]

# Template (HTML) routes
template_urlpatterns = [
    path('', apc_landing, name='apc_landing'),
    path('panel/', apc_panel, name='apc_panel'),
    path('coordinador/', apc_coordinador, name='apc_coordinador'),
    path('coordinador/guardar-firma/', apc_coordinador_guardar_firma, name='apc_coord_guardar_firma'),
    path('solicitud/', apc_solicitud_publica, name='apc_solicitud'),
    path('firmar/', apc_firmar, name='apc_firmar'),
    path('logout/', apc_logout, name='apc_logout'),
]
