#!/usr/bin/env python
"""
Script per testare l'invio di una comunicazione specifica
con logging dettagliato
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from comunicazioni.models import Comunicazione
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils.html import strip_tags
from django.utils import timezone
import time

def test_send_comunicazione(comm_id):
    """Testa l'invio di una comunicazione specifica"""
    
    print(f"\n{'='*80}")
    print(f"TEST INVIO COMUNICAZIONE #{comm_id}")
    print(f"{'='*80}\n")
    
    # Carica comunicazione
    try:
        comunicazione = Comunicazione.objects.prefetch_related('allegati').get(id=comm_id)
    except Comunicazione.DoesNotExist:
        print(f"❌ Comunicazione #{comm_id} non trovata")
        return False
    
    print(f"Oggetto: {comunicazione.oggetto}")
    print(f"Destinatari: {comunicazione.destinatari}")
    print(f"Stato corrente: {comunicazione.stato}")
    print(f"Allegati: {comunicazione.allegati.count()}")
    print()
    
    # Configurazione
    print(f"Configurazione SMTP:")
    print(f"  Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"  SSL: {settings.EMAIL_USE_SSL}")
    print(f"  TLS: {settings.EMAIL_USE_TLS}")
    print(f"  Timeout: {settings.EMAIL_TIMEOUT}s")
    print(f"  User: {settings.EMAIL_HOST_USER}")
    print()
    
    # Prepara email
    print("[1/5] Preparazione email...")
    connection_kwargs = {}
    if settings.EMAIL_TIMEOUT:
        connection_kwargs["timeout"] = settings.EMAIL_TIMEOUT
    
    connection = get_connection(**connection_kwargs)
    corpo_testo = comunicazione.corpo or strip_tags(comunicazione.corpo_html or "")
    
    email = EmailMultiAlternatives(
        subject=comunicazione.oggetto,
        body=corpo_testo,
        from_email=comunicazione.mittente or settings.DEFAULT_FROM_EMAIL,
        to=comunicazione.get_destinatari_lista(),
        connection=connection,
    )
    
    if comunicazione.corpo_html:
        email.attach_alternative(comunicazione.corpo_html, "text/html")
    
    # Allegati
    print(f"[2/5] Caricamento {comunicazione.allegati.count()} allegati...")
    for allegato in comunicazione.allegati.all():
        try:
            file_path = allegato.get_file_path()
            filename = allegato.get_filename()
            
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                    email.attach(filename, content)
                    size_mb = len(content) / (1024 * 1024)
                    print(f"      ✓ {filename} ({size_mb:.2f} MB)")
        except Exception as e:
            print(f"      ✗ Errore allegato {allegato.id}: {e}")
    
    # Invio
    try:
        print(f"\n[3/5] Apertura connessione SMTP...")
        start_time = time.time()
        connection.open()
        elapsed = time.time() - start_time
        print(f"      ✓ Connessione aperta ({elapsed:.2f}s)")
        
        print(f"\n[4/5] Invio messaggio...")
        start_time = time.time()
        result = connection.send_messages([email])
        elapsed = time.time() - start_time
        print(f"      ✓ Messaggio inviato ({elapsed:.2f}s) - Risultato: {result}")
        
        connection.close()
        
        # Archiviazione IMAP (opzionale)
        print(f"\n[5/5] Archiviazione IMAP...")
        try:
            from comunicazioni.email_archiver import EmailAppendError, append_to_sent_folder
            start_time = time.time()
            append_to_sent_folder(email.message())
            elapsed = time.time() - start_time
            print(f"      ✓ Archiviato in IMAP ({elapsed:.2f}s)")
        except Exception as e:
            print(f"      ⚠️  Archiviazione IMAP fallita: {e}")
            print(f"      (L'email è stata comunque inviata)")
        
        # Aggiorna stato
        print(f"\n✅ EMAIL INVIATA CON SUCCESSO!")
        print(f"\nVuoi aggiornare lo stato a 'inviata'? [s/N]: ", end='')
        risposta = input().strip().lower()
        
        if risposta in ['s', 'si', 'sì', 'y', 'yes']:
            comunicazione.stato = "inviata"
            comunicazione.data_invio = timezone.now()
            comunicazione.log_errore = ""
            comunicazione.save(update_fields=["stato", "data_invio", "log_errore"])
            print(f"✓ Stato aggiornato")
        else:
            print(f"Stato NON aggiornato")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRORE DURANTE L'INVIO: {type(e).__name__}")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Test invio comunicazione')
    parser.add_argument('comm_id', type=int, help='ID della comunicazione da inviare')
    args = parser.parse_args()
    
    success = test_send_comunicazione(args.comm_id)
    sys.exit(0 if success else 1)
