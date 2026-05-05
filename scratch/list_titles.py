from consentimientos.models import DocumentoConsentimiento
with open('consent_titles.txt', 'w', encoding='utf-8') as f:
    for i, d in enumerate(DocumentoConsentimiento.objects.all()):
        f.write(f"{i+1}. {d.titulo}\n")
