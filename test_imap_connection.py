#!/usr/bin/env python
"""
Script di diagnostica IMAP per MyGest
Testa la connessione al server IMAP per l'archiviazione email
"""
import os
import sys
import imaplib
import socket
from pathlib import Path

# Carica variabili d'ambiente da .env
from dotenv import load_dotenv

# Trova il file .env
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Configurazione da variabili d'ambiente
class Settings:
    IMAP_HOST = os.getenv('EMAIL_IMAP_HOST', 'imaps.aruba.it')
    IMAP_PORT = int(os.getenv('EMAIL_IMAP_PORT', '993'))
    IMAP_USE_SSL = True  # Sempre True per porta 993
    IMAP_USERNAME = os.getenv('EMAIL_IMAP_USER', os.getenv('EMAIL_HOST_USER', ''))
    IMAP_PASSWORD = os.getenv('EMAIL_IMAP_PASSWORD', os.getenv('EMAIL_HOST_PASSWORD', ''))
    IMAP_TIMEOUT = int(os.getenv('EMAIL_IMAP_TIMEOUT', os.getenv('EMAIL_TIMEOUT', '60')))
    EMAIL_IMAP_SENT_FOLDER = os.getenv('EMAIL_IMAP_SENT_FOLDER', 'Sent')

settings = Settings()


def test_imap_connection():
    """Testa la connessione IMAP"""
    print("=" * 80)
    print("TEST CONNESSIONE IMAP")
    print("=" * 80)
    
    host = settings.IMAP_HOST
    port = settings.IMAP_PORT
    username = settings.IMAP_USERNAME
    password = settings.IMAP_PASSWORD
    use_ssl = settings.IMAP_USE_SSL
    timeout = settings.IMAP_TIMEOUT
    
    print(f"\nConfigurazione:")
    print(f"  Host: {host}")
    print(f"  Porta: {port}")
    print(f"  Username: {username}")
    print(f"  Password: {'*' * len(password) if password else 'NON CONFIGURATA'}")
    print(f"  SSL: {use_ssl}")
    print(f"  Timeout: {timeout}s")
    print()
    
    try:
        print(f"[1/6] Test risoluzione DNS per {host}...")
        ip = socket.gethostbyname(host)
        print(f"      ✓ Risolto: {ip}")
        
        print(f"\n[2/6] Test connessione TCP a {host}:{port}...")
        sock = socket.create_connection((host, port), timeout=timeout)
        print(f"      ✓ Connessione TCP stabilita")
        sock.close()
        
        print(f"\n[3/6] Test connessione IMAP SSL...")
        if use_ssl:
            imap = imaplib.IMAP4_SSL(host, port, timeout=timeout)
            print(f"      ✓ Connessione IMAP SSL stabilita")
        else:
            imap = imaplib.IMAP4(host, port, timeout=timeout)
            print(f"      ✓ Connessione IMAP stabilita")
        
        print(f"\n[4/6] Test autenticazione...")
        imap.login(username, password)
        print(f"      ✓ Autenticazione riuscita")
        
        print(f"\n[5/6] Test lista cartelle...")
        status, folders = imap.list()
        if status == 'OK':
            print(f"      ✓ Trovate {len(folders)} cartelle")
            
            # Decodifica e mostra le cartelle principali
            folder_names = []
            for folder in folders[:10]:  # Prime 10 cartelle
                # Parsing della risposta IMAP
                folder_str = folder.decode() if isinstance(folder, bytes) else str(folder)
                # Estrai il nome della cartella (ultima parte dopo le virgolette)
                if '"' in folder_str:
                    parts = folder_str.split('"')
                    if len(parts) >= 4:
                        name = parts[-2]
                        folder_names.append(name)
            
            if folder_names:
                print(f"      Cartelle trovate: {', '.join(folder_names[:5])}")
                if len(folder_names) > 5:
                    print(f"                        ... e altre {len(folder_names) - 5}")
        else:
            print(f"      ⚠️  Impossibile ottenere lista cartelle")
        
        print(f"\n[6/6] Test accesso cartella 'Sent' (posta inviata)...")
        # Prova diverse varianti del nome della cartella Sent
        sent_folders = [
            settings.EMAIL_IMAP_SENT_FOLDER,
            'Sent',
            'INBOX.Sent',
            'Sent Items',
            'INBOX.Sent Items',
            'Posta inviata',
            'INBOX.Posta inviata',
        ]
        
        sent_found = False
        for sent_folder in sent_folders:
            try:
                status, data = imap.select(sent_folder, readonly=True)
                if status == 'OK':
                    # Conta messaggi
                    msg_count = data[0].decode() if data and data[0] else '0'
                    print(f"      ✓ Cartella '{sent_folder}' accessibile ({msg_count} messaggi)")
                    sent_found = True
                    break
            except:
                continue
        
        if not sent_found:
            print(f"      ⚠️  Nessuna cartella 'Sent' trovata con i nomi standard")
            print(f"      Suggerimento: verifica il nome esatto nel tuo client email")
        
        imap.logout()
        
        print("\n" + "=" * 80)
        print("✓ TUTTI I TEST SUPERATI - Server IMAP funzionante")
        print("=" * 80)
        return True
        
    except socket.gaierror as e:
        print(f"\n❌ ERRORE DNS: Impossibile risolvere {host}")
        print(f"   Dettagli: {e}")
        return False
        
    except socket.timeout as e:
        print(f"\n❌ ERRORE TIMEOUT: Il server non risponde entro {timeout}s")
        print(f"   Dettagli: {e}")
        print(f"\nSuggerimenti:")
        print(f"  - Aumentare IMAP_TIMEOUT nel file .env")
        print(f"  - Verificare firewall/proxy che potrebbero bloccare la porta {port}")
        return False
        
    except imaplib.IMAP4.error as e:
        error_msg = str(e)
        if 'authentication' in error_msg.lower() or 'login' in error_msg.lower():
            print(f"\n❌ ERRORE AUTENTICAZIONE: Username o password errati")
            print(f"   Dettagli: {e}")
            print(f"\nVerifica le credenziali in .env:")
            print(f"  IMAP_USERNAME={username}")
            print(f"  IMAP_PASSWORD=...")
        else:
            print(f"\n❌ ERRORE IMAP: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ ERRORE: {type(e).__name__}")
        print(f"   Dettagli: {e}")
        return False


def main():
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "DIAGNOSTICA IMAP - MyGest" + " " * 33 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    # Test connessione
    connection_ok = test_imap_connection()
    
    if not connection_ok:
        print("\n⚠️  La connessione IMAP ha fallito.")
        print("    Risolvi i problemi sopra indicati prima di procedere.")
        sys.exit(1)
    
    print("\n✅ Configurazione IMAP funzionante!")
    print("   Le email inviate verranno archiviate correttamente nella cartella Sent.")
    print()


if __name__ == "__main__":
    main()
