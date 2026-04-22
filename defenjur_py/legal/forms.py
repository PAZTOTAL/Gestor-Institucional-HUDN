from django import forms
from django.contrib.auth import get_user_model
from .models import (
    AccionTutela, DerechoPeticion, ProcesoExtrajudicial, ProcesoJudicialActiva, ProcesoJudicialPasiva,
    Peritaje, PagoSentenciaJudicial, ProcesoJudicialTerminado,
    ProcesoAdministrativoSancionatorio, RequerimientoEnteControl
)

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
    class Meta:
        model = AccionTutela
        fields = ['num_proceso', 'fecha_llegada', 'despacho_judicial', 'cedula_accionante', 'accionante', 'accionado', 'cedula_abogado', 'abogado_responsable']
        widgets = {
            'fecha_llegada': forms.DateInput(attrs={'type': 'date'}),
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
    class Meta:
        model = ProcesoExtrajudicial
        fields = [
            'demandante', 'demandado', 'apoderado',
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
    class Meta:
        model = ProcesoJudicialActiva
        fields = [
            'num_proceso', 'demandante', 'demandado', 'apoderado', 'despacho_actual',
            'medio_control', 'ciudad', 'estimacion_cuantia', 'sentencia_primera_instancia',
            'pretension', 'ultima_actuacion', 'estado_actual',
        ]

class ProcesoJudicialPasivaForm(PremiumModelForm):
    class Meta:
        model = ProcesoJudicialPasiva
        fields = [
            'num_proceso', 'demandante', 'cc_demandante', 'demandado', 'apoderado', 'despacho_actual',
            'medio_control', 'calidad_entidad', 'hecho_generador',
            'valor_pretension_inicial', 'valor_provisionar', 'fallo_sentencia', 'valor_fallo_sentencia',
            'riesgo_perdida', 'porcentaje_probabilidad_perdida',
            'pretensiones', 'hechos_relevantes', 'enfoque_defensa', 'estado_actual', 'observaciones',
        ]

class PeritajeForm(PremiumModelForm):
    class Meta:
        model = Peritaje
        fields = [
            'num_proceso', 'fecha_correo_electronico', 'entidad_remitente_requerimiento',
            'demandante', 'demandado', 'abogado_responsable',
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
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña inicial', required=True)
    rol = forms.ChoiceField(choices=[('administrador', 'Administrador'), ('abogado', 'Abogado'), ('invitado', 'Invitado')], required=True)
    nick = forms.CharField(required=False)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            from usuarios.models import PerfilUsuario
            perfil, created = PerfilUsuario.objects.get_or_create(user=user)
            perfil.legal_rol = self.cleaned_data.get('rol')
            perfil.legal_nick = self.cleaned_data.get('nick') or user.username
            perfil.save()
        return user


class UsuarioHudnUpdateForm(PremiumModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput, label='Nueva contraseña', required=False,
        help_text='Dejar en blanco para no cambiar.',
    )
    rol = forms.ChoiceField(choices=[('administrador', 'Administrador'), ('abogado', 'Abogado'), ('invitado', 'Invitado')], required=False)
    nick = forms.CharField(required=False)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            perfil = getattr(self.instance, 'perfil', None)
            if perfil:
                self.fields['rol'].initial = perfil.legal_rol
                self.fields['nick'].initial = perfil.legal_nick

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get('password')
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
            from usuarios.models import PerfilUsuario
            perfil, created = PerfilUsuario.objects.get_or_create(user=user)
            if self.cleaned_data.get('rol'):
                perfil.legal_rol = self.cleaned_data.get('rol')
            if self.cleaned_data.get('nick'):
                perfil.legal_nick = self.cleaned_data.get('nick')
            perfil.save()
        return user


