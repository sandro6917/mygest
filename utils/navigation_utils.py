"""
Navigation Utilities - Funzioni per gestione navigazione intelligente
"""


def get_referrer_from_request(request):
    """
    Estrae l'URL referrer dalla richiesta HTTP.
    
    Args:
        request: Oggetto request Django
    
    Returns:
        str: URL referrer o None
    """
    return request.META.get('HTTP_REFERER')


def should_redirect_to_referrer(request, default_url='/'):
    """
    Determina se redirigere al referrer o a un URL di default.
    
    Args:
        request: Oggetto request Django
        default_url: URL di fallback (default: '/')
    
    Returns:
        str: URL a cui redirigere
    """
    referrer = get_referrer_from_request(request)
    
    if referrer and referrer.startswith(request.build_absolute_uri('/')):
        # Referrer è interno al sito
        return referrer
    
    return default_url


def build_back_url(request, fallback_url):
    """
    Costruisce l'URL "indietro" basato sul referrer o un fallback.
    
    Args:
        request: Oggetto request Django
        fallback_url: URL di fallback
    
    Returns:
        str: URL per il pulsante indietro
    """
    referrer = get_referrer_from_request(request)
    
    # Se c'è un referrer interno, usalo
    if referrer:
        host = request.get_host()
        if host in referrer:
            # Estrai il path dal referrer
            from urllib.parse import urlparse
            parsed = urlparse(referrer)
            return parsed.path
    
    # Altrimenti usa il fallback
    return fallback_url
