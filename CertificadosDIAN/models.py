from django.db import models
from django.contrib.auth.models import User

class RegistroDescargaCertificado(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    cedula_consultada = models.CharField(max_length=20)
    nombre_empleado = models.CharField('Nombre del empleado', max_length=255, blank=True, null=True)
    anio_gravable = models.IntegerField('Año gravable', default=2025)
    fecha_descarga = models.DateTimeField(auto_now_add=True)
    ip_descarga = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField('Navegador / Dispositivo', blank=True, null=True)
    enviado_whatsapp = models.BooleanField('Enviado por WhatsApp', default=False)
    telefono_whatsapp = models.CharField('Teléfono WhatsApp', max_length=20, blank=True, null=True)
    fecha_whatsapp = models.DateTimeField('Fecha envío WhatsApp', blank=True, null=True)

    class Meta:
        verbose_name = "Registro de Descarga"
        verbose_name_plural = "Registros de Descargas"
        ordering = ['-fecha_descarga']

    def __str__(self):
        return f"{self.usuario.username} → {self.cedula_consultada} ({self.anio_gravable}) — {self.fecha_descarga.strftime('%Y-%m-%d %H:%M')}"

class SolicitudCertificadoEmail(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    cedula_consultada = models.CharField(max_length=20)
    nombre_empleado = models.CharField(max_length=255, blank=True, null=True)
    email_envio = models.EmailField(blank=True, null=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    procesado = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Solicitud de Certificado (Email)"
        verbose_name_plural = "Solicitudes de Certificados (Email)"

    def __str__(self):
        status = "Procesado" if self.procesado else "Pendiente"
        return f"[{status}] {self.usuario.username} -> {self.email_envio} ({self.fecha_solicitud.strftime('%H:%M')})"

class DatosCertificadoDIAN(models.Model):
    anio_gravable = models.IntegerField(default=2025)
    cedula = models.CharField(max_length=20, db_index=True)
    primer_apellido = models.CharField(max_length=100, blank=True)
    segundo_apellido = models.CharField(max_length=100, blank=True)
    primer_nombre = models.CharField(max_length=100, blank=True)
    otros_nombres = models.CharField(max_length=100, blank=True)
    
    # Valores de las cajas del Formulario 220 (Mapeados del Excel)
    caja_36 = models.DecimalField(max_digits=15, decimal_places=2, default=0) # Salarios
    caja_42 = models.DecimalField(max_digits=15, decimal_places=2, default=0) # Prestaciones
    caja_46 = models.DecimalField(max_digits=15, decimal_places=2, default=0) # Otros pagos
    caja_47 = models.DecimalField(max_digits=15, decimal_places=2, default=0) # Cesantías pagadas
    caja_49 = models.DecimalField(max_digits=15, decimal_places=2, default=0) # Cesantías consignadas
    caja_52 = models.DecimalField(max_digits=15, decimal_places=2, default=0) # Total ingresos brutos
    caja_53 = models.DecimalField(max_digits=15, decimal_places=2, default=0) # Salud
    caja_54 = models.DecimalField(max_digits=15, decimal_places=2, default=0) # Pensión
    caja_56 = models.DecimalField(max_digits=15, decimal_places=2, default=0) # Aportes voluntarios
    caja_57 = models.DecimalField(max_digits=15, decimal_places=2, default=0) # AFC
    caja_59 = models.DecimalField(max_digits=15, decimal_places=2, default=0) # Retención promedio
    caja_60 = models.DecimalField(max_digits=15, decimal_places=2, default=0) # Retención total

    class Meta:
        unique_together = ('anio_gravable', 'cedula')
        verbose_name = "Datos de Certificado DIAN"
        verbose_name_plural = "Datos de Certificados DIAN"

    def __str__(self):
        return f"{self.anio_gravable} - {self.cedula} - {self.primer_apellido} {self.primer_nombre}"
