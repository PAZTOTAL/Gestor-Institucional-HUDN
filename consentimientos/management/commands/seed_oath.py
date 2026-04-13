from django.core.management.base import BaseCommand
from consentimientos.models import DocumentoConsentimiento

class Command(BaseCommand):
    help = 'Crea el documento de juramento de antecedentes personales'

    def handle(self, *args, **options):
        titulo = "Declaración Jurada de Antecedentes"
        contenido = "Bajo gravedad de juramento certifico que no tengo Antecedente Personales"
        
        doc, created = DocumentoConsentimiento.objects.get_or_create(
            titulo=titulo,
            defaults={'contenido': contenido}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Documento creado con ID: {doc.id}'))
        else:
            doc.contenido = contenido
            doc.save()
            self.stdout.write(self.style.SUCCESS(f'Documento actualizado con ID: {doc.id}'))
