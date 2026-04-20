from django.db import connections

def check_ids(ids):
    with connections['readonly'].cursor() as cursor:
        id_strs = [str(i) for i in ids]
        placeholders = ', '.join(['%s'] * len(id_strs))
        
        # Check in NMEMPLEA
        query = f"SELECT NEMCODIGO, NEMNOMCOM FROM NMEMPLEA WHERE RTRIM(LTRIM(NEMCODIGO)) IN ({placeholders})"
        cursor.execute(query, id_strs)
        print(f"Found in NMEMPLEA (trimmed): {cursor.fetchall()}")
        
        # Check in NOMEMPLEADO
        query2 = f"SELECT EMPCODIGO, EMPNOMBRE1 FROM NOMEMPLEADO WHERE RTRIM(LTRIM(EMPCODIGO)) IN ({placeholders})"
        cursor.execute(query2, id_strs)
        print(f"Found in NOMEMPLEADO (trimmed): {cursor.fetchall()}")

if __name__ == '__main__':
    ids = [1085253706, 1085291427, 98388109, 36950788, 27109141, 1085276465, 30742939, 27097336, 1116247718, 34317408]
    check_ids(ids)
