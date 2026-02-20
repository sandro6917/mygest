# ✅ CHECKLIST DEPLOYMENT - Sistema Help Builder

## Pre-Deployment (Sviluppo)

### Verifica Codice
- [x] Tutti i file creati sono sintatticamente corretti
- [x] Import corretti in tutti i file
- [x] Signals configurati in `apps.py`
- [x] Form registrato in Admin
- [x] Command wizard funzionante
- [x] CSS/JS file presenti

### Test Locali
- [x] `python manage.py check` → No errori
- [x] `python manage.py configure_help_wizard --help` → Output corretto
- [x] `python manage.py configure_help_wizard --tipo CED --rebuild-technical` → Successo
- [ ] Test manuale form Admin (richiede DB configurato)
- [ ] Test creazione nuovo tipo documento
- [ ] Test modifica attributo esistente

---

## Deployment Staging

### 1. Backup
```bash
# Backup database
python manage.py dumpdata documenti.DocumentiTipo > backup_tipi_pre_help_builder.json

# Backup file statici
tar -czf backup_static_$(date +%Y%m%d).tar.gz static/
```

### 2. Deploy Codice
```bash
# Pull dal repository
cd /srv/mygest/app
git pull origin main

# Attiva virtualenv
source venv/bin/activate

# Installa dipendenze (se necessario)
pip install -r requirements.txt
```

### 3. Collect Static
```bash
# Copia file CSS/JS in STATIC_ROOT
python manage.py collectstatic --noinput

# Verifica file copiati
ls -la /srv/mygest/app/staticfiles/admin/css/help_admin.css
ls -la /srv/mygest/app/staticfiles/admin/js/help_admin.js
ls -la /srv/mygest/app/staticfiles/schemas/help_data_schema.json
```

### 4. Test Funzionalità
```bash
# Test wizard
python manage.py configure_help_wizard --tipo CED --rebuild-technical

# Verifica help_data generato
python manage.py shell << EOF
from documenti.models import DocumentiTipo
tipo = DocumentiTipo.objects.get(codice='CED')
print("Sezioni:", list(tipo.help_data.keys()))
EOF
```

### 5. Test Admin UI
```
1. Accedi a /admin/documenti/documentitipo/
2. Clicca su tipo esistente (es. CED)
3. Verifica presenza sezioni Help collassabili
4. Verifica CSS caricato (colori sezioni)
5. Verifica JS caricato (badge AUTO/MANUALE)
6. Prova validazione FAQ JSON
7. Salva → Verifica messaggio "Sezioni tecniche rigenerate"
```

### 6. Test Signal Auto-Aggiornamento
```python
# Da Django shell
from documenti.models import DocumentiTipo, AttributoDefinizione

tipo = DocumentiTipo.objects.get(codice='CED')

# Test: Aggiungi attributo
attr = AttributoDefinizione.objects.create(
    tipo_documento=tipo,
    codice='test_attr',
    nome='Test Attributo',
    tipo_dato='str',
    required=False
)

# Verifica: help_data aggiornato automaticamente
tipo.refresh_from_db()
attr_din = tipo.help_data.get('attributi_dinamici', {})
attr_codes = [a['codice'] for a in attr_din.get('disponibili', [])]
print('test_attr' in attr_codes)  # Deve essere True

# Cleanup
attr.delete()
```

### 7. Test Wizard Completo
```bash
# Test interattivo (se hai accesso terminale)
python manage.py configure_help_wizard

# Oppure test automatico rebuild
for tipo in CED FAT CNT; do
    python manage.py configure_help_wizard --tipo $tipo --rebuild-technical
done
```

---

## Deployment Produzione

### 1. Pre-Requisiti
- [ ] Tutti i test staging passati
- [ ] Backup database eseguito
- [ ] Backup static files eseguito
- [ ] Team informato del deployment

### 2. Migrazione Dati Esistenti
```python
# Script migrazione tipi esistenti
python manage.py shell << 'EOF'
from documenti.models import DocumentiTipo
from documenti.help_builder import rebuild_help_technical_sections

tipi_migrati = 0
tipi_errori = 0

for tipo in DocumentiTipo.objects.all():
    try:
        if tipo.help_data:
            # Preserva sezioni discorsive, rigenera tecniche
            tipo.help_data = rebuild_help_technical_sections(tipo)
            tipo.save()
            print(f"✓ {tipo.codice} migrato")
            tipi_migrati += 1
        else:
            # Inizializza help_data vuoto
            from documenti.help_builder import HelpDataBuilder
            builder = HelpDataBuilder(tipo)
            tipo.help_data = builder.build_all_technical_sections()
            tipo.save()
            print(f"✓ {tipo.codice} inizializzato")
            tipi_migrati += 1
    except Exception as e:
        print(f"✗ {tipo.codice} errore: {e}")
        tipi_errori += 1

print(f"\nRiepilogo: {tipi_migrati} migrati, {tipi_errori} errori")
EOF
```

