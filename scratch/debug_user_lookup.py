from django.db import connections

def find_user_by_cedula(cedula):
    with connections['readonly'].cursor() as cursor:
        # Strategy 1: Direct NumeroDocumento
        cursor.execute("SELECT USUNOMBRE, USUDESCRI FROM GENUSUARIO WHERE NumeroDocumento = %s", [cedula])
        res = cursor.fetchone()
        if res:
            return f"FOUND in GENUSUARIO.NumeroDocumento: {res[0]} ({res[1]})"

        # Strategy 2: Join via GENMEDICO (Medical staff)
        # GENUSUARIO.USUNOMBRE = GENMEDICO.GMECODIGO
        # GENMEDICO.GENTERCER = GENTERCER.OID
        # GENTERCER.TERNUMDOC = cedula
        sql = """
        SELECT U.USUNOMBRE, U.USUDESCRI
        FROM GENUSUARIO U
        INNER JOIN GENMEDICO M ON U.USUNOMBRE = M.GMECODIGO
        INNER JOIN GENTERCER T ON M.GENTERCER = T.OID
        WHERE T.TERNUMDOC = %s
        """
        cursor.execute(sql, [cedula])
        res = cursor.fetchone()
        if res:
            return f"FOUND in GENUSUARIO via GENMEDICO/GENTERCER: {res[0]} ({res[1]})"

        # Strategy 3: Search for USUNOMBRE starting with cedula
        cursor.execute("SELECT USUNOMBRE, USUDESCRI FROM GENUSUARIO WHERE USUNOMBRE LIKE %s", [cedula + '%'])
        res = cursor.fetchone()
        if res:
            return f"FOUND in GENUSUARIO.USUNOMBRE (LIKE): {res[0]} ({res[1]})"
            
        return "NOT FOUND in any known path"

if __name__ == "__main__":
    import sys
    cedula = sys.argv[1] if len(sys.argv) > 1 else "13498870" # Example from a previous log if any
    print(find_user_by_cedula(cedula))
