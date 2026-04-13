import base64
import io
import json
import os
from ftplib import FTP
from pathlib import Path

import pyodbc
from django.http import FileResponse, HttpResponseNotAllowed, JsonResponse
from dotenv import load_dotenv


load_dotenv()


def get_db_connection():
    driver = os.getenv("DB1_DRIVER", "ODBC Driver 18 for SQL Server")
    server = os.getenv("DB1_SERVER")
    port = os.getenv("DB1_PORT", "1433")
    database = os.getenv("DB1_DATABASE", "SGC_HUDN")
    user = os.getenv("DB1_USER")
    password = os.getenv("DB1_PASSWORD")

    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server},{port};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=10)


def _serialize_datetime(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _serve_base_file(relative_path, content_type):
    base_dir = Path(__file__).resolve().parent.parent
    file_path = base_dir / relative_path
    return FileResponse(open(file_path, "rb"), content_type=content_type)


def static_app_js(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    return _serve_base_file("app.js", "application/javascript")


def static_styles_css(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    return _serve_base_file("styles.css", "text/css")


def static_pdf_lib(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    return _serve_base_file(
        "assets/pdf-lib.min.js",
        "application/javascript",
    )


def parsear_obligaciones(raw):
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def health(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    return JsonResponse({"ok": True, "app": "consulta-externa-contratos"})


def contratos(request, identificacion):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ide_contratista_int
            FROM [SGC_HUDN].[dbo].[JurContratistaInterno]
            WHERE identificacion = ?
            """,
            (identificacion,),
        )
        rows = cursor.fetchall()
        if not rows:
            return JsonResponse([], safe=False)

        ides = [r[0] for r in rows]
        placeholders = ",".join(["?"] * len(ides))
        cursor.execute(
            f"""
            SELECT ide_condiciones, ide_contratista_int, fecha_inicio, fecha_terminacion, obligaciones_especificas
            FROM [SGC_HUDN].[dbo].[jur_condiciones_contratacion]
            WHERE ide_contratista_int IN ({placeholders})
            """,
            tuple(ides),
        )
        condiciones = cursor.fetchall()

        contratos_result = []
        for cond in condiciones:
            ide_condiciones, ide_contratista_int, fecha_inicio, fecha_terminacion, obligaciones = cond

            cursor.execute(
                """
                SELECT TOP 1 numero_contrato
                FROM [SGC_HUDN].[dbo].[jur_contrato]
                WHERE ide_condiciones = ?
                """,
                (ide_condiciones,),
            )
            contrato_row = cursor.fetchone()

            cursor.execute(
                """
                SELECT TOP 1 objeto_contractual, valor_contrato, valor_letras
                FROM [SGC_HUDN].[dbo].[jur_componente_tecnico]
                WHERE ide_contratista_int = ?
                """,
                (ide_contratista_int,),
            )
            componente_row = cursor.fetchone()

            contratos_result.append(
                {
                    "ide_contratista_int": ide_contratista_int,
                    "numero_contrato": contrato_row[0] if contrato_row else "Sin número",
                    "fecha_inicio": _serialize_datetime(fecha_inicio),
                    "fecha_terminacion": _serialize_datetime(fecha_terminacion),
                    "objeto_contractual": componente_row[0] if componente_row else "",
                    "valor_contrato": componente_row[1] if componente_row else 0,
                    "valor_letras": componente_row[2] if componente_row else "",
                    "obligaciones": parsear_obligaciones(obligaciones),
                }
            )

        return JsonResponse(contratos_result, safe=False)
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=500)
    finally:
        if conn:
            conn.close()


def documentos(request, ide_contratista_int):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
              id_documento_contratista,
              nombre_archivo,
              ruta_ftp,
              tamanio_bytes,
              fecha_carga,
              condicion
            FROM (
              SELECT
                id_documento_contratista,
                nombre_archivo,
                ruta_ftp,
                tamanio_bytes,
                fecha_carga,
                condicion,
                ROW_NUMBER() OVER (
                  PARTITION BY id_documento_contratista
                  ORDER BY condicion ASC, fecha_carga DESC
                ) AS rn
              FROM [SGC_HUDN].[dbo].[JurContratistaDocumentos]
              WHERE ide_contratista_int = ?
            ) t
            WHERE rn = 1
            ORDER BY id_documento_contratista ASC
            """,
            (ide_contratista_int,),
        )
        docs = cursor.fetchall()
        payload = [
            {
                "id_documento_contratista": row[0],
                "nombre_archivo": row[1],
                "ruta_ftp": row[2],
                "tamanio_bytes": row[3],
                "fecha_carga": _serialize_datetime(row[4]),
                "condicion": row[5],
            }
            for row in docs
        ]
        return JsonResponse(payload, safe=False)
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=500)
    finally:
        if conn:
            conn.close()


def _download_from_ftp(remote_path):
    host = os.getenv("FTP_HOST")
    port = int(os.getenv("FTP_PORT", "21"))
    user = os.getenv("FTP_USER")
    password = os.getenv("FTP_PASSWORD")

    candidates = [remote_path]
    try:
        candidates.append(remote_path.encode("latin1", errors="ignore").decode("latin1"))
    except Exception:
        pass

    last_error = None
    for path_candidate in candidates:
        ftp_client = FTP()
        try:
            ftp_client.connect(host=host, port=port, timeout=10)
            ftp_client.login(user=user, passwd=password)
            buffer = io.BytesIO()
            ftp_client.retrbinary(f"RETR {path_candidate}", buffer.write)
            ftp_client.quit()
            return buffer.getvalue()
        except Exception as exc:
            last_error = exc
            try:
                ftp_client.close()
            except Exception:
                pass
    raise last_error if last_error else Exception("No se pudo descargar archivo FTP")


def documento(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    ide = request.GET.get("ide")
    id_doc = request.GET.get("idDoc")
    if not ide or not id_doc:
        return JsonResponse({"message": "Parámetros faltantes"}, status=400)

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT TOP 1 ruta_ftp, nombre_archivo, tamanio_bytes
            FROM [SGC_HUDN].[dbo].[JurContratistaDocumentos]
            WHERE ide_contratista_int = ?
              AND id_documento_contratista = ?
            ORDER BY condicion ASC, id DESC
            """,
            (int(ide), int(id_doc)),
        )
        row = cursor.fetchone()
        if not row:
            return JsonResponse({"message": "Documento no encontrado."}, status=404)

        ruta_ftp, nombre_archivo, _ = row
        file_bytes = _download_from_ftp(ruta_ftp)
        file_b64 = base64.b64encode(file_bytes).decode("ascii")
        return JsonResponse(
            {
                "success": True,
                "nombre_archivo": nombre_archivo,
                "archivo_base64": f"data:application/pdf;base64,{file_b64}",
            }
        )
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=500)
    finally:
        if conn:
            conn.close()


def index(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    return _serve_base_file("index.html", "text/html")
