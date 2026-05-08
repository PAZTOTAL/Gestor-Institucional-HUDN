from django.db import models
from django.conf import settings
from django.utils import timezone
from BasesGenerales.models import Formatos_Hudn

class BaseFormatModel(models.Model):
    """
    Modelo base para todos los formatos institucionales digitalizados.
    """
    formato_maestro = models.ForeignKey(
        Formatos_Hudn, 
        on_delete=models.PROTECT,
        verbose_name="Formato Maestro",
        help_text="Vínculo con el catálogo institucional de formatos"
    )
    paciente_oid = models.IntegerField(
        null=True, blank=True, 
        verbose_name="OID del Paciente (Nexus)",
        help_text="Identificador único del paciente en el sistema clínico"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Registrado Por"
    )
    ultima_modificacion = models.DateTimeField(auto_now=True, verbose_name="Última Modificación")
    
    # Metadatos técnicos
    ip_registro = models.GenericIPAddressField(null=True, blank=True)
    dispositivo = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True

class FRQUI_095_Model(BaseFormatModel):
    """
    FRQUI - 095: LISTA DE CHEQUEO INSTRUMENTACION QUIRURGICA
    """
    # Información General
    identificacion_paciente = models.CharField(max_length=50, verbose_name="Identificación Paciente")
    paciente_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre del Paciente")
    atencion_codigo = models.CharField(max_length=50, blank=True, null=True, verbose_name="N° Atención / HC")
    eps = models.CharField(max_length=200, blank=True, null=True, verbose_name="EPS")
    fecha_operacion = models.DateField(default=timezone.now, verbose_name="Fecha de Operación")
    
    # Equipo Quirúrgico
    cirujano_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Cédula Cirujano")
    cirujano_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Cirujano")
    
    ayudante_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Cédula Ayudante")
    ayudante_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Ayudante")
    
    anestesiologo_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Cédula Anestesiólogo")
    anestesiologo_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Anestesiólogo")
    
    auxiliar_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Cédula Auxiliar Circulante")
    auxiliar_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Auxiliar Circulante")
    
    # Datos Clínicos
    diagnostico = models.CharField(max_length=500, blank=True, null=True, verbose_name="Diagnóstico")
    procedimiento = models.CharField(max_length=500, blank=True, null=True, verbose_name="Procedimiento")
    
    # Sección de Chequeo (Nuevos campos según imagen)
    HERIDA_CHOICES = [
        ('LIMPIA', 'Limpia'),
        ('CONTAMINADA', 'Contaminada'),
        ('LIMPIA_CONTAMINADA', 'Limpia Contaminada'),
        ('SUCIA', 'Sucia'),
    ]
    clasificacion_herida = models.CharField(max_length=20, choices=HERIDA_CHOICES, blank=True, null=True, verbose_name="Clasificación Herida Quirúrgica")
    
    electrobisturi = models.BooleanField(default=False, verbose_name="Electrobisturí (SI/NO)")
    sitio_ubicacion_placa = models.CharField(max_length=255, blank=True, null=True, verbose_name="Sitio de ubicación de placa")
    
    # Verificación de Esterilización
    indicador_quimico = models.BooleanField(default=False, verbose_name="Indicador Químico (General)")
    indicador_quimico_interno = models.BooleanField(default=False, verbose_name="Indicador Químico Interno")
    indicador_quimico_externo = models.BooleanField(default=False, verbose_name="Indicador Químico Externo")
    indicador_biologico = models.BooleanField(default=False, verbose_name="Indicador Biológico")
    
    # Conteo de Material (Inicial y Final)
    # Usaremos campos JSON o campos específicos según la complejidad
    # Conteo de Material (Orden Oficial: Compresas, Gasas, Torundas, Pinzas, Tetras, Agujas, Cotonoides, Hoja Bisturí, Mechas, Vendas)
    # Compresas
    compresas_inicial = models.IntegerField(default=0, blank=True, null=True, verbose_name="Compresas (Inicial)")
    compresas_final = models.IntegerField(default=0, blank=True, null=True, verbose_name="Compresas (Final)")
    compresas_na = models.BooleanField(default=False, verbose_name="Compresas (N/A)")
    compresas_responsable_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Responsable Compresas")
    compresas_responsable_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Responsable Compresas")
    compresas_observacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Compresas")

    # Gasas
    gasas_inicial = models.IntegerField(default=0, blank=True, null=True, verbose_name="Gasas (Inicial)")
    gasas_final = models.IntegerField(default=0, blank=True, null=True, verbose_name="Gasas (Final)")
    gasas_na = models.BooleanField(default=False, verbose_name="Gasas (N/A)")
    gasas_responsable_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Responsable Gasas")
    gasas_responsable_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Responsable Gasas")
    gasas_observacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Gasas")

    # Torundas
    torundas_inicial = models.IntegerField(default=0, blank=True, null=True, verbose_name="Torundas (Inicial)")
    torundas_final = models.IntegerField(default=0, blank=True, null=True, verbose_name="Torundas (Final)")
    torundas_na = models.BooleanField(default=False, verbose_name="Torundas (N/A)")
    torundas_responsable_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Responsable Torundas")
    torundas_responsable_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Responsable Torundas")
    torundas_observacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Torundas")

    # Pinzas
    pinzas_inicial = models.IntegerField(default=0, blank=True, null=True, verbose_name="Pinzas (Inicial)")
    pinzas_final = models.IntegerField(default=0, blank=True, null=True, verbose_name="Pinzas (Final)")
    pinzas_na = models.BooleanField(default=False, verbose_name="Pinzas (N/A)")
    pinzas_responsable_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Responsable Pinzas")
    pinzas_responsable_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Responsable Pinzas")
    pinzas_observacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Pinzas")

    # Tetras
    tetras_inicial = models.IntegerField(default=0, blank=True, null=True, verbose_name="Tetras (Inicial)")
    tetras_final = models.IntegerField(default=0, blank=True, null=True, verbose_name="Tetras (Final)")
    tetras_na = models.BooleanField(default=False, verbose_name="Tetras (N/A)")
    tetras_responsable_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Responsable Tetras")
    tetras_responsable_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Responsable Tetras")
    tetras_observacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Tetras")

    # Agujas
    agujas_inicial = models.IntegerField(default=0, blank=True, null=True, verbose_name="Agujas (Inicial)")
    agujas_final = models.IntegerField(default=0, blank=True, null=True, verbose_name="Agujas (Final)")
    agujas_na = models.BooleanField(default=False, verbose_name="Agujas (N/A)")
    agujas_responsable_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Responsable Agujas")
    agujas_responsable_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Responsable Agujas")
    agujas_observacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Agujas")

    # Cotonoides
    cotonoides_inicial = models.IntegerField(default=0, blank=True, null=True, verbose_name="Cotonoides (Inicial)")
    cotonoides_final = models.IntegerField(default=0, blank=True, null=True, verbose_name="Cotonoides (Final)")
    cotonoides_na = models.BooleanField(default=False, verbose_name="Cotonoides (N/A)")
    cotonoides_responsable_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Responsable Cotonoides")
    cotonoides_responsable_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Responsable Cotonoides")
    cotonoides_observacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Cotonoides")

    # Hoja Bisturí
    hoja_bisturi_inicial = models.IntegerField(default=0, blank=True, null=True, verbose_name="Hoja Bisturí (Inicial)")
    hoja_bisturi_final = models.IntegerField(default=0, blank=True, null=True, verbose_name="Hoja Bisturí (Final)")
    hoja_bisturi_na = models.BooleanField(default=False, verbose_name="Hoja Bisturí (N/A)")
    hoja_bisturi_responsable_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Responsable Hoja Bisturí")
    hoja_bisturi_responsable_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Responsable Hoja Bisturí")
    hoja_bisturi_observacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Hoja Bisturí")

    # Mechas
    mechas_inicial = models.IntegerField(default=0, blank=True, null=True, verbose_name="Mechas (Inicial)")
    mechas_final = models.IntegerField(default=0, blank=True, null=True, verbose_name="Mechas (Final)")
    mechas_na = models.BooleanField(default=False, verbose_name="Mechas (N/A)")
    mechas_responsable_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Responsable Mechas")
    mechas_responsable_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Responsable Mechas")
    mechas_observacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Mechas")

    # Vendas de Gasa
    vendas_gasa_inicial = models.IntegerField(default=0, blank=True, null=True, verbose_name="Vendas de Gasa (Inicial)")
    vendas_gasa_final = models.IntegerField(default=0, blank=True, null=True, verbose_name="Vendas de Gasa (Final)")
    vendas_gasa_na = models.BooleanField(default=False, verbose_name="Vendas de Gasa (N/A)")
    vendas_gasa_responsable_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="ID Responsable Vendas de Gasa")
    vendas_gasa_responsable_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Responsable Vendas de Gasa")
    vendas_gasa_observacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Vendas de Gasa")
    
    # Otros datos
    num_personas_cirugia = models.IntegerField(verbose_name="N° de personas en cirugía incluyendo el paciente")
    puerta_cerrada = models.BooleanField(default=True, verbose_name="Se opera con puerta cerrada")
    
    # Lavado y Muestra
    lavado_zona_operatoria_por = models.CharField(max_length=200, verbose_name="Lavado Zona Operatoria Realizado por")
    descripcion_muestra = models.TextField(blank=True, null=True, verbose_name="Descripción de la muestra")
    
    # Observaciones finales
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    
    class Meta:
        db_table = "FRQUI_095_Data"
        verbose_name = "Registro FRQUI-095"
        verbose_name_plural = "Registros FRQUI-095"

    def __str__(self):
        return f"FRQUI-095 - {self.identificacion_paciente} - {self.fecha_registro.date()}"

