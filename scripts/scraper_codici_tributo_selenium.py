"""
Scraper avanzato per codici tributo F24 usando Selenium.

Questo script usa Selenium per gestire siti con JavaScript dinamico.
Richiede Chrome/Chromium e chromedriver installati.

Installazione dipendenze:
    pip install selenium webdriver-manager

Uso:
    python scraper_codici_tributo_selenium.py
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium non installato. Installa con: pip install selenium webdriver-manager")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SeleniumCodiceTributoScraper:
    """Scraper avanzato con Selenium per pagine JavaScript."""
    
    def __init__(self, headless: bool = True):
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium non disponibile")
        
        self.headless = headless
        self.driver = None
        self.codici = []
    
    def setup_driver(self):
        """Configura il driver Chrome."""
        logger.info("Configurazione Chrome WebDriver...")
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("✓ Driver configurato")
    
    def scrape_agenzia_entrate_erario(self) -> List[Dict]:
        """Scrape codici tributo Erario dall'Agenzia delle Entrate."""
        url = "https://www.agenziaentrate.gov.it/portale/web/guest/schede/versamenti/f24/f24-codici-tributo-erario"
        logger.info(f"Caricamento pagina: {url}")
        
        try:
            self.driver.get(url)
            
            # Attendi che la pagina sia caricata
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            time.sleep(2)  # Attesa aggiuntiva per JavaScript
            
            # Cerca le tabelle
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            logger.info(f"Trovate {len(tables)} tabelle")
            
            codici = []
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                
                for row in rows[1:]:  # Salta l'header
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        codice = {
                            'codice': cells[0].text.strip(),
                            'sezione': 'erario',
                            'descrizione': cells[1].text.strip(),
                            'causale': cells[2].text.strip() if len(cells) > 2 else '',
                            'periodicita': '',
                            'note': '',
                            'attivo': True,
                            'data_inizio_validita': None,
                            'data_fine_validita': None,
                        }
                        
                        if codice['codice'] and len(codice['codice']) <= 10:
                            codici.append(codice)
            
            logger.info(f"✓ Estratti {len(codici)} codici Erario")
            return codici
        
        except Exception as e:
            logger.error(f"Errore scraping Erario: {e}")
            return []
    
    def scrape_all(self) -> List[Dict]:
        """Esegue lo scraping completo."""
        all_codici = []
        
        # Erario
        codici_erario = self.scrape_agenzia_entrate_erario()
        all_codici.extend(codici_erario)
        
        # Qui si possono aggiungere altri metodi per INPS, Regioni, ecc.
        
        return all_codici
    
    def save_to_json(self, codici: List[Dict], output_dir: str = 'scripts'):
        """Salva i codici in formato JSON."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = output_path / f'codici_tributo_f24_selenium_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(codici, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Salvati {len(codici)} codici in {filename}")
    
    def run(self):
        """Esegue lo scraping completo."""
        try:
            self.setup_driver()
            
            logger.info("="*60)
            logger.info("Inizio scraping con Selenium")
            logger.info("="*60)
            
            codici = self.scrape_all()
            
            # Rimuovi duplicati
            seen = set()
            unique_codici = []
            for codice in codici:
                key = (codice['codice'], codice['sezione'])
                if key not in seen:
                    seen.add(key)
                    unique_codici.append(codice)
            
            logger.info(f"\nTotale codici estratti: {len(unique_codici)}")
            
            if unique_codici:
                self.save_to_json(unique_codici)
            else:
                logger.warning("Nessun codice estratto")
            
            logger.info("="*60)
            logger.info("Scraping completato!")
            logger.info("="*60)
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Driver chiuso")


def main():
    """Funzione principale."""
    if not SELENIUM_AVAILABLE:
        print("\n❌ Selenium non installato!")
        print("Installa con: pip install selenium webdriver-manager")
        print("\nIn alternativa, usa lo scraper base con dati manuali:")
        print("python scripts/scraper_codici_tributo.py")
        return
    
    scraper = SeleniumCodiceTributoScraper(headless=True)
    scraper.run()


if __name__ == '__main__':
    main()
