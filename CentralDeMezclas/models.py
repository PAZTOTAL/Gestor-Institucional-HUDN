from django.db import models
from django.utils import timezone

class MezclaOrden(models.Model):
    TIPOS_MEZCLA = [
        ('NPT', 'Nutrición Parenteral Total'),
        ('ATB', 'Antibióticos Reconstituidos'),
        ('ONC', 'Medicamentos Oncológicos'),
        ('AJU', 'Ajuste de Dosis Específicas'),
    ]
    
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de Verificación'),
        ('VERIFICADA', 'Validada por Farmacéutico'),
        ('PREPARANDO', 'En Proceso de Mezcla'),
        ('CONTROLADA', 'Control de Calidad Aprobado'),
        ('DISTRIBUIDA', 'Entregada a Servicio'),
        ('CANCELADA', 'Cancelada'),
    ]

    PRIORIDADES = [
        ('NORMAL', 'Normal'),
        ('URGENTE', 'Urgente'),
        ('STAT', 'Inmediata (STAT)'),
    ]

    # Referencias a bases externas
    paciente_oid = models.IntegerField(verbose_name="OID Paciente")
    medico_oid = models.IntegerField(verbose_name="OID Médico Solicitante")
    
    tipo_mezcla = models.CharField(max_length=3, choices=TIPOS_MEZCLA, verbose_name="Tipo de Mezcla")
    descripcion_medicamento = models.TextField(verbose_name="Medicamento y Dosis Solicitada")
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default='NORMAL')
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    observaciones_clinicas = models.TextField(blank=True, null=True)

    # Validación ORDEN MÉDICA (FRFAR-156)
    validado_por = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='ordenes_validadas', verbose_name="Validado por (QF)")
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    
    # 12 Criterios de Validación
    criterio_prestador = models.BooleanField(default=True, verbose_name="1. Nombre prestador/profesional")
    criterio_lugar_fecha = models.BooleanField(default=True, verbose_name="2. Lugar, fecha, período")
    criterio_paciente = models.BooleanField(default=True, verbose_name="3. Nombre paciente, ID, historia")
    criterio_tipo_usuario = models.BooleanField(default=True, verbose_name="4. Tipo de usuario")
    criterio_dci = models.BooleanField(default=True, verbose_name="5. Nombre genérico DCI")
    criterio_concentracion = models.BooleanField(default=True, verbose_name="6. Concentración, forma, dosis")
    criterio_via_frecuencia = models.BooleanField(default=True, verbose_name="7. Vía y frecuencia")
    criterio_cantidad = models.BooleanField(default=True, verbose_name="8. Cantidad total unidades")
    criterio_indicaciones = models.BooleanField(default=True, verbose_name="9. Indicaciones, firma, registro")
    criterio_legibilidad = models.BooleanField(default=True, verbose_name="10. Letra legible, sin tachones")
    criterio_periodo = models.BooleanField(default=True, verbose_name="11. Período duración tratamiento")
    criterio_vigencia = models.BooleanField(default=True, verbose_name="12. Vigencia prescripción")

    class Meta:
        verbose_name = "Orden de Mezcla"
        verbose_name_plural = "Órdenes de Mezcla"
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Orden {self.id} - {self.get_tipo_mezcla_display()} - Paciente OID {self.paciente_oid}"

class MezclaPreparacion(models.Model):
    orden = models.OneToOneField(MezclaOrden, on_delete=models.CASCADE, related_name='preparacion')
    lote_interno = models.CharField(max_length=50, unique=True, verbose_name="Lote de Preparación")
    farmaceutico_oid = models.IntegerField(verbose_name="OID Farmacéutico Responsable")
    cabina_id = models.CharField(max_length=50, verbose_name="Identificación de Cabina/Flujo Laminar")
    
    insumos_utilizados = models.TextField(default="{}", verbose_name="Detalle de Insumos y Cantidades")
    
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    
    tecnico_preparador = models.CharField(max_length=100, verbose_name="Nombre del Técnico Preparador")
    
    # Roles de Producción (Trazabilidad)
    jefe_produccion = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='preparaciones_jefe', verbose_name="Jefe de Producción")
    qf_preparador = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='preparaciones_qf', verbose_name="QF Preparador")
    alistamiento_por = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='preparaciones_alistamiento', verbose_name="Alistamiento por")
    director_tecnico = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='preparaciones_director', verbose_name="Director Técnico")

    # Campos Técnicos FRFAR-177
    viales_ampollas = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Viales/Ampollas")
    solucion_diluyente = models.CharField(max_length=255, blank=True, null=True, verbose_name="Solución Diluyente")
    volumen_dilucion = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Volumen Dilución (mL)")
    volumen_dosis = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Volumen Dosis (mL)")
    vehiculo_volumen_final = models.CharField(max_length=255, blank=True, null=True, verbose_name="Vehículo y Vol. Final")

    class Meta:
        verbose_name = "Preparación de Mezcla"
        verbose_name_plural = "Preparaciones de Mezcla"

class MezclaControlCalidad(models.Model):
    preparacion = models.OneToOneField(MezclaPreparacion, on_delete=models.CASCADE, related_name='control')
    
    visual_ok = models.BooleanField(default=False, verbose_name="Inspección Visual Correcta")
    etiquetado_ok = models.BooleanField(default=False, verbose_name="Etiquetado y Trazabilidad Correcta")
    hermeticidad_ok = models.BooleanField(default=False, verbose_name="Cierre Hermético Verificado")
    
    valoracion_final = models.TextField(blank=True, null=True, verbose_name="Observaciones de Calidad")
    aprobado = models.BooleanField(default=False)
    
    fecha_control = models.DateTimeField(auto_now_add=True)
    controlador_oid = models.IntegerField(verbose_name="OID del Validador de Calidad", null=True, blank=True)
    
    # Roles de Calidad (Trazabilidad FRFAR-187)
    verificado_por = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='controles_verificados', verbose_name="Verificado por")
    aprobado_por = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='controles_aprobados', verbose_name="Aprobado por (Jefe Calidad)")

    # Control de Calidad Detallado (FRFAR-187)
    # Control Inicial (CI)
    ci_particulas_extranas = models.BooleanField(default=True, verbose_name="CI: Ausencia de partículas extrañas")
    ci_concordancia_op = models.BooleanField(default=True, verbose_name="CI: Concordancia con OP")
    ci_fugas = models.BooleanField(default=True, verbose_name="CI: Sin fugas")
    
    # Control Final (CF)
    cf_etiqueta_ok = models.BooleanField(default=True, verbose_name="CF: Etiqueta correcta (Paciente/Lote/Vence)")
    cf_hermeticidad = models.BooleanField(default=True, verbose_name="CF: Hermeticidad y sellado ok")
    cf_limpieza = models.BooleanField(default=True, verbose_name="CF: Envase limpio sin roturas")

    class Meta:
        verbose_name = "Control de Calidad"
        verbose_name_plural = "Controles de Calidad"

