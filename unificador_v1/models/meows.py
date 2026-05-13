from django.db import models
from datetime import date

# ============================================================================
# 0️⃣ MODELOS EXTERNOS (ReadOnly)
# ============================================================================

class Genpacien(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    PACNUMDOC = models.CharField(max_length=20, db_column='PACNUMDOC')
    PACTIPDOC = models.IntegerField(db_column='PACTIPDOC')
    PACPRINOM = models.CharField(max_length=100, db_column='PACPRINOM')
    PACSEGNOM = models.CharField(max_length=100, db_column='PACSEGNOM', null=True)
    PACPRIAPE = models.CharField(max_length=100, db_column='PACPRIAPE')
    PACSEGAPE = models.CharField(max_length=100, db_column='PACSEGAPE', null=True)
    GPAFECNAC = models.DateTimeField(db_column='GPAFECNAC')
    GPASEXPAC = models.IntegerField(db_column='GPASEXPAC')

    class Meta:
        managed = False
        db_table = 'Genpacien'
        verbose_name = "Paciente Externo (Genpacien)"

    def __str__(self):
        return f"{self.PACNUMDOC}"

class Gendiagno(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    DIACODIGO = models.CharField(max_length=20, db_column='DIACODIGO')
    DIANOMBRE = models.CharField(max_length=500, db_column='DIANOMBRE')
    class Meta:
        managed = False
        db_table = 'GENDIAGNO'

class Gendetcon(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    GDECODIGO = models.CharField(max_length=50, db_column='GDECODIGO')
    GDENOMBRE = models.CharField(max_length=200, db_column='GDENOMBRE')
    class Meta:
        managed = False
        db_table = 'GENDETCON'

class Hpngrupos(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    HGRCODIGO = models.CharField(max_length=50, db_column='HGRCODIGO')
    HGRNOMBRE = models.CharField(max_length=200, db_column='HGRNOMBRE')
    class Meta:
        managed = False
        db_table = 'HPNGRUPOS'

class Hpnsubgru(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    HSUCODIGO = models.CharField(max_length=50, db_column='HSUCODIGO')
    HSUNOMBRE = models.CharField(max_length=200, db_column='HSUNOMBRE')
    HGRGRUPO = models.ForeignKey(Hpngrupos, models.DO_NOTHING, db_column='HGRGRUPO', null=True, blank=True)
    class Meta:
        managed = False
        db_table = 'HPNSUBGRU'

class Hpndefcam(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    HCACODIGO = models.CharField(max_length=50, db_column='HCACODIGO')
    HCANOMBRE = models.CharField(max_length=200, db_column='HCANOMBRE')
    HPNGRUPOS = models.ForeignKey(Hpngrupos, models.DO_NOTHING, db_column='HPNGRUPOS', null=True, blank=True)
    HPNSUBGRU = models.ForeignKey(Hpnsubgru, models.DO_NOTHING, db_column='HPNSUBGRU', null=True, blank=True)
    class Meta:
        managed = False
        db_table = 'HPNDEFCAM'

class Adningreso(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    AINCONSEC = models.IntegerField(db_column='AINCONSEC')
    GENPACIEN = models.ForeignKey(Genpacien, models.DO_NOTHING, db_column='GENPACIEN', related_name='ingresos_meows')
    AINFECING = models.DateTimeField(db_column='AINFECING', null=True, blank=True)
    AINESTADO = models.IntegerField(db_column='AINESTADO', null=True, blank=True)
    GENDETCON = models.ForeignKey(Gendetcon, models.DO_NOTHING, db_column='GENDETCON', null=True, blank=True)
    HPNDEFCAM = models.ForeignKey(Hpndefcam, models.DO_NOTHING, db_column='HPNDEFCAM', null=True, blank=True)
    class Meta:
        managed = False
        db_table = 'ADNINGRESO'

class Hpnestanc(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    ADNINGRES = models.ForeignKey(Adningreso, models.DO_NOTHING, db_column='ADNINGRES', related_name='estancias_meows')
    HPNDEFCAM = models.ForeignKey(Hpndefcam, models.DO_NOTHING, db_column='HPNDEFCAM', related_name='estancias_meows')
    HESFECING = models.DateTimeField(db_column='HESFECING', null=True, blank=True)
    HESFECSAL = models.DateTimeField(db_column='HESFECSAL', null=True, blank=True)
    class Meta:
        managed = False
        db_table = 'HPNESTANC'

class Hcnfolio(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    HCNUMFOL = models.IntegerField(db_column='HCNUMFOL')
    HCFECFOL = models.DateTimeField(db_column='HCFECFOL', null=True, blank=True)
    GENPACIEN = models.ForeignKey(Genpacien, models.DO_NOTHING, db_column='GENPACIEN', related_name='folios_meows')
    ADNINGRESO = models.ForeignKey(Adningreso, models.DO_NOTHING, db_column='ADNINGRESO', related_name='folios_meows')
    class Meta:
        managed = False
        db_table = 'HCNFOLIO'

class Hcndiapac(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    HCNFOLIO = models.ForeignKey(Hcnfolio, models.DO_NOTHING, db_column='HCNFOLIO', related_name='diagnosticos_meows')
    GENDIAGNO = models.ForeignKey(Gendiagno, models.DO_NOTHING, db_column='GENDIAGNO')
    HCPDIAPRIN = models.IntegerField(db_column='HCPDIAPRIN', null=True, blank=True)
    class Meta:
        managed = False
        db_table = 'HCNDIAPAC'

class Hcmwingin(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    HCNFOLIO = models.ForeignKey(Hcnfolio, models.DO_NOTHING, db_column='HCNFOLIO')
    class Meta:
        managed = False
        db_table = 'HCMWINGIN'

# ============================================================================
# 1️⃣ MODELO PACIENTE (Renombrado para evitar conflicto)
# ============================================================================
class PacienteMEOWS(models.Model):
    numero_documento = models.CharField(max_length=20, unique=True)
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    sexo = models.CharField(max_length=1, choices=[("F", "Femenino"), ("M", "Masculino")])
    aseguradora = models.CharField(max_length=200, blank=True)
    cama = models.CharField(max_length=50, blank=True)
    num_historia_clinica = models.CharField(max_length=50, blank=True, default="")
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    responsable = models.CharField(max_length=200, blank=True)
    diagnostico = models.TextField(blank=True, default="")
    tipo_sangre = models.CharField(max_length=5, blank=True)
    nombre_acompanante = models.CharField(max_length=200, blank=True)
    edad_gestacional = models.PositiveSmallIntegerField(null=True, blank=True)
    gestas = models.PositiveSmallIntegerField(null=True, blank=True, default=1)
    n_controles_prenatales = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'meows_paciente'
        verbose_name = "Paciente MEOWS"
        verbose_name_plural = "Pacientes MEOWS"
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f"{self.numero_documento} - {self.nombres} {self.apellidos}"

    @property
    def info_externa(self):
        if hasattr(self, "_info_externa_cache"): return self._info_externa_cache
        from django.conf import settings
        if not getattr(settings, 'HABILITAR_BD_EXTERNA', True): return None
        if not self.numero_documento: return None
        try:
            ext = Genpacien.objects.using('readonly').filter(PACNUMDOC=self.numero_documento).first()
            if not ext:
                doc_limpio = self.numero_documento.lstrip('0')
                if doc_limpio and doc_limpio != self.numero_documento:
                    ext = Genpacien.objects.using('readonly').filter(PACNUMDOC=doc_limpio).first()
            if not ext:
                ext = Genpacien.objects.using('readonly').filter(PACNUMDOC__endswith=self.numero_documento).first()
            self._info_externa_cache = ext
            return ext
        except Exception: return None

    @property
    def edad(self):
        fn = self.fecha_nacimiento
        if fn:
            today = date.today()
            return today.year - fn.year - ((today.month, today.day) < (fn.month, fn.day))
        return None

# ============================================================================
# 2️⃣ MODELOS DE FORMULARIO Y MEDICIÓN
# ============================================================================
class FormularioMEOWS(models.Model):
    codigo = models.CharField(max_length=30)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    version = models.CharField(max_length=20, default="1.0")
    activo = models.BooleanField(default=True)
    class Meta:
        db_table = 'meows_formulario'
        unique_together = [('codigo', 'version')]
    def __str__(self): return f"{self.nombre} v{self.version}"

class ParametroMEOWS_Def(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100)
    unidad = models.CharField(max_length=20)
    orden = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)
    class Meta:
        db_table = 'meows_parametro'
        ordering = ['orden']
    def __str__(self): return f"{self.codigo} - {self.nombre}"

class MedicionMEOWS(models.Model):
    atencion = models.ForeignKey("AtencionParto", on_delete=models.SET_NULL, null=True, blank=True, related_name="mediciones_meows")
    paciente = models.ForeignKey(PacienteMEOWS, on_delete=models.CASCADE, related_name="mediciones")
    formulario = models.ForeignKey(FormularioMEOWS, on_delete=models.CASCADE, related_name="mediciones")
    fecha_hora = models.DateTimeField(auto_now_add=True)
    meows_total = models.PositiveIntegerField(null=True, blank=True)
    meows_riesgo = models.CharField(max_length=10, null=True, blank=True)
    meows_mensaje = models.TextField(null=True, blank=True)
    class Meta:
        db_table = 'meows_medicion'
        ordering = ['-fecha_hora']

class MedicionValorMEOWS(models.Model):
    medicion = models.ForeignKey(MedicionMEOWS, on_delete=models.CASCADE, related_name="valores")
    parametro = models.ForeignKey(ParametroMEOWS_Def, on_delete=models.PROTECT)
    valor = models.CharField(max_length=20)
    puntaje = models.PositiveSmallIntegerField(null=True, blank=True)
    class Meta:
        db_table = 'meows_medicionvalor'
        unique_together = ("medicion", "parametro")

class RangoParametroMEOWS(models.Model):
    parametro = models.ForeignKey(ParametroMEOWS_Def, on_delete=models.CASCADE, related_name="rangos")
    valor_min = models.DecimalField(max_digits=10, decimal_places=2)
    valor_max = models.DecimalField(max_digits=10, decimal_places=2)
    score = models.PositiveSmallIntegerField()
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    class Meta:
        db_table = 'meows_rangoparametro'

class FirmaPacienteMEOWS(models.Model):
    paciente_id = models.CharField(max_length=50)
    formulario_id = models.CharField(max_length=50, null=True, blank=True)
    template_huella = models.TextField()
    imagen_huella = models.ImageField(upload_to="huellas_biometria/", null=True, blank=True)
    imagen_firma = models.ImageField(upload_to="firmas/", null=True, blank=True)
    usuario = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'meows_firmapaciente'
class ParametroMEOWS_Legacy(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100)
    unidad = models.CharField(max_length=20)
    orden = models.PositiveIntegerField()
    class Meta:
        db_table = 'meows_parametromeows'
        verbose_name = "Parámetro MEOWS (Legacy)"
        verbose_name_plural = "Parámetros MEOWS (Legacy)"
        ordering = ['orden']
    def __str__(self): return f"{self.codigo} - {self.nombre}"

# Alias para compatibilidad con código legacy
ParametroMEOWS = ParametroMEOWS_Legacy
Parametro = ParametroMEOWS_Def
Medicion = MedicionMEOWS
MedicionValor = MedicionValorMEOWS
FirmaPaciente = FirmaPacienteMEOWS
