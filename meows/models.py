from django.db import models
from datetime import date


# ============================================================================
# 0️⃣ MODELO EXTERNO: GENPACIEN (Base de datos ReadOnly)
# ============================================================================

class Genpacien(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    PACNUMDOC = models.CharField(max_length=20, db_column='PACNUMDOC')
    PACTIPDOC = models.IntegerField(db_column='PACTIPDOC')  # 1:CC, 2:TI, etc.
    PACPRINOM = models.CharField(max_length=100, db_column='PACPRINOM')
    PACSEGNOM = models.CharField(max_length=100, db_column='PACSEGNOM', null=True)
    PACPRIAPE = models.CharField(max_length=100, db_column='PACPRIAPE')
    PACSEGAPE = models.CharField(max_length=100, db_column='PACSEGAPE', null=True)
    GPAFECNAC = models.DateTimeField(db_column='GPAFECNAC')
    GPASEXPAC = models.IntegerField(db_column='GPASEXPAC')  # 1:M, 2:F (según convención usual, verificar)

    class Meta:
        managed = False
        db_table = 'Genpacien'
        verbose_name = "Paciente Externo (Genpacien)"

    def __str__(self):
        return f"{self.PACNUMDOC}"


# ============================================================================
# 1️⃣ MODELO PACIENTE
# ============================================================================
class Paciente(models.Model):
    # Campos persistentes (Solo lo que NO viene de Genpacien o es necesario para ordenamiento/cache)
    numero_documento = models.CharField(max_length=20, unique=True)
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    sexo = models.CharField(
        max_length=1,
        choices=[("F", "Femenino"), ("M", "Masculino")]
    )
    
    # Campos clínicos específicos de esta app
    aseguradora = models.CharField(max_length=200, blank=True, help_text="Nombre de la aseguradora")
    cama = models.CharField(max_length=50, blank=True, help_text="Número o código de cama")
    fecha_ingreso = models.DateField(null=True, blank=True, help_text="Fecha de ingreso al hospital")
    responsable = models.CharField(max_length=200, blank=True, help_text="Nombre del responsable del paciente")
    tipo_sangre = models.CharField(
        max_length=5, 
        blank=True, 
        null=True,
        choices=[
            ("A+", "A+"), ("A-", "A-"),
            ("B+", "B+"), ("B-", "B-"),
            ("AB+", "AB+"), ("AB-", "AB-"),
            ("O+", "O+"), ("O-", "O-")
        ],
        help_text="Tipo de sangre y RH"
    )

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f"{self.numero_documento} - {self.nombres} {self.apellidos}"

    @property
    def info_externa(self):
        """Devuelve la instancia de Genpacien asociada."""
        if not self.numero_documento:
            return None
        return Genpacien.objects.using('readonly').filter(PACNUMDOC=self.numero_documento).first()

    @property
    def fecha_nacimiento(self):
        """Obtiene fecha de nacimiento directamente de Genpacien."""
        ext = self.info_externa
        if ext and ext.GPAFECNAC:
            return ext.GPAFECNAC.date()
        return None

    @property
    def edad(self):
        """Calcula edad al vuelo basada en Genpacien."""
        fn = self.fecha_nacimiento
        if fn:
            today = date.today()
            return today.year - fn.year - ((today.month, today.day) < (fn.month, fn.day))
        return None

    @property
    def tipo_documento(self):
        """Mapea tipo de documento desde Genpacien."""
        ext = self.info_externa
        if ext:
            mapa_docs = {1: 'CC', 2: 'TI', 3: 'CE', 4: 'RC', 5: 'PA'}
            return mapa_docs.get(ext.PACTIPDOC, 'CC')
        return None

    def save(self, *args, **kwargs):
        # Si faltan nombres, intentar poblar (cachear nombres para búsquedas/ordenamiento)
        if not self.nombres:
            self.poblar_datos_basicos()
        super().save(*args, **kwargs)

    def poblar_datos_basicos(self):
        """Busca el paciente en la BD externa y llena nombres/sexo."""
        if not self.numero_documento:
            return

        try:
            ext = self.info_externa
            
            if ext:
                # Nombres
                seg_nom = f" {ext.PACSEGNOM}" if ext.PACSEGNOM else ""
                self.nombres = f"{ext.PACPRINOM}{seg_nom}".strip()
                
                # Apellidos
                seg_ape = f" {ext.PACSEGAPE}" if ext.PACSEGAPE else ""
                self.apellidos = f"{ext.PACPRIAPE}{seg_ape}".strip()
                
                # Sexo (Mapeo: 1=M, 2=F)
                if ext.GPASEXPAC == 1:
                    self.sexo = 'M'
                elif ext.GPASEXPAC == 2:
                    self.sexo = 'F'

        except Exception as e:
            print(f"Error poblando desde Genpacien: {e}")





# ============================================================================
# 2️⃣ MODELO FORMULARIO
# ============================================================================
class Formulario(models.Model):
    codigo = models.CharField(max_length=30)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    version = models.CharField(max_length=20, default="1.0", help_text="Versión del formulario (ej: 1.0, 2.0)")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Formulario"
        verbose_name_plural = "Formularios"
        ordering = ['nombre']
        unique_together = [('codigo', 'version')]

    def __str__(self):
        return f"{self.nombre} v{self.version}"


# ============================================================================
# 3️⃣ MODELO PARÁMETRO (Catálogo clínico genérico)
# ============================================================================
class Parametro(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100)
    unidad = models.CharField(max_length=20)
    orden = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Parámetro"
        verbose_name_plural = "Parámetros"
        ordering = ['orden']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


# ============================================================================
# 4️⃣ MODELO MEDICIÓN (Cabecera de la toma)
# ============================================================================
class Medicion(models.Model):
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="mediciones"
    )
    formulario = models.ForeignKey(
        Formulario,
        on_delete=models.CASCADE,
        related_name="mediciones"
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)
    
    # 🧠 RESULTADOS MEOWS (se llenan luego)
    meows_total = models.PositiveIntegerField(null=True, blank=True)
    meows_riesgo = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        choices=[
            ("BLANCO", "Blanco"),
            ("VERDE", "Verde"),
            ("AMARILLO", "Amarillo"),
            ("ROJO", "Rojo"),
        ]
    )
    meows_mensaje = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Medición"
        verbose_name_plural = "Mediciones"
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"Medición {self.id} - {self.fecha_hora}"


