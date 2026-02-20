"""
Custom decorators per le view di stampa che supportano sia sessioni Django che JWT tokens.
"""
from __future__ import annotations
from functools import wraps
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken


def login_required_or_jwt(view_func):
    """
    Decorator che permette l'accesso sia con sessione Django che con JWT token.
    Utile per endpoint che devono essere accessibili sia da browser (sessione)
    che da chiamate API/Axios (JWT).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 1. Controlla se c'è una sessione valida (login tradizionale)
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        
        # 2. Controlla se c'è un JWT token nell'header Authorization
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token_str = auth_header[7:]  # Rimuovi "Bearer "
            try:
                # Valida il token JWT
                token = AccessToken(token_str)
                user_id = token.get('user_id')
                
                # Recupera l'utente
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.filter(pk=user_id).first()
                
                if user and user.is_active:
                    # Imposta l'utente nella request (senza creare sessione)
                    request.user = user
                    return view_func(request, *args, **kwargs)
                    
            except (TokenError, InvalidToken, KeyError):
                pass  # Token non valido, prosegui con login_required
        
        # 3. Fallback: usa login_required standard (redirect a login)
        return login_required(view_func)(request, *args, **kwargs)
    
    return wrapper
