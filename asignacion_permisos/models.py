from django.db import models


class ListaBlancaAdmin(models.Model):
    """Usuarios con acceso administrativo al módulo APC (pueden editar el formulario)."""
    usunombre = models.CharField(max_length=100, unique=True)
    usuemail = models.CharField(max_length=150)
    nombre = models.CharField(max_length=150)
    avatar = models.CharField(max_length=4, default='US')
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'apc_lista_blanca_admin'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.usunombre})"


class EncabezadoConfig(models.Model):
    """Singleton: configuración del encabezado del formato imprimible."""
    titulo = models.CharField(max_length=200, default='ASIGNACIÓN DE PERMISOS Y CLAVES')
    codigo = models.CharField(max_length=50, default='FRSGI-002')
    version = models.CharField(max_length=10, default='06')
    fecha_elaboracion = models.CharField(max_length=100, default='05 DE JUNIO DE 2014')
    fecha_actualizacion = models.CharField(max_length=100, default='22 DE SEPTIEMBRE DE 2023')
    hoja = models.CharField(max_length=20, default='1 DE 1')
    texto_mensaje = models.TextField(
        default=(
            'Declaro de manera libre, expresa, inequívoca e informada que, conozco el '
            'ACUERDO INDIVIDUAL DE CONFIDENCIALIDAD DE LA INFORMACIÓN FRSG1-001 y que '
            'mediante la firma de este documento confirmo y acepto mi responsabilidad '
            'para los fines pertinentes.'
        )
    )

    class Meta:
        db_table = 'apc_encabezado_config'

    def __str__(self):
        return self.titulo


class CampoConfig(models.Model):
    """Etiquetas editables de los campos fijos del formulario (secciones 1, 2 y 4)."""
    seccion = models.SmallIntegerField()
    campo_clave = models.CharField(max_length=100)
    etiqueta = models.CharField(max_length=200)
    activo = models.BooleanField(default=True)
    orden = models.SmallIntegerField(default=1)

    class Meta:
        db_table = 'apc_campos_config'
        unique_together = [('seccion', 'campo_clave')]
        ordering = ['seccion', 'orden']

    def __str__(self):
        return f"Sección {self.seccion} · {self.campo_clave}"


class SeccionConfig(models.Model):
    """Secciones del formulario — título editable por admin."""
    numero = models.SmallIntegerField()
    titulo = models.CharField(max_length=200)
    activa = models.BooleanField(default=True)
    orden = models.SmallIntegerField(default=1)

    class Meta:
        db_table = 'apc_secciones_config'
        ordering = ['orden']

    def __str__(self):
        return f"Sección {self.numero}: {self.titulo}"


class PermisoAccesoConfig(models.Model):
    """Lista de permisos y accesos disponibles para marcar en el formulario (Sección 3)."""
    clave = models.CharField(max_length=80, unique=True)
    etiqueta = models.CharField(max_length=120)
    activo = models.BooleanField(default=True)
    orden = models.SmallIntegerField(default=1)
    # Si requiere_contratista=False significa que NO está disponible para tercerizados
    disponible_tercerizado = models.BooleanField(default=True)

    class Meta:
        db_table = 'apc_permisos_acceso_config'
        ordering = ['orden']

    def __str__(self):
        return self.etiqueta


class CoordinadorArea(models.Model):
    """Coordinador de área para el flujo de firmas — se asocia al área de servicios elegida."""
    area_nombre = models.CharField(max_length=150, unique=True)
    nombre_coordinador = models.CharField(max_length=150)
    email_coordinador = models.CharField(max_length=150)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'apc_coordinadores_area'
        ordering = ['area_nombre']

    def __str__(self):
        return f"{self.area_nombre} → {self.nombre_coordinador}"


