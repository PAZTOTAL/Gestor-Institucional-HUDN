"""JWT auth para el módulo Asignación de Permisos y Claves."""
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from django.conf import settings


def _secret():
    return getattr(settings, 'APC_JWT_SECRET',
                   getattr(settings, 'PYS_JWT_SECRET', settings.SECRET_KEY))


def create_token(payload: dict, expire_hours: int = None) -> str:
    hours = expire_hours or getattr(settings, 'APC_JWT_EXPIRE_HOURS', 8)
    exp = datetime.now(timezone.utc) + timedelta(hours=hours)
    data = {**payload, 'exp': exp}
    return pyjwt.encode(data, _secret(), algorithm='HS256')


def decode_token(token: str) -> dict:
    try:
        return pyjwt.decode(token, _secret(), algorithms=['HS256'])
    except pyjwt.ExpiredSignatureError:
        raise ValueError('Token expirado')
    except pyjwt.InvalidTokenError:
        raise ValueError('Token inválido')


def create_firma_token(solicitud_id: int, tipo_firma: str, firma_id: int) -> str:
    return create_token(
        {
            'solicitud_id': solicitud_id,
            'tipo_firma': tipo_firma,
            'firma_id': firma_id,
            'tipo': 'firma_apc',
        },
        expire_hours=72,
    )
