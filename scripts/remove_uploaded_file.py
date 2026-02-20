#!/usr/bin/env python3
"""
Script per eliminare file dopo l'upload nell'archivio MyGest.

Questo script può essere utilizzato per eliminare automaticamente i file
dal filesystem locale dopo averli caricati nell'archivio documentale.

Uso:
    python remove_uploaded_file.py /percorso/al/file.pdf
    python remove_uploaded_file.py /percorso/al/file.pdf --force  # Salta conferma
"""

import os
import sys
import argparse
from pathlib import Path


def chiedi_conferma(filepath: str) -> bool:
    """
    Chiede conferma all'utente prima di eliminare il file.
    
    Args:
        filepath: Percorso del file da eliminare
        
    Returns:
        True se l'utente conferma, False altrimenti
    """
    print(f"\n{'='*60}")
    print(f"ATTENZIONE: Stai per eliminare il file:")
    print(f"  {filepath}")
    print(f"{'='*60}\n")
    
    # Mostra informazioni sul file
    try:
        file_stat = os.stat(filepath)
        file_size = file_stat.st_size
        
        # Formatta dimensione file
        if file_size < 1024:
            size_str = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.2f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.2f} MB"
            
        print(f"Dimensione: {size_str}")
        print(f"Percorso completo: {os.path.abspath(filepath)}")
        print()
    except Exception as e:
        print(f"Errore nel leggere le informazioni del file: {e}\n")
    
    # Chiedi conferma
    while True:
        risposta = input("Sei sicuro di voler eliminare questo file? (si/no): ").strip().lower()
        if risposta in ['si', 's', 'sì', 'y', 'yes']:
            return True
        elif risposta in ['no', 'n']:
            return False
        else:
            print("Risposta non valida. Digita 'si' o 'no'.")


def elimina_file(filepath: str, force: bool = False) -> bool:
    """
    Elimina un file dal filesystem dopo conferma dell'utente.
    
    Args:
        filepath: Percorso del file da eliminare
        force: Se True, salta la richiesta di conferma
        
    Returns:
        True se il file è stato eliminato, False altrimenti
    """
    # Verifica che il file esista
    if not os.path.exists(filepath):
        print(f"❌ ERRORE: Il file '{filepath}' non esiste.")
        return False
    
    # Verifica che sia effettivamente un file e non una directory
    if not os.path.isfile(filepath):
        print(f"❌ ERRORE: '{filepath}' non è un file.")
        return False
    
    # Chiedi conferma se non in modalità force
    if not force:
        if not chiedi_conferma(filepath):
            print("\n✋ Operazione annullata dall'utente.")
            return False
    
    # Tenta di eliminare il file
    try:
        os.remove(filepath)
        print(f"\n✅ File eliminato con successo: {filepath}")
        return True
    except PermissionError:
        print(f"\n❌ ERRORE: Permessi insufficienti per eliminare il file.")
        print(f"   Prova ad eseguire lo script con permessi elevati.")
        return False
    except Exception as e:
        print(f"\n❌ ERRORE durante l'eliminazione: {e}")
        return False


def elimina_file_multipli(filepaths: list, force: bool = False) -> dict:
    """
    Elimina più file dopo conferma.
    
    Args:
        filepaths: Lista di percorsi dei file da eliminare
        force: Se True, salta la richiesta di conferma
        
    Returns:
        Dizionario con risultati: {'eliminati': [...], 'falliti': [...]}
    """
    risultati = {
        'eliminati': [],
        'falliti': []
    }
    
    print(f"\n{'='*60}")
    print(f"Preparazione eliminazione di {len(filepaths)} file(s)")
    print(f"{'='*60}\n")
    
    for filepath in filepaths:
        if elimina_file(filepath, force):
            risultati['eliminati'].append(filepath)
        else:
            risultati['falliti'].append(filepath)
    
    # Mostra riepilogo
    print(f"\n{'='*60}")
    print("RIEPILOGO:")
    print(f"  ✅ File eliminati: {len(risultati['eliminati'])}")
    print(f"  ❌ File non eliminati: {len(risultati['falliti'])}")
    print(f"{'='*60}\n")
    
    return risultati


def main():
    """Funzione principale dello script."""
    parser = argparse.ArgumentParser(
        description='Elimina file dopo l\'upload nell\'archivio MyGest',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
  %(prog)s documento.pdf
  %(prog)s documento.pdf --force
  %(prog)s file1.pdf file2.pdf file3.pdf
  %(prog)s /percorso/completo/al/documento.pdf
        """
    )
    
    parser.add_argument(
        'files',
        nargs='+',
        help='File da eliminare (uno o più percorsi)'
    )
    
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Salta la richiesta di conferma'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Mostra informazioni dettagliate'
    )
    
    args = parser.parse_args()
    
    # Espandi i percorsi relativi
    filepaths = [os.path.abspath(f) for f in args.files]
    
    if args.verbose:
        print(f"File da processare: {len(filepaths)}")
        for fp in filepaths:
            print(f"  - {fp}")
    
    # Elimina i file
    if len(filepaths) == 1:
        success = elimina_file(filepaths[0], args.force)
        sys.exit(0 if success else 1)
    else:
        risultati = elimina_file_multipli(filepaths, args.force)
        sys.exit(0 if len(risultati['falliti']) == 0 else 1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✋ Operazione interrotta dall'utente (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ ERRORE CRITICO: {e}")
        sys.exit(1)
