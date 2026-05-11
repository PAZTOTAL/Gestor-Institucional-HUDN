#!/usr/bin/python 

import pandas as pd
import sys
from pathlib import Path

"""
excel_to_csv_fralg062.py
========================
Validates the structure of the FRALG-062 Excel sheet and exports
only the data rows to a clean CSV file.

Expected sheet structure
------------------------
Row  1	: Title block (col D: "REMISIONES DE USUARIOS COMENTADOS POR CRUE, ESE, SAS, EPS")
Row  7	: Year/month label (col A: "AÑO:", col L: "MES: ")
Row  9	: Main column headers  (31 non-None columns across A–AE)
Row  10 : Sub-column headers   (17 sub-headers)
Rows 11+ : Data rows (col A is a consecutive integer row number)

Column layout (1-based Excel columns → CSV header)
---------------------------------------------------
Col  1	A	no
Col  2	B	fecha
Col  3	C	hora
Col  4	D	nombre_paciente
Col  5	E	tipo_documento
Col  6	F	identificacion
Col  7	G	gestante_si			 ← sub-header "SI"	under "GESTANTE"
Col  8	H	gestante_no			 ← sub-header "NO"
Col  9	I	sexo_m				 ← sub-header "M"	under "SEXO EDAD"
Col 10	J	sexo_f				 ← sub-header "F"
Col 11	K	edad				 ← sub-header "ED"
Col 12	L	diagnostico
Col 13	M	sv_ta				 ← sub-header "TA"	under "SIGNOS VITALES"
Col 14	N	sv_fc				 ← sub-header "FC"
Col 15	O	sv_fr				 ← sub-header "FR"
Col 16	P	sv_temperatura		 ← sub-header "T°"
Col 17	Q	sv_spo2				 ← sub-header "SPO2"
Col 18	R	sv_glasgow			 ← sub-header "Glasgow"
Col 19	S	eps
Col 20	T	institucion_reporta
Col 21	U	municipio
Col 22	V	medico_refiere
Col 23	W	medico_hudn_confirma
Col 24	X	radio_operador
Col 25	Y	observacion
Col 26	Z	aceptado_si			 ← sub-header "SI"	 under "ACEPTADO"
Col 27	AA	aceptado_no			 ← sub-header "NO"
Col 28	AB	aceptado_urg_vital	 ← sub-header "URG VITAL"
Col 29	AC	aceptado_fecha		 ← sub-header "FECHA"
Col 30	AD	aceptado_hora		 ← sub-header "HORA"
Col 31	AE	oportunidad
"""

HEADERS = [
	"no","fecha","hora","nombre","tipoId","id","gestSi","gestNo","sexM","sexF",
	"edad","diagnostico","ta","fc","fr","tm","spo2","glasgow","eps",
	"institucion","municipio","medRefiere","medHudn","radioop","obs",
	"aceptaSi","aceptaNo","aceptaURG","fechaRes","horaRes","oportunidad"
]

#--------------------------------------------------------------------
#--------------------------------------------------------------------
def main ():
	if len (sys.argv) < 2:
		print ("Usage: python script.py input.xlsx [output.csv]")
		sys.exit (1)

	input_file = sys.argv[1]
	output_file = sys.argv[2] if len (sys.argv) > 2 else None

	excelToCsv (input_file, output_file)

#--------------------------------------------------------------------
#--------------------------------------------------------------------
def excelToCsv (input_path: str, output_path: str = None, sheet_name=None):
	import os
	try:
		df	 = excel_to_clean_df (input_path, sheet_name=sheet_name)
		row  = None
		rows = []	# Rows for dataframe
		output_path = os.path.basename (input_path.split (".")[0] + ".csv")
		for _, r in df.iterrows ():
			gestSi, gestNo = getBool (r[6], r[7], "SI", "NO")
			sexF, sexM	   = getBool (r[9], r[8], "F", "M")
			acepSi, acepNo, acepUrg = getBoolTri (r[25], r[26], r[27])		 # AceptaSI
			nombre, id	   = getText (r[3]), getText (r[5])
			if not nombre and not id:
				continue
			row = [
				r[0],
				getDate (r[1]), getTime (r[2]), getText (r[3]), getTipoId (r[4]), getText (r[5]),  #...tipoId, id
				gestSi, gestNo, sexM, sexF, getText (r[10]), getText (r[11]),					   #...edad, diagnostico
				getRate (r[12]), getInt (r[13]), getInt (r[14]), getFloat (r[15]), getFloat (r[16]), getRate (r[17]), #...Glasgow
				getText (r[18]), getText (r[19]), getText (r[20]),								   #...municipo,
				getText (r[21]), getText (r[22]), getText (r[23]), getText (r[24]),				   #...observacion
				acepSi, acepNo, acepUrg, getDate (r[28]), getTime (r[29]),					 #...fecha_res, hora_res
				getOportunidad (r[1],r[2],r[28],r[29])											   #...oportunidad
			]
			rows.append (row)

		# Create a dataframe and a Remision object
		newDf = pd.DataFrame (rows, columns=HEADERS)
		newDf.to_csv (output_path, index=False, encoding="utf-8")

		print (f"✅ CSV created at: {output_path}")
		return newDf
	except Exception as ex:
		print (f"+++ {ex=}")
		raise Exception (f"Error importando excel to csv: Error en fila: {row}")
	return None


