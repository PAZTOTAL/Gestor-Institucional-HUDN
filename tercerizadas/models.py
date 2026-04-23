from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils import timezone


only_digits = RegexValidator(r'^\d+$', 'Solo se permiten números.')


# ─────────────────────────────────────────────
# 1. EMPRESA TERCERIZADA
# ─────────────────────────────────────────────
class EmpresaTercerizada(models.Model):
    nit = models.CharField('NIT', max_length=20, unique=True)
    razon_social = models.CharField('Razón Social', max_length=200)
    representante_legal = models.CharField('Representante Legal', max_length=200, blank=True, null=True)
    tipo_servicio = models.CharField('Tipo de Servicio', max_length=200,
                                     help_text='Ej: Aseo, Vigilancia, Alimentación, Mantenimiento')
    telefono = models.CharField('Teléfono', max_length=20, blank=True, null=True)
    email = models.EmailField('Correo', blank=True, null=True)
    direccion = models.CharField('Dirección', max_length=300, blank=True, null=True)
    activa = models.BooleanField('Activa', default=True)
    observaciones = models.TextField('Observaciones', blank=True, null=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='empresas_registradas', verbose_name='Registrado por'
    )
    fecha_registro = models.DateTimeField('Fecha de Registro', auto_now_add=True)

    class Meta:
        db_table = 'terc_empresa_tercerizada'
        verbose_name = 'Empresa Tercerizada'
        verbose_name_plural = 'Empresas Tercerizadas'
        ordering = ['razon_social']

    def __str__(self):
        return f"{self.nit} — {self.razon_social}"


# ─────────────────────────────────────────────
# 2. CONTRATO TERCERIZADO
# ─────────────────────────────────────────────
ESTADO_CONTRATO = [
    ('ACTIVO', 'Activo'),
    ('VENCIDO', 'Vencido'),
    ('LIQUIDADO', 'Liquidado'),
]

class ContratoTercerizado(models.Model):
    empresa = models.ForeignKey(
        EmpresaTercerizada, on_delete=models.PROTECT,
        related_name='contratos', verbose_name='Empresa'
    )
    numero_contrato = models.CharField('N° Contrato', max_length=50, unique=True)
    objeto_contrato = models.TextField('Objeto del Contrato')
    fecha_inicio = models.DateField('Fecha de Inicio')
    fecha_fin = models.DateField('Fecha de Fin', blank=True, null=True)
    valor_contrato = models.DecimalField('Valor ($)', max_digits=18, decimal_places=2, blank=True, null=True)
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CONTRATO, default='ACTIVO')
    documento_contrato = models.FileField(
        'PDF del Contrato', upload_to='tercerizadas/contratos/', blank=True, null=True
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='contratos_registrados', verbose_name='Registrado por'
    )
    fecha_registro = models.DateTimeField('Fecha de Registro', auto_now_add=True)

    class Meta:
        db_table = 'terc_contrato_tercerizado'
        verbose_name = 'Contrato Tercerizado'
        verbose_name_plural = 'Contratos Tercerizados'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.numero_contrato} — {self.empresa.razon_social}"

    @property
    def esta_vigente(self):
        if self.fecha_fin is None:
            return self.estado == 'ACTIVO'
        return self.estado == 'ACTIVO' and self.fecha_fin >= timezone.now().date()


# ─────────────────────────────────────────────
# 3. ACTIVIDAD TERCERIZADO
# ─────────────────────────────────────────────
class ActividadTercerizado(models.Model):
    nombre = models.CharField('Actividad', max_length=200, unique=True)
    descripcion = models.TextField('Descripción', blank=True, null=True)
    activa = models.BooleanField('Activa', default=True)

    class Meta:
        db_table = 'terc_actividad_tercerizado'
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


