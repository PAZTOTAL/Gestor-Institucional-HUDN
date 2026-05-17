"""Servicio de generación de reportes Excel para traslados."""

import io

import openpyxl
from django.utils import timezone


# Encabezados en español en el orden definido por el modelo Traslado
ENCABEZADOS = [
	'FECHA REPORTE',
	'FECHA EGRESO',
	'FECHA INGRESO',
	'NOMBRE DE PACIENTE',
	'DOCUMENTO',
	'SERVICIO',
	'QUIEN REPORTA',
	'DESTINO',
	'PROCEDIMIENTO',
	'MÉDICO',
	'AUX. ENFERMERÍA',
	'CONDUCTOR',
	'RADIO OPERADOR',
	'AMBULANCIA DE TRASLADO',
	'OBSERVACIÓN',
]


def generarExcel (queryset, mes):
	"""Genera un archivo Excel con los registros del queryset dado.

	Crea un libro de trabajo con una hoja única que contiene los encabezados
	en español y una fila por cada registro de Traslado. Si el queryset
	está vacío, retorna el archivo con solo los encabezados.

	Args:
		queryset: QuerySet de Traslado con los registros a incluir.
		mes: Número de mes (1–12) usado para nombrar el archivo.

	Returns:
		tuple: (bytes del archivo .xlsx, nombre del archivo str)
	"""
	libro = openpyxl.Workbook ()
	hoja = libro.active
	hoja.title = f'Traslados Mes {mes}'

	# Escribir encabezados
	hoja.append (ENCABEZADOS)

	# Escribir una fila por registro
	for registro in queryset:
		# Convertir a hora local y eliminar tzinfo para compatibilidad con openpyxl
		fechaReporte = timezone.localtime (registro.fecha_reporte).replace (tzinfo=None) if registro.fecha_reporte else ''
		fechaEgreso = timezone.localtime (registro.fecha_egreso).replace (tzinfo=None) if registro.fecha_egreso else ''
		fechaIngreso = timezone.localtime (registro.fecha_ingreso).replace (tzinfo=None) if registro.fecha_ingreso else ''
		fila = [
			fechaReporte,
			fechaEgreso,
			fechaIngreso,
			registro.nombre_paciente,
			registro.documento,
			registro.servicio,
			registro.quien_reporta,
			registro.destino,
			registro.procedimiento,
			registro.medico,
			registro.aux_enfermeria,
			registro.conductor,
			registro.radio_operador,
			registro.ambulancia,
			registro.observacion,
		]
		hoja.append (fila)

	# Serializar a bytes en memoria
	buffer = io.BytesIO ()
	libro.save (buffer)
	buffer.seek (0)


	from datetime import datetime

	meses = {
		1: 'Enero', 2: 'Febrero', 3: 'Marzo',
		4: 'Abril', 5: 'Mayo', 6: 'Junio',
		7: 'Julio', 8: 'Agosto', 9: 'Septiembre',
		10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
	}

	ahora = datetime.now()

	fecha_actual = f"{ahora.year}-{meses[ahora.month]}-{ahora.day:02d}"

	nombreArchivo = f"reporte_traslados_{fecha_actual}.xlsx"

	return buffer.getvalue(), nombreArchivo
