#!/usr/bin/env python
"""
Script para crear el grupo 'crue_remisiones', el admin y los usuarios operadores.

Ejecutar desde el directorio del proyecto:
    python manage.py shell < scripts/create_users_crue.py

O directamente:
    cd hudn_crue_remisiones_app
    python manage.py shell -c "exec(open('scripts/create_users_crue.py').read())"
"""

from django.contrib.auth.models import User, Group

# ---------------------------------------------------------------------------
# 1. Crear grupo
# ---------------------------------------------------------------------------
GRUPO = 'crue_radiooperadores'
group, created = Group.objects.get_or_create(name=GRUPO)
print(f"Grupo '{GRUPO}': {'creado' if created else 'ya existe'}")

# ---------------------------------------------------------------------------
# 2. Crear admin
# ---------------------------------------------------------------------------
ADMIN_USERNAME = 'admin_crue'
ADMIN_PASSWORD = 'admin_crue2026$'

admin_user, created = User.objects.get_or_create(username=ADMIN_USERNAME)
if created:
    admin_user.set_password(ADMIN_PASSWORD)
    admin_user.is_superuser = True
    admin_user.is_staff = True
    admin_user.first_name = 'Admin'
    admin_user.last_name = 'CRUE'
    admin_user.email = 'admin_crue@hosdenar.gov.co'
    admin_user.save()
    print(f"Admin '{ADMIN_USERNAME}' creado (password: {ADMIN_PASSWORD})")
else:
    print(f"Admin '{ADMIN_USERNAME}' ya existe")
admin_user.groups.add(group)

# ---------------------------------------------------------------------------
# 3. Crear usuarios operadores
# ---------------------------------------------------------------------------
USUARIOS = [
    # (usuario, nombres, apellidos, correo, clave)
    ('asantander', 'AYDA CECILIA', 'SANTANDER MATTA', 'asantander@hosdenar.gov.co', 'asantander2026'),
    ('dnoguera', 'Vanessa', 'Noguera', 'dnoguera@hosdenar.gov.co', 'dnoguera2026'),
    ('jmoncayo', 'JUAN CARLOS', 'MONCAYO RIASCOS', 'jmoncayo@hosdenar.gov.co', 'jmoncayo2026'),
    ('mhigidio', 'María Alejandra', 'Higidio Miranda', 'mhigidio@hosdenar.gov.co', 'mhigidio2026'),
    ('mjimenez', 'Mario Armando', 'Jiménez Ramos', 'mjimenez@hosdenar.gov.co', 'mjimenez2026'),
]

for username, first_name, last_name, email, password in USUARIOS:
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_password(password)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        print(f"  ✓ {username} creado")
    else:
        print(f"  - {username} ya existe")
    user.groups.add(group)

# ---------------------------------------------------------------------------
print(f"\nTotal usuarios en grupo '{GRUPO}': {group.user_set.count()}")
print("Listo.")

