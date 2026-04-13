from django.urls import path
from . import views

app_name = 'horas_extras'

urlpatterns = [
    path('', views.TalentoHumanoDashboardView.as_view(), name='dashboard'),
    path('horas-extras/', views.HoraExtraListView.as_view(), name='hora_extra_list'),
    path('cargar/', views.CargarHorasView.as_view(), name='cargar'),
    path('buscar-empleado/', views.buscar_empleado, name='buscar_empleado'),
    path('informes/', views.InformesDashboardView.as_view(), name='informes_dashboard'),
    path('informes/personal-activo/', views.PersonalActivoReportView.as_view(), name='reporte_personal_activo'),
    path('informes/personal-area/', views.PersonalPorAreaReportView.as_view(), name='reporte_personal_area'),
    path('informes/personal-temporal/', views.PersonalTemporalReportView.as_view(), name='reporte_personal_temporal'),
    path('informes/buscar-funcionario/', views.BuscarFuncionarioView.as_view(), name='buscar_funcionario'),
    path('informes/personal-area/<str:area_code>/', views.PersonalAreaDetailView.as_view(), name='reporte_personal_area_detalle'),
]
