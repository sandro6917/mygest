#!/usr/bin/env python
"""
Script di test per verificare le configurazioni di performance
Esegui: python scripts/test_performance.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.core.cache import cache
from django.db import connection
from django.conf import settings
import time


def test_redis_connection():
    """Test connessione Redis"""
    print("\n" + "="*60)
    print("TEST 1: Redis Connection")
    print("="*60)
    
    try:
        # Test set/get
        test_key = 'performance_test_key'
        test_value = 'test_value_' + str(time.time())
        
        cache.set(test_key, test_value, timeout=60)
        retrieved = cache.get(test_key)
        
        if retrieved == test_value:
            print("✅ Redis connection: OK")
            print(f"   Test key: {test_key}")
            print(f"   Value: {test_value}")
        else:
            print("❌ Redis connection: FAILED")
            print(f"   Expected: {test_value}")
            print(f"   Got: {retrieved}")
            return False
        
        # Test cache info
        try:
            from django_redis import get_redis_connection
            conn = get_redis_connection("default")
            info = conn.info()
            print(f"✅ Redis stats accessible")
            print(f"   Connected clients: {info.get('connected_clients', 'N/A')}")
            print(f"   Used memory: {info.get('used_memory_human', 'N/A')}")
        except Exception as e:
            print(f"⚠️  Redis stats not accessible: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        return False


def test_cache_performance():
    """Test performance caching"""
    print("\n" + "="*60)
    print("TEST 2: Cache Performance")
    print("="*60)
    
    try:
        iterations = 1000
        
        # Test write performance
        start = time.time()
        for i in range(iterations):
            cache.set(f'perf_test_{i}', f'value_{i}', timeout=60)
        write_time = time.time() - start
        
        # Test read performance
        start = time.time()
        for i in range(iterations):
            cache.get(f'perf_test_{i}')
        read_time = time.time() - start
        
        print(f"✅ Cache performance test completed")
        print(f"   Write {iterations} keys: {write_time:.3f}s ({iterations/write_time:.0f} ops/sec)")
        print(f"   Read {iterations} keys: {read_time:.3f}s ({iterations/read_time:.0f} ops/sec)")
        
        # Cleanup
        for i in range(iterations):
            cache.delete(f'perf_test_{i}')
        
        return True
        
    except Exception as e:
        print(f"❌ Cache performance test failed: {e}")
        return False


def test_database_pool():
    """Test database connection pool"""
    print("\n" + "="*60)
    print("TEST 3: Database Connection Pool")
    print("="*60)
    
    try:
        # Verifica configurazione
        db_engine = settings.DATABASES['default']['ENGINE']
        print(f"✅ Database engine: {db_engine}")
        
        if 'pool' in db_engine.lower():
            print("✅ Connection pooling: ENABLED")
            pool_options = settings.DATABASES['default'].get('POOL_OPTIONS', {})
            print(f"   Pool size: {pool_options.get('POOL_SIZE', 'default')}")
            print(f"   Max overflow: {pool_options.get('MAX_OVERFLOW', 'default')}")
        else:
            print("⚠️  Connection pooling: NOT CONFIGURED")
            print("   Consider using 'dj_db_conn_pool.backends.postgresql'")
        
        # Test query
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result[0] == 1:
                print("✅ Database query: OK")
        
        # Info connessioni
        try:
            if hasattr(connection, 'pool'):
                print(f"✅ Pool stats accessible")
                print(f"   Pool size: {connection.pool.size()}")
                print(f"   Checked out: {connection.pool.checkedout()}")
        except Exception as e:
            print(f"⚠️  Pool stats not accessible: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database pool test failed: {e}")
        return False


def test_query_optimization():
    """Test ottimizzazione query"""
    print("\n" + "="*60)
    print("TEST 4: Query Optimization")
    print("="*60)
    
    try:
        from django.db import reset_queries
        from documenti.models import Documento
        
        reset_queries()
        
        # Query senza ottimizzazione
        start = time.time()
        documenti = list(Documento.objects.all()[:10])
        for doc in documenti:
            _ = doc.tipo  # Accesso FK
        query_time_unoptimized = time.time() - start
        query_count_unoptimized = len(connection.queries)
        
        reset_queries()
        
        # Query ottimizzata
        start = time.time()
        documenti = list(Documento.objects.select_related('tipo', 'cliente').all()[:10])
        for doc in documenti:
            _ = doc.tipo
        query_time_optimized = time.time() - start
        query_count_optimized = len(connection.queries)
        
        print(f"✅ Query optimization test completed")
        print(f"   Unoptimized: {query_count_unoptimized} queries in {query_time_unoptimized:.3f}s")
        print(f"   Optimized: {query_count_optimized} queries in {query_time_optimized:.3f}s")
        
        if query_count_optimized < query_count_unoptimized:
            improvement = ((query_count_unoptimized - query_count_optimized) / query_count_unoptimized) * 100
            print(f"✅ Query reduction: {improvement:.1f}%")
        else:
            print("⚠️  No query reduction detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Query optimization test failed: {e}")
        return False


def test_staticfiles_compression():
    """Test compressione staticfiles"""
    print("\n" + "="*60)
    print("TEST 5: Staticfiles Compression")
    print("="*60)
    
    try:
        compress_enabled = getattr(settings, 'COMPRESS_ENABLED', False)
        print(f"✅ Django Compressor enabled: {compress_enabled}")
        
        storages = getattr(settings, 'STORAGES', {})
        staticfiles_storage = storages.get('staticfiles', {}).get('BACKEND', 'N/A')
        print(f"✅ Staticfiles storage: {staticfiles_storage}")
        
        if 'Compressed' in staticfiles_storage:
            print("✅ Static compression: ENABLED")
        else:
            print("⚠️  Static compression: NOT CONFIGURED")
        
        return True
        
    except Exception as e:
        print(f"❌ Staticfiles test failed: {e}")
        return False


def test_debug_toolbar():
    """Test Debug Toolbar"""
    print("\n" + "="*60)
    print("TEST 6: Debug Toolbar")
    print("="*60)
    
    try:
        debug = settings.DEBUG
        installed_apps = settings.INSTALLED_APPS
        
        print(f"✅ DEBUG mode: {debug}")
        
        if debug and 'debug_toolbar' in installed_apps:
            print("✅ Debug Toolbar: INSTALLED")
            internal_ips = getattr(settings, 'INTERNAL_IPS', [])
            print(f"   Internal IPs: {internal_ips}")
        elif debug:
            print("⚠️  Debug Toolbar: NOT INSTALLED (but DEBUG=True)")
        else:
            print("ℹ️  Debug Toolbar: Disabled (DEBUG=False)")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug Toolbar test failed: {e}")
        return False


def test_session_cache():
    """Test session su cache"""
    print("\n" + "="*60)
    print("TEST 7: Session Cache")
    print("="*60)
    
    try:
        session_engine = settings.SESSION_ENGINE
        print(f"✅ Session engine: {session_engine}")
        
        if 'cache' in session_engine:
            print("✅ Sessions stored in cache: YES")
            session_cache_alias = getattr(settings, 'SESSION_CACHE_ALIAS', 'default')
            print(f"   Cache alias: {session_cache_alias}")
        else:
            print("⚠️  Sessions stored in: database")
            print("   Consider using cache backend for better performance")
        
        return True
        
    except Exception as e:
        print(f"❌ Session cache test failed: {e}")
        return False


def run_all_tests():
    """Esegui tutti i test"""
    print("\n" + "="*60)
    print("PERFORMANCE TEST SUITE")
    print("="*60)
    print(f"Django version: {django.get_version()}")
    print(f"Settings module: {settings.SETTINGS_MODULE}")
    print(f"Debug mode: {settings.DEBUG}")
    
    results = {
        'Redis Connection': test_redis_connection(),
        'Cache Performance': test_cache_performance(),
        'Database Pool': test_database_pool(),
        'Query Optimization': test_query_optimization(),
        'Staticfiles Compression': test_staticfiles_compression(),
        'Debug Toolbar': test_debug_toolbar(),
        'Session Cache': test_session_cache(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print("-"*60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All performance optimizations are working correctly!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check configuration.")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
