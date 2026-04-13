from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    CATEGORIAS = (
        ('ADMIN', 'Administrador'),
        ('EDITOR', 'Editor'),
        ('LECTOR', 'Lector'),
        ('IMPRESOR', 'Impresor'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='LECTOR')
    
    # Personalización Estética
    color_primario = models.CharField(max_length=7, default='#2563eb')
    color_secundario = models.CharField(max_length=7, default='#1e40af')
    color_fondo = models.CharField(max_length=7, default='#f8fafc')
    estilo_fondo = models.CharField(max_length=20, default='solid') # solid, gradient, pattern
    telefono = models.CharField(max_length=20, null=True, blank=True)

    # ─── Campos para DEFENJUR (Defensa Jurídica) ───
    legal_rol = models.CharField(max_length=120, default='INVITADO', help_text="Rol dentro del módulo DEFENJUR")
    legal_nick = models.CharField(max_length=120, null=True, blank=True, help_text="Nombre de usuario legacy para DEFENJUR")


    def __str__(self):
        return f"{self.user.username} - {self.get_categoria_display()}"

class PermisoApp(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permisos_app')
    app_label = models.CharField(max_length=100)
    permitido = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'app_label')

    def __str__(self):
        return f"{self.user.username} -> App: {self.app_label}"

class PermisoModelo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permisos_modelo')
    app_label = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    permitido = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'app_label', 'model_name')

    def __str__(self):
        return f"{self.user.username} -> Model: {self.app_label}.{self.model_name}"