class MezclaDistribucion(models.Model):
    preparacion = models.OneToOneField(MezclaPreparacion, on_delete=models.CASCADE, related_name='distribucion')
    
    servicio_destino = models.CharField(max_length=100, verbose_name="Servicio de Destino (UCI, ONCO, etc.)")
    responsable_recibe = models.CharField(max_length=150, verbose_name="Nombre de quien recibe en Servicio")
    
    fecha_entrega = models.DateTimeField(default=timezone.now)
    entregado_por_oid = models.IntegerField(verbose_name="OID Personal que entrega")

    class Meta:
        verbose_name = "Distribución de Mezcla"
        verbose_name_plural = "Distribuciones de Mezcla"


# --- MÓDULO DE REEMPAQUE Y REENVASE (RV-RS) ---
class ConvencionFormaFarmaceutica(models.Model):
    """Módulos de Reempaque - Forma Farmacéutica y Vía (FRFAR-090)"""
    forma_farmaceutica = models.CharField(max_length=100, verbose_name="Forma Farmacéutica")
    via = models.CharField(max_length=100, verbose_name="Vía de administración")

    def __str__(self):
        return f"{self.forma_farmaceutica} ({self.via})"

class Alerta(models.Model):
    """Módulos de Reempaque - Alertas con Color y Código (FRFAR-090)"""
    color = models.CharField(max_length=50, verbose_name="Color")
    codigo = models.CharField(max_length=50, verbose_name="Código")

    def __str__(self):
        return f"{self.codigo} - {self.color}"

class ReempaqueMedicamento(models.Model):
    """Módulos de Reempaque - Catálogo de Medicamentos (FRFAR-089)"""
    nombre = models.CharField(max_length=255, verbose_name="Medicamento")
    concentracion = models.CharField(max_length=100, verbose_name="CONCENTRACION")
    convencion = models.ForeignKey(ConvencionFormaFarmaceutica, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Forma y Vía")
    alerta = models.ForeignKey(Alerta, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Alerta / Semaforización")
    condiciones_almacenamiento = models.CharField(max_length=255, verbose_name="Temperatura Y Humedad")
    fotosensibilidad = models.CharField(max_length=50, verbose_name="Fotosensibilidad")

    class Meta:
        verbose_name = "Medicamento para Reempaque"
        verbose_name_plural = "Medicamentos para Reempaque"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} {self.concentracion}"

class ReempaqueOrden(models.Model):
    """Orden de Producción Reempaque y Reenvase (FRFAR-184)"""
    medicamento = models.ForeignKey(ReempaqueMedicamento, on_delete=models.PROTECT, related_name='ordenes')
    lote_interno = models.CharField(max_length=50, unique=True, verbose_name="Lote Interno (REE...)")
    lote_fabricante = models.CharField(max_length=50, verbose_name="Lote del Fabricante")
    laboratorio = models.CharField(max_length=100, verbose_name="Laboratorio", blank=True, null=True)
    registro_invima = models.CharField(max_length=100, verbose_name="Registro INVIMA", blank=True, null=True)
    
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento Original")
    fecha_vencimiento_reempaque = models.DateField(verbose_name="Vencimiento Post-Reempaque")
    
    cantidad_a_reempacar = models.IntegerField(verbose_name="Cantidad Inicial")
    cantidad_final_aprobada = models.IntegerField(null=True, blank=True, verbose_name="Cantidad Final Aprobada")
    
    semaforizacion = models.CharField(max_length=50, verbose_name="Semaforización", blank=True, null=True)
    
    fecha_produccion = models.DateTimeField(default=timezone.now)
    responsable_reempaque = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='reempaques_responsable', verbose_name="Responsable de Reempaque")
    farmaceutico_validador = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='reempaques_validador', verbose_name="Farmacéutico Validador")
    
    TIPO_CHOICES = [
        ('REEMPAQUE', 'Reempaque (Sólidos)'),
        ('REENVASE', 'Reenvase (Líquidos/Semisólidos)'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='REEMPAQUE', verbose_name="Tipo de Proceso")
    
    estado = models.CharField(max_length=20, choices=[
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('CONTROL_CALIDAD', 'En Control de Calidad'),
        ('LIBERADO', 'Liberado'),
        ('RECHAZADO', 'Rechazado')
    ], default='PENDIENTE')

    class Meta:
        verbose_name = "Orden de Reempaque"
        verbose_name_plural = "Órdenes de Reempaque"
        ordering = ['-fecha_produccion']

    def __str__(self):
        return f"OP {self.lote_interno} - {self.medicamento.nombre}"

class ReempaqueControl(models.Model):
    """Control de Calidad y Liberación (FRFAR-188)"""
    orden = models.OneToOneField(ReempaqueOrden, on_delete=models.CASCADE, related_name='control_calidad')
    
    # Pruebas de Calidad
    aspecto_fisico_ok = models.BooleanField(default=False, verbose_name="Aspecto Físico Correcto")
    hermeticidad_ok = models.BooleanField(default=False, verbose_name="Hermeticidad Verificada")
    etiquetado_completo_ok = models.BooleanField(default=False, verbose_name="Etiquetado con Info Completa")
    limpieza_area_ok = models.BooleanField(default=False, verbose_name="Limpieza de Área Verificada")
    
    unidades_defectuosas = models.IntegerField(default=0, verbose_name="Unidades Defectuosas Halladas")
    observaciones_calidad = models.TextField(blank=True, null=True)
    
    liberado = models.BooleanField(default=False, verbose_name="Producto Liberado")
    fecha_liberacion = models.DateTimeField(null=True, blank=True)
    responsable_liberacion = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='reempaques_liberacion', verbose_name="Responsable Liberación (QF)")

    class Meta:
        verbose_name = "Control de Calidad Reempaque"
        verbose_name_plural = "Controles de Calidad Reempaque"

