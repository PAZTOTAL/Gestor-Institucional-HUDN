from django.urls import path
from .views import CustomLoginView, CustomLogoutView, RegistroView, PanelUsuariosView, GestionPermisosView, ConfigPerfilView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('registro/', RegistroView.as_view(), name='registro'),
    path('gestion/', PanelUsuariosView.as_view(), name='gestion_usuarios'),
    path('permisos/<int:pk>/', GestionPermisosView.as_view(), name='gestion_permisos'),
    path('configuracion/apariencia/', ConfigPerfilView.as_view(), name='config_perfil'),
]
