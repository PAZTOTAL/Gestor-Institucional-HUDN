import csv
import io
import zipfile
from datetime import datetime
from django.db.models import Sum, Count
from consultas_externas.models import Slnfactur, Genpacien, Adningreso, Slnserhoj, Genserips

class RipsGenerator:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.provider_code = "1234567890" # Placeholder or fetch from config
        self.files = {}
        self.invoices = []
        self.patients = set()
        self.control_data = []

    def generate(self):
        # 1. Fetch Invoices
        self.invoices = Slnfactur.objects.filter(
            sfafecfac__range=[self.start_date, self.end_date],
            sfadocanu=False  # Exclude annulled (?)
        ).select_related('adningreso', 'adningreso__genpacien')

        if not self.invoices.exists():
            return None

        # 2. Generate Files
        self.generate_af()
        self.generate_us()
        self.generate_services() # AC, AP, etc.
        self.generate_ct()

        # 3. Create ZIP
        return self.create_zip()

    def format_date(self, date_obj):
        if not date_obj:
            return ""
        return date_obj.strftime("%d/%m/%Y")

    def format_decimal(self, value):
        if value is None:
            return "0"
        return "{:.2f}".format(value).replace(".", ",")

    def clean_text(self, text, length):
        if not text:
            return ""
        return str(text)[:length].strip()

    def generate_af(self):
        rows = []
        for inv in self.invoices:
            # Basic mapping - adjust fields as per actual data model
            row = [
                self.provider_code,
                "RAZON SOCIAL PRESTADOR", # Placeholder
                "NI", # Provider ID Type
                "900123456", # Provider ID
                inv.sfanumfac,
                self.format_date(inv.sfafecfac),
                self.format_date(inv.sfafecini),
                self.format_date(inv.sfafecfin),
                "EPS001", # Payer Code - needs mapping
                "NOMBRE EPS", # Payer Name
                "CONTRATO",
                "PLAN",
                "", # Policy
                self.format_decimal(inv.sfaabopac), # Copago
                "0", # Comision
                self.format_decimal(inv.sfavaldes), # Descuentos
                self.format_decimal(inv.sfavalpag)  # Net to pay
            ]
            rows.append(",".join(map(str, row)))
            
            # Collect patients for US file
            if inv.adningreso and inv.adningreso.genpacien:
                self.patients.add(inv.adningreso.genpacien.oid)

        self.files['AF'] = rows
        self.control_data.append(['AF', len(rows)])

    def generate_us(self):
        rows = []
        # Fetch unique patients
        patients_db = Genpacien.objects.filter(oid__in=self.patients)
        
        for pat in patients_db:
            # Map Document Type (Integer to Code)
            tipdoc_map = {1: 'CC', 2: 'TI', 3: 'CE', 4: 'RC', 5: 'PA', 6: 'AS', 7: 'MS'}
            tipdoc = tipdoc_map.get(pat.pactipdoc, 'CC')

            row = [
                tipdoc,
                pat.pacnumdoc,
                "EPS001", # Admin Code
                "1", # User Type (1=Contributivo, etc.) select default
                self.clean_text(pat.pacpriape, 30),
                self.clean_text(pat.pacsegape, 30),
                self.clean_text(pat.pacprinom, 20),
                self.clean_text(pat.pacsegnom, 20),
                "30", # Age - need calculation
                "1", # Unit Age (1=Years)
                "M" if pat.gpasexpac == 1 else "F", # Sex
                "52", # Dept Code
                "001", # Muni Code
                "U" # Zone
            ]
            rows.append(",".join(map(str, row)))

        self.files['US'] = rows
        self.control_data.append(['US', len(rows)])

    def generate_services(self):
        # This discriminates between AC, AP, AM, etc.
        # For simplicity in this iteration, I'll create placeholder lists
        # In a real impl, query Slnserhoj linked to Slnfactur
        
        # Placeholder for AC
        ac_rows = []
        # Logic to fetch consultations...
        # self.files['AC'] = ac_rows
        # if ac_rows: self.control_data.append(['AC', len(ac_rows)])
        pass

    def generate_ct(self):
        rows = []
        for file_code, count in self.control_data:
            filename = f"{file_code}000001" # Serial needs to be dynamic normally
            row = [
                self.provider_code,
                self.format_date(datetime.now()),
                filename,
                count
            ]
            rows.append(",".join(map(str, row)))
        self.files['CT'] = rows

    def create_zip(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for code, lines in self.files.items():
                if not lines: continue
                filename = f"{code}000001.txt"
                content = "\r\n".join(lines)
                zip_file.writestr(filename, content)
        
        buffer.seek(0)
        return buffer
