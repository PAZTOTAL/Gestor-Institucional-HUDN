# Sistema web de REMISIONES DE USUARIOS COMENTADOS POR CRUE, ESE, SAS, EPS

El sistema **CRUE Remisiones Pacientes** es una aplicacion web Django que reemplaza el uso de hojas de calculo para el registro, gestion y reporte de remisiones de pacientes comentados por CRUE, ESE, SAS y EPSs. Permite a los usuarios (RADIOPERADORES y DIRECTOR) registrar remisiones con autocompletado de campos, visualizar registros en una tabla estilo Excel, importar datos desde Excel y generar reportes en Excel. El acceso esta protegido por autenticacion con roles. Los registros del dia actual pueden editarse y eliminarse; los registros de dias anteriores son de solo lectura (Registro_Historico), preservando la integridad historica.

## Objetivos de Diseno

- Reemplazar el flujo de trabajo en Excel con una aplicacion web Django.
- Minimizar el esfuerzo de digitacion mediante valores por defecto y autoformato.
- Garantizar integridad historica: registros de dias anteriores son inmutables.
- Diseno portable: SQLite para MVP, migracion transparente a PostgreSQL/SQL Server via Django ORM exclusivamente.
- UI responsiva con tabla estilo Excel, modales y panel lateral colapsable.
- Importacion masiva desde Excel con validacion atomica.

## LOG
Abr/28/26: r0.95 : Testing by real users and data. Added 'Especialidad'. UX filling response date.

Abr/28/26: r0.94 : Testing by real users and data.

Abr/28/26: r0.93 : Fixed user reqs: full cloning, secure delete. Changed logo.

Abr/27/26: r0.92 : Ready for testing.

Abr/26/26: r0.91 : Running with logos and PG DB
Abr/23/26: r0.90 : Requirements (90%), Design (90%), tasks (80%)

