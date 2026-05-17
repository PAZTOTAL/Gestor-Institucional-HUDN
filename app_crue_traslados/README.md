# Sistema web para el registro y gestión de servicios de traslado de pacientes.
Sistema web Django para el registro y gestión de servicios de traslado de pacientes. Reemplaza el proceso actual basado en hojas de cálculo Excel, permitiendo a los usuarios (FUNCIONARIO y DIRECTOR) registrar, consultar, editar y eliminar registros de traslados, generar reportes en Excel y PDF, y controlar el cierre mensual de registros. El sistema no conserva datos históricos; los registros son limpiados por el DIRECTOR cuando se requiere reiniciar el sistema.

## LOG
May/16/26: r0.92 : Fixed session expired problem.

May/13/26: r0.91 : Fixed pagination. Removed obligatory fields. Converted to module

May/10/26: r0.91 : Before to convert to module for main Gestion Repo

May/02/26: r0.90 : Added excelToCsv function in utils-lg.py. Added 'especialidad'. Added docs

Abr/28/26: r1.14 : Removed PDFs. Showing month name.
Abr/28/26: r1.13 : Testing on linux VM.
Abr/22/26: r1.12 : First running version: OK. Needs hospital logos (UX, Reports). Testing. Daily backup.

