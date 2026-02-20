#!/usr/bin/env python3
"""
Script per aggiornare tutti i componenti Autocomplete per usare AutocompletePortal
"""
import os
import re
from pathlib import Path

FRONTEND_COMPONENTS = Path("/home/sandro/mygest/frontend/src/components")

# Lista dei componenti da aggiornare
AUTOCOMPLETE_COMPONENTS = [
    "AnagraficaAutocomplete.tsx",
    "FascicoloAutocomplete.tsx",
    "UbicazioneAutocomplete.tsx",
    "TitolarioAutocomplete.tsx",
    "PraticaAutocomplete.tsx",
    "ComuneAutocomplete.tsx",
    "DocumentoAutocomplete.tsx",
    "TipoDocumentoAutocomplete.tsx",
]

def add_import(content: str) -> str:
    """Aggiunge l'import di AutocompletePortal se non presente"""
    if "AutocompletePortal" in content:
        return content
    
    # Trova l'ultimo import
    import_pattern = r"(import .+ from .+;)\n"
    imports = list(re.finditer(import_pattern, content))
    
    if imports:
        last_import = imports[-1]
        insert_pos = last_import.end()
        new_import = "import { AutocompletePortal } from './AutocompletePortal';\n"
        content = content[:insert_pos] + new_import + content[insert_pos:]
    
    return content

def find_dropdown_divs(content: str) -> list:
    """Trova tutti i div dropdown con position: absolute e zIndex"""
    # Pattern per trovare i div dropdown
    pattern = r'{isOpen[^}]*&&[^<]*<div style=\{\{[^}]*position:\s*[\'"]absolute[\'"][^}]*zIndex:\s*\d+[^}]*\}\}'
    
    matches = []
    for match in re.finditer(pattern, content, re.DOTALL):
        matches.append({
            'start': match.start(),
            'end': match.end(),
            'text': match.group()
        })
    
    return matches

def update_component(file_path: Path) -> bool:
    """Aggiorna un singolo componente"""
    print(f"Elaborazione {file_path.name}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Aggiungi import
        content = add_import(content)
        
        # Sostituisci i div dropdown con AutocompletePortal
        # Pattern più specifico per catturare l'intero blocco
        # Cerca: {isOpen && ... ( <div style={{ position: 'absolute', ... }}>...</div> )}
        
        # Pattern 1: dropdown singolo
        pattern1 = r'{isOpen\s*&&\s*([^&]+\s*&&\s*)?([^<]*)<div style=\{\{([^}]*position:\s*[\'"]absolute[\'"][^}]*)\}\}>(.*?)</div>\s*\}'
        
        def replace_dropdown(match):
            condition = match.group(1) or ""
            extra_cond = match.group(2) or ""
            styles = match.group(3)
            children = match.group(4)
            
            # Estrai maxHeight se presente
            max_height_match = re.search(r"maxHeight:\s*['\"](\d+px)['\"]", styles)
            max_height = f' maxHeight="{max_height_match.group(1)}"' if max_height_match else ''
            
            # Costruisci la condizione completa
            full_condition = f"isOpen{' && ' + condition.strip() if condition.strip() else ''}{' && ' + extra_cond.strip() if extra_cond.strip() else ''}"
            
            # Costruisci il portal
            return f'<AutocompletePortal isOpen={{{full_condition}}} anchorRef={{wrapperRef}}{max_height}>{children}</AutocompletePortal>'
        
        # Sostituisci tutti i dropdown
        content = re.sub(pattern1, replace_dropdown, content, flags=re.DOTALL)
        
        if content != original_content:
            # Scrivi il file aggiornato
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {file_path.name} aggiornato")
            return True
        else:
            print(f"⏭️  {file_path.name} già aggiornato o nessuna modifica necessaria")
            return False
            
    except Exception as e:
        print(f"❌ Errore elaborando {file_path.name}: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Inizio aggiornamento componenti Autocomplete...\n")
    
    updated_count = 0
    
    for component_name in AUTOCOMPLETE_COMPONENTS:
        file_path = FRONTEND_COMPONENTS / component_name
        
        if not file_path.exists():
            print(f"⚠️  {component_name} non trovato")
            continue
        
        if update_component(file_path):
            updated_count += 1
    
    print(f"\n✨ Completato! {updated_count}/{len(AUTOCOMPLETE_COMPONENTS)} componenti aggiornati")

if __name__ == "__main__":
    main()
