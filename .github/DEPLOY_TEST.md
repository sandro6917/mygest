# Deploy Test

Test deploy automatico GitHub Actions.

**Data test**: 2026-02-20 15:30
**Commit**: Test workflow con secrets configurati
**Obiettivo**: Verificare funzionamento completo deploy to VPS

## Checklist Pre-Deploy
- [x] GitHub Secrets configurati (SSH_HOST, SSH_USER, SSH_KEY, SSH_PORT)
- [x] SSH tunnel attivo (PID 1982189)
- [x] NAS mount funzionante (3.6TB disponibili)
- [x] VPS accessibile (72.62.34.249)
- [x] Script deploy.sh testato manualmente

## Expected Behavior
1. Test job: PostgreSQL + Redis + Django tests → ✅ PASS
2. Build Frontend: npm ci + build → ✅ PASS (2.15MB bundle)
3. Deploy: SSH connect + git pull + deploy.sh → ⏳ TESTING

## Troubleshooting
Se deploy fallisce, verificare:
- SSH key format (deve includere BEGIN/END headers)
- Host in known_hosts
- Permessi deploy_key (600)
- Service gunicorn_mygest status
