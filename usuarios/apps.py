from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'

    def ready(self):
        from django.contrib.auth.signals import user_logged_in

        def on_login(sender, request, user, **kwargs):
            from .views import _activar_permiso_coordinador
            _activar_permiso_coordinador(user)

        user_logged_in.connect(on_login, weak=False)