class ReempaqueMuestreo(models.Model):
    """Muestreo basado en MIL-STD-105E (FRFAR-092)"""
    orden = models.ForeignKey(ReempaqueOrden, on_delete=models.CASCADE, related_name='muestreos')
    tamano_lote = models.IntegerField()
    nivel_inspeccion = models.CharField(max_length=10, default='II', verbose_name="Nivel de Inspección")
    letra_codigo = models.CharField(max_length=5, verbose_name="Letra Código")
    tamano_muestra = models.IntegerField(verbose_name="Tamaño de la Muestra")
    
    ac = models.IntegerField(verbose_name="Número de Aceptación (Ac)")
    re = models.IntegerField(verbose_name="Número de Rechazo (Re)")
    
    fecha_muestreo = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def obtener_plan(n_lote):
        """
        Retorna (Letra, Tamaño Muestra, Ac, Re) basado en MIL-STD-105E Nivel II Normal.
        Simplificado para rangos comunes en reempaque hospitalario.
        """
        if 2 <= n_lote <= 8: return ('A', 2, 0, 1)
        if 9 <= n_lote <= 15: return ('B', 3, 0, 1)
        if 16 <= n_lote <= 25: return ('C', 5, 0, 1)
        if 26 <= n_lote <= 50: return ('D', 8, 0, 1)
        if 51 <= n_lote <= 90: return ('E', 13, 0, 1)
        if 91 <= n_lote <= 150: return ('F', 20, 1, 2)
        if 151 <= n_lote <= 280: return ('G', 32, 2, 3)
        if 281 <= n_lote <= 500: return ('H', 50, 3, 4)
        if 501 <= n_lote <= 1200: return ('J', 80, 5, 6)
        return ('K', 125, 7, 8) # Lotes muy grandes

    class Meta:
        verbose_name = "Muestreo de Calidad"
        verbose_name_plural = "Muestreos de Calidad"

# --- MODELOS DE CONVENCIONES Y ALERTAS (USADOS EN REEMPAQUE) ---

class MedicamentoEsteril(models.Model):
    """Base de Datos Medicamentos Estériles (Maestro de Preparaciones)"""
    codigo = models.CharField(max_length=50, verbose_name="COD.")
    medicamento_1 = models.CharField(max_length=255, verbose_name="MEDICAMENTO 1")
    medicamento_2 = models.CharField(max_length=255, null=True, blank=True, verbose_name="MEDICAMENTO 2")
    
    concentracion_1 = models.CharField(max_length=100, verbose_name="CONCENTRACION MED 1")
    concentracion_2 = models.CharField(max_length=100, null=True, blank=True, verbose_name="CONCENTRACION MED 2")
    
    dosis_estandar = models.CharField(max_length=255, verbose_name="DOSIS ESTANDAR")
    dosis_frecuencia = models.CharField(max_length=255, verbose_name="DOSIS Y FRECUENCIA")
    
    dosis_med_1 = models.CharField(max_length=100, verbose_name="DOSIS MED 1")
    dosis_med_2 = models.CharField(max_length=100, null=True, blank=True, verbose_name="DOSIS MED 2")
    
    vol_reconstitucion_1 = models.CharField(max_length=100, verbose_name="VOL. RECONSTITUCION MED 1")
    vol_reconstitucion_2 = models.CharField(max_length=100, null=True, blank=True, verbose_name="VOL. RECONSTITUCION MED 2")
    
    cantidad_necesaria = models.CharField(max_length=100, verbose_name="CANTIDAD NECESARIA")
    
    diluyente = models.CharField(max_length=255, null=True, blank=True, verbose_name="DILUYENTE")
    cod_diluyente = models.CharField(max_length=50, null=True, blank=True, verbose_name="COD. DIL.")
    
    via = models.CharField(max_length=50, verbose_name="VIA")
    vehiculo_final = models.CharField(max_length=255, verbose_name="VEHICULO FINAL")
    
    jeringa = models.CharField(max_length=255, verbose_name="JERINGA")
    agua_hipodermica = models.CharField(max_length=255, verbose_name="AGUA HIPODERMICA")
    
    almacenamiento = models.CharField(max_length=255, verbose_name="ALMACENAMIENTO")
    es_control_especial = models.BooleanField(default=False, verbose_name="ACE (Control Especial)")
    manejo_especial = models.CharField(max_length=255, null=True, blank=True, verbose_name="OBSERVACIONES / MANEJO")
    
    fecha_preparacion = models.CharField(max_length=50, null=True, blank=True, verbose_name="FECHA PREPARACIÓN")
    
    cod_med_1 = models.CharField(max_length=50, verbose_name="COD. MED 1")
    cod_med_2 = models.CharField(max_length=50, null=True, blank=True, verbose_name="COD. MED 2")

    # Seguridad del Paciente
    lasa = models.BooleanField(default=False, verbose_name="LASA")
    alto_riesgo = models.BooleanField(default=False, verbose_name="ALTO RIESGO")

    # Campos de Validación (Solicitados)
    elaborado_por = models.CharField(max_length=150, verbose_name="ELABORADO POR", default="Q.F. ELBERT MUÑOZ")
    verificado_por = models.CharField(max_length=150, verbose_name="VERIFICADO POR", default="PILAR GALLARDO")

    class Meta:
        verbose_name = "Medicamento Estéril (Base)"
        verbose_name_plural = "Medicamentos Estériles (Base)"
        ordering = ['medicamento_1']

    def __str__(self):
        return f"{self.codigo} - {self.medicamento_1}"

class Funcionario(models.Model):
    """Catálogo de Funcionarios (Personal)"""
    cedula = models.CharField(max_length=20, unique=True, verbose_name="CÉDULA")
    nombre_completo = models.CharField(max_length=255, verbose_name="NOMBRE COMPLETO")
    cargo = models.CharField(max_length=150, verbose_name="CARGO", blank=True, null=True)
    activo = models.BooleanField(default=True, verbose_name="ACTIVO")

    class Meta:
        verbose_name = "Funcionario"
        verbose_name_plural = "Funcionarios"
        ordering = ['nombre_completo']

    def __str__(self):
        return f"{self.cedula} - {self.nombre_completo}"

