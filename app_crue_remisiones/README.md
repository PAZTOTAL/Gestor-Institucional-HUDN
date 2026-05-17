# Sistema web de REMISIONES DE USUARIOS COMENTADOS POR CRUE, ESE, SAS, EPS

El sistema **CRUE Remisiones Pacientes** es una aplicacion web Django que reemplaza el uso de hojas de calculo para el registro, gestion y reporte de remisiones de pacientes comentados por CRUE, ESE, SAS y EPSs. Permite a los usuarios (RADIOPERADORES y DIRECTOR) registrar remisiones con autocompletado de campos, visualizar registros en una tabla estilo Excel, importar datos desde Excel y generar reportes en Excel. El acceso esta protegido por autenticacion con roles. Los registros del dia actual pueden editarse y eliminarse; los registros de dias anteriores son de solo lectura (Registro_Historico), preservando la integridad historica.

## Objetivos de Diseno

- Reemplazar el flujo de trabajo en Excel con una aplicacion web Django.
- Minimizar el esfuerzo de digitacion mediante valores por defecto y autoformato.
- Garantizar integridad historica: registros de dias anteriores son inmutables.
- Diseno portable: SQLite para MVP, PostgreSQL para pruebas, MSSQL para producción, todo via Django ORM exclusivamente.
- UI responsiva con tabla estilo Excel, modales y panel lateral colapsable.
- Importacion masiva desde Excel con validacion atomica.

## LOG
May/16/26: r0.9995 : Report ordered by fecha ASC

May/15/26: r0.9994 : Added CRUE_RUNTYPE

May/14/26: r0.9993 : Fixed timezone in form (stripped).
May/14/26: r0.9992 : Added complete CRUD to admin

May/14/26: r0.9991 : Before change win server local to service
May/14/26: r0.999 : Config as app in win server

May/12/26: r0.998 : Standarized settings.py: USE_TZ=T, no LOCAL, three DBs

May/12/26: r0.997 : Added text truncation when migrating from excel file

May/12/26: r0.996 : Integrated HUDN crue_remisiones with config for testing

May/07/26: r0.996 : Using a external DB. User taken from global django project. Ready for deploying as a module.

May/07/26: r0.995 : changed to work with subpath: /crue-remisiones/. Before unifying to default user model.

May/06/26: r0.994 : After new changes (not tested): pagination, editable reg, medico_hudn charfield.

May/06/26: r0.994 : Before new changes: pagination, editable reg, medico_hudn charfield.
May/05/26: r0.994 : Improved UX interaction: Search by doc/name. No range filter. Clear obs and diag. Add Dr. DX:
May/04/26: r0.993 : Improved UX: Filters autoupdate.
May/04/26: r0.992 : Improved getDate format in excelToCsv: validating only current date

May/04/26: r0.991 : Added excel sheet selection, for the different months.
May/04/26: r0.99 : Renamed app 'remisiones' to 'crueremisiones' and 'UsuariCrue' to 'Usuario'
May/04/26: r0.98 : Fixed statics and user creation. Before rename model entities.
May/04/26: r0.97 : Improved UX: sorting. Fixed importing from excel. Removed PDFs.

May/03/26: r0.96 : Added excelToCsv function in utils-lg.py. Added 'especialidad'. Added docs
Abr/28/26: r0.95 : Testing by real users and data. Added 'Especialidad'. UX filling response date.
Abr/28/26: r0.94 : Testing by real users and data.
Abr/28/26: r0.93 : Fixed user reqs: full cloning, secure delete. Changed logo.
Abr/27/26: r0.92 : Ready for testing.
Abr/26/26: r0.91 : Running with logos and PG DB
Abr/23/26: r0.90 : Requirements (90%), Design (90%), tasks (80%)

