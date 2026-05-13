"""Servicio de correo para el módulo Asignación de Permisos y Claves."""
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.db import close_old_connections

_ANTI_CLIP = (
    '&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;'
) * 20


def _send_sync(to: str, subject: str, html: str):
    host = getattr(settings, 'PYS_MAIL_HOST', settings.EMAIL_HOST)
    port = getattr(settings, 'PYS_MAIL_PORT', settings.EMAIL_PORT)
    user = getattr(settings, 'PYS_MAIL_USER', settings.EMAIL_HOST_USER)
    password = getattr(settings, 'PYS_MAIL_PASS', settings.EMAIL_HOST_PASSWORD)
    from_addr = getattr(settings, 'PYS_MAIL_FROM', user) or user

    if not host or not user:
        print(f'[APC MAIL] SMTP no configurado — correo para {to} no enviado.')
        return

    msg = MIMEMultipart('alternative')
    msg['From'] = from_addr
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    with smtplib.SMTP(host, port) as srv:
        srv.ehlo()
        srv.starttls()
        srv.ehlo()
        srv.login(user, password)
        srv.sendmail(user, to, msg.as_string())

    print(f'[APC MAIL] OK → {to}')


def send_mail_async(to: str, subject: str, html: str, solicitud_id=None):
    def _worker():
        close_old_connections()
        try:
            _send_sync(to, subject, html)
            _log(solicitud_id, to, subject, 'ENVIADO')
        except Exception as e:
            print(f'[APC MAIL ERROR] {to}: {e}')
            _log(solicitud_id, to, subject, 'ERROR', str(e))

    threading.Thread(target=_worker, daemon=True).start()


def _log(solicitud_id, destinatario, asunto, estado, error_msg=None):
    try:
        close_old_connections()
        from .models import EmailLogAPC
        EmailLogAPC.objects.create(
            solicitud_id=solicitud_id,
            destinatario=destinatario,
            asunto=asunto,
            estado=estado,
            error_msg=error_msg,
        )
    except Exception as e:
        print(f'[APC EMAIL LOG ERROR] {e}')


# ── Templates de correo ──────────────────────────────────────────────────────

