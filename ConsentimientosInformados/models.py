from django.db import models
from django.utils import timezone

class ConsentimientoTemplate(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Formato")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    contenido_html = models.TextField(verbose_name="Contenido HTML/Markdown del Formato")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Plantilla de Consentimiento"
        verbose_name_plural = "Plantillas de Consentimiento"

    def __str__(self):
        return self.nombre

class ConsentimientoRegistro(models.Model):
    template = models.ForeignKey(ConsentimientoTemplate, on_delete=models.CASCADE, verbose_name="Plantilla")
    
    # Referencias a registros existentes (usando OID ya que son bases externas)
    paciente_oid = models.IntegerField(verbose_name="OID del Paciente")
    profesional_oid = models.IntegerField(verbose_name="OID del Profesional")
    
    # Firmas en Base64 para visualización rápida o archivos para almacenamiento
    firma_paciente = models.TextField(verbose_name="Firma del Paciente (Base64)", blank=True, null=True)
    firma_profesional = models.TextField(verbose_name="Firma del Profesional (Base64)", blank=True, null=True)
    
    # Otros medios mencionados: huella, foto, email
    huella_paciente = models.TextField(verbose_name="Huella del Paciente (Base64)", blank=True, null=True)
    foto_paciente = models.TextField(verbose_name="Fotografía del Paciente (Base64)", blank=True, null=True)
    email_enviado = models.BooleanField(default=False, verbose_name="Enviado por Email")
    email_destino = models.EmailField(blank=True, null=True, verbose_name="Email de Destino")
    
    fecha_firma = models.DateTimeField(default=timezone.now, verbose_name="Fecha y Hora de Firma")
    
    # Campo para almacenar el PDF generado si es necesario
    pdf_resultado = models.FileField(upload_to='consentimientos/pdfs/', blank=True, null=True, verbose_name="PDF Firmado")
    
    # Datos adicionales capturados en el momento (JSON o campos específicos)
    datos_extra = models.TextField(default="{}", blank=True, verbose_name="Datos capturados en el formulario")

    class Meta:
        verbose_name = "Registro de Consentimiento"
        verbose_name_plural = "Registros de Consentimiento"

    def __str__(self):
        return f"{self.template.nombre} - OID Paciente: {self.paciente_oid} - {self.fecha_firma}"
