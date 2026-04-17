from django.urls import path
from . import views

app_name = 'horas_extras'

urlpatterns = [
    # ── Dashboard principal ──────────────────────────────────────────────────
    path('', views.TalentoHumanoDashboardView.as_view(), name='dashboard'),

    # ── Horas Extras (módulo original) ──────────────────────────────────────
    path('asignacion-turnos/', views.TurnosRecargosView.as_view(), name='hora_extra_list'),
    path('cargar/', views.CargarHorasView.as_view(), name='cargar'),
    path('buscar-empleado/', views.buscar_empleado, name='buscar_empleado'),

    # ── Informes ─────────────────────────────────────────────────────────────
    path('informes/', views.InformesDashboardView.as_view(), name='informes_dashboard'),
    path('informes/personal-activo/', views.PersonalActivoReportView.as_view(), name='reporte_personal_activo'),
    path('informes/personal-area/', views.PersonalPorAreaReportView.as_view(), name='reporte_personal_area'),
    path('informes/personal-temporal/', views.PersonalTemporalReportView.as_view(), name='reporte_personal_temporal'),
    path('informes/buscar-funcionario/', views.BuscarFuncionarioView.as_view(), name='buscar_funcionario'),
    path('informes/personal-area/<str:area_code>/', views.PersonalAreaDetailView.as_view(), name='reporte_personal_area_detalle'),

    # ── Recargos / Turnos (módulo nuevo) ─────────────────────────────────────
    path('horas-extra/', views.TurnosRecargosView.as_view(), name='turnos_recargos'),
    path('horas-extra/configuracion/', views.ConfiguracionRecargosView.as_view(), name='configuracion_recargos'),
    path('horas-extra/reporte/', views.ReporteRecargosView.as_view(), name='reporte_recargos'),

    # ── API Recargos ──────────────────────────────────────────────────────────
    path('horas-extra/api/areas/',                      views.api_areas,                name='api_areas'),
    path('horas-extra/api/areas/<int:pk>/',             views.api_area_detail,          name='api_area_detail'),
    path('horas-extra/api/empleados/',                  views.api_empleados,            name='api_empleados'),
    path('horas-extra/api/empleados/<int:pk>/',         views.api_empleado_detail,      name='api_empleado_detail'),
    path('horas-extra/api/turnos/',                     views.api_turnos,               name='api_turnos'),
    path('horas-extra/api/turnos/<int:pk>/',            views.api_turno_detail,         name='api_turno_detail'),
    path('horas-extra/api/festivos/',                   views.api_festivos,             name='api_festivos'),
    path('horas-extra/api/observacion-mensual/',        views.api_observacion_mensual,  name='api_observacion_mensual'),
    path('horas-extra/api/reporte-xlsx/',               views.api_reporte_xlsx,         name='api_reporte_xlsx'),
    path('horas-extra/api/reporte-area-xlsx/',          views.api_reporte_area_xlsx,    name='api_reporte_area_xlsx'),
    path('horas-extra/api/preview-area/',               views.api_preview_area,         name='api_preview_area'),
    path('horas-extra/api/reporte-pdf/',                views.api_reporte_pdf,          name='api_reporte_pdf'),
    path('horas-extra/api/coordinadores/',              views.api_coordinadores,        name='api_coordinadores'),
    path('horas-extra/api/coordinadores/<int:pk>/',     views.api_coordinador_detail,   name='api_coordinador_detail'),

    # ── Importar desde Nómina ─────────────────────────────────────────────────
    path('horas-extra/api/nomina-dependencias/',        views.api_nomina_dependencias,  name='api_nomina_dependencias'),
    path('horas-extra/api/nomina-empleados/',           views.api_nomina_empleados,     name='api_nomina_empleados'),
    path('horas-extra/api/importar-empleados/',         views.api_importar_empleados,   name='api_importar_empleados'),
]
