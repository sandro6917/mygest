#!/usr/bin/env python3
"""
MyGest Agent - Versione Windows
================================

Agent desktop per eliminazione automatica file su filesystem Windows.
Gira direttamente su PC Windows e può accedere a path locali (C:\...) 
e di rete (\\server\share\...).

Installazione Windows:
    pip install requests

Configurazione:
    1. Ottieni token: python manage_agent_tokens.py show sandro
    2. Crea file config: config_agent.ini
    3. Avvia: python mygest_agent_windows.py

Esecuzione come servizio Windows:
    - Usa NSSM (Non-Sucking Service Manager)
    - Oppure Task Scheduler con trigger "At startup"
"""

import os
import sys
import time
import logging
import requests
import configparser
from pathlib import Path, PureWindowsPath
from datetime import datetime
from typing import List, Dict, Optional

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mygest_agent_windows.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('MyGestAgentWindows')


class MyGestAgentWindows:
    """
    Agent per eliminazione file su Windows.
    Supporta path locali (C:\...) e UNC (\\server\share\...).
    """
    
    def __init__(self, config_file: str = 'config_agent.ini'):
        """
        Inizializza l'agent leggendo la configurazione.
        
        Args:
            config_file: Path al file di configurazione
        """
        self.config = self._load_config(config_file)
        self.server_url = self.config['server']['url'].rstrip('/')
        self.token = self.config['server']['token']
        self.poll_interval = int(self.config['agent'].get('poll_interval', '30'))
        self.running = False
        
        # Statistiche
        self.stats = {
            'deleted': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        # Headers per autenticazione
        self.headers = {
            'Authorization': f'Token {self.token}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Agent Windows inizializzato")
        logger.info(f"Server: {self.server_url}")
        logger.info(f"Polling: ogni {self.poll_interval} secondi")
    
    def _load_config(self, config_file: str) -> configparser.ConfigParser:
        """Carica configurazione da file INI."""
        config = configparser.ConfigParser()
        
        if not os.path.exists(config_file):
            logger.error(f"File di configurazione non trovato: {config_file}")
            logger.info("Creane uno con:")
            logger.info("[server]")
            logger.info("url = http://localhost:8000")
            logger.info("token = IL_TUO_TOKEN")
            logger.info("[agent]")
            logger.info("poll_interval = 30")
            sys.exit(1)
        
        config.read(config_file, encoding='utf-8')
        return config
    
    def ping_server(self) -> bool:
        """Verifica connessione al server."""
        try:
            response = requests.get(
                f'{self.server_url}/api/v1/agent/ping/',
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Ping OK: {data.get('message')}")
                return True
            else:
                logger.warning(f"Ping fallito: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Errore ping: {e}")
            return False
    
    def get_pending_deletions(self) -> List[Dict]:
        """Recupera lista richieste di eliminazione pendenti."""
        try:
            response = requests.get(
                f'{self.server_url}/api/v1/agent/pending-deletions/',
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('deletions', [])
            else:
                logger.warning(f"Errore recupero richieste: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Errore chiamata API: {e}")
            return []
    
    def delete_file_windows(self, file_path: str) -> tuple[bool, Optional[str]]:
        """
        Elimina un file Windows (locale o di rete).
        
        Args:
            file_path: Path Windows (C:\... o \\server\share\...)
        
        Returns:
            Tuple (success, error_message)
        """
        try:
            # Normalizza path Windows
            path = Path(file_path)
            
            # Verifica esistenza
            if not path.exists():
                error_msg = f"File non trovato: {file_path}"
                logger.error(error_msg)
                return False, error_msg
            
            # Verifica che sia un file
            if not path.is_file():
                error_msg = f"Non è un file: {file_path}"
                logger.error(error_msg)
                return False, error_msg
            
            # Ottieni dimensione prima di eliminare
            file_size = path.stat().st_size
            
            # Elimina il file
            path.unlink()
            
            logger.info(f"✅ File eliminato: {file_path} ({file_size} bytes)")
            self.stats['deleted'] += 1
            
            return True, None
            
        except PermissionError as e:
            error_msg = f"Permesso negato: {file_path}"
            logger.error(error_msg)
            self.stats['errors'] += 1
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Errore eliminando {file_path}: {str(e)}"
            logger.error(error_msg)
            self.stats['errors'] += 1
            return False, error_msg
    
    def confirm_deletion(self, deletion_id: int, success: bool, error_message: str = None):
        """
        Conferma al server l'esito dell'eliminazione.
        
        Args:
            deletion_id: ID della richiesta di eliminazione
            success: True se l'eliminazione è riuscita
            error_message: Messaggio di errore opzionale
        """
        try:
            payload = {
                'deletion_id': deletion_id,
                'success': success,
                'error_message': error_message,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(
                f'{self.server_url}/api/v1/agent/confirm-deletion/',
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Conferma inviata per deletion_id={deletion_id}")
            else:
                logger.warning(f"⚠️ Errore invio conferma: HTTP {response.status_code} per deletion_id={deletion_id}")
                
        except Exception as e:
            logger.error(f"❌ Errore invio conferma: {e}")
    
    def process_deletions(self):
        """Elabora tutte le richieste di eliminazione pendenti."""
        deletions = self.get_pending_deletions()
        
        if not deletions:
            logger.debug("Nessuna richiesta di eliminazione pendente")
            return
        
        logger.info(f"Trovate {len(deletions)} richieste di eliminazione")
        
        for deletion in deletions:
            deletion_id = deletion['id']
            file_path = deletion['source_path']
            documento_id = deletion.get('documento')
            
            logger.info(f"Elaborazione richiesta {deletion_id}: documento={documento_id}, path={file_path}")
            
            # Tenta eliminazione
            success, error_message = self.delete_file_windows(file_path)
            
            # Conferma al server
            self.confirm_deletion(deletion_id, success, error_message)
    
    def print_stats(self):
        """Stampa statistiche correnti."""
        uptime = datetime.now() - self.stats['start_time']
        logger.info("=" * 60)
        logger.info(f"📊 STATISTICHE AGENT WINDOWS")
        logger.info(f"File eliminati: {self.stats['deleted']}")
        logger.info(f"Errori: {self.stats['errors']}")
        logger.info(f"Uptime: {uptime}")
        logger.info("=" * 60)
    
    def run(self):
        """Loop principale dell'agent."""
        logger.info("🚀 Avvio MyGest Agent Windows")
        logger.info(f"Piattaforma: {sys.platform}")
        logger.info(f"Python: {sys.version}")
        
        # Verifica connessione iniziale
        if not self.ping_server():
            logger.error("❌ Impossibile connettersi al server. Verificare configurazione.")
            return
        
        logger.info("✅ Connessione al server OK")
        logger.info(f"⏰ Polling ogni {self.poll_interval} secondi")
        logger.info("Premi Ctrl+C per terminare")
        logger.info("-" * 60)
        
        self.running = True
        iteration = 0
        
        try:
            while self.running:
                iteration += 1
                logger.debug(f"Iterazione {iteration}")
                
                # Elabora richieste
                self.process_deletions()
                
                # Stampa statistiche ogni 10 iterazioni
                if iteration % 10 == 0:
                    self.print_stats()
                
                # Attendi prossimo ciclo
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logger.info("\n⏹️  Interruzione richiesta dall'utente")
        except Exception as e:
            logger.error(f"❌ Errore inaspettato: {e}")
        finally:
            self.running = False
            self.print_stats()
            logger.info("👋 Agent terminato")


def main():
    """Entry point."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║           MyGest Agent - Versione Windows                 ║
║  Eliminazione automatica file dopo archiviazione          ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Cerca file di configurazione
    config_files = ['config_agent.ini', 'config_agent_windows.ini']
    config_file = None
    
    for cf in config_files:
        if os.path.exists(cf):
            config_file = cf
            break
    
    if not config_file:
        print("❌ File di configurazione non trovato!")
        print("\nCrea un file 'config_agent.ini' con:")
        print("-" * 60)
        print("[server]")
        print("url = http://TUO_SERVER:8000")
        print("token = IL_TUO_TOKEN")
        print("\n[agent]")
        print("poll_interval = 30")
        print("-" * 60)
        print("\nPer ottenere il token:")
        print("python manage_agent_tokens.py show tuo_username")
        sys.exit(1)
    
    # Avvia agent
    agent = MyGestAgentWindows(config_file)
    agent.run()


if __name__ == '__main__':
    main()
