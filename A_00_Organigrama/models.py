from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError

# ============================
# Validadores reutilizables
# ============================
def exact_len(n: int):
    return MinLengthValidator(n, message=f"Debe tener exactamente {n} caracteres.")

only_upper_letters_digits = RegexValidator(
    regex=r"^[A-Z0-9]+$",
    message="Use solo mayúsculas y dígitos (sin espacios).",
)

# ============================
# Modelos del Organigrama (App 001)
# ============================

class Organigrama01(models.Model):
    codigo = models.CharField(
        max_length=3, primary_key=True, validators=[exact_len(3), only_upper_letters_digits], verbose_name="Código Nivel 1"
    )
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "tablas_001_Organigrama_Nivel1"
        verbose_name = "Organigrama Nivel 1"
        verbose_name_plural = "Organigramas Nivel 1"
        ordering = ("codigo",)

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


class Organigrama02(models.Model):
    Organigrama01 = models.ForeignKey(
        "Organigrama01", on_delete=models.PROTECT, related_name="nivel2", verbose_name="Nivel 1"
    )
    codigo = models.CharField(
        max_length=2, validators=[exact_len(2), only_upper_letters_digits], verbose_name="Código Nivel 2"
    )
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "tablas_001_Organigrama_Nivel2"
        verbose_name = "Organigrama Nivel 2"
        verbose_name_plural = "Organigramas Nivel 2"
        ordering = ("Organigrama01_id", "codigo")
        unique_together = ("Organigrama01", "codigo")

    def __str__(self):
        return f"{self.Organigrama01.codigo}{self.codigo} - {self.descripcion}"


class Organigrama03(models.Model):
    Organigrama01 = models.ForeignKey(
        "Organigrama01", on_delete=models.PROTECT, related_name="nivel3p1", verbose_name="Nivel 1"
    )
    Organigrama02 = models.ForeignKey(
        "Organigrama02", on_delete=models.PROTECT, related_name="nivel3", verbose_name="Nivel 2"
    )
    codigo = models.CharField(
        max_length=2, validators=[exact_len(2), only_upper_letters_digits], verbose_name="Código Nivel 3"
    )
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "tablas_001_Organigrama_Nivel3"
        verbose_name = "Organigrama Nivel 3"
        verbose_name_plural = "Organigramas Nivel 3"
        ordering = ("Organigrama01_id", "Organigrama02_id", "codigo")
        unique_together = ("Organigrama01", "Organigrama02", "codigo")

    def clean(self):
        super().clean()
        if self.Organigrama02_id and self.Organigrama01_id:
            if self.Organigrama02 and self.Organigrama02.Organigrama01_id != self.Organigrama01_id:
                raise ValidationError({"Organigrama02": "El nivel 2 no pertenece al nivel 1 seleccionado."})

    def __str__(self):
        return f"{self.Organigrama01.codigo}{self.Organigrama02.codigo}{self.codigo} - {self.descripcion}"


class Organigrama04(models.Model):
    Organigrama01 = models.ForeignKey(
        "Organigrama01", on_delete=models.PROTECT, related_name="nivel4p1", verbose_name="Nivel 1"
    )
    Organigrama02 = models.ForeignKey(
        "Organigrama02", on_delete=models.PROTECT, related_name="nivel4p2", verbose_name="Nivel 2"
    )
    Organigrama03 = models.ForeignKey(
        "Organigrama03", on_delete=models.PROTECT, related_name="nivel4", verbose_name="Nivel 3"
    )
    codigo = models.CharField(
        max_length=3, validators=[exact_len(3), only_upper_letters_digits], verbose_name="Código Nivel 4"
    )
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "tablas_001_Organigrama_Nivel4"
        verbose_name = "Organigrama Nivel 4"
        verbose_name_plural = "Organigramas Nivel 4"
        ordering = ("Organigrama01_id", "Organigrama02_id", "Organigrama03_id", "codigo")
        unique_together = ("Organigrama01", "Organigrama02", "Organigrama03", "codigo")

    def clean(self):
        super().clean()
        if self.Organigrama03_id and self.Organigrama02_id:
            if self.Organigrama03 and self.Organigrama03.Organigrama02_id != self.Organigrama02_id:
                 raise ValidationError({"Organigrama03": "El nivel 3 no pertenece al nivel 2 seleccionado."})
        if self.Organigrama02_id and self.Organigrama01_id:
            if self.Organigrama02 and self.Organigrama02.Organigrama01_id != self.Organigrama01_id:
                raise ValidationError({"Organigrama02": "El nivel 2 no pertenece al nivel 1 seleccionado."})

    def __str__(self):
        return f"{self.Organigrama01.codigo}{self.Organigrama02.codigo}{self.Organigrama03.codigo}{self.codigo} - {self.descripcion}"


