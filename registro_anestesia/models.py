from django.db import models
from django.conf import settings
from BasesGenerales.models import DocumentoDeIdentidad

class CirugiaPropuesta(models.Model):
    nombre = models.CharField(max_length=200, unique=True, verbose_name="Nombre de la Cirugía")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Cirugía Propuesta"
        verbose_name_plural = "Cirugías Propuestas"
        ordering = ['nombre']

class RegistroAnestesia(models.Model):
    """
    Main Model for Anesthesia Record (Point 1, 2)
    """
    paciente = models.ForeignKey('consultas_externas.Genpacien', on_delete=models.PROTECT, verbose_name="Paciente (GENPACIEN)", db_constraint=False)
    anestesiologo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Anestesiólogo")
    fecha = models.DateField(auto_now_add=True, verbose_name="Fecha")
    sala = models.CharField(max_length=50, blank=True, null=True, verbose_name="Sala/Quirófano")
    
    # Point 2
    diagnostico_pre = models.TextField(verbose_name="Diagnóstico Preoperatorio")
    cirugia_propuesta_texto = models.TextField(verbose_name="Cirugía Propuesta (Texto Libre)", blank=True, null=True)
    cirugia_propuesta = models.ForeignKey(CirugiaPropuesta, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cirugía Propuesta")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Anestesia {self.id} - {self.paciente}"

    class Meta:
        verbose_name = "Registro de Anestesia"
        verbose_name_plural = "Registros de Anestesia"

class EvaluacionPreAnestesica(models.Model):
    """
    Points 15-22
    """
    registro = models.OneToOneField(RegistroAnestesia, on_delete=models.CASCADE, related_name='evaluacion_preanestesica')
    
    # Point 15 Header
    entidad = models.CharField(max_length=100, blank=True, null=True)
    patologia_principal = models.CharField(max_length=200, blank=True, null=True)
    
    # Point 16, 17 Anamnesis/Antecedentes
    antecedentes_patologicos = models.TextField(blank=True, null=True)
    antecedentes_quirurgicos = models.TextField(blank=True, null=True)
    antecedentes_farmacologicos = models.TextField(blank=True, null=True)
    antecedentes_alergicos = models.TextField(blank=True, null=True)
    antecedentes_toxicos = models.TextField(blank=True, null=True)
    
    # Point 18 Exams
    hb = models.CharField(max_length=20, blank=True, null=True, verbose_name="Hbna")
    hto = models.CharField(max_length=20, blank=True, null=True, verbose_name="Hcto")
    plaquetas = models.CharField(max_length=20, blank=True, null=True)
    tp = models.CharField(max_length=20, blank=True, null=True)
    tpt = models.CharField(max_length=20, blank=True, null=True)
    
    # Point 19 Rx
    rayos_x_comentario = models.TextField(blank=True, null=True, verbose_name="Rx Comentarios")
    
    # Point 20 Physical Exam
    peso = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    talla = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    fc = models.CharField(max_length=10, blank=True, null=True, verbose_name="FC")
    fr = models.CharField(max_length=10, blank=True, null=True, verbose_name="FR")
    pa = models.CharField(max_length=20, blank=True, null=True, verbose_name="PA")
    sao2 = models.CharField(max_length=10, blank=True, null=True, verbose_name="SaO2")
    
    # Point 21 Airway
    mallampati = models.CharField(max_length=10, blank=True, null=True)
    apertura_bucal = models.CharField(max_length=20, blank=True, null=True)
    dentadura = models.CharField(max_length=50, blank=True, null=True) # Fija, Movil, etc.
    cuello = models.CharField(max_length=100, blank=True, null=True)
    
    # Point 22 Plan
    asa = models.CharField(max_length=10, blank=True, null=True, verbose_name="ASA") # I, II, III etc.
    plan_anestesia = models.TextField(blank=True, null=True)
    apto_cirugia = models.BooleanField(default=True)

class Monitoreo(models.Model):
    """
    Points 3, 11
    """
    registro = models.OneToOneField(RegistroAnestesia, on_delete=models.CASCADE, related_name='monitoreo')
    
    ekg = models.BooleanField(default=False, verbose_name="EKG")
    pni = models.BooleanField(default=False, verbose_name="PNI") # Pressure Non-Invasive
    pulx = models.BooleanField(default=False, verbose_name="Pulx")
    capno = models.BooleanField(default=False, verbose_name="Capno")
    temp = models.BooleanField(default=False, verbose_name="Temp")
    est_n_perif = models.BooleanField(default=False, verbose_name="Est. N. Periférico")
    otro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Otro Monitor")
    
    # Point 11 Lines
    linea_arterial = models.BooleanField(default=False, verbose_name="PAI (Línea Arterial)")
    cvc = models.BooleanField(default=False, verbose_name="PVC (CVC)")

class Ventilacion(models.Model):
    """
    Points 6, 7
    """
    registro = models.OneToOneField(RegistroAnestesia, on_delete=models.CASCADE, related_name='ventilacion')
    
    # Point 6 Type
    espontanea = models.BooleanField(default=False)
    asistida = models.BooleanField(default=False)
    controlada = models.BooleanField(default=False)
    
    # Point 7 Params
    vt = models.CharField(max_length=20, blank=True, null=True, verbose_name="Volumen Tidal")
    fr = models.CharField(max_length=20, blank=True, null=True, verbose_name="Frecuencia Resp")
    peep = models.CharField(max_length=20, blank=True, null=True)

class Medicamentos(models.Model):
    """
    Point 4 (List of meds)
    """
    registro = models.ForeignKey(RegistroAnestesia, on_delete=models.CASCADE, related_name='medicamentos')
    nombre = models.CharField(max_length=100)
    dosis = models.CharField(max_length=50)
    hora = models.TimeField()
    via = models.CharField(max_length=50, blank=True, null=True)

class Liquidos(models.Model):
    """
    Point 8
    """
    registro = models.OneToOneField(RegistroAnestesia, on_delete=models.CASCADE, related_name='liquidos')
    
    pvc = models.CharField(max_length=20, blank=True, null=True, verbose_name="PVC")
    liquidos_administrados = models.TextField(blank=True, null=True) # Description or total
    sangre_derivados = models.TextField(blank=True, null=True)
    diuresis = models.CharField(max_length=50, blank=True, null=True)

class SignosVitales(models.Model):
    """
    Point 5 (Time series)
    """
    registro = models.ForeignKey(RegistroAnestesia, on_delete=models.CASCADE, related_name='signos_vitales')
    hora = models.TimeField()
    pa_sistolica = models.IntegerField(blank=True, null=True)
    pa_diastolica = models.IntegerField(blank=True, null=True)
    fc = models.IntegerField(blank=True, null=True)
    sao2 = models.IntegerField(blank=True, null=True)
    etco2 = models.IntegerField(blank=True, null=True)

class Tecnica(models.Model):
    """
    Point 12
    """
    registro = models.OneToOneField(RegistroAnestesia, on_delete=models.CASCADE, related_name='tecnica')
    
    general = models.BooleanField(default=False)
    regional = models.BooleanField(default=False)
    sedacion = models.BooleanField(default=False)
    local = models.BooleanField(default=False)
    combinada = models.BooleanField(default=False)
    descripcion = models.TextField(blank=True, null=True)

class Salida(models.Model):
    """
    Points 9, 10, 13
    """
    registro = models.OneToOneField(RegistroAnestesia, on_delete=models.CASCADE, related_name='salida')
    
    # Point 9
    diagnostico_post = models.TextField(verbose_name="Diagnóstico Postoperatorio")
    
    # Point 10
    cirugia_realizada = models.TextField(verbose_name="Cirugía Realizada")
    
    # Point 13
    destino = models.CharField(max_length=50, blank=True, null=True) # Recuperacion, UCI, Hab, etc.
    aldrete = models.CharField(max_length=10, blank=True, null=True) # Score

class Observaciones(models.Model):
    """
    Point 14
    """
    registro = models.OneToOneField(RegistroAnestesia, on_delete=models.CASCADE, related_name='observaciones')
    texto = models.TextField(blank=True, null=True)