class UnidosisPeriodo(models.Model):
    """Encabezado de Producción Diaria (Matriz Unidosis)"""
    fecha = models.DateField(default=timezone.now)
    orden_produccion = models.CharField(max_length=50, unique=True, verbose_name="ORDEN DE PRODUCCIÓN")
    
    jefe_produccion = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='periodos_jefe_prod', verbose_name="JEFE DE PRODUCCIÓN")
    qf_preparador = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='periodos_qf_prep', verbose_name="QF PREPARADOR")
    alistamiento = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='periodos_alistamiento', verbose_name="ALISTAMIENTO")
    
    jefe_calidad = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='periodos_jefe_calidad', verbose_name="JEFE DE C. CALIDAD")
    registrado_por = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='periodos_registrado', verbose_name="REGISTRADO POR")
    digitador = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='periodos_digitador', verbose_name="DIGITADOR")
    
    director_tecnico = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='periodos_director', verbose_name="DIRECTOR TÉCNICO")
    preelaboracion = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='periodos_preelab', verbose_name="PREELABORACIÓN")

    class Meta:
        verbose_name = "Periodo de Producción Unidosis"
        verbose_name_plural = "Periodos de Producción Unidosis"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.orden_produccion} ({self.fecha})"

class UnidosisOrden(models.Model):
    """Fila de la Matriz de Producción Unidosis"""
    periodo = models.ForeignKey(UnidosisPeriodo, on_delete=models.CASCADE, related_name='ordenes')
    lote_interno = models.CharField(max_length=50, verbose_name="LOTE INTERNO")
    
    # Datos del Paciente
    paciente_nombre = models.CharField(max_length=255, verbose_name="NOMBRE DEL PACIENTE")
    paciente_identificacion = models.CharField(max_length=50, verbose_name="IDENTIFICACION")
    cama = models.CharField(max_length=20, verbose_name="CAMA")
    servicio = models.CharField(max_length=100, verbose_name="SERVICIO")
    
    # Referencia al Medicamento Base (Catálogo)
    medicamento_base = models.ForeignKey(MedicamentoEsteril, on_delete=models.PROTECT, verbose_name="MEDICAMENTO")
    
    # Datos que suelen venir del catálogo pero que pueden variar
    dosis_estandar_pme = models.CharField(max_length=255, verbose_name="MEDICAMENTO+DOSIS ESTANDAR PME")
    dosis_frecuencia = models.CharField(max_length=255, verbose_name="DOSIS Y FRECUENCIA")
    sln_diluyente = models.CharField(max_length=255, verbose_name="SLN DILUYENTE")
    volumen_dilucion = models.CharField(max_length=100, verbose_name="VOLUMEN DILUCION")
    vehiculo_volumen_final = models.CharField(max_length=255, verbose_name="VEHICULO Y VOLUMEN FINAL")
    via = models.CharField(max_length=50, verbose_name="VIA")
    frecuencia = models.CharField(max_length=100, verbose_name="FRECUENCIA")
    
    # Datos Operativos
    cantidad_necesaria = models.CharField(max_length=50, verbose_name="CANTIDAD NECESARIA")
    volumen_dosis = models.CharField(max_length=50, verbose_name="VOLUMEN DOSIS")
    fecha_expiracion = models.DateTimeField(verbose_name="FECHA DE EXPIRACIÓN")
    
    # Almacenamiento
    temp_almacenamiento = models.CharField(max_length=50, default="2-8 °C", verbose_name="T°")
    luz_almacenamiento = models.CharField(max_length=50, default="PROTEGER LUZ", verbose_name="LUZ")

    class Meta:
        verbose_name = "Orden Unidosis Adultos"
        verbose_name_plural = "Órdenes Unidosis Adultos"

    def __str__(self):
        return f"{self.lote_interno} - {self.paciente_nombre}"


# --- MÓDULO MEDICAMENTOS ONCOLÓGICOS ALTA COMPLEJIDAD (FRFAR-126) ---

class MedicamentoOncologico(models.Model):
    """Base de Datos Medicamentos Oncológicos Alta Complejidad (FRFAR-126)"""
    cod = models.IntegerField(verbose_name="COD.", null=True, blank=True)
    producto = models.CharField(max_length=255, verbose_name="PRODUCTO")
    medicamento = models.CharField(max_length=255, verbose_name="MEDICAMENTO")
    concentracion = models.CharField(max_length=100, verbose_name="CONCENTRACIÓN (mg, UI)")
    forma_farmaceutica = models.CharField(max_length=100, verbose_name="FORMA FARMACÉUTICA")

    # Reconstitución
    volumen_reconstitucion = models.CharField(max_length=100, verbose_name="VOLUMEN DE RECONSTITUCIÓN", null=True, blank=True)
    solucion_reconstitucion = models.CharField(max_length=255, verbose_name="SOLUCIÓN DE RECONSTITUCIÓN", null=True, blank=True)
    cod_dil = models.CharField(max_length=50, verbose_name="COD. DIL.", null=True, blank=True)

    # Administración
    administracion = models.CharField(max_length=50, verbose_name="ADMINISTRACIÓN")
    vol_final = models.CharField(max_length=100, verbose_name="VOL. FINAL (mL)", null=True, blank=True)
    vehiculo = models.CharField(max_length=255, verbose_name="VEHÍCULO", null=True, blank=True)

    # Dispositivos
    jeringa = models.CharField(max_length=255, verbose_name="JERINGA", null=True, blank=True)
    aguja = models.CharField(max_length=255, verbose_name="AGUJA", null=True, blank=True)

    # Almacenamiento y expiración
    almacenamiento = models.CharField(max_length=255, verbose_name="ALMACENAMIENTO", null=True, blank=True)
    es_control_especial = models.BooleanField(default=False, verbose_name="ACE (Control Especial)")
    proteccion_luz = models.CharField(max_length=255, verbose_name="PROTECCIÓN LUZ / OBSERVACIONES", null=True, blank=True)
    fecha_expiracion = models.CharField(max_length=100, verbose_name="FECHA DE EXPIRACIÓN", null=True, blank=True)

    class Meta:
        verbose_name = "Medicamento Oncológico (Base)"
        verbose_name_plural = "Medicamentos Oncológicos Alta Complejidad (Base)"
        ordering = ['medicamento']

    def __str__(self):
        return f"{self.cod} - {self.medicamento} {self.concentracion}"


# --- FRFAR-127 MATRIZ ONCOLÓGICOS ---

class OncologicoMatriz(models.Model):
    """Encabezado de la Matriz Oncológica (FRFAR-127)"""
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha")
    orden_produccion = models.CharField(max_length=50, unique=True, verbose_name="Orden de Producción")
    quien_prepara = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='oncologico_prepara', verbose_name="Quien Prepara")
    preelaboracion = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='oncologico_preelab', verbose_name="Preelaboración")
    alistamiento = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='oncologico_alistamiento', verbose_name="Alistamiento")
    quien_cobra = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='oncologico_cobra', verbose_name="Quien Cobra")
    jefe_produccion = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='oncologico_jefe_prod', verbose_name="Jefe de Producción")
    jefe_control_calidad = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='oncologico_jefe_calidad', verbose_name="Jefe de C. Calidad")
    digitador = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='oncologico_digitador', verbose_name="Digitador")

    class Meta:
        verbose_name = "Matriz Oncológica (Encabezado)"
        verbose_name_plural = "Matrices Oncológicas"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.orden_produccion} ({self.fecha})"

