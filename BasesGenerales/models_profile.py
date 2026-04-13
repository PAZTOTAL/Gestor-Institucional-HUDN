# BasesGenerales/models_profile.py
from django.conf import settings
from django.db import models

class UserProfile(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="perfil")
    documento=models.ForeignKey("BasesGenerales.DocumentoDeIdentidad",on_delete=models.PROTECT,verbose_name="Documento",to_field="codigo",db_column="documento_codigo",unique=True)
    Organigrama01 = models.ForeignKey(
        "BasesGenerales.Organigrama01", on_delete=models.PROTECT, related_name="user_org_nivel1", verbose_name="Nivel 1", null=True, blank=True
    )
    Organigrama02 = models.ForeignKey(
        "BasesGenerales.Organigrama02", on_delete=models.PROTECT, related_name="user_org_nivel2", verbose_name="Nivel 2", null=True, blank=True
    )
    Organigrama03 = models.ForeignKey(
        "BasesGenerales.Organigrama03", on_delete=models.PROTECT, related_name="user_org_nivel3", verbose_name="Nivel 3", null=True, blank=True
    )
    Organigrama04 = models.ForeignKey(
        "BasesGenerales.Organigrama04", on_delete=models.PROTECT, related_name="user_org_nivel4", verbose_name="Nivel 4", null=True, blank=True
    )
    class Meta: db_table="user_profile"
    def __str__(self): return f"{self.user.username} – {self.documento_id}"
