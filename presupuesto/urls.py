from django.urls import path
from . import views

urlpatterns = [
    path('', views.PresupuestoIndexView.as_view(), name='presupuesto_index'),
    path('cdp/', views.ConsultaCDPView.as_view(), name='presupuesto_cdp_list'),
    path('rp/', views.ConsultaRPView.as_view(), name='presupuesto_rp_list'),
    path('obligacion/', views.ConsultaObligacionView.as_view(), name='presupuesto_obligacion_list'),
]