class NeonatosMedicamento(models.Model):
    """Base de Datos Medicamentos Neonatos"""
    cod = models.IntegerField(verbose_name="COD.", null=True, blank=True)
    producto = models.CharField(max_length=255, verbose_name="PRODUCTO")
    medicamento = models.CharField(max_length=255, verbose_name="MEDICAMENTO")
    concentracion = models.CharField(max_length=100, verbose_name="CONCENTRACIÓN")
    forma_farmaceutica = models.CharField(max_length=100, verbose_name="FORMA FARMACÉUTICA")

    volumen_reconstitucion = models.CharField(max_length=100, verbose_name="VOLUMEN DE RECONSTITUCIÓN", null=True, blank=True)
    solucion_reconstitucion = models.CharField(max_length=255, verbose_name="SOLUCIÓN DE RECONSTITUCIÓN", null=True, blank=True)
    cod_dil = models.CharField(max_length=50, verbose_name="COD. DIL.", null=True, blank=True)

    administracion = models.CharField(max_length=50, verbose_name="ADMINISTRACIÓN", null=True, blank=True)
    vol_final = models.CharField(max_length=100, verbose_name="VOL. FINAL (mL)", null=True, blank=True)
    vehiculo = models.CharField(max_length=255, verbose_name="VEHÍCULO", null=True, blank=True)

    jeringa = models.CharField(max_length=255, verbose_name="JERINGA", null=True, blank=True)
    aguja = models.CharField(max_length=255, verbose_name="AGUJA", null=True, blank=True)

    almacenamiento = models.CharField(max_length=255, verbose_name="ALMACENAMIENTO", null=True, blank=True)
    proteccion_luz = models.CharField(max_length=255, verbose_name="PROTECCIÓN LUZ / OBSERVACIONES", null=True, blank=True)
    fecha_expiracion = models.CharField(max_length=100, verbose_name="FECHA DE EXPIRACIÓN", null=True, blank=True)

    class Meta:
        verbose_name = "Medicamento Neonato (Base)"
        verbose_name_plural = "Medicamentos Neonatos (Base)"
        ordering = ['medicamento']

    def __str__(self):
        return f"{self.cod} - {self.medicamento} {self.concentracion}"


class NeonatosMatriz(models.Model):
    """Encabezado de la Matriz Neonatos"""
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha")
    orden_produccion = models.CharField(max_length=50, unique=True, verbose_name="Orden de Producción")
    quien_prepara = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='neonato_prepara', verbose_name="Quien Prepara")
    preelaboracion = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='neonato_preelab', verbose_name="Preelaboración")
    alistamiento = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='neonato_alistamiento', verbose_name="Alistamiento")
    quien_cobra = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='neonato_cobra', verbose_name="Quien Cobra")
    jefe_produccion = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='neonato_jefe_prod', verbose_name="Jefe de Producción")
    jefe_control_calidad = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='neonato_jefe_calidad', verbose_name="Jefe de C. Calidad")
    digitador = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='neonato_digitador', verbose_name="Digitador")

    class Meta:
        verbose_name = "Matriz Neonatos (Encabezado)"
        verbose_name_plural = "Matrices Neonatos"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.orden_produccion} ({self.fecha})"


class NeonatosMatrizItem(models.Model):
    """Fila de la Matriz Neonatos"""
    matriz = models.ForeignKey(NeonatosMatriz, on_delete=models.CASCADE, related_name='items')
    lote_interno = models.CharField(max_length=50, verbose_name="Lote Interno")

    # Datos del Paciente
    paciente_nombre = models.CharField(max_length=255, verbose_name="Nombre del Paciente")
    identificacion = models.CharField(max_length=50, verbose_name="Identificación")
    cama = models.CharField(max_length=20, verbose_name="Cama")
    servicio = models.CharField(max_length=100, verbose_name="Servicio")

    medicamento_base = models.ForeignKey(NeonatosMedicamento, on_delete=models.PROTECT, verbose_name="Medicamento (Catálogo)", null=True, blank=True)
    cod = models.CharField(max_length=50, verbose_name="COD", blank=True, null=True)
    medicamento = models.CharField(max_length=255, verbose_name="Medicamento")
    concentracion = models.CharField(max_length=100, verbose_name="Concentración")
    forma_farmaceutica = models.CharField(max_length=100, verbose_name="Forma Farmacéutica", blank=True, null=True)

    dosis = models.CharField(max_length=100, verbose_name="Dosis")
    frecuencia = models.CharField(max_length=100, verbose_name="Frecuencia", blank=True, null=True)

    volumen_final = models.CharField(max_length=100, verbose_name="Volumen Final", blank=True, null=True)
    lote = models.CharField(max_length=50, verbose_name="Lote Fabricante", blank=True, null=True)
    fecha_vencimiento = models.CharField(max_length=50, verbose_name="Fecha Vencimiento", blank=True, null=True)
    solucion_diluyente = models.CharField(max_length=255, verbose_name="Solución Diluyente", blank=True, null=True)
    viales_ampollas = models.CharField(max_length=100, verbose_name="Viales/Ampollas", blank=True, null=True)
    vol_dilucion = models.CharField(max_length=100, verbose_name="Volumen Dilución", blank=True, null=True)
    vol_dosis = models.CharField(max_length=100, verbose_name="Volumen de Dosis", blank=True, null=True)
    vol_final_unidosis = models.CharField(max_length=100, verbose_name="Volumen Final Unidosis", blank=True, null=True)
    via_admon = models.CharField(max_length=50, verbose_name="Vía de Administración", blank=True, null=True)

    class Meta:
        verbose_name = "Ítem Matriz Neonatos"
        verbose_name_plural = "Ítems Matriz Neonatos"

    def __str__(self):
        return f"{self.lote_interno} - {self.paciente_nombre}"


class NeonatosOrdenProduccion(models.Model):
    """Encabezado de la Orden de Producción Neonatos"""
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha")
    numero_orden = models.CharField(max_length=50, unique=True, verbose_name="Nº Orden de Producción")

    class Meta:
        verbose_name = "Orden de Producción Neonatos"
        verbose_name_plural = "Órdenes de Producción Neonatos"
        ordering = ['-fecha']

    def __str__(self):
        return f"OP-NEO {self.numero_orden} ({self.fecha})"


