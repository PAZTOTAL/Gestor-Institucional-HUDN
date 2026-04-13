from django.db import models

class PacienteNeurocritico(models.Model):
    item = models.IntegerField(null=True, blank=True)
    fecha_identificacion = models.DateTimeField(null=True, blank=True)
    busqueda_activa = models.CharField(max_length=50, null=True, blank=True)
    busqueda_pasiva = models.CharField(max_length=50, null=True, blank=True)
    servicio = models.CharField(max_length=100, null=True, blank=True)
    paciente_intubado = models.CharField(max_length=10, null=True, blank=True) # SI/NO
    tipo_identificacion = models.CharField(max_length=50, null=True, blank=True)
    numero_documento = models.CharField(max_length=50, null=True, blank=True)
    primer_nombre = models.CharField(max_length=100, null=True, blank=True)
    segundo_nombre = models.CharField(max_length=100, null=True, blank=True)
    primer_apellido = models.CharField(max_length=100, null=True, blank=True)
    segundo_apellido = models.CharField(max_length=100, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=20, null=True, blank=True)
    edad = models.IntegerField(null=True, blank=True)
    ocupacion = models.CharField(max_length=200, null=True, blank=True)
    etnia = models.CharField(max_length=100, null=True, blank=True)
    municipio_residencia = models.CharField(max_length=100, null=True, blank=True)
    eapb = models.CharField(max_length=100, null=True, blank=True) # EPS
    fecha_ingreso = models.DateTimeField(null=True, blank=True)
    glasgow_ingreso = models.IntegerField(null=True, blank=True)
    codigo_cie10 = models.CharField(max_length=20, null=True, blank=True)
    diagnostico = models.TextField(null=True, blank=True)
    paciente_alertado = models.CharField(max_length=10, null=True, blank=True) # SI/NO
    fecha_hora_alerta_crt = models.DateTimeField(null=True, blank=True)
    causa_no_alerta = models.TextField(null=True, blank=True)
    voluntades_anticipadas = models.CharField(max_length=100, null=True, blank=True)
    dx_muerte_encefalica = models.CharField(max_length=10, null=True, blank=True) # SI/NO
    fecha_diagnostico_me_hora = models.DateTimeField(null=True, blank=True)
    paciente_legalizado = models.CharField(max_length=10, null=True, blank=True) # SI/NO
    causa_no_legalizacion = models.TextField(null=True, blank=True)
    fecha_legalizacion = models.DateTimeField(null=True, blank=True)
    donante_efectivo = models.CharField(max_length=10, null=True, blank=True) # SI/NO
    causa_no_donante_efectivo = models.TextField(null=True, blank=True)
    estado_vital_egreso = models.CharField(max_length=50, null=True, blank=True)
    fecha_egreso = models.DateTimeField(null=True, blank=True)
    organos_recatados = models.TextField(null=True, blank=True)
    medico_alerta = models.CharField(max_length=150, null=True, blank=True)
    medico_no_alerta = models.CharField(max_length=150, null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.numero_documento} - {self.primer_nombre} {self.primer_apellido}"

    class Meta:
        verbose_name = "Paciente Neurocrítico"
        verbose_name_plural = "Pacientes Neurocríticos"
