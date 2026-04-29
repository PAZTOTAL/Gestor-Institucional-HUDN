"""
Configuración de Django para pruebas.
Usa base de datos en memoria y backend de email en memoria.
"""
from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Deshabilitar validadores de contraseña en pruebas
AUTH_PASSWORD_VALIDATORS = []

# Usar hasher rápido en pruebas
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
