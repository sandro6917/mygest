"""
Script di test per verificare il funzionamento del widget anagrafica nei template.

Uso:
    python manage.py shell < test_widget_anagrafica.py
"""

from comunicazioni.models_template import TemplateComunicazione, TemplateContextField
from comunicazioni.models import Comunicazione
from anagrafiche.models import Anagrafica

# Crea un template di test
template = TemplateComunicazione.objects.create(
    nome="Test Widget Anagrafica",
    oggetto="Comunicazione per {{ cliente.denominazione_anagrafica }}",
    corpo_testo="""
Gentile Responsabile,

con la presente comunichiamo che la documentazione relativa al cliente
{{ cliente.denominazione_anagrafica }} (CF: {{ cliente.codice_fiscale }})
è stata preparata e sarà disponibile a breve.

Cordiali saluti.
""",
    attivo=True
)

# Aggiungi il campo con widget anagrafica
campo = TemplateContextField.objects.create(
    template=template,
    key="cliente",
    label="Cliente di riferimento",
    field_type=TemplateContextField.FieldType.INTEGER,
    widget="anagrafica",
    required=True,
    help_text="Seleziona il cliente a cui si riferisce la comunicazione",
    ordering=1,
    active=True
)

print(f"✓ Template creato: {template}")
print(f"✓ Campo creato: {campo}")
print(f"  - key: {campo.key}")
print(f"  - field_type: {campo.field_type}")
print(f"  - widget: {campo.widget}")

# Verifica che esista almeno un'anagrafica
anagrafica = Anagrafica.objects.first()
if not anagrafica:
    print("\n⚠ Nessuna anagrafica trovata nel database. Creane una per testare.")
else:
    print(f"\n✓ Anagrafica di test trovata: {anagrafica}")
    
    # Crea una comunicazione usando il template
    comunicazione = Comunicazione.objects.create(
        tipo=Comunicazione.TipoComunicazione.INFORMATIVA,
        direzione=Comunicazione.Direzione.OUT,
        oggetto="Test comunicazione",
        corpo="Test",
        destinatari="test@example.com",
        mittente="mittente@example.com",
        template=template,
        dati_template={"cliente": anagrafica.id}  # Salva l'ID
    )
    
    print(f"\n✓ Comunicazione creata: {comunicazione}")
    print(f"  - dati_template: {comunicazione.dati_template}")
    
    # Testa il contesto
    context = comunicazione.get_template_context()
    print(f"\n✓ Contesto generato:")
    print(f"  - cliente: {context.get('cliente')}")
    print(f"  - tipo cliente: {type(context.get('cliente'))}")
    
    if 'cliente' in context and hasattr(context['cliente'], 'denominazione_anagrafica'):
        print(f"  - cliente.denominazione_anagrafica: {context['cliente'].denominazione_anagrafica}")
        print("\n✅ TEST SUPERATO! Il widget anagrafica funziona correttamente.")
    else:
        print("\n❌ TEST FALLITO! Il cliente non è stato risolto correttamente.")
    
    # Pulizia
    comunicazione.delete()
    print(f"\n✓ Comunicazione di test eliminata")

# Pulizia template
campo.delete()
template.delete()
print(f"✓ Template e campo eliminati")

print("\n" + "="*60)
print("Test completato!")
print("="*60)
