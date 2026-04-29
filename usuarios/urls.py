from django.urls import path
from .views import (
    CustomLoginView, CustomLogoutView, RegistroView, PanelUsuariosView, 
    GestionPermisosView, ConfigPerfilView, lookup_tercero_por_cedula,
    PasswordResetRequestView, PasswordResetVerifyView, PasswordResetConfirmView
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('registro/', RegistroView.as_view(), name='registro'),
    path('api/lookup-cedula/', lookup_tercero_por_cedula, name='lookup_cedula'),
    path('gestion/', PanelUsuariosView.as_view(), name='gestion_usuarios'),
    path('permisos/<int:pk>/', GestionPermisosView.as_view(), name='gestion_permisos'),
    path('configuracion/apariencia/', ConfigPerfilView.as_view(), name='config_perfil'),
    
    # Recuperación de Contraseña
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/verify/', PasswordResetVerifyView.as_view(), name='password_reset_verify'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
