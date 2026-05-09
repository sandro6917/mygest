#!/usr/bin/env python3
"""
MyGest Agent con Auto-Detection File

Estensione dell'agent che monitora cartelle configurate e correla
automaticamente i file uploadati per eliminarli senza input utente.

Workflow:
1. Agent monitora cartelle (es: Downloads, Desktop)
2. Tiene cache recente dei file (nome + dimensione + path)
3. Quando backend chiede eliminazione, cerca match per nome+size
4. Se trova corrispondenza univoca, elimina automaticamente
"""

import os
import time
import signal
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

logger = logging.getLogger('MyGestAgent')


class FileTracker:
    """Traccia file in cartelle monitorate per correlazione automatica."""
    
    def __init__(self, retention_hours: int = 24):
        """
        Args:
            retention_hours: Ore di retention cache file (default: 24h)
        """
        self.retention_hours = retention_hours
        # Cache: {filename: [(full_path, size, modified_time), ...]}
        self.file_cache: Dict[str, List[Tuple[str, int, datetime]]] = {}
        
    def add_file(self, file_path: str):
        """Aggiunge un file alla cache."""
        try:
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                return
            
            filename = path.name
            size = path.stat().st_size
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            
            if filename not in self.file_cache:
                self.file_cache[filename] = []
            
            # Aggiungi alla lista (possono esserci omonimi)
            self.file_cache[filename].append((str(path), size, mtime))
            
            logger.debug(f"File aggiunto a cache: {filename} ({size} bytes)")
            
        except Exception as e:
            logger.error(f"Errore aggiungendo file a cache: {e}")
    
    def cleanup_old_entries(self):
        """Rimuove voci vecchie dalla cache."""
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)
        
        for filename in list(self.file_cache.keys()):
            # Filtra voci vecchie
            self.file_cache[filename] = [
                (path, size, mtime) 
                for path, size, mtime in self.file_cache[filename]
                if mtime > cutoff
            ]
            
            # Rimuovi chiave se lista vuota
            if not self.file_cache[filename]:
                del self.file_cache[filename]
    
    def find_file_by_name_and_size(
        self, 
        filename: str, 
        file_size: Optional[int] = None
    ) -> Optional[str]:
        """
        Cerca un file per nome e dimensione.
        
        Args:
            filename: Nome del file
            file_size: Dimensione in bytes (opzionale ma consigliata)
            
        Returns:
            Path completo se trovata corrispondenza univoca, None altrimenti
        """
        if filename not in self.file_cache:
            logger.debug(f"File non in cache: {filename}")
            return None
        
        matches = self.file_cache[filename]
        
        # Se abbiamo size, filtra per dimensione
        if file_size is not None:
            matches = [
                (path, size, mtime) 
                for path, size, mtime in matches 
                if size == file_size
            ]
        
        if len(matches) == 0:
            logger.debug(f"Nessun match per {filename} (size={file_size})")
            return None
        
        if len(matches) > 1:
            logger.warning(
                f"Multipli match per {filename} (size={file_size}): {len(matches)} file. "
                f"Non posso determinare quale eliminare."
            )
            return None
        
        # Corrispondenza univoca ✅
        full_path, _, _ = matches[0]
        
        # Verifica che esista ancora
        if not Path(full_path).exists():
            logger.warning(f"File trovato in cache ma non esiste più: {full_path}")
            return None
        
        logger.info(f"✅ Match trovato: {filename} → {full_path}")
        return full_path


class MonitoredFolderHandler(FileSystemEventHandler):
    """Handler per eventi filesystem nelle cartelle monitorate."""
    
    def __init__(self, tracker: FileTracker):
        self.tracker = tracker
    
    def on_created(self, event):
        """Chiamato quando un file viene creato."""
        if not event.is_directory:
            logger.debug(f"File creato: {event.src_path}")
            self.tracker.add_file(event.src_path)
    
    def on_modified(self, event):
        """Chiamato quando un file viene modificato."""
        if not event.is_directory:
            logger.debug(f"File modificato: {event.src_path}")
            # Riaggiorna cache (potrebbe essere cambiata dimensione)
            self.tracker.add_file(event.src_path)


