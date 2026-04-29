"""
Servicio de correo para Paz y Salvo. Envío síncrono en hilo secundario.
"""
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.db import close_old_connections

from .models import EmailLog, PazSalvo, Area


def _send_sync(to: str, subject: str, html: str):
    host = getattr(settings, 'PYS_MAIL_HOST', settings.EMAIL_HOST)
    port = getattr(settings, 'PYS_MAIL_PORT', settings.EMAIL_PORT)
    user = getattr(settings, 'PYS_MAIL_USER', settings.EMAIL_HOST_USER)
    password = getattr(settings, 'PYS_MAIL_PASS', settings.EMAIL_HOST_PASSWORD)
    from_addr = getattr(settings, 'PYS_MAIL_FROM', user) or user

    if not host or not user:
        print(f'[PYS MAIL] SMTP no configurado — correo para {to} no enviado.')
        return

    print(f'[PYS MAIL] Enviando a {to} via {host}:{port} como {user} (from={from_addr})')

    msg = MIMEMultipart('alternative')
    msg['From'] = from_addr
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    with smtplib.SMTP(host, port) as srv:
        srv.ehlo()
        srv.starttls()
        srv.ehlo()  # requerido después de STARTTLS (RFC 3207)
        srv.login(user, password)
        # envelope sender = cuenta autenticada para evitar rechazo de Gmail
        srv.sendmail(user, to, msg.as_string())

    print(f'[PYS MAIL] OK → {to}')


def send_mail_async(to: str, subject: str, html: str, ps_id=None, area_id=None):
    """Lanza el envío en un hilo secundario y registra el resultado en EmailLog."""
    def _worker():
        close_old_connections()
        try:
            _send_sync(to, subject, html)
            _log(ps_id, area_id, to, subject, 'ENVIADO')
        except Exception as e:
            print(f'[PYS MAIL ERROR] {to}: {e}')
            _log(ps_id, area_id, to, subject, 'ERROR', str(e))

    threading.Thread(target=_worker, daemon=True).start()


def _log(ps_id, area_id, destinatario, asunto, estado, error_msg=None):
    try:
        close_old_connections()
        EmailLog.objects.create(
            ps_id=ps_id,
            area_id=area_id,
            destinatario=destinatario,
            asunto=asunto,
            estado=estado,
            error_msg=error_msg,
        )
    except Exception as e:
        print(f'[PYS EMAIL LOG ERROR] {e}')


# ── Template correo validación PS ────────────────────────────────────────────

_ANTI_CLIP = (
    '&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;'
    '&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;'
) * 12


