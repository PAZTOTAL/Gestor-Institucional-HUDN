from django.urls import path
from . import vistas

urlpatterns = [
	path ('login/', vistas.LoginVista.as_view (), name='login'),
	path ('logout/', vistas.LogoutVista.as_view (), name='logout'),
]
