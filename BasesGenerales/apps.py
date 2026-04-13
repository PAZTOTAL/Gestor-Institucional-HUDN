from django.apps import AppConfig
class BasesGeneralesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "BasesGenerales"
    verbose_name = "Bases Generales"

    def ready(self):
        import BasesGenerales.signals