def build_email_ps(ps_dict: dict, area_dict: dict, link: str, nombre_completo: str = '') -> str:
    fecha_retiro = str(ps_dict.get('fecha_retiro', ''))
    nombre_dest = nombre_completo or area_dict.get('responsable', '')
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Validación Paz y Salvo — HUDN</title>
</head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:Arial,Helvetica,sans-serif;">
  <div style="display:none;max-height:0;overflow:hidden;font-size:1px;color:#f0f4f8;">{_ANTI_CLIP}</div>
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f0f4f8;padding:32px 16px;">
    <tr><td align="center">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="max-width:560px;background:#ffffff;border-radius:14px;
                    box-shadow:0 4px 24px rgba(0,0,0,0.09);overflow:hidden;">
        <tr>
          <td style="background:linear-gradient(135deg,#0284c7,#0369a1);padding:28px 32px;text-align:center;">
            <p style="margin:0 0 6px;font-size:13px;color:rgba(255,255,255,0.75);letter-spacing:1px;text-transform:uppercase;">
              Hospital Universitario Departamental de Nariño E.S.E.
            </p>
            <h1 style="margin:0;font-size:20px;font-weight:800;color:#ffffff;">Solicitud de Validación</h1>
            <p style="margin:6px 0 0;font-size:13px;color:rgba(255,255,255,0.85);">Sistema de Paz y Salvos</p>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 32px 0;">
            <p style="margin:0;font-size:14px;color:#475569;line-height:1.6;">
              Estimado(a) <strong style="color:#0f172a;">{nombre_dest}</strong>,
            </p>
            <p style="margin:8px 0 0;font-size:14px;color:#475569;line-height:1.6;">
              Se requiere su validación para el siguiente Paz y Salvo:
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 32px 0;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
              <tr><td style="padding:16px 20px;">
                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td style="padding:5px 0;font-size:12px;color:#64748b;font-weight:700;width:38%;vertical-align:top;">Funcionario</td>
                    <td style="padding:5px 0;font-size:13px;color:#0f172a;font-weight:600;vertical-align:top;">{ps_dict['nombre']}</td>
                  </tr>
                  <tr>
                    <td style="padding:5px 0;font-size:12px;color:#64748b;font-weight:700;vertical-align:top;">Identificación</td>
                    <td style="padding:5px 0;font-size:13px;color:#0f172a;font-weight:600;vertical-align:top;">{ps_dict['identificacion']}</td>
                  </tr>
                  <tr>
                    <td style="padding:5px 0;font-size:12px;color:#64748b;font-weight:700;vertical-align:top;">Cargo</td>
                    <td style="padding:5px 0;font-size:13px;color:#0f172a;font-weight:600;vertical-align:top;">{ps_dict['cargo']}</td>
                  </tr>
                  <tr>
                    <td style="padding:5px 0;font-size:12px;color:#64748b;font-weight:700;vertical-align:top;">Dependencia</td>
                    <td style="padding:5px 0;font-size:13px;color:#0f172a;font-weight:600;vertical-align:top;">{ps_dict['dependencia']}</td>
                  </tr>
                  <tr>
                    <td style="padding:5px 0;font-size:12px;color:#64748b;font-weight:700;vertical-align:top;">Fecha de retiro</td>
                    <td style="padding:5px 0;font-size:13px;color:#0f172a;font-weight:600;vertical-align:top;">{fecha_retiro}</td>
                  </tr>
                </table>
              </td></tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 32px 0;text-align:center;">
            <a href="{link}"
               style="display:inline-block;background:linear-gradient(135deg,#0284c7,#0369a1);
                      color:#ffffff !important;text-decoration:none;font-weight:800;
                      font-size:16px;padding:16px 40px;border-radius:10px;
                      box-shadow:0 4px 14px rgba(2,132,199,0.4);">
              &#10003;&nbsp;&nbsp;Validar Paz y Salvo
            </a>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px 0;text-align:center;">
            <p style="margin:0;font-size:11px;color:#94a3b8;line-height:1.6;">
              Si el botón no funciona, copia y pega este enlace en tu navegador:
            </p>
            <p style="margin:6px 0 0;font-size:10px;color:#94a3b8;word-break:break-all;">{link}</p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px 28px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="border-top:1px solid #e2e8f0;padding-top:20px;">
              <tr>
                <td style="font-size:11px;color:#94a3b8;line-height:1.7;text-align:center;">
                  Este enlace es personal e intransferible. Válido por <strong style="color:#64748b;">72 horas</strong>.<br>
                  No reenvíe este correo a otras personas.<br><br>
                  <strong style="color:#64748b;">Hospital Universitario Departamental de Nariño E.S.E.</strong><br>
                  Sistema de Gestión de Paz y Salvos
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


def enviar_correos_turno(ps_id: int):
    """
    Lee las áreas con validaciones PENDIENTE en el orden más bajo,
    obtiene el correo del validador desde pys_lista_blanca y envía el link.
    Llamar en hilo secundario.
    """
    close_old_connections()

    try:
        _enviar_correos_turno_impl(ps_id)
    except Exception as e:
        print(f'[PYS CORREOS TURNO ERROR] ps_id={ps_id}: {e}')
        import traceback
        traceback.print_exc()


