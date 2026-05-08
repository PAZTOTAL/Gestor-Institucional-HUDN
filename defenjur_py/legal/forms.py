from django import forms
from django.contrib.auth import get_user_model
from .models import (
    AccionTutela, DerechoPeticion, ProcesoExtrajudicial, ProcesoJudicialActiva, ProcesoJudicialPasiva,
    Peritaje, PagoSentenciaJudicial, ProcesoJudicialTerminado,
    ProcesoAdministrativoSancionatorio, RequerimientoEnteControl, DespachoJudicial,
    CatalogoDerechoVulnerado, CatalogoAccionado, IncidenteDesacato, PronunciamientoHecho
)


def get_despacho_choices():
    """Devuelve lista de opciones para el select de Despacho Judicial."""
    try:
        opciones = [('', '— Seleccione un despacho —')]
        opciones += [
            (d.nombre, f"{d.ciudad} — {d.nombre}")
            for d in DespachoJudicial.objects.order_by('ciudad', 'nombre')
        ]
        return opciones
    except Exception:
        return [('', '— Sin despachos disponibles —')]

class PremiumModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'premium-input')
            if not field.widget.attrs.get('placeholder'):
                field.widget.attrs['placeholder'] = field.label
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['rows'] = 4

class AnyMultipleChoiceField(forms.MultipleChoiceField):
    def valid_value(self, value):
        return True