def build_email_firma(solicitud_dict: dict, firma_dict: dict, link: str) -> str:
    nombre_dest = firma_dict.get('nombre_firmante', '')
    tipo_label = firma_dict.get('tipo_label', 'Firma requerida')
    nombre_solicitante = solicitud_dict.get('nombres_apellidos', '')
    identificacion = solicitud_dict.get('num_identificacion', '')
    area = solicitud_dict.get('area_servicios', '')
    cargo = solicitud_dict.get('cargo_funcionario', '')

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Firma requerida — HUDN</title>
</head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:Arial,Helvetica,sans-serif;">
  <div style="display:none;max-height:0;overflow:hidden;font-size:1px;color:#f0f4f8;">{_ANTI_CLIP}</div>
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f0f4f8;padding:32px 16px;">
    <tr><td align="center">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="max-width:580px;background:#ffffff;border-radius:14px;
                    box-shadow:0 4px 24px rgba(0,0,0,0.09);overflow:hidden;">
        <tr>
          <td style="background:linear-gradient(135deg,#0f766e,#0d9488);padding:28px 32px;text-align:center;">
            <p style="margin:0 0 6px;font-size:12px;color:rgba(255,255,255,0.75);letter-spacing:1px;text-transform:uppercase;">
              Hospital Universitario Departamental de Nariño E.S.E.
            </p>
            <h1 style="margin:0;font-size:20px;font-weight:800;color:#ffffff;">Firma Requerida</h1>
            <p style="margin:6px 0 0;font-size:13px;color:rgba(255,255,255,0.85);">Asignación de Permisos y Claves — FRSGI-002</p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px 0;">
            <p style="margin:0;font-size:14px;color:#475569;">
              Estimado(a) <strong style="color:#0f172a;">{nombre_dest}</strong>,
            </p>
            <p style="margin:8px 0 0;font-size:14px;color:#475569;">
              Se requiere su firma como <strong>{tipo_label}</strong> para la siguiente solicitud:
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:18px 32px 0;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;">
              <tr><td style="padding:16px 20px;">
                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td style="padding:4px 0;font-size:11px;color:#64748b;font-weight:700;width:38%;vertical-align:top;">Solicitante</td>
                    <td style="padding:4px 0;font-size:13px;color:#0f172a;font-weight:600;vertical-align:top;">{nombre_solicitante}</td>
                  </tr>
                  <tr>
                    <td style="padding:4px 0;font-size:11px;color:#64748b;font-weight:700;vertical-align:top;">Identificación</td>
                    <td style="padding:4px 0;font-size:13px;color:#0f172a;font-weight:600;vertical-align:top;">{identificacion}</td>
                  </tr>
                  <tr>
                    <td style="padding:4px 0;font-size:11px;color:#64748b;font-weight:700;vertical-align:top;">Área</td>
                    <td style="padding:4px 0;font-size:13px;color:#0f172a;font-weight:600;vertical-align:top;">{area}</td>
                  </tr>
                  <tr>
                    <td style="padding:4px 0;font-size:11px;color:#64748b;font-weight:700;vertical-align:top;">Cargo</td>
                    <td style="padding:4px 0;font-size:13px;color:#0f172a;font-weight:600;vertical-align:top;">{cargo}</td>
                  </tr>
                </table>
              </td></tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px 0;text-align:center;">
            <a href="{link}"
               style="display:inline-block;background:linear-gradient(135deg,#0f766e,#0d9488);
                      color:#ffffff !important;text-decoration:none;font-weight:800;
                      font-size:16px;padding:14px 36px;border-radius:10px;
                      box-shadow:0 4px 14px rgba(15,118,110,0.4);">
              ✍&nbsp;&nbsp;Revisar y Firmar
            </a>
          </td>
        </tr>
        <tr>
          <td style="padding:14px 32px 0;text-align:center;">
            <p style="margin:0;font-size:10px;color:#94a3b8;">Si el botón no funciona, copia este enlace:</p>
            <p style="margin:4px 0 0;font-size:10px;color:#94a3b8;word-break:break-all;">{link}</p>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 32px 24px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="border-top:1px solid #e2e8f0;padding-top:16px;">
              <tr>
                <td style="font-size:11px;color:#94a3b8;line-height:1.7;text-align:center;">
                  Enlace personal e intransferible — válido por <strong style="color:#64748b;">72 horas</strong>.<br>
                  <strong style="color:#64748b;">Hospital Universitario Departamental de Nariño E.S.E.</strong><br>
                  Módulo Asignación de Permisos y Claves
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def build_email_completado(solicitud_dict: dict, permisos: list) -> str:
    nombre = solicitud_dict.get('nombres_apellidos', '')
    identificacion = solicitud_dict.get('num_identificacion', '')
    area = solicitud_dict.get('area_servicios', '')
    permisos_html = ''.join(
        f'<span style="display:inline-block;margin:3px;padding:3px 10px;background:#d1fae5;'
        f'color:#065f46;border-radius:99px;font-size:11px;font-weight:700;">{p}</span>'
        for p in permisos
    )
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Solicitud Completada — HUDN</title></head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:32px 16px;">
    <tr><td align="center">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="max-width:560px;background:#fff;border-radius:14px;box-shadow:0 4px 24px rgba(0,0,0,0.09);overflow:hidden;">
        <tr>
          <td style="background:linear-gradient(135deg,#0f766e,#0d9488);padding:28px 32px;text-align:center;">
            <h1 style="margin:0;font-size:20px;font-weight:800;color:#fff;">Solicitud Aprobada</h1>
            <p style="margin:6px 0 0;font-size:13px;color:rgba(255,255,255,0.85);">Asignación de Permisos y Claves — FRSGI-002</p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px;">
            <p style="font-size:14px;color:#475569;">
              La solicitud de <strong>{nombre}</strong> (C.C. {identificacion}) del área <strong>{area}</strong>
              ha sido <strong style="color:#059669;">aprobada y firmada por todos los responsables</strong>.
            </p>
            <p style="font-size:13px;color:#64748b;margin-top:12px;">Permisos y accesos solicitados:</p>
            <div style="margin-top:8px;">{permisos_html or '<em style="color:#94a3b8;font-size:12px;">Ninguno registrado</em>'}</div>
          </td>
        </tr>
        <tr>
          <td style="padding:0 32px 24px;font-size:11px;color:#94a3b8;text-align:center;border-top:1px solid #e2e8f0;padding-top:16px;">
            <strong>Hospital Universitario Departamental de Nariño E.S.E.</strong><br>
            Sistema de Gestión Institucional
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def enviar_correos_firma(solicitud_id: int, orden: int):
    """Envía correos a las firmas del siguiente grupo de orden especificado."""
    close_old_connections()
    try:
        _enviar_correos_impl(solicitud_id, orden)
    except Exception as e:
        import traceback
        print(f'[APC CORREOS ERROR] solicitud_id={solicitud_id} orden={orden}: {e}')
        traceback.print_exc()