#--------------------------------------------------------------------
#--------------------------------------------------------------------
def excel_to_clean_df (input_path: str, sheet_name=None) -> pd.DataFrame:
	"""
	Reads Excel starting from row 11 and applies fixed headers.
	Returns a cleaned DataFrame.
	If sheet_name is provided, reads that specific sheet; otherwise reads the first sheet.
	"""
	kwargs = {
		'skiprows': 10,
		'header': None,
		'dtype': str,
	}
	if sheet_name:
		kwargs['sheet_name'] = sheet_name

	df = pd.read_excel (input_path, **kwargs)

	# Trim to expected number of columns
	df = df.iloc[:, :len (HEADERS)]

	# Assign headers
#	 df.columns = HEADERS

	# Basic cleanup
	df = df.dropna (how="all")	  # remove empty rows
	df = df.fillna ("")			  # replace NaN with empty string
	df = df.apply (lambda col: col.str.strip() if col.dtype == "object" else col)

	return df


#--------------------------------------------------------------------
# Formatting functions for each column
#--------------------------------------------------------------------
import re
from datetime import datetime

def _combinar_fecha_hora (fecha_str, hora_str):
	"""
	Combines date string 'YYYY-MM-DD' and time string 'HH:MM' into a datetime.
	Returns None if either is empty/None.
	Returns None if combination is invalid.
	"""
	from datetime import datetime as _datetime
	fecha_s = str(fecha_str or '').strip()
	hora_s = str(hora_str or '').strip()
	if not fecha_s or not hora_s:
		return None
	try:
		return _datetime.strptime(f'{fecha_s} {hora_s}', '%Y-%m-%d %H:%M')
	except ValueError:
		return None



def getDate (x):
	if not x:
		return None
	try:
		dt = datetime.fromisoformat (str(x))
		return dt.date ()
	except:
		try:
			return datetime.strptime (str(x), "%Y-%m-%d").date()
		except:
			return None



#--------------------------------------------------------------------
# Parse a date and ensure it belongs to the current year.
# Raises:
#	 ValueError if:
#	 format is invalid
#	 year is not current year
#--------------------------------------------------------------------
def getDate(x):
	if not x:
		return None

	raw = str(x).strip()

	# Try ISO first
	try:
		dt = datetime.fromisoformat(raw)
	except Exception:
		try:
			dt = datetime.strptime(raw, "%Y-%m-%d")
		except Exception:
			raise ValueError(f"Invalid date format: {raw}")

	current_year = datetime.now().year

	if dt.year != current_year:
		raise ValueError( f"Año inválido {dt.year} (esperado {current_year}) valor actual: {raw}")

	return dt.date()


def getTime (x):
	if not x or str (x).lower() == 'nan':
		return None

	s = str (x).strip()

	# 1. Extract time part if datetime string (covers Excel "1900-01-01 HH:MM:SS")
	if " " in s:
		s = s.split (" ")[-1]  # take time part

	# 2. Try parsing HH:MM[:SS]
	try:
		t = datetime.strptime (s, "%H:%M:%S").time()
		return f"{t.hour:02d}:{t.minute:02d}"
	except:
		try:
			t = datetime.strptime (s, "%H:%M").time()
			return f"{t.hour:02d}:{t.minute:02d}"
		except:
			pass

	# 3. Fallback regex (for messy strings)
	m = re.search (r'(\d{1,2}):(\d{2})', s)
	if m:
		h = int (m.group(1))
		mnt = int (m.group(2))
		return f"{h:02d}:{mnt:02d}"

	return None

def getText (x):
	return str (x).strip() if x else ""

def getTipoId (x):
	valid = {"CC", "TI", "CE", "RC", "CN"}
	x = str (x).strip().upper() if x else ""
	return x if x in valid else "CC"

def getBool (x, y, xVal, yVal):
	if (x and y) or (not x and not y):
		return "", yVal
	return ("", yVal) if y else (xVal, "")


def getRate (x):
	if not x:
		return "NO REFIERE"
	x = str (x).strip()
	if re.match (r"^\d+/\d+$", x):
		return x
	return "NO REFIERE"

def getInt (x):
	try:
		return str (int(float(x)))
	except:
		return "NO REFIERE"

def getFloat (x):
	try:
		return str (float(x))
	except:
		return "NO REFIERE"

def getBoolTri (x, y, w):
	res = ("","NO","")
	if (x and y and w) or (not x and not y and not w ):
		res = ("", "NO", "")
	if x:
		res = ("SI", "", "")
	if w:
		res = ("", "", "URG VITAL")
	if y:
		res = ("", "NO", "")
	return res

def getOportunidad (x1, y1, x2, y2):
	#print (f"+++ {x1=} {y1=} {x2=} {y2=}")
	try:
		x1 = getDate (x1)
		y1 = getTime (y1)
		x2 = getDate (x2)
		y2 = getTime (y2)

		dt1 = datetime.fromisoformat (f"{x1} {y1}")
		dt2 = datetime.fromisoformat (f"{x2} {y2}")
		diff = dt2 - dt1

		total_minutes = int (diff.total_seconds() // 60)
		h = total_minutes // 60
		m = total_minutes % 60

		return f"{h:02d}:{m:02d}"
	except Exception as ex:
		print (f"+++ {x1=} {y1=} {x2=} {y2=} {ex=}")
		return None

#--------------------------------------------------------------------
#--------------------------------------------------------------------
if __name__ == "__main__":
	main ()
