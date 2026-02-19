"""
ViewSet per esplorazione filesystem (directory browser)
"""
import os
import logging
from pathlib import Path
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)


class FileSystemViewSet(viewsets.ViewSet):
    """
    ViewSet per esplorare il filesystem.
    
    Endpoints:
    - GET /filesystem/browse/?path=/path/to/dir - Lista contenuti directory
    - GET /filesystem/quick-access/ - Percorsi quick access
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def browse(self, request):
        """
        Lista contenuti di una directory.
        Query params:
        - path: percorso directory (default: home utente o root)
        - show_hidden: mostra file nascosti (default: false)
        """
        path_str = request.query_params.get('path', '')
        show_hidden = request.query_params.get('show_hidden', 'false').lower() == 'true'
        
        # Default path
        if not path_str:
            # Prova home utente, altrimenti /
            path_str = os.path.expanduser('~')
            if not os.path.exists(path_str):
                path_str = '/'
        
        try:
            path = Path(path_str).resolve()
            
            # Security: verifica che path esista e sia leggibile
            if not path.exists():
                return Response(
                    {'error': f'Percorso non esistente: {path}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if not path.is_dir():
                return Response(
                    {'error': f'Non è una directory: {path}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not os.access(path, os.R_OK):
                return Response(
                    {'error': f'Permessi di lettura negati: {path}'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Lista contenuti
            items = []
            
            try:
                for entry in os.scandir(path):
                    # Skip file nascosti se richiesto
                    if not show_hidden and entry.name.startswith('.'):
                        continue
                    
                    try:
                        stat = entry.stat()
                        
                        item = {
                            'name': entry.name,
                            'path': str(Path(entry.path).resolve()),
                            'is_dir': entry.is_dir(),
                            'is_file': entry.is_file(),
                            'size': stat.st_size if entry.is_file() else 0,
                            'modified': stat.st_mtime,
                            'readable': os.access(entry.path, os.R_OK),
                            'writable': os.access(entry.path, os.W_OK),
                        }
                        
                        # Conta elementi se è directory
                        if entry.is_dir():
                            try:
                                item['item_count'] = len(list(Path(entry.path).iterdir()))
                            except (PermissionError, OSError):
                                item['item_count'] = 0
                        
                        items.append(item)
                    
                    except (PermissionError, OSError) as e:
                        # Skip file/dir non accessibili
                        logger.debug(f"Skip {entry.name}: {e}")
                        continue
            
            except PermissionError:
                return Response(
                    {'error': f'Permessi negati per leggere directory: {path}'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Ordina: directory prima, poi alfabeticamente
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            
            # Parent directory
            parent = str(path.parent) if path.parent != path else None
            
            result = {
                'current_path': str(path),
                'parent_path': parent,
                'items': items,
                'total_items': len(items),
            }
            
            return Response(result)
        
        except Exception as e:
            logger.error(f"Errore browse directory {path_str}: {e}", exc_info=True)
            return Response(
                {'error': f'Errore durante esplorazione: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def quick_access(self, request):
        """
        Ritorna lista di percorsi quick access (home, mount points, etc)
        """
        quick_paths = []
        
        # Home utente
        home = os.path.expanduser('~')
        if os.path.exists(home):
            quick_paths.append({
                'name': 'Home',
                'path': home,
                'icon': 'home',
                'type': 'home',
            })
        
        # Root
        quick_paths.append({
            'name': 'Root /',
            'path': '/',
            'icon': 'folder',
            'type': 'root',
        })
        
        # /tmp
        if os.path.exists('/tmp'):
            quick_paths.append({
                'name': 'Temp',
                'path': '/tmp',
                'icon': 'folder',
                'type': 'temp',
            })
        
        # Mount points comuni
        mount_base = '/mnt'
        if os.path.exists(mount_base):
            try:
                for entry in os.scandir(mount_base):
                    if entry.is_dir() and os.access(entry.path, os.R_OK):
                        quick_paths.append({
                            'name': f'Mount: {entry.name}',
                            'path': str(Path(entry.path).resolve()),
                            'icon': 'storage',
                            'type': 'mount',
                        })
            except (PermissionError, OSError):
                pass
        
        # Media root (MyGest)
        from django.conf import settings
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if media_root and os.path.exists(media_root):
            quick_paths.append({
                'name': 'Media MyGest',
                'path': media_root,
                'icon': 'folder_special',
                'type': 'media',
            })
        
        return Response(quick_paths)
