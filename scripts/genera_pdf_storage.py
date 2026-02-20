#!/usr/bin/env python
"""
Script per generare un PDF completo della documentazione storage.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
from reportlab.lib.colors import HexColor
from datetime import datetime
from pathlib import Path

# Configurazione
OUTPUT_FILE = "Documentazione_Storage_MyGest.pdf"
BASE_DIR = Path(__file__).resolve().parent.parent

def create_styles():
    """Crea gli stili per il documento"""
    styles = getSampleStyleSheet()
    
    # Titolo principale
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    # Titolo sezione
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#34495E'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    ))
    
    # Sottotitolo
    styles.add(ParagraphStyle(
        name='SubTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#7F8C8D'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    ))
    
    # Paragrafo
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        fontName='Helvetica'
    ))
    
    # Codice
    styles.add(ParagraphStyle(
        name='CodeBlock',
        parent=styles['Code'],
        fontSize=8,
        fontName='Courier',
        leftIndent=20,
        rightIndent=20,
        spaceAfter=10,
        spaceBefore=10,
        backColor=HexColor('#F5F5F5')
    ))
    
    return styles

def add_content(story, styles):
    """Aggiunge il contenuto al documento"""
    
    # Titolo principale
    story.append(Paragraph("DOCUMENTAZIONE STORAGE", styles['CustomTitle']))
    story.append(Paragraph("Gestione File e Archivio - MyGest", styles['SubTitle']))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y')}", styles['CustomBody']))
    story.append(PageBreak())
    
    # Indice
    story.append(Paragraph("INDICE", styles['SectionTitle']))
    indice = """
    1. Panoramica<br/>
    2. Architettura dello Storage<br/>
    3. Configurazione per Ambiente<br/>
    4. Implementazione Tecnica<br/>
    5. Migrazione da media/ al Nuovo Storage<br/>
    6. Setup Ambiente Locale (WSL)<br/>
    7. Messa in Produzione (VPS)<br/>
    8. Script e Comandi Utili<br/>
    9. Risoluzione Problemi<br/>
    10. Riepilogo Modifiche Tecniche<br/>
    """
    story.append(Paragraph(indice, styles['CustomBody']))
    story.append(PageBreak())
    
    # 1. PANORAMICA
    story.append(Paragraph("1. PANORAMICA", styles['SectionTitle']))
    story.append(Paragraph(
        "MyGest utilizza una configurazione di storage centralizzata che separa completamente i file "
        "dell'archivio dalla directory media/ di default di Django. Tutti i file vengono salvati in una "
        "directory configurabile tramite la variabile d'ambiente <b>ARCHIVIO_BASE_PATH</b>.",
        styles['CustomBody']
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Obiettivi principali:</b>", styles['CustomBody']))
    story.append(Paragraph("• Separazione tra ambiente di sviluppo (WSL/NAS) e produzione (VPS)", styles['CustomBody']))
    story.append(Paragraph("• Gestione unificata di tutti i file del sistema", styles['CustomBody']))
    story.append(Paragraph("• Flessibilità nella configurazione del percorso di storage", styles['CustomBody']))
    story.append(Paragraph("• Facilità di backup e sincronizzazione", styles['CustomBody']))
    story.append(Spacer(1, 0.5*cm))
    
    # 2. ARCHITETTURA
    story.append(Paragraph("2. ARCHITETTURA DELLO STORAGE", styles['SectionTitle']))
    story.append(Paragraph("<b>Struttura delle directory:</b>", styles['SubTitle']))
    
    structure = """ARCHIVIO_BASE_PATH/
