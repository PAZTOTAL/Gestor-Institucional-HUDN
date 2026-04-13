from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db import connections

class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo Electrónico")
    first_name = forms.CharField(max_length=100, required=True, label="Nombre")
    last_name = forms.CharField(max_length=100, required=True, label="Apellido")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        # Validar contra Dinámica Nexus (GENUSUARIO)
        try:
            with connections['readonly'].cursor() as cursor:
                # Se utiliza UPPER() si el sistema almacena en mayúsculas
                cursor.execute("SELECT USUNOMBRE FROM GENUSUARIO WHERE UPPER(USUNOMBRE) = UPPER(%s)", [username])
                row = cursor.fetchone()
                if not row:
                    raise ValidationError("El usuario proporcionado no existe en la base de datos de Dinámica (GENUSUARIO). Debe registrarse usando su usuario institucional.")
        except Exception as e:
            if isinstance(e, ValidationError):
                raise e
            # En caso de que falle la conexión a la bd readonly, registrar error y rechazar
            print(f"Error verificando en Dinámica: {str(e)}")
            raise ValidationError("Error al verificar el usuario con el sistema central. Intente más tarde.")

        return username

    def save(self, commit=True):
        user = super(RegistroForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user
