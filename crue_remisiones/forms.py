from django import forms

from .models import Remision
from .services import validar_edad, validar_glasg, validar_ta


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Usuario', max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario', 'autofocus': True}),
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
    )


class RemisionForm(forms.ModelForm):
    class Meta:
        model = Remision
        fields = [
            'fecha', 'nombre', 'tipo_doc', 'doc', 'gest', 'sexo', 'edad', 'especialidad',
            'diagnostico', 'ta', 'fc', 'fr', 'tm', 'spo2', 'glasg',
            'eps', 'institucion_reporta', 'municipio',
            'medico_refiere', 'medico_hudn', 'radio_operador',
            'observacion', 'aceptado', 'fecha_res',
        ]
        widgets = {
            'fecha': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_doc': forms.Select(attrs={'class': 'form-select'}),
            'doc': forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'numeric'}),
            'gest': forms.Select(attrs={'class': 'form-select', 'id': 'id_gest'}),
            'sexo': forms.Select(attrs={'class': 'form-select', 'id': 'id_sexo'}),
            'especialidad': forms.TextInput(attrs={'class': 'form-control'}),
            'edad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 25 AÑOS, 3 MESES, 10 DIAS'}),
            'diagnostico': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'style': 'resize:vertical'}),
            'ta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '120/80 o NO REFIERE'}),
            'fc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Valor o NO REFIERE'}),
            'fr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Valor o NO REFIERE'}),
            'tm': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '36° o NO REFIERE', 'id': 'id_tm'}),
            'spo2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '98% o NO REFIERE', 'id': 'id_spo2'}),
            'glasg': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '15/15 o NO REFIERE'}),
            'eps': forms.TextInput(attrs={'class': 'form-control'}),
            'institucion_reporta': forms.TextInput(attrs={'class': 'form-control'}),
            'municipio': forms.TextInput(attrs={'class': 'form-control'}),
            'medico_refiere': forms.TextInput(attrs={'class': 'form-control'}),
            'medico_hudn': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '300'}),
            'radio_operador': forms.TextInput(attrs={'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'style': 'resize:vertical'}),
            'aceptado': forms.Select(attrs={'class': 'form-select'}),
            'fecha_res': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_res'].required = False
        for field in ['especialidad', 'diagnostico', 'ta', 'fc', 'fr', 'tm', 'spo2', 'glasg',
                      'eps', 'institucion_reporta', 'municipio',
                      'medico_refiere', 'medico_hudn', 'radio_operador', 'observacion']:
            self.fields[field].required = False
        self.fields['fecha'].input_formats = ['%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M']
        self.fields['fecha_res'].input_formats = ['%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M']

    def clean_edad(self):
        valor = self.cleaned_data.get('edad', '').strip()
        if valor and not validar_edad(valor):
            raise forms.ValidationError('Formato inválido. Use: número + AÑOS, MESES o DIAS. Ej: 25 AÑOS')
        return valor

    def clean_ta(self):
        valor = self.cleaned_data.get('ta', '').strip()
        if valor and not validar_ta(valor):
            raise forms.ValidationError('Formato inválido. Use fracción (ej: 120/80) o NO REFIERE.')
        return valor

    def clean_glasg(self):
        valor = self.cleaned_data.get('glasg', '').strip()
        if valor and not validar_glasg(valor):
            raise forms.ValidationError('Formato inválido. Use fracción (ej: 15/15) o NO REFIERE.')
        return valor

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if not fecha:
            raise forms.ValidationError('La fecha de ingreso es obligatoria.')
        return fecha

    def clean_doc(self):
        valor = self.cleaned_data.get('doc', '').strip()
        if valor and not valor.isdigit():
            raise forms.ValidationError('El documento debe contener solo números.')
        return valor

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        fecha_res = cleaned_data.get('fecha_res')
        if fecha and fecha_res and fecha_res < fecha:
            raise forms.ValidationError('La fecha de respuesta no puede ser anterior a la fecha de ingreso.')
        return cleaned_data


class CambiarPasswordForm(forms.Form):
    password_actual = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password_nueva = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8,
    )
    password_confirmacion = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        nueva = cleaned_data.get('password_nueva')
        confirmacion = cleaned_data.get('password_confirmacion')
        if nueva and confirmacion and nueva != confirmacion:
            raise forms.ValidationError('La nueva contraseña y su confirmación no coinciden.')
        return cleaned_data


class ImportarExcelForm(forms.Form):
    archivo = forms.FileField(
        label='Archivo Excel',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'}),
    )

    def clean_archivo(self):
        archivo = self.cleaned_data['archivo']
        nombre = archivo.name.lower()
        if not (nombre.endswith('.xlsx') or nombre.endswith('.xls')):
            raise forms.ValidationError('Solo se permiten archivos .xlsx o .xls.')
        return archivo
