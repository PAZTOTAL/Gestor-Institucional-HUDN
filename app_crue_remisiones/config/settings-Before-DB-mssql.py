"""
Django settings for config project.
"""

import os
from pathlib import Path

# settings.py (or base.py / dev.py / prod.py depending on your setup)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-fvyg4s259i8yf8+g)bsj!v)r_--bnq$8@+5v63*1u&*f)@9x(!'

DEBUG = True

#ALLOWED_HOSTS = ["*"]
#ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
ALLOWED_HOSTS = [
    '172.20.211.163',
	"172.20.209.60",
	"localhost",
	"127.0.0.1",
]

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "http")

CSRF_TRUSTED_ORIGINS = [
    'http://172.20.10.250',
    'http://172.20.211.163',
    'http://172.20.209.60',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crueremisiones',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
				"django.template.context_processors.csrf",
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'crue_remisiones_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres2026'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Internacionalización ────────────────────────────────────────────────────
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = False

# ─── Archivos estáticos ──────────────────────────────────────────────────────
FORCE_SCRIPT_NAME = '/crue-remisiones'

STATIC_URL       = '/crue-remisiones/static/'
STATIC_ROOT      = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

# ─── Archivos de medios ──────────────────────────────────────────────────────
MEDIA_URL        = '/crue-remisiones/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Modelo de usuario personalizado
AUTH_USER_MODEL = 'crueremisiones.Usuario'

# ─── Autenticación ───────────────────────────────────────────────────────────
LOGIN_URL = '/crue-remisiones/login/'
LOGIN_REDIRECT_URL = '/crue-remisiones/'
LOGOUT_REDIRECT_URL = '/crue-remisiones/login/'

# Email (configurar SMTP en producción)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@hudn.gov.co'
