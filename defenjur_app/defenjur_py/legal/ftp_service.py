"""
Espejo de adjuntos hacia FTP/NAS (misma convención que defenjur-back/helpers/ftpService.js).
Solo actúa si DEFENJUR_FTP_ENABLED=True en settings.
"""
import logging
from ftplib import FTP, error_perm

from django.conf import settings

logger = logging.getLogger(__name__)

FTP_ENTITY_FOLDER = {
    'tutela': 'acciones_tutela',
    'peticion': 'derechos_peticion',
    'proceso_activo': 'proc_judiciales_activa',
    'proceso_pasivo': 'proc_judiciales_pasiva',
    'proceso_terminado': 'proc_judiciales_terminados',
    'peritaje': 'peritajes',
    'pago': 'pagos_sentencias_judiciales',
    'sancionatorio': 'procesos_administrativos_sancionatorios',
    'requerimiento': 'requerimientos_entes_control',
    'extrajudicial': 'proc_extrajudiciales',
}


def _ftp_config():
    return {
        'enabled': getattr(settings, 'DEFENJUR_FTP_ENABLED', False),
        'host': getattr(settings, 'DEFENJUR_FTP_HOST', '') or '',
        'user': getattr(settings, 'DEFENJUR_FTP_USER', '') or '',
        'password': getattr(settings, 'DEFENJUR_FTP_PASSWORD', '') or '',
        'base_path': getattr(settings, 'DEFENJUR_FTP_BASE_PATH', '/web/defenjur_files').rstrip('/'),
    }


def _ftp_mkd_cwd(ftp: FTP, segment: str):
    try:
        ftp.cwd(segment)
    except error_perm:
        try:
            ftp.mkd(segment)
        except error_perm:
            pass
        ftp.cwd(segment)


def _navigate_to_remote_dir(ftp: FTP, remote_dir_abs: str):
    """
    remote_dir_abs: /web/defenjur_files/acciones_tutela/5
    Deja la sesión posicionada en ese directorio.
    """
    parts = [p for p in remote_dir_abs.strip('/').split('/') if p]
    try:
        ftp.cwd('/')
    except error_perm:
        pass
    for p in parts:
        _ftp_mkd_cwd(ftp, p)


def mirror_archivo_adjunto_to_ftp(tipo_asociado: str, id_asociado: int, archivo_field, nombre_original: str):
    cfg = _ftp_config()
    if not cfg['enabled'] or not cfg['host'] or not cfg['user']:
        return
    folder = FTP_ENTITY_FOLDER.get(tipo_asociado)
    if not folder:
        logger.warning('FTP: tipo_asociado desconocido: %s', tipo_asociado)
        return
    path_local = getattr(archivo_field, 'path', None)
    if not path_local:
        return
    remote_dir = f"{cfg['base_path']}/{folder}/{id_asociado}"
    try:
        with FTP() as ftp:
            ftp.connect(cfg['host'], timeout=30)
            ftp.login(cfg['user'], cfg['password'])
            _navigate_to_remote_dir(ftp, remote_dir)
            with open(path_local, 'rb') as fh:
                ftp.storbinary(f'STOR {nombre_original}', fh)
            logger.info('FTP: subido %s/%s', remote_dir, nombre_original)
    except Exception as e:
        logger.warning('FTP: fallo subida (%s id=%s): %s', tipo_asociado, id_asociado, e)
