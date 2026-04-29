import os
from pathlib import Path

BASE_DIR = Path (__file__).resolve ().parent.parent

SECRET_KEY = 'django-insecure-cambia-esto-en-produccion'

DEBUG = True

#--------------------------------------------------------------------
# Autenticación por email (Requisito 6.4, 6.5)
# Si ambos están vacíos, el login deniega acceso por defecto
# Lista de correos/domini permitidos para la gestion de la app
#--------------------------------------------------------------------
EMAIL_WHITELIST = ["lgarreta@yahoo.com", "lgarreta@gmail.com"]
EMAIL_DOMINIO_PERMITIDO = 'hodenar.gov.co'

#--------------------------------------------------------------------
# Twilio — Notificaciones SMS (Requisito 10)
#--------------------------------------------------------------------
#TWILIO_ACCOUNT_SID = os.getenv ('TWILIO_ACCOUNT_SID')
#TWILIO_AUTH_TOKEN  = os.getenv ('TWILIO_AUTH_TOKEN')
#TWILIO_FROM_NUMBER = os.getenv ('TWILIO_FROM_NUMBER')

TWILIO_ACCOUNT_SID = 'ACb8b354d4f5b40698eeb6df0b9726f94c'
TWILIO_AUTH_TOKEN  = '3fdfa0e15c3392a522ac48245b81bacf'
TWILIO_FROM_NUMBER = '+19382046901'
#--------------------------------------------------------------------

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'app_autenticacion',
	'app_core',
	'app_notificaciones',
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

ROOT_URLCONF = 'quiroinfo.urls'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [BASE_DIR / 'templates'],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',
			],
		},
	},
]

WSGI_APPLICATION = 'quiroinfo.wsgi.application'

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql',
		'NAME': 'quiroinfo',
		'USER': 'postgres',
		'PASSWORD': 'postgres2026',
		'HOST': 'localhost',
		'PORT': '5432',
	}
}

AUTH_PASSWORD_VALIDATORS = [
	{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
	{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
	{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
	{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Sesión: expira tras 120 minutos de inactividad (Requisito 6.6)
SESSION_COOKIE_AGE = 7200

LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'handlers': {
		'consola': {
			'class': 'logging.StreamHandler',
			'stream': 'ext://sys.stdout'  # 👈 this is key
		},
	},
	'root': {
		'handlers': ['consola'],
		'level': 'INFO',
	},
}
