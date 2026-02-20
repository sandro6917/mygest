"""
Verifica la configurazione del campo cliente nel template
"""

from comunicazioni.models_template import TemplateComunicazione, TemplateContextField

# Cerca il template "Invio presenze edac"
templates = TemplateComunicazione.objects.filter(nome__icontains="presenze")

print("="*60)
print("VERIFICA CONFIGURAZIONE TEMPLATE")
print("="*60)

if not templates.exists():
    print("\n❌ Nessun template trovato con 'presenze' nel nome")
    print(f"\nTemplate disponibili:")
    for t in TemplateComunicazione.objects.all()[:10]:
        print(f"  - {t.nome}")
else:
    for template in templates:
        print(f"\n✓ Template: {template.nome}")
        print(f"  ID: {template.id}")
        
        # Cerca il campo cliente
        campi = template.context_fields.all()
        print(f"\n  Campi del template ({campi.count()}):")
        
        for campo in campi:
            print(f"\n  - Campo: {campo.key}")
            print(f"    Label: {campo.label}")
            print(f"    Tipo: {campo.field_type}")
            print(f"    Widget: '{campo.widget}'")
            print(f"    Required: {campo.required}")
            print(f"    Active: {campo.active}")
            
            if campo.key == "cliente":
                print(f"\n    ⚠️  CAMPO CLIENTE TROVATO!")
                if campo.widget in ("anagrafica", "fk_anagrafica", "anag"):
                    if campo.field_type == TemplateContextField.FieldType.INTEGER:
                        print(f"    ✅ Configurazione corretta (integer + widget anagrafica)")
                    else:
                        print(f"    ❌ PROBLEMA: field_type dovrebbe essere INTEGER, è '{campo.field_type}'")
                else:
                    print(f"    ❌ PROBLEMA: widget dovrebbe essere 'anagrafica', è '{campo.widget}'")

print("\n" + "="*60)
