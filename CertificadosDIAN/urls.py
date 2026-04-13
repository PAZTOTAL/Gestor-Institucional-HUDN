from django.urls import path
from .views import (
    CertificadosDashboardView, generar_certificado_ingresos, 
    LoginRapidoView, solicitar_certificado_whatsapp, 
    ListarSolicitudesWhatsappView, marcar_procesado_whatsapp
)

app_name = 'certificados_dian'

urlpatterns = [
    path('acceso-rapido/', LoginRapidoView.as_view(), name='login_rapido'),
    path('', CertificadosDashboardView.as_view(), name='dashboard'),
    path('generar-ingresos/', generar_certificado_ingresos, name='generar_ingresos'),
    path('solicitar-whatsapp/', solicitar_certificado_whatsapp, name='solicitar_whatsapp'),
    path('solicitudes/', ListarSolicitudesWhatsappView.as_view(), name='lista_solicitudes'),
    path('solicitudes/marcar/<int:pk>/', marcar_procesado_whatsapp, name='marcar_procesado'),
]