# ─────────────────────────────────────────────
# 4. SERVIDOR TERCERIZADO  (tabla principal)
# ─────────────────────────────────────────────
class ServidorTercerizado(models.Model):
    # — Identificación —
    tipo_documento = models.ForeignKey(
        'BasesGenerales.ListaTipoDocumento', on_delete=models.PROTECT,
        verbose_name='Tipo de Documento'
    )
    numero_documento = models.CharField(
        'Número de Documento', max_length=20, unique=True,
        validators=[only_digits]
    )

    # — Verificación contra GENTERCER (Dinámica) —
    en_dinamica = models.BooleanField('Registrado en Dinámica', default=False)
    fecha_verificacion_dinamica = models.DateTimeField(
        'Fecha de Verificación', blank=True, null=True
    )

    # — Datos personales —
    primer_nombre = models.CharField('Primer Nombre', max_length=100)
    segundo_nombre = models.CharField('Segundo Nombre', max_length=100, blank=True, null=True)
    primer_apellido = models.CharField('Primer Apellido', max_length=100)
    segundo_apellido = models.CharField('Segundo Apellido', max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField('Fecha de Nacimiento', blank=True, null=True)

    grupo_sanguineo = models.ForeignKey(
        'BasesGenerales.ListaTipoGrupoSanguineo', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Grupo Sanguíneo'
    )
    sexo = models.ForeignKey(
        'BasesGenerales.ListaTipoSexo', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Sexo'
    )

    # — Lugar de nacimiento —
    pais_nacimiento = models.ForeignKey(
        'BasesGenerales.Geo01Pais', on_delete=models.PROTECT,
        related_name='servidores_nacidos_pais',
        verbose_name='País de Nacimiento', blank=True, null=True
    )
    departamento_nacimiento = models.ForeignKey(
        'BasesGenerales.Geo02Departamento', on_delete=models.PROTECT,
        related_name='servidores_nacidos_dep',
        verbose_name='Departamento de Nacimiento', blank=True, null=True
    )
    municipio_nacimiento = models.ForeignKey(
        'BasesGenerales.Geo03Municipio', on_delete=models.PROTECT,
        related_name='servidores_nacidos_mun',
        verbose_name='Municipio de Nacimiento', blank=True, null=True
    )

    # — Residencia —
    direccion_residencia = models.CharField('Dirección de Residencia', max_length=300, blank=True, null=True)
    municipio_residencia = models.ForeignKey(
        'BasesGenerales.Geo03Municipio', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='servidores_residencia',
        verbose_name='Municipio de Residencia'
    )

    # — Documentos —
    foto = models.ImageField('Foto', upload_to='tercerizadas/fotos/', blank=True, null=True)
    documento_pdf = models.FileField(
        'Documento de Identidad (PDF)', upload_to='tercerizadas/documentos/', blank=True, null=True
    )

    # — Empresa y contrato —
    empresa = models.ForeignKey(
        EmpresaTercerizada, on_delete=models.PROTECT,
        related_name='servidores', verbose_name='Empresa'
    )
    contrato = models.ForeignKey(
        ContratoTercerizado, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='servidores', verbose_name='Contrato'
    )

    # — Estado —
    activo_hospital = models.BooleanField('Activo en el Hospital', default=True)
    fecha_ingreso = models.DateField('Fecha de Ingreso')
    fecha_retiro = models.DateField('Fecha de Retiro', blank=True, null=True)

    # — Contacto —
    telefono = models.CharField('Teléfono', max_length=20, blank=True, null=True)
    email = models.EmailField('Correo', blank=True, null=True)

    # — Auditoría —
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='servidores_registrados', verbose_name='Registrado por'
    )
    fecha_registro = models.DateTimeField('Fecha de Registro', auto_now_add=True)
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='servidores_modificados', verbose_name='Modificado por'
    )
    fecha_modificacion = models.DateTimeField('Última Modificación', auto_now=True)

    class Meta:
        db_table = 'terc_servidor_tercerizado'
        verbose_name = 'Servidor Tercerizado'
        verbose_name_plural = 'Servidores Tercerizados'
        ordering = ['primer_apellido', 'primer_nombre']

    def __str__(self):
        return f"{self.numero_documento} — {self.primer_nombre} {self.primer_apellido}"

    @property
    def nombre_completo(self):
        partes = [self.primer_nombre, self.segundo_nombre or '',
                  self.primer_apellido, self.segundo_apellido or '']
        return ' '.join(p for p in partes if p).strip()


