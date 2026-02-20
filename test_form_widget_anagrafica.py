"""
Test per verificare che il form con widget anagrafica funzioni correttamente.

Uso:
    python manage.py shell < test_form_widget_anagrafica.py
"""

from comunicazioni.models_template import TemplateComunicazione, TemplateContextField
from comunicazioni.models import Comunicazione
from comunicazioni.forms import ComunicazioneForm
from anagrafiche.models import Anagrafica
from django import forms

print("="*60)
print("TEST FORM CON WIDGET ANAGRAFICA")
print("="*60)

# Crea un template di test
template = TemplateComunicazione.objects.create(
    nome="Test Form Widget",
    oggetto="Test per {{ cliente.denominazione_anagrafica }}",
    corpo_testo="Corpo test",
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

# Test 1: Creazione del form
print("\n" + "-"*60)
print("TEST 1: Creazione form con template")
print("-"*60)

comunicazione = Comunicazione(
    tipo=Comunicazione.TipoComunicazione.INFORMATIVA,
    direzione=Comunicazione.Direzione.OUT,
    template=template
)

form = ComunicazioneForm(instance=comunicazione)
campo_nome = f"ctx__{campo.key}"  # Usa doppio underscore

print(f"\n✓ Form creato")
print(f"  - Campo '{campo_nome}' presente: {campo_nome in form.fields}")

if campo_nome in form.fields:
    field = form.fields[campo_nome]
    print(f"  - Tipo campo: {type(field).__name__}")
    print(f"  - È ModelChoiceField: {isinstance(field, forms.ModelChoiceField)}")
    print(f"  - Label: {field.label}")
    print(f"  - Required: {field.required}")
    
    if isinstance(field, forms.ModelChoiceField):
        print(f"  - Queryset count: {field.queryset.count()}")
        print(f"  - Ha label_from_instance: {hasattr(field, 'label_from_instance')}")
        
        # Testa il formato della label
        if field.queryset.exists():
            prima_anag = field.queryset.first()
            if hasattr(field, 'label_from_instance'):
                label_text = field.label_from_instance(prima_anag)
                print(f"  - Esempio label: {label_text}")
        
        print("\n✅ TEST 1 SUPERATO: Campo anagrafica creato correttamente!")
    else:
        print("\n❌ TEST 1 FALLITO: Campo non è ModelChoiceField!")
else:
    print(f"\n❌ TEST 1 FALLITO: Campo '{campo_nome}' non trovato nel form!")

# Test 2: Salvataggio e modifica
print("\n" + "-"*60)
print("TEST 2: Salvataggio e ricaricamento")
print("-"*60)

# Simula POST data - usa il nome campo corretto!
post_data = {
    "tipo": Comunicazione.TipoComunicazione.INFORMATIVA,
    "direzione": Comunicazione.Direzione.OUT,
    "template": str(template.id),  # Includi il template!
    "oggetto": "Test oggetto",
    "corpo": "Test corpo",
    "destinatari": "test@example.com",
    "mittente": "mittente@example.com",
    campo_nome: str(anagrafica.id),  # Usa campo_nome con doppio underscore
}

comunicazione_nuova = Comunicazione(template=template)
form = ComunicazioneForm(post_data, instance=comunicazione_nuova)

print(f"\n✓ Form creato con POST data")
print(f"  - POST data keys: {list(post_data.keys())}")

if form.is_valid():
    print(f"\n✓ Form valido")
    print(f"  - cleaned_data keys: {list(form.cleaned_data.keys())}")
    print(f"  - _template_context_data: {form.cleaned_data.get('_template_context_data', 'NON PRESENTE')}")
    print(f"  - dati_template in cleaned_data: {form.cleaned_data.get('dati_template', 'NON PRESENTE')}")
    
    # Debug: verifica prima del save
    print(f"\n  [DEBUG] Prima del save:")
    print(f"    - context_data dal cleaned_data: {form.cleaned_data.get('_template_context_data', {})}")
    print(f"    - form instance.dati_template: {form.instance.dati_template}")
    
    # Proviamo a impostarlo manualmente prima del save
    form.instance.dati_template = form.cleaned_data.get('_template_context_data', {})
    print(f"    - dopo assegnazione manuale: {form.instance.dati_template}")
    
    saved_comm = form.save()
    
    # Debug: verifica dopo il save
    print(f"\n  [DEBUG] Dopo il save:")
    print(f"    - saved_comm.dati_template: {saved_comm.dati_template}")
    
    # Ricarica dal DB per essere sicuri
    saved_comm.refresh_from_db()
    print(f"  [DEBUG] Dopo refresh_from_db:")
    print(f"    - saved_comm.dati_template: {saved_comm.dati_template}")
    print(f"\n✓ Comunicazione salvata: {saved_comm}")
    print(f"  - dati_template: {saved_comm.dati_template}")
    print(f"  - cliente ID salvato: {saved_comm.dati_template.get('cliente')}")
    
    # Test ricaricamento
    print("\n✓ Ricaricamento form per modifica...")
    # Ricarica saved_comm per avere tutti i dati aggiornati
    saved_comm = Comunicazione.objects.get(pk=saved_comm.pk)
    edit_form = ComunicazioneForm(instance=saved_comm)
    
    print(f"  - Template della comunicazione: {saved_comm.template}")
    print(f"  - Campi nel form: {len(edit_form.fields)}")
    
    if campo_nome in edit_form.fields:
        initial_value = edit_form.fields[campo_nome].initial
        print(f"  - Valore iniziale: {initial_value}")
        print(f"  - Tipo valore: {type(initial_value).__name__}")
        
        if isinstance(initial_value, Anagrafica):
            print(f"  - Anagrafica caricata: {initial_value}")
            print("\n✅ TEST 2 SUPERATO: Salvataggio e ricaricamento funzionano!")
        else:
            print(f"\n⚠ TEST 2 PARZIALE: Valore non è un'istanza di Anagrafica")
    else:
        print(f"\n❌ TEST 2 FALLITO: Campo '{campo_nome}' non trovato nel form di modifica")
        print(f"    Campi disponibili: {list(edit_form.fields.keys())}")
    
    # Pulizia
    saved_comm.delete()
else:
    print(f"\n❌ TEST 2 FALLITO: Form non valido")
    print(f"  - Errori: {form.errors}")

# Pulizia finale
campo.delete()
template.delete()
print("\n" + "="*60)
print("TEST COMPLETATO - Template e campo eliminati")
print("="*60)
