"""
Servicio para cargar parámetros MEOWS desde el archivo congelado.
Contiene la lógica de negocio para la carga de datos.
"""
from meows.models import ParametroMEOWS, Parametro
from meows.meows_params import MEOWS_PARAMETROS


def cargar_parametros_meows():
    """
    Carga los parámetros MEOWS desde el archivo congelado.
    Carga en ambos modelos: ParametroMEOWS (legacy) y Parametro (nuevo).
    
    Returns:
        tuple: (cargados, existentes) - Cantidad de parámetros nuevos y existentes
    """
    cargados = 0
    existentes = 0
    
    for p in MEOWS_PARAMETROS:
        # Cargar en ParametroMEOWS (legacy)
        parametro_legacy, created_legacy = ParametroMEOWS.objects.get_or_create(
            codigo=p["codigo"],
            defaults={
                "nombre": p["nombre"],
                "unidad": p["unidad"],
                "orden": p["orden"],
            }
        )
        
        # Cargar en Parametro (nuevo modelo genérico)
        parametro, created = Parametro.objects.get_or_create(
            codigo=p["codigo"],
            defaults={
                "nombre": p["nombre"],
                "unidad": p["unidad"],
                "orden": p["orden"],
                "activo": True,
            }
        )
        
        if created:
            cargados += 1
        else:
            existentes += 1
    
    return cargados, existentes