class NeonatosOrdenItem(models.Model):
    """Ítem de la Orden de Producción Neonatos"""
    orden = models.ForeignKey(NeonatosOrdenProduccion, on_delete=models.CASCADE, related_name='items')
    lote_interno = models.CharField(max_length=50, verbose_name="Lote Interno")
    medicamento = models.CharField(max_length=255, verbose_name="Medicamento")
    lote_fabricante = models.CharField(max_length=50, verbose_name="Lote Fabricante")
    cantidad_unidades = models.IntegerField(verbose_name="Cantidad Unidades")
    volumen_etiquetar = models.CharField(max_length=100, verbose_name="Volumen a Etiquetar")
    # Trazabilidad Operación
    preparador = models.ForeignKey('Funcionario', on_delete=models.PROTECT, related_name='neonato_orden_prep', null=True, blank=True)
    verificador = models.ForeignKey('Funcionario', on_delete=models.PROTECT, related_name='neonato_orden_verif', null=True, blank=True)

    class Meta:
        verbose_name = "Ítem Orden de Producción Neonatos"
        verbose_name_plural = "Ítems Orden de Producción Neonatos"

    def __str__(self):
        return f"{self.lote_interno} - {self.medicamento}"


class NeonatosAlistamiento(models.Model):
    """Alistamiento y Conciliación Neonatos"""
    orden_produccion = models.ForeignKey(NeonatosOrdenProduccion, on_delete=models.CASCADE, related_name='alistamientos', verbose_name="Orden de Producción")
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha de Alistamiento")
    responsable = models.ForeignKey('Funcionario', on_delete=models.PROTECT, verbose_name="Responsable Alistamiento")

    class Meta:
        verbose_name = "Alistamiento Neonatos"
        verbose_name_plural = "Alistamientos Neonatos"

    def __str__(self):
        return f"AL-NEO {self.orden_produccion.numero_orden} ({self.fecha})"


class NeonatosAlistamientoItem(models.Model):
    """Ítem de Alistamiento Neonatos"""
    alistamiento = models.ForeignKey(NeonatosAlistamiento, on_delete=models.CASCADE, related_name='items')
    codigo_med = models.CharField(max_length=50, verbose_name="Código")
    descripcion = models.CharField(max_length=255, verbose_name="Descripción (Medicamento/Acondicionamiento)")
    lote = models.CharField(max_length=50, verbose_name="Lote")
    fecha_vencimiento = models.DateField(verbose_name="Vencimiento", null=True, blank=True)
    cantidad_entregada = models.IntegerField(verbose_name="Cantidad Entregada")
    cantidad_devuelta = models.IntegerField(verbose_name="Cantidad Devuelta", default=0)
    cantidad_averiada = models.IntegerField(verbose_name="Cantidad Averiada", default=0)
    cantidad_consumida = models.IntegerField(verbose_name="Cantidad Consumida", default=0)
    
    class Meta:
        verbose_name = "Ítem Alistamiento Neonatos"
        verbose_name_plural = "Ítems Alistamiento Neonatos"

    def __str__(self):
        return f"{self.codigo_med} - {self.descripcion}"

class UnidosisProduccionOrden(models.Model):
    """Módulo: Unidosis Producción - (MAGHUDN1 - FRFAR-152/153/154)"""
    fecha = models.DateField(default=timezone.now)
    lote_interno = models.CharField(max_length=50, unique=True, verbose_name="Lote Interno (UNI-...)")
    
    # Datos de Matriz / Producción
    medicamento = models.CharField(max_length=255, verbose_name="Medicamento / Mezcla")
    cantidad_unidades = models.IntegerField(verbose_name="Cantidad Unidades")
    volumen_individual = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Volumen (mL/und)")
    
    # Trazabilidad Operativa
    elaborado_por = models.ForeignKey('Funcionario', on_delete=models.PROTECT, related_name='unidosis_elaborado', null=True, blank=True)
    revisado_por = models.ForeignKey('Funcionario', on_delete=models.PROTECT, related_name='unidosis_revisado', null=True, blank=True)
    aprobado_por = models.ForeignKey('Funcionario', on_delete=models.PROTECT, related_name='unidosis_aprobado', null=True, blank=True)

    class Meta:
        verbose_name = "Orden de Producción Unidosis"
        verbose_name_plural = "Órdenes de Producción Unidosis"

class NptMatriz(models.Model):
    """Encabezado de la Matriz Nutriciones Parentales (FRFAR-106)"""
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha")
    orden_produccion = models.CharField(max_length=50, unique=True, verbose_name="Orden de Producción")
    
    jefe_produccion = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='npt_jefe_prod')
    qf_preparador = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='npt_prepara')
    alistamiento = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='npt_alistamiento')
    digitador = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='npt_digitador')
    
    jefe_control_calidad = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='npt_jefe_cal')
    registrado_por = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='npt_registra')
    preelaboracion = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='npt_preelab')
    director_tecnico = models.ForeignKey('Funcionario', on_delete=models.PROTECT, null=True, blank=True, related_name='npt_director')

    class Meta:
        verbose_name = "Matriz NPT (Encabezado)"
        verbose_name_plural = "Matrices NPT"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.orden_produccion} ({self.fecha})"