def _enviar_correos_impl(solicitud_id: int, orden: int):
    from django.conf import settings as dj_settings
    from .models import SolicitudAPC, FirmaAPC
    from .auth import create_firma_token

    try:
        solicitud = SolicitudAPC.objects.get(id=solicitud_id)
    except SolicitudAPC.DoesNotExist:
        return

    firmas_turno = FirmaAPC.objects.filter(
        solicitud=solicitud,
        orden=orden,
        firmado=False,
        email_firmante__gt='',
    ).exclude(auto_firma_con__isnull=False)  # no enviar a las que se auto-firman

    site_url = getattr(dj_settings, 'PYS_SITE_URL', 'http://localhost:8000').rstrip('/')
    sol_dict = {
        'nombres_apellidos': solicitud.nombres_apellidos,
        'num_identificacion': solicitud.num_identificacion,
        'area_servicios': solicitud.area_servicios,
        'cargo_funcionario': solicitud.cargo_funcionario,
    }

    TIPO_LABELS = {
        'coordinador_area': 'Coordinador de Área',
        'resp_contratista': 'Responsable Contratista',
        'coord_talento_humano': 'Coordinador de Talento Humano',
        'coord_gestion_info': 'Coordinador de Gestión de Información',
    }

    for firma in firmas_turno:
        token = create_firma_token(solicitud_id, firma.tipo_firma, firma.id)
        firma.token_firma = token
        firma.save(update_fields=['token_firma'])

        link = f"{site_url}/asignacion-permisos/firmar/?token={token}"
        firma_dict = {
            'nombre_firmante': firma.nombre_firmante,
            'tipo_label': TIPO_LABELS.get(firma.tipo_firma, firma.tipo_firma),
        }
        html = build_email_firma(sol_dict, firma_dict, link)
        asunto = f"Firma requerida — Asignación de Permisos y Claves: {solicitud.nombres_apellidos}"
        send_mail_async(firma.email_firmante, asunto, html, solicitud_id=solicitud_id)


def enviar_correos_carnet(solicitud_id: int):
    """Notifica a los destinatarios de carnet/tarjeta_chip con todos los datos del solicitante."""
    close_old_connections()
    try:
        from .models import SolicitudAPC, PermisoSolicitado, DestinatarioRol
        solicitud = SolicitudAPC.objects.get(id=solicitud_id)

        permisos_carnet = list(
            PermisoSolicitado.objects.filter(
                solicitud=solicitud,
                permiso_clave__in=['carnet', 'tarjeta_chip'],
            ).values_list('permiso_clave', flat=True)
        )
        if not permisos_carnet:
            return

        destinatarios = list(
            DestinatarioRol.objects.filter(
                permiso_clave__in=permisos_carnet, activo=True
            ).values('email', 'nombre').distinct()
        )

        foto_tag = ''
        if solicitud.foto_carnet:
            foto_tag = (
                f'<tr><td style="padding:12px 20px 0;">'
                f'<p style="margin:0 0 6px;font-size:11px;color:#64748b;font-weight:700;">FOTO PARA CARNET</p>'
                f'<img src="{solicitud.foto_carnet}" alt="Foto carnet"'
                f'     style="max-width:150px;max-height:180px;border-radius:8px;border:1px solid #e2e8f0;">'
                f'</td></tr>'
            )

        tipos_label = {'carnet': 'Carnet', 'tarjeta_chip': 'Tarjeta con Chip'}
        tipos_str = ', '.join(tipos_label.get(c, c) for c in permisos_carnet)

        html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Solicitud de Carnet — HUDN</title></head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:Arial,sans-serif;">
  <div style="display:none;max-height:0;overflow:hidden;font-size:1px;color:#f0f4f8;">{_ANTI_CLIP}</div>
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f4f8;padding:32px 16px;">
    <tr><td align="center">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="max-width:580px;background:#fff;border-radius:14px;box-shadow:0 4px 24px rgba(0,0,0,0.09);overflow:hidden;">
        <tr>
          <td style="background:linear-gradient(135deg,#0f766e,#0d9488);padding:28px 32px;text-align:center;">
            <p style="margin:0 0 6px;font-size:12px;color:rgba(255,255,255,0.75);letter-spacing:1px;text-transform:uppercase;">
              Hospital Universitario Departamental de Nariño E.S.E.
            </p>
            <h1 style="margin:0;font-size:20px;font-weight:800;color:#fff;">Solicitud de Carnet</h1>
            <p style="margin:6px 0 0;font-size:13px;color:rgba(255,255,255,0.85);">Asignación de Permisos y Claves — FRSGI-002</p>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 32px 0;">
            <p style="margin:0;font-size:13px;color:#475569;">
              Se ha recibido una solicitud de <strong style="color:#0f172a;">{tipos_str}</strong>
              con los siguientes datos:
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:14px 32px 0;">
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;">
              <tr><td style="padding:16px 20px;">
                <table width="100%" cellpadding="0" cellspacing="0">
                  <tr>
                    <td style="padding:4px 0;font-size:11px;color:#64748b;font-weight:700;width:38%;vertical-align:top;">Nombre completo</td>
                    <td style="padding:4px 0;font-size:13px;color:#0f172a;font-weight:600;">{solicitud.nombres_apellidos}</td>
                  </tr>
                  <tr>
                    <td style="padding:4px 0;font-size:11px;color:#64748b;font-weight:700;vertical-align:top;">Identificación</td>
                    <td style="padding:4px 0;font-size:13px;color:#0f172a;font-weight:600;">{solicitud.num_identificacion}</td>
                  </tr>
                  <tr>
                    <td style="padding:4px 0;font-size:11px;color:#64748b;font-weight:700;vertical-align:top;">Área</td>
                    <td style="padding:4px 0;font-size:13px;color:#0f172a;font-weight:600;">{solicitud.area_servicios}</td>
                  </tr>
                  <tr>
                    <td style="padding:4px 0;font-size:11px;color:#64748b;font-weight:700;vertical-align:top;">Cargo</td>
                    <td style="padding:4px 0;font-size:13px;color:#0f172a;font-weight:600;">{solicitud.cargo_funcionario}</td>
                  </tr>
                  <tr>
                    <td style="padding:4px 0;font-size:11px;color:#64748b;font-weight:700;vertical-align:top;">Tipo de sangre</td>
                    <td style="padding:4px 0;font-size:13px;color:#0f172a;font-weight:600;">{solicitud.tipo_sangre or '—'}</td>
                  </tr>
                  <tr>
                    <td style="padding:4px 0;font-size:11px;color:#64748b;font-weight:700;vertical-align:top;">Período contrato</td>
                    <td style="padding:4px 0;font-size:13px;color:#0f172a;font-weight:600;">{solicitud.periodo_inicio} al {solicitud.periodo_fin}</td>
                  </tr>
                  <tr>
                    <td style="padding:4px 0;font-size:11px;color:#64748b;font-weight:700;vertical-align:top;">Tipo vinculación</td>
                    <td style="padding:4px 0;font-size:13px;color:#0f172a;font-weight:600;">{solicitud.get_tipo_vinculacion_display()}</td>
                  </tr>
                  <tr>
                    <td style="padding:4px 0;font-size:11px;color:#64748b;font-weight:700;vertical-align:top;">Tipo(s) de carnet</td>
                    <td style="padding:4px 0;font-size:13px;color:#0d9488;font-weight:700;">{tipos_str}</td>
                  </tr>
                </table>
              </td></tr>
            </table>
          </td>
        </tr>
        {foto_tag}
        <tr>
          <td style="padding:20px 32px 24px;font-size:11px;color:#94a3b8;text-align:center;border-top:1px solid #e2e8f0;margin-top:16px;">
            <strong>Hospital Universitario Departamental de Nariño E.S.E.</strong><br>
            Módulo Asignación de Permisos y Claves — FRSGI-002
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

        seen = set()
        for dest in destinatarios:
            email = dest['email']
            if not email or email in seen:
                continue
            seen.add(email)
            asunto = f"Solicitud de Carnet — {solicitud.nombres_apellidos}"
            send_mail_async(email, asunto, html, solicitud_id=solicitud_id)

    except Exception as e:
        import traceback
        print(f'[APC CARNET ERROR] {e}')
        traceback.print_exc()


