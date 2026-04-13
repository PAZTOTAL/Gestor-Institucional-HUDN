from django import forms
from .models import (
    RegistroAnestesia, EvaluacionPreAnestesica, Monitoreo, Ventilacion,
    Medicamentos, Liquidos, SignosVitales, Tecnica, Salida, Observaciones
)

class RegistroAnestesiaForm(forms.ModelForm):
    class Meta:
        model = RegistroAnestesia
        fields = ['paciente', 'sala', 'diagnostico_pre', 'cirugia_propuesta']
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-control select2'}),
            'sala': forms.TextInput(attrs={'class': 'form-control'}),
            'diagnostico_pre': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cirugia_propuesta': forms.Select(attrs={'class': 'form-control select2'}),
        }

    def __init__(self, *args, **kwargs):
        from consultas_externas.models import Genpacien
        super().__init__(*args, **kwargs)
        # Prevent loading all 580k records on initial render
        self.fields['paciente'].queryset = Genpacien.objects.none()

        if 'paciente' in self.data:
            try:
                oid = int(self.data.get('paciente'))
                self.fields['paciente'].queryset = Genpacien.objects.filter(pk=oid)
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset
        elif self.instance.pk:
            self.fields['paciente'].queryset = Genpacien.objects.filter(pk=self.instance.paciente.pk)

class EvaluacionPreAnestesicaForm(forms.ModelForm):
    class Meta:
        model = EvaluacionPreAnestesica
        exclude = ['registro']
        widgets = {
            'antecedentes_patologicos': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'antecedentes_quirurgicos': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'antecedentes_farmacologicos': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'antecedentes_alergicos': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'antecedentes_toxicos': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'rayos_x_comentario': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'plan_anestesia': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class MonitoreoForm(forms.ModelForm):
    class Meta:
        model = Monitoreo
        exclude = ['registro']
        widgets = {
             'otro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Especificar otro monitor...'}),
        }

class VentilacionForm(forms.ModelForm):
    class Meta:
        model = Ventilacion
        exclude = ['registro']

class MedicamentosForm(forms.ModelForm):
    class Meta:
        model = Medicamentos
        exclude = ['registro']
        widgets = {
             'hora': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

class LiquidosForm(forms.ModelForm):
    class Meta:
        model = Liquidos
        exclude = ['registro']

class SignosVitalesForm(forms.ModelForm):
    class Meta:
        model = SignosVitales
        exclude = ['registro']
        widgets = {
             'hora': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

class TecnicaForm(forms.ModelForm):
    class Meta:
        model = Tecnica
        exclude = ['registro']
        widgets = {
             'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        general = cleaned_data.get('general')
        regional = cleaned_data.get('regional')
        sedacion = cleaned_data.get('sedacion')
        combinada = cleaned_data.get('combinada')
        # local = cleaned_data.get('local') # If local exists in model

        if not any([general, regional, sedacion, combinada]):
             raise forms.ValidationError("Debe seleccionar al menos una técnica anestésica (General, Regional, Sedación, etc.).")
        return cleaned_data

class SalidaForm(forms.ModelForm):
    class Meta:
        model = Salida
        exclude = ['registro']
        widgets = {
             'diagnostico_post': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
             'cirugia_realizada': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class ObservacionesForm(forms.ModelForm):
    class Meta:
        model = Observaciones
        exclude = ['registro']
        widgets = {
             'texto': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
