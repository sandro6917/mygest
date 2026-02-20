#!/usr/bin/env python
"""
Script di test per verificare la connessione SMTP
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
import smtplib
import socket

def test_smtp_connection():
    """Test connessione SMTP diretta"""
    print("=" * 80)
    print("TEST CONNESSIONE SMTP")
    print("=" * 80)
    
    print(f"\nConfigurazione:")
    print(f"  Host: {settings.EMAIL_HOST}")
    print(f"  Port: {settings.EMAIL_PORT}")
    print(f"  Use SSL: {settings.EMAIL_USE_SSL}")
    print(f"  Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"  Username: {settings.EMAIL_HOST_USER}")
    print(f"  Timeout: {settings.EMAIL_TIMEOUT}")
    
    print(f"\n1. Test risoluzione DNS...")
    try:
        ip = socket.gethostbyname(settings.EMAIL_HOST)
        print(f"   ✅ DNS OK: {settings.EMAIL_HOST} -> {ip}")
    except socket.gaierror as e:
        print(f"   ❌ Errore DNS: {e}")
        return False
    
    print(f"\n2. Test connessione socket...")
    try:
        sock = socket.create_connection((settings.EMAIL_HOST, settings.EMAIL_PORT), timeout=10)
        print(f"   ✅ Socket connesso a {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        sock.close()
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"   ❌ Errore connessione socket: {e}")
        return False
    
    print(f"\n3. Test SMTP con SSL...")
    try:
        if settings.EMAIL_USE_SSL:
            server = smtplib.SMTP_SSL(
                settings.EMAIL_HOST, 
                settings.EMAIL_PORT, 
                timeout=settings.EMAIL_TIMEOUT
            )
        else:
            server = smtplib.SMTP(
                settings.EMAIL_HOST, 
                settings.EMAIL_PORT, 
                timeout=settings.EMAIL_TIMEOUT
            )
            if settings.EMAIL_USE_TLS:
                server.starttls()
        
        print(f"   ✅ Connessione SMTP stabilita")
        
        print(f"\n4. Test autenticazione...")
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print(f"   ✅ Autenticazione riuscita")
        
        server.quit()
        print(f"\n✅ TUTTI I TEST SUPERATI!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Errore autenticazione: {e}")
        print(f"      Verifica username e password")
        return False
    except smtplib.SMTPException as e:
        print(f"   ❌ Errore SMTP: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Errore generico: {type(e).__name__}: {e}")
        return False


def test_django_email():
    """Test invio email con Django"""
    print("\n" + "=" * 80)
    print("TEST INVIO EMAIL CON DJANGO")
    print("=" * 80)
    
    try:
        send_mail(
            subject='Test Email da MyGest',
            message='Questa è una email di test per verificare la configurazione SMTP.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        print("✅ Email inviata con successo!")
        print(f"   Controlla la casella: {settings.EMAIL_HOST_USER}")
        return True
    except Exception as e:
        print(f"❌ Errore invio email: {type(e).__name__}: {e}")
        return False


if __name__ == '__main__':
    print("\n🔍 Avvio test connessione SMTP...\n")
    
    smtp_ok = test_smtp_connection()
    
    if smtp_ok:
        print("\n" + "=" * 80)
        risposta = input("\nVuoi testare l'invio di una email reale? (s/n): ")
        if risposta.lower() in ['s', 'si', 'y', 'yes']:
            test_django_email()
    else:
        print("\n" + "=" * 80)
        print("⚠️  Connessione SMTP fallita. Possibili cause:")
        print("   1. Firewall che blocca la porta 465")
        print("   2. Server SMTP non raggiungibile dalla tua rete")
        print("   3. Credenziali errate")
        print("   4. Server SMTP richiede configurazione diversa")
        print("\n💡 Suggerimenti:")
        print("   - Verifica le credenziali email")
        print("   - Prova con porta 587 e TLS invece di 465 e SSL")
        print("   - Controlla il firewall/antivirus")
        print("   - Usa un VPN se sei su una rete aziendale")
        print("=" * 80)
