from django.urls import path, include
from rest_framework_nested import routers
from ..views import fetal as views

router = routers.DefaultRouter()
router.register(r'registros', views.RegistroPartoViewSet, basename='fetal_registro')

registros_router = routers.NestedDefaultRouter(router, r'registros', lookup='registro')
registros_router.register(r'fetocardia', views.ControlFetocardiaViewSet, basename='fetal_fetocardia')
registros_router.register(r'recien-nacido', views.ControlRecienNacidoViewSet, basename='fetal_recien_nacido')
registros_router.register(r'postparto', views.ControlPostpartoViewSet, basename='fetal_postparto')

urlpatterns = [
    path('', views.FormularioRegistroView.as_view(), name='frecuenciafetal_home'),
    path('captura-huella/', views.captura_huella, name='fetal_captura_huella'),
    path('api/', include(router.urls)),
    path('api/', include(registros_router.urls)),
    path('api/guardar-huella-bebe/', views.guardar_huella_bebe, name='fetal_guardar_huella_bebe'),
    path('api/guardar-huella/', views.guardar_huella, name='fetal_guardar_huella'),
    path('api/guardar-firma/', views.guardar_firma_digital, name='fetal_guardar_firma'),
    path('api/huella/<str:documento>/', views.ultima_huella, name='fetal_ultima_huella'),
    path('ver-huella/<str:documento>/', views.ver_huella, name='fetal_ver_huella'),
]