class AccionTutelaForm(PremiumModelForm):
    email_accionante = forms.EmailField(
        label='EMAIL ACCIONANTE',
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'})
    )
    cedula_abogado = forms.CharField(
        label='CÉDULA ABOGADO', 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Buscar abogado...'})
    )
    despacho_judicial = forms.ChoiceField(
        label='DESPACHO JUDICIAL',
        required=False,
        widget=forms.Select(attrs={'class': 'premium-input'})
    )
    accionado = AnyMultipleChoiceField(
        label='ACCIONADO',
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'premium-input select2-tags', 'data-placeholder': 'Escriba entidades y presione Enter...', 'style': 'width: 100%'})
    )
    vinculados = AnyMultipleChoiceField(
        label='VINCULADOS',
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'premium-input select2-tags', 'data-placeholder': 'Escriba vinculados y presione Enter...', 'style': 'width: 100%'})
    )
    derechos_vulnerados = AnyMultipleChoiceField(
        label='DERECHOS VULNERADOS',
        choices=[],
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'premium-input select2-tags', 'data-placeholder': 'Seleccione o escriba derechos...', 'style': 'width: 100%'})
    )

    campos_fase1 = [
        'num_proceso', 'fecha_llegada', 'despacho_judicial', 'num_reparto', 'cedula_accionante', 
        'accionante', 'email_accionante', 'accionado', 'cedula_abogado', 
        'abogado_responsable', 'fecha_notificacion', 'termino_dias', 
        'termino_horas', 'fecha_vencimiento'
    ]
    
    campos_fase2 = [
        'vinculados', 'derechos_vulnerados', 'pretensiones', 'fecha_respuesta', 'radicado_respuesta', 'medio_envio_respuesta',
        'estado_tutela', 'sentido_fallo', 'requiere_cumplimiento', 'fecha_limite_cumplimiento', 'incidente_desacato', 'observaciones'
    ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Lógica de detección de roles (Paridad con views.py)
        perfil = getattr(self.user, 'perfil', None) if self.user else None
        rol = (getattr(self.user, 'rol', None) or getattr(perfil, 'legal_rol', '') or '').lower()
        
        is_abogado = rol in ['abogado', 'especialista', 'coordinador']
        is_radicador = rol == 'radicador'
        
        # 1. Si es ABOGADO y ya existe el registro, BLOQUEAR fase 1 (Radicación)
        if is_abogado and self.instance and self.instance.pk:
            for field_name in self.campos_fase1:
                if field_name in self.fields:
                    # Usar readonly en lugar de disabled para asegurar visualización de datos
                    self.fields[field_name].widget.attrs['readonly'] = True
                    self.fields[field_name].widget.attrs['class'] = self.fields[field_name].widget.attrs.get('class', '') + ' readonly-field'
                    # Para selects, disabled es necesario pero readonly-field ayudará
                    if isinstance(self.fields[field_name].widget, (forms.Select, forms.SelectMultiple)):
                        self.fields[field_name].disabled = True

        # 2. Si es RADICADOR, BLOQUEAR fase 2 (Gestión)
        if is_radicador:
            for field_name in self.campos_fase2:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs['readonly'] = True
                    self.fields[field_name].widget.attrs['class'] = self.fields[field_name].widget.attrs.get('class', '') + ' readonly-field'
                    if isinstance(self.fields[field_name].widget, (forms.Select, forms.SelectMultiple)):
                        self.fields[field_name].disabled = True

        self.fields['despacho_judicial'].choices = get_despacho_choices()
            
        derecho_choices = list(CatalogoDerechoVulnerado.objects.values_list('nombre', 'nombre'))
        
        accionado_objs = CatalogoAccionado.objects.all()
        accionado_choices = []
        for obj in accionado_objs:
            label = f"[{obj.nit}] {obj.nombre}" if obj.nit else obj.nombre
            accionado_choices.append((obj.nombre, label))
            
        self.fields['derechos_vulnerados'].choices = derecho_choices
        self.fields['accionado'].choices = accionado_choices
        
        if self.instance and self.instance.pk:
            if self.instance.despacho_judicial:
                current_desp_choices = [c[0] for c in self.fields['despacho_judicial'].choices]
                if self.instance.despacho_judicial not in current_desp_choices:
                    self.fields['despacho_judicial'].choices.append((self.instance.despacho_judicial, self.instance.despacho_judicial))

            if self.instance.vinculados:
                curr_vinc = [x.strip() for x in self.instance.vinculados.split(',') if x.strip()]
                self.initial['vinculados'] = curr_vinc
                self.fields['vinculados'].choices = [(x, x) for x in curr_vinc]
                
            if self.instance.accionado:
                curr_acc = [x.strip() for x in self.instance.accionado.split(',') if x.strip()]
                self.initial['accionado'] = curr_acc
                exist_acc = [c[0] for c in accionado_choices]
                extra_acc = [(x, x) for x in curr_acc if x not in exist_acc]
                self.fields['accionado'].choices = accionado_choices + extra_acc
            if self.instance.derechos_vulnerados:
                curr_der = [x.strip() for x in self.instance.derechos_vulnerados.split(',') if x.strip()]
                self.initial['derechos_vulnerados'] = curr_der
                exist_der = [c[0] for c in derecho_choices]
                extra_der = [(x, x) for x in curr_der if x not in exist_der]
                self.fields['derechos_vulnerados'].choices = derecho_choices + extra_der

    def clean_accionado(self):
        data = self.cleaned_data.get('accionado')
        if isinstance(data, list):
            return ", ".join([x.strip() for x in data if x.strip()])
        return data

    def clean_vinculados(self):
        data = self.cleaned_data.get('vinculados')
        if isinstance(data, list):
            return ", ".join([x.strip() for x in data if x.strip()])
        return data

    def clean_derechos_vulnerados(self):
        data = self.cleaned_data.get('derechos_vulnerados')
        if isinstance(data, list):
            return ", ".join([x.strip() for x in data if x.strip()])
        return data

    class Meta:
        model = AccionTutela
        fields = [
            'num_proceso', 'fecha_llegada', 'despacho_judicial', 'num_reparto', 'cedula_accionante', 'accionante', 'email_accionante', 'accionado', 'cedula_abogado', 'abogado_responsable',
            'fecha_notificacion', 'termino_dias', 'termino_horas', 'fecha_vencimiento',
            'vinculados', 'derechos_vulnerados', 'pretensiones',
            'fecha_respuesta', 'radicado_respuesta', 'medio_envio_respuesta',
            'estado_tutela', 'sentido_fallo',
            'requiere_cumplimiento', 'fecha_limite_cumplimiento', 'incidente_desacato',
            'observaciones'
        ]
        widgets = {
            'fecha_llegada': forms.DateInput(attrs={'type': 'date'}),
            'fecha_notificacion': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_vencimiento': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_respuesta': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_limite_cumplimiento': forms.DateInput(attrs={'type': 'date'}),
            'cedula_accionante': forms.TextInput(attrs={'placeholder': 'Digite cédula para buscar...'}),
            'pretensiones': forms.Textarea(attrs={'rows': 4}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

class IncidenteDesacatoForm(PremiumModelForm):
    class Meta:
        model = IncidenteDesacato
        fields = [
            'fecha_notificacion', 'termino_dias', 'termino_horas', 
            'fecha_vencimiento', 'fecha_respuesta', 'radicado_respuesta', 
            'medio_envio', 'observaciones'
        ]
        widgets = {
            'fecha_notificacion': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_vencimiento': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_respuesta': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'observaciones': forms.Textarea(attrs={'rows': 2}),
        }

from django.forms import inlineformset_factory
IncidenteDesacatoFormSet = inlineformset_factory(
    AccionTutela, IncidenteDesacato, form=IncidenteDesacatoForm,
    extra=1, can_delete=True
)

class PronunciamientoHechoForm(PremiumModelForm):
    class Meta:
        model = PronunciamientoHecho
        fields = ['hecho_referencia', 'tipo_respuesta', 'pronunciamiento']
        widgets = {
            'hecho_referencia': forms.TextInput(attrs={'placeholder': 'Ej: FRENTE AL PRIMER HECHO...'}),
            'pronunciamiento': forms.Textarea(attrs={'rows': 2}),
        }

PronunciamientoHechoFormSet = inlineformset_factory(
    AccionTutela, PronunciamientoHecho, form=PronunciamientoHechoForm,
    extra=1, can_delete=True
)

class DerechoPeticionForm(PremiumModelForm):
    cedula_accionante = forms.CharField(
        label='CÉDULA SOLICITANTE', 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Digite cédula para buscar...'})
    )
    cedula_abogado = forms.CharField(
        label='CÉDULA ABOGADO', 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Buscar abogado...'})
    )
    class Meta:
        model = DerechoPeticion
        fields = [
            'cedula_accionante', 'nombre_persona_solicitante', 'fecha_correo', 'num_reparto', 
            'fecha_reparto', 'num_rad_interno', 'fecha_remitente_peticion', 
            'cedula_persona_solicitante', 'peticionario_int_ext', 'peticionario', 
            'causa_peticion', 'cedula_abogado', 'abogado_responsable', 'modalidad_peticion', 
            'tramite_impartido', 'area_remitir_informacion',
            'fecha_notificacion', 'termino_dias', 'termino_horas', 'fecha_vencimiento',
            'fecha_respuesta_real', 'radicado_respuesta_salida', 'medio_envio_respuesta',
            'estado_peticion', 'observaciones'
        ]
        widgets = {
            'fecha_correo': forms.DateInput(attrs={'type': 'date'}),
            'fecha_reparto': forms.DateInput(attrs={'type': 'date'}),
            'fecha_remitente_peticion': forms.DateInput(attrs={'type': 'date'}),
            'fecha_respuesta_peticion': forms.DateInput(attrs={'type': 'date'}),
            'fecha_notificacion': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_vencimiento': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_respuesta_real': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'tramite_impartido': forms.Textarea(attrs={'rows': 3}),
            'causa_peticion': forms.Textarea(attrs={'rows': 4}),
        }


class ProcesoExtrajudicialForm(PremiumModelForm):
    cedula_solicitante = forms.CharField(label='CÉDULA DEMANDANTE', required=False)
    class Meta:
        model = ProcesoExtrajudicial
        fields = [
            'cedula_solicitante', 'demandante', 'demandado', 'apoderado',
            'medio_control', 'despacho_conocimiento',
            'estado', 'clasificacion',
        ]
        widgets = {
            'despacho_conocimiento': forms.Textarea(attrs={'rows': 6}),
            'clasificacion': forms.TextInput(
                attrs={'placeholder': 'Ej.: Conciliado, No conciliado, En trámite…'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['despacho_conocimiento'].widget.attrs['rows'] = 6
        self.fields['clasificacion'].help_text = 'Opcional. Use términos alineados con los filtros Conciliados / No conciliados de la lista.'

class ProcesoJudicialActivaForm(PremiumModelForm):
    cc_demandante = forms.CharField(label='C.C. DEMANDANTE', required=False)
    class Meta:
        model = ProcesoJudicialActiva
        fields = [
            'num_proceso', 'cc_demandante', 'demandante', 'demandado', 'apoderado', 'despacho_actual',
            'medio_control', 'ciudad', 'estimacion_cuantia', 'sentencia_primera_instancia',
            'pretension', 'ultima_actuacion', 'estado_actual',
        ]

class ProcesoJudicialPasivaForm(PremiumModelForm):
    class Meta:
        model = ProcesoJudicialPasiva
        fields = [
            'num_proceso', 'cc_demandante', 'demandante', 'demandado', 'apoderado', 'despacho_actual',
            'medio_control', 'calidad_entidad', 'hecho_generador',
            'valor_pretension_inicial', 'valor_provisionar', 'fallo_sentencia', 'valor_fallo_sentencia',
            'riesgo_perdida', 'porcentaje_probabilidad_perdida',
            'pretensiones', 'hechos_relevantes', 'enfoque_defensa', 'estado_actual', 'observaciones',
        ]

class PeritajeForm(PremiumModelForm):
    cedula_solicitante = forms.CharField(label='CÉDULA DEMANDANTE', required=False)
    class Meta:
        model = Peritaje
        fields = [
            'num_proceso', 'fecha_correo_electronico', 'entidad_remitente_requerimiento',
            'cedula_solicitante', 'demandante', 'demandado', 'abogado_responsable',
            'num_reparto', 'fecha_reparto',
            'asunto', 'fecha_asignar_perito', 'perito_asignado', 'pago_honorarios', 'observaciones',
        ]
        widgets = {
            'fecha_correo_electronico': forms.DateInput(attrs={'type': 'date'}),
            'fecha_reparto': forms.DateInput(attrs={'type': 'date'}),
            'fecha_asignar_perito': forms.DateInput(attrs={'type': 'date'}),
        }

class PagoSentenciaJudicialForm(PremiumModelForm):
    class Meta:
        model = PagoSentenciaJudicial
        fields = [
            'num_proceso', 'fecha_pago', 'despacho_tramitante', 'medio_control',
            'demandante', 'demandado',
            'valor_pagado', 'estado', 'tipo_pago', 'abogado_responsable',
            'fecha_ejecutoria_sentencia', 'imputacion_costo', 'fecha_registro',
        ]
        widgets = {
            'fecha_pago': forms.DateInput(attrs={'type': 'date'}),
            'fecha_ejecutoria_sentencia': forms.DateInput(attrs={'type': 'date'}),
            'fecha_registro': forms.DateTimeInput(
                format='%Y-%m-%d %H:%M:%S',
                attrs={'placeholder': 'AAAA-MM-DD HH:MM:SS'},
            ),
        }

class ProcesoJudicialTerminadoForm(PremiumModelForm):
    class Meta:
        model = ProcesoJudicialTerminado
        fields = [
            'num_proceso', 'demandante', 'cc_demandante', 'demandado', 'apoderado', 'despacho_actual',
            'medio_control', 'ciudad', 'calidad_entidad', 'hecho_generador',
            'valor_proceso', 'valor_pretension_inicial', 'valor_provisionar',
            'fallo_sentencia', 'valor_fallo_sentencia', 'riesgo_perdida', 'porcentaje_probabilidad_perdida',
            'informe_pago', 'accion_repeticion',
            'pretensiones', 'ultima_actuacion', 'estado_actual', 'hechos_relevantes', 'enfoque_defensa', 'observaciones',
        ]

class ProcesoAdministrativoSancionatorioForm(PremiumModelForm):
    class Meta:
        model = ProcesoAdministrativoSancionatorio
        fields = [
            'num_proceso', 'fecha_requerimiento', 'entidad', 'causa', 'estado',
            'entidad_solicitante_requerimiento',
            'objeto_requerimiento', 'fecha_dar_tramite_desde', 'fecha_dar_tramite_hasta',
        ]
        widgets = {
            'fecha_requerimiento': forms.DateInput(attrs={'type': 'date'}),
            'fecha_dar_tramite_desde': forms.DateInput(attrs={'type': 'date'}),
            'fecha_dar_tramite_hasta': forms.DateInput(attrs={'type': 'date'}),
        }

class RequerimientoEnteControlForm(PremiumModelForm):
    class Meta:
        model = RequerimientoEnteControl
        fields = [
            'num_reparto', 'num_proceso', 'fecha_correo_electronico',
            'entidad_remitente_requerimiento', 'asunto', 'abogado_responsable',
            'correo', 'fecha_reparto', 'tipo_tramite', 'termino_dar_tramite',
            'observaciones', 'tramite_impartido', 'fecha_respuesta_tramite',
        ]
        widgets = {
            'fecha_correo_electronico': forms.DateInput(attrs={'type': 'date'}),
            'fecha_reparto': forms.DateInput(attrs={'type': 'date'}),
            'fecha_respuesta_tramite': forms.DateInput(attrs={'type': 'date'}),
        }


Usuario = get_user_model()


class UsuarioHudnCreateForm(PremiumModelForm):
    user_select = forms.ModelChoiceField(
        queryset=Usuario.objects.all(),
        label='Seleccionar Usuario del Sistema',
        help_text='Busque el funcionario por su nombre de usuario o cédula.',
        widget=forms.Select(attrs={'class': 'premium-input select2-enabled'})
    )
    rol = forms.ChoiceField(choices=[('administrador', 'Administrador'), ('abogado', 'Abogado'), ('radicador', 'Radicador'), ('invitado', 'Invitado')], required=True)

    # Matriz de Permisos
    perm_tutela = forms.BooleanField(label='Tutelas', required=False)
    perm_peticion = forms.BooleanField(label='Peticiones', required=False)
    perm_activa = forms.BooleanField(label='Proc. Activa', required=False)
    perm_pasiva = forms.BooleanField(label='Proc. Pasiva', required=False)
    perm_terminado = forms.BooleanField(label='Proc. Terminados', required=False)
    perm_peritaje = forms.BooleanField(label='Peritajes', required=False)
    perm_pago = forms.BooleanField(label='Pagos Sentencias', required=False)
    perm_sancionatorio = forms.BooleanField(label='Sancionatorios', required=False)
    perm_requerimiento = forms.BooleanField(label='Requerimientos', required=False)
    perm_extrajudicial = forms.BooleanField(label='Extrajudiciales', required=False)
    perm_catalogo = forms.BooleanField(label='Catálogos', required=False)

    MAP_PERMS = {
        'perm_tutela': 'acciontutela',
        'perm_peticion': 'derechopeticion',
        'perm_activa': 'procesojudicialactiva',
        'perm_pasiva': 'procesojudicialpasiva',
        'perm_terminado': 'procesojudicialterminado',
        'perm_peritaje': 'peritaje',
        'perm_pago': 'pagosentenciajudicial',
        'perm_sancionatorio': 'procesoadministrativosancionatorio',
        'perm_requerimiento': 'requerimientoentecontrol',
        'perm_extrajudicial': 'procesoextrajudicial',
        'perm_catalogo': 'catalogoderechovulnerado',
    }

    class Meta:
        model = Usuario
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from usuarios.models import PermisoApp
        users_with_perm = PermisoApp.objects.filter(
            app_label__in=['defenjur', 'legal'], 
            permitido=True
        ).values_list('user_id', flat=True)
        
        self.fields['user_select'].queryset = Usuario.objects.exclude(
            id__in=users_with_perm
        ).order_by('username')
        
        self.fields['user_select'].label_from_instance = lambda obj: f"{obj.username} - {obj.get_full_name()}"

    def save(self, commit=True):
        from django.db import transaction
        user = self.cleaned_data.get('user_select')
        if commit:
            from usuarios.models import PerfilUsuario, PermisoApp, PermisoModelo
            from django.core.cache import cache
            
            with transaction.atomic():
                selected_rol = self.cleaned_data.get('rol')
                # Sincronizar campo 'rol' en el modelo de Usuario (para listas)
                user.rol = selected_rol
                user.save()

                perfil, created = PerfilUsuario.objects.get_or_create(user=user)
                perfil.legal_rol = selected_rol
                perfil.legal_nick = user.username
                perfil.save()
                
                # Otorgar permiso principal
                PermisoApp.objects.update_or_create(user=user, app_label='defenjur', defaults={'permitido': True})
                PermisoApp.objects.update_or_create(user=user, app_label='legal', defaults={'permitido': True})
                
                # Guardar Matriz de Permisos
                for field_name, model_name in self.MAP_PERMS.items():
                    val = self.cleaned_data.get(field_name, False)
                    PermisoModelo.objects.update_or_create(
                        user=user, app_label='defenjur', model_name=model_name,
                        defaults={'permitido': val}
                    )
                    # También para 'legal' para evitar fallos de filtro
                    PermisoModelo.objects.update_or_create(
                        user=user, app_label='legal', model_name=model_name,
                        defaults={'permitido': val}
                    )
                
                cache.delete(f'user_dashboard_nav_{user.id}')
                cache.delete(f'dashboard_structure_{user.id}')
                
        return user


class UsuarioHudnUpdateForm(PremiumModelForm):
    rol = forms.ChoiceField(choices=[('administrador', 'Administrador'), ('abogado', 'Abogado'), ('radicador', 'Radicador'), ('invitado', 'Invitado')], required=False)

    # Matriz de Permisos DEFENJUR
    perm_tutela = forms.BooleanField(label='Tutelas', required=False)
    perm_peticion = forms.BooleanField(label='Peticiones', required=False)
    perm_activa = forms.BooleanField(label='Proc. Activa', required=False)
    perm_pasiva = forms.BooleanField(label='Proc. Pasiva', required=False)
    perm_terminado = forms.BooleanField(label='Proc. Terminados', required=False)
    perm_peritaje = forms.BooleanField(label='Peritajes', required=False)
    perm_pago = forms.BooleanField(label='Pagos Sentencias', required=False)
    perm_sancionatorio = forms.BooleanField(label='Sancionatorios', required=False)
    perm_requerimiento = forms.BooleanField(label='Requerimientos', required=False)
    perm_extrajudicial = forms.BooleanField(label='Extrajudiciales', required=False)
    perm_catalogo = forms.BooleanField(label='Catálogos', required=False)

    MAP_PERMS = {
        'perm_tutela': 'acciontutela',
        'perm_peticion': 'derechopeticion',
        'perm_activa': 'procesojudicialactiva',
        'perm_pasiva': 'procesojudicialpasiva',
        'perm_terminado': 'procesojudicialterminado',
        'perm_peritaje': 'peritaje',
        'perm_pago': 'pagosentenciajudicial',
        'perm_sancionatorio': 'procesoadministrativosancionatorio',
        'perm_requerimiento': 'requerimientoentecontrol',
        'perm_extrajudicial': 'procesoextrajudicial',
        'perm_catalogo': 'catalogoderechovulnerado',
    }

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            perfil = getattr(self.instance, 'perfil', None)
            if perfil:
                self.fields['rol'].initial = perfil.legal_rol
            
            # Cargar permisos existentes
            from usuarios.models import PermisoModelo
            permisos = PermisoModelo.objects.filter(user=self.instance, app_label__in=['defenjur', 'legal'])
            # Prioritize True if there are duplicates
            perm_dict = {}
            for p in permisos:
                if p.permitido or p.model_name not in perm_dict:
                    perm_dict[p.model_name] = p.permitido
            for field_name, model_name in self.MAP_PERMS.items():
                self.fields[field_name].initial = perm_dict.get(model_name, False)

    def save(self, commit=True):
        from django.db import transaction
        from usuarios.models import PerfilUsuario, PermisoModelo
        from django.core.cache import cache

        user = super().save(commit=False)
        
        if commit:
            with transaction.atomic():
                selected_rol = self.cleaned_data.get('rol')
                if selected_rol:
                    user.rol = selected_rol
                user.save()
                
                # 1. Actualizar Perfil
                perfil, created = PerfilUsuario.objects.get_or_create(user=user)
                if selected_rol:
                    perfil.legal_rol = selected_rol
                perfil.legal_nick = user.username
                perfil.save()

                # 2. Guardar Permisos de Módulo (Usando update_or_create para asegurar ambos app_labels)
                for field_name, model_name in self.MAP_PERMS.items():
                    val = self.cleaned_data.get(field_name, False)
                    PermisoModelo.objects.update_or_create(
                        user=user, app_label='defenjur', model_name=model_name,
                        defaults={'permitido': val}
                    )
                    PermisoModelo.objects.update_or_create(
                        user=user, app_label='legal', model_name=model_name,
                        defaults={'permitido': val}
                    )

                # 3. Invalidar Cache de Navegación
                cache.delete(f'user_dashboard_nav_{user.id}')
                cache.delete(f'dashboard_structure_{user.id}')
            
        return user


