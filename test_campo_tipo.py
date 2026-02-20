"""
Test per verificare che il campo venga creato correttamente come ModelChoiceField
"""

from comunicazioni.models_template import TemplateComunicazione, TemplateContextField
from comunicazioni.forms import ComunicazioneForm
from comunicazioni.models import Comunicazione
from anagrafiche.models import Anagrafica
from django import forms

print("="*60)
print("TEST TIPO CAMPO NEL FORM")
print("="*60)

# Crea template
template = TemplateComunicazione.objects.create(
    nome="Test Campo Tipo",
    oggetto="Test",
    corpo_testo="Test",
)

campo = TemplateContextField.objects.create(
    template=template,
    key="cliente",
    label="Cliente",
    field_type=TemplateContextField.FieldType.INTEGER,
    widget="anagrafica",
    required=False,
)

print(f"\n✓ Template e campo creati")
print(f"  - Campo key: {campo.key}")
print(f"  - Campo widget: {campo.widget}")
print(f"  - Campo field_type: {campo.field_type}")

# Crea comunicazione con template
comm = Comunicazione(template=template, tipo=Comunicazione.TipoComunicazione.INFORMATIVA)

# Crea form
form = ComunicazioneForm(instance=comm)

campo_nome = f"ctx__{campo.key}"
print(f"\n✓ Form creato")
print(f"  - Campo nel form: {campo_nome in form.fields}")

if campo_nome in form.fields:
    field = form.fields[campo_nome]
    print(f"  - Tipo campo: {type(field).__name__}")
    print(f"  - È ModelChoiceField: {isinstance(field, forms.ModelChoiceField)}")
    print(f"  - Widget type: {type(field.widget).__name__}")
    print(f"  - Widget attrs: {field.widget.attrs}")
    
    if isinstance(field, forms.ModelChoiceField):
        print(f"  - Queryset count: {field.queryset.count()}")
        print("  ✅ CAMPO CREATO CORRETTAMENTE COME ModelChoiceField")
    else:
        print("  ❌ PROBLEMA: Campo non è ModelChoiceField!")
        
    # Prova a renderizzarlo
    print(f"\n✓ Rendering del campo:")
    rendered = str(field.widget.render(campo_nome, None, attrs=field.widget.attrs))
    print(f"  - HTML length: {len(rendered)}")
    print(f"  - HTML snippet (primi 200 char):")
    print(f"    {rendered[:200]}")
    
    # Conta le option
    option_count = rendered.count('<option')
    print(f"  - Numero di <option> nel HTML: {option_count}")
else:
    print(f"  ❌ Campo non trovato nel form!")

# Pulizia
campo.delete()
template.delete()
print("\n" + "="*60)
print("TEST COMPLETATO")
print("="*60)
