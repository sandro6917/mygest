#!/bin/bash
# Helper per avviare comandi Django caricando automaticamente le variabili da .env
set -euo pipefail
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$BASE_DIR/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "File .env non trovato in $BASE_DIR" >&2
  exit 1
fi

# Esporta le variabili dello .env e lancia il comando richiesto
set -a
source "$ENV_FILE"
set +a

if [[ $# -eq 0 ]]; then
  exec /bin/bash
else
  exec "$@"
fi