class NptMatrizItem(models.Model):
    """Fila de la Matriz NPT (FRFAR-106)"""
    matriz = models.ForeignKey(NptMatriz, on_delete=models.CASCADE, related_name='items')
    lote_interno = models.CharField(max_length=50, verbose_name="Lote Interno")
    cod = models.CharField(max_length=50, verbose_name="COD.", blank=True, null=True)
    medicamento = models.CharField(max_length=255, verbose_name="Medicamento")
    paciente_nombre = models.CharField(max_length=255, verbose_name="Nombre de Paciente")
    identificacion = models.CharField(max_length=50, verbose_name="Identificación")
    servicio = models.CharField(max_length=100, verbose_name="Servicio")
    cama = models.CharField(max_length=20, verbose_name="Cama")
    peso = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Peso")
    
    volumen_dextrosa = models.CharField(max_length=50, blank=True, null=True, verbose_name="VOLUMEN DEXTROSA")
    concentracion_dextrosa = models.CharField(max_length=50, blank=True, null=True, verbose_name="CONCENTRACION DEXTROSA")
    aa_neonatos_10 = models.CharField(max_length=50, blank=True, null=True, verbose_name="A.A. Neonatos 10%")
    aa_adultos_10 = models.CharField(max_length=50, blank=True, null=True, verbose_name="A.A. Adultos 10%")
    aa_adultos_15 = models.CharField(max_length=50, blank=True, null=True, verbose_name="A.A. Adultos 15%")
    glutamina = models.CharField(max_length=50, blank=True, null=True, verbose_name="Glutamina")
    omegaven = models.CharField(max_length=50, blank=True, null=True, verbose_name="Omegaven")
    acidos_grasos = models.CharField(max_length=50, blank=True, null=True, verbose_name="Acidos Grasos")
    sodio = models.CharField(max_length=50, blank=True, null=True, verbose_name="Sodio (Na)")
    potasio = models.CharField(max_length=50, blank=True, null=True, verbose_name="Potasio (K)")
    glicerol_fosfato = models.CharField(max_length=50, blank=True, null=True, verbose_name="Glicerol Fosfato")
    calcio = models.CharField(max_length=50, blank=True, null=True, verbose_name="Calcio (Ca)")
    magnesio = models.CharField(max_length=50, blank=True, null=True, verbose_name="Magnesio (Mg)")
    multivitamina_cernevit = models.CharField(max_length=50, blank=True, null=True, verbose_name="Multivitamina (Cernevit)")
    multi_hidro_neo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Multivitamina Hidrosoluble Neo")
    multi_lipo_neo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Multivitamina Liposoluble Neo")
    vitamina_c = models.CharField(max_length=50, blank=True, null=True, verbose_name="Vitamina C")
    elementos_traza_neo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Elementos traza Neonatos (Peditrace)")
    elementos_traza_adultos = models.CharField(max_length=50, blank=True, null=True, verbose_name="Elementos traza Adultos")
    
    profesional_tratante = models.CharField(max_length=255, blank=True, null=True, verbose_name="PROFESIONAL TRATANTE")
    ajuste_flujo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Ajuste de Flujo")
    volumen_total = models.CharField(max_length=50, blank=True, null=True, verbose_name="Volumen Total")
    volumen_total_purga = models.CharField(max_length=50, blank=True, null=True, verbose_name="Volumen Total + Purga")
    bolsa_eva_formulada = models.CharField(max_length=50, blank=True, null=True, verbose_name="Bolsa EVA formulada")
    bolsa_final = models.CharField(max_length=50, blank=True, null=True, verbose_name="BOLSA FINAL")

    class Meta:
        verbose_name = "Ítem Matriz NPT"
        verbose_name_plural = "Ítems Matriz NPT"

    def __str__(self):
        return f"{self.lote_interno} - {self.paciente_nombre}"

class NptOrdenProduccion(models.Model):
    """Encabezado de la Orden de Producción NPT (FRFAR-182)"""
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha")
    numero_orden = models.CharField(max_length=50, unique=True, verbose_name="Nº Orden de Producción")

    class Meta:
        verbose_name = "Orden de Producción NPT"
        verbose_name_plural = "Órdenes de Producción NPT"
        ordering = ['-fecha']

    def __str__(self):
        return f"OP-NPT {self.numero_orden} ({self.fecha})"

class NptOrdenItem(models.Model):
    """Fila de la Orden de Producción NPT"""
    orden = models.ForeignKey(NptOrdenProduccion, on_delete=models.CASCADE, related_name='items')
    lote_interno = models.CharField(max_length=50, verbose_name="Lote Interno")
    paciente_nombre = models.CharField(max_length=255, verbose_name="Nombre del Paciente")
    medicamento = models.CharField(max_length=255, verbose_name="Medicamento")
    volumen_final = models.CharField(max_length=100, verbose_name="Volumen Final", blank=True, null=True)

    class Meta:
        verbose_name = "Ítem Orden NPT"
        verbose_name_plural = "Ítems Orden NPT"

    def __str__(self):
        return f"{self.lote_interno} - {self.paciente_nombre}"

class NptAlistamiento(models.Model):
    """Alistamiento y Conciliación NPT (FRFAR-162)"""
    orden_produccion = models.ForeignKey(NptOrdenProduccion, on_delete=models.CASCADE, related_name='alistamientos', verbose_name="Orden de Producción")
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha de Alistamiento")
    responsable = models.ForeignKey('Funcionario', on_delete=models.PROTECT, verbose_name="Responsable Alistamiento", null=True, blank=True)

    class Meta:
        verbose_name = "Alistamiento NPT"
        verbose_name_plural = "Alistamientos NPT"

    def __str__(self):
        return f"AL-NPT {self.orden_produccion.numero_orden} ({self.fecha})"

class NptAlistamientoItem(models.Model):
    """Ítem de Alistamiento NPT"""
    alistamiento = models.ForeignKey(NptAlistamiento, on_delete=models.CASCADE, related_name='items')
    material = models.CharField(max_length=255, verbose_name="Material de Partida")
    lote = models.CharField(max_length=50, verbose_name="Lote", blank=True, null=True)
    fecha_vencimiento = models.DateField(verbose_name="Vencimiento", null=True, blank=True)
    cantidad_solicitada = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad Solicitada", null=True, blank=True)
    cantidad_ingresada = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad Ingresada", null=True, blank=True)
    aprovechamiento = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Aprovechamiento", null=True, blank=True)
    producto_terminado = models.CharField(max_length=255, verbose_name="Producto Terminado", blank=True, null=True)
    
    class Meta:
        verbose_name = "Ítem Alistamiento NPT"
        verbose_name_plural = "Ítems Alistamiento NPT"

    def __str__(self):
        return self.material

