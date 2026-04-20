from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db import connections
from .models import PerfilUsuario

class RegistroForm(UserCreationForm):
    primer_nombre = forms.CharField(max_length=100, required=True, label="Primer Nombre")
    segundo_nombre = forms.CharField(max_length=100, required=False, label="Segundo Nombre")
    primer_apellido = forms.CharField(max_length=100, required=True, label="Primer Apellido")
    segundo_apellido = forms.CharField(max_length=100, required=False, label="Segundo Apellido")
    email_institucional = forms.EmailField(required=False, label="Correo Institucional")
    email_personal = forms.EmailField(required=True, label="Correo Personal")
    cedula = forms.CharField(max_length=20, required=True, label="Cédula")
    direccion = forms.CharField(max_length=255, required=False, label="Dirección")
    telefono = forms.CharField(max_length=20, required=False, label="Teléfono")
    fecha_nacimiento = forms.DateField(required=False, label="Fecha de Nacimiento", widget=forms.DateInput(attrs={'type': 'date'}))
    sexo = forms.ChoiceField(choices=[('', 'Seleccione'), ('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], required=False)
    grupo_sanguineo = forms.ChoiceField(choices=[('', 'Seleccione'), ('O', 'O'), ('A', 'A'), ('B', 'B'), ('AB', 'AB')], required=False)
    rh = forms.ChoiceField(choices=[('', 'Seleccione'), ('+', '+'), ('-', '-')], required=False)

    class Meta:
        model = User
        fields = ['username']

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if PerfilUsuario.objects.filter(cedula=cedula).exists():
            raise ValidationError("Esta cédula ya se encuentra registrada en el sistema.")
        return cedula

    def clean_username(self):
        username = self.cleaned_data.get('username')
        cedula = self.cleaned_data.get('cedula')
        
        # 1. Verificar si el usuario ya existe en nuestro sistema
        if User.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya está registrado en el Gestor Institucional.")

        # 2. Validar contra Dinámica Nexus (Si cedula está presente)
        if cedula:
            try:
                # Usamos una conexión con timeout corto para no bloquear eternamente
                with connections['readonly'].cursor() as cursor:
                    # Estrategia A: Por Cédula
                    cursor.execute("SELECT USUNOMBRE FROM GENUSUARIO WHERE NumeroDocumento = %s AND USUESTADO = 1", [cedula])
                    usu_row = cursor.fetchone()
                    
                    # Estrategia B: Por Médico
                    if not usu_row:
                        sql_medico = """
                        SELECT U.USUNOMBRE FROM GENUSUARIO U 
                        INNER JOIN GENMEDICO M ON U.USUNOMBRE = M.GMECODIGO 
                        INNER JOIN GENTERCER T ON M.GENTERCER = T.OID 
                        WHERE T.TERNUMDOC = %s AND U.USUESTADO = 1
                        """
                        cursor.execute(sql_medico, [cedula])
                        usu_row = cursor.fetchone()

                    if usu_row:
                        usu_institucional = usu_row[0]
                        if username.lower() != usu_institucional.lower():
                            raise ValidationError(f"Para funcionarios del HUDN, el usuario debe ser exactamente su código institucional: {usu_institucional}")
            except Exception as e:
                # Si es un ValidationError lo relanzamos, si es error de conexión (timeout) dejamos pasar 
                # para no bloquear el registro si la base de datos externa está caída.
                if isinstance(e, ValidationError):
                    raise e
                # Log system error here if logger were available
                pass 

        return username

    def save(self, commit=True):
        user = super(RegistroForm, self).save(commit=False)
        # Combinar nombres para el User model estándar
        user.first_name = f"{self.cleaned_data['primer_nombre']} {self.cleaned_data.get('segundo_nombre', '')}".strip()
        user.last_name = f"{self.cleaned_data['primer_apellido']} {self.cleaned_data.get('segundo_apellido', '')}".strip()
        # Usamos el personal como email principal de la cuenta
        user.email = self.cleaned_data["email_personal"]
        
        if commit:
            user.save()
            from .models import PerfilUsuario
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.cedula = self.cleaned_data.get("cedula")
            perfil.direccion = self.cleaned_data.get("direccion")
            perfil.telefono = self.cleaned_data.get("telefono")
            perfil.fecha_nacimiento = self.cleaned_data.get("fecha_nacimiento")
            perfil.email_personal = self.cleaned_data.get("email_personal")
            perfil.email_institucional = self.cleaned_data.get("email_institucional")
            perfil.sexo = self.cleaned_data.get("sexo")
            perfil.grupo_sanguineo = self.cleaned_data.get("grupo_sanguineo")
            perfil.rh = self.cleaned_data.get("rh")
            perfil.save()
        return user
