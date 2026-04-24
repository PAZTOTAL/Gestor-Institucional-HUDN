from django.db import models
from django import forms
from .models import (
    EmpresaTercerizada, ContratoTercerizado, ActividadTercerizado,
    ServidorTercerizado, AsignacionOrganigrama, AfiliacionSeguridad
)


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = EmpresaTercerizada
        exclude = ['registrado_por', 'fecha_registro']
        widgets = {
            'nit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NIT sin dígito de verificación'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razón social de la empresa'}),
            'representante_legal': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_servicio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Aseo, Vigilancia'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ContratoForm(forms.ModelForm):
    class Meta:
        model = ContratoTercerizado
        exclude = ['registrado_por', 'fecha_registro']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'numero_contrato': forms.TextInput(attrs={'class': 'form-control'}),
            'objeto_contrato': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor_contrato': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'documento_contrato': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ActividadForm(forms.ModelForm):
    class Meta:
        model = ActividadTercerizado
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ServidorForm(forms.ModelForm):
    class Meta:
        model = ServidorTercerizado
        exclude = ['registrado_por', 'fecha_registro', 'modificado_por',
                   'fecha_modificacion', 'en_dinamica', 'fecha_verificacion_dinamica']
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'numero_documento': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_numero_documento',
                'autocomplete': 'off',
                'placeholder': 'Ingrese el número de documento'
            }),
            'primer_nombre': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_primer_nombre'}),
            'segundo_nombre': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_segundo_nombre'}),
            'primer_apellido': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_primer_apellido'}),
            'segundo_apellido': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_segundo_apellido'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'grupo_sanguineo': forms.Select(attrs={'class': 'form-select'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'pais_nacimiento': forms.Select(attrs={'class': 'form-select'}),
            'departamento_nacimiento': forms.Select(attrs={'class': 'form-select'}),
            'municipio_nacimiento': forms.Select(attrs={'class': 'form-select'}),
            'direccion_residencia': forms.TextInput(attrs={'class': 'form-control'}),
            'municipio_residencia': forms.Select(attrs={'class': 'form-select'}),
            'foto': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'documento_pdf': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'contrato': forms.Select(attrs={'class': 'form-select'}),
            'activo_hospital': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fecha_ingreso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_retiro': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class AsignacionForm(forms.ModelForm):
    class Meta:
        model = AsignacionOrganigrama
        exclude = ['servidor']
        widgets = {
            'organigrama_nivel1': forms.Select(attrs={'class': 'form-select'}),
            'organigrama_nivel2': forms.Select(attrs={'class': 'form-select'}),
            'organigrama_nivel3': forms.Select(attrs={'class': 'form-select'}),
            'organigrama_nivel4': forms.Select(attrs={'class': 'form-select'}),
            'organigrama_nivel5': forms.Select(attrs={'class': 'form-select'}),
            'organigrama_nivel6': forms.Select(attrs={'class': 'form-select'}),
            'actividad': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'verificado_por': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class AfiliacionForm(forms.ModelForm):
    class Meta:
        model = AfiliacionSeguridad
        exclude = ['servidor']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'nombre_entidad': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_afiliacion': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_afiliacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vigente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'documento_soporte': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        }