class Organigrama05(models.Model):
    Organigrama01 = models.ForeignKey(
        "Organigrama01", on_delete=models.PROTECT, related_name="nivel5p1", verbose_name="Nivel 1"
    )
    Organigrama02 = models.ForeignKey(
        "Organigrama02", on_delete=models.PROTECT, related_name="nivel5p2", verbose_name="Nivel 2"
    )
    Organigrama03 = models.ForeignKey(
        "Organigrama03", on_delete=models.PROTECT, related_name="nivel5p3", verbose_name="Nivel 3"
    )
    Organigrama04 = models.ForeignKey(
        "Organigrama04", on_delete=models.PROTECT, related_name="nivel5", verbose_name="Nivel 4"
    )
    codigo = models.CharField(
        max_length=2, validators=[exact_len(2), only_upper_letters_digits], verbose_name="Código Nivel 5"
    )
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "tablas_001_Organigrama_Nivel5"
        verbose_name = "Organigrama Nivel 5"
        verbose_name_plural = "Organigramas Nivel 5"
        ordering = ("Organigrama01_id", "Organigrama02_id", "Organigrama03_id", "Organigrama04_id", "codigo")
        unique_together = ("Organigrama01", "Organigrama02", "Organigrama03", "Organigrama04", "codigo")

    def clean(self):
        super().clean()
        if self.Organigrama04_id and self.Organigrama03_id:
            if self.Organigrama04 and self.Organigrama04.Organigrama03_id != self.Organigrama03_id:
                raise ValidationError({"Organigrama04": "El nivel 4 no pertenece al nivel 3 seleccionado."})
        if self.Organigrama03_id and self.Organigrama02_id:
            if self.Organigrama03 and self.Organigrama03.Organigrama02_id != self.Organigrama02_id:
                raise ValidationError({"Organigrama03": "El nivel 3 no pertenece al nivel 2 seleccionado."})
        if self.Organigrama02_id and self.Organigrama01_id:
            if self.Organigrama02 and self.Organigrama02.Organigrama01_id != self.Organigrama01_id:
                raise ValidationError({"Organigrama02": "El nivel 2 no pertenece al nivel 1 seleccionado."})

    def __str__(self):
        return f"{self.Organigrama01.codigo}{self.Organigrama02.codigo}{self.Organigrama03.codigo}{self.Organigrama04.codigo}{self.codigo} - {self.descripcion}"