# ─────────────────────────────────────────────
# 5. ASIGNACIÓN ÁREA (usa Organigrama existente)
# ─────────────────────────────────────────────
class AsignacionOrganigrama(models.Model):
    servidor = models.ForeignKey(
        ServidorTercerizado, on_delete=models.CASCADE,
        related_name='asignaciones', verbose_name='Servidor'
    )

    # Referencia jerárquica al organigrama (niveles 1–6)
    organigrama_nivel1 = models.ForeignKey(
        'A_00_Organigrama.Organigrama01', on_delete=models.PROTECT,
        verbose_name='Nivel 1 (Dirección)'
    )
    organigrama_nivel2 = models.ForeignKey(
        'A_00_Organigrama.Organigrama02', on_delete=models.PROTECT,
        verbose_name='Nivel 2 (División)'
    )
    organigrama_nivel3 = models.ForeignKey(
        'A_00_Organigrama.Organigrama03', on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Nivel 3 (Servicio)'
    )
    organigrama_nivel4 = models.ForeignKey(
        'A_00_Organigrama.Organigrama04', on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Nivel 4 (Área)'
    )
    organigrama_nivel5 = models.ForeignKey(
        'A_00_Organigrama.Organigrama05', on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Nivel 5 (Subárea)'
    )
    organigrama_nivel6 = models.ForeignKey(
        'A_00_Organigrama.Organigrama06', on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Nivel 6 (Unidad)'
    )

    actividad = models.ForeignKey(
        ActividadTercerizado, on_delete=models.PROTECT,
        verbose_name='Actividad que realiza'
    )
    fecha_inicio = models.DateField('Desde')
    fecha_fin = models.DateField('Hasta', blank=True, null=True)
    activa = models.BooleanField('Asignación Activa', default=True)
    verificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='asignaciones_verificadas', verbose_name='Verificado por'
    )
    observaciones = models.TextField('Observaciones', blank=True, null=True)

    class Meta:
        db_table = 'terc_asignacion_organigrama'
        verbose_name = 'Asignación de Área'
        verbose_name_plural = 'Asignaciones de Área'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.servidor} → {self.organigrama_nivel2.descripcion}"

    @property
    def area_display(self):
        """Retorna la descripción del nivel más específico asignado."""
        for nivel in [self.organigrama_nivel6, self.organigrama_nivel5,
                      self.organigrama_nivel4, self.organigrama_nivel3,
                      self.organigrama_nivel2, self.organigrama_nivel1]:
            if nivel:
                return nivel.descripcion
        return '—'


# ─────────────────────────────────────────────
# 6. AFILIACIÓN SEGURIDAD SOCIAL
# ─────────────────────────────────────────────
TIPO_AFILIACION = [
    ('ARL', 'ARL — Administradora de Riesgos Laborales'),
    ('EPS', 'EPS — Entidad Promotora de Salud'),
    ('IPS', 'IPS — Institución Prestadora de Servicios'),
    ('AFP', 'AFP — Fondo de Pensiones'),
]

class AfiliacionSeguridad(models.Model):
    servidor = models.ForeignKey(
        ServidorTercerizado, on_delete=models.CASCADE,
        related_name='afiliaciones', verbose_name='Servidor'
    )
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_AFILIACION)
    nombre_entidad = models.CharField('Entidad', max_length=200)
    numero_afiliacion = models.CharField('N° de Afiliación', max_length=50, blank=True, null=True)
    fecha_afiliacion = models.DateField('Fecha de Afiliación', blank=True, null=True)
    fecha_vencimiento = models.DateField('Fecha de Vencimiento', blank=True, null=True)
    vigente = models.BooleanField('Vigente', default=True)
    documento_soporte = models.FileField(
        'Soporte (PDF)', upload_to='tercerizadas/afiliaciones/', blank=True, null=True
    )

    class Meta:
        db_table = 'terc_afiliacion_seguridad'
        verbose_name = 'Afiliación de Seguridad Social'
        verbose_name_plural = 'Afiliaciones de Seguridad Social'
        ordering = ['tipo', 'nombre_entidad']

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.nombre_entidad} ({self.servidor})"
