from django.db import models
from django.contrib.auth.models import User

class opsComponenteTecnico(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='estudio_opscomponente_set')
    numeroComponente = models.CharField(max_length=100, unique=True, verbose_name="Número Componente")
    Area = models.CharField(max_length=255, blank=True, null=True, verbose_name="Área")
    Subgerencia = models.CharField(max_length=255, blank=True, null=True, verbose_name="Subgerencia")
    Dependencia = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dependencia")
    objetoContractual = models.TextField(blank=True, null=True, verbose_name="Objeto Contractual")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción de la Necesidad")
    claseServicio = models.CharField(max_length=255, blank=True, null=True, verbose_name="Clase de Servicio")
    VALORTOTALCONTRATO = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True, verbose_name="Valor Total Contrato")
    
    def __str__(self):
        return f"Componente Técnico - {self.numeroComponente}"
    
    class Meta:
        verbose_name = "Componente Técnico Ops"
        verbose_name_plural = "Componentes Técnicos Ops"

class opsCondiciones(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.CASCADE, to_field='numeroComponente', db_column='NumeroComponente', related_name='condiciones')
    PAA_UNSPS = models.CharField(max_length=255, blank=True, null=True, verbose_name="Código PAA/UNSPSC y Nombre")
    FECHADEINICIO = models.DateField(blank=True, null=True, verbose_name="Fecha de Inicio")
    FECHADETERMINACION = models.DateField(blank=True, null=True, verbose_name="Fecha de Terminación")
    LUGARDEEJECUCION = models.CharField(max_length=500, blank=True, null=True, verbose_name="Lugar de Ejecución")

    class Meta:
        verbose_name = "Condiciones Ops"
        verbose_name_plural = "Condiciones Ops"

class opsObligacionesGenerales(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.CASCADE, to_field='numeroComponente', db_column='NumeroComponente', related_name='obligaciones_generales')
    Obligacion = models.TextField(verbose_name="Obligación General")

    class Meta:
        verbose_name = "Obligación General Ops"
        verbose_name_plural = "Obligaciones Generales Ops"

class opsObligacionesEspecificas(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.CASCADE, to_field='numeroComponente', db_column='NumeroComponente', related_name='obligaciones_especificas')
    Obligacion = models.TextField(verbose_name="Obligación Específica")

    class Meta:
        verbose_name = "Obligación Específica Ops"
        verbose_name_plural = "Obligaciones Específicas Ops"

class ops3_1AspectosLegales(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.CASCADE, to_field='numeroComponente', db_column='NumeroComponente', related_name='aspectos_legales')
    aspectolegal = models.TextField(verbose_name="Aspecto Legal")

    class Meta:
        verbose_name = "Aspecto Legal Ops"
        verbose_name_plural = "Aspectos Legales Ops"

class ops3_2AspectosIdoneidad(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.CASCADE, to_field='numeroComponente', db_column='NumeroComponente', related_name='aspectos_idoneidad')
    idoneidad = models.TextField(verbose_name="Idoneidad (Educación y Formación)")

    class Meta:
        verbose_name = "Aspecto Idoneidad Ops"
        verbose_name_plural = "Aspectos Idoneidad Ops"

class ops3_2AspectosExperiencia(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.CASCADE, to_field='numeroComponente', db_column='NumeroComponente', related_name='aspectos_experiencia')
    experiencia = models.TextField(verbose_name="Experiencia requerida")

    class Meta:
        verbose_name = "Aspecto Experiencia Ops"
        verbose_name_plural = "Aspectos Experiencia Ops"

class ops33_ValorTotaldelContratoyformadepago(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.CASCADE, to_field='numeroComponente', db_column='NumeroComponente', related_name='valor_formas_pago')
    formadepago = models.TextField(verbose_name="Forma de pago")

    class Meta:
        verbose_name = "Valor Y Forma Pago Ops"
        verbose_name_plural = "Valor Y Forma Pago Ops"

class ops4garantias(models.Model):
    NumeroComponente = models.OneToOneField(opsComponenteTecnico, on_delete=models.CASCADE, to_field='numeroComponente', db_column='NumeroComponente', related_name='garantia')
    tiene_garantias = models.BooleanField(default=False, verbose_name="Requiere Garantías")

    class Meta:
        verbose_name = "Garantías Ops"
        verbose_name_plural = "Garantías Ops"

class ops4garantiasDetalle(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.CASCADE, to_field='numeroComponente', db_column='NumeroComponente', related_name='garantias_detalle')
    cabecera = models.ForeignKey(ops4garantias, on_delete=models.CASCADE, related_name='detalles')
    garantia = models.CharField(max_length=255, verbose_name="Garantía a exigir")

    class Meta:
        verbose_name = "Detalle Garantía Ops"
        verbose_name_plural = "Detalles Garantía Ops"

class ops4dependencia(models.Model):
    NumeroComponente = models.OneToOneField(opsComponenteTecnico, on_delete=models.CASCADE, to_field='numeroComponente', db_column='NumeroComponente', related_name='estado_dependencia')
    Area = models.CharField(max_length=255, blank=True, null=True, verbose_name="Área Solicitante")
    Subgerencia = models.CharField(max_length=255, blank=True, null=True, verbose_name="Subgerencia")
    Dependencia = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dependencia")
    fecha = models.DateField(blank=True, null=True, verbose_name="Fecha de Solicitud")

    class Meta:
        verbose_name = "Dependencia Ops"
        verbose_name_plural = "Dependencias Ops"

class ops4viabilidad(models.Model):
    NumeroComponente = models.OneToOneField(opsComponenteTecnico, on_delete=models.CASCADE, to_field='numeroComponente', db_column='NumeroComponente', related_name='estado_viabilidad')
    Subgerencia = models.CharField(max_length=255, blank=True, null=True, verbose_name="Subgerencia que da Viabilidad")

    class Meta:
        verbose_name = "Viabilidad Ops"
        verbose_name_plural = "Viabilidades Ops"

class ops4Disponibilidad(models.Model):
    NumeroComponente = models.OneToOneField(opsComponenteTecnico, on_delete=models.CASCADE, to_field='numeroComponente', db_column='NumeroComponente', related_name='disponibilidad')
    NumerodeCdp = models.CharField(max_length=100, blank=True, null=True, verbose_name="Número de CDP")

    class Meta:
        verbose_name = "Disponibilidad Ops"
        verbose_name_plural = "Disponibilidades Ops"

class ops4aceptaGerencia(models.Model):
    NumeroComponente = models.OneToOneField(opsComponenteTecnico, on_delete=models.CASCADE, to_field='numeroComponente', db_column='NumeroComponente', related_name='aceptacion_gerencia')
    aceptagerencia = models.BooleanField(default=False, verbose_name="Aprueba Gerencia")

    class Meta:
        verbose_name = "Aceptación Gerencia Ops"
        verbose_name_plural = "Aceptaciones Gerencia Ops"
