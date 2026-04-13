from django.core.management.base import BaseCommand
from consentimientos.models import DocumentoConsentimiento

class Command(BaseCommand):
    help = 'Crea un documento de consentimiento inicial'

    def handle(self, *args, **options):
        doc, created = DocumentoConsentimiento.objects.get_or_create(
            titulo="Consentimiento de Tratamiento de Datos Personales",
            defaults={
                "contenido": """
                    <h2>Aviso de Privacidad</h2>
                    <p>En cumplimiento de la Ley 1581 de 2012, autorizo a <b>AlexaTotal</b> para el tratamiento de mis datos personales 
                    registrados en este documento para fines administrativos, comerciales y de seguridad.</p>
                    <p>Entiendo que puedo ejercer mis derechos de conocer, actualizar, rectificar y suprimir la información en cualquier momento.</p>
                    <br>
                    <p>Al firmar con mi biometría, acepto los términos y condiciones aquí descritos.</p>
                """,
                "version": "1.0"
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Documento creado: {doc.titulo}'))
        else:
            self.stdout.write(self.style.WARNING('El documento ya existe.'))
