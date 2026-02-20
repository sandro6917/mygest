#!/usr/bin/env python3
"""
Script per generare un PDF con l'analisi del progetto MyGest.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from datetime import datetime

def create_analysis_pdf():
    """Genera il PDF con l'analisi completa del progetto MyGest."""
    
    filename = f"Analisi_Progetto_MyGest_{datetime.now().strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4,
                          rightMargin=2*cm, leftMargin=2*cm,
                          topMargin=2*cm, bottomMargin=2*cm)
    
    # Container per gli elementi del documento
    story = []
    
    # Stili
    styles = getSampleStyleSheet()
    
    # Stili personalizzati
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#555555'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leading=14
    )
    
    critical_style = ParagraphStyle(
        'Critical',
        parent=body_style,
        textColor=colors.HexColor('#c0392b'),
        fontName='Helvetica-Bold'
    )
    
    warning_style = ParagraphStyle(
        'Warning',
        parent=body_style,
        textColor=colors.HexColor('#f39c12')
    )
    
    success_style = ParagraphStyle(
        'Success',
        parent=body_style,
        textColor=colors.HexColor('#27ae60')
    )
    
    # ===== TITOLO E INTESTAZIONE =====
    story.append(Paragraph("Analisi Progetto MyGest", title_style))
    story.append(Spacer(1, 0.3*cm))
    
    info_data = [
        ['Data Analisi:', datetime.now().strftime('%d/%m/%Y %H:%M')],
        ['Progetto:', 'MyGest - Sistema di Gestione Documentale'],
        ['Repository:', 'sandro6917/mygest'],
        ['Branch:', 'main'],
        ['Framework:', 'Django 4.2.16 + PostgreSQL'],
    ]
    
    info_table = Table(info_data, colWidths=[4*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
        ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.grey),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.8*cm))
    
    # ===== EXECUTIVE SUMMARY =====
    story.append(Paragraph("Executive Summary", heading1_style))
    story.append(Paragraph(
        "Il progetto MyGest è un'applicazione Django modulare per la gestione documentale, "
        "protocollo, pratiche e scadenze. L'architettura è ben strutturata con 12 app Django "
        "separate. <b>L'applicazione è già in produzione su VPS Hostinger</b> con configurazione "
        "di sicurezza adeguata (variabili d'ambiente, HTTPS, etc). L'ambiente analizzato è quello "
        "di sviluppo. Il codice è di buona qualità ma può beneficiare di miglioramenti in "
        "testing, monitoring e performance optimization.",
        body_style
    ))
    story.append(Spacer(1, 0.5*cm))
    
    # Tabella riepilogativa
    summary_data = [
        ['Categoria', 'Stato', 'Priorità'],
        ['Sicurezza Prod', '� CONFIGURATO', 'N/A'],
        ['Testing', '🟡 MEDIO', 'ALTA'],
        ['Performance', '🟡 MEDIO', 'MEDIA'],
        ['Architettura', '🟢 BUONO', 'MEDIA'],
        ['Monitoring', '🟡 BASE', 'ALTA'],
        ['Documentazione', '🟢 BUONO', 'BASSA'],
    ]
    
    summary_table = Table(summary_data, colWidths=[6*cm, 5*cm, 5*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    
    story.append(summary_table)
    story.append(PageBreak())
    
    # ===== NOTA IMPORTANTE =====
    story.append(Paragraph("⚠️ Nota Importante", heading1_style))
    story.append(Spacer(1, 0.2*cm))
    
    story.append(Paragraph(
        "<b>Ambiente Analizzato:</b> Questa analisi si basa sul codice dell'ambiente di sviluppo. "
        "L'applicazione è già <b>in produzione su VPS Hostinger</b> con configurazione di sicurezza "
        "adeguata (variabili d'ambiente tramite .env, DEBUG=False, ALLOWED_HOSTS configurato, HTTPS attivo). "
        "Le considerazioni di sicurezza riportate sono relative all'ambiente di sviluppo locale.",
        ParagraphStyle('Note', parent=body_style, 
                      backColor=colors.HexColor('#e8f4f8'),
                      borderPadding=10,
                      borderColor=colors.HexColor('#3498db'),
                      borderWidth=1)
    ))
    story.append(Spacer(1, 0.5*cm))
    
    # ===== AREE DI MIGLIORAMENTO =====
    story.append(Paragraph("🎯 Aree di Miglioramento", heading1_style))
    story.append(Spacer(1, 0.3*cm))
    
    # 1. Sicurezza - Best Practices
    story.append(Paragraph("1. Sicurezza - Best Practices Ambiente Dev", heading2_style))
    
    security_issues = [
        "<b>Separazione settings:</b> Creare settings/base.py, settings/dev.py, settings/prod.py per gestione più pulita",
        "<b>File .env nel repository:</b> Usare .env.example come template senza valori sensibili",
        "<b>csrf_exempt</b> in whatsapp/views.py - Valutare validazione signature webhook invece di disabilitare CSRF",
        "<b>Rate limiting:</b> Aggiungere django-ratelimit per proteggere login e API",
        "<b>Security headers:</b> Implementare django-csp per Content Security Policy",
        "<b>Audit log:</b> Tracciare accessi e modifiche critiche (protocollo, documenti)",
    ]
    
    for issue in security_issues:
        story.append(Paragraph(f"• {issue}", warning_style))
    
    story.append(Spacer(1, 0.4*cm))
    
    # 2. Database
    story.append(Paragraph("2. Database", heading2_style))
    
    db_issues = [
        "<b>Password database hardcoded</b> in settings.py (linea 106): 'ScegliUnaPasswordSicura'",
        "Uso estensivo di <b>on_delete=models.CASCADE</b> in 20+ modelli - Rischio eliminazioni a cascata non volute",
        "Mancano indici su campi frequently queried (es. stato, data_creazione in vari modelli)",
        "Nessun backup automatico configurato (solo script manuale backup_mygest.sh)",
        "Connection pooling non configurato per ambienti ad alto carico",
    ]
    
    for issue in db_issues:
        story.append(Paragraph(f"• {issue}", critical_style))
    
    story.append(Spacer(1, 0.4*cm))
    
    # 3. Gestione File
    story.append(Paragraph("3. Gestione File e Storage", heading2_style))
    
    storage_issues = [
        "Storage misto tra MEDIA_ROOT e NAS (NASPathStorage) può creare confusione",
        "Percorso temporaneo tmp/ in documento_upload_to non viene pulito automaticamente",
        "Path hardcoded: /mnt/archivio, /home/sandro/documenti - Non portabile",
        "Nessuna validazione dimensione massima file upload",
        "Mancano controlli antivirus sui file caricati",
    ]
    
    for issue in storage_issues:
        story.append(Paragraph(f"• {issue}", warning_style))
    
    story.append(PageBreak())
    
    # ===== MIGLIORAMENTI CONSIGLIATI =====
    story.append(Paragraph("🟡 Miglioramenti Consigliati", heading1_style))
    story.append(Spacer(1, 0.3*cm))
    
    # 1. Architettura & Codice
    story.append(Paragraph("1. Architettura & Codice", heading2_style))
    
    story.append(Paragraph("<b>Settings Management:</b>", heading3_style))
    arch_improvements = [
        "Separare settings per ambiente (base.py, dev.py, prod.py, test.py)",
        "Usare django-environ per TUTTE le variabili sensibili",
        "Implementare settings validation al startup",
        "Creare template .env.example senza valori sensibili",
    ]
    for item in arch_improvements:
        story.append(Paragraph(f"• {item}", body_style))
    
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Performance:</b>", heading3_style))
    perf_improvements = [
        "Implementare caching (Redis/Memcached) - attualmente assente",
        "Aggiungere Django Debug Toolbar in sviluppo per analisi query",
        "Ottimizzare query N+1 - select_related/prefetch_related presente ma non ovunque",
        "Implementare paginazione consistente su tutte le liste",
        "Database connection pooling (pgBouncer in produzione)",
        "Compressione statica (django-compressor, Brotli/Gzip)",
    ]
    for item in perf_improvements:
        story.append(Paragraph(f"• {item}", body_style))
    
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Testing:</b>", heading3_style))
    test_improvements = [
        "Coverage attuale molto bassa - aumentare al 70%+ minimo",
        "Mancano test di integrazione tra app",
        "Nessun test per API GraphQL/REST",
        "Aggiungere test per validatori CF/PIVA",
        "Implementare CI/CD pipeline (GitHub Actions)",
        "Test di carico e stress testing",
    ]
    for item in test_improvements:
        story.append(Paragraph(f"• {item}", body_style))
    
    story.append(Spacer(1, 0.4*cm))
    
    # 2. Code Quality
    story.append(Paragraph("2. Code Quality", heading2_style))
    
    quality_items = [
        "Type hints più consistenti (mypy installato ma poco utilizzato)",
        "Docstrings mancanti nella maggior parte delle funzioni",
        "Logging strutturato (attualmente solo protocollazione.log)",
        "Exception handling più robusto e specifico",
        "Validazioni business logic centralizzate nei modelli",
        "Codice duplicato in vari admin.py e forms.py",
    ]
    for item in quality_items:
        story.append(Paragraph(f"• {item}", body_style))
    
    story.append(Spacer(1, 0.4*cm))
    
    # 3. Dipendenze
    story.append(Paragraph("3. Gestione Dipendenze", heading2_style))
    
    deps_table_data = [
        ['Problema', 'Descrizione', 'Azione'],
        ['Duplicati', 'psycopg2-binary appare 2 volte', 'Rimuovere duplicato'],
        ['Conflitto', 'psycopg e psycopg-binary insieme', 'Usare solo psycopg[binary]'],
        ['Versioni', 'Versioni pinned ma vecchie', 'Aggiornare Django 4.2.16 → 5.1+'],
        ['Sicurezza', 'Verificare vulnerabilità note', 'pip-audit o safety check'],
    ]
    
    deps_table = Table(deps_table_data, colWidths=[3.5*cm, 7*cm, 5.5*cm])
    deps_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(deps_table)
    story.append(Spacer(1, 0.4*cm))
    
    # 4. Task Asincroni
    story.append(Paragraph("4. Task Asincroni", heading2_style))
    
    story.append(Paragraph(
        "File <b>comunicazioni/tasks.py</b> presente ma <b>Celery/Redis NON configurato</b>. "
        "Questo è un problema significativo perché:",
        body_style
    ))
    
    async_issues = [
        "Email import è potenzialmente bloccante (IMAP sync)",
        "Invio massivo comunicazioni blocca l'applicazione",
        "Generazione report PDF pesanti rallenta le richieste",
        "Sincronizzazione Google Calendar sincrona",
        "Nessuna gestione retry per operazioni fallite",
    ]
    for item in async_issues:
        story.append(Paragraph(f"• {item}", warning_style))
    
    story.append(PageBreak())
    
    # 5. API & Monitoring
    story.append(Paragraph("5. API & Monitoring", heading2_style))
    
    story.append(Paragraph("<b>API:</b>", heading3_style))
    api_items = [
        "GraphQL configurato ma schema minimale (solo in mygest/schema.py)",
        "REST API solo per comunicazioni (comunicazioni/api/)",
        "Mancano endpoint per: documenti, pratiche, fascicoli, protocollo",
        "Autenticazione API limitata a Session/Basic - mancano token JWT",
        "Nessuna throttling/rate limiting",
        "Documentazione API assente (considerare drf-spectacular)",
    ]
    for item in api_items:
        story.append(Paragraph(f"• {item}", body_style))
    
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Monitoring:</b>", heading3_style))
    
    monitoring_missing = [
        "Sentry o simile per error tracking",
        "Application Performance Monitoring (APM) - es. New Relic, DataDog",
        "Structured logging (JSON logs per parsing automatico)",
        "Health check endpoints (/health/, /ready/)",
        "Metrics/Prometheus per metriche applicative",
        "Uptime monitoring e alerting",
    ]
    for item in monitoring_missing:
        story.append(Paragraph(f"• {item}", warning_style))
    
    story.append(PageBreak())
    
    # ===== PUNTI DI FORZA =====
    story.append(Paragraph("🟢 Punti di Forza", heading1_style))
    story.append(Spacer(1, 0.3*cm))
    
    strengths = [
        ("Architettura modulare", "12 app Django ben separate: anagrafiche, documenti, pratiche, fascicoli, protocollo, scadenze, comunicazioni, whatsapp, archivio_fisico, stampe, titolario"),
        ("Modelli Django standard", "Uso corretto di ForeignKey, ManyToMany, scelte, validators personalizzati"),
        ("Validatori robusti", "Validazione CF/PIVA con checksum completo secondo normativa italiana"),
        ("Documentazione presente", "4 guide in docs/: guida_messa_in_produzione, guida_principianti, guida_scadenze"),
        ("Script di deploy", "scripts/deploy.sh automatizza: pull, pip install, migrate, collectstatic, restart"),
        ("Permessi gestiti", "@login_required presente su tutte le view sensibili"),
        ("Transazioni database", "Uso corretto di @transaction.atomic per operazioni critiche"),
        ("Query optimization", "select_related/prefetch_related presenti in views e admin"),
        ("Migrazioni strutturate", "148 file di migrazione, schema database ben evolvibile"),
        ("Integrazione esterna", "WhatsApp Cloud API, Google Calendar, IMAP/SMTP configurabile"),
        ("Multi-DB test", "Configurazione automatica SQLite per tests (settings.py linea 137)"),
        ("Gestione protocollo", "Sistema completo di protocollazione IN/OUT con numerazione automatica"),
    ]
    
    for title, desc in strengths:
        story.append(Paragraph(f"<b>{title}:</b> {desc}", success_style))
        story.append(Spacer(1, 0.2*cm))
    
    story.append(PageBreak())
    
    # ===== EVOLUZIONI SUGGERITE =====
    story.append(Paragraph("🚀 Roadmap Evolutiva", heading1_style))
    story.append(Spacer(1, 0.3*cm))
    
    # Fase 1
    story.append(Paragraph("Fase 1: Qualità e Monitoring (1-2 mesi) - PRIORITÀ ALTA", heading2_style))
    
    phase1_data = [
        ['Area', 'Attività', 'Effort', 'Impatto'],
        ['Settings', 'Separare settings per ambiente\nTemplate .env.example\nAudit logging', '3gg', 'ALTO'],
        ['Monitoring', 'Integrare Sentry\nHealth check endpoints\nLog aggregation (ELK/Loki)\nUptime monitoring', '4gg', 'ALTO'],
        ['Testing', 'Coverage base 70%+\nTest per protocollo/documenti\nCI/CD pipeline (GitHub Actions)\nTest di integrazione', '8gg', 'ALTO'],
        ['Database', 'Review CASCADE deletes\nAggiungere indici mancanti\nVerificare backup automatici\nQuery optimization', '4gg', 'ALTO'],
    ]
    
    phase1_table = Table(phase1_data, colWidths=[3*cm, 8*cm, 2*cm, 3*cm])
    phase1_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c0392b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ffe6e6')]),
    ]))
    
    story.append(phase1_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Fase 2
    story.append(Paragraph("Fase 2: Performance (2-3 mesi) - PRIORITÀ MEDIA", heading2_style))
    
    phase2_data = [
        ['Area', 'Attività', 'Effort', 'Impatto'],
        ['Caching', 'Redis per sessioni e cache\nCache query frequenti\nTemplate fragment caching', '4gg', 'ALTO'],
        ['Async Tasks', 'Setup Celery + Redis\nQueue per email e notifiche\nBackground jobs import/export', '6gg', 'ALTO'],
        ['DB Optimization', 'Query analyzer e ottimizzazione\nConnection pooling (pgBouncer)\nPartitioning tabelle grandi', '5gg', 'MEDIO'],
        ['Frontend', 'Asset optimization (compress)\nLazy loading immagini\nWebpack/Vite per bundle', '4gg', 'MEDIO'],
    ]
    
    phase2_table = Table(phase2_data, colWidths=[3*cm, 8*cm, 2*cm, 3*cm])
    phase2_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff5e6')]),
    ]))
    
    story.append(phase2_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Fase 3
    story.append(Paragraph("Fase 3: Feature Enhancement (3-6 mesi) - PRIORITÀ BASSA", heading2_style))
    
    phase3_items = [
        "<b>API Completa:</b> REST API per tutte le risorse, versioning, OpenAPI/Swagger docs, JWT auth",
        "<b>Frontend Moderno:</b> SPA con React/Vue, Progressive Web App, real-time updates (WebSockets)",
        "<b>Integrazioni Avanzate:</b> Firma digitale, PEC avanzata, calendar sync bidirezionale, export contabilità",
        "<b>Business Intelligence:</b> Dashboard analytics, report customizzabili, export strutturati",
        "<b>Multi-tenancy:</b> Supporto multi-cliente, permessi granulari RBAC, isolamento dati",
        "<b>Mobile App:</b> App nativa iOS/Android o PWA avanzata per gestione mobile",
    ]
    
    for item in phase3_items:
        story.append(Paragraph(f"• {item}", body_style))
    
    story.append(PageBreak())
    
    # ===== CHECKLIST IMMEDIATA =====
    story.append(Paragraph("📋 Checklist Immediata (Prossime 2 Settimane)", heading1_style))
    story.append(Spacer(1, 0.3*cm))
    
    checklist_data = [
        ['Prior.', 'Task', 'Effort', 'Status'],
        ['🔴', 'Separare settings: base.py, dev.py, prod.py', '2h', '☐'],
        ['🔴', 'Creare .env.example (senza valori sensibili)', '30min', '☐'],
        ['🔴', 'Aggiungere Sentry per error tracking', '1h', '☐'],
        ['🔴', 'Implementare health check endpoint', '1h', '☐'],
        ['🟡', 'Verificare backup automatici DB su VPS', '1h', '☐'],
        ['🟡', 'Creare test per funzioni critiche (protocollo)', '4h', '☐'],
        ['🟡', 'Aggiungere test coverage measurement (coverage.py)', '1h', '☐'],
        ['🟡', 'Documentare API GraphQL/REST esistenti', '2h', '☐'],
        ['🟡', 'Review CASCADE deletes nei modelli', '3h', '☐'],
        ['🟡', 'Aggiungere indici database mancanti', '2h', '☐'],
        ['�', 'Implementare audit log per azioni critiche', '3h', '☐'],
        ['🟢', 'Setup Django Debug Toolbar in dev', '30min', '☐'],
        ['🟢', 'Configurare Celery + Redis per task async', '4h', '☐'],
        ['🟢', 'Aggiungere rate limiting (django-ratelimit)', '2h', '☐'],
        ['🟢', 'Implementare monitoring uptime (UptimeRobot)', '30min', '☐'],
    ]
    
    checklist_table = Table(checklist_data, colWidths=[1.5*cm, 9*cm, 2*cm, 1.5*cm])
    checklist_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    
    story.append(checklist_table)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph(
        "<i>Legenda: 🔴 Critico | 🟡 Importante | 🟢 Consigliato</i>",
        ParagraphStyle('Legend', parent=body_style, fontSize=8, textColor=colors.grey)
    ))
    
    story.append(PageBreak())
    
    # ===== METRICHE RACCOMANDATE =====
    story.append(Paragraph("📈 Metriche e KPI Raccomandati", heading1_style))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("Metriche da tracciare per monitorare la salute dell'applicazione:", body_style))
    story.append(Spacer(1, 0.3*cm))
    
    metrics_data = [
        ['Categoria', 'Metrica', 'Soglia Target', 'Tool Consigliato'],
        ['Performance', 'Tempo risposta medio endpoint', '< 200ms', 'APM / Django Debug Toolbar'],
        ['Performance', 'Query database lente', '< 100ms', 'django-silk / pgBadger'],
        ['Performance', 'Tempo generazione PDF', '< 5s', 'Custom logging'],
        ['Affidabilità', 'Error rate', '< 0.1%', 'Sentry'],
        ['Affidabilità', 'Uptime', '> 99.5%', 'UptimeRobot / Pingdom'],
        ['Affidabilità', 'Success rate email', '> 98%', 'Custom metric'],
        ['Storage', 'Utilizzo disco NAS', '< 80%', 'System monitoring'],
        ['Storage', 'File temp non puliti', '0', 'Cron job + log'],
        ['Database', 'Dimensione database', 'Monitoraggio crescita', 'PostgreSQL stats'],
        ['Database', 'Connection pool usage', '< 80%', 'pgBouncer stats'],
        ['Sicurezza', 'Failed login attempts', 'Alert > 10/min', 'Django signals + Sentry'],
        ['Sicurezza', 'Accessi non autorizzati', '0', 'Custom middleware'],
        ['Business', 'Documenti protocollati/giorno', 'Trend', 'Custom analytics'],
        ['Business', 'Pratiche aperte/chiuse', 'Ratio', 'Custom analytics'],
        ['Business', 'Tempo medio chiusura pratica', 'Report mensile', 'Custom analytics'],
    ]
    
    metrics_table = Table(metrics_data, colWidths=[3*cm, 5*cm, 3.5*cm, 4.5*cm])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    
    story.append(metrics_table)
    story.append(PageBreak())
    
    # ===== CONCLUSIONI =====
    story.append(Paragraph("Conclusioni", heading1_style))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph(
        "Il progetto <b>MyGest</b> presenta un'architettura solida e ben strutturata, "
        "con moduli Django chiaramente separati e un buon utilizzo delle funzionalità del framework. "
        "La qualità del codice è generalmente buona, con validatori personalizzati, gestione transazioni "
        "e ottimizzazioni query già implementate.",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph(
        "<b>Punti di attenzione per lo sviluppo continuo:</b>",
        heading3_style
    ))
    story.append(Spacer(1, 0.2*cm))
    
    attention_points = [
        "Testing: aumentare coverage e aggiungere test di integrazione",
        "Monitoring: implementare Sentry e metriche applicative",
        "Performance: valutare caching e task asincroni per operazioni pesanti",
        "Manutenibilità: separare settings per ambiente e migliorare documentazione API",
    ]
    for item in attention_points:
        story.append(Paragraph(f"• {item}", body_style))
    
    story.append(Spacer(1, 0.4*cm))
    
    story.append(Paragraph(
        "L'applicazione è già operativa in produzione con successo. Gli sforzi futuri dovrebbero "
        "concentrarsi su qualità del codice, testing, monitoring e performance optimization. "
        "L'implementazione della Fase 1 (Qualità e Monitoring) porterebbe significativi benefici "
        "in termini di manutenibilità e visibilità sullo stato dell'applicazione.",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph(
        "<b>Raccomandazione finale:</b> Concentrarsi sulla checklist immediata e sulla Fase 1 "
        "della roadmap, con particolare enfasi su testing, monitoring e separazione degli ambienti. "
        "Il ROI di queste attività è alto in termini di stabilità operativa e manutenibilità futura.",
        ParagraphStyle('Recommendation', parent=body_style, 
                      textColor=colors.HexColor('#27ae60'),
                      fontName='Helvetica-Bold')
    ))
    
    story.append(Spacer(1, 1*cm))
    
    # Footer
    story.append(Paragraph(
        "_______________________________________________",
        ParagraphStyle('Line', parent=body_style, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"Documento generato automaticamente - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle('Footer', parent=body_style, fontSize=8, 
                      textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    # Build PDF
    doc.build(story)
    print(f"✅ PDF generato con successo: {filename}")
    return filename

if __name__ == "__main__":
    create_analysis_pdf()
