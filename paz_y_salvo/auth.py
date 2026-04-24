"""
JWT + MD5 VB.NET compatible auth para Paz y Salvo.
Compatible con el sistema hospitalario legacy (VB.NET).
"""
import hashlib
import base64
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from django.conf import settings


def md5_vbnet(password: str) -> str:
    """MD5 UTF-16 LE + Base64, compatible con VB.NET UnicodeEncoding."""
    raw = password.encode('utf-16-le')
    digest = hashlib.md5(raw).digest()
    return base64.b64encode(digest).decode('ascii')


def create_token(payload: dict, expire_hours: int = None) -> str:
    hours = expire_hours or getattr(settings, 'PYS_JWT_EXPIRE_HOURS', 8)
    exp = datetime.now(timezone.utc) + timedelta(hours=hours)
    data = {**payload, 'exp': exp}
    return pyjwt.encode(data, settings.PYS_JWT_SECRET, algorithm='HS256')


def decode_token(token: str) -> dict:
    try:
        return pyjwt.decode(token, settings.PYS_JWT_SECRET, algorithms=['HS256'])
    except pyjwt.ExpiredSignatureError:
        raise ValueError('Token expirado')
    except pyjwt.InvalidTokenError:
        raise ValueError('Token inválido')


def create_validacion_token(area_id: int, ps_id: int, usunombre: str) -> str:
    return create_token(
        {'area_id': area_id, 'ps_id': ps_id, 'usunombre': usunombre, 'tipo': 'validacion'},
        expire_hours=72,
    )