class MyGestAgentWithAutoDetection:
    """Agent esteso con auto-detection file."""
    
    def __init__(
        self, 
        server_url: str, 
        api_token: str,
        monitored_folders: List[str] = None,
        poll_interval: int = 30,
        protected_paths: List[str] = None,
        cache_retention_hours: int = 24
    ):
        # Importa agent base
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        from mygest_agent import MyGestAgent
        
        # Inizializza agent base
        self.base_agent = MyGestAgent(server_url, api_token, poll_interval)
        
        # Override protected paths se forniti
        if protected_paths:
            self.base_agent.protected_paths = protected_paths
        
        # Espone attributi necessari
        self.running = True
        self.stats = {
            'files_deleted': 0,
            'files_failed': 0,
            'auto_detected': 0,
            'manual_required': 0
        }
        
        # Tracker per correlazione automatica
        self.tracker = FileTracker(retention_hours=cache_retention_hours)
        
        # Cartelle monitorate (default comuni)
        if monitored_folders is None:
            monitored_folders = [
                os.path.expanduser('~/Downloads'),
                os.path.expanduser('~/Desktop'),
                os.path.expanduser('~/Documents'),
            ]
        
        self.monitored_folders = [
            path for path in monitored_folders 
            if os.path.exists(path)
        ]
        
        # Watchdog observers per monitoraggio real-time
        self.observers = []
        
        logger.info(f"Cartelle monitorate: {', '.join(self.monitored_folders)}")
    
    def start_monitoring(self):
        """Avvia monitoraggio cartelle."""
        handler = MonitoredFolderHandler(self.tracker)
        
        for folder in self.monitored_folders:
            observer = Observer()
            observer.schedule(handler, folder, recursive=False)
            observer.start()
            self.observers.append(observer)
            logger.info(f"📂 Monitoraggio avviato: {folder}")
        
        # Scan iniziale cartelle
        self._initial_scan()
    
    def _initial_scan(self):
        """Scan iniziale delle cartelle monitorate."""
        logger.info("Scansione iniziale cartelle...")
        
        for folder in self.monitored_folders:
            try:
                for file_path in Path(folder).iterdir():
                    if file_path.is_file():
                        self.tracker.add_file(str(file_path))
            except Exception as e:
                logger.error(f"Errore scansione {folder}: {e}")
        
        logger.info(f"Scansione completata: {len(self.tracker.file_cache)} file unici tracciati")
    
    def process_deletion_with_auto_detection(self, deletion: Dict):
        """
        Elabora eliminazione con auto-detection.
        
        Se source_path è vuoto, prova a trovare file automaticamente.
        """
        deletion_id = deletion.get('id')
        source_path = deletion.get('source_path', '').strip()
        filename = deletion.get('file_name')  # Backend deve passarlo
        file_size = deletion.get('file_size')
        
        # Se path esplicito, usa quello (comportamento originale)
        if source_path:
            logger.info(f"Path esplicito fornito: {source_path}")
            success = self.delete_file(source_path)
            self.confirm_deletion(deletion_id, success)
            return
        
        # 🔍 AUTO-DETECTION
        if not filename:
            logger.error(f"Deletion {deletion_id}: né path né filename forniti")
            self.confirm_deletion(
                deletion_id, 
                False, 
                "Né path esplicito né filename disponibili per auto-detection"
            )
            return
        
        logger.info(f"🔍 Auto-detection per: {filename} (size={file_size})")
        
        # Cerca nella cache
        found_path = self.tracker.find_file_by_name_and_size(filename, file_size)
        
        if found_path:
            logger.info(f"✅ File trovato automaticamente: {found_path}")
            success = self.delete_file(found_path)
            self.confirm_deletion(deletion_id, success)
        else:
            logger.warning(
                f"❌ File non trovato: {filename}. "
                f"Potrebbe essere già stato eliminato o non essere nelle cartelle monitorate."
            )
            self.confirm_deletion(
                deletion_id, 
                False, 
                f"File {filename} non trovato nelle cartelle monitorate"
            )
    
    def print_stats(self):
        """Stampa statistiche sessione."""
        logger.info("=== Statistiche Sessione ===")
        logger.info(f"File eliminati: {self.stats['files_deleted']}")
        logger.info(f"Fallimenti: {self.stats['files_failed']}")
        logger.info(f"Auto-detected: {self.stats['auto_detected']}")
        logger.info(f"Richiesta manuale: {self.stats['manual_required']}")
    
    def get_pending_deletions(self):
        """Delega a agent base."""
        return self.base_agent.get_pending_deletions()
    
    def delete_file(self, path: str) -> bool:
        """Delega a agent base."""
        return self.base_agent.delete_file(path)
    
    def confirm_deletion(self, deletion_id: int, success: bool, error_message: str = None):
        """Delega a agent base."""
        return self.base_agent.confirm_deletion(deletion_id, success, error_message)
    
    def run(self):
        """Esegue il loop principale con monitoraggio."""
        self.start_monitoring()
        
        # Signal handlers
        def signal_handler(sig, frame):
            logger.info("Arresto richiesto via segnale")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Agent avviato con auto-detection")
        logger.info(f"Polling ogni {self.base_agent.poll_interval} secondi")
        
        try:
            while self.running:
                # Cleanup cache periodico
                self.tracker.cleanup_old_entries()
                
                # Elabora richieste eliminazione
                deletions = self.get_pending_deletions()
                for deletion in deletions:
                    self.process_deletion_with_auto_detection(deletion)
                
                time.sleep(self.base_agent.poll_interval)
        
        except Exception as e:
            logger.error(f"Errore nel loop principale: {e}")
        finally:
            # Stop observers
            for observer in self.observers:
                observer.stop()
                observer.join()
            
            self.print_stats()


# Esempio uso con configurazione
if __name__ == '__main__':
    import argparse
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='MyGest Agent con Auto-Detection')
    parser.add_argument('--config', help='File configurazione (default: ~/.mygest-agent.conf)')
    args = parser.parse_args()
    
    # Carica configurazione
    sys.path.insert(0, os.path.dirname(__file__))
    from mygest_agent_config import create_agent_from_config
    
    try:
        # Crea agent da configurazione con auto-detection
        base_agent_data = create_agent_from_config(args.config)
        
        agent = MyGestAgentWithAutoDetection(
            server_url=base_agent_data['server_url'],
            api_token=base_agent_data['api_token'],
            monitored_folders=base_agent_data['monitored_folders'],
            poll_interval=base_agent_data['poll_interval'],
            protected_paths=base_agent_data['protected_paths'],
            cache_retention_hours=base_agent_data['cache_retention_hours']
        )
        
        agent.run()
        
    except Exception as e:
        logger.error(f"Errore fatale: {e}")
        sys.exit(1)

