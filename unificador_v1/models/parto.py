from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class EstadoFormularioParto(models.TextChoices):
    G = "g", "G"
    P = "p", "P"
    C = "c", "C"
    A = "a", "A"
    V = "v", "V"
    M = "m", "M"

class TipoSangreParto(models.TextChoices):
    O_POS = "O+", "O+"
    O_NEG = "O-", "O-"
    A_POS = "A+", "A+"
    A_NEG = "A-", "A-"
    B_POS = "B+", "B+"
    B_NEG = "B-", "B-"
    AB_POS = "AB+", "AB+"
    AB_NEG = "AB-", "AB-"

class TipoValorParto(models.TextChoices):
    NUMBER = "number", "number"
    TEXT = "text", "text"
    BOOLEAN = "boolean", "boolean"
    JSON = "json", "json"

class AseguradoraParto(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    class Meta:
        db_table = "aseguradora"
        ordering = ["nombre"]

class PacienteParto(models.Model):
    num_historia_clinica = models.CharField(max_length=255, unique=True)
    num_identificacion = models.CharField(max_length=255, unique=True)
    nombres = models.CharField(max_length=255)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    tipo_sangre = models.CharField(max_length=3, choices=TipoSangreParto.choices, null=True, blank=True)
    class Meta:
        db_table = "paciente"
        ordering = ["nombres"]

class FormularioParto(models.Model):
    atencion = models.ForeignKey("AtencionParto", on_delete=models.SET_NULL, null=True, blank=True, related_name="formularios_parto")
    codigo = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    fecha_elabora = models.DateField()
    fecha_actualizacion = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    num_hoja = models.PositiveIntegerField()
    aseguradora = models.ForeignKey(AseguradoraParto, null=True, blank=True, on_delete=models.SET_NULL, related_name="formularios_parto")
    paciente = models.ForeignKey(PacienteParto, on_delete=models.CASCADE, related_name="formularios_parto")
    diagnostico = models.TextField(null=True, blank=True)
    edad_snapshot = models.PositiveIntegerField(null=True, blank=True)
    edad_gestion = models.PositiveIntegerField(null=True, blank=True)
    estado = models.CharField(max_length=1, choices=EstadoFormularioParto.choices)
    n_controles_prenatales = models.PositiveIntegerField(null=True, blank=True)
    responsable = models.CharField(max_length=255)
    class Meta:
        db_table = "formulario"
        ordering = ["-fecha_actualizacion"]

class ItemParto(models.Model):
    codigo = models.CharField(max_length=255, unique=True)
    nombre = models.CharField(max_length=255)
    class Meta:
        db_table = "item"
        ordering = ["codigo"]

class ParametroParto(models.Model):
    item = models.ForeignKey(ItemParto, on_delete=models.CASCADE, related_name="parametros_parto")
    codigo = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255)
    unidad = models.CharField(max_length=50, null=True, blank=True)
    orden = models.PositiveIntegerField(default=1)
    activo = models.BooleanField(default=True)
    class Meta:
        db_table = "parametro"
        unique_together = ("item", "codigo")
        ordering = ["item_id", "orden", "id"]

class FormularioItemParametroParto(models.Model):
    formulario = models.ForeignKey(FormularioParto, on_delete=models.CASCADE, related_name="parametros_formulario_parto")
    item = models.ForeignKey(ItemParto, on_delete=models.CASCADE, related_name="formularios_items_parto")
    parametro = models.ForeignKey(ParametroParto, on_delete=models.CASCADE, related_name="formularios_parametro_parto")
    requerido = models.BooleanField(default=False)
    class Meta:
        db_table = "formulario_item_parametro"
        unique_together = ("formulario", "parametro")

class CampoParametroParto(models.Model):
    parametro = models.ForeignKey(ParametroParto, on_delete=models.CASCADE, related_name="campos_parto")
    codigo = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255)
    tipo_valor = models.CharField(max_length=10, choices=TipoValorParto.choices)
    unidad = models.CharField(max_length=50, null=True, blank=True)
    orden = models.PositiveIntegerField(default=1)
    class Meta:
        db_table = "campo_parametro"
        unique_together = ("parametro", "codigo")

class MedicionParto(models.Model):
    formulario = models.ForeignKey(FormularioParto, on_delete=models.CASCADE, related_name="mediciones_parto")
    parametro = models.ForeignKey(ParametroParto, on_delete=models.CASCADE, related_name="mediciones_parto")
    tomada_en = models.DateTimeField()
    observacion = models.TextField(null=True, blank=True)
    class Meta:
        db_table = "medicion"
        unique_together = ("formulario", "parametro", "tomada_en")

class MedicionValorParto(models.Model):
    medicion = models.ForeignKey(MedicionParto, on_delete=models.CASCADE, related_name="valores_parto")
    campo = models.ForeignKey(CampoParametroParto, on_delete=models.CASCADE, related_name="valores_parto")
    valor_number = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    valor_text = models.TextField(null=True, blank=True)
    valor_boolean = models.BooleanField(null=True, blank=True)
    valor_json = models.JSONField(null=True, blank=True)
    class Meta:
        db_table = "medicion_valor"
        unique_together = ("medicion", "campo")

class HuellaParto(models.Model):
    paciente_id = models.CharField(max_length=50)
    formulario_id = models.CharField(max_length=50, null=True, blank=True)
    template = models.TextField(null=True, blank=True)
    imagen = models.ImageField(upload_to="huellas_biometricas/", null=True, blank=True)
    imagen_firma = models.ImageField(upload_to="firmas/", null=True, blank=True)
    usuario = models.CharField(max_length=50)
    fecha = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "huella"
        ordering = ["-fecha"]
