from django import forms
from .models import FRQUI_001_Model

class FRQUI_001_Form(forms.ModelForm):
    class Meta:
        model = FRQUI_001_Model
        exclude = ['formato_maestro', 'paciente_oid', 'usuario_registro', 'ip_registro', 'dispositivo']
        widgets = {
            'hora_egreso': forms.TimeInput(attrs={'type': 'time'}),
            'cuidados_especiales': forms.Textarea(attrs={'rows': 2, 'class': 'custom-textarea'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campos de identificación que tendrán lupa/búsqueda
        lookup_fields = [
            'auxiliar_entrega_id', 'auxiliar_recibe_id', 
            'enfermeria_entrega_id', 'enfermeria_recibe_id', 
            'firma_enfermera_id'
        ]
        
        # Campos de nombre que se auto-completan
        display_fields = [
            'auxiliar_entrega_nombre', 'auxiliar_recibe_nombre', 
            'enfermeria_entrega_nombre', 'enfermeria_recibe_nombre', 
            'firma_enfermera_nombre'
        ]

        # Aplicar clases uniformes y widgets de radio para SI/NO/NA
        for field_name, field in self.fields.items():
            if field_name.endswith('_status'):
                field.widget = forms.RadioSelect(
                    choices=FRQUI_001_Model.SI_NO_NA_CHOICES,
                    attrs={'class': 'radio-inline'}
                )
                field.initial = 'NA'
            
            # Clase base para todos los inputs
            if not isinstance(field.widget, forms.RadioSelect):
                existing_class = field.widget.attrs.get('class', '')
                base_class = f"{existing_class} form-input-modern".strip()
                
                if field_name in lookup_fields:
                    base_class += " field-id-lookup"
                if field_name in display_fields:
                    base_class += " field-name-display bg-slate-50"
                    # field.widget.attrs['readonly'] = True # Opcional: desbloquear si el usuario lo pide
                
                field.widget.attrs['class'] = base_class
