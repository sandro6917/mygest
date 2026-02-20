"""
Scraper Avanzato Codici Tributo F24 - Agenzia delle Entrate
=============================================================

Questo script scarica e aggiorna automaticamente i codici tributo F24
dal sito ufficiale dell'Agenzia delle Entrate.

Link principali:
- Erariali e Regionali: https://www.agenziaentrate.gov.it/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti/tabelle-dei-codici-tributo-e-altri-codici-per-il-modello-f24/tabella-codici-tributo-erariali-e-regionali
- Tributi Locali: https://www.agenziaentrate.gov.it/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti/tabelle-dei-codici-tributo-e-altri-codici-per-il-modello-f24/tabelle-codici-per-tributi-locali
- INPS: https://www.agenziaentrate.gov.it/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti/tabelle-dei-codici-tributo-e-altri-codici-per-il-modello-f24/tabelle-codici-inps-e-enti-previdenziali-ed-assicurativi

Uso:
    python scripts/scraper_ade_ufficiale.py [--update-db] [--export-csv] [--export-json]
    
Opzioni:
    --update-db     Aggiorna il database Django
    --export-csv    Esporta i risultati in CSV
    --export-json   Esporta i risultati in JSON
    --verbose       Output dettagliato
"""

import os
import sys
import requests
import json
import csv
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
import argparse

# Setup Django se necessario
if '--update-db' in sys.argv:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
    django.setup()
    from scadenze.models import CodiceTributoF24


