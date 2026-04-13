import os

from django.core.management.base import BaseCommand

from certificados.services.db import get_connection


def q(value):
    return f"[{str(value).replace(']', ']]')}]"


class Command(BaseCommand):
    help = "Crea columna calculada e índice de cédula normalizada en tablas contratos_YYYY."

    def handle(self, *args, **options):
        db_schema = os.getenv("DB_SCHEMA", "dbo")
        max_retries = int(os.getenv("DB_INDEX_RETRIES", "4"))
        max_year = int(os.getenv("DB_MAX_CONTRACT_YEAR", "2026"))

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = ?
                  AND table_name LIKE 'contratos[_][0-9][0-9][0-9][0-9]'
                  AND TRY_CONVERT(INT, RIGHT(table_name, 4)) <= ?
                ORDER BY table_name
                """,
                db_schema,
                max_year,
            )
            tables = [row[0] for row in cursor.fetchall()]

        failed = []
        for table_name in tables:
            done = False
            for attempt in range(1, max_retries + 1):
                try:
                    with get_connection() as conn:
                        cursor = conn.cursor()
                        full_table = f"{q(db_schema)}.{q(table_name)}"
                        index_name = f"IX_{table_name}_cedula_nit_digits"
                        sql_text = f"""
                            IF COL_LENGTH('{db_schema}.{table_name}', 'cedula_nit_digits') IS NULL
                            BEGIN
                              ALTER TABLE {full_table}
                              ADD cedula_nit_digits AS REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(CAST([cedula_nit] AS NVARCHAR(100)), '-', ''), '.', ''), ' ', ''), '/', ''), ',', ''), '(', ''), ')', ''), CHAR(9), ''), CHAR(10), ''), CHAR(13), '') PERSISTED;
                            END

                            IF NOT EXISTS (
                              SELECT 1
                              FROM sys.indexes
                              WHERE name = '{index_name}'
                                AND object_id = OBJECT_ID('{db_schema}.{table_name}')
                            )
                            BEGIN
                              CREATE INDEX {q(index_name)} ON {full_table} ([cedula_nit_digits]);
                            END
                        """
                        cursor.execute(sql_text)
                        conn.commit()
                    self.stdout.write(f"Indexado OK: {db_schema}.{table_name}")
                    done = True
                    break
                except Exception as error:
                    if attempt == max_retries:
                        failed.append({"table": table_name, "reason": str(error)})
                        self.stderr.write(f"Fallo {db_schema}.{table_name}: {error}")
                    else:
                        self.stdout.write(f"Reintento {attempt}/{max_retries - 1} para {db_schema}.{table_name}...")
            if not done:
                continue

        if failed:
            self.stderr.write(
                "Tablas pendientes de indexar: " + ", ".join([item["table"] for item in failed])
            )
            raise SystemExit(1)
        self.stdout.write("Proceso completado.")