# ============================================================================
# 5️⃣ MODELO MEDICIÓN VALOR (Detalle por parámetro)
# ============================================================================
class MedicionValor(models.Model):
    medicion = models.ForeignKey(
        Medicion,
        on_delete=models.CASCADE,
        related_name="valores"
    )
    parametro = models.ForeignKey(
        Parametro,
        on_delete=models.PROTECT
    )
    valor = models.CharField(max_length=20)
    puntaje = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Valor de Medición"
        verbose_name_plural = "Valores de Medición"
        unique_together = ("medicion", "parametro")
        ordering = ['parametro__orden']

    def __str__(self):
        return f"{self.parametro.codigo}: {self.valor}"


# ============================================================================
# 6️⃣ MODELO RANGO PARÁMETRO (Rangos de valores para cálculo de scores)
# ============================================================================
class RangoParametro(models.Model):
    """
    Define los rangos de valores y sus scores asociados para cada parámetro.
    Permite cambiar reglas sin modificar código.
    """
    parametro = models.ForeignKey(
        Parametro,
        on_delete=models.CASCADE,
        related_name="rangos"
    )
    valor_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor mínimo del rango (inclusive)"
    )
    valor_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor máximo del rango (inclusive)"
    )
    score = models.PositiveSmallIntegerField(
        help_text="Puntaje asignado a este rango (0-3)"
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de evaluación (menor a mayor)"
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Rango de Parámetro"
        verbose_name_plural = "Rangos de Parámetros"
        ordering = ['parametro', 'orden', 'valor_min']
        indexes = [
            models.Index(fields=['parametro', 'activo', 'orden']),
        ]

    def __str__(self):
        return f"{self.parametro.codigo}: [{self.valor_min}-{self.valor_max}] = {self.score}"

    def contiene_valor(self, valor: float) -> bool:
        """Verifica si un valor está dentro de este rango."""
        return self.valor_min <= valor <= self.valor_max


# ============================================================================
# MODELO LEGACY: ParametroMEOWS (mantener por compatibilidad)
# ============================================================================
class ParametroMEOWS(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100)
    unidad = models.CharField(max_length=20)
    orden = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Parámetro MEOWS"
        verbose_name_plural = "Parámetros MEOWS"
        ordering = ['orden']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


# ============================================================================
# 7️⃣ MODELOS EXTERNOS ADICIONALES (ReadOnly - DGEMPRES99)
# ============================================================================

class Gendiagno(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    DIACODIGO = models.CharField(max_length=20, db_column='DIACODIGO')
    DIANOMBRE = models.CharField(max_length=500, db_column='DIANOMBRE')

    class Meta:
        managed = False
        db_table = 'GENDIAGNO'
        verbose_name = "Diagnóstico (Gendiagno)"

    def __str__(self):
        return f"{self.DIACODIGO} - {self.DIANOMBRE}"

class Gendetcon(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    GDECODIGO = models.CharField(max_length=50, db_column='GDECODIGO')
    GDENOMBRE = models.CharField(max_length=200, db_column='GDENOMBRE')

    class Meta:
        managed = False
        db_table = 'GENDETCON'

    def __str__(self):
        return f"{self.GDENOMBRE}"

class Hpngrupos(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    HGRCODIGO = models.CharField(max_length=50, db_column='HGRCODIGO')
    HGRNOMBRE = models.CharField(max_length=200, db_column='HGRNOMBRE')

    class Meta:
        managed = False
        db_table = 'HPNGRUPOS'

    def __str__(self):
        return self.HGRNOMBRE

class Hpnsubgru(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    HSUCODIGO = models.CharField(max_length=50, db_column='HSUCODIGO')
    HSUNOMBRE = models.CharField(max_length=200, db_column='HSUNOMBRE')
    HGRGRUPO = models.ForeignKey(Hpngrupos, models.DO_NOTHING, db_column='HGRGRUPO', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'HPNSUBGRU'

    def __str__(self):
        return self.HSUNOMBRE

class Hpndefcam(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    HCACODIGO = models.CharField(max_length=50, db_column='HCACODIGO')
    HCANOMBRE = models.CharField(max_length=200, db_column='HCANOMBRE')
    HPNGRUPOS = models.ForeignKey(Hpngrupos, models.DO_NOTHING, db_column='HPNGRUPOS', null=True, blank=True)
    HPNSUBGRU = models.ForeignKey(Hpnsubgru, models.DO_NOTHING, db_column='HPNSUBGRU', null=True, blank=True)
    HCANUMHABI = models.CharField(max_length=50, db_column='HCANUMHABI')

    class Meta:
        managed = False
        db_table = 'HPNDEFCAM'
        verbose_name = "Cama (Hpndefcam)"

    def __str__(self):
        return self.HCANOMBRE

class Adningreso(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    AINCONSEC = models.IntegerField(db_column='AINCONSEC')
    GENPACIEN = models.ForeignKey(Genpacien, models.DO_NOTHING, db_column='GENPACIEN', related_name='ingresos')
    AINFECING = models.DateTimeField(db_column='AINFECING', null=True, blank=True)
    AINESTADO = models.IntegerField(db_column='AINESTADO', null=True, blank=True)
    GENDETCON = models.ForeignKey(Gendetcon, models.DO_NOTHING, db_column='GENDETCON', null=True, blank=True)
    HPNDEFCAM = models.ForeignKey(Hpndefcam, models.DO_NOTHING, db_column='HPNDEFCAM', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'ADNINGRESO'
        verbose_name = "Ingreso (Adningreso)"

    def __str__(self):
        return f"Ingreso {self.AINCONSEC}"

class Hpnestanc(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    ADNINGRES = models.ForeignKey(Adningreso, models.DO_NOTHING, db_column='ADNINGRES', related_name='estancias')
    HPNDEFCAM = models.ForeignKey(Hpndefcam, models.DO_NOTHING, db_column='HPNDEFCAM', related_name='estancias')
    HESFECING = models.DateTimeField(db_column='HESFECING', null=True, blank=True)
    HESFECSAL = models.DateTimeField(db_column='HESFECSAL', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'HPNESTANC'

class Hcnfolio(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    HCNUMFOL = models.IntegerField(db_column='HCNUMFOL')
    HCFECFOL = models.DateTimeField(db_column='HCFECFOL', null=True, blank=True)
    GENPACIEN = models.ForeignKey(Genpacien, models.DO_NOTHING, db_column='GENPACIEN', related_name='folios')
    ADNINGRESO = models.ForeignKey(Adningreso, models.DO_NOTHING, db_column='ADNINGRESO', related_name='folios')

    class Meta:
        managed = False
        db_table = 'HCNFOLIO'
        verbose_name = "Folio Clínico"

    def __str__(self):
        return f"Folio {self.HCNUMFOL}"

class Hcndiapac(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    HCNFOLIO = models.ForeignKey(Hcnfolio, models.DO_NOTHING, db_column='HCNFOLIO', related_name='diagnosticos')
    GENDIAGNO = models.ForeignKey(Gendiagno, models.DO_NOTHING, db_column='GENDIAGNO')
    HCPDIAPRIN = models.IntegerField(db_column='HCPDIAPRIN', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'HCNDIAPAC'

class Hcmwingin(models.Model):
    OID = models.IntegerField(primary_key=True, db_column='OID')
    HCNFOLIO = models.ForeignKey(Hcnfolio, models.DO_NOTHING, db_column='HCNFOLIO')
    # Tabla extensa

    class Meta:
        managed = False
        db_table = 'HCMWINGIN'

