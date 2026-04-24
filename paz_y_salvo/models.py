from django.db import models


class Area(models.Model):
    nombre = models.CharField(max_length=120)
    responsable = models.CharField(max_length=120)
    orden = models.SmallIntegerField(default=1)
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'pys_areas'
        ordering = ['orden', 'id']

    def __str__(self):
        return self.nombre


class ListaBlanca(models.Model):
    ROL_CHOICES = [
        ('paz_salvo', 'Paz y Salvo'),
        ('permisos', 'Permisos'),
        ('validador', 'Validador'),
        ('firmador', 'Firmador'),
        ('admin', 'Admin'),
    ]
    usunombre = models.CharField(max_length=100, unique=True)
    usuemail = models.CharField(max_length=150)
    nombre = models.CharField(max_length=150)
    avatar = models.CharField(max_length=4, default='US')
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)
    area = models.ForeignKey(Area, null=True, blank=True, on_delete=models.SET_NULL)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pys_lista_blanca'

    def __str__(self):
        return f"{self.usunombre} ({self.rol})"


class UsuarioApp(models.Model):
    TEMA_CHOICES = [('claro', 'Claro'), ('oscuro', 'Oscuro')]
    usunombre = models.CharField(max_length=100, unique=True)
    nombre_completo = models.CharField(max_length=150)
    cargo = models.CharField(max_length=150, null=True, blank=True)
    dependencia = models.CharField(max_length=150, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    foto_url = models.CharField(max_length=500, null=True, blank=True)
    tema = models.CharField(max_length=10, choices=TEMA_CHOICES, default='claro')
    ultimo_login = models.DateTimeField(null=True, blank=True)
    total_logins = models.PositiveIntegerField(default=0)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pys_usuarios_app'


class PazSalvo(models.Model):
    ESTADO_CHOICES = [
        ('EN_TRAMITE', 'En Trámite'),
        ('VALIDADO', 'Validado'),
        ('RECHAZADO', 'Rechazado'),
        ('CANCELADO', 'Cancelado'),
    ]
    identificacion = models.CharField(max_length=20)
    nombre = models.CharField(max_length=150)
    cargo = models.CharField(max_length=150)
    dependencia = models.CharField(max_length=150)
    coordinador = models.CharField(max_length=150)
    fecha_retiro = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='EN_TRAMITE')
    archivado = models.BooleanField(default=False)
    creado_por = models.CharField(max_length=100)
    correo = models.CharField(max_length=150, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pys_paz_salvos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre} ({self.identificacion})"


class Validacion(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('VALIDADO', 'Validado'),
        ('RECHAZADO', 'Rechazado'),
    ]
    ps = models.ForeignKey(PazSalvo, on_delete=models.CASCADE, related_name='validaciones')
    area = models.ForeignKey(Area, on_delete=models.PROTECT)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    observacion = models.TextField(null=True, blank=True)
    fecha = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'pys_validaciones'
        unique_together = [('ps', 'area')]


class LogAcceso(models.Model):
    ACCION_CHOICES = [('LOGIN', 'Login'), ('LOGOUT', 'Logout')]
    usunombre = models.CharField(max_length=100)
    nombre = models.CharField(max_length=150)
    rol = models.CharField(max_length=30)
    accion = models.CharField(max_length=10, choices=ACCION_CHOICES)
    ip = models.CharField(max_length=45, null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pys_log_accesos'
        ordering = ['-fecha_hora']


class EmailLog(models.Model):
    ESTADO_CHOICES = [('ENVIADO', 'Enviado'), ('ERROR', 'Error')]
    ps = models.ForeignKey(PazSalvo, null=True, blank=True, on_delete=models.SET_NULL)
    area = models.ForeignKey(Area, null=True, blank=True, on_delete=models.SET_NULL)
    destinatario = models.CharField(max_length=150)
    asunto = models.CharField(max_length=250)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    error_msg = models.TextField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pys_email_log'
        ordering = ['-fecha_hora']


class SolicitudPS(models.Model):
    ESTADO_CHOICES = [('PENDIENTE', 'Pendiente'), ('PROCESADA', 'Procesada')]
    nombre = models.CharField(max_length=150)
    identificacion = models.CharField(max_length=20)
    correo = models.CharField(max_length=150, null=True, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    procesado_por = models.CharField(max_length=100, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pys_solicitudes_ps'
        ordering = ['-fecha_creacion']


class SolicitudPSArchivo(models.Model):
    solicitud = models.ForeignKey(SolicitudPS, on_delete=models.CASCADE, related_name='archivos')
    nombre_original = models.CharField(max_length=255)
    contenido = models.BinaryField()
    tipo_mime = models.CharField(max_length=100, default='application/octet-stream')

    class Meta:
        db_table = 'pys_solicitudes_ps_archivos'


class EncuestaRetiro(models.Model):
    CALIF_CHOICES = [
        ('excelente', 'Excelente'),
        ('buena', 'Buena'),
        ('mala', 'Mala'),
    ]
    nombre = models.CharField(max_length=150)
    identificacion = models.CharField(max_length=20)
    correo = models.CharField(max_length=150)
    fecha_retiro = models.DateField()
    aspectos_positivos = models.TextField(null=True, blank=True)
    actividades_sugeridas = models.TextField(null=True, blank=True)
    calif_compañeros = models.CharField(max_length=15, choices=CALIF_CHOICES, default='')
    calif_formacion = models.CharField(max_length=15, choices=CALIF_CHOICES, default='')
    calif_ambiente = models.CharField(max_length=15, choices=CALIF_CHOICES, default='')
    calif_reconocimiento = models.CharField(max_length=15, choices=CALIF_CHOICES, default='')
    calif_carga_trabajo = models.CharField(max_length=15, choices=CALIF_CHOICES, default='')
    calif_superior = models.CharField(max_length=15, choices=CALIF_CHOICES, default='')
    calif_beneficios = models.CharField(max_length=15, choices=CALIF_CHOICES, default='')
    calif_salario = models.CharField(max_length=15, choices=CALIF_CHOICES, default='')
    calif_valores = models.CharField(max_length=15, choices=CALIF_CHOICES, default='')
    calif_cultura = models.CharField(max_length=15, choices=CALIF_CHOICES, default='')
    calif_trabajo_equipo = models.CharField(max_length=15, choices=CALIF_CHOICES, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pys_encuestas_retiro'


class FirmanteConfig(models.Model):
    lb = models.ForeignKey(ListaBlanca, on_delete=models.CASCADE)
    rol_label = models.CharField(max_length=100)
    orden = models.SmallIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'pys_firmantes_config'
        unique_together = [('lb', 'rol_label')]
        ordering = ['orden']
