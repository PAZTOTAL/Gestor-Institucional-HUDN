from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

# ============================
# Validadores reutilizables
# ============================
def exact_len(n: int):
    return MinLengthValidator(n, message=f"Debe tener exactamente {n} caracteres.")

only_upper_letters_digits = RegexValidator(
    regex=r"^[A-Z0-9]+$",
    message="Use solo mayúsculas y dígitos (sin espacios).",
)

only_letters_spaces = RegexValidator(
    regex=r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s\-\.\(\)\/]+$",
    message="Solo letras, espacios y signos básicos (- . / ( )).",
)

only_digits = RegexValidator(
    r"^\d+$", "Solo se permiten números (sin letras ni caracteres especiales)."
)




# ============================
# Catálogos generales
# ============================
class ListaTipoDocumento(models.Model):
    codigo = models.CharField(
        max_length=2,
        primary_key=True,
        validators=[exact_len(2), only_upper_letters_digits],
        verbose_name="Código Tipo Documento",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "ListaTipoDocumento"
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documento"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ListaTipoSexo(models.Model):
    codigo = models.CharField(
        max_length=2,
        primary_key=True,
        validators=[exact_len(2), only_upper_letters_digits],
        verbose_name="Código Sexo",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "ListaTipoSexo"
        verbose_name = "Sexo"
        verbose_name_plural = "Sexos"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ListaTipoColor(models.Model):
    codigo = models.CharField(
        max_length=3,
        primary_key=True,
        validators=[exact_len(3), only_upper_letters_digits],
        verbose_name="Código Color",
    )
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "ListaTipoColor"
        verbose_name = "Color"
        verbose_name_plural = "Colores"

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


class ListaTipoGenero(models.Model):
    codigo = models.CharField(
        max_length=2,
        primary_key=True,
        validators=[exact_len(2), only_upper_letters_digits],
        verbose_name="Código Género",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "ListaTipoGenero"
        verbose_name = "Género"
        verbose_name_plural = "Géneros"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ListaTipoHabito(models.Model):
    codigo = models.CharField(
        max_length=2,
        primary_key=True,
        validators=[exact_len(2), only_upper_letters_digits],
        verbose_name="Código Hábito",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")
    descripcion = models.CharField(max_length=400, verbose_name="Descripción")

    class Meta:
        db_table = "ListaTipoHabito"
        verbose_name = "Hábito"
        verbose_name_plural = "Hábitos"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ListaTipoEstadoCivil(models.Model):
    codigo = models.CharField(
        max_length=2,
        primary_key=True,
        validators=[exact_len(2), only_upper_letters_digits],
        verbose_name="Código Estado Civil",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")
    descripcion = models.CharField(max_length=400, verbose_name="Descripción")

    class Meta:
        db_table = "ListaTipoEstadoCivil"
        verbose_name = "Estado Civil"
        verbose_name_plural = "Estados Civiles"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ListaTipoConsanguinidad(models.Model):
    codigo = models.CharField(
        max_length=2,
        primary_key=True,
        validators=[exact_len(2), only_upper_letters_digits],
        verbose_name="Código Consanguinidad",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "ListaTipoConsanguinidad"
        verbose_name = "Consanguinidad"
        verbose_name_plural = "Grados de Consanguinidad"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ListaTipoUnidadDeMedida(models.Model):
    codigo = models.CharField(
        max_length=3,
        primary_key=True,
        validators=[exact_len(3), only_upper_letters_digits],
        verbose_name="Código Unidad",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")
    # nombre viene de models.Model
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "ListaTipoUnidadDeMedida"
        verbose_name = "Unidad de Medida"
        verbose_name_plural = "Unidades de Medida"

    def __str__(self):
        return f"{self.codigo}-{self.nombre}"


class ListaTipoUnidadDeMedidaDetalle(models.Model):
    ListaUnidadDeMedida = models.ForeignKey(
        "BasesGenerales.ListaTipoUnidadDeMedida",
        on_delete=models.PROTECT,
        related_name="detalles",
        verbose_name="Unidad de Medida",
    )
    codigo = models.CharField(
        max_length=3,
        validators=[exact_len(3), only_upper_letters_digits],
        verbose_name="Código Detalle",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")
    # nombre viene de models.Model
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "ListaTipoUnidadDeMedidaDetalle"
        verbose_name = "Detalle Unidad de Medida"
        verbose_name_plural = "Detalles Unidades de Medida"
        unique_together = ("ListaUnidadDeMedida", "codigo")

    def __str__(self):
        return f"{self.ListaUnidadDeMedida.codigo}-{self.codigo}-{self.nombre}"


class ListaTipoGrupoSanguineo(models.Model):
    codigo = models.CharField(
        max_length=3,
        primary_key=True,
        validators=[exact_len(3), only_upper_letters_digits],
        verbose_name="Código Grupo Sanguíneo",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "ListaTipoGrupoSanguineo"
        verbose_name = "Grupo Sanguíneo"
        verbose_name_plural = "Grupos Sanguíneos"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"







# ============================
# Catálogo de Formatos HUDN
# ============================

# Validador para código de formato: FR + 3 letras mayúsculas + guion + 3 dígitos
formato_hudn_validator = RegexValidator(
    regex=r"^FR[A-Z]{3}-\d{3}$",
    message="El código debe tener el formato FRXXX-NNN (ej: FRJUR-001, FRADM-025)",
)


class Formatos_Hudn(models.Model):
    codigo_formato = models.CharField(
        max_length=10,
        primary_key=True,
        validators=[formato_hudn_validator],
        verbose_name="Código del Formato",
        help_text="Formato: FR + 3 letras del área + guion + 3 dígitos (ej: FRJUR-001)",
    )
    nombre_formato = models.CharField(
        max_length=200,
        verbose_name="Nombre del Formato",
        validators=[only_letters_spaces],
    )
    version = models.CharField(
        max_length=10,
        verbose_name="Versión",
        default="1.0",
        help_text="Versión del formato (ej: 1.0, 2.1, etc.)",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación",
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Modificación",
    )
    elaborado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="formatos_elaborados",
        verbose_name="Elaborado Por",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="formatos_modificados",
        null=True,
        blank=True,
        verbose_name="Modificado Por",
    )

    class Meta:
        db_table = "Formatos_Hudn"
        verbose_name = "Formato HUDN"
        verbose_name_plural = "Formatos HUDN"
        ordering = ("codigo_formato",)

    def __str__(self):
        return f"{self.codigo_formato} - {self.nombre_formato} (v{self.version})"

    def save(self, *args, **kwargs):
        # Convertir código a mayúsculas automáticamente
        if self.codigo_formato:
            self.codigo_formato = self.codigo_formato.upper()
        super().save(*args, **kwargs)




# ============================
# Catálogos Georeferencia
# ============================
class Geo01Pais(models.Model):
    codigo = models.CharField(
        max_length=3,
        primary_key=True,
        validators=[exact_len(3), only_upper_letters_digits],
        verbose_name="Código País",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")    
    # nombre viene de models.Model
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "Geo01Pais"
        verbose_name = "País"
        verbose_name_plural = "Países"
        ordering = ("codigo",)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Geo02Departamento(models.Model):
    Geo01Pais = models.ForeignKey(
        "BasesGenerales.Geo01Pais",
        on_delete=models.PROTECT,
        related_name="departamentos",
        verbose_name="País",
    )
    codigo = models.CharField(
        max_length=2,
        validators=[exact_len(2), only_upper_letters_digits],
        verbose_name="Código Departamento",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")    
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "Geo02Departamento"
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        unique_together = ("Geo01Pais", "codigo")

    def __str__(self):
        return f"{self.Geo01Pais.codigo}{self.codigo} - {self.nombre}"


class Geo03Municipio(models.Model):
    Geo01Pais = models.ForeignKey(
        "BasesGenerales.Geo01Pais",
        on_delete=models.PROTECT,
        related_name="municipios",
        verbose_name="País",
    )
    Geo02Departamento = models.ForeignKey(
        "BasesGenerales.Geo02Departamento",
        on_delete=models.PROTECT,
        related_name="municipios",
        verbose_name="Departamento",
    )
    codigo = models.CharField(
        max_length=3,
        validators=[exact_len(3), only_upper_letters_digits],
        verbose_name="Código Municipio",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")    
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "Geo03Municipio"
        verbose_name = "Municipio"
        verbose_name_plural = "Municipios"
        unique_together = ("Geo01Pais", "Geo02Departamento", "codigo")

    def clean(self):
        super().clean()
        if self.Geo01Pais_id and self.Geo02Departamento_id:
            if self.Geo02Departamento.Geo01Pais_id != self.Geo01Pais_id:
                raise ValidationError(
                    {"Geo02Departamento": "El departamento no pertenece al país seleccionado."}
                )

    def __str__(self):
        return f"{self.Geo01Pais.codigo}{self.Geo02Departamento.codigo}{self.codigo} - {self.nombre}"


class Geo04Ciudad(models.Model):
    Geo01Pais = models.ForeignKey(
        "BasesGenerales.Geo01Pais",
        on_delete=models.PROTECT,
        related_name="ciudades",
        verbose_name="País",
    )
    Geo02Departamento = models.ForeignKey(
        "BasesGenerales.Geo02Departamento",
        on_delete=models.PROTECT,
        related_name="ciudades",
        verbose_name="Departamento",
    )
    Geo03Municipio = models.ForeignKey(
        "BasesGenerales.Geo03Municipio",
        on_delete=models.PROTECT,
        related_name="ciudades",
        verbose_name="Municipio",
    )
    codigo = models.CharField(
        max_length=3,
        validators=[exact_len(3), only_upper_letters_digits],
        verbose_name="Código Ciudad",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")    
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "Geo04Ciudad"
        verbose_name = "Ciudad"
        verbose_name_plural = "Ciudades"
        ordering = ("Geo01Pais", "Geo02Departamento", "Geo03Municipio", "codigo")
        unique_together = ("Geo01Pais", "Geo02Departamento", "Geo03Municipio", "codigo")

    def clean(self):
        super().clean()
        if (
            self.Geo01Pais_id
            and self.Geo02Departamento_id
            and self.Geo03Municipio_id
        ):
            if self.Geo02Departamento.Geo01Pais_id != self.Geo01Pais_id:
                raise ValidationError(
                    {"Geo02Departamento": "El departamento no pertenece al país seleccionado."}
                )
            if self.Geo03Municipio.Geo02Departamento_id != self.Geo02Departamento_id:
                raise ValidationError(
                    {"Geo03Municipio": "El municipio no pertenece al departamento seleccionado."}
                )
            if self.Geo03Municipio.Geo01Pais_id != self.Geo01Pais_id:
                raise ValidationError(
                    {"Geo03Municipio": "El municipio no pertenece al país seleccionado."}
                )

    def __str__(self):
        return (
            f"{self.Geo01Pais.codigo}"
            f"{self.Geo02Departamento.codigo}"
            f"{self.Geo03Municipio.codigo}"
            f"{self.codigo} - {self.nombre}"
        )


class Geo05Comuna(models.Model):
    Geo01Pais = models.ForeignKey(
        "BasesGenerales.Geo01Pais",
        on_delete=models.PROTECT,
        related_name="comunas",
        verbose_name="País",
    )
    Geo02Departamento = models.ForeignKey(
        "BasesGenerales.Geo02Departamento",
        on_delete=models.PROTECT,
        related_name="comunas",
        verbose_name="Departamento",
    )
    Geo03Municipio = models.ForeignKey(
        "BasesGenerales.Geo03Municipio",
        on_delete=models.PROTECT,
        related_name="comunas",
        verbose_name="Municipio",
    )
    Geo04Ciudad = models.ForeignKey(
        "BasesGenerales.Geo04Ciudad",
        on_delete=models.PROTECT,
        related_name="comunas",
        verbose_name="Ciudad",
    )
    codigo = models.CharField(
        max_length=2,
        validators=[exact_len(2), only_upper_letters_digits],
        verbose_name="Código Comuna",
    )
    nombre=models.CharField(max_length=100,verbose_name="Nombre")    
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "Geo05Comuna"
        verbose_name = "Comuna"
        verbose_name_plural = "Comunas"
        ordering = ("Geo01Pais", "Geo02Departamento", "Geo03Municipio", "Geo04Ciudad", "codigo")
        unique_together = ("Geo01Pais", "Geo02Departamento", "Geo03Municipio", "Geo04Ciudad", "codigo")

    def clean(self):
        super().clean()
        if (
            self.Geo01Pais_id
            and self.Geo02Departamento_id
            and self.Geo03Municipio_id
            and self.Geo04Ciudad_id
        ):
            if self.Geo02Departamento.Geo01Pais_id != self.Geo01Pais_id:
                raise ValidationError({"Geo02Departamento": "El departamento no pertenece al país seleccionado."})
            if self.Geo03Municipio.Geo02Departamento_id != self.Geo02Departamento_id:
                raise ValidationError({"Geo03Municipio": "El municipio no pertenece al departamento seleccionado."})
            if self.Geo03Municipio.Geo01Pais_id != self.Geo01Pais_id:
                raise ValidationError({"Geo03Municipio": "El municipio no pertenece al país seleccionado."})
            if self.Geo04Ciudad.Geo03Municipio_id != self.Geo03Municipio_id:
                raise ValidationError({"Geo04Ciudad": "La ciudad no pertenece al municipio seleccionado."})
            if self.Geo04Ciudad.Geo02Departamento_id != self.Geo02Departamento_id:
                raise ValidationError({"Geo04Ciudad": "La ciudad no pertenece al departamento seleccionado."})
            if self.Geo04Ciudad.Geo01Pais_id != self.Geo01Pais_id:
                raise ValidationError({"Geo04Ciudad": "La ciudad no pertenece al país seleccionado."})

    def __str__(self):
        return (
            f"{self.Geo01Pais.codigo}{self.Geo02Departamento.codigo}"
            f"{self.Geo03Municipio.codigo}{self.Geo04Ciudad.codigo}"
            f"{self.codigo} - {self.nombre}"
        )


# ============================
# catalogo Personas / documentos
# ============================
class DocumentoDeIdentidad(models.Model):
    # nombre = 'Usuario' (viene de base, renombramos solo el verbose_name)
    numeroDocumento = models.CharField(
        max_length=12,
        primary_key=True,
        validators=[only_digits],
        verbose_name="Número de Documento",
        help_text="Solo números (sin puntos ni letras)",
    )

    tipoDocumento = models.IntegerField(
        verbose_name="Tipo de Documento (GENTERCER)",
        null=True, 
        blank=True,
        help_text="Se carga automáticamente de GENTERCER"
    )
    
    
    primerNombre = models.CharField(
        max_length=100, validators=[only_letters_spaces], verbose_name="Primer Nombre"
    )
    segundoNombre = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[only_letters_spaces],
        verbose_name="Segundo Nombre",
    )
    primerApellido = models.CharField(
        max_length=100, validators=[only_letters_spaces], verbose_name="Primer Apellido"
    )
    segundoApellido = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[only_letters_spaces],
        verbose_name="Segundo Apellido",
    )

    class Meta:
        db_table = "DocumentoDeIdentidad"
        verbose_name = "Documento de Identidad"
        verbose_name_plural = "Documentos de Identidad"
        ordering = ("numeroDocumento",)

    def __str__(self):
        return f"{self.tipoDocumento}-{self.numeroDocumento} - {self.primerNombre} {self.primerApellido}"

    def clean(self):
        super().clean()
        if not self.numeroDocumento:
            return

        try:
            from django.apps import apps
            Gentercer = apps.get_model('consultas_externas', 'Gentercer')
            
            # Use filter().first() to avoid MultipleObjectsReturned or DoesNotExist handling complexity here
            tercero = Gentercer.objects.filter(ternumdoc=self.numeroDocumento).first()
            
            if not tercero:
                raise ValidationError({
                    'numeroDocumento': f"El documento {self.numeroDocumento} no existe en la base de datos externa (GENTERCER). No se puede continuar."
                })
            
            # Auto-populate fields from Gentercer
            self.primerNombre = tercero.terprinom or self.primerNombre
            self.segundoNombre = tercero.tersegnom or self.segundoNombre
            self.primerApellido = tercero.terpriape or self.primerApellido
            self.segundoApellido = tercero.tersegape or self.segundoApellido
            
            # Direct assignment of Type ID from Gentercer
            if tercero.tertipdoc is not None:
                self.tipoDocumento = tercero.tertipdoc

        except LookupError:
            # If app not ready or model missing (shouldn't happen in production)
            pass


class DocumentoDeIdentidadDatos(models.Model):
    numeroDocumento = models.ForeignKey(
        "BasesGenerales.DocumentoDeIdentidad",
        on_delete=models.PROTECT,
        related_name="datos",
        verbose_name="Número de Documento",
    )
    
    grupoSanguineo = models.ForeignKey(
        "BasesGenerales.ListaTipoGrupoSanguineo",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Grupo Sanguíneo",
    )
    sexo = models.ForeignKey(
        "BasesGenerales.ListaTipoSexo",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Sexo",
    )
    paisNacimiento = models.ForeignKey(
        "BasesGenerales.Geo01Pais",
        on_delete=models.PROTECT,
        related_name="personas_nacidas_pais",
        verbose_name="País de Nacimiento",
    )
    departamentoNacimiento = models.ForeignKey(
        "BasesGenerales.Geo02Departamento",
        on_delete=models.PROTECT,
        related_name="personas_nacidas_departamento",
        verbose_name="Departamento de Nacimiento",
    )
    municipioNacimiento = models.ForeignKey(
        "BasesGenerales.Geo03Municipio",
        on_delete=models.PROTECT,
        related_name="personas_nacidas_municipio",
        verbose_name="Municipio de Nacimiento",
    )
    ciudadNacimiento = models.ForeignKey(
        "BasesGenerales.Geo04Ciudad",
        on_delete=models.PROTECT,
        related_name="personas_nacidas_ciudad",
        verbose_name="Ciudad de Nacimiento",
    )
    paisExpedicion = models.ForeignKey(
        "BasesGenerales.Geo01Pais",
        on_delete=models.PROTECT,
        related_name="documentos_expedidos_pais",
        verbose_name="País de Expedición",
    )
    departamentoExpedicion = models.ForeignKey(
        "BasesGenerales.Geo02Departamento",
        on_delete=models.PROTECT,
        related_name="documentos_expedidos_departamento",
        verbose_name="Departamento de Expedición",
    )
    municipioExpedicion = models.ForeignKey(
        "BasesGenerales.Geo03Municipio",
        on_delete=models.PROTECT,
        related_name="documentos_expedidos_municipio",
        verbose_name="Municipio de Expedición",
    )
    ciudadExpedicion = models.ForeignKey(
        "BasesGenerales.Geo04Ciudad",
        on_delete=models.PROTECT,
        related_name="documentos_expedidos_ciudad",
        verbose_name="Ciudad de Expedición",
    )
    fechaNacimiento = models.DateField(verbose_name="Fecha de Nacimiento")
    fechaExpedicion = models.DateField(verbose_name="Fecha de Expedición")
    documentoPDF = models.FileField(
        upload_to="documentos_identidad/",
        blank=True,
        null=True,
        verbose_name="Copia del Documento en PDF",
    )
    correoElectronico = models.EmailField(
        max_length=150, verbose_name="Correo Electrónico de Notificación"
    )

    class Meta:
        db_table = "DocumentoDeIdentidadDatos"
        verbose_name = "Datos de Documento de Identidad"
        verbose_name_plural = "Datos de Documentos de Identidad"
        ordering = ("numeroDocumento",)

    def __str__(self):
        try:
            # Intentar mostrar Nombre del DocumentoDeIdentidad padre
            doc = self.numeroDocumento
            return f"{doc.primerNombre} {doc.primerApellido} ({doc.codigo})"
        except Exception:
            return f"{self.numeroDocumento_id}"

    @staticmethod
    def _fk_id(obj, *names):
        for n in names:
            if hasattr(obj, f"{n}_id"):
                return getattr(obj, f"{n}_id")
            if hasattr(obj, n):
                val = getattr(obj, n)
                if val is not None:
                    return getattr(val, "pk", None)
        return None

    def clean(self):
        super().clean()
        e = {}
        # Nacimiento
        if self.departamentoNacimiento_id and self.paisNacimiento_id:
            if (
                self._fk_id(self.departamentoNacimiento, "Geo01Pais", "CodigoPais", "codigoGeo01Pais")
                != self.paisNacimiento_id
            ):
                e["departamentoNacimiento"] = "El departamento de nacimiento no pertenece al país seleccionado."
        if self.municipioNacimiento_id:
            if (
                self._fk_id(self.municipioNacimiento, "Geo01Pais", "CodigoPais", "codigoGeo01Pais")
                != self.paisNacimiento_id
            ):
                e["municipioNacimiento"] = "El municipio de nacimiento no pertenece al país seleccionado."
            if (
                self._fk_id(self.municipioNacimiento, "Geo02Departamento", "CodigoDepartamento", "codigoGeo02Departamento")
                != self.departamentoNacimiento_id
            ):
                e["municipioNacimiento"] = "El municipio de nacimiento no pertenece al departamento seleccionado."
        if self.ciudadNacimiento_id:
            if (
                self._fk_id(self.ciudadNacimiento, "Geo01Pais", "CodigoPais", "codigoGeo01Pais")
                != self.paisNacimiento_id
            ):
                e["ciudadNacimiento"] = "La ciudad de nacimiento no pertenece al país seleccionado."
            if (
                self._fk_id(self.ciudadNacimiento, "Geo02Departamento", "CodigoDepartamento", "codigoGeo02Departamento")
                != self.departamentoNacimiento_id
            ):
                e["ciudadNacimiento"] = "La ciudad de nacimiento no pertenece al departamento seleccionado."
            if (
                self._fk_id(self.ciudadNacimiento, "Geo03Municipio", "CodigoMunicipio", "codigoGeo03Municipio")
                != self.municipioNacimiento_id
            ):
                e["ciudadNacimiento"] = "La ciudad de nacimiento no pertenece al municipio seleccionado."
        # Expedición
        if self.departamentoExpedicion_id and self.paisExpedicion_id:
            if (
                self._fk_id(self.departamentoExpedicion, "Geo01Pais", "CodigoPais", "codigoGeo01Pais")
                != self.paisExpedicion_id
            ):
                e["departamentoExpedicion"] = "El departamento de expedición no pertenece al país seleccionado."
        if self.municipioExpedicion_id:
            if (
                self._fk_id(self.municipioExpedicion, "Geo01Pais", "CodigoPais", "codigoGeo01Pais")
                != self.paisExpedicion_id
            ):
                e["municipioExpedicion"] = "El municipio de expedición no pertenece al país seleccionado."
            if (
                self._fk_id(self.municipioExpedicion, "Geo02Departamento", "CodigoDepartamento", "codigoGeo02Departamento")
                != self.departamentoExpedicion_id
            ):
                e["municipioExpedicion"] = "El municipio de expedición no pertenece al departamento seleccionado."
        if self.ciudadExpedicion_id:
            if (
                self._fk_id(self.ciudadExpedicion, "Geo01Pais", "CodigoPais", "codigoGeo01Pais")
                != self.paisExpedicion_id
            ):
                e["ciudadExpedicion"] = "La ciudad de expedición no pertenece al país seleccionado."
            if (
                self._fk_id(self.ciudadExpedicion, "Geo02Departamento", "CodigoDepartamento", "codigoGeo02Departamento")
                != self.departamentoExpedicion_id
            ):
                e["ciudadExpedicion"] = "La ciudad de expedición no pertenece al departamento seleccionado."
            if (
                self._fk_id(self.ciudadExpedicion, "Geo03Municipio", "CodigoMunicipio", "codigoGeo03Municipio")
                != self.municipioExpedicion_id
            ):
                e["ciudadExpedicion"] = "La ciudad de expedición no pertenece al municipio seleccionado."
        if e:
            raise ValidationError(e)

# ============================
# Catálogos contables PUC
# ============================

class Puc01Clase(models.Model):
    codigo = models.CharField(
        max_length=1, primary_key=True, validators=[exact_len(1), only_upper_letters_digits], verbose_name="Código Clase"
    )  
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        db_table = "Puc01Clase"
        verbose_name = "Clase PUC"
        verbose_name_plural = "Clases PUC"
        ordering = ("codigo",)

    def __str__(self):
        return f"{self.codigo}-{self.nombre}"


class Puc02Grupo(models.Model):
    Puc01Clase = models.ForeignKey(
        "BasesGenerales.Puc01Clase",
        on_delete=models.PROTECT,
        related_name="Puc02Grupos",
        verbose_name="Clase",
    )
    codigo = models.CharField(
        max_length=1, validators=[exact_len(1), only_upper_letters_digits], verbose_name="Código Grupo"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        db_table = "Puc02Grupo"
        verbose_name = "Grupo PUC"
        verbose_name_plural = "Grupos PUC"
        ordering = ("Puc01Clase", "codigo")
        unique_together = ("Puc01Clase", "codigo")

    def __str__(self):
        return f"{self.Puc01Clase.codigo}{self.codigo}-{self.nombre}"


class Puc03Cuenta(models.Model):
    Puc01Clase = models.ForeignKey(
        "BasesGenerales.Puc01Clase",
        on_delete=models.PROTECT,
        related_name="Puc03CuentasClase",
        verbose_name="Clase",
    )
    Puc02Grupo = models.ForeignKey(
        "BasesGenerales.Puc02Grupo",
        on_delete=models.PROTECT,
        related_name="Puc03CuentasGrupo",
        verbose_name="Grupo",
    )
    codigo = models.CharField(
        max_length=2, validators=[exact_len(2), only_upper_letters_digits], verbose_name="Código Cuenta"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        db_table = "Puc03Cuenta"
        verbose_name = "Cuenta PUC"
        verbose_name_plural = "Cuentas PUC"
        ordering = ("Puc01Clase", "Puc02Grupo", "codigo")
        unique_together = ("Puc01Clase", "Puc02Grupo", "codigo")

    def __str__(self):
        return f"{self.Puc01Clase.codigo}{self.Puc02Grupo.codigo}{self.codigo}-{self.nombre}"


class Puc04Subcuenta(models.Model):
    Puc01Clase = models.ForeignKey(
        "BasesGenerales.Puc01Clase",
        on_delete=models.PROTECT,
        related_name="Puc04SubcuentasClase",
        verbose_name="Clase",
    )
    Puc02Grupo = models.ForeignKey(
        "BasesGenerales.Puc02Grupo",
        on_delete=models.PROTECT,
        related_name="Puc04SubcuentasGrupo",
        verbose_name="Grupo",
    )
    Puc03Cuenta = models.ForeignKey(
        "BasesGenerales.Puc03Cuenta",
        on_delete=models.PROTECT,
        related_name="Puc04SubcuentasCuenta",
        verbose_name="Cuenta",
    )
    codigo = models.CharField(
        max_length=2, validators=[exact_len(2), only_upper_letters_digits], verbose_name="Código Subcuenta"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        db_table = "Puc04Subcuenta"
        verbose_name = "Subcuenta PUC"
        verbose_name_plural = "Subcuentas PUC"
        ordering = ("Puc01Clase", "Puc02Grupo", "Puc03Cuenta", "codigo")
        unique_together = ("Puc01Clase", "Puc02Grupo", "Puc03Cuenta", "codigo")

    def __str__(self):
        return f"{self.Puc01Clase.codigo}{self.Puc02Grupo.codigo}{self.Puc03Cuenta.codigo}{self.codigo}-{self.nombre}"


# ============================
# Catálogos contable UNSPSC
# ============================
class UNSPS01Segmento(models.Model):
    codigo = models.CharField(
        max_length=2, primary_key=True, validators=[exact_len(2), only_upper_letters_digits], verbose_name="Código Segmento"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "UNSPS01Segmento"
        verbose_name = "Segmento UNSPSC"
        verbose_name_plural = "Segmentos UNSPSC"
        ordering = ("codigo",)

    def __str__(self):
        return f"{self.codigo}-{self.nombre}"


class UNSPS02Familia(models.Model):
    UNSPS01Segmento = models.ForeignKey(
        "BasesGenerales.UNSPS01Segmento",
        on_delete=models.PROTECT,
        related_name="familias",
        verbose_name="Segmento",
    )
    codigo = models.CharField(
        max_length=2, validators=[exact_len(2), only_upper_letters_digits], verbose_name="Código Familia"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "UNSPS02Familia"
        verbose_name = "Familia UNSPSC"
        verbose_name_plural = "Familias UNSPSC"
        ordering = ("UNSPS01Segmento", "codigo")
        unique_together = ("UNSPS01Segmento", "codigo")

    def __str__(self):
        return f"{self.UNSPS01Segmento.codigo}{self.codigo}-{self.nombre}"


class UNSPS03Clase(models.Model):
    UNSPS01Segmento = models.ForeignKey(
        "BasesGenerales.UNSPS01Segmento",
        on_delete=models.PROTECT,
        related_name="clases_segmento",
        verbose_name="Segmento",
    )
    UNSPS02Familia = models.ForeignKey(
        "BasesGenerales.UNSPS02Familia",
        on_delete=models.PROTECT,
        related_name="clases",
        verbose_name="Familia",
    )
    codigo = models.CharField(
        max_length=2, validators=[exact_len(2), only_upper_letters_digits], verbose_name="Código Clase"
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "UNSPS03Clase"
        verbose_name = "Clase UNSPSC"
        verbose_name_plural = "Clases UNSPSC"
        ordering = ("UNSPS01Segmento", "UNSPS02Familia", "codigo")
        unique_together = ("UNSPS01Segmento", "UNSPS02Familia", "codigo")

    def __str__(self):
        return f"{self.UNSPS01Segmento.codigo}{self.UNSPS02Familia.codigo}{self.codigo}-{self.nombre}"

class UNSPS04Producto(models.Model):
    UNSPS01Segmento = models.ForeignKey("BasesGenerales.UNSPS01Segmento", on_delete=models.PROTECT, related_name="productos_segmento", verbose_name="Segmento")
    UNSPS02Familia = models.ForeignKey("BasesGenerales.UNSPS02Familia", on_delete=models.PROTECT, related_name="productos_familia", verbose_name="Familia")
    UNSPS03Clase = models.ForeignKey("BasesGenerales.UNSPS03Clase", on_delete=models.PROTECT, related_name="productos", verbose_name="Clase")
    codigo = models.CharField(max_length=2, validators=[exact_len(2), only_upper_letters_digits], verbose_name="Código Producto")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "UNSPS04Producto"
        verbose_name = "Producto UNSPSC"
        verbose_name_plural = "Productos UNSPSC"
        ordering = ("UNSPS01Segmento", "UNSPS02Familia", "UNSPS03Clase", "codigo")
        unique_together = ("UNSPS01Segmento", "UNSPS02Familia", "UNSPS03Clase", "codigo")

    def __str__(self):
        return f"{self.UNSPS01Segmento.codigo}{self.UNSPS02Familia.codigo}{self.UNSPS03Clase.codigo}{self.codigo}-{self.nombre}"
# ============================
# Catálogos contable presupuesto
# ============================

class presupuestoAsignado(models.Model):
    CodigoPresupuestal = models.CharField(max_length=15, verbose_name="Código Presupuestal")
    ValorAsignado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Asignado")
    fecha_Asignado = models.DateField(verbose_name="Fecha")

    class Meta:
        db_table = "presupuestoAsignado"
        verbose_name = "Presupuesto Asignado"
        verbose_name_plural = "Presupuestos Asignados"
        ordering = ("fecha_Asignado",)

    def __str__(self):
        return f"{self.CodigoPresupuestal} - ${self.ValorAsignado}"


class solicitudCDP(models.Model):
    NumeroSolicitud = models.PositiveIntegerField(unique=True, verbose_name="Número de Solicitud")
    fecha_Solicitud = models.DateField(verbose_name="Fecha de Solicitud")
    # solicitante = models.ForeignKey(
    #     "empresa.Reg05Empresa_Empleados",
    #     on_delete=models.PROTECT,
    #     related_name="solicitudes_cdp",
    #     verbose_name="Solicitante"
    # )
    CodigoPresupuestal = models.ForeignKey(
        presupuestoAsignado,
        on_delete=models.PROTECT,
        related_name="solicitudes_cdp",
        verbose_name="Código Presupuestal"
    )
    ValorSolicitado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Solicitado")
    objeto = models.CharField(max_length=600, verbose_name="Objeto")
    fecha_Aprobacion = models.DateField(verbose_name="Fecha de Aprobación", null=True, blank=True)
    # aprobado = models.ForeignKey(
    #     "empresa.Reg05Empresa_Empleados",
    #     on_delete=models.PROTECT,
    #     related_name="solicitudes_cdp_aprobadas",
    #     verbose_name="Aprobador",
    #     null=True,
    #     blank=True
    # )

    class Meta:
        db_table = "solicitudCDP"
        verbose_name = "Solicitud CDP"
        verbose_name_plural = "Solicitudes CDP"
        ordering = ("fecha_Solicitud",)

    def __str__(self):
        return f"{self.NumeroSolicitud} - {self.fecha_Solicitud}"


class presupuestoCDP(models.Model):
    fechaCDP = models.DateField(verbose_name="Fecha")
    numeroCdp = models.IntegerField(verbose_name="Número de CDP")
    solicitudCDP = models.ForeignKey(
        solicitudCDP,
        on_delete=models.PROTECT,
        related_name="cdps",
        verbose_name="Solicitud CDP"
    )

    class Meta:
        db_table = "presupuestoCDP"
        verbose_name = "Presupuesto CDP"
        verbose_name_plural = "Presupuestos CDP"
        ordering = ("fechaCDP",)

    def __str__(self):
        return f"CDP {self.numeroCdp} - {self.fechaCDP}"


class presupuestoSolicitudRP(models.Model):
    fechaSolicitud = models.DateField(verbose_name="Fecha")
    numContrato = models.PositiveIntegerField(unique=True, verbose_name="Número de Contrato")

    class Meta:
        db_table = "presupuestoSolicitudRP"
        verbose_name = "Solicitud RP"
        verbose_name_plural = "Solicitudes RP"
        ordering = ("fechaSolicitud",)

    def __str__(self):
        return f"Solicitud RP {self.numContrato} - {self.fechaSolicitud}"


class PresupuestoRP(models.Model):
    NumeroSolicitud = models.ForeignKey(
        presupuestoSolicitudRP,
        on_delete=models.PROTECT,
        related_name="rps",
        verbose_name="Número de Solicitud"
    )
    numeroRP = models.PositiveIntegerField(unique=True, verbose_name="Número de RP")
    fechaRP = models.DateField(verbose_name="Fecha de RP")
    valorRP = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor de RP")

    class Meta:
        db_table = "PresupuestoRP"
        verbose_name = "Presupuesto RP"
        verbose_name_plural = "Presupuestos RP"
        ordering = ("fechaRP",)

    def __str__(self):
        return f"RP {self.numeroRP} - ${self.valorRP}"






class ListaTipoContratacion(models.Model):
    codigo = models.CharField(
        max_length=2, primary_key=True, validators=[exact_len(2), only_upper_letters_digits], verbose_name="Código Contratación"
    )
    descripcion = models.CharField(max_length=600, verbose_name="Descripción")

    class Meta:
        db_table = "ListaTipoContratacion"
        verbose_name = "Contratación"
        verbose_name_plural = "Tipos de Contratación"


# Los modelos de Organigrama y Supervisores han sido movidos a la APP 'Organigrama'


# ============================
# Catálogos planeacion formatos institucionales
# ============================

class FormatosInstitucionales(models.Model):

    codigo = models.CharField(max_length=15)
    nombre = models.CharField(max_length=255)
    Version = models.CharField(max_length=2)
    FechaElaboracion = models.DateField()
    FechaActulizacion = models.DateField()
    AREA = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombre} - {self.codigo}"
# ============================
# Catálogos procesos institucionales estudio conveniencia
# ============================

class opsComponenteTecnico(models.Model):
    usuario=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,verbose_name="Usuario", null=True, blank=True)
    numeroComponente = models.PositiveIntegerField(unique=True, verbose_name="Número de Componente", null=True, blank=True)
    Area = models.ForeignKey(
        "A_00_Organigrama.Organigrama01", on_delete=models.PROTECT, related_name="+", verbose_name="Área", null=True, blank=True
    )
    Subgerencia = models.ForeignKey(
        "A_00_Organigrama.Organigrama02", on_delete=models.PROTECT, related_name="+", verbose_name="Subgerencia", null=True, blank=True
    )
    Dependencia = models.ForeignKey(
        "A_00_Organigrama.Organigrama03", on_delete=models.PROTECT, related_name="+", verbose_name="Dependencia", null=True, blank=True
    )
    objetoContractual = models.CharField(max_length=500, verbose_name="Objeto Contractual")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    claseServicio = models.ForeignKey("A_00_Organigrama.doc_tabHonorarios", on_delete=models.PROTECT, verbose_name="Clase de Servicio")
    VALORTOTALCONTRATO = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor Total del Contrato")

    class Meta:
        db_table = "juridica_opscomponentetecnico"
        verbose_name = "Componente Técnico OPS"
        verbose_name_plural = "Componentes Técnicos OPS"

    def save(self, *args, **kwargs):
        # Si es nuevo registro, forzamos el cálculo del consecutivo
        # para evitar usar un valor 'stale' que venga del formulario.
        if self.pk is None:
            last = opsComponenteTecnico.objects.aggregate(models.Max('numeroComponente'))['numeroComponente__max']
            self.numeroComponente = (last or 0) + 1
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        e = {}
        if self.Subgerencia_id and self.Area_id:
            if self.Subgerencia.Organigrama01_id != self.Area_id:
                e["Subgerencia"] = "La subgerencia no pertenece al área seleccionada."
        if self.Dependencia_id and self.Subgerencia_id:
            if self.Dependencia.Organigrama02_id != self.Subgerencia_id:
                e["Dependencia"] = "La dependencia no pertenece a la subgerencia seleccionada."
        if e:
            raise ValidationError(e)

    def __str__(self):
        return f"{self.numeroComponente} - {self.objetoContractual}"


class opsCondiciones(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    PAA_UNSPS = models.ForeignKey("BasesGenerales.PAA", on_delete=models.PROTECT, related_name="condiciones_segmento", verbose_name="CODIGO UNSPS PAA")
    FECHADEINICIO = models.DateField(verbose_name="Fecha de Inicio")
    FECHADETERMINACION = models.DateField(verbose_name="Fecha de Terminación")
    LUGARDEEJECUCION = models.CharField(max_length=600, verbose_name="Lugar de Ejecución")

    class Meta:
        db_table = "juridica_opscondiciones"
        verbose_name = "Condiciones OPS"
        verbose_name_plural = "Condiciones OPS"

    def __str__(self):
        return f"{self.NumeroComponente} - {self.UNSPS04Producto}"

class opsObligacionesGenerales(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    Obligacion = models.CharField(max_length=500, verbose_name="Obligaciones Generales")

    class Meta:
        db_table = "juridica_opsobligacionesgenerales"
        verbose_name = "Obligaciones Generales OPS"
        verbose_name_plural = "Obligaciones Generales OPS"

    def __str__(self):
        return f"{self.NumeroComponente} - {self.Obligacion}"

class opsObligacionesEspecificas(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    Obligacion = models.CharField(max_length=500, verbose_name="Obligaciones Especificas")

    class Meta:
        db_table = "juridica_opsobligacionesespecificas"
        verbose_name = "Obligaciones Específicas OPS"
        verbose_name_plural = "Obligaciones Específicas OPS"

    def __str__(self):
        return f"{self.NumeroComponente} - {self.Obligacion}"

# class opsSupervicion(models.Model):
#     NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
#     supervisor = models.ForeignKey(Supervisores, on_delete=models.PROTECT, verbose_name="Supervisor")
# 
#     class Meta:
#         db_table = "juridica_opssupervicion"
#         verbose_name = "Supervisión OPS"
#         verbose_name_plural = "Supervisiones OPS"
# 
#     def __str__(self):
#         return f"{self.NumeroComponente} - {self.supervisor}"

class ops3_1AspectosLegales(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    aspectolegal = models.CharField(max_length=500, verbose_name="Aspectos Legales")

    class Meta:
        db_table = "juridica_ops3_1aspectoslegales"
        verbose_name = "Aspectos Legales OPS"
        verbose_name_plural = "Aspectos Legales OPS"

    def __str__(self):
        return f"{self.NumeroComponente} - {self.aspectolegal}"

class ops3_2AspectosIdoneidad(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    idoneidad = models.CharField(max_length=500, verbose_name="Ideneidad")

    class Meta:
        db_table = "juridica_ops3_2aspectosidoneidad"
        verbose_name = "Aspectos Idoneidad OPS"
        verbose_name_plural = "Aspectos Idoneidad OPS"

    def __str__(self):
        return f"{self.NumeroComponente} - {self.idoneidad}"

class ops3_2AspectosExperiencia(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    experiencia = models.CharField(max_length=500, verbose_name="Experiencia")

    class Meta:
        db_table = "juridica_ops3_2aspectosexperiencia"
        verbose_name = "Aspectos Experiencia OPS"
        verbose_name_plural = "Aspectos Experiencia OPS"

    def __str__(self):
        return f"{self.NumeroComponente} - {self.experiencia}"

class ops33_ValorTotaldelContratoyformadepago(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    formadepago = models.CharField(max_length=500, verbose_name="Forma de Pago")

    class Meta:
        db_table = "juridica_ops33_valortotaldelcontratoyformadepago"
        verbose_name = "Valor y Forma Pago OPS"
        verbose_name_plural = "Valores y Formas Pago OPS"
    
    def __str__(self):
        return f"{self.NumeroComponente} - {self.formadepago}"

class ops4garantias(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    tiene_garantias = models.BooleanField(default=False, verbose_name="¿Tiene Garantías?")

    class Meta:
        db_table = "juridica_ops4garantias"
        verbose_name = "Garantías OPS"
        verbose_name_plural = "Garantías OPS"

    def __str__(self):
        return f"{self.NumeroComponente} - Garantías: {'Sí' if self.tiene_garantias else 'No'}"

class ops4garantiasDetalle(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    cabecera = models.ForeignKey(ops4garantias, on_delete=models.CASCADE, related_name="detalles")
    garantia = models.CharField(max_length=600, verbose_name="Garantía")

    class Meta:
        db_table = "juridica_ops4garantiasdetalle"
        verbose_name = "Detalle Garantía OPS"
        verbose_name_plural = "Detalles Garantía OPS"

    def __str__(self):
        return self.garantia

class ops4dependencia(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    Area = models.ForeignKey(
        "A_00_Organigrama.Organigrama01", on_delete=models.PROTECT, related_name="+", verbose_name="Área", null=True, blank=True
    )
    Subgerencia = models.ForeignKey(
        "A_00_Organigrama.Organigrama02", on_delete=models.PROTECT, related_name="+", verbose_name="Subgerencia", null=True, blank=True
    )
    Dependencia = models.ForeignKey(
        "A_00_Organigrama.Organigrama03", on_delete=models.PROTECT, related_name="+", verbose_name="Dependencia", null=True, blank=True
    )
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro") 

    class Meta:
        db_table = "juridica_ops4dependencia"
        verbose_name = "Dependencia OPS"
        verbose_name_plural = "Dependencias OPS"


    def clean(self):
        super().clean()
        e = {}
        if self.Subgerencia_id and self.Area_id:
            if self.Subgerencia.Organigrama01_id != self.Area_id:
                e["Subgerencia"] = "La subgerencia no pertenece al área seleccionada."
        if self.Dependencia_id and self.Subgerencia_id:
            if self.Dependencia.Organigrama02_id != self.Subgerencia_id:
                e["Dependencia"] = "La dependencia no pertenece a la subgerencia seleccionada."
        if e:
            raise ValidationError(e)

    def __str__(self):
        return f"{self.NumeroComponente} - {self.Area} - {self.Subgerencia} - {self.Dependencia}"
 

class ops4viabilidad(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    Subgerencia = models.ForeignKey("A_00_Organigrama.Organigrama02", on_delete=models.PROTECT, verbose_name="Seleccione Subgerencia (Administrativa o Salud)")

    class Meta:
        db_table = "juridica_ops4viabilidad"
        verbose_name = "Viabilidad OPS"
        verbose_name_plural = "Viabilidades OPS"

    def __str__(self):
        return f"{self.NumeroComponente} - {self.Subgerencia}"


class ops4Disponibilidad(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    NumerodeCdp = models.ForeignKey("A_00_Organigrama.Organigrama02", on_delete=models.PROTECT, verbose_name="Seleccione Subgerencia (Administrativa o Salud)")

    class Meta:
        db_table = "juridica_ops4disponibilidad"
        verbose_name = "Disponibilidad OPS"
        verbose_name_plural = "Disponibilidades OPS"

    def __str__(self):
        return f"{self.NumeroComponente} - {self.Subgerencia}"


class ops4aceptaGerencia(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    aceptagerencia = models.BooleanField(default=False, verbose_name="¿Acepta Gerencia?")

    class Meta:
        db_table = "juridica_ops4aceptagerencia"
        verbose_name = "Aceptación Gerencia OPS"
        verbose_name_plural = "Aceptaciones Gerencia OPS"

    def __str__(self):
        return f"{self.NumeroComponente} - {'Acepta' if self.aceptagerencia else 'No Acepta'}"


# ============================
# Catálogos Financiera PAA
# ============================

class PAA(models.Model):
    item=models.PositiveIntegerField(verbose_name="Ítem")
    UNSPS01Segmento=models.ForeignKey("BasesGenerales.UNSPS01Segmento",on_delete=models.PROTECT,related_name="paa_segmento",verbose_name="Segmento")
    UNSPS02Familia=models.ForeignKey("BasesGenerales.UNSPS02Familia",on_delete=models.PROTECT,related_name="paa_familia",verbose_name="Familia")
    UNSPS03Clase=models.ForeignKey("BasesGenerales.UNSPS03Clase",on_delete=models.PROTECT,related_name="paa_clase",verbose_name="Clase")
    UNSPS04Producto=models.ForeignKey("BasesGenerales.UNSPS04Producto",on_delete=models.PROTECT,related_name="paa_producto",verbose_name="Producto")
    descripcion=models.CharField(max_length=500,verbose_name="Descripción")
    valor_subido=models.DecimalField(max_digits=18,decimal_places=2,verbose_name="Valor subido")
    fecha_estimada_ofertas=models.DateField(verbose_name="Fecha estimada de presentación de ofertas")
    duracion_contrato_numero=models.PositiveIntegerField(verbose_name="Duración del contrato (número)")
    DURACION_UNIDAD_CHOICES=[("DIAS","Días"),("MESES","Meses"),("ANIOS","Años")]
    duracion_contrato_unidad=models.CharField(max_length=5,choices=DURACION_UNIDAD_CHOICES,verbose_name="Unidad duración")
    modalidad_seleccion=models.CharField(max_length=200,verbose_name="Modalidad de selección")
    fuente_recursos=models.CharField(max_length=200,verbose_name="Fuente de los recursos")
    valor_total_estimado=models.DecimalField(max_digits=18,decimal_places=2,verbose_name="Valor total estimado")
    valor_estimado_vigencia_actual=models.DecimalField(max_digits=18,decimal_places=2,verbose_name="Valor estimado vigencia actual")
    requiere_vigencias_futuras=models.BooleanField(default=False,verbose_name="¿Requiere vigencias futuras?")
    estado_vigencias_futuras=models.CharField(max_length=200,null=True,blank=True,verbose_name="Estado vigencias futuras")
    unidad_contratacion=models.CharField(max_length=200,verbose_name="Unidad de contratación")
    ubicacion=models.CharField(max_length=600,verbose_name="Ubicación")
    nombre_responsable=models.CharField(max_length=200,verbose_name="Responsable")
    telefono_responsable=models.CharField(max_length=50,verbose_name="Teléfono responsable")
    correo_responsable=models.EmailField(verbose_name="Correo responsable")
    debe_cumplir_invertir=models.BooleanField(default=False,verbose_name="¿Debe cumplir con invertir?")
    incluye_bienes_servicios_no_alimentos=models.BooleanField(default=False,verbose_name="¿Incluye bienes/servicios no alimentos?")
    Dependencia_1=models.ForeignKey("A_00_Organigrama.Organigrama01",on_delete=models.PROTECT,related_name="paa_dep1",null=True,blank=True,verbose_name="Dependencia 1")
    Dependencia_2=models.ForeignKey("A_00_Organigrama.Organigrama02",on_delete=models.PROTECT,related_name="paa_dep2",null=True,blank=True,verbose_name="Dependencia 2")
    Dependencia_3=models.ForeignKey("A_00_Organigrama.Organigrama03",on_delete=models.PROTECT,related_name="paa_dep3",null=True,blank=True,verbose_name="Dependencia 3")
    Dependencia_4=models.ForeignKey("A_00_Organigrama.Organigrama04",on_delete=models.PROTECT,related_name="paa_dep4",null=True,blank=True,verbose_name="Dependencia 4")
    Dependencia_5=models.ForeignKey("A_00_Organigrama.Organigrama05",on_delete=models.PROTECT,related_name="paa_dep5",null=True,blank=True,verbose_name="Dependencia 5")
    Dependencia_6=models.ForeignKey("A_00_Organigrama.Organigrama06",on_delete=models.PROTECT,related_name="paa_dep6",null=True,blank=True,verbose_name="Dependencia 6")
    vigencia=models.PositiveIntegerField(verbose_name="Año vigencia")
    class Meta:
        db_table="PAA"
        verbose_name="Plan Anual de Adquisiciones"
        verbose_name_plural="Plan Anual de Adquisiciones"
        ordering=("vigencia","item")
    def __str__(self): return f"PAA {self.vigencia} - Item {self.item}"



# ============================
# Catálogos Recurso Humano OPS
# ============================

class opsInexistencia(models.Model):
    NumeroComponente=models.ForeignKey(opsComponenteTecnico,on_delete=models.PROTECT,verbose_name="Número de Componente")
    FECHADEELABORACION=models.DateField(verbose_name="Fecha de Elaboración")
    # AprobadoPor=models.ForeignKey("empresa.Reg05Empresa_Empleados",on_delete=models.PROTECT,verbose_name="Aprobado por")

    class Meta:
        db_table = "juridica_opsinexistencia"
        verbose_name = "Inexistencia OPS"
        verbose_name_plural = "Inexistencias OPS"

    def __str__(self): return f"Inexistencia {self.NumeroComponente}"


# ============================
# Catálogos Procesos OPS 
# ============================

class opsAdjudicacion(models.Model):
    NumeroComponente=models.ForeignKey(opsComponenteTecnico,on_delete=models.PROTECT,verbose_name="Número de Componente")
    FECHADEAdjudicacion=models.DateField(verbose_name="Fecha de Adjudicación")
    Adjudicado=models.ForeignKey(DocumentoDeIdentidad,on_delete=models.PROTECT,verbose_name="Adjudicado a")

    class Meta:
        db_table = "juridica_opsadjudicacion"
        verbose_name = "Adjudicación OPS"
        verbose_name_plural = "Adjudicaciones OPS"

    def __str__(self): return f"Adjudicación {self.NumeroComponente}"

class opsDocumentosRequeridos(models.Model):
    NumeroComponente=models.ForeignKey(opsComponenteTecnico,on_delete=models.PROTECT,verbose_name="Número de Componente")
    fecha_recepcion_documentos=models.DateField(verbose_name="Fecha")
    PROPUESTA=models.BooleanField(default=False,verbose_name="Propuesta")
    DOC_IDENTIFICACION=models.BooleanField(default=False,verbose_name="Fotocopia Documento de Identificación")
    SARLAFT=models.BooleanField(default=False,verbose_name="Formulario Único SARLAFT")
    CAMARA_COMERCIO=models.BooleanField(default=False,verbose_name="Cámara de Comercio (2 meses)")
    ANTECEDENTES_DISC=models.BooleanField(default=False,verbose_name="Cert. Antecedentes Disciplinarios")
    ANTECEDENTES_FISC=models.BooleanField(default=False,verbose_name="Cert. Antecedentes Fiscales")
    ANTECEDENTES_JUD=models.BooleanField(default=False,verbose_name="Cert. Antecedentes Judiciales")
    RNMC=models.BooleanField(default=False,verbose_name="Cert. RNMC")
    REDAM=models.BooleanField(default=False,verbose_name="Certificado REDAM")
    LIBRETA_MILITAR=models.BooleanField(default=False,verbose_name="Copia Libreta Militar")
    INHABILIDADES=models.BooleanField(default=False,verbose_name="Certificado Inhabilidades")
    RUT=models.BooleanField(default=False,verbose_name="RUT")
    CUENTA_BANCARIA=models.BooleanField(default=False,verbose_name="Certificado Cuenta Bancaria")
    SIGEP=models.BooleanField(default=False,verbose_name="Hoja de Vida SIGEP / Certificaciones")
    RETHUS=models.BooleanField(default=False,verbose_name="RETHUS")
    SOPORTE_VITAL=models.BooleanField(default=False,verbose_name="Soporte Vital")
    INDUCCION_HSEQ=models.BooleanField(default=False,verbose_name="Inducción HSEQ")
    EXAMEN_MEDICO=models.BooleanField(default=False,verbose_name="Examen Médico Vigente")
    AFILIACION_SALUD=models.BooleanField(default=False,verbose_name="Afiliación Salud")
    AFILIACION_PENSION=models.BooleanField(default=False,verbose_name="Afiliación Pensión")
    AFILIACION_RIESGOS=models.BooleanField(default=False,verbose_name="Afiliación Riesgos")
    PAZ_Y_SALVO_SS=models.BooleanField(default=False,verbose_name="Paz y Salvo Seguridad Social")
    FORM_BIENES_RENTA=models.BooleanField(default=False,verbose_name="Formulario Bienes y Renta")
    ANEXO_TECNICO=models.BooleanField(default=False,verbose_name="Anexo Técnico FRJUR-016")
    CONFIDENCIALIDAD=models.BooleanField(default=False,verbose_name="Acuerdo de Confidencialidad FRSGI-001")
    POLIZA_RCivil=models.BooleanField(default=False,verbose_name="Póliza Resp. Civil")

    class Meta:
        db_table = "juridica_opsdocumentosrequeridos"
        verbose_name = "Documentos Requeridos OPS"
        verbose_name_plural = "Documentos Requeridos OPS"

    def __str__(self): return f"Documentos requeridos {self.NumeroComponente}"


# ============================
# Catálogos Juridica Tipos Contrato
# ============================

class opsTiposdeContrato(models.Model):
    codigo = models.CharField(max_length=20, verbose_name="Código")
    tipo_de_contrato = models.CharField(max_length=200, verbose_name="Tipo de Contrato")

    class Meta:
        db_table = "opsTiposdeContrato"
        verbose_name = "Tipo de Contrato"
        verbose_name_plural = "Tipos de Contrato"
        ordering = ("codigo",)

    def __str__(self):
        return f"{self.codigo} - {self.tipo_de_contrato}"

# ============================
# Catálogos Juridica Contratos
# ============================

class opsContrato(models.Model):
    NumeroComponente = models.ForeignKey(opsComponenteTecnico, on_delete=models.PROTECT, verbose_name="Número de Componente")
    tipo_de_contrato = models.ForeignKey(opsTiposdeContrato, on_delete=models.PROTECT, verbose_name="Tipo de Contrato")
    numero_de_contrato = models.PositiveIntegerField(unique=True, verbose_name="Número de Contrato")
    fecha_de_contrato = models.DateField(verbose_name="Fecha de Adjudicación")

    class Meta:
        db_table = "opsContrato"
        verbose_name = "Contrato OPS"
        verbose_name_plural = "Contratos OPS"
        ordering = ("NumeroComponente", "numero_de_contrato")

    def __str__(self):
        return f"Contrato {self.numero_de_contrato} - {self.NumeroComponente}"

# ============================
# Catálogos Juridica Documentos
# ============================

class DocumentoTipoAd(models.Model):
    nombre=models.CharField(max_length=200,unique=True,verbose_name="Tipo de Documento")
    def __str__(self): return self.nombre

class opsDocumentosAdjudicados(models.Model):
    NumeroComponente=models.ForeignKey(opsComponenteTecnico,on_delete=models.PROTECT,verbose_name="Número de Componente")
    FECHADERecepcionDocumentos=models.DateField(verbose_name="Fecha de Recepción de Documentos")

    class Meta:
        db_table = "juridica_opsdocumentosadjudicados"
        verbose_name = "Documentos Adjudicados OPS"
        verbose_name_plural = "Documentos Adjudicados OPS"

    def __str__(self): return f"Documentos del componente {self.NumeroComponente}"

class DocumentoDetalle(models.Model):
    adjudicacion=models.ForeignKey(opsDocumentosAdjudicados,on_delete=models.CASCADE,related_name="documentos",verbose_name="Adjudicación")
    tipo=models.ForeignKey(DocumentoTipoAd,on_delete=models.PROTECT,verbose_name="Tipo de Documento")
    aplica=models.BooleanField(default=False,verbose_name="¿Aplica?")
    fecha_generacion=models.DateField(null=True,blank=True,verbose_name="Fecha de Generación")
    fecha_vigencia=models.DateField(null=True,blank=True,verbose_name="Fecha de Vigencia")
    empresa_emisora=models.CharField(max_length=200,null=True,blank=True,verbose_name="Empresa Emisora")
    archivo_pdf=models.FileField(upload_to="documentos_adjudicados/",null=True,blank=True,verbose_name="Archivo PDF")
    def __str__(self): return f"{self.tipo} - {self.adjudicacion.NumeroComponente}"

# ============================
# Catálogos ServicioSalus Controles 
# ============================

class ControlesMaternos(models.Model):
    paciente=models.ForeignKey(DocumentoDeIdentidad,on_delete=models.PROTECT,verbose_name="Paciente")
    hora_lectura=models.DateTimeField(auto_now_add=True,verbose_name="Hora de Lectura")
    tension_arterial=models.CharField(max_length=20,verbose_name="Tensión Arterial (mmHg)")
    frec_cardiaca=models.PositiveIntegerField(verbose_name="Frecuencia Cardiaca (lpm)")
    frec_respiratoria=models.PositiveIntegerField(verbose_name="Frecuencia Respiratoria (rpm)")
    temperatura=models.DecimalField(max_digits=4,decimal_places=1,verbose_name="Temperatura (°C)")
    frecuencia=models.CharField(max_length=50,verbose_name="Frecuencia")

class MaternosCONTRACCIONESUTERINAS(models.Model):
    paciente=models.ForeignKey(DocumentoDeIdentidad,on_delete=models.PROTECT,verbose_name="Paciente")
    hora_lectura=models.DateTimeField(auto_now_add=True,verbose_name="Hora de Lectura")
    cu_frecuencia=models.CharField(max_length=50,verbose_name="Frecuencia",blank=True,null=True)
    cu_duracion=models.CharField(max_length=50,verbose_name="Duración",blank=True,null=True)
    cu_intensidad=models.CharField(max_length=50,verbose_name="Intensidad",blank=True,null=True)

class MaternosCONTROLFETAL(models.Model):
    paciente=models.ForeignKey(DocumentoDeIdentidad,on_delete=models.PROTECT,verbose_name="Paciente")
    hora_lectura=models.DateTimeField(auto_now_add=True,verbose_name="Hora de Lectura")
    fetal_frecuencia_cardiaca=models.PositiveIntegerField(verbose_name="Frecuencia Cardiaca Fetal",blank=True,null=True)
    fetal_movimientos=models.CharField(max_length=200,verbose_name="Movimientos Fetales",blank=True,null=True)
    fetal_presentacion=models.CharField(max_length=100,verbose_name="Presentación Fetal",blank=True,null=True)

class MaternosTACTOVAGINAL(models.Model):
    paciente=models.ForeignKey(DocumentoDeIdentidad,on_delete=models.PROTECT,verbose_name="Paciente")
    hora_lectura=models.DateTimeField(auto_now_add=True,verbose_name="Hora de Lectura")
    tv_membranas_integras=models.BooleanField(default=False,verbose_name="Membranas Íntegras")
    tv_membranas_rotas=models.BooleanField(default=False,verbose_name="Membranas Rotas")
    tv_liquido_amniotico=models.CharField(max_length=100,verbose_name="Líquido Amniótico",blank=True,null=True)
    tv_hora_ruptura=models.TimeField(verbose_name="Hora de Ruptura",blank=True,null=True)
    tv_dilatacion=models.CharField(max_length=50,verbose_name="Dilatación (cm)",blank=True,null=True)
    tv_borramiento=models.CharField(max_length=50,verbose_name="Borramiento (%)",blank=True,null=True)

class MaternosMONITOREOFETAL(models.Model):
    paciente=models.ForeignKey(DocumentoDeIdentidad,on_delete=models.PROTECT,verbose_name="Paciente")
    hora_lectura=models.DateTimeField(auto_now_add=True,verbose_name="Hora de Lectura")
    mf_hora=models.TimeField(verbose_name="Hora Monitoreo",blank=True,null=True)
    mf_categoria=models.CharField(max_length=50,verbose_name="Categoría Monitoreo Fetal",blank=True,null=True)

class MaternosOxitocina(models.Model):
    paciente=models.ForeignKey(DocumentoDeIdentidad,on_delete=models.PROTECT,verbose_name="Paciente")
    hora_lectura=models.DateTimeField(auto_now_add=True,verbose_name="Hora de Lectura")
    ox_miliunidades=models.CharField(max_length=50,verbose_name="Oxitocina (mU/min)",blank=True,null=True)
    ox_cc_hora=models.CharField(max_length=50,verbose_name="Oxitocina (cc/h)",blank=True,null=True)


class ingresoHospital(models.Model):
    usuario=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,verbose_name="Usuario", null=True, blank=True)
    NumeroIngreso=models.IntegerField(unique=True,verbose_name="Número de Ingreso") # debe ser un Numero incremental
    cedulaPaciente=models.ForeignKey(DocumentoDeIdentidad,on_delete=models.PROTECT,verbose_name="Paciente")
    Area = models.ForeignKey(
        "A_00_Organigrama.Organigrama01", on_delete=models.PROTECT, related_name="+", verbose_name="Área", null=True, blank=True
    )
    Subgerencia = models.ForeignKey(
        "A_00_Organigrama.Organigrama02", on_delete=models.PROTECT, related_name="+", verbose_name="Subgerencia", null=True, blank=True
    )
    Dependencia = models.ForeignKey(
        "A_00_Organigrama.Organigrama03", on_delete=models.PROTECT, related_name="+", verbose_name="Dependencia", null=True, blank=True
    )