def _enviar_correos_turno_impl(ps_id: int):
    import pyodbc
    from django.conf import settings as dj_settings
    from django.db.models import Min
    from .auth import create_validacion_token
    from .models import Validacion

    try:
        ps = PazSalvo.objects.get(id=ps_id)
    except PazSalvo.DoesNotExist:
        print(f'[PYS CORREOS] PazSalvo id={ps_id} no encontrado')
        return

    # Orden mínimo con pendientes
    min_orden = (
        Validacion.objects.filter(ps=ps, estado='PENDIENTE')
        .aggregate(min_orden=Min('area__orden'))['min_orden']
    )
    if min_orden is None:
        print(f'[PYS CORREOS] ps_id={ps_id} sin validaciones PENDIENTE')
        return

    print(f'[PYS CORREOS] ps_id={ps_id} — procesando turno orden={min_orden}')

    # Validaciones del turno actual
    validaciones = (
        Validacion.objects
        .filter(ps=ps, estado='PENDIENTE', area__orden=min_orden)
        .select_related('area')
    )

    site_url = getattr(dj_settings, 'PYS_SITE_URL', 'http://localhost:8000').rstrip('/')

    for val in validaciones:
        area = val.area

        # Validadores activos de esta área en lista blanca (con correo válido)
        todos_activos = list(
            ListaBlanca.objects.filter(area=area, activo=True)
            .values('id', 'usunombre', 'usuemail', 'nombre', 'rol')
        )
        # Detectar usuarios sin correo (esto causa envíos fallidos silenciosos)
        sin_correo = [lb for lb in todos_activos if not lb['usuemail'].strip()]
        if sin_correo:
            print(f'[PYS CORREOS] Área "{area.nombre}" — {len(sin_correo)} usuario(s) sin correo: {[lb["usunombre"] for lb in sin_correo]}')

        lbs_todos = [lb for lb in todos_activos if lb['usuemail'].strip()]
        # Prioridad: rol validador. Si no hay validadores, usar cualquier activo con correo del área.
        lbs = [lb for lb in lbs_todos if lb['rol'] == 'validador']
        if not lbs:
            lbs = lbs_todos

        if not lbs:
            print(f'[PYS CORREOS] Área "{area.nombre}" (id={area.id}) sin usuarios activos con correo en lista blanca — se omite')
            continue

        print(f'[PYS CORREOS] Área "{area.nombre}" — {len(lbs)} destinatario(s): {[lb["usuemail"] for lb in lbs]}')

        ps_dict = {
            'nombre': ps.nombre,
            'identificacion': ps.identificacion,
            'cargo': ps.cargo,
            'dependencia': ps.dependencia,
            'fecha_retiro': str(ps.fecha_retiro),
        }
        area_dict = {'responsable': area.responsable, 'nombre': area.nombre}

        for lb in lbs:
            token = create_validacion_token(area.id, ps_id, lb['usunombre'])
            link = f"{site_url}/paz-y-salvo/validar/?token={token}"

            # Nombre completo desde SQL Server — opcional, falla silenciosamente
            nombre_completo = lb['nombre'] or area.responsable
            try:
                conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={dj_settings.DATABASES['default']['HOST']},1433;"
                    f"DATABASE={getattr(dj_settings, 'PYS_DB_NEXUS_NAME', 'DGEMPRES_NEXUS')};"
                    f"UID={getattr(dj_settings, 'PYS_DB_NEXUS_USER', '')};"
                    f"PWD={getattr(dj_settings, 'PYS_DB_NEXUS_PASS', '')};"
                    f"TrustServerCertificate=yes;Connection Timeout=3;"
                )
                with pyodbc.connect(conn_str, timeout=3) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT USUDESCRI FROM genusuario WHERE USUNOMBRE = ?",
                        lb['usunombre'],
                    )
                    row = cursor.fetchone()
                    if row and row[0]:
                        nombre_completo = row[0].strip()
            except Exception:
                pass

            html = build_email_ps(ps_dict, area_dict, link, nombre_completo)
            asunto = f"Validación requerida — Paz y Salvo: {ps.nombre}"
            send_mail_async(lb['usuemail'], asunto, html, ps_id=ps_id, area_id=area.id)


from .models import ListaBlanca
