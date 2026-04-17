from django.db import connections

def check_ids(ids):
    with connections['readonly'].cursor() as cursor:
        placeholders = ', '.join(['%s'] * len(ids))
        # SQL Server often pads with zeros
        padded_ids = [str(i).zfill(15) for i in ids]
        query = f"SELECT NEMCODIGO, NEMNOMCOM FROM NMEMPLEA WHERE NEMCODIGO IN ({placeholders})"
        cursor.execute(query, padded_ids)
        results = cursor.fetchall()
        print(f"Found in NMEMPLEA: {results}")
        
        # Check in NOMEMPLEADO
        query2 = f"SELECT EMPCODIGO, EMPNOMBRE1 FROM NOMEMPLEADO WHERE EMPCODIGO IN ({placeholders})"
        cursor.execute(query2, padded_ids)
        results2 = cursor.fetchall()
        print(f"Found in NOMEMPLEADO: {results2}")

if __name__ == '__main__':
    ids = [1085253706, 1085291427, 98388109, 36950788, 27109141, 1085276465, 30742939, 27097336, 1116247718, 34317408]
    check_ids(ids)
