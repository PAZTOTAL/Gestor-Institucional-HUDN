from django.db import models
from consultas_externas.models import Gentercer

class CDP(models.Model):
    cdp_numero = models.CharField(max_length=50, unique=True, verbose_name="Número CDP")
    fecha = models.DateField(verbose_name="Fecha CDP")
    valor = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="Valor")
    tercero = models.ForeignKey(Gentercer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Tercero", db_constraint=False)
    objeto = models.TextField(verbose_name="Objeto")
    rubro = models.CharField(max_length=100, verbose_name="Rubro", blank=True, null=True)
    nombre_rubro = models.CharField(max_length=255, verbose_name="Nombre Rubro", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CDP {self.cdp_numero} - {self.fecha}"

    class Meta:
        verbose_name = "CDP (Certificado Disponibilidad Presupuestal)"
        verbose_name_plural = "CDPs"

class RP(models.Model):
    rp_numero = models.CharField(max_length=50, unique=True, verbose_name="Número RP")
    cdp = models.ForeignKey(CDP, on_delete=models.CASCADE, related_name='rps', verbose_name="CDP Asociado")
    fecha = models.DateField(verbose_name="Fecha RP")
    valor = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="Valor")
    tercero = models.ForeignKey(Gentercer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Tercero", db_constraint=False)
    objeto = models.TextField(verbose_name="Objeto")
    otros_datos = models.TextField(blank=True, null=True, verbose_name="Otros Datos de Importancia")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"RP {self.rp_numero} - {self.fecha}"

    class Meta:
        verbose_name = "RP (Registro Presupuestal)"
        verbose_name_plural = "RPs"