class Organigrama06(models.Model):
    Organigrama01 = models.ForeignKey(
        "Organigrama01", on_delete=models.PROTECT, related_name="nivel6p1", verbose_name="Nivel 1"
    )
    Organigrama02 = models.ForeignKey(
        "Organigrama02", on_delete=models.PROTECT, related_name="nivel6p2", verbose_name="Nivel 2"
    )
    Organigrama03 = models.ForeignKey(
        "Organigrama03", on_delete=models.PROTECT, related_name="nivel6p3", verbose_name="Nivel 3"
    )
    Organigrama04 = models.ForeignKey(
        "Organigrama04", on_delete=models.PROTECT, related_name="nivel6p4", verbose_name="Nivel 4"
    )
    Organigrama05 = models.ForeignKey(
        "Organigrama05", on_delete=models.PROTECT, related_name="nivel6p5", verbose_name="Nivel 5"
    )
    codigo = models.CharField(
        max_length=3, validators=[exact_len(3), only_upper_letters_digits], verbose_name="Código Nivel 6"
    )
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "tablas_001_Organigrama_Nivel6"
        verbose_name = "Organigrama Nivel 6"
        verbose_name_plural = "Organigramas Nivel 6"
        ordering = ("Organigrama01_id", "Organigrama02_id", "Organigrama03_id", "Organigrama04_id", "Organigrama05_id", "codigo")
        unique_together = ("Organigrama01", "Organigrama02", "Organigrama03", "Organigrama04", "Organigrama05", "codigo")

    def clean(self):
        super().clean()
        if self.Organigrama05_id and self.Organigrama04_id:
            if self.Organigrama05 and self.Organigrama05.Organigrama04_id != self.Organigrama04_id:
                raise ValidationError({"Organigrama05": "El nivel 5 no pertenece al nivel 4 seleccionado."})
        if self.Organigrama04_id and self.Organigrama03_id:
            if self.Organigrama04 and self.Organigrama04.Organigrama03_id != self.Organigrama03_id:
                raise ValidationError({"Organigrama04": "El nivel 4 no pertenece al nivel 3 seleccionado."})
        if self.Organigrama03_id and self.Organigrama02_id:
            if self.Organigrama03 and self.Organigrama03.Organigrama02_id != self.Organigrama02_id:
                 raise ValidationError({"Organigrama03": "El nivel 3 no pertenece al nivel 2 seleccionado."})
        if self.Organigrama02_id and self.Organigrama01_id:
            if self.Organigrama02 and self.Organigrama02.Organigrama01_id != self.Organigrama01_id:
                raise ValidationError({"Organigrama02": "El nivel 2 no pertenece al nivel 1 seleccionado."})

    def __str__(self):
        return (
            f"{self.Organigrama01.codigo}{self.Organigrama02.codigo}{self.Organigrama03.codigo}"
            f"{self.Organigrama04.codigo}{self.Organigrama05.codigo}{self.codigo} - {self.descripcion}"
        )


class doc_tabHonorarios(models.Model):
    codigo = models.CharField(max_length=10, validators=[only_upper_letters_digits], verbose_name="Código Honorario")
    valorHora = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="Valor por Hora")
    valorMes = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="Valor por Mes")

    class Meta:
        db_table = "tablas_001_Organigrama_Honorarios"
        verbose_name = "Tabla de Honorarios"
        verbose_name_plural = "Tablas de Honorarios"
        ordering = ("codigo",)

    def __str__(self):
        return f"{self.codigo} - Hora: {self.valorHora} / Mes: {self.valorMes}"


class Supervisores(models.Model):
    Organigrama01 = models.ForeignKey(
        "Organigrama01", on_delete=models.PROTECT, related_name="+", verbose_name="Nivel 1"
    )
    Organigrama02 = models.ForeignKey(
        "Organigrama02", on_delete=models.PROTECT, related_name="+", verbose_name="Nivel 2"
    )
    Organigrama03 = models.ForeignKey(
        "Organigrama03", on_delete=models.PROTECT, related_name="+", verbose_name="Nivel 3"
    )
    Organigrama04 = models.ForeignKey(
        "Organigrama04", on_delete=models.PROTECT, related_name="+", verbose_name="Nivel 4", null=True, blank=True
    )
    Organigrama05 = models.ForeignKey(
        "Organigrama05", on_delete=models.PROTECT, related_name="+", verbose_name="Nivel 5", null=True, blank=True
    )
    Organigrama06 = models.ForeignKey(
        "Organigrama06", on_delete=models.PROTECT, related_name="+", verbose_name="Nivel 6", null=True, blank=True
    )
    Item = models.PositiveIntegerField(editable=False, verbose_name="Ítem")
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Usuario",
        null=True,
        blank=True
    )
 
    class Meta:
        db_table = "tablas_001_Organigrama_Supervisores"
        verbose_name = "Supervisor"
        verbose_name_plural = "Supervisores"
        ordering = ("Item",)
 
    def __str__(self):
        return f"{self.usuario} (Item {self.Item})"
 
    def save(self, *a, **k):
        if not self.Item:
            last = (
                Supervisores.objects.all()
                .order_by("-Item")
                .values_list("Item", flat=True)
                .first()
                or 0
            )
            self.Item = last + 1
        super().save(*a, **k)
