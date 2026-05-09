#!/usr/bin/env python
"""
Script di diagnostica SMTP per MyGest
Testa la connessione al server SMTP e l'invio di email di prova
"""
import os
import sys
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

# Carica variabili d'ambiente da .env
from dotenv import load_dotenv

# Trova il file .env
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Configurazione da variabili d'ambiente
class Settings:
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.aruba.it')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'false').lower() == 'true'
    EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '30'))
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

settings = Settings()


def test_smtp_connection():
    """Testa la connessione SMTP senza inviare email"""
    print("=" * 80)
    print("TEST CONNESSIONE SMTP")
    print("=" * 80)
    
    host = settings.EMAIL_HOST
    port = settings.EMAIL_PORT
    username = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD
    use_tls = settings.EMAIL_USE_TLS
    timeout = getattr(settings, 'EMAIL_TIMEOUT', 30)
    
    print(f"\nConfigurazione:")
    print(f"  Host: {host}")
    print(f"  Porta: {port}")
    print(f"  Username: {username}")
    print(f"  Password: {'*' * len(password) if password else 'NON CONFIGURATA'}")
    print(f"  TLS: {use_tls}")
    print(f"  Timeout: {timeout}s")
    print()
    
    try:
        print(f"[1/4] Test risoluzione DNS per {host}...")
        ip = socket.gethostbyname(host)
        print(f"      ✓ Risolto: {ip}")
        
        print(f"\n[2/4] Test connessione TCP a {host}:{port}...")
        sock = socket.create_connection((host, port), timeout=timeout)
        print(f"      ✓ Connessione TCP stabilita")
        sock.close()
        
        print(f"\n[3/4] Test handshake SMTP...")
        if use_tls:
            server = smtplib.SMTP(host, port, timeout=timeout)
            server.starttls()
            print(f"      ✓ TLS attivato")
        else:
            server = smtplib.SMTP_SSL(host, port, timeout=timeout)
            print(f"      ✓ SSL attivato")
        
        print(f"\n[4/4] Test autenticazione...")
        server.login(username, password)
        print(f"      ✓ Autenticazione riuscita")
        
        server.quit()
        
        print("\n" + "=" * 80)
        print("✓ TUTTI I TEST SUPERATI - Server SMTP funzionante")
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
        print(f"  - Aumentare EMAIL_TIMEOUT nel file .env")
        print(f"  - Verificare firewall/proxy che potrebbero bloccare la porta {port}")
        return False
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ ERRORE AUTENTICAZIONE: Username o password errati")
        print(f"   Dettagli: {e}")
        print(f"\nVerifica le credenziali in .env:")
        print(f"  EMAIL_HOST_USER={username}")
        print(f"  EMAIL_HOST_PASSWORD=...")
        return False
        
    except Exception as e:
        print(f"\n❌ ERRORE: {type(e).__name__}")
        print(f"   Dettagli: {e}")
        return False


def send_test_email(recipient=None):
    """Invia un'email di test"""
    if not recipient:
        recipient = input("\nInserisci email destinatario per test: ").strip()
        if not recipient:
            print("Destinatario non specificato, test annullato.")
            return False
    
    print("\n" + "=" * 80)
    print("TEST INVIO EMAIL")
    print("=" * 80)
    
    try:
        subject = f"Test MyGest SMTP - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message = (
            "Questa è un'email di test inviata da MyGest.\n\n"
            f"Timestamp: {datetime.now()}\n"
            f"Server SMTP: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}\n"
            f"Mittente: {settings.DEFAULT_FROM_EMAIL}\n\n"
            "Se ricevi questa email, la configurazione SMTP funziona correttamente!"
        )
        
        print(f"\nInvio email di test a: {recipient}")
        print(f"Da: {settings.DEFAULT_FROM_EMAIL}")
        print(f"Oggetto: {subject}")
        print()
        
        # Crea messaggio email
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = settings.DEFAULT_FROM_EMAIL
        msg['To'] = recipient
        
        # Connetti e invia
        if settings.EMAIL_USE_TLS:
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=settings.EMAIL_TIMEOUT)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=settings.EMAIL_TIMEOUT)
        
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print("✓ Email inviata con successo!")
        print(f"  Controlla la casella {recipient}")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ ERRORE nell'invio: {type(e).__name__}")
        print(f"   Dettagli: {e}")
        print("=" * 80)
        return False


def main():
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "DIAGNOSTICA SMTP - MyGest" + " " * 33 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    # Test connessione
    connection_ok = test_smtp_connection()
    
    if not connection_ok:
        print("\n⚠️  La connessione SMTP ha fallito.")
        print("    Risolvi i problemi sopra indicati prima di procedere.")
        sys.exit(1)
    
    # Chiedi se inviare email di test
    print()
    risposta = input("Vuoi inviare un'email di test? [s/N]: ").strip().lower()
    
    if risposta in ['s', 'si', 'sì', 'y', 'yes']:
        send_test_email()
    else:
        print("\nTest completato senza invio email.")
    
    print()


if __name__ == "__main__":
    main()