### 3. Deploy Steps
```bash
# 1. Manutenzione mode (opzionale)
# touch /srv/mygest/app/maintenance.flag

# 2. Pull codice
cd /srv/mygest/app
git pull origin main

# 3. Collect static
source venv/bin/activate
python manage.py collectstatic --noinput

# 4. Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# 5. Check logs
sudo journalctl -u gunicorn -f
```

### 4. Verifica Post-Deploy
```bash
# Check servizi
sudo systemctl status gunicorn
sudo systemctl status nginx

# Test endpoint
curl -I https://tuodominio.com/admin/

# Test static files
curl -I https://tuodominio.com/static/admin/css/help_admin.css
```

### 5. Smoke Test
- [ ] Login admin funziona
- [ ] `/admin/documenti/documentitipo/` carica
- [ ] Form modifica tipo documento mostra sezioni Help
- [ ] CSS caricato (colori sezioni visibili)
- [ ] JS caricato (badge visibili)
- [ ] Salvataggio tipo documento funziona
- [ ] Frontend `/help/documenti/CED` mostra sezioni aggiornate
- [ ] Export PDF help funziona

### 6. Monitoraggio Post-Deploy (24h)
- [ ] Controlla log Django per errori signal
- [ ] Verifica performance Admin (tempo caricamento form)
- [ ] Monitora query database (select_related/prefetch_related)
- [ ] Feedback utenti su usabilità form

---

## Rollback Plan (Se Necessario)

### Quick Rollback
```bash
# 1. Revert commit
cd /srv/mygest/app
git revert HEAD
# oppure
git reset --hard <COMMIT_PRECEDENTE>

# 2. Collect static
python manage.py collectstatic --noinput

# 3. Restart
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### Database Rollback
```bash
# Restore backup
python manage.py loaddata backup_tipi_pre_help_builder.json
```

### File Rollback
```bash
# Restore static files
tar -xzf backup_static_YYYYMMDD.tar.gz -C /
```

---

## Post-Deployment

### Documentazione Utenti
- [ ] Invia guida rapida: `QUICK_REFERENCE_HELP_BUILDER.md`
- [ ] Organizza training session (se team grande)
- [ ] Crea video tutorial (opzionale)
- [ ] Aggiorna wiki/knowledge base

### Monitoring
- [ ] Aggiungi alert su errori signal (logging)
- [ ] Monitora performance form Admin
- [ ] Traccia usage wizard CLI (log analytics)
- [ ] Feedback loop con utenti

### Miglioramenti Futuri
- [ ] Formset inline per FAQ (invece di JSON)
- [ ] Preview help in modal Admin
- [ ] Template predefiniti per categorie
- [ ] Import/Export configurazioni help
- [ ] AI assistant per FAQ suggerite

---

## Troubleshooting Comune

### Problema: CSS non caricato
```bash
# Verifica collectstatic
python manage.py collectstatic --noinput -v 2

# Check permessi
ls -la /srv/mygest/app/staticfiles/admin/css/

# Nginx config
# Verifica che static_root sia corretto in nginx.conf
```

### Problema: Signal non attivati
```python
# Verifica apps.py
cat documenti/apps.py | grep "import documenti.signals"

# Se manca, aggiungi in ready():
def ready(self):
    import documenti.signals
```

### Problema: Wizard non trovato
```bash
# Verifica file esiste
ls -la documenti/management/commands/configure_help_wizard.py

# Check sintassi
python manage.py check

# Riavvia shell se necessario
```

### Problema: Form errori validazione
```python
# Check in Django shell
from documenti.help_forms import HelpDataAdminForm
from documenti.models import DocumentiTipo

tipo = DocumentiTipo.objects.first()
form = HelpDataAdminForm(instance=tipo)
print(form.errors)
```

---

## Checklist Finale

### Pre-Deploy
- [x] Codice committato
- [x] Documentazione completa
- [ ] Test staging passati
- [ ] Backup eseguiti
- [ ] Team informato

### Deploy
- [ ] Codice deployed
- [ ] Static collected
- [ ] Services restarted
- [ ] Logs checked

### Post-Deploy
- [ ] Smoke test passato
- [ ] Utenti notificati
- [ ] Documentazione distribuita
- [ ] Monitoring attivo

### Sign-Off
- [ ] Product Owner approva
- [ ] Tech Lead approva
- [ ] Deployment completato con successo

---

**Note**: Adatta questa checklist al tuo specifico ambiente di deployment.

**Data Creazione**: 11 Febbraio 2026  
**Versione**: 1.0  
**Owner**: Sandro Chimenti
