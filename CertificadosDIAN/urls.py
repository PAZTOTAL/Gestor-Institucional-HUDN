from django.urls import path
from .views import (
    CertificadosDashboardView,
    generar_certificado_ingresos,
    LoginRapidoView,
    TrazabilidadDescargasView,
    ListaSolicitudesView,
    registrar_envio_whatsapp,
)

app_name = 'certificados_dian'

urlpatterns = [
    path('acceso-rapido/', LoginRapidoView.as_view(), name='login_rapido'),
    path('', CertificadosDashboardView.as_view(), name='dashboard'),
    path('generar-ingresos/', generar_certificado_ingresos, name='generar_ingresos'),
    path('trazabilidad/', TrazabilidadDescargasView.as_view(), name='trazabilidad'),
    path('solicitudes/', ListaSolicitudesView.as_view(), name='lista_solicitudes'),
    path('solicitudes/whatsapp/<int:pk>/', registrar_envio_whatsapp, name='registrar_whatsapp'),
]