class ScraperADEUfficiale:
    """Scraper per i codici tributo dal sito dell'Agenzia delle Entrate."""
    
    BASE_URL = "https://www.agenziaentrate.gov.it"
    
    URLS = {
        'erario_regioni': '/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti/tabelle-dei-codici-tributo-e-altri-codici-per-il-modello-f24/tabella-codici-tributo-erariali-e-regionali',
        'tributi_locali': '/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti/tabelle-dei-codici-tributo-e-altri-codici-per-il-modello-f24/tabelle-codici-per-tributi-locali',
        'inps': '/portale/strumenti/codici-attivita-e-tributo/f24-codici-tributo-per-i-versamenti/tabelle-dei-codici-tributo-e-altri-codici-per-il-modello-f24/tabelle-codici-inps-e-enti-previdenziali-ed-assicurativi',
    }
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.codici: List[Dict] = []
    
    def log(self, message: str):
        """Log se verbose."""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Scarica una pagina e ritorna il BeautifulSoup."""
        try:
            self.log(f"Scaricamento: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"❌ Errore scaricamento {url}: {e}")
            return None
    
    def pulisci_testo(self, testo: str) -> str:
        """Pulisce un testo da spazi multipli e caratteri strani."""
        if not testo:
            return ""
        # Rimuovi spazi multipli
        testo = re.sub(r'\s+', ' ', testo)
        # Rimuovi \n, \t, \r
        testo = testo.replace('\n', ' ').replace('\t', ' ').replace('\r', ' ')
        return testo.strip()
    
    def estrai_codici_da_tabella(self, soup: BeautifulSoup, sezione: str) -> List[Dict]:
        """Estrae codici tributo da una tabella HTML."""
        codici = []
        
        # Cerca tutte le tabelle nella pagina
        tabelle = soup.find_all('table')
        self.log(f"Trovate {len(tabelle)} tabelle in sezione '{sezione}'")
        
        for idx, tabella in enumerate(tabelle):
            self.log(f"  Analisi tabella {idx + 1}...")
            
            # Cerca l'header per capire la struttura
            headers = []
            header_row = tabella.find('thead')
            if header_row:
                headers = [self.pulisci_testo(th.get_text()) for th in header_row.find_all(['th', 'td'])]
            else:
                # Prova con la prima riga
                first_row = tabella.find('tr')
                if first_row:
                    headers = [self.pulisci_testo(cell.get_text()) for cell in first_row.find_all(['th', 'td'])]
            
            self.log(f"    Headers: {headers}")
            
            # Estrai le righe dati
            tbody = tabella.find('tbody') or tabella
            righe = tbody.find_all('tr')
            
            for riga in righe:
                celle = riga.find_all(['td', 'th'])
                if len(celle) < 2:
                    continue
                
                # Estrai i dati dalla riga
                dati = [self.pulisci_testo(cella.get_text()) for cella in celle]
                
                # Salta righe header
                if any(h.lower() in dati[0].lower() for h in ['codice', 'tributo', 'descrizione']):
                    continue
                
                # Cerca di mappare i dati
                codice = dati[0] if dati else None
                descrizione = dati[1] if len(dati) > 1 else None
                causale = dati[2] if len(dati) > 2 else None
                
                # Validazione
                if not codice or len(codice) < 2 or len(codice) > 10:
                    continue
                
                if not descrizione or len(descrizione) < 5:
                    continue
                
                # Determina se è obsoleto
                attivo = True
                if descrizione:
                    parole_obsoleto = ['soppresso', 'abolito', 'non più', 'cessato', 'dismesso', 'abrogato']
                    attivo = not any(p in descrizione.lower() for p in parole_obsoleto)
                
                codici.append({
                    'codice': codice,
                    'sezione': sezione,
                    'descrizione': descrizione,
                    'causale': causale if causale and len(causale) > 3 else None,
                    'periodicita': None,
                    'attivo': attivo,
                    'fonte': 'ADE',
                    'data_aggiornamento': datetime.now().strftime('%Y-%m-%d')
                })
        
        return codici
    
    def scrape_erario_regioni(self):
        """Scarica codici tributo ERARIO e REGIONI."""
        self.log("\n🏛️  Scaricamento codici ERARIO e REGIONI...")
        url = self.BASE_URL + self.URLS['erario_regioni']
        soup = self.fetch_page(url)
        
        if not soup:
            print("❌ Impossibile scaricare la pagina Erario/Regioni")
            return
        
        # Estrai codici erario
        codici = self.estrai_codici_da_tabella(soup, 'erario')
        
        # Alcuni codici potrebbero essere regionali
        for codice in codici:
            # Identifica codici regionali (solitamente hanno prefisso particolare)
            if any(keyword in codice['descrizione'].lower() for keyword in ['region', 'irap', 'addizionale regional']):
                codice['sezione'] = 'regioni'
        
        self.codici.extend(codici)
        print(f"✓ Trovati {len(codici)} codici ERARIO/REGIONI")
    
    def scrape_tributi_locali(self):
        """Scarica codici tributo LOCALI (IMU, TASI, TARI)."""
        self.log("\n🏘️  Scaricamento codici TRIBUTI LOCALI...")
        url = self.BASE_URL + self.URLS['tributi_locali']
        soup = self.fetch_page(url)
        
        if not soup:
            print("❌ Impossibile scaricare la pagina Tributi Locali")
            return
        
        codici = self.estrai_codici_da_tabella(soup, 'imu')
        self.codici.extend(codici)
        print(f"✓ Trovati {len(codici)} codici TRIBUTI LOCALI")
    
    def scrape_inps(self):
        """Scarica codici tributo INPS e altri enti previdenziali."""
        self.log("\n💼 Scaricamento codici INPS...")
        url = self.BASE_URL + self.URLS['inps']
        soup = self.fetch_page(url)
        
        if not soup:
            print("❌ Impossibile scaricare la pagina INPS")
            return
        
        codici = self.estrai_codici_da_tabella(soup, 'inps')
        
        # Identifica altri enti (INAIL, etc.)
        for codice in codici:
            if 'inail' in codice['descrizione'].lower():
                codice['sezione'] = 'inail'
        
        self.codici.extend(codici)
        print(f"✓ Trovati {len(codici)} codici INPS/ENTI")
    
    def scrape_all(self):
        """Scarica tutti i codici tributo."""
        print("\n" + "="*60)
        print("🚀 SCRAPER CODICI TRIBUTO F24 - AGENZIA DELLE ENTRATE")
        print("="*60)
        
        self.scrape_erario_regioni()
        self.scrape_tributi_locali()
        self.scrape_inps()
        
        print(f"\n📊 TOTALE CODICI SCARICATI: {len(self.codici)}")
        
        # Statistiche
        sezioni = {}
        for codice in self.codici:
            sezione = codice['sezione']
            sezioni[sezione] = sezioni.get(sezione, 0) + 1
        
        print("\n📈 Statistiche per sezione:")
        for sezione, count in sorted(sezioni.items()):
            print(f"  - {sezione.upper()}: {count} codici")
    
    def export_csv(self, filename: str = "codici_tributo_ade.csv"):
        """Esporta i codici in formato CSV."""
        filepath = os.path.join('scripts', filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if not self.codici:
                print("⚠️  Nessun codice da esportare")
                return
            
            fieldnames = ['codice', 'sezione', 'descrizione', 'causale', 'periodicita', 'attivo', 'fonte', 'data_aggiornamento']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for codice in self.codici:
                writer.writerow(codice)
        
        print(f"✓ CSV esportato: {filepath}")
    
    def export_json(self, filename: str = "codici_tributo_ade.json"):
        """Esporta i codici in formato JSON."""
        filepath = os.path.join('scripts', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'fonte': 'Agenzia delle Entrate',
                    'url': 'https://www.agenziaentrate.gov.it',
                    'data_scaricamento': datetime.now().isoformat(),
                    'totale_codici': len(self.codici)
                },
                'codici': self.codici
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✓ JSON esportato: {filepath}")
    
    def update_database(self):
        """Aggiorna il database Django con i codici scaricati."""
        print("\n💾 Aggiornamento database...")
        
        creati = 0
        aggiornati = 0
        
        for codice_data in self.codici:
            codice, created = CodiceTributoF24.objects.update_or_create(
                codice=codice_data['codice'],
                sezione=codice_data['sezione'],
                defaults={
                    'descrizione': codice_data['descrizione'],
                    'causale': codice_data['causale'],
                    'periodicita': codice_data['periodicita'],
                    'attivo': codice_data['attivo'],
                }
            )
            
            if created:
                creati += 1
            else:
                aggiornati += 1
        
        print(f"✓ Database aggiornato:")
        print(f"  - Creati: {creati} nuovi codici")
        print(f"  - Aggiornati: {aggiornati} codici esistenti")
        print(f"  - Totale nel DB: {CodiceTributoF24.objects.count()}")


def main():
    parser = argparse.ArgumentParser(
        description='Scraper codici tributo F24 dall\'Agenzia delle Entrate'
    )
    parser.add_argument('--update-db', action='store_true',
                        help='Aggiorna il database Django')
    parser.add_argument('--export-csv', action='store_true',
                        help='Esporta in formato CSV')
    parser.add_argument('--export-json', action='store_true',
                        help='Esporta in formato JSON')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Output dettagliato')
    
    args = parser.parse_args()
    
    # Se nessuna opzione, esporta tutto
    if not any([args.update_db, args.export_csv, args.export_json]):
        args.export_csv = True
        args.export_json = True
    
    # Crea scraper ed esegui
    scraper = ScraperADEUfficiale(verbose=args.verbose)
    scraper.scrape_all()
    
    # Esporta/aggiorna
    if args.export_csv:
        scraper.export_csv()
    
    if args.export_json:
        scraper.export_json()
    
    if args.update_db:
        scraper.update_database()
    
    print("\n✅ Operazione completata!")
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
