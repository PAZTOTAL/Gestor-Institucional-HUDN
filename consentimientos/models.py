from django.db import models
from django.contrib.auth.models import User

class DocumentoConsentimiento(models.Model):
    titulo = models.CharField(max_length=255)
    contenido = models.TextField(help_text="Contenido del documento en HTML o texto plano")
    version = models.CharField(max_length=50, default="1.0")
    codigo_formato = models.CharField(max_length=100, null=True, blank=True)
    fecha_elaboracion = models.CharField(max_length=100, null=True, blank=True)
    fecha_actualizacion = models.CharField(max_length=100, null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} (v{self.version})"

class WebAuthnCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="webauthn_credentials")
    credential_id = models.CharField(max_length=250, unique=True, help_text="Base64 encoded credential ID")
    public_key = models.TextField(help_text="Base64 encoded public key")
    sign_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Credencial de {self.user.username}"

class FirmaBiometrica(models.Model):
    documento = models.ForeignKey(DocumentoConsentimiento, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Datos de Trazabilidad HUDN (Mag HUDN1)
    ingreso_id = models.IntegerField(null=True, blank=True, help_text="ID de Admisión en el sistema hospitalario")
    paciente_oid = models.IntegerField(null=True, blank=True)
    folio = models.IntegerField(null=True, blank=True, help_text="Número de Folio / Historia Clínica")
    historia_clinica = models.CharField(max_length=50, null=True, blank=True)
    
    # Firmas en Base64
    firma_data = models.TextField(help_text="Base64 de la firma del Paciente")
    firma_medico_data = models.TextField(null=True, blank=True, help_text="Base64 de la firma del Médico o Responsable")
    firma_testigo_data = models.TextField(null=True, blank=True, help_text="Base64 de la firma del Testigo (en caso de rechazo)")
    
    datos_formulario = models.TextField(default="{}", help_text="Valores de los placeholders diligenciados en JSON")
    metadata_seguridad = models.TextField(default="{}", help_text="Timestamp, IP, User Agent, etc.")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Firma #{self.pk} - {self.documento.titulo} - Paciente: {self.historia_clinica}"

class FirmaFuncionario(models.Model):
    """Registro de Firma Oficial para Personal Médico / Staff"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="firma_oficial")
    firma_data = models.TextField(help_text="Base64 de la firma oficial registrada")
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Firma Oficial de {self.user.get_full_name() or self.user.username}"
