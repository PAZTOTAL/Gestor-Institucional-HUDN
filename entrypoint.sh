#!/bin/bash
set -e

echo "→ Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "→ Aplicando migraciones..."
python manage.py migrate

echo "→ Iniciando servidor Gunicorn..."
exec gunicorn HospitalManagement.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --worker-class gthread \
    --threads 4 \
    --timeout 120 \
    --preload \
    --access-logfile - \
    --error-logfile -
