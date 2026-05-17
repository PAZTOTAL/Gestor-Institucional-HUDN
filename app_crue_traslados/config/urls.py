"""
URLs de entrada 
"""

from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as authViews

urlpatterns = [
	path ('admin/', admin.site.urls),
	path ('login/', authViews.LoginView.as_view (), name='login'),
	path ('logout/', authViews.LogoutView.as_view (), name='logout'),
	path ('', include ('crue_traslados.urls'))
	#path ('', include ('crue_traslados.urls', namespace='crue_traslados')),
]