class OncologicoMatrizItem(models.Model):
    """Fila de la Matriz Oncológica (FRFAR-127)"""
    matriz = models.ForeignKey(OncologicoMatriz, on_delete=models.CASCADE, related_name='items')
    lote_interno = models.CharField(max_length=50, verbose_name="Lote Interno")

    # Datos del Paciente
    paciente_nombre = models.CharField(max_length=255, verbose_name="Nombre del Paciente")
    identificacion = models.CharField(max_length=50, verbose_name="Identificación")
    cama = models.CharField(max_length=20, verbose_name="Cama")
    servicio = models.CharField(max_length=100, verbose_name="Servicio")

    # Medicamento (referencia al catálogo base)
    medicamento_base = models.ForeignKey(MedicamentoOncologico, on_delete=models.PROTECT,
                                         verbose_name="Medicamento (Catálogo)", null=True, blank=True)
    cod = models.CharField(max_length=50, verbose_name="COD", blank=True, null=True)
    medicamento = models.CharField(max_length=255, verbose_name="Medicamento")
    concentracion = models.CharField(max_length=100, verbose_name="Concentración (mg, UI)")
    forma_farmaceutica = models.CharField(max_length=100, verbose_name="Forma Farmacéutica", blank=True, null=True)

    # Dosificación
    dosis = models.CharField(max_length=100, verbose_name="Dosis (mg, UI)")
    frecuencia = models.CharField(max_length=100, verbose_name="Frecuencia (Cantidad)", blank=True, null=True)

    # Preparación
    volumen_final = models.CharField(max_length=100, verbose_name="Volumen Final", blank=True, null=True)
    lote = models.CharField(max_length=50, verbose_name="Lote Fabricante", blank=True, null=True)
    fecha_vencimiento = models.CharField(max_length=50, verbose_name="Fecha Vencimiento", blank=True, null=True)
    solucion_diluyente = models.CharField(max_length=255, verbose_name="Solución Diluyente", blank=True, null=True)
    viales_ampollas = models.CharField(max_length=100, verbose_name="Viales/Ampollas", blank=True, null=True)
    vol_dilucion = models.CharField(max_length=100, verbose_name="Volumen Dilución", blank=True, null=True)
    vol_dosis = models.CharField(max_length=100, verbose_name="Volumen de Dosis", blank=True, null=True)
    vol_final_unidosis = models.CharField(max_length=100, verbose_name="Volumen Final Unidosis", blank=True, null=True)
    via_admon = models.CharField(max_length=50, verbose_name="Vía de Administración", blank=True, null=True)

    class Meta:
        verbose_name = "Ítem Matriz Oncológica"
        verbose_name_plural = "Ítems Matriz Oncológica"

    def __str__(self):
        return f"{self.lote_interno} - {self.paciente_nombre}"


# --- FRFAR-178 ORDEN DE PRODUCCIÓN ONCOLÓGICOS ---

class OncologicoOrdenProduccion(models.Model):
    """Encabezado de la Orden de Producción Oncológica (FRFAR-178)"""
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha")
    numero_orden = models.CharField(max_length=50, unique=True, verbose_name="Nº Orden de Producción")

    class Meta:
        verbose_name = "Orden de Producción Oncológica"
        verbose_name_plural = "Órdenes de Producción Oncológicas"
        ordering = ['-fecha']

    def __str__(self):
        return f"OP-ONC {self.numero_orden} ({self.fecha})"


class OncologicoOrdenItem(models.Model):
    """Fila de la Orden de Producción Oncológica (FRFAR-178)"""
    orden = models.ForeignKey(OncologicoOrdenProduccion, on_delete=models.CASCADE, related_name='items')

    # Datos del paciente
    paciente_nombre = models.CharField(max_length=255, verbose_name="Nombre del Paciente")
    identificacion = models.CharField(max_length=50, verbose_name="Identificación")
    cama = models.CharField(max_length=20, verbose_name="Cama")
    medicamento = models.CharField(max_length=255, verbose_name="Medicamento")
    via_administracion = models.CharField(max_length=50, verbose_name="Vía de Administración", blank=True, null=True)

    # Reconstitución
    viales_ampollas = models.CharField(max_length=100, verbose_name="Viales/Ampollas", blank=True, null=True)
    vehiculo_reconstitucion = models.CharField(max_length=255, verbose_name="Vehículo Reconstitución", blank=True, null=True)
    volumen_reconstitucion = models.CharField(max_length=100, verbose_name="Volumen Reconstitución (mL)", blank=True, null=True)

    # Unidosis
    dosis = models.CharField(max_length=100, verbose_name="Dosis (mg, UI)", blank=True, null=True)
    vol_dosis = models.CharField(max_length=100, verbose_name="Volumen de Dosis (mL)", blank=True, null=True)
    vehiculo_unidosis = models.CharField(max_length=255, verbose_name="Vehículo Unidosis", blank=True, null=True)
    vol_final = models.CharField(max_length=100, verbose_name="Volumen Final (mL)", blank=True, null=True)
    concentracion_final = models.CharField(max_length=100, verbose_name="Concentración Final (mg/mL, UI/mL)", blank=True, null=True)

    # Control
    lote_interno = models.CharField(max_length=50, verbose_name="Lote Interno")
    cantidad = models.IntegerField(default=1, verbose_name="Cantidad")
    recibido = models.BooleanField(default=False, verbose_name="Recibido")

    class Meta:
        verbose_name = "Ítem Orden Producción Oncológica"
        verbose_name_plural = "Ítems Orden Producción Oncológica"

    def __str__(self):
        return f"{self.lote_interno} - {self.paciente_nombre}"


# --- FRFAR-162 ALISTAMIENTO Y CONCILIACIÓN ONCOLÓGICOS ---

class OncologicoAlistamiento(models.Model):
    """Encabezado del Alistamiento y Conciliación (FRFAR-162)"""
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha")
    numero_orden = models.CharField(max_length=50, verbose_name="No. Orden", blank=True, null=True)
    area = models.CharField(max_length=100, default="ONCOLOGICOS", verbose_name="Área")

    class Meta:
        verbose_name = "Alistamiento Oncológico"
        verbose_name_plural = "Alistamientos Oncológicos"
        ordering = ['-fecha']

    def __str__(self):
        return f"Alistamiento {self.numero_orden} ({self.fecha})"


class OncologicoAlistamientoItem(models.Model):
    """Fila del Alistamiento y Conciliación (FRFAR-162)"""
    alistamiento = models.ForeignKey(OncologicoAlistamiento, on_delete=models.CASCADE, related_name='items')

    material = models.CharField(max_length=255, verbose_name="Material de Partida")
    lote_fabricante = models.CharField(max_length=50, verbose_name="Lote Fabricante", blank=True, null=True)
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento", null=True, blank=True)
    cantidad_solicitada = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad Solicitada", null=True, blank=True)
    cantidad_ingresada = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad Ingresada", null=True, blank=True)
    aprovechamiento = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Aprovechamiento", null=True, blank=True)
    producto_terminado = models.CharField(max_length=255, verbose_name="Producto Terminado", blank=True, null=True)

    class Meta:
        verbose_name = "Ítem Alistamiento Oncológico"
        verbose_name_plural = "Ítems Alistamiento Oncológico"

    def __str__(self):
        return f"{self.material} - {self.alistamiento}"
