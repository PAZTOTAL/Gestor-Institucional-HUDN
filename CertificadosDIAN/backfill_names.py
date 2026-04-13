from CertificadosDIAN.models import SolicitudCertificadoWhatsapp, DatosCertificadoDIAN
requests = SolicitudCertificadoWhatsapp.objects.filter(nombre_empleado__isnull=True) | SolicitudCertificadoWhatsapp.objects.filter(nombre_empleado='')
print(f"Buscando {requests.count()} solicitudes sin nombre...")
for s in requests:
    d = DatosCertificadoDIAN.objects.filter(cedula=s.cedula_consultada).first()
    if d:
        s.nombre_empleado = f"{d.primer_nombre} {d.primer_apellido}"
        s.save()
        print(f"Actualizada cédula {s.cedula_consultada}: {s.nombre_empleado}")
    else:
        s.nombre_empleado = "Funcionario HUDN"
        s.save()
        print(f"Cédula {s.cedula_consultada} no encontrada en base de datos DIAN.")
