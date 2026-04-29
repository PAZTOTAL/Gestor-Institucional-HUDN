"""
Configuración de URLs del proyecto — enruta hacia las apps y rutas de autenticación.
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as authViews

urlpatterns = [
	path ('admin/', admin.site.urls),
	path ('login/', authViews.LoginView.as_view (template_name='traslados/login.html'), name='login'),
	path ('logout/', authViews.LogoutView.as_view (), name='logout'),
	path ('', include ('traslados.urls')),
]
