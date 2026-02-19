"""
Health Check API Endpoint
Fornisce informazioni sullo stato del sistema per monitoring e deploy automation
"""
from django.db import connections
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
import time


@never_cache
@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint per monitoring e deploy automation.
    
    Verifica:
    - Database connectivity
    - Cache (Redis) connectivity
    - Response time
    
    Returns:
        200 OK: Sistema operativo
        503 Service Unavailable: Sistema con problemi
    """
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "checks": {},
        "timestamp": time.time(),
    }
    
    status_code = 200
    
    # Check 1: Database
    try:
        connections['default'].ensure_connection()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connesso"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }
        health_status["status"] = "unhealthy"
        status_code = 503
    
    # Check 2: Cache (Redis)
    try:
        cache_key = "health_check_test"
        cache.set(cache_key, "ok", 10)
        cache_value = cache.get(cache_key)
        if cache_value == "ok":
            health_status["checks"]["cache"] = {
                "status": "healthy",
                "message": "Cache operativa"
            }
        else:
            raise Exception("Cache read/write mismatch")
    except Exception as e:
        health_status["checks"]["cache"] = {
            "status": "degraded",
            "message": f"Cache warning: {str(e)}"
        }
        # Cache non è critico, non cambiamo status
    
    # Response time
    response_time = (time.time() - start_time) * 1000  # ms
    health_status["response_time_ms"] = round(response_time, 2)
    
    return JsonResponse(health_status, status=status_code)


@never_cache
@require_http_methods(["GET"])
def ready_check(request):
    """
    Readiness probe - verifica se l'applicazione è pronta a ricevere traffico.
    Più leggero di health_check, solo per Kubernetes/container orchestration.
    """
    try:
        # Quick database check
        connections['default'].ensure_connection()
        return JsonResponse({"status": "ready"}, status=200)
    except Exception:
        return JsonResponse({"status": "not ready"}, status=503)


@never_cache
@require_http_methods(["GET"])
def live_check(request):
    """
    Liveness probe - verifica se l'applicazione è viva.
    Ritorna sempre 200 se Django risponde.
    """
    return JsonResponse({"status": "alive"}, status=200)