class FRQUI_001_Model(BaseFormatModel):
    """
    FRQUI - 001: LISTA DE CHEQUEO TRASLADO DEL PACIENTE DE RECUPERACIÓN A HOSPITALIZACIÓN O AMBULATORIO
    """
    # Información General
    identificacion_paciente = models.CharField(max_length=50, verbose_name="Identificación Paciente")
    paciente_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre del Paciente")
    atencion_codigo = models.CharField(max_length=50, blank=True, null=True, verbose_name="N° Atención / HC")
    eps = models.CharField(max_length=200, blank=True, null=True, verbose_name="EPS")
    hora_egreso = models.TimeField(default=timezone.now, verbose_name="Hora de Egreso")
    
    SI_NO_NA_CHOICES = [
        ('SI', 'SI'),
        ('NO', 'NO'),
        ('NA', 'NA'),
    ]

    # SECCIÓN 1: REQUISITOS PARA EL TRASLADO
    # 1. Camilla de transporte disponible...
    camilla_transporte_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Camilla disponible")
    camilla_transporte_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Camilla")
    
    # 2. Confirma identificación con manilla...
    confirma_identificacion_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Confirma identificación")
    confirma_identificacion_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Identificación")
    
    # 3. En caso de cesárea verificar identificación materna...
    cesarea_identificacion_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Identificación materna (Cesárea)")
    cesarea_identificacion_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Cesárea")
    
    # 4. Puntaje de escala de ALDRETE entre 8 y 10
    puntaje_aldrete_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Escala ALDRETE")
    puntaje_aldrete_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación ALDRETE")
    
    # 5. Puntaje de escala de BROMAGE (fuerza motora completa - 0)
    puntaje_bromage_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Escala BROMAGE")
    puntaje_bromage_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación BROMAGE")
    
    # 6. Escala de dolor con puntuación de 4 o menos
    escala_dolor_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Escala Dolor")
    escala_dolor_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Dolor")
    
    # 7. Se encuentra en buenas condiciones clínicas para su traslado.
    condiciones_clinicas_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Condiciones clínicas")
    condiciones_clinicas_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Condiciones")
    
    # 8. Plan de tratamiento médico iniciado y registrado
    plan_tratamiento_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Plan tratamiento")
    plan_tratamiento_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Plan")
    
    # 9. Kardex y tarjetas de medicamentos
    kardex_tarjetas_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Kardex y tarjetas")
    kardex_tarjetas_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Kardex")
    
    # 10. Paciente comentado telefónicamente a enfermera del servicio
    paciente_comentado_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Paciente comentado")
    paciente_comentado_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Comentado")
    
    # 11. Acceso venoso permeable y rotulado, sin signos de flebitis.
    acceso_venoso_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Acceso venoso")
    acceso_venoso_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Acceso")
    
    # 12. Herida quirúrgica cubierta y seca, sin evidencia de hemorragias...
    herida_quirurgica_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Herida quirúrgica")
    herida_quirurgica_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Herida")
    
    # 13. Tubos, drenes, sonda vesical permeable y debidamente rotulado.
    tubos_drenes_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Tubos y drenes")
    tubos_drenes_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Tubos")
    
    # 14. Limpieza e integridad de la piel
    limpieza_piel_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Limpieza piel")
    limpieza_piel_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación Piel")
    
    # 15. Cuidados especiales:
    cuidados_especiales = models.TextField(blank=True, null=True, verbose_name="Cuidados Especiales")
    
    # Responsables Traslado
    auxiliar_entrega_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="Cédula Auxiliar Entrega")
    auxiliar_entrega_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Auxiliar que Entrega")
    auxiliar_recibe_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="Cédula Auxiliar Recibe")
    auxiliar_recibe_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Auxiliar que Recibe")

    # SECCIÓN 2: ENTREGA HISTORIA CLINICA COMPLETA
    # 1. Descripción operatoria.
    historia_descripcion_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Descripción operatoria")
    historia_descripcion_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Descripción")
    
    # 2. Record de Anestesia.
    historia_anestesia_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Record Anestesia")
    historia_anestesia_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Anestesia")
    
    # 3. Escala de ALDRETE / BROMAGE, ESCALA DEL DOLOR.
    historia_escalas_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Escalas HC")
    historia_escalas_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Escalas")
    
    # 4. Fórmula médica.
    historia_formula_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Fórmula médica HC")
    historia_formula_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Fórmula")
    
    # 5. Consentimiento Informado.
    historia_consentimiento_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Consentimiento HC")
    historia_consentimiento_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Consentimiento")
    
    # 6. Entregar Triple tarjeta.
    historia_triple_tarjeta_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Triple tarjeta HC")
    historia_triple_tarjeta_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Triple tarjeta")
    
    # 7. Lista de chequeo de Instrumentación Quirúrgica.
    historia_lista_instrumentacion_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Lista Instrumentación HC")
    historia_lista_instrumentacion_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Lista")
    
    # Responsables Enfermería
    enfermeria_entrega_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="Cédula Enfermería Entrega")
    enfermeria_entrega_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Enfermería que Entrega")
    enfermeria_recibe_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="Cédula Enfermería Recibe")
    enfermeria_recibe_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Enfermería que Recibe")

    # SECCIÓN 3: AMBULATORIO
    # 1. Informar el nombre del médico quien realizo la intervención.
    amb_nombre_medico_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Informar nombre médico")
    amb_nombre_medico_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Nombre médico")
    
    # 2. Informar fecha y hora del control por consulta externa.
    amb_fecha_control_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Informar fecha control")
    amb_fecha_control_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Fecha control")
    
    # 3. Entrega fórmula médica y explicar nombre de medicamentos...
    amb_formula_explicacion_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Entrega y explica fórmula")
    amb_formula_explicacion_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Fórmula Ambulatorio")
    
    # 4. Explicar cuidados generales a tener en casa...
    amb_cuidados_casa_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Explicar cuidados casa")
    amb_cuidados_casa_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Cuidados casa")
    
    # 5. Hacer entrega de instructivo de cuidados en casa.
    amb_instructivo_cuidados_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Entrega instructivo")
    amb_instructivo_cuidados_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Instructivo")
    
    # 6. Explicar y entregar lista de recomendaciones, signos de alarma.
    amb_recomendaciones_alarmas_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Explicar recomendaciones")
    amb_recomendaciones_alarmas_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Recomendaciones")
    
    # 7. Entregar rayos X, ecografías y demas documentos...
    amb_rayos_x_otros_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Entregar RX y otros")
    amb_rayos_x_otros_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. RX y otros")
    
    # 8. Entregar Triple tarjeta
    amb_triple_tarjeta_status = models.CharField(max_length=2, choices=SI_NO_NA_CHOICES, default='NA', verbose_name="Entregar Triple tarjeta AMB")
    amb_triple_tarjeta_obs = models.CharField(max_length=255, blank=True, null=True, verbose_name="Obs. Triple tarjeta AMB")
    
    # Firmas Finales
    firma_usuario_familiar = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Usuario o Familiar")
    firma_enfermera_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="Cédula Enfermera")
    firma_enfermera_nombre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre Enfermera")

    class Meta:
        db_table = "FRQUI_001_Data"
        verbose_name = "Registro FRQUI-001"
        verbose_name_plural = "Registros FRQUI-001"

    def __str__(self):
        return f"FRQUI-001 - {self.identificacion_paciente} - {self.fecha_registro.date()}"
