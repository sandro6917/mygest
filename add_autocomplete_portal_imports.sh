#!/bin/bash
# Script per aggiungere AutocompletePortal a tutti i componenti Autocomplete

COMPONENTS_DIR="/home/sandro/mygest/frontend/src/components"

# Array di componenti da aggiornare
COMPONENTS=(
    "AnagraficaAutocomplete.tsx"
    "UbicazioneAutocomplete.tsx"
    "TitolarioAutocomplete.tsx"
    "PraticaAutocomplete.tsx"
    "ComuneAutocomplete.tsx"
    "DocumentoAutocomplete.tsx"
    "TipoDocumentoAutocomplete.tsx"
)

echo "🚀 Aggiornamento componenti Autocomplete..."
echo ""

for COMPONENT in "${COMPONENTS[@]}"; do
    FILE="${COMPONENTS_DIR}/${COMPONENT}"
    
    if [ ! -f "$FILE" ]; then
        echo "⚠️  $COMPONENT non trovato"
        continue
    fi
    
    echo "📝 Elaborazione $COMPONENT..."
    
    # Verifica se il file ha già l'import
    if grep -q "AutocompletePortal" "$FILE"; then
        echo "   ✅ Import già presente"
    else
        echo "   ➕ Aggiunta import AutocompletePortal"
        # Trova l'ultima riga di import e aggiungi dopo
        sed -i "/^import .* from /a import { AutocompletePortal } from './AutocompletePortal';" "$FILE"
    fi
    
    echo ""
done

echo "✨ Script completato!"
echo ""
echo "⚠️  NOTA: Gli import sono stati aggiunti, ma devi manualmente:"
echo "   1. Sostituire i <div> dropdown con <AutocompletePortal>"
echo "   2. Testare ogni componente"
echo ""
echo "📖 Esempio di conversione:"
echo "   DA:"
echo "     {isOpen && ("
echo "       <div style={{ position: 'absolute', ... }}>...</div>"
echo "     )}"
echo ""
echo "   A:"
echo "     <AutocompletePortal isOpen={isOpen} anchorRef={wrapperRef}>"
echo "       ..."
echo "     </AutocompletePortal>"
