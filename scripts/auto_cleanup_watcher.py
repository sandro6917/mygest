#!/usr/bin/env python3
"""
Script daemon per monitorare e pulire automaticamente i file uploadati.

Monitora una cartella "staging" e elimina i file dopo che sono stati
caricati con successo nell'archivio MyGest.

Uso:
    python auto_cleanup_watcher.py --watch-dir /percorso/staging --delay 300
"""

import os
import sys
import time
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Set

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'auto_cleanup.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AutoCleanup')


class FileWatcher:
    """Monitora una directory e gestisce la pulizia automatica dei file."""
    
    def __init__(self, watch_dir: str, delay_seconds: int = 300, 
                 state_file: str = None, marker_file: str = '.uploaded'):
        """
        Inizializza il watcher.
        
        Args:
            watch_dir: Directory da monitorare
            delay_seconds: Secondi di attesa prima di eliminare (default: 300 = 5 minuti)
            state_file: File per salvare lo stato (default: auto_cleanup_state.json)
            marker_file: Nome del file marker che indica upload completato (default: .uploaded)
        """
        self.watch_dir = Path(watch_dir).resolve()
        self.delay_seconds = delay_seconds
        self.marker_file = marker_file
        
        if state_file is None:
            state_file = os.path.join(os.path.dirname(__file__), 'auto_cleanup_state.json')
        self.state_file = state_file
        
        # Dizionario: filepath -> timestamp di quando è stato marcato
        self.marked_files: Dict[str, float] = {}
        self.load_state()
        
        logger.info(f"FileWatcher inizializzato: watch_dir={self.watch_dir}, delay={self.delay_seconds}s")
    
    def load_state(self):
        """Carica lo stato salvato."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    self.marked_files = json.load(f)
                logger.info(f"Stato caricato: {len(self.marked_files)} file marcati")
            except Exception as e:
                logger.warning(f"Impossibile caricare stato: {e}")
                self.marked_files = {}
    
    def save_state(self):
        """Salva lo stato corrente."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.marked_files, f, indent=2)
        except Exception as e:
            logger.error(f"Impossibile salvare stato: {e}")
    
    def scan_directory(self) -> Set[str]:
        """
        Scansiona la directory per file marcati.
        
        Returns:
            Set di percorsi file con marker presente
        """
        marked = set()
        
        if not self.watch_dir.exists():
            logger.warning(f"Directory non trovata: {self.watch_dir}")
            return marked
        
        # Cerca file marker
        for marker_path in self.watch_dir.rglob(self.marker_file):
            # Il file da eliminare ha lo stesso nome del marker ma senza il prefisso
            # Es: documento.pdf.uploaded -> documento.pdf
            target_file = marker_path.parent / marker_path.name.replace(self.marker_file, '')
            
            # Oppure, se il marker è nella stessa directory con nome fisso
            # cerchiamo tutti i file nella stessa directory
            parent_dir = marker_path.parent
            for file_path in parent_dir.iterdir():
                if file_path.is_file() and file_path.name != self.marker_file:
                    marked.add(str(file_path.resolve()))
        
        return marked
    
    def mark_file_for_deletion(self, filepath: str):
        """
        Marca un file per l'eliminazione futura.
        
        Args:
            filepath: Percorso del file da marcare
        """
        if filepath not in self.marked_files:
            self.marked_files[filepath] = time.time()
            logger.info(f"File marcato per eliminazione: {filepath}")
            self.save_state()
    
    def should_delete_file(self, filepath: str) -> bool:
        """
        Verifica se un file deve essere eliminato.
        
        Args:
            filepath: Percorso del file
            
        Returns:
            True se il file deve essere eliminato
        """
        if filepath not in self.marked_files:
            return False
        
        marked_time = self.marked_files[filepath]
        elapsed = time.time() - marked_time
        
        return elapsed >= self.delay_seconds
    
    def delete_file(self, filepath: str) -> bool:
        """
        Elimina un file e il suo marker.
        
        Args:
            filepath: Percorso del file da eliminare
            
        Returns:
            True se l'eliminazione è riuscita
        """
        try:
            # Elimina il file
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                logger.info(f"File eliminato: {filepath} ({file_size} bytes)")
            
            # Elimina il marker associato
            marker_path = Path(filepath).parent / self.marker_file
            if marker_path.exists():
                os.remove(marker_path)
                logger.debug(f"Marker eliminato: {marker_path}")
            
            # Rimuovi dallo stato
            if filepath in self.marked_files:
                del self.marked_files[filepath]
                self.save_state()
            
            return True
            
        except Exception as e:
            logger.error(f"Errore eliminando {filepath}: {e}")
            return False
    
    def cleanup_stale_entries(self):
        """Rimuove dallo stato i file che non esistono più."""
        to_remove = []
        for filepath in self.marked_files:
            if not os.path.exists(filepath):
                to_remove.append(filepath)
        
        if to_remove:
            for filepath in to_remove:
                del self.marked_files[filepath]
            self.save_state()
            logger.info(f"Rimossi {len(to_remove)} file obsoleti dallo stato")
    
    def run(self, interval: int = 60):
        """
        Esegue il loop principale di monitoraggio.
        
        Args:
            interval: Intervallo in secondi tra le scansioni (default: 60)
        """
        logger.info(f"Avvio monitoraggio di {self.watch_dir}")
        logger.info(f"Intervallo scansione: {interval}s, Delay eliminazione: {self.delay_seconds}s")
        
        try:
            while True:
                # Scansiona directory per nuovi file marcati
                marked = self.scan_directory()
                
                # Marca i nuovi file
                for filepath in marked:
                    if filepath not in self.marked_files:
                        self.mark_file_for_deletion(filepath)
                
                # Elimina i file che hanno superato il delay
                files_to_delete = [
                    fp for fp in self.marked_files.keys()
                    if self.should_delete_file(fp)
                ]
                
                for filepath in files_to_delete:
                    self.delete_file(filepath)
                
                # Pulizia periodica
                if int(time.time()) % 3600 == 0:  # Ogni ora
                    self.cleanup_stale_entries()
                
                # Attendi prima della prossima scansione
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Arresto richiesto dall'utente")
        except Exception as e:
            logger.error(f"Errore nel loop principale: {e}", exc_info=True)
        finally:
            self.save_state()


def main():
    parser = argparse.ArgumentParser(
        description='Monitora e pulisce automaticamente i file uploadati'
    )
    parser.add_argument(
        '--watch-dir',
        required=True,
        help='Directory da monitorare'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=300,
        help='Secondi di attesa prima di eliminare (default: 300)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Intervallo tra le scansioni in secondi (default: 60)'
    )
    parser.add_argument(
        '--marker',
        default='.uploaded',
        help='Nome del file marker (default: .uploaded)'
    )
    parser.add_argument(
        '--state-file',
        help='File per salvare lo stato (default: auto_cleanup_state.json)'
    )
    
    args = parser.parse_args()
    
    watcher = FileWatcher(
        watch_dir=args.watch_dir,
        delay_seconds=args.delay,
        state_file=args.state_file,
        marker_file=args.marker
    )
    
    watcher.run(interval=args.interval)


if __name__ == '__main__':
    main()
