#!/usr/bin/env python3
"""
MyGest Desktop Agent - Agent locale per eliminazione file

Questo agent gira sul PC dell'utente e si occupa di:
1. Monitorare le richieste di eliminazione dal server MyGest
2. Eliminare i file originali dal filesystem locale
3. Confermare l'eliminazione al server

Installazione:
    pip install requests watchdog

Uso:
    python mygest_agent.py --server http://localhost:8000 --token YOUR_TOKEN

Configurazione come servizio systemd:
    Vedi mygest-agent.service
"""

import os
import sys
import time
import json
import argparse
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import threading
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/.mygest-agent.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MyGestAgent')


class MyGestAgent:
    """Agent locale per comunicazione con MyGest server."""
    
    def __init__(self, server_url: str, api_token: str, poll_interval: int = 30):
        """
        Inizializza l'agent.
        
        Args:
            server_url: URL del server MyGest (es: http://localhost:8000)
            api_token: Token di autenticazione API
            poll_interval: Intervallo polling in secondi (default: 30)
        """
        self.server_url = server_url.rstrip('/')
        self.api_token = api_token
        self.poll_interval = poll_interval
        self.running = False
        
        # Percorsi protetti (NON verranno MAI eliminati)
        self.protected_paths = [
            '/mnt/archivio',           # Archivio documenti MyGest
            '/home/sandro/mygest',     # Progetto MyGest
            '/var/www',                # Web server
            '/opt',                    # Software installato
            '/usr',                    # Sistema
            '/etc',                    # Configurazioni
            '/bin',                    # Eseguibili sistema
            '/sbin',                   # Eseguibili amministrazione
        ]
        
        # Statistiche
        self.stats = {
            'deleted': 0,
            'errors': 0,
            'protected_blocks': 0,    # File bloccati per protezione
            'last_poll': None,
            'started_at': datetime.now()
        }
        
        logger.info(f"Agent inizializzato: server={server_url}, poll_interval={poll_interval}s")
        logger.info(f"⚠️  Percorsi protetti: {', '.join(self.protected_paths)}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Restituisce gli headers per le richieste API."""
        return {
            'Authorization': f'Token {self.api_token}',
            'Content-Type': 'application/json'
        }
    
    def ping_server(self) -> bool:
        """
        Verifica la connessione al server.
        
        Returns:
            True se il server è raggiungibile
        """
        try:
            response = requests.get(
                f'{self.server_url}/api/v1/agent/ping/',
                headers=self._get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Errore ping server: {e}")
            return False
    
    def get_pending_deletions(self) -> List[Dict]:
        """
        Ottiene la lista di file da eliminare.
        
        Returns:
            Lista di richieste di eliminazione pendenti
        """
        try:
            response = requests.get(
                f'{self.server_url}/api/v1/agent/pending-deletions/',
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('deletions', [])
            else:
                logger.warning(f"Errore recupero eliminazioni: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Errore durante get_pending_deletions: {e}")
            return []
    
    def is_protected_path(self, file_path: str) -> bool:
        """
        Verifica se il path è protetto e NON deve essere eliminato.
        
        Args:
            file_path: Percorso da verificare
            
        Returns:
            True se il path è protetto
        """
        try:
            # Rimuovi virgolette se presenti (da "Copia come percorso" Windows)
            clean_path = file_path.strip()
            if clean_path.startswith('"') and clean_path.endswith('"'):
                clean_path = clean_path[1:-1]
            if clean_path.startswith("'") and clean_path.endswith("'"):
                clean_path = clean_path[1:-1]
            
            path = Path(clean_path).resolve()
            path_str = str(path)
            
            for protected in self.protected_paths:
                if path_str.startswith(protected):
                    return True
            return False
        except Exception:
            # In caso di errore, proteggi per sicurezza
            return True
    
    def delete_file(self, file_path: str) -> bool:
        """
        Elimina un file dal filesystem locale.
        
        Args:
            file_path: Percorso completo del file
            
        Returns:
            True se l'eliminazione è riuscita
        """
        try:
            # Rimuovi virgolette se presenti
            clean_path = file_path.strip()
            if clean_path.startswith('"') and clean_path.endsWith('"'):
                clean_path = clean_path[1:-1]
            if clean_path.startswith("'") and clean_path.endsWith("'"):
                clean_path = clean_path[1:-1]
            
            # ⚠️ VERIFICA PROTEZIONE
            if self.is_protected_path(clean_path):
                logger.error(f"🛡️  BLOCCATO: Path protetto: {clean_path}")
                self.stats['protected_blocks'] += 1
                return False
            
            path = Path(clean_path).resolve()
            
            if not path.exists():
                logger.warning(f"File non trovato: {clean_path}")
                return False
            
            if not path.is_file():
                logger.error(f"Non è un file: {clean_path}")
                return False
            
            # Ottieni dimensione prima di eliminare
            file_size = path.stat().st_size
            
            # Elimina il file
            path.unlink()
            
            logger.info(f"✅ File eliminato: {clean_path} ({file_size} bytes)")
            self.stats['deleted'] += 1
            
            return True
            
        except PermissionError:
            logger.error(f"Permesso negato per eliminare: {clean_path}")
            return False
        except Exception as e:
            logger.error(f"Errore eliminando {clean_path}: {e}")
            self.stats['errors'] += 1
            return False
    
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
                'success': success
            }
            
            # Aggiungi error_message solo se presente
            if error_message:
                payload['error_message'] = error_message
            
            response = requests.post(
                f'{self.server_url}/api/v1/agent/confirm-deletion/',
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Conferma inviata per deletion_id={deletion_id}")
            else:
                logger.warning(
                    f"⚠️ Errore invio conferma: HTTP {response.status_code} "
                    f"per deletion_id={deletion_id}"
                )
                # Log della risposta per debug
                try:
                    error_detail = response.json()
                    logger.warning(f"Dettaglio errore: {error_detail}")
                except:
                    logger.warning(f"Response text: {response.text[:200]}")
                
        except Exception as e:
            logger.error(f"❌ Errore durante confirm_deletion: {e}")
    
    def process_pending_deletions(self):
        """Elabora tutte le richieste di eliminazione pendenti."""
        deletions = self.get_pending_deletions()
        
        if not deletions:
            logger.debug("Nessuna eliminazione pendente")
            return
        
        logger.info(f"Trovate {len(deletions)} richieste di eliminazione")
        
        for deletion in deletions:
            deletion_id = deletion.get('id')
            file_path = deletion.get('source_path')
            documento_id = deletion.get('documento_id')
            
            logger.info(
                f"Elaborazione richiesta {deletion_id}: "
                f"documento={documento_id}, path={file_path}"
            )
            
            # Tentativo di eliminazione
            success = self.delete_file(file_path)
            
            # Conferma al server
            error_msg = None if success else "Errore eliminazione file"
            self.confirm_deletion(deletion_id, success, error_msg)
            
            # Pausa tra le eliminazioni
            time.sleep(1)
    
    def run(self):
        """Esegue il loop principale dell'agent."""
        self.running = True
        logger.info("Agent avviato")
        
        # Verifica connessione iniziale
        if not self.ping_server():
            logger.error("Impossibile connettersi al server MyGest")
            logger.error(f"URL: {self.server_url}")
            logger.error("Verifica che il server sia in esecuzione e il token sia corretto")
            return
        
        logger.info("Connessione al server verificata ✓")
        
        try:
            while self.running:
                try:
                    self.stats['last_poll'] = datetime.now()
                    
                    # Elabora le richieste pendenti
                    self.process_pending_deletions()
                    
                    # Attendi prima del prossimo poll
                    time.sleep(self.poll_interval)
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(f"Errore nel loop principale: {e}", exc_info=True)
                    time.sleep(self.poll_interval)
                    
        except KeyboardInterrupt:
            logger.info("Arresto richiesto dall'utente")
        finally:
            self.running = False
            self.print_stats()
    
    def stop(self):
        """Ferma l'agent."""
        logger.info("Arresto agent in corso...")
        self.running = False
    
    def print_stats(self):
        """Stampa le statistiche dell'agent."""
        uptime = datetime.now() - self.stats['started_at']
        
        logger.info("=" * 60)
        logger.info("Statistiche Agent")
        logger.info("=" * 60)
        logger.info(f"Uptime: {uptime}")
        logger.info(f"File eliminati: {self.stats['deleted']}")
        logger.info(f"🛡️  Bloccati (protetti): {self.stats['protected_blocks']}")
        logger.info(f"Errori: {self.stats['errors']}")
        logger.info(f"Ultimo poll: {self.stats['last_poll']}")
        logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='MyGest Desktop Agent - Elimina file locali su richiesta del server'
    )
    parser.add_argument(
        '--server',
        required=True,
        help='URL del server MyGest (es: http://localhost:8000)'
    )
    parser.add_argument(
        '--token',
        required=True,
        help='Token API per autenticazione'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=30,
        help='Intervallo polling in secondi (default: 30)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Testa la connessione e esce'
    )
    
    args = parser.parse_args()
    
    # Crea l'agent
    agent = MyGestAgent(
        server_url=args.server,
        api_token=args.token,
        poll_interval=args.poll_interval
    )
    
    # Modalità test
    if args.test:
        if agent.ping_server():
            print("✓ Connessione al server riuscita")
            sys.exit(0)
        else:
            print("✗ Impossibile connettersi al server")
            sys.exit(1)
    
    # Gestione segnali
    def signal_handler(signum, frame):
        agent.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Avvia l'agent
    agent.run()


if __name__ == '__main__':
    main()