def enviar_correos_completado(solicitud_id: int):
    """Envía el formato completado a los destinatarios según permisos solicitados."""
    close_old_connections()
    try:
        from .models import SolicitudAPC, PermisoSolicitado, DestinatarioRol, PermisoAccesoConfig
        solicitud = SolicitudAPC.objects.get(id=solicitud_id)

        permisos_claves = list(
            PermisoSolicitado.objects.filter(solicitud=solicitud)
            .values_list('permiso_clave', flat=True)
        )

        etiquetas_map = {
            p.clave: p.etiqueta
            for p in PermisoAccesoConfig.objects.filter(clave__in=permisos_claves)
        }
        permisos_etiquetas = [etiquetas_map.get(c, c) for c in permisos_claves]

        destinatarios = list(
            DestinatarioRol.objects.filter(
                permiso_clave__in=permisos_claves, activo=True
            ).values('email', 'nombre').distinct()
        )

        sol_dict = {
            'nombres_apellidos': solicitud.nombres_apellidos,
            'num_identificacion': solicitud.num_identificacion,
            'area_servicios': solicitud.area_servicios,
            'cargo_funcionario': solicitud.cargo_funcionario,
        }

        seen_emails = set()
        for dest in destinatarios:
            email = dest['email']
            if email in seen_emails:
                continue
            seen_emails.add(email)
            html = build_email_completado(sol_dict, permisos_etiquetas)
            asunto = f"Solicitud aprobada — Permisos y Claves: {solicitud.nombres_apellidos}"
            send_mail_async(email, asunto, html, solicitud_id=solicitud_id)

    except Exception as e:
        import traceback
        print(f'[APC COMPLETADO ERROR] {e}')
        traceback.print_exc()
