from django.db import connections

def list_subgroups():
    sql = "SELECT TOP 20 GRP.HGRCODIGO, SUB.HSUCODIGO, SUB.HSUDESCRIP FROM HPNSUBGRU AS SUB INNER JOIN HPNGRUPOS AS GRP ON SUB.HPNGRUPOS = GRP.OID WHERE SUB.HSUDESCRIP LIKE '%URGENC%'"
    with connections['readonly'].cursor() as cursor:
        cursor.execute(sql)
        for row in cursor.fetchall():
            print(row)

if __name__ == "__main__":
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HospitalManagement.settings')
    django.setup()
    list_subgroups()
