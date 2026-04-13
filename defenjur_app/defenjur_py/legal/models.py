from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone as django_timezone

class Usuario(AbstractUser):
    nick = models.CharField(max_length=120, unique=True, null=True, blank=True)
    rol = models.CharField(max_length=120)
    estado = models.IntegerField(default=1)
    
    def __str__(self):
        return self.username

class ProcesoExtrajudicial(models.Model):
    demandante = models.CharField(max_length=255)
    demandado = models.CharField(max_length=255)
    apoderado = models.CharField(max_length=255)
    medio_control = models.CharField(max_length=255)
    despacho_conocimiento = models.TextField()
    estado = models.CharField(max_length=120)
    clasificacion = models.CharField(max_length=120, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Procesos Extrajudiciales"

class ProcesoJudicialActiva(models.Model):
    num_proceso = models.CharField('N° proceso', max_length=255, null=True, blank=True)
    fecha_registro = models.DateTimeField('Fecha registro', auto_now_add=True)
    medio_control = models.CharField(
        'Medio de control', max_length=255, null=True, blank=True,
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
        verbose_name = 'Proceso judicial activo'
        verbose_name_plural = 'Procesos Judiciales Activos'

class ProcesoJudicialPasiva(models.Model):
    num_proceso = models.CharField('N° proceso', max_length=255, null=True, blank=True)
    fecha_registro = models.DateTimeField('Fecha registro', auto_now_add=True)
    medio_control = models.CharField(
        'Medio de control', max_length=255, null=True, blank=True,
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
        verbose_name = 'Proceso judicial pasivo'
        verbose_name_plural = 'Procesos Judiciales Pasivos'

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

    class Meta:
        verbose_name = 'Derecho de petición'
        verbose_name_plural = 'Derechos de Petición'

class AccionTutela(models.Model):
    fecha_llegada = models.CharField(max_length=255, null=True, blank=True)
    num_reparto = models.CharField(max_length=255, null=True, blank=True)
    fecha_reparto = models.CharField(max_length=255, null=True, blank=True)
    # Alineados con el formato tipo “Derechos de Petición” (Excel / trazabilidad interna)
    fecha_correo = models.CharField(max_length=255, null=True, blank=True)
    solicitante = models.CharField(max_length=255, null=True, blank=True)
    peticionario = models.CharField(max_length=255, null=True, blank=True)
    causa = models.TextField(null=True, blank=True)
    num_proceso = models.CharField(max_length=255, null=True, blank=True)
    despacho_judicial = models.CharField(max_length=255, null=True, blank=True)
    area_responsable = models.CharField(max_length=255, null=True, blank=True)
    accionante = models.CharField(max_length=255, null=True, blank=True)
    tipo_identificacion_accionante = models.CharField(max_length=120, null=True, blank=True)
    identificacion_accionante = models.CharField(max_length=120, null=True, blank=True)
    accionado = models.CharField(max_length=255, null=True, blank=True)
    vinculados = models.TextField(null=True, blank=True)
    objeto_tutela = models.TextField(null=True, blank=True)
    asunto_tutela = models.TextField(null=True, blank=True)
    abogado_responsable = models.CharField(max_length=255, null=True, blank=True)
    tipo_tramite = models.CharField(max_length=255, null=True, blank=True)
    termino_dar_tramite = models.CharField(max_length=255, null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    tramite_impartido = models.TextField(null=True, blank=True)
    fecha_respuesta_tramite = models.CharField(max_length=255, null=True, blank=True)
    rad_interno_arch_central = models.CharField(max_length=255, null=True, blank=True)
    fecha_fallo_primera_instancia = models.CharField(max_length=255, null=True, blank=True)
    fallo_primera_instancia = models.TextField(null=True, blank=True)
    impugnacion = models.CharField(max_length=255, null=True, blank=True)
    fecha_impugnacion = models.CharField(max_length=255, null=True, blank=True)
    fecha_fallo_segunda_instancia = models.CharField(max_length=255, null=True, blank=True)
    fallo_segunda_instancia = models.TextField(null=True, blank=True)
    desacato = models.CharField(max_length=255, null=True, blank=True)
    fecha_tramite_desacato = models.CharField(max_length=255, null=True, blank=True)
    respuesta_incidente_desacato = models.TextField(null=True, blank=True)
    rad_interno = models.CharField(max_length=255, null=True, blank=True)
    fallo_desacato = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Acciones de Tutela"

class ArchivoAdjunto(models.Model):
    tipo_asociado = models.CharField(max_length=100)
    id_asociado = models.IntegerField()
    archivo = models.FileField(upload_to='adjuntos/%Y/%m/%d/')
    nombre_original = models.CharField(max_length=255)
    fecha_carga = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo_asociado} - {self.nombre_original}"

# ─── Nuevos modelos ───────────────────────────────────────────────────────────

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
        verbose_name = 'Peritaje'
        verbose_name_plural = 'Peritajes'

class PagoSentenciaJudicial(models.Model):
    num_proceso = models.CharField('N° proceso', max_length=255, null=True, blank=True)
    despacho_tramitante = models.CharField(
        'Despacho tramitante', max_length=255, null=True, blank=True,
    )
    medio_control = models.CharField(
        'Medio de control', max_length=255, null=True, blank=True,
    )
    demandante = models.CharField('Demandante', max_length=255, null=True, blank=True)
    demandado = models.CharField('Demandado', max_length=255, null=True, blank=True)
    valor_pagado = models.CharField('Valor pagado', max_length=255, null=True, blank=True)
    estado = models.CharField('Estado', max_length=255, null=True, blank=True)
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
        verbose_name = 'Pago de sentencia judicial'
        verbose_name_plural = 'Pagos de Sentencias Judiciales'

class ProcesoJudicialTerminado(models.Model):
    num_proceso = models.CharField('N° proceso', max_length=255, null=True, blank=True)
    medio_control = models.CharField(
        'Medio de control', max_length=255, null=True, blank=True,
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
        verbose_name = 'Proceso judicial terminado'
        verbose_name_plural = 'Procesos Judiciales Terminados'

class ProcesoAdministrativoSancionatorio(models.Model):
    num_proceso = models.CharField('N° proceso', max_length=255, null=True, blank=True)
    entidad = models.CharField('Entidad', max_length=255, null=True, blank=True)
    causa = models.TextField('Causa', null=True, blank=True)
    estado = models.CharField('Estado', max_length=120, null=True, blank=True)
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
        verbose_name = 'Proceso administrativo sancionatorio'
        verbose_name_plural = 'Procesos Administrativos Sancionatorios'

class RequerimientoEnteControl(models.Model):
    """Orden de campos alineado a la grilla Excel (ID automático + columnas principales primero)."""
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
        verbose_name = 'Requerimiento de ente de control'
        verbose_name_plural = 'Requerimientos de Entes de Control'
