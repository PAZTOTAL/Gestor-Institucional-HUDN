from django.contrib import admin
from .models import (
    opsComponenteTecnico,
    opsCondiciones,
    opsObligacionesGenerales,
    opsObligacionesEspecificas,
    ops3_1AspectosLegales,
    ops3_2AspectosIdoneidad,
    ops3_2AspectosExperiencia,
    ops33_ValorTotaldelContratoyformadepago,
    ops4garantias,
    ops4garantiasDetalle,
    ops4dependencia,
    ops4viabilidad,
    ops4Disponibilidad,
    ops4aceptaGerencia,
)

admin.site.register(opsComponenteTecnico)
admin.site.register(opsCondiciones)
admin.site.register(opsObligacionesGenerales)
admin.site.register(opsObligacionesEspecificas)
admin.site.register(ops3_1AspectosLegales)
admin.site.register(ops3_2AspectosIdoneidad)
admin.site.register(ops3_2AspectosExperiencia)
admin.site.register(ops33_ValorTotaldelContratoyformadepago)
admin.site.register(ops4garantias)
admin.site.register(ops4garantiasDetalle)
admin.site.register(ops4dependencia)
admin.site.register(ops4viabilidad)
admin.site.register(ops4Disponibilidad)
admin.site.register(ops4aceptaGerencia)
