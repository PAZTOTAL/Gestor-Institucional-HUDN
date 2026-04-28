from django import forms
from django.contrib.auth import get_user_model
from .models import (
    AccionTutela, DerechoPeticion, ProcesoExtrajudicial, ProcesoJudicialActiva, ProcesoJudicialPasiva,
    Peritaje, PagoSentenciaJudicial, ProcesoJudicialTerminado,
    ProcesoAdministrativoSancionatorio, RequerimientoEnteControl, DespachoJudicial
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

class AccionTutelaForm(PremiumModelForm):
    cedula_accionante = forms.CharField(
        label='CÉDULA ACCIONANTE', 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Digite cédula para buscar...'})
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['despacho_judicial'].choices = get_despacho_choices()
        if 'identificacion_accionante' in self.fields: # Si existe en el modelo (check migrations)
            self.fields['cedula_accionante'].initial = self.instance.identificacion_accionante

    class Meta:
        model = AccionTutela
        fields = [
            'num_proceso', 'fecha_llegada', 'despacho_judicial', 'cedula_accionante', 'accionante', 'accionado', 'cedula_abogado', 'abogado_responsable',
            'fecha_notificacion', 'termino_dias', 'termino_horas', 'fecha_vencimiento',
            'fecha_respuesta', 'radicado_respuesta', 'medio_envio_respuesta',
            'derechos_vulnerados', 'pretensiones',
            'estado_tutela', 'sentido_fallo',
            'requiere_cumplimiento', 'fecha_limite_cumplimiento', 'incidente_desacato', 'observaciones'
        ]
        widgets = {
            'fecha_llegada': forms.DateInput(attrs={'type': 'date'}),
            'fecha_notificacion': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_vencimiento': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_respuesta': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_limite_cumplimiento': forms.DateInput(attrs={'type': 'date'}),
            'derechos_vulnerados': forms.Textarea(attrs={'rows': 2}),
            'pretensiones': forms.Textarea(attrs={'rows': 4}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

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
            'tramite_impartido', 'area_remitir_informacion', 'observaciones'
        ]
        widgets = {
            'fecha_correo': forms.DateInput(attrs={'type': 'date'}),
            'fecha_reparto': forms.DateInput(attrs={'type': 'date'}),
            'fecha_remitente_peticion': forms.DateInput(attrs={'type': 'date'}),
            'fecha_respuesta_peticion': forms.DateInput(attrs={'type': 'date'}),
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
    rol = forms.ChoiceField(choices=[('administrador', 'Administrador'), ('abogado', 'Abogado'), ('invitado', 'Invitado')], required=True)

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
                perfil, created = PerfilUsuario.objects.get_or_create(user=user)
                perfil.legal_rol = self.cleaned_data.get('rol')
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
    rol = forms.ChoiceField(choices=[('administrador', 'Administrador'), ('abogado', 'Abogado'), ('invitado', 'Invitado')], required=False)

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
            permisos = PermisoModelo.objects.filter(user=self.instance, app_label='defenjur')
            perm_dict = {p.model_name: p.permitido for p in permisos}
            for field_name, model_name in self.MAP_PERMS.items():
                self.fields[field_name].initial = perm_dict.get(model_name, False)

    def save(self, commit=True):
        from django.db import transaction
        from usuarios.models import PerfilUsuario, PermisoModelo
        from django.core.cache import cache

        user = super().save(commit=False)
        
        if commit:
            with transaction.atomic():
                user.save()
                
                # 1. Actualizar Perfil
                perfil, created = PerfilUsuario.objects.get_or_create(user=user)
                if self.cleaned_data.get('rol'):
                    perfil.legal_rol = self.cleaned_data.get('rol')
                perfil.legal_nick = user.username
                perfil.save()

                # 2. Guardar Permisos de Módulo (Optimizado con Bulk)
                permisos_actuales = {p.model_name: p for p in PermisoModelo.objects.filter(user=user, app_label='defenjur')}
                objs_to_update = []
                objs_to_create = []
                
                for field_name, model_name in self.MAP_PERMS.items():
                    val = self.cleaned_data.get(field_name, False)
                    if model_name in permisos_actuales:
                        p = permisos_actuales[model_name]
                        if p.permitido != val:
                            p.permitido = val
                            objs_to_update.append(p)
                    else:
                        objs_to_create.append(PermisoModelo(user=user, app_label='defenjur', model_name=model_name, permitido=val))
                
                if objs_to_update:
                    PermisoModelo.objects.bulk_update(objs_to_update, ['permitido'])
                if objs_to_create:
                    PermisoModelo.objects.bulk_create(objs_to_create)

                # 3. Invalidar Cache de Navegación
                cache.delete(f'user_dashboard_nav_{user.id}')
                cache.delete(f'dashboard_structure_{user.id}')
            
        return user


