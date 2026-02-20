#!/usr/bin/env python3
"""
Script helper per gestire i token API dell'agent desktop.

Uso:
    python manage_agent_tokens.py list              # Lista tutti i token
    python manage_agent_tokens.py create <username> # Crea token per utente
    python manage_agent_tokens.py show <username>   # Mostra token utente
    python manage_agent_tokens.py delete <username> # Elimina token utente
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()


def list_tokens():
    """Lista tutti i token esistenti."""
    print("\n" + "="*70)
    print("TOKEN API ESISTENTI")
    print("="*70)
    
    tokens = Token.objects.select_related('user').all()
    
    if not tokens:
        print("Nessun token trovato.")
        return
    
    for token in tokens:
        print(f"\nUtente: {token.user.username}")
        print(f"Token:  {token.key}")
        print(f"Email:  {token.user.email}")
        print(f"Creato: {token.created}")
    
    print("\n" + "="*70)


def create_token(username):
    """Crea un token per l'utente specificato."""
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"❌ Errore: Utente '{username}' non trovato.")
        return False
    
    token, created = Token.objects.get_or_create(user=user)
    
    if created:
        print(f"\n✅ Token creato per {username}:")
        print(f"   {token.key}")
    else:
        print(f"\n⚠️  Token già esistente per {username}:")
        print(f"   {token.key}")
    
    print(f"\nPer avviare l'agent desktop:")
    print(f"python3 mygest_agent.py --server http://localhost:8000 --token {token.key}")
    
    return True


def show_token(username):
    """Mostra il token per l'utente specificato."""
    try:
        user = User.objects.get(username=username)
        token = Token.objects.get(user=user)
        
        print(f"\n{'='*70}")
        print(f"TOKEN PER {username}")
        print(f"{'='*70}")
        print(f"\nToken: {token.key}")
        print(f"Creato: {token.created}")
        print(f"\nComando per avviare l'agent:")
        print(f"python3 mygest_agent.py --server http://localhost:8000 --token {token.key}")
        print(f"{'='*70}\n")
        
    except User.DoesNotExist:
        print(f"❌ Errore: Utente '{username}' non trovato.")
        return False
    except Token.DoesNotExist:
        print(f"❌ Errore: Nessun token trovato per '{username}'.")
        print(f"Usa: python manage_agent_tokens.py create {username}")
        return False
    
    return True


def delete_token(username):
    """Elimina il token per l'utente specificato."""
    try:
        user = User.objects.get(username=username)
        token = Token.objects.get(user=user)
        
        confirm = input(f"⚠️  Eliminare il token per {username}? (s/n): ")
        if confirm.lower() == 's':
            token.delete()
            print(f"✅ Token eliminato per {username}")
            return True
        else:
            print("Operazione annullata.")
            return False
            
    except User.DoesNotExist:
        print(f"❌ Errore: Utente '{username}' non trovato.")
        return False
    except Token.DoesNotExist:
        print(f"❌ Errore: Nessun token trovato per '{username}'.")
        return False


def list_users():
    """Lista tutti gli utenti disponibili."""
    print("\n" + "="*70)
    print("UTENTI DISPONIBILI")
    print("="*70)
    
    users = User.objects.all()
    
    for user in users:
        has_token = Token.objects.filter(user=user).exists()
        token_status = "✅ Token presente" if has_token else "❌ Nessun token"
        
        print(f"\nUsername: {user.username}")
        print(f"Email:    {user.email}")
        print(f"Staff:    {'Sì' if user.is_staff else 'No'}")
        print(f"Token:    {token_status}")
    
    print("\n" + "="*70)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nComandi disponibili:")
        print("  list              - Lista tutti i token")
        print("  users             - Lista tutti gli utenti")
        print("  create <username> - Crea token per utente")
        print("  show <username>   - Mostra token utente")
        print("  delete <username> - Elimina token utente")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'list':
        list_tokens()
    
    elif command == 'users':
        list_users()
    
    elif command == 'create':
        if len(sys.argv) < 3:
            print("❌ Errore: Specifica username")
            print("Uso: python manage_agent_tokens.py create <username>")
            sys.exit(1)
        create_token(sys.argv[2])
    
    elif command == 'show':
        if len(sys.argv) < 3:
            print("❌ Errore: Specifica username")
            print("Uso: python manage_agent_tokens.py show <username>")
            sys.exit(1)
        show_token(sys.argv[2])
    
    elif command == 'delete':
        if len(sys.argv) < 3:
            print("❌ Errore: Specifica username")
            print("Uso: python manage_agent_tokens.py delete <username>")
            sys.exit(1)
        delete_token(sys.argv[2])
    
    else:
        print(f"❌ Comando sconosciuto: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
