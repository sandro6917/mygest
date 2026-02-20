#!/bin/bash
# Script di supporto per creare marker file dopo l'upload

# Questo script può essere chiamato dopo l'upload per creare
# un file marker che indica il successo dell'operazione

FILE_PATH="$1"

if [ -z "$FILE_PATH" ]; then
    echo "Uso: $0 /percorso/al/file.pdf"
    exit 1
fi

if [ ! -f "$FILE_PATH" ]; then
    echo "Errore: File non trovato: $FILE_PATH"
    exit 1
fi

# Crea marker nella stessa directory
MARKER_FILE="${FILE_PATH}.uploaded"
touch "$MARKER_FILE"

echo "Marker creato: $MARKER_FILE"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')" > "$MARKER_FILE"
echo "File: $FILE_PATH" >> "$MARKER_FILE"

exit 0
