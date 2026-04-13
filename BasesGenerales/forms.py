from django import forms
from .models import DocumentoDeIdentidad

class DocumentoDeIdentidadForm(forms.ModelForm):
    class Meta:
        model=DocumentoDeIdentidad
        fields="__all__"
        widgets={
            "codigo":forms.TextInput(attrs={
                "type":"number",
                "min":"0",
                "oninput":"this.value=this.value.replace(/[^0-9]/g,'');",
                "placeholder":"Solo números"
            })
        }


