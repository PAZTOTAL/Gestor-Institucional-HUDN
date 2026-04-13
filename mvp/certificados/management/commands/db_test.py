import os

from django.core.management.base import BaseCommand

from certificados.services.db import get_connection


class Command(BaseCommand):
    help = "Verifica conexión a SQL Server y cuenta tablas contratos_YYYY."

    def handle(self, *args, **options):
        schema = os.getenv("DB_SCHEMA", "dbo")
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DB_NAME() AS db, SUSER_SNAME() AS usr")
            db_name, user_name = cursor.fetchone()
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = ?
                  AND table_name LIKE 'contratos[_][0-9][0-9][0-9][0-9]'
                ORDER BY table_name
                """,
                schema,
            )
            tables = [row[0] for row in cursor.fetchall()]

        self.stdout.write("Conexion OK")
        self.stdout.write(str({"db": db_name, "usr": user_name}))
        self.stdout.write(
            str({"tablas_contratos_anuales": len(tables), "ejemplo": tables[:3]})
        )
