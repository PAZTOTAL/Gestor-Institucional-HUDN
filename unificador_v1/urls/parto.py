from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views import parto as views

router = DefaultRouter()
router.register(r'aseguradoras', views.AseguradoraViewSet, basename='parto_aseguradora')
router.register(r'pacientes', views.PacienteViewSet, basename='parto_paciente')
router.register(r'formularios', views.FormularioViewSet, basename='parto_formulario')
router.register(r'items', views.ItemViewSet, basename='parto_item')
router.register(r'parametros', views.ParametroViewSet, basename='parto_parametro')
router.register(r'campos-parametro', views.CampoParametroViewSet, basename='parto_campo_parametro')
router.register(r'formularios-items-parametros', views.FormularioItemParametroViewSet, basename='parto_fip')
router.register(r'mediciones', views.MedicionViewSet, basename='parto_medicion')
router.register(r'mediciones-valores', views.MedicionValorViewSet, basename='parto_medicion_valor')

urlpatterns = [
    path('', views.parto_home, name='parto_home'),
    path('api/', include(router.urls)),
    path('api/guardar-huella/', views.guardar_huella, name='parto_guardar_huella'),
    path('api/huella/<int:paciente_id>/', views.consulta_huella, name='parto_consulta_huella'),
    path('api/vincular-huella/', views.vincular_huella, name='parto_vincular_huella'),
    path('formulario/<int:formulario_id>/pdf/', views.generar_pdf_formulario, name='generar_pdf_formulario'),
    path('formulario/<int:formulario_id>/impresion/', views.vista_impresion_formulario, name='vista_impresion_formulario'),
    path('pacientes/<int:paciente_id>/pdf/', views.generar_pdf_paciente, name='generar_pdf_paciente'),
    path('pacientes/<int:paciente_id>/preview/', views.preview_pdf_paciente, name='preview_pdf_paciente'),
    path('huella/ver/<str:documento>/', views.ver_huella, name='parto_ver_huella'),
]
