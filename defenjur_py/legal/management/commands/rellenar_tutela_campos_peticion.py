"""
Rellena fecha_correo, solicitante, peticionario y causa en tutelas ya guardadas,
usando fecha_llegada, accionante, accionado, asunto/objeto (misma lógica que la importación CSV).

Uso: python manage.py rellenar_tutela_campos_peticion
     python manage.py rellenar_tutela_campos_peticion --dry-run
"""

from django.core.management.base import BaseCommand

from legal.models import AccionTutela


def _c(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


class Command(BaseCommand):
    help = "Completa campos tipo petición en AccionTutela a partir de datos judiciales ya cargados."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Solo cuenta, no guarda.")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        updated = 0
        for t in AccionTutela.objects.iterator():
            fields = []
            if not _c(t.fecha_correo) and _c(t.fecha_llegada):
                t.fecha_correo = t.fecha_llegada
                fields.append("fecha_correo")
            if not _c(t.solicitante) and _c(t.accionante):
                t.solicitante = t.accionante
                fields.append("solicitante")
            if not _c(t.peticionario) and _c(t.accionado):
                t.peticionario = t.accionado
                fields.append("peticionario")
            if not _c(t.causa):
                a = _c(t.asunto_tutela)
                o = _c(t.objeto_tutela)
                if a or o:
                    t.causa = "\n\n".join(x for x in (a, o) if x)
                    fields.append("causa")
            if fields and not dry:
                t.save(update_fields=fields)
            if fields:
                updated += 1
        msg = f"Registros afectados: {updated}" + (" [dry-run]" if dry else "")
        self.stdout.write(self.style.SUCCESS(msg))
