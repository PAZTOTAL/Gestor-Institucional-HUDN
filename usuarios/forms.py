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
            conn = connections['readonly']
            cursor = None
            try:
                # Asegurar conexión activa
                conn.ensure_connection()
                cursor = conn.cursor()
                
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
            except ValidationError as ve:
                raise ve
            except Exception as e:
                # Si falla la conexión, cerramos para limpiar el pool y seguimos
                try:
                    conn.close()
                except:
                    pass
                pass 
            finally:
                if cursor:
                    try:
                        cursor.close()
                    except:
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

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={'placeholder': 'Ingrese su correo electrónico registrado', 'class': 'form-input'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise ValidationError("No existe ningún usuario registrado con este correo electrónico.")
        return email

class PasswordResetCodeForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        label="Código de Recuperación",
        widget=forms.TextInput(attrs={'placeholder': '000000', 'class': 'form-input text-center tracking-widest text-2xl font-bold'})
    )

class PasswordResetConfirmForm(forms.Form):
    password = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'placeholder': 'Nueva contraseña', 'class': 'form-input'})
    )
    confirm_password = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar contraseña', 'class': 'form-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Las contraseñas no coinciden.")
        return cleaned_data
