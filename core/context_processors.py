def modules_processor(request):
    asistenciales = [
        {'name': 'Registro de Anestesia', 'slug': 'registro_anestesia', 'description': 'Registro Clínico de Anestesia (FRQUI-032)', 'url': '/registro-anestesia/create/', 'icon': 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2 14 8 20 8 M16 13H8 M16 17H8 M10 9H9H8'},
        {'name': 'Sistema MEOWS', 'slug': 'meows', 'description': 'Sistema de Alerta Temprana Obstétrico', 'url': '/meows/nuevo/0/', 'icon': 'M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z'},
        {'name': 'Gestión de Partos', 'slug': 'parto', 'description': 'Historia Clínico y Partograma', 'url': '/parto/', 'icon': 'M9 12h.01 M15 12h.01 M10 16a2.5 2.5 0 0 0 4 0 M12 22a7 7 0 1 0 0-14 7 7 0 0 0 0 14z M12 8V2 M5.88 10.9a3.5 3.5 0 1 1 5.24 4.77 M18.12 10.9a3.5 3.5 0 1 0-5.24 4.77'},
        {'name': 'Consentimientos Informados', 'slug': 'ConsentimientosInformados', 'description': 'Autorizaciones y Firmas Electrónicas', 'url': '/consentimientos/', 'icon': 'M12 20h9 M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z'},
        {'name': 'Central de Mezclas', 'slug': 'CentralDeMezclas', 'description': 'Laboratorio de Preparaciones Estériles', 'url': '/central-mezclas/', 'icon': 'M16.3 3.4 12 10V2M11 10.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z M5.5 15.5l1.5-2 M17 15.5l-1.5-2 M2 22h20 M7 22l1-4.5 M17 22l-1-4.5'},
        {'name': 'Trasplantes y Donaciones', 'slug': 'trasplantes_donacion', 'description': 'Seguimiento de Pacientes Neurocríticos y Donación', 'url': '/trasplantes-donacion/', 'icon': 'M22 12h-4l-3 9L9 3l-3 9H2'},
    ]
    
    administrativos = [
        {'name': 'Generales y Seguridad', 'slug': 'usuarios', 'description': 'Configuración general y seguridad'},
        {'name': 'Consultas Base Externa', 'slug': 'consultas_externas', 'description': 'Consulta de datos GENTERCER y otros', 'url': '/consultas-externas/'},
        {'name': 'Talento Humano', 'slug': 'horas_extras', 'description': 'Nómina: Horas Extras y Recargos', 'url': '/horas-extras/', 'icon': 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z'},
        {'name': 'Presupuesto', 'slug': 'presupuesto', 'description': 'Gestión de CDPs y RPs', 'url': '/presupuesto/cdp/'},
    ]
    
    varios = [
        {'name': 'Bases Generales', 'slug': 'BasesGenerales', 'description': 'Configuración de bases generales'},
        {'name': 'Certificado de Ingresos', 'slug': 'CertificadosDIAN', 'description': 'Generación de Certificados y Bienes 2025', 'url': '/certificados-dian/', 'icon': 'M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z M14 2 14 8 20 8 M8 13h2 M8 17h2 M14 13h2 M14 17h2'},
        {'name': 'Solicitudes WhatsApp', 'slug': 'CertificadosDIAN', 'description': 'Listado de solicitudes para envío por WA', 'url': '/certificados-dian/solicitudes/', 'icon': 'M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 1 1-7.6-11.7 8.38 8.38 0 0 1 3.8.9L21 3z'},
    ]
    
    consultas = [
        {'name': 'Administrativas', 'slug': 'consultas_admin', 'description': 'Reportes de Facturación y Aseguradoras', 'url': '/consultas/admin/'},
        {'name': 'Asistenciales', 'slug': 'consultas_salud', 'description': 'Indicadores Médicos y de Salud', 'url': '/consultas/salud/'},
    ]
    
    for mod in asistenciales + administrativos + varios + consultas:
        if 'url' not in mod:
            mod['url'] = f"/modulo/{mod['slug']}/"
        
    return {
        'nav_asistenciales': asistenciales,
        'nav_administrativos': administrativos,
        'nav_varios': varios,
        'nav_consultas': consultas,
        'readonly_db_available': getattr(request, 'readonly_db_available', True)
    }
