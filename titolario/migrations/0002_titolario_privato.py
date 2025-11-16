from django.db import migrations

def create_titolario_privato(apps, schema_editor):
    TitolarioVoce = apps.get_model("titolario", "TitolarioVoce")

    titolario = [
        ("GOV", "Governance", [
            ("ATT", "Atti societari", []),
            ("ORG", "Organigramma e deleghe", []),
            ("BD", "CdA e verbali", []),
            ("POL", "Policy e procedure interne", []),
        ]),
        ("AF", "Amministrazione, Finanza e Controllo", [
            ("AF-ACQ", "Contabilità fornitori", []),
            ("AF-VEN", "Contabilità clienti", []),
            ("AF-PRC", "Prima nota e cassa", []),
            ("AF-TES", "Tesoreria e banche", []),
            ("AF-IVA", "IVA", []),
            ("AF-LIB", "Libri contabili", []),
            ("AF-DIC", "Dichiarazioni fiscali", []),
            ("AF-TAX", "Imposte e tasse", []),
            ("AF-BIL", "Bilanci e reportistica", []),
            ("AF-CTR", "Controllo di gestione", []),
            ("AF-CESP", "Cespiti e inventari", []),
            ("AF_IMM", "Immobilizzazioni", []),
        ]),
        ("HR", "Risorse Umane", [
            ("HR-PERS", "Dossier personale", []),
            ("HR-PAY", "Paghe e contributi", []),
            ("HR-REC", "Recruiting e selezione", []),
            ("HR-FORM", "Formazione", []),
            ("HR-SAF", "Salute e sicurezza", []),
        ]),
        ("SALES", "Commerciale e Vendite", [
            ("SALES-LEAD", "Lead e opportunità", []),
            ("SALES-OFF", "Offerte e preventivi", []),
            ("SALES-ORD", "Ordini clienti", []),
            ("SALES-CTR", "Contratti commerciali", []),
        ]),
        ("MKT", "Marketing e Comunicazione", [
            ("MKT-CAMP", "Campagne", []),
            ("MKT-BRAND", "Brand e materiali", []),
            ("MKT-EVT", "Eventi e fiere", []),
            ("MKT-PR", "Comunicazione e PR", []),
        ]),
        ("PROC", "Acquisti e Fornitori", [
            ("PROC-REQ", "Richieste di acquisto", []),
            ("PROC-ORD", "Ordini a fornitori", []),
            ("PROC-CTR", "Contratti fornitori", []),
            ("PROC-VENDOR", "Albo fornitori", []),
        ]),
        ("OPS", "Operazioni / Produzione", [
            ("OPS-PROD", "Piani e ordini di produzione", []),
            ("OPS-MAN", "Manutenzione", []),
            ("OPS-QUAL", "Qualità di processo", []),
        ]),
        ("LOG", "Logistica", [
            ("LOG-MAG", "Magazzino e inventario", []),
            ("LOG-SPED", "Spedizioni", []),
            ("LOG-TRAS", "Trasporti", []),
        ]),
        ("IT", "Sistemi Informativi", [
            ("IT-INFRA", "Infrastruttura", []),
            ("IT-APP", "Applicazioni", []),
            ("IT-TKT", "Ticketing e assistenza", []),
            ("IT-SEC", "Sicurezza informatica", []),
        ]),
        ("LEG", "Affari Legali e Societari", [
            ("LEG-CTR", "Contratti", []),
            ("LEG-CONT", "Contenzioso", []),
            ("LEG-PRIV", "Privacy GDPR", []),
            ("LEG-IP", "Proprietà intellettuale", []),
        ]),
        ("QHSE", "Qualità, Sicurezza e Ambiente", [
            ("QHSE-QMS", "Sistema gestione qualità", []),
            ("QHSE-HSE", "Sicurezza sul lavoro", []),
            ("QHSE-ENV", "Ambiente", []),
            ("QHSE-AUD", "Audit e non conformità", []),
        ]),
        ("RND", "Ricerca e Sviluppo", [
            ("RND-IDEA", "Idee e fattibilità", []),
            ("RND-PJT", "Progetti R&D", []),
            ("RND-DOC", "Documentazione tecnica", []),
        ]),
        ("PRJ", "Progetti / Clienti", [
            ("PRJ-CLI", "Clienti e commesse", []),
            ("PRJ-CONTR", "Contratti di progetto", []),
            ("PRJ-DOC", "Documentazione progetto", []),
        ]),
    ]

    def ensure(parent, code, title, pattern=None):
        defaults = {"titolo": title}
        if pattern:
            defaults["pattern_codice"] = pattern
        obj, created = TitolarioVoce.objects.get_or_create(
            parent=parent, codice=code, defaults=defaults
        )
        changed = False
        if obj.titolo != title:
            obj.titolo = title
            changed = True
        if pattern and obj.pattern_codice != pattern:
            obj.pattern_codice = pattern
            changed = True
        if changed:
            obj.save(update_fields=["titolo", "pattern_codice"])
        return obj

    def build(parent, nodes):
        for item in nodes:
            # tuple: (codice, titolo, figli[, pattern_codice])
            code, title, children, *rest = item
            pattern = rest[0] if rest else None
            node = ensure(parent, code, title, pattern)
            build(node, children)

    build(None, titolario)

def delete_titolario_privato(apps, schema_editor):
    TitolarioVoce = apps.get_model("titolario", "TitolarioVoce")
    root_codes = ["GOV","AF","HR","SALES","MKT","PROC","OPS","LOG","IT","LEG","QHSE","RND","PRJ"]
    TitolarioVoce.objects.filter(parent__isnull=True, codice__in=root_codes).delete()

class Migration(migrations.Migration):
    dependencies = [
        ("titolario", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_titolario_privato, delete_titolario_privato),
    ]