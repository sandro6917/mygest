"""
Test per verificare il preview del template con widget anagrafica (come nelle views).

Uso:
    python manage.py shell < test_widget_anagrafica_preview.py
"""

from comunicazioni.models_template import TemplateComunicazione, TemplateContextField
from comunicazioni.models import Comunicazione
from comunicazioni.forms import ComunicazioneForm
from anagrafiche.models import Anagrafica
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

print("="*60)
print("TEST PREVIEW TEMPLATE CON WIDGET ANAGRAFICA")
print("="*60)

# Crea un template di test
template = TemplateComunicazione.objects.create(
    nome="Test Preview Widget",
    oggetto="Comunicazione per {{ cliente.denominazione_anagrafica }}",
    corpo_testo="""
Gentile Responsabile,

con la presente comunichiamo che la documentazione relativa al cliente
{{ cliente.denominazione_anagrafica }} (CF: {{ cliente.codice_fiscale }})
è stata preparata.

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
    help_text="Seleziona il cliente",
    ordering=1,
    active=True
)

print(f"\n✓ Template creato: {template}")
print(f"✓ Campo creato con widget='anagrafica'")

# Verifica che esista almeno un'anagrafica
anagrafica = Anagrafica.objects.first()
if not anagrafica:
    print("\n⚠ Nessuna anagrafica trovata. Test interrotto.")
    campo.delete()
    template.delete()
    exit(1)

print(f"\n✓ Anagrafica di test: {anagrafica}")

# Simula la view con _build_template_context_from_data
print("\n" + "-"*60)
print("TEST: Simulazione build context da data (come nella view)")
print("-"*60)

# Simula un utente
user = User.objects.first()
if not user:
    print("\n⚠ Nessun utente trovato")
    user = None

# Simula i dati POST della view
data = {
    "tipo": Comunicazione.TipoComunicazione.INFORMATIVA,
    "direzione": Comunicazione.Direzione.OUT,
    "template": str(template.id),
    "oggetto": "Test oggetto",
    "corpo": "Test corpo",
    "destinatari": "test@example.com",
    f"ctx__{campo.key}": str(anagrafica.id),  # Campo dinamico con ID anagrafica
}

# Simula il context building della view
context = {
    "user": user,
    "utente": user,
    "operatore": user,
    "oggi": timezone.now(),
}

# Processa i campi del template (simula _build_template_context_from_data)
context_fields = template.context_fields.filter(active=True).order_by("ordering", "id")
for ctx_field in context_fields:
    field_name = ComunicazioneForm.context_field_name(ctx_field.key)
    raw_value = data.get(field_name)
    
    print(f"\n✓ Processing campo: {ctx_field.key}")
    print(f"  - field_name: {field_name}")
    print(f"  - raw_value: {raw_value}")
    print(f"  - widget: {ctx_field.widget}")
    
    # Usa parse_raw_input che ora gestisce il widget anagrafica
    value = ctx_field.parse_raw_input(raw_value)
    
    print(f"  - parsed value: {value}")
    print(f"  - type: {type(value).__name__}")
    
    if value is not None:
        context[ctx_field.key] = value

# Verifica il contesto
print(f"\n" + "-"*60)
print("Contesto generato:")
print(f"  - 'cliente' presente: {'cliente' in context}")

if 'cliente' in context:
    cliente_val = context['cliente']
    print(f"  - tipo: {type(cliente_val).__name__}")
    print(f"  - valore: {cliente_val}")
    
    if isinstance(cliente_val, Anagrafica):
        print(f"  - cliente.denominazione_anagrafica: {cliente_val.denominazione_anagrafica}")
        print(f"  - cliente.codice_fiscale: {cliente_val.codice_fiscale}")
        print("\n✅ TEST SUPERATO: Il widget anagrafica funziona nel preview!")
    else:
        print("\n❌ TEST FALLITO: Il valore non è un'istanza di Anagrafica")
else:
    print("\n❌ TEST FALLITO: Campo 'cliente' non trovato nel contesto")

# Pulizia
campo.delete()
template.delete()
print("\n" + "="*60)
print("TEST COMPLETATO")
print("="*60)
