# 🚀 Quick Start - UI Comunicazioni

## Setup Rapido in 5 Passi

### 1. Verifica Backend Django
```bash
cd /home/sandro/mygest
python manage.py runserver
```

Verifica che le API rispondano:
```bash
curl http://localhost:8000/api/v1/comunicazioni/comunicazioni/
```

### 2. Installa Dipendenze Frontend (se necessario)
```bash
cd frontend
npm install
```

### 3. Avvia il Frontend
```bash
npm run dev
```

### 4. Accedi all'App
- Apri browser: http://localhost:5173
- Fai login con le tue credenziali
- Clicca su **"Comunicazioni"** nel menu

### 5. Testa le Funzionalità
✅ Visualizza lista comunicazioni  
✅ Applica filtri (tipo, direzione, stato)  
✅ Crea nuova comunicazione  
✅ Aggiungi destinatari  
✅ Salva e invia  
✅ Visualizza dettaglio  

## 📁 File Creati

```
frontend/src/
├── api/comunicazioni.ts                    # ✅ API client
├── types/comunicazioni.ts                  # ✅ TypeScript types
├── pages/
│   ├── ComunicazioniListPage.tsx          # ✅ Lista
│   ├── ComunicazioneFormPage.tsx          # ✅ Form
│   └── ComunicazioneDetailPage.tsx        # ✅ Dettaglio
├── styles/comunicazioni.css               # ✅ Stili
└── routes/index.tsx                       # ✅ Route

comunicazioni/
├── UI_REACT_README.md                     # 📖 Documentazione completa
└── UI_IMPLEMENTATION_SUMMARY.md           # 📊 Riepilogo
```

## 🎯 URL Principali

| Pagina | URL | Descrizione |
|--------|-----|-------------|
| Lista | `/comunicazioni` | Visualizza tutte le comunicazioni |
| Nuova | `/comunicazioni/create` | Crea nuova comunicazione |
| Dettaglio | `/comunicazioni/:id` | Dettagli comunicazione |
| Modifica | `/comunicazioni/:id/edit` | Modifica comunicazione |

## 🔑 Funzionalità Chiave

### Lista Comunicazioni
- ✅ Tabella paginata
- ✅ Filtri: tipo, direzione, stato, ricerca
- ✅ Badge colorati per stato
- ✅ Azioni rapide

### Form Comunicazione
- ✅ Campi validati
- ✅ Destinatari manuali
- ✅ Autocomplete contatti
- ✅ Autocomplete liste
- ✅ Protezione protocollati

### Dettaglio Comunicazione
- ✅ Info complete
- ✅ Lista destinatari
- ✅ Contenuto messaggio
- ✅ Azioni (modifica, invia, elimina)
- ✅ Visualizzazione errori

## 🛠️ Troubleshooting Rapido

### Backend non risponde
```bash
# Verifica che Django sia in esecuzione
ps aux | grep manage.py
# Se non attivo, avvia:
python manage.py runserver
```

### Frontend non si avvia
```bash
cd frontend
# Reinstalla dipendenze
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Errori TypeScript
```bash
cd frontend
# Controlla errori
npm run build
```

### Errori CORS
Aggiungi in `mygest/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
```

## 📚 Documentazione Completa

Per maggiori dettagli, consulta:
- **UI_REACT_README.md** - Guida completa
- **UI_IMPLEMENTATION_SUMMARY.md** - Riepilogo tecnico

## ✨ Prossimi Passi

1. ✅ Testa tutte le funzionalità
2. ⚙️ Configura variabili ambiente
3. 🎨 Personalizza stili se necessario
4. 📧 Configura invio email (backend)
5. 🚀 Deploy in produzione

## 💡 Suggerimenti

### Performance
- React Query gestisce la cache automaticamente
- Le liste sono paginate per performance
- I filtri sono debounced per ridurre chiamate API

### Sicurezza
- Tutte le route sono protette (JWT)
- I token vengono refresh automaticamente
- Le azioni distruttive richiedono conferma

### UX
- Loading states ovunque
- Error handling completo
- Feedback visivo per ogni azione
- Design responsive mobile-first

## 🎉 Pronto!

L'UI React per il modulo Comunicazioni è **pronta all'uso**!

Buon lavoro! 🚀
