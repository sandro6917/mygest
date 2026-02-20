#!/usr/bin/env python3
"""
Script interattivo per gestire l'eliminazione di file dopo l'upload.

Questo script fornisce un'interfaccia interattiva per:
1. Selezionare file da eliminare
2. Vedere un'anteprima delle informazioni
3. Confermare l'eliminazione
4. Mantenere un log delle eliminazioni

Uso:
    python interactive_file_cleanup.py
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import glob


class FileCleanupManager:
    """Gestisce l'eliminazione interattiva dei file uploadati."""
    
    def __init__(self, log_file: str = None):
        """
        Inizializza il manager.
        
        Args:
            log_file: Percorso del file di log (default: scripts/deleted_files.log)
        """
        if log_file is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            log_file = os.path.join(script_dir, 'deleted_files.log')
        
        self.log_file = log_file
        self.deleted_files = []
    
    def cerca_file(self, directory: str = None, pattern: str = "*.*") -> List[str]:
        """
        Cerca file in una directory.
        
        Args:
            directory: Directory dove cercare (default: directory corrente)
            pattern: Pattern per filtrare i file (es: "*.pdf")
            
        Returns:
            Lista di percorsi file trovati
        """
        if directory is None:
            directory = os.getcwd()
        
        search_path = os.path.join(directory, pattern)
        files = glob.glob(search_path)
        
        # Filtra solo i file (non le directory)
        return [f for f in files if os.path.isfile(f)]
    
    def mostra_menu_principale(self):
        """Mostra il menu principale interattivo."""
        print("\n" + "="*70)
        print(" "*20 + "GESTIONE FILE UPLOADATI")
        print("="*70)
        print("\n📁 Opzioni disponibili:\n")
        print("  1. Elimina file specifico (inserisci percorso)")
        print("  2. Cerca e seleziona file nella directory corrente")
        print("  3. Cerca file in una directory specifica")
        print("  4. Visualizza log eliminazioni")
        print("  5. Esci")
        print("\n" + "="*70)
    
    def ottieni_info_file(self, filepath: str) -> Dict:
        """
        Ottiene informazioni dettagliate su un file.
        
        Args:
            filepath: Percorso del file
            
        Returns:
            Dizionario con le informazioni del file
        """
        try:
            stat = os.stat(filepath)
            size = stat.st_size
            
            # Formatta dimensione
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.2f} KB"
            elif size < 1024 * 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.2f} MB"
            else:
                size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
            
            return {
                'path': os.path.abspath(filepath),
                'name': os.path.basename(filepath),
                'size': size,
                'size_str': size_str,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'exists': True
            }
        except Exception as e:
            return {
                'path': filepath,
                'error': str(e),
                'exists': False
            }
    
    def mostra_file_con_selezione(self, files: List[str]) -> List[str]:
        """
        Mostra una lista di file e permette la selezione multipla.
        
        Args:
            files: Lista di percorsi file
            
        Returns:
            Lista di file selezionati
        """
        if not files:
            print("\n❌ Nessun file trovato.")
            return []
        
        print(f"\n📄 Trovati {len(files)} file(s):\n")
        
        # Mostra lista numerata
        for i, filepath in enumerate(files, 1):
            info = self.ottieni_info_file(filepath)
            if info['exists']:
                print(f"  {i:2d}. {info['name']:40s} {info['size_str']:>10s}  {info['modified']}")
            else:
                print(f"  {i:2d}. {filepath:40s} [ERRORE: {info.get('error')}]")
        
        print("\nInserisci i numeri dei file da eliminare (es: 1,3,5 oppure 1-3):")
        print("Oppure 'all' per tutti, 'q' per annullare")
        
        while True:
            try:
                scelta = input("\n>>> ").strip().lower()
                
                if scelta == 'q':
                    return []
                
                if scelta == 'all':
                    return files
                
                # Parse selezione
                selected_indices = set()
                parts = scelta.split(',')
                
                for part in parts:
                    part = part.strip()
                    if '-' in part:
                        # Range
                        start, end = map(int, part.split('-'))
                        selected_indices.update(range(start, end + 1))
                    else:
                        # Singolo numero
                        selected_indices.add(int(part))
                
                # Valida gli indici
                if any(i < 1 or i > len(files) for i in selected_indices):
                    print(f"❌ Errore: Inserisci numeri tra 1 e {len(files)}")
                    continue
                
                # Restituisci i file selezionati
                return [files[i - 1] for i in sorted(selected_indices)]
                
            except ValueError:
                print("❌ Formato non valido. Riprova.")
            except Exception as e:
                print(f"❌ Errore: {e}")
    
    def conferma_eliminazione(self, files: List[str]) -> bool:
        """
        Chiede conferma finale per l'eliminazione.
        
        Args:
            files: Lista di file da eliminare
            
        Returns:
            True se confermato, False altrimenti
        """
        print(f"\n{'='*70}")
        print("⚠️  CONFERMA ELIMINAZIONE")
        print(f"{'='*70}")
        print(f"\nStai per eliminare {len(files)} file(s):\n")
        
        total_size = 0
        for filepath in files:
            info = self.ottieni_info_file(filepath)
            if info['exists']:
                print(f"  ❌ {info['name']}")
                total_size += info['size']
        
        # Formatta dimensione totale
        if total_size < 1024 * 1024:
            total_str = f"{total_size / 1024:.2f} KB"
        else:
            total_str = f"{total_size / (1024 * 1024):.2f} MB"
        
        print(f"\n📊 Spazio totale da liberare: {total_str}")
        print(f"{'='*70}")
        
        while True:
            risposta = input("\n🔴 Confermi l'eliminazione? (SI/no): ").strip()
            if risposta.upper() in ['SI', 'S', 'SÌ', 'YES', 'Y', '']:
                return True
            elif risposta.upper() in ['NO', 'N']:
                return False
            else:
                print("❌ Risposta non valida. Digita 'SI' o 'no'.")
    
    def elimina_files(self, files: List[str]) -> Dict:
        """
        Elimina i file selezionati.
        
        Args:
            files: Lista di file da eliminare
            
        Returns:
            Dizionario con risultati
        """
        risultati = {
            'eliminati': [],
            'falliti': []
        }
        
        print(f"\n{'='*70}")
        print("🗑️  ELIMINAZIONE IN CORSO...")
        print(f"{'='*70}\n")
        
        for filepath in files:
            try:
                info = self.ottieni_info_file(filepath)
                os.remove(filepath)
                
                risultati['eliminati'].append(filepath)
                self.deleted_files.append({
                    'path': filepath,
                    'name': info.get('name', os.path.basename(filepath)),
                    'size': info.get('size', 0),
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                })
                
                print(f"  ✅ {os.path.basename(filepath)}")
                
            except Exception as e:
                risultati['falliti'].append((filepath, str(e)))
                self.deleted_files.append({
                    'path': filepath,
                    'timestamp': datetime.now().isoformat(),
                    'success': False,
                    'error': str(e)
                })
                print(f"  ❌ {os.path.basename(filepath)} - Errore: {e}")
        
        # Salva log
        self.salva_log()
        
        # Mostra riepilogo
        print(f"\n{'='*70}")
        print(f"✅ File eliminati: {len(risultati['eliminati'])}")
        print(f"❌ File non eliminati: {len(risultati['falliti'])}")
        print(f"{'='*70}\n")
        
        return risultati
    
    def salva_log(self):
        """Salva il log delle eliminazioni."""
        try:
            # Carica log esistente
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = {'deletions': []}
            
            # Aggiungi nuove eliminazioni
            log_data['deletions'].extend(self.deleted_files)
            
            # Salva
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            self.deleted_files = []  # Reset
            
        except Exception as e:
            print(f"⚠️  Impossibile salvare il log: {e}")
    
    def visualizza_log(self):
        """Visualizza il log delle eliminazioni."""
        if not os.path.exists(self.log_file):
            print("\n📝 Nessun log disponibile.")
            return
        
        try:
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            
            deletions = log_data.get('deletions', [])
            
            if not deletions:
                print("\n📝 Nessuna eliminazione registrata.")
                return
            
            print(f"\n{'='*70}")
            print(f"📝 LOG ELIMINAZIONI ({len(deletions)} operazioni)")
            print(f"{'='*70}\n")
            
            for entry in deletions[-20:]:  # Ultimi 20
                timestamp = entry.get('timestamp', 'N/A')
                name = entry.get('name', os.path.basename(entry.get('path', 'Unknown')))
                success = entry.get('success', False)
                
                icon = "✅" if success else "❌"
                print(f"  {icon} [{timestamp}] {name}")
                
                if not success and 'error' in entry:
                    print(f"     Errore: {entry['error']}")
            
            print(f"\n{'='*70}\n")
            
        except Exception as e:
            print(f"❌ Errore nella lettura del log: {e}")
    
    def esegui(self):
        """Esegue il loop principale interattivo."""
        while True:
            self.mostra_menu_principale()
            
            try:
                scelta = input("\n🎯 Seleziona un'opzione (1-5): ").strip()
                
                if scelta == '1':
                    # File specifico
                    filepath = input("\n📄 Inserisci il percorso del file: ").strip()
                    if filepath and os.path.exists(filepath):
                        if self.conferma_eliminazione([filepath]):
                            self.elimina_files([filepath])
                    else:
                        print(f"\n❌ File non trovato: {filepath}")
                
                elif scelta == '2':
                    # Directory corrente
                    pattern = input("\n🔍 Pattern di ricerca (default: *.*): ").strip() or "*.*"
                    files = self.cerca_file(pattern=pattern)
                    selected = self.mostra_file_con_selezione(files)
                    if selected and self.conferma_eliminazione(selected):
                        self.elimina_files(selected)
                
                elif scelta == '3':
                    # Directory specifica
                    directory = input("\n📁 Inserisci il percorso della directory: ").strip()
                    if os.path.isdir(directory):
                        pattern = input("🔍 Pattern di ricerca (default: *.*): ").strip() or "*.*"
                        files = self.cerca_file(directory, pattern)
                        selected = self.mostra_file_con_selezione(files)
                        if selected and self.conferma_eliminazione(selected):
                            self.elimina_files(selected)
                    else:
                        print(f"\n❌ Directory non trovata: {directory}")
                
                elif scelta == '4':
                    # Visualizza log
                    self.visualizza_log()
                
                elif scelta == '5':
                    print("\n👋 Arrivederci!")
                    break
                
                else:
                    print("\n❌ Opzione non valida. Riprova.")
                
                # Pausa prima del prossimo menu
                if scelta != '5':
                    input("\n⏸️  Premi INVIO per continuare...")
                
            except KeyboardInterrupt:
                print("\n\n✋ Operazione interrotta.")
                break
            except Exception as e:
                print(f"\n❌ Errore: {e}")


def main():
    """Funzione principale."""
    print("\n" + "🚀 " * 35)
    print("\n  MYGEST - Gestione File Uploadati")
    print("  Elimina in modo sicuro i file dopo l'upload\n")
    print("🚀 " * 35)
    
    manager = FileCleanupManager()
    manager.esegui()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✋ Programma terminato.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERRORE CRITICO: {e}")
        sys.exit(1)
