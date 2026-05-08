from .settings import *  # noqa: F401, F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Desactivar logging en tests para no ensuciar la salida
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {},
    'root': {
        'handlers': [],
        'level': 'CRITICAL',
    },
}
