#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/sandro/mygest"
VENV_DIR="$PROJECT_DIR/venv"
BACKUP_ROOT="/home/sandro/backups/mygest"

# Fallback interpreti
PY="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"
if [[ ! -x "$PY" ]]; then PY="$(command -v python3)"; fi
if [[ ! -x "$PIP" ]]; then PIP="$(command -v pip3 || true)"; fi

TS="$(date +%F_%H%M%S)"
WORK_DIR="$BACKUP_ROOT/$TS"
ARCHIVE="$BACKUP_ROOT/mygest_backup_$TS.tar.gz"

mkdir -p "$WORK_DIR"

echo "[*] Esporto dipendenze..."
if [[ -n "$PIP" ]]; then
  "$PIP" freeze > "$WORK_DIR/requirements.txt" || true
fi

echo "[*] Leggo configurazione DB da Django..."
read -r DB_ENGINE DB_NAME DB_USER DB_PASS DB_HOST DB_PORT < <(
  cd "$PROJECT_DIR"
  "$PY" - <<'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
try:
    import django
    django.setup()
    from django.conf import settings
    db = settings.DATABASES["default"]
    print(db.get("ENGINE",""), db.get("NAME",""), db.get("USER",""), db.get("PASSWORD",""), db.get("HOST",""), str(db.get("PORT","")))
except Exception:
    print("", "", "", "", "", "")
PY
)

echo "[*] Dump dati applicativi (dumpdata JSON)..."
cd "$PROJECT_DIR"
"$PY" manage.py dumpdata \
  --natural-foreign --natural-primary \
  --exclude contenttypes --exclude auth.permission \
  --indent 2 > "$WORK_DIR/data_dump.json" || true

echo "[*] Backup database specifico..."
shopt -s nocasematch
if [[ "$DB_ENGINE" == *"sqlite3"* && -n "${DB_NAME:-}" && -f "$DB_NAME" ]]; then
  cp -a "$DB_NAME" "$WORK_DIR/sqlite_db_backup.sqlite3"
elif [[ "$DB_ENGINE" == *"postgresql"* ]]; then
  if command -v pg_dump >/dev/null 2>&1; then
    export PGPASSWORD="${DB_PASS:-}"
    pg_dump -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" \
      -U "${DB_USER:-postgres}" -F p -d "${DB_NAME:-postgres}" \
      > "$WORK_DIR/postgres_dump.sql" || true
    unset PGPASSWORD
  else
    echo "[!] pg_dump non trovato, salto dump PostgreSQL."
  fi
elif [[ "$DB_ENGINE" == *"mysql"* || "$DB_ENGINE" == *"mariadb"* ]]; then
  if command -v mysqldump >/dev/null 2>&1; then
    export MYSQL_PWD="${DB_PASS:-}"
    mysqldump -h "${DB_HOST:-localhost}" -P "${DB_PORT:-3306}" \
      -u "${DB_USER:-root}" "${DB_NAME:-}" > "$WORK_DIR/mysql_dump.sql" || true
    unset MYSQL_PWD
  else
    echo "[!] mysqldump non trovato, salto dump MySQL."
  fi
else
  echo "[!] Motore DB non riconosciuto o non configurato, uso solo dumpdata."
fi
shopt -u nocasematch

echo "[*] Copio media e .env..."
[[ -d "$PROJECT_DIR/media" ]] && rsync -a --delete "$PROJECT_DIR/media/" "$WORK_DIR/media/"
[[ -f "$PROJECT_DIR/.env" ]] && cp -a "$PROJECT_DIR/.env" "$WORK_DIR/.env"

echo "[*] Creo archivio tar.gz (codice + artefatti backup)..."
EXCLUDES=(
  --exclude=".git"
  --exclude="__pycache__"
  --exclude="*.pyc"
  --exclude="node_modules"
  --exclude="venv"
  --exclude=".mypy_cache"
  --exclude=".pytest_cache"
  --exclude="staticfiles"
  --exclude="media"
)
tar -czf "$ARCHIVE" \
  "${EXCLUDES[@]}" \
  -C "$PROJECT_DIR" . \
  -C "$WORK_DIR" .

echo "[*] Calcolo checksum..."
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"

echo "[*] Pulizia temporanei..."
rm -rf "$WORK_DIR"

echo "[✓] Backup completato: $ARCHIVE"