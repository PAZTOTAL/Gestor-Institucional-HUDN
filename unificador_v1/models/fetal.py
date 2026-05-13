from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class RegistroPartoFetal(models.Model):
    atencion = models.ForeignKey('AtencionParto', on_delete=models.SET_NULL, null=True, blank=True, related_name="registros_fetal")
    GENERO_CHOICES = [('M', 'Masculino'), ('F', 'Femenino'), ('I', 'Indeterminado')]
    PARTO_CHOICES = [('VAGINAL', 'Vaginal'), ('INSTRUMENTADO', 'Instrumentado'), ('CESAREA', 'Cesárea')]
    ALUMBRAMIENTO_CHOICES = [('ESPONTANEO', 'Espontáneo'), ('DIRIGIDO', 'Dirigido'), ('MANUAL', 'Manual')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre_paciente = models.CharField(max_length=200)
    identificacion = models.CharField(max_length=50)
    edad_gestacional = models.PositiveSmallIntegerField(validators=[MinValueValidator(20), MaxValueValidator(45)])
    gestas = models.PositiveSmallIntegerField(default=1)
    nombre_acompanante = models.CharField(max_length=200, blank=True, null=True)
    tipo_parto = models.CharField(max_length=20, choices=PARTO_CHOICES, blank=True, null=True)
    episiotomia = models.BooleanField(default=False)
    tipo_alumbramiento = models.CharField(max_length=20, choices=ALUMBRAMIENTO_CHOICES, blank=True, null=True)
    parto_atendido_por = models.CharField(max_length=200, blank=True, null=True)
    firma_paciente = models.ImageField(upload_to='firmas/', blank=True, null=True)
    nombre_firma_paciente = models.CharField(max_length=200, blank=True, null=True)
    fecha_hora_firma = models.DateTimeField(blank=True, null=True)
    profesional_nombre = models.CharField(max_length=200, blank=True, null=True)
    profesional_identificacion = models.CharField(max_length=50, blank=True, null=True)
    profesional_tarjeta_pro = models.CharField(max_length=50, blank=True, null=True)
    firma_profesional_base64 = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'frecuenciafetal_registroparto'
        ordering = ['-created_at']

class ControlFetocardiaFetal(models.Model):
    registro = models.ForeignKey(RegistroPartoFetal, on_delete=models.CASCADE, related_name='controles_fetocardia_fetal')
    fecha = models.DateField()
    hora = models.TimeField()
    fetocardia = models.PositiveSmallIntegerField(validators=[MinValueValidator(50), MaxValueValidator(250)])
    responsable = models.CharField(max_length=200, blank=True, default='')
    class Meta:
        db_table = 'frecuenciafetal_controlfetocardia'
        ordering = ['fecha', 'hora']

class ControlRecienNacidoFetal(models.Model):
    registro = models.OneToOneField(RegistroPartoFetal, on_delete=models.CASCADE, related_name='control_recien_nacido_fetal')
    hora_nacimiento = models.TimeField()
    pasa_uci_neonatal = models.BooleanField(default=False)
    causa_uci = models.TextField(blank=True, null=True)
    genero = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Femenino'), ('I', 'Indeterminado')])
    peso = models.DecimalField(max_digits=6, decimal_places=2)
    talla = models.DecimalField(max_digits=4, decimal_places=1)
    pc = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    pt = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    p_abd = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    apgar_1min = models.PositiveSmallIntegerField()
    apgar_5min = models.PositiveSmallIntegerField()
    apgar_10min = models.PositiveSmallIntegerField(blank=True, null=True)
    tsh = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    hemoclasificacion = models.CharField(max_length=10, blank=True, null=True)
    vacuna_hb = models.BooleanField(default=False)
    vacuna_bcg = models.BooleanField(default=False)
    caracteristicas_liquido_amniotico = models.TextField(blank=True, null=True)
    lavado_gastrico = models.BooleanField(default=False)
    lavado_elimina = models.BooleanField(default=False)
    meconio = models.BooleanField(default=False)
    oximetria_nacimiento_preductal = models.PositiveSmallIntegerField(blank=True, null=True)
    oximetria_nacimiento_posductal = models.PositiveSmallIntegerField(blank=True, null=True)
    oximetria_12h_preductal = models.PositiveSmallIntegerField(blank=True, null=True)
    oximetria_12h_posductal = models.PositiveSmallIntegerField(blank=True, null=True)
    ta_msd = models.CharField(max_length=20, blank=True, null=True)
    ta_msi = models.CharField(max_length=20, blank=True, null=True)
    ta_mid = models.CharField(max_length=20, blank=True, null=True)
    ta_miiz = models.CharField(max_length=20, blank=True, null=True)
    neonato_atendido_por = models.CharField(max_length=200, blank=True, null=True)
    valorado_pediatra = models.BooleanField(default=False)
    huella_pie = models.ImageField(upload_to='huellas_pie/%Y/%m/', blank=True, null=True)
    huella_pie_base64 = models.TextField(blank=True, null=True)
    class Meta:
        db_table = 'frecuenciafetal_controlreciennacido'

class GlucometriaRecienNacidoFetal(models.Model):
    control_rn = models.ForeignKey(ControlRecienNacidoFetal, on_delete=models.CASCADE, related_name='glucometrias_fetal')
    hora = models.TimeField()
    resultado = models.DecimalField(max_digits=5, decimal_places=1)
    class Meta:
        db_table = 'frecuenciafetal_glucometriareciennacido'
        ordering = ['hora']

class ControlPostpartoInmediatoFetal(models.Model):
    registro = models.ForeignKey(RegistroPartoFetal, on_delete=models.CASCADE, related_name='controles_postparto_fetal')
    minuto_control = models.PositiveSmallIntegerField()
    fecha = models.DateField()
    hora = models.TimeField()
    tension_arterial = models.CharField(max_length=20, blank=True, null=True)
    temperatura = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    pulso = models.PositiveSmallIntegerField(blank=True, null=True)
    respiracion = models.PositiveSmallIntegerField(blank=True, null=True)
    sangrado_vaginal = models.CharField(max_length=20, blank=True, null=True)
    cuantificacion_gravimetrica_vaginal = models.PositiveIntegerField(blank=True, null=True)
    involucion_uterina = models.CharField(max_length=20, blank=True, null=True)
    responsable = models.CharField(max_length=200, blank=True, null=True)
    class Meta:
        db_table = 'frecuenciafetal_controlpostpartoinmediato'
        ordering = ['fecha', 'hora']

class HuellaBebeFetal(models.Model):
    bebe_id = models.IntegerField()
    tipo = models.CharField(max_length=20)
    imagen = models.ImageField(upload_to="huellas_bebe/")
    fecha = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'frecuenciafetal_huellabebe'

class FirmaPacienteFetal(models.Model):
    formulario = models.ForeignKey(RegistroPartoFetal, on_delete=models.CASCADE, null=True, blank=True, related_name='firmas_fetal')
    paciente_id = models.IntegerField()
    template_huella = models.TextField()
    imagen_huella = models.ImageField(upload_to="huellas/", null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=100)
    class Meta:
        db_table = 'frecuenciafetal_firmapaciente'

class HuellaFetal(models.Model):
    documento = models.CharField(max_length=50)
    template = models.TextField()
    imagen_huella = models.ImageField(upload_to="huellas_biometricas/", null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=100, default="SYSTEM")
    class Meta:
        db_table = 'frecuenciafetal_huella'
        ordering = ['-fecha']
