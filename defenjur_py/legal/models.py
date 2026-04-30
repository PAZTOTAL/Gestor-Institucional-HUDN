from django.db import models
from django.utils import timezone as django_timezone
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    nick = models.CharField(max_length=120, unique=True, null=True, blank=True)
    rol = models.CharField(max_length=120)
    estado = models.IntegerField(default=1)

    # Evitar choques con el User de auth estándar en el monorepo
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='legal_usuario_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='legal_usuario_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

# Diccionarios (Enums) para asegurar integridad en dashboard
ESTADO_CHOICES = [
    ('ACTIVO', 'Activo'),
    ('INACTIVO', 'Inactivo'),
    ('TERMINADO', 'Terminado'),
    ('TRAMITE', 'En Trámite'),
]

MEDIO_CONTROL_CHOICES = [
    ('REPARACION_DIRECTA', 'Reparación Directa'),
    ('NULIDAD_RESTABLECIMIENTO', 'Nulidad y Restablecimiento del Derecho'),
    ('ACCION_POPULAR', 'Acción Popular'),
    ('ACCION_CUMPLIMIENTO', 'Acción de Cumplimiento'),
    ('ACCION_TUTELA', 'Acción de Tutela'),
    ('OTROS', 'Otros'),
]

class ProcesoExtrajudicial(models.Model):
    demandante = models.CharField(max_length=255)
    demandado = models.CharField(max_length=255)
    apoderado = models.CharField(max_length=255)
    medio_control = models.CharField(max_length=255, choices=MEDIO_CONTROL_CHOICES, default='OTROS')
    despacho_conocimiento = models.TextField()
    estado = models.CharField(max_length=120, choices=ESTADO_CHOICES, default='TRAMITE')
    clasificacion = models.CharField(max_length=120, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'defenjur_app_procesoextrajudicial'
        verbose_name_plural = "Procesos Extrajudiciales"
        indexes = [
            models.Index(fields=['apoderado']),
        ]

class ProcesoJudicialActiva(models.Model):
    num_proceso = models.CharField('N° proceso', max_length=255, null=True, blank=True)
    fecha_registro = models.DateTimeField('Fecha registro', auto_now_add=True)
    medio_control = models.CharField(
        'Medio de control', max_length=255, null=True, blank=True, choices=MEDIO_CONTROL_CHOICES
    )
    demandante = models.CharField('Demandante', max_length=255, null=True, blank=True)
    demandado = models.CharField('Demandado', max_length=255, null=True, blank=True)
    apoderado = models.CharField('Apoderado', max_length=255, null=True, blank=True)
    despacho_actual = models.CharField('Despacho', max_length=255, null=True, blank=True)
    ciudad = models.CharField('Ciudad', max_length=255, null=True, blank=True)
    pretension = models.TextField('Pretensión', null=True, blank=True)
    estimacion_cuantia = models.CharField(
        'Estimación cuantía', max_length=255, null=True, blank=True,
    )
    sentencia_primera_instancia = models.CharField(
        'Sentencia primera instancia', max_length=255, null=True, blank=True,
    )
    ultima_actuacion = models.TextField('Última actuación', null=True, blank=True)
    estado_actual = models.TextField('Estado actual', null=True, blank=True)

    class Meta:
        db_table = 'defenjur_app_procesojudicialactiva'
        verbose_name = 'Proceso judicial activo'
        verbose_name_plural = 'Procesos Judiciales Activos'
        indexes = [
            models.Index(fields=['num_proceso']),
            models.Index(fields=['apoderado']),
        ]

class ProcesoJudicialPasiva(models.Model):
    num_proceso = models.CharField('N° proceso', max_length=255, null=True, blank=True)
    fecha_registro = models.DateTimeField('Fecha registro', auto_now_add=True)
    medio_control = models.CharField(
        'Medio de control', max_length=255, null=True, blank=True, choices=MEDIO_CONTROL_CHOICES
    )
    demandante = models.CharField('Demandante', max_length=255, null=True, blank=True)
    cc_demandante = models.CharField('C.C. demandante', max_length=255, null=True, blank=True)
    demandado = models.CharField('Demandado', max_length=255, null=True, blank=True)
    apoderado = models.CharField('Apoderado', max_length=255, null=True, blank=True)
    despacho_actual = models.CharField('Despacho', max_length=255, null=True, blank=True)
    pretensiones = models.TextField('Pretensiones', null=True, blank=True)
    valor_pretension_inicial = models.CharField(
        'Valor pretensión inicial', max_length=255, null=True, blank=True,
    )
    valor_provisionar = models.CharField(
        'Valor a provisionar', max_length=255, null=True, blank=True,
    )
    fallo_sentencia = models.CharField('Fallo / sentencia', max_length=255, null=True, blank=True)
    valor_fallo_sentencia = models.CharField(
        'Valor fallo sentencia', max_length=255, null=True, blank=True,
    )
    estado_actual = models.TextField('Estado actual', null=True, blank=True)
    riesgo_perdida = models.CharField('Riesgo pérdida', max_length=255, null=True, blank=True)
    porcentaje_probabilidad_perdida = models.CharField(
        '% probabilidad pérdida', max_length=255, null=True, blank=True,
    )
    hechos_relevantes = models.TextField('Hechos relevantes', null=True, blank=True)
    enfoque_defensa = models.TextField('Enfoque defensa', null=True, blank=True)
    calidad_entidad = models.CharField('Calidad entidad', max_length=255, null=True, blank=True)
    hecho_generador = models.CharField('Hecho generador', max_length=255, null=True, blank=True)
    observaciones = models.TextField('Observaciones', null=True, blank=True)

    class Meta:
        db_table = 'defenjur_app_procesojudicialpasiva'
        verbose_name = 'Proceso judicial pasivo'
        verbose_name_plural = 'Procesos Judiciales Pasivos'
        indexes = [
            models.Index(fields=['num_proceso']),
            models.Index(fields=['apoderado']),
        ]

class DerechoPeticion(models.Model):
    fecha_correo = models.CharField(
        'Fecha correo', max_length=255, null=True, blank=True,
    )
    correo_remitente_peticion = models.EmailField(
        'Correo remitente petición', null=True, blank=True,
    )
    num_reparto = models.CharField(
        'N° reparto', max_length=255, null=True, blank=True,
    )
    fecha_reparto = models.CharField(
        'Fecha reparto', max_length=255, null=True, blank=True,
    )
    num_rad_interno = models.CharField(
        'N° radicado interno', max_length=255, null=True, blank=True,
    )
    fecha_remitente_peticion = models.CharField(
        'Fecha remitente petición', max_length=255, null=True, blank=True,
    )
    nombre_persona_solicitante = models.CharField(
        'Solicitante', max_length=255, null=True, blank=True,
    )
    cedula_persona_solicitante = models.CharField(
        'Cédula solicitante', max_length=255, null=True, blank=True,
    )
    peticionario_int_ext = models.CharField(
        'Peticionario int./ext.', max_length=255, null=True, blank=True,
    )
    peticionario = models.CharField(
        'Peticionario', max_length=255, null=True, blank=True,
    )
    causa_peticion = models.TextField('Causa', null=True, blank=True)
    abogado_responsable = models.CharField(
        'Abogado responsable', max_length=255, null=True, blank=True,
    )
    modalidad_peticion = models.CharField(
        'Modalidad petición', max_length=255, null=True, blank=True,
    )
    tramite_impartido = models.TextField('Trámite impartido', null=True, blank=True)
    tiempo_area_remitir_informacion = models.CharField(
        'Tiempo área remitir información', max_length=255, null=True, blank=True,
    )
    area_remitir_informacion = models.CharField(
        'Área remitir información', max_length=255, null=True, blank=True,
    )
    termino_dar_tramite = models.CharField(
        'Término dar trámite', max_length=255, null=True, blank=True,
    )
    fecha_respuesta_peticion = models.CharField(
        'Fecha respuesta petición', max_length=255, null=True, blank=True,
    )
    num_rad_arch_central = models.CharField(
        'N° rad. archivo central', max_length=255, null=True, blank=True,
    )
    observaciones = models.TextField('Observaciones', null=True, blank=True)

    # ==========================================
    # NUEVOS CAMPOS (Seguimiento y Control)
    # Todos son null=True, blank=True para no afectar las peticiones antiguas
    # ==========================================
    
    fecha_notificacion = models.DateTimeField('FECHA Y HORA DE NOTIFICACIÓN', null=True, blank=True)
    termino_dias = models.IntegerField('TÉRMINO (DÍAS)', null=True, blank=True)
    termino_horas = models.IntegerField('TÉRMINO (HORAS)', null=True, blank=True)
    fecha_vencimiento = models.DateTimeField('FECHA DE VENCIMIENTO', null=True, blank=True)
    
    fecha_respuesta_real = models.DateTimeField('FECHA DE RESPUESTA (RADICACIÓN)', null=True, blank=True)
    radicado_respuesta_salida = models.CharField('RADICADO DE RESPUESTA', max_length=255, null=True, blank=True)
    medio_envio_respuesta = models.CharField('MEDIO DE ENVÍO', max_length=255, null=True, blank=True)
    
    ESTADOS_PETICION = [
        ('NUEVA', 'Nueva / Por Asignar'),
        ('EN_TRAMITE', 'En Trámite'),
        ('CONTESTADA', 'Contestada'),
        ('VENCIDA', 'Vencida'),
        ('CERRADA', 'Cerrada / Terminada'),
    ]
    estado_peticion = models.CharField('ESTADO DE LA PETICIÓN', max_length=50, choices=ESTADOS_PETICION, default='NUEVA', null=True, blank=True)

    @property
    def semaforo(self):
        if self.estado_peticion in ['CONTESTADA', 'CERRADA']:
            return 'gris'
            
        if not self.fecha_vencimiento:
            return 'gris'

        from django.utils import timezone
        ahora = timezone.now()
        delta = self.fecha_vencimiento - ahora
        
        if delta.total_seconds() < 0:
            return 'rojo'
        elif delta.total_seconds() <= 86400: # 24h
            return 'amarillo'
        else:
            return 'verde'

    class Meta:
        db_table = 'defenjur_app_derechopeticion'
        verbose_name = 'Derecho de petición'
        verbose_name_plural = 'Derechos de Petición'
        indexes = [
            models.Index(fields=['num_reparto']),
            models.Index(fields=['abogado_responsable']),
        ]

class AccionTutela(models.Model):
    # Campos obligatorios según esquema técnico y solicitud del usuario
    num_proceso = models.CharField('NÚMERO DE PROCESO', max_length=255, db_column='num_proceso', null=True, blank=True)
    fecha_llegada = models.CharField('FECHA DE LLEGADA', max_length=255, db_column='fecha_llegada', null=True, blank=True)
    despacho_judicial = models.CharField('DESPACHO JUDICIAL', max_length=255, db_column='despacho_judicial', null=True, blank=True)
    num_reparto = models.CharField('N° REPARTO', max_length=255, db_column='num_reparto', null=True, blank=True)
    
    cedula_accionante = models.CharField('CÉDULA ACCIONANTE', max_length=50, null=True, blank=True)
    accionante = models.CharField('ACCIONANTE', max_length=255, db_column='accionante', null=True, blank=True)
    email_accionante = models.EmailField('EMAIL ACCIONANTE', max_length=255, null=True, blank=True)
    
    accionado = models.CharField('ACCIONADO', max_length=255, db_column='accionado', null=True, blank=True)
    abogado_responsable = models.CharField('ABOGADO RESPONSABLE', max_length=255, db_column='abogado_responsable', null=True, blank=True)
    
    # Auditoría (Carga)
    usuario_carga = models.CharField('Usuario Carga', max_length=150, null=True, blank=True)
    fecha_registro = models.DateTimeField('Fecha Registro', auto_now_add=True, null=True)

    # ==========================================
    # NUEVOS CAMPOS (Seguimiento y Control)
    # Todos son null=True, blank=True para no afectar las tutelas antiguas
    # ==========================================
    
    # 1. Fechas y Términos
    fecha_notificacion = models.DateTimeField('FECHA Y HORA DE NOTIFICACIÓN', null=True, blank=True)
    termino_dias = models.IntegerField('TÉRMINO (DÍAS)', null=True, blank=True)
    termino_horas = models.IntegerField('TÉRMINO (HORAS)', null=True, blank=True)
    fecha_vencimiento = models.DateTimeField('FECHA DE VENCIMIENTO', null=True, blank=True)
    
    # 2. Contestación
    fecha_respuesta = models.DateTimeField('FECHA DE RESPUESTA (RADICACIÓN)', null=True, blank=True)
    radicado_respuesta = models.CharField('RADICADO DE RESPUESTA', max_length=255, null=True, blank=True)
    medio_envio_respuesta = models.CharField('MEDIO DE ENVÍO', max_length=255, null=True, blank=True)
    
    # 3. Detalles Jurídicos
    derechos_vulnerados = models.TextField('DERECHOS VULNERADOS', null=True, blank=True)
    pretensiones = models.TextField('PRETENSIONES', null=True, blank=True)
    
    # 4. Estados y Fallos
    ESTADOS_TUTELA = [
        ('NUEVA', 'Nueva / Por Asignar'),
        ('EN_TERMINO', 'En Término'),
        ('CONTESTADA', 'Contestada'),
        ('FALLO_1RA', 'Fallo 1ra Instancia'),
        ('IMPUGNADA', 'Impugnada'),
        ('FALLO_2DA', 'Fallo 2da Instancia'),
        ('EN_CUMPLIMIENTO', 'En Cumplimiento'),
        ('CERRADA', 'Cerrada / Terminada'),
    ]
    estado_tutela = models.CharField('ESTADO DE LA TUTELA', max_length=50, choices=ESTADOS_TUTELA, default='NUEVA', null=True, blank=True)
    
    SENTIDO_FALLO = [
        ('CONCEDE', 'Concede'),
        ('NIEGA', 'Niega'),
        ('IMPROCEDENTE', 'Declara Improcedente'),
        ('HECHO_SUPERADO', 'Hecho Superado'),
        ('OTRO', 'Otro'),
    ]
    sentido_fallo = models.CharField('SENTIDO DEL FALLO', max_length=50, choices=SENTIDO_FALLO, null=True, blank=True)
    
    # 5. Cumplimiento y Desacato
    requiere_cumplimiento = models.BooleanField('REQUIERE CUMPLIMIENTO', default=False)
    fecha_limite_cumplimiento = models.DateField('FECHA LÍMITE CUMPLIMIENTO', null=True, blank=True)
    incidente_desacato = models.BooleanField('INCIDENTE DE DESACATO', default=False)
    
    observaciones = models.TextField('OBSERVACIONES GENERALES', null=True, blank=True)

    class Meta:
        db_table = 'defenjur_app_acciontutela'
        verbose_name_plural = "Acciones de Tutela"
        indexes = [
            models.Index(fields=['num_proceso']),
            models.Index(fields=['num_reparto']),
            models.Index(fields=['abogado_responsable']),
        ]

    @property
    def semaforo(self):
        if self.estado_tutela in ['CONTESTADA', 'CERRADA']:
            return 'gris'
            
        from django.utils import timezone
        ahora = timezone.now()
        
        # Si hay incidentes de desacato, el semáforo depende del más reciente activo
        if self.incidente_desacato:
            ultimo_incidente = self.incidentes.order_by('-fecha_notificacion').first()
            if ultimo_incidente and ultimo_incidente.fecha_vencimiento:
                if ultimo_incidente.fecha_respuesta:
                    return 'gris' # Ya respondido
                
                delta = ultimo_incidente.fecha_vencimiento - ahora
                if delta.total_seconds() < 0:
                    return 'rojo'
                elif delta.total_seconds() <= 86400:
                    return 'amarillo'
                else:
                    return 'verde'

        if not self.fecha_vencimiento:
            return 'gris'

        delta = self.fecha_vencimiento - ahora
        
        if delta.total_seconds() < 0:
            return 'rojo'
        elif delta.total_seconds() <= 86400: # 24h
            return 'amarillo'
        else:
            return 'verde'

class IncidenteDesacato(models.Model):
    tutela = models.ForeignKey(AccionTutela, on_delete=models.CASCADE, related_name='incidentes')
    fecha_notificacion = models.DateTimeField('FECHA Y HORA DE NOTIFICACIÓN', null=True, blank=True)
    termino_dias = models.IntegerField('TÉRMINO (DÍAS)', null=True, blank=True)
    termino_horas = models.IntegerField('TÉRMINO (HORAS)', null=True, blank=True)
    fecha_vencimiento = models.DateTimeField('FECHA DE VENCIMIENTO', null=True, blank=True)
    fecha_respuesta = models.DateTimeField('FECHA DE RESPUESTA (RADICACIÓN)', null=True, blank=True)
    radicado_respuesta = models.CharField('RADICADO DE RESPUESTA', max_length=100, null=True, blank=True)
    medio_envio = models.CharField('MEDIO DE ENVÍO', max_length=100, null=True, blank=True)
    observaciones = models.TextField('OBSERVACIONES DEL INCIDENTE', null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'defenjur_app_incidentedesacato'
        verbose_name = 'Incidente de Desacato'
        verbose_name_plural = 'Incidentes de Desacato'

    def __str__(self):
        return f"Incidente de {self.tutela.num_proceso} - {self.fecha_notificacion}"

class PronunciamientoHecho(models.Model):
    TIPO_RESPUESTA = [
        ('ADMITA', 'Admita'),
        ('NIEGA', 'Niega'),
        ('NO_CONSTA', 'No le Consta'),
        ('PARCIAL', 'Parcialmente Cierto'),
    ]
    tutela = models.ForeignKey(AccionTutela, on_delete=models.CASCADE, related_name='pronunciamientos_hechos')
    hecho_referencia = models.CharField('REFERENCIA AL HECHO', max_length=255, help_text='Ej: FRENTE AL PRIMER HECHO, DEL SEGUNDO AL NOVENO...')
    tipo_respuesta = models.CharField('RESPUESTA', max_length=20, choices=TIPO_RESPUESTA, default='ADMITA')
    pronunciamiento = models.TextField('PRONUNCIAMIENTO / EXPLICACIÓN')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'defenjur_app_pronunciamientohecho'
        verbose_name = "Pronunciamiento sobre Hecho"
        verbose_name_plural = "Pronunciamientos sobre Hechos"

class ArchivoAdjunto(models.Model):
    tipo_asociado = models.CharField(max_length=100)
    id_asociado = models.IntegerField()
    archivo = models.FileField(upload_to='adjuntos/%Y/%m/%d/')
    nombre_original = models.CharField(max_length=255)
    fecha_carga = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'defenjur_app_archivoadjunto'

    def __str__(self):
        return f"{self.tipo_asociado} - {self.nombre_original}"

class Peritaje(models.Model):
    fecha_correo_electronico = models.CharField(
        'Fecha correo', max_length=255, null=True, blank=True,
    )
    num_reparto = models.CharField('N° reparto', max_length=255, null=True, blank=True)
    fecha_reparto = models.CharField('Fecha reparto', max_length=255, null=True, blank=True)
    num_proceso = models.CharField('N° proceso', max_length=255, null=True, blank=True)
    entidad_remitente_requerimiento = models.CharField(
        'Entidad requirente', max_length=255, null=True, blank=True,
    )
    demandante = models.CharField('Demandante', max_length=255, null=True, blank=True)
    demandado = models.CharField('Demandado', max_length=255, null=True, blank=True)
    asunto = models.TextField('Asunto', null=True, blank=True)
    abogado_responsable = models.CharField(
        'Abogado responsable', max_length=255, null=True, blank=True,
    )
    fecha_asignar_perito = models.CharField(
        'Fecha asignar perito', max_length=255, null=True, blank=True,
    )
    perito_asignado = models.CharField('Perito asignado', max_length=255, null=True, blank=True)
    pago_honorarios = models.CharField('Pago honorarios', max_length=120, null=True, blank=True)
    observaciones = models.TextField('Observaciones', null=True, blank=True)
    fecha_registro = models.DateTimeField('Fecha registro', auto_now_add=True)

    class Meta:
        db_table = 'defenjur_app_peritaje'
        verbose_name = 'Peritaje'
        verbose_name_plural = 'Peritajes'
        indexes = [
            models.Index(fields=['num_proceso']),
            models.Index(fields=['abogado_responsable']),
        ]

class PagoSentenciaJudicial(models.Model):
    num_proceso = models.CharField('N° proceso', max_length=255, null=True, blank=True)
    despacho_tramitante = models.CharField(
        'Despacho tramitante', max_length=255, null=True, blank=True,
    )
    medio_control = models.CharField(
        'Medio de control', max_length=255, null=True, blank=True, choices=MEDIO_CONTROL_CHOICES
    )
    demandante = models.CharField('Demandante', max_length=255, null=True, blank=True)
    demandado = models.CharField('Demandado', max_length=255, null=True, blank=True)
    valor_pagado = models.CharField('Valor pagado', max_length=255, null=True, blank=True)
    estado = models.CharField('Estado', max_length=255, null=True, blank=True, choices=ESTADO_CHOICES)
    tipo_pago = models.CharField('Tipo de pago', max_length=255, null=True, blank=True)
    abogado_responsable = models.CharField(
        'Abogado responsable', max_length=255, null=True, blank=True,
    )
    fecha_pago = models.CharField('Fecha pago', max_length=255, null=True, blank=True)
    fecha_ejecutoria_sentencia = models.CharField(
        'Fecha ejecutoria sentencia', max_length=255, null=True, blank=True,
    )
    imputacion_costo = models.CharField(
        'Imputación costo', max_length=255, null=True, blank=True,
    )
    fecha_registro = models.DateTimeField(
        'Fecha registro', default=django_timezone.now, null=True, blank=True,
    )

    class Meta:
        db_table = 'defenjur_app_pagosentenciajudicial'
        verbose_name = 'Pago de sentencia judicial'
        verbose_name_plural = 'Pagos de Sentencias Judiciales'
        indexes = [
            models.Index(fields=['num_proceso']),
        ]

class ProcesoJudicialTerminado(models.Model):
    num_proceso = models.CharField('N° proceso', max_length=255, null=True, blank=True)
    medio_control = models.CharField(
        'Medio de control', max_length=255, null=True, blank=True, choices=MEDIO_CONTROL_CHOICES
    )
    demandante = models.CharField('Demandante', max_length=255, null=True, blank=True)
    cc_demandante = models.CharField('C.C. demandante', max_length=255, null=True, blank=True)
    demandado = models.CharField('Demandado', max_length=255, null=True, blank=True)
    apoderado = models.CharField('Apoderado', max_length=255, null=True, blank=True)
    despacho_actual = models.CharField('Despacho', max_length=255, null=True, blank=True)
    ciudad = models.CharField('Ciudad', max_length=255, null=True, blank=True)
    pretensiones = models.TextField('Pretensiones', null=True, blank=True)
    valor_proceso = models.CharField('Valor proceso', max_length=255, null=True, blank=True)
    valor_pretension_inicial = models.CharField(
        'Valor pretensión inicial', max_length=255, null=True, blank=True,
    )
    valor_provisionar = models.CharField(
        'Valor a provisionar', max_length=255, null=True, blank=True,
    )
    fallo_sentencia = models.CharField('Fallo / sentencia', max_length=255, null=True, blank=True)
    valor_fallo_sentencia = models.CharField(
        'Valor fallo sentencia', max_length=255, null=True, blank=True,
    )
    estado_actual = models.TextField('Estado actual', null=True, blank=True)
    ultima_actuacion = models.TextField('Última actuación', null=True, blank=True)
    riesgo_perdida = models.CharField('Riesgo pérdida', max_length=255, null=True, blank=True)
    porcentaje_probabilidad_perdida = models.CharField(
        '% probabilidad pérdida', max_length=255, null=True, blank=True,
    )
    hechos_relevantes = models.TextField('Hechos relevantes', null=True, blank=True)
    enfoque_defensa = models.TextField('Enfoque defensa', null=True, blank=True)
    calidad_entidad = models.CharField('Calidad entidad', max_length=255, null=True, blank=True)
    hecho_generador = models.CharField('Hecho generador', max_length=255, null=True, blank=True)
    observaciones = models.TextField('Observaciones', null=True, blank=True)
    informe_pago = models.CharField('Informe pago', max_length=255, null=True, blank=True)
    accion_repeticion = models.CharField('Acción repetición', max_length=120, null=True, blank=True)
    fecha_registro = models.DateTimeField('Fecha registro', auto_now_add=True)

    class Meta:
        db_table = 'defenjur_app_procesojudicialterminado'
        verbose_name = 'Proceso judicial terminado'
        verbose_name_plural = 'Procesos Judiciales Terminados'
        indexes = [
            models.Index(fields=['num_proceso']),
            models.Index(fields=['apoderado']),
        ]

class ProcesoAdministrativoSancionatorio(models.Model):
    num_proceso = models.CharField('N° proceso', max_length=255, null=True, blank=True)
    entidad = models.CharField('Entidad', max_length=255, null=True, blank=True)
    causa = models.TextField('Causa', null=True, blank=True)
    estado = models.CharField(max_length=120, null=True, blank=True, choices=ESTADO_CHOICES)
    fecha_requerimiento = models.CharField(
        'Fecha requerimiento', max_length=255, null=True, blank=True,
    )
    entidad_solicitante_requerimiento = models.CharField(
        'Entidad solicitante', max_length=255, null=True, blank=True,
    )
    objeto_requerimiento = models.TextField('Objeto del requerimiento', null=True, blank=True)
    fecha_dar_tramite_desde = models.CharField(
        'Fecha dar trámite desde', max_length=255, null=True, blank=True,
    )
    fecha_dar_tramite_hasta = models.CharField(
        'Fecha dar trámite hasta', max_length=255, null=True, blank=True,
    )
    fecha_registro = models.DateTimeField('Fecha registro', auto_now_add=True)

    class Meta:
        db_table = 'defenjur_app_procesoadministrativosancionatorio'
        verbose_name = 'Proceso administrativo sancionatorio'
        verbose_name_plural = 'Procesos Administrativos Sancionatorios'
        indexes = [
            models.Index(fields=['num_proceso']),
        ]

class RequerimientoEnteControl(models.Model):
    num_reparto = models.CharField('N° reparto', max_length=255, null=True, blank=True)
    num_proceso = models.CharField('N° proceso', max_length=255, null=True, blank=True)
    fecha_correo_electronico = models.CharField(
        'Fecha correo', max_length=255, null=True, blank=True,
    )
    entidad_remitente_requerimiento = models.CharField(
        'Entidad', max_length=255, null=True, blank=True,
    )
    asunto = models.TextField('Asunto', null=True, blank=True)
    abogado_responsable = models.CharField(
        'Responsable', max_length=255, null=True, blank=True,
    )
    correo = models.EmailField('Correo', null=True, blank=True)
    fecha_reparto = models.CharField(
        'Fecha reparto', max_length=255, null=True, blank=True,
    )
    tipo_tramite = models.CharField(
        'Tipo trámite', max_length=255, null=True, blank=True,
    )
    termino_dar_tramite = models.CharField(
        'Término dar trámite', max_length=255, null=True, blank=True,
    )
    observaciones = models.TextField('Observaciones', null=True, blank=True)
    tramite_impartido = models.TextField('Trámite impartido', null=True, blank=True)
    fecha_respuesta_tramite = models.CharField(
        'Fecha respuesta trámite', max_length=255, null=True, blank=True,
    )
    fecha_registro = models.DateTimeField('Fecha registro', auto_now_add=True)

    class Meta:
        db_table = 'defenjur_app_requerimientoentecontrol'
        verbose_name = 'Requerimiento de ente de control'
        verbose_name_plural = 'Requerimientos de Entes de Control'
        indexes = [
            models.Index(fields=['num_proceso']),
            models.Index(fields=['num_reparto']),
            models.Index(fields=['abogado_responsable']),
        ]


class DespachoJudicial(models.Model):
    """
    Catálogo de Despachos Judiciales.
    Fuente: despachoJudicial.xlsx — 55 registros.
    Tabla en BD: despachoJudicial
    """
    ciudad = models.CharField('Ciudad', max_length=100)
    nombre = models.CharField('Nombre del Despacho', max_length=255)
    correo = models.EmailField('Correo Institucional', max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'defenjur_app_despachojudicial'
        verbose_name = 'Despacho Judicial'
        verbose_name_plural = 'Despachos Judiciales'
        ordering = ['ciudad', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.ciudad})"

class CatalogoDerechoVulnerado(models.Model):
    nombre = models.CharField('Nombre del Derecho', max_length=255, unique=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'defenjur_app_catalogoderechovulnerado'
        verbose_name = 'Catálogo de Derecho Vulnerado'
        verbose_name_plural = 'Catálogo de Derechos Vulnerados'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class CatalogoAccionado(models.Model):
    nombre = models.CharField('Nombre de Entidad/Persona', max_length=255, unique=True)
    nit = models.CharField('NIT / Código', max_length=50, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'defenjur_app_catalogoaccionado'
        verbose_name = 'Catálogo de Accionado'
        verbose_name_plural = 'Catálogo de Accionados'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