class FirmantesFijos(models.Model):
    """Firmantes fijos del proceso: Talento Humano y Gestión de Información."""
    ROL_CHOICES = [
        ('coord_talento_humano', 'Coordinador Talento Humano'),
        ('coord_gestion_info', 'Coordinador Gestión de Información'),
    ]
    rol = models.CharField(max_length=30, choices=ROL_CHOICES, unique=True)
    nombre = models.CharField(max_length=150)
    email = models.CharField(max_length=150)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'apc_firmantes_fijos'

    def __str__(self):
        return f"{self.get_rol_display()}: {self.nombre}"


class DestinatarioRol(models.Model):
    """Usuarios finales que reciben el formato completo cuando el permiso X fue solicitado."""
    permiso_clave = models.CharField(max_length=80)
    nombre = models.CharField(max_length=150)
    email = models.CharField(max_length=150)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'apc_destinatarios_rol'
        ordering = ['permiso_clave', 'nombre']

    def __str__(self):
        return f"{self.permiso_clave} → {self.nombre}"


class SolicitudAPC(models.Model):
    """Solicitud principal de Asignación de Permisos y Claves."""
    ESTADO_CHOICES = [
        ('EN_TRAMITE', 'En Trámite'),
        ('COMPLETADO', 'Completado'),
        ('RECHAZADO', 'Rechazado'),
    ]
    TIPO_VINCULACION_CHOICES = [
        ('planta_permanente', 'Planta Permanente'),
        ('planta_temporal', 'Planta Temporal'),
        ('ops', 'OPS'),
        ('tercerizado', 'Tercerizado(a)/Contratista'),
    ]

    # ── Sección 1: Datos personales ──────────────────────────────────────────
    fecha_diligenciamiento = models.DateField()
    num_identificacion = models.CharField(max_length=20)
    lugar_expedicion = models.CharField(max_length=100)
    nombres_apellidos = models.CharField(max_length=200)
    direccion_residencia = models.CharField(max_length=200)
    tel_celular = models.CharField(max_length=20)
    correo_personal = models.CharField(max_length=150)
    tel_fijo = models.CharField(max_length=20, blank=True, default='')

    # ── Sección 2: Datos de vinculación ──────────────────────────────────────
    tipo_vinculacion = models.CharField(max_length=20, choices=TIPO_VINCULACION_CHOICES)
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    area_servicios = models.CharField(max_length=150)
    cargo_funcionario = models.CharField(max_length=150)
    numero_contrato = models.CharField(max_length=100, blank=True, default='')
    num_registro_tarjeta = models.CharField(max_length=100, blank=True, default='')
    nombre_empresa_contratista = models.CharField(max_length=200, blank=True, default='')
    direccion_empresa_contratista = models.CharField(max_length=200, blank=True, default='')
    tel_empresa_contratista = models.CharField(max_length=20, blank=True, default='')
    empresa_tercerizada_id = models.IntegerField(null=True, blank=True)

    # ── Sección 4: Entrenamiento ──────────────────────────────────────────────
    fecha_entrenamiento = models.DateField(null=True, blank=True)
    hora_inicio_entrenamiento = models.TimeField(null=True, blank=True)
    hora_fin_entrenamiento = models.TimeField(null=True, blank=True)
    responsable_entrenamiento = models.CharField(max_length=150, blank=True, default='')
    entrenamiento_dgh = models.BooleanField(default=False)
    entrenamiento_correo = models.BooleanField(default=False)
    entrenamiento_aplicativos = models.BooleanField(default=False)
    entrenamiento_intranet = models.BooleanField(default=False)
    acepto_confidencialidad = models.BooleanField(default=False)

    # ── Datos de carnet (solo cuando se solicita carnet o tarjeta_chip) ─────────
    foto_carnet = models.TextField(blank=True, default='')   # base64 PNG
    tipo_sangre = models.CharField(max_length=10, blank=True, default='')

    # ── Firma del funcionario (base64 PNG) ────────────────────────────────────
    firma_funcionario = models.TextField(blank=True, default='')

    # ── Metadatos ─────────────────────────────────────────────────────────────
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='EN_TRAMITE')
    creado_por = models.CharField(max_length=100, blank=True, default='')
    correo_notificacion = models.CharField(max_length=150, blank=True, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'apc_solicitudes'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombres_apellidos} ({self.num_identificacion})"

    @property
    def es_tercerizado(self):
        return self.tipo_vinculacion == 'tercerizado'