├── documenti/              # Documenti gestiti dal sistema
│   ├── 2024/
│   │   ├── CLI001/
│   │   └── CLI002/
│   └── 2025/
├── archivio_fisico/        # File dell'archivio fisico
│   ├── operazioni/         # Scansioni verbali operazioni
│   └── verbali/            # Template verbali
└── fascicoli/              # Fascicoli e documenti correlati"""
    
    story.append(Preformatted(structure, styles['CodeBlock']))
    story.append(Spacer(1, 0.5*cm))
    
    # 3. CONFIGURAZIONE
    story.append(Paragraph("3. CONFIGURAZIONE PER AMBIENTE", styles['SectionTitle']))
    
    story.append(Paragraph("<b>Ambiente Locale (WSL)</b>", styles['SubTitle']))
    story.append(Paragraph("Percorso: <b>/mnt/archivio</b> (montaggio NAS)", styles['CustomBody']))
    story.append(Paragraph("File di configurazione: <b>.env</b>", styles['CustomBody']))
    code_local = "ARCHIVIO_BASE_PATH=/mnt/archivio"
    story.append(Preformatted(code_local, styles['CodeBlock']))
    
    story.append(Paragraph("<b>Ambiente Produzione (VPS)</b>", styles['SubTitle']))
    story.append(Paragraph("Percorso: <b>/srv/mygest/archivio</b>", styles['CustomBody']))
    story.append(Paragraph("File di configurazione: <b>.env</b> o <b>.env.production</b>", styles['CustomBody']))
    code_prod = "ARCHIVIO_BASE_PATH=/srv/mygest/archivio"
    story.append(Preformatted(code_prod, styles['CodeBlock']))
    story.append(PageBreak())
    
    # 4. IMPLEMENTAZIONE TECNICA
    story.append(Paragraph("4. IMPLEMENTAZIONE TECNICA", styles['SectionTitle']))
    
    story.append(Paragraph("<b>NASPathStorage</b>", styles['SubTitle']))
    story.append(Paragraph(
        "Il progetto utilizza una classe di storage personalizzata definita in <b>mygest/storages.py</b>:",
        styles['CustomBody']
    ))
    
    code_storage = """from mygest.storages import NASPathStorage

nas_storage = NASPathStorage()

class Documento(models.Model):
    file = models.FileField(
        storage=nas_storage,
        upload_to="documenti/...",
        max_length=500
    )"""
    story.append(Preformatted(code_storage, styles['CodeBlock']))
    
    story.append(Paragraph("<b>Caratteristiche:</b>", styles['CustomBody']))
    story.append(Paragraph("• Legge dinamicamente il percorso da settings.ARCHIVIO_BASE_PATH", styles['CustomBody']))
    story.append(Paragraph("• Garantisce che i file vengano salvati nella directory corretta", styles['CustomBody']))
    story.append(Paragraph("• Supporta test e ambienti multipli", styles['CustomBody']))
    story.append(Spacer(1, 0.5*cm))
    
    # 5. MIGRAZIONE
    story.append(Paragraph("5. MIGRAZIONE DA MEDIA/ AL NUOVO STORAGE", styles['SectionTitle']))
    
    story.append(Paragraph("<b>Prerequisiti</b>", styles['SubTitle']))
    story.append(Paragraph("1. Backup completo del database", styles['CustomBody']))
    story.append(Paragraph("2. Backup completo della directory media/", styles['CustomBody']))
    story.append(Paragraph("3. NAS montato o directory creata", styles['CustomBody']))
    story.append(Paragraph("4. File .env aggiornato con ARCHIVIO_BASE_PATH", styles['CustomBody']))
    
    story.append(Paragraph("<b>Esecuzione Migrazione</b>", styles['SubTitle']))
    
    code_migrate = """# 1. Simulazione (dry-run)
cd /home/sandro/mygest
python scripts/migrate_storage.py --dry-run

# 2. Migrazione reale
python scripts/migrate_storage.py

# 3. Verifica
python manage.py runserver
# Testa upload/download documenti

# 4. Pulizia (dopo verifica)
rm -rf /home/sandro/mygest/media"""
    story.append(Preformatted(code_migrate, styles['CodeBlock']))
    story.append(PageBreak())
    
    # 6. SETUP LOCALE
    story.append(Paragraph("6. SETUP AMBIENTE LOCALE (WSL)", styles['SectionTitle']))
    
    story.append(Paragraph("<b>Opzione 1: Cambiare i permessi</b>", styles['SubTitle']))
    code_perm = """sudo chown -R sandro:sandro /mnt/archivio
sudo chmod -R 755 /mnt/archivio"""
    story.append(Preformatted(code_perm, styles['CodeBlock']))
    
    story.append(Paragraph("<b>Opzione 2: Montare il NAS (Raccomandato)</b>", styles['SubTitle']))
    code_mount = """# Smonta se già montato
sudo umount /mnt/archivio 2>/dev/null

# Crea il punto di montaggio
sudo mkdir -p /mnt/archivio

# Monta il NAS con permessi utente
sudo mount -t drvfs '\\\\IP_NAS\\SHARE' /mnt/archivio \\
    -o uid=$(id -u),gid=$(id -g),metadata

# Verifica
ls -ld /mnt/archivio
touch /mnt/archivio/test.txt && \\
    rm /mnt/archivio/test.txt && \\
    echo "✓ Scrittura OK" """
    story.append(Preformatted(code_mount, styles['CodeBlock']))
    
    story.append(Paragraph("<b>Verifica Setup</b>", styles['SubTitle']))
    code_check = """cd ~/mygest
source venv/bin/activate
python scripts/check_storage.py"""
    story.append(Preformatted(code_check, styles['CodeBlock']))
    story.append(PageBreak())
    
    # 7. PRODUZIONE
    story.append(Paragraph("7. MESSA IN PRODUZIONE (VPS)", styles['SectionTitle']))
    
    story.append(Paragraph("<b>1. Preparazione VPS</b>", styles['SubTitle']))
    code_vps_prep = """ssh user@your-vps

# Crea la directory archivio
sudo mkdir -p /srv/mygest/archivio
sudo chown www-data:www-data /srv/mygest/archivio
sudo chmod 755 /srv/mygest/archivio"""
    story.append(Preformatted(code_vps_prep, styles['CodeBlock']))
    
    story.append(Paragraph("<b>2. Configurazione Environment</b>", styles['SubTitle']))
    code_env = """cd /srv/mygest/app

# Crea/aggiorna .env
cat > .env << EOF
ARCHIVIO_BASE_PATH=/srv/mygest/archivio
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
EOF"""
    story.append(Preformatted(code_env, styles['CodeBlock']))
    
    story.append(Paragraph("<b>3. Deploy Applicazione</b>", styles['SubTitle']))
    code_deploy = """cd /srv/mygest/app
git pull origin main

source /srv/mygest/venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

sudo systemctl restart gunicorn
sudo systemctl restart nginx"""
    story.append(Preformatted(code_deploy, styles['CodeBlock']))
    
    story.append(Paragraph("<b>4. Migrazione File (se necessario)</b>", styles['SubTitle']))
    code_migrate_prod = """cd /srv/mygest/app
python scripts/migrate_storage.py --dry-run
python scripts/migrate_storage.py"""
    story.append(Preformatted(code_migrate_prod, styles['CodeBlock']))
    story.append(PageBreak())
    
    # 8. SCRIPT E COMANDI
    story.append(Paragraph("8. SCRIPT E COMANDI UTILI", styles['SectionTitle']))
    
    story.append(Paragraph("<b>Script check_storage.py</b>", styles['SubTitle']))
    story.append(Paragraph(
        "Verifica la configurazione dello storage e i permessi della directory:",
        styles['CustomBody']
    ))
    code_check_script = """python scripts/check_storage.py

# Output:
# - Configurazione (ARCHIVIO_BASE_PATH, MEDIA_ROOT, MEDIA_URL)
# - Verifica directory (esistenza, permessi)
# - Test scrittura/lettura
# - Statistiche file"""
    story.append(Preformatted(code_check_script, styles['CodeBlock']))
    
    story.append(Paragraph("<b>Script migrate_storage.py</b>", styles['SubTitle']))
    story.append(Paragraph(
        "Migra i file da media/ alla nuova struttura archivio:",
        styles['CustomBody']
    ))
    code_migrate_script = """# Simulazione (nessuna modifica)
python scripts/migrate_storage.py --dry-run

# Migrazione reale
python scripts/migrate_storage.py

# Caratteristiche:
# - Copia sicura (mantiene originali)
# - Report dettagliato
# - Gestione errori"""
    story.append(Preformatted(code_migrate_script, styles['CodeBlock']))
    
    story.append(Paragraph("<b>Backup e Sincronizzazione</b>", styles['SubTitle']))
    code_backup = """# Backup Locale → VPS
rsync -avz --progress /mnt/archivio/ \\
    user@vps:/srv/mygest/archivio/

# Backup VPS → Locale
rsync -avz --progress \\
    user@vps:/srv/mygest/archivio/ /mnt/archivio/"""
    story.append(Preformatted(code_backup, styles['CodeBlock']))
    story.append(PageBreak())
    
    # 9. TROUBLESHOOTING
    story.append(Paragraph("9. RISOLUZIONE PROBLEMI", styles['SectionTitle']))
    
    story.append(Paragraph("<b>File non trovati dopo migrazione</b>", styles['SubTitle']))
    code_trouble1 = """# Verifica configurazione
python manage.py shell
>>> from django.conf import settings
>>> print(settings.ARCHIVIO_BASE_PATH)

# Verifica permessi
ls -la /mnt/archivio  # locale
ls -la /srv/mygest/archivio  # VPS"""
    story.append(Preformatted(code_trouble1, styles['CodeBlock']))
    
    story.append(Paragraph("<b>Errori di permesso</b>", styles['SubTitle']))
    code_trouble2 = """# Locale (WSL)
sudo chown -R sandro:sandro /mnt/archivio

# VPS
sudo chown -R www-data:www-data /srv/mygest/archivio
sudo chmod -R 755 /srv/mygest/archivio"""
    story.append(Preformatted(code_trouble2, styles['CodeBlock']))
    
    story.append(Paragraph("<b>NAS non montato (WSL)</b>", styles['SubTitle']))
    code_trouble3 = """# Verifica il montaggio
mount | grep /mnt/archivio

# Monta manualmente
sudo mkdir -p /mnt/archivio
sudo mount -t drvfs '\\\\192.168.1.X\\share' /mnt/archivio"""
    story.append(Preformatted(code_trouble3, styles['CodeBlock']))
    story.append(PageBreak())
    
    # 10. RIEPILOGO MODIFICHE
    story.append(Paragraph("10. RIEPILOGO MODIFICHE TECNICHE", styles['SectionTitle']))
    
    story.append(Paragraph("<b>File Modificati</b>", styles['SubTitle']))
    story.append(Paragraph("• <b>mygest/settings.py</b> - Configurazione unificata storage", styles['CustomBody']))
    story.append(Paragraph("• <b>archivio_fisico/models.py</b> - Aggiunto nas_storage ai FileField", styles['CustomBody']))
    story.append(Paragraph("• <b>.env</b> - Aggiunto ARCHIVIO_BASE_PATH", styles['CustomBody']))
    story.append(Paragraph("• <b>README.md</b> - Riferimenti alla documentazione", styles['CustomBody']))
    story.append(Paragraph("• <b>.gitignore</b> - Esclusi file .env.production e .env.local", styles['CustomBody']))
    
    story.append(Paragraph("<b>File Creati</b>", styles['SubTitle']))
    story.append(Paragraph("• <b>.env.example</b> - Template configurazione", styles['CustomBody']))
    story.append(Paragraph("• <b>.env.production</b> - Configurazione VPS", styles['CustomBody']))
    story.append(Paragraph("• <b>scripts/migrate_storage.py</b> - Script migrazione file", styles['CustomBody']))
    story.append(Paragraph("• <b>scripts/check_storage.py</b> - Script verifica storage", styles['CustomBody']))
    story.append(Paragraph("• <b>docs/guida_storage.md</b> - Guida completa", styles['CustomBody']))
    story.append(Paragraph("• <b>docs/setup_archivio_locale.md</b> - Setup WSL", styles['CustomBody']))
    story.append(Paragraph("• <b>docs/RIEPILOGO_MODIFICHE_STORAGE.md</b> - Dettagli tecnici", styles['CustomBody']))
    
    story.append(Paragraph("<b>Benefici</b>", styles['SubTitle']))
    story.append(Paragraph("✓ Configurazione storage unificata e flessibile", styles['CustomBody']))
    story.append(Paragraph("✓ Separazione chiara tra sviluppo e produzione", styles['CustomBody']))
    story.append(Paragraph("✓ Script automatizzati per migrazione e verifica", styles['CustomBody']))
    story.append(Paragraph("✓ Documentazione completa e dettagliata", styles['CustomBody']))
    story.append(Paragraph("✓ Backup e sincronizzazione semplificati", styles['CustomBody']))
    story.append(Paragraph("✓ Struttura directory organizzata e logica", styles['CustomBody']))
    
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("<b>Stato:</b> ✅ Implementazione completata e testata", styles['CustomBody']))
    story.append(Paragraph("<b>Pronto per:</b> Testing locale e deploy produzione", styles['CustomBody']))

def main():
    """Genera il PDF"""
    output_path = BASE_DIR / OUTPUT_FILE
    
    print("=" * 80)
    print("GENERAZIONE PDF DOCUMENTAZIONE STORAGE")
    print("=" * 80)
    print(f"Output: {output_path}")
    print()
    
    # Crea il documento
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Crea gli stili
    styles = create_styles()
    
    # Crea la storia (contenuto)
    story = []
    add_content(story, styles)
    
    # Genera il PDF
    print("Generazione in corso...")
    doc.build(story)
    
    print()
    print("✓ PDF generato con successo!")
    print(f"  File: {output_path}")
    print(f"  Dimensione: {output_path.stat().st_size / 1024:.1f} KB")
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()