class PermisoSolicitado(models.Model):
    """Permisos y accesos marcados en la Sección 3."""
    solicitud = models.ForeignKey(
        SolicitudAPC, on_delete=models.CASCADE, related_name='permisos_solicitados'
    )
    permiso_clave = models.CharField(max_length=80)

    class Meta:
        db_table = 'apc_permisos_solicitados'
        unique_together = [('solicitud', 'permiso_clave')]

    def __str__(self):
        return f"Solicitud {self.solicitud_id} — {self.permiso_clave}"


class FirmaAPC(models.Model):
    """Una firma del proceso de aprobación."""
    TIPO_CHOICES = [
        ('coordinador_area', 'Coordinador de Área'),
        ('resp_contratista', 'Responsable Contratista'),
        ('funcionario', 'Funcionario'),
        ('coord_talento_humano', 'Coordinador Talento Humano'),
        ('coord_gestion_info', 'Coordinador Gestión de Información'),
    ]

    solicitud = models.ForeignKey(
        SolicitudAPC, on_delete=models.CASCADE, related_name='firmas'
    )
    tipo_firma = models.CharField(max_length=30, choices=TIPO_CHOICES)
    nombre_firmante = models.CharField(max_length=150)
    email_firmante = models.CharField(max_length=150, blank=True, default='')
    firma_imagen = models.TextField(blank=True, default='')  # base64 PNG
    token_firma = models.CharField(max_length=250, unique=True, null=True, blank=True)
    token_expira = models.DateTimeField(null=True, blank=True)
    firmado = models.BooleanField(default=False)
    fecha_firma = models.DateTimeField(null=True, blank=True)
    orden = models.SmallIntegerField(default=1)
    # Si auto_firma_con != null: al firmar esta firma, también se auto-firma la referenciada
    auto_firma_con = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='auto_firmadas_por'
    )

    class Meta:
        db_table = 'apc_firmas'
        ordering = ['orden', 'id']

    def __str__(self):
        estado = 'Firmado' if self.firmado else 'Pendiente'
        return f"{self.get_tipo_firma_display()} — {self.nombre_firmante} [{estado}]"


class CoordinadorAreaGmail(models.Model):
    """
    Copia local de cada CoordinadorRecargos (horas_extras) dentro de APC.
    nombre y areas se sincronizan automáticamente desde horas_extras al consultar.
    gmail y usuario_dinamica son los únicos campos editables por el administrador APC.
    """
    coordinador_id = models.IntegerField(unique=True)
    nombre = models.CharField(max_length=150, default='')
    areas = models.TextField(default='')  # nombres de áreas separados por coma
    gmail = models.CharField(max_length=150, blank=True, default='')
    usuario_dinamica = models.CharField(max_length=150, blank=True, default='')
    firma_imagen = models.TextField(blank=True, default='')  # base64 PNG

    class Meta:
        db_table = 'apc_coordinador_area_gmail'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} → {self.gmail or '(sin gmail)'}"


class EmailLogAPC(models.Model):
    """Log de correos enviados por el módulo APC."""
    ESTADO_CHOICES = [('ENVIADO', 'Enviado'), ('ERROR', 'Error')]
    solicitud = models.ForeignKey(
        SolicitudAPC, null=True, blank=True, on_delete=models.SET_NULL
    )
    destinatario = models.CharField(max_length=150)
    asunto = models.CharField(max_length=250)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    error_msg = models.TextField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'apc_email_log'
        ordering = ['-fecha_hora']
