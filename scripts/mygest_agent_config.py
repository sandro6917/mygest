#!/usr/bin/env python3
"""
MyGest Agent - Configurazione da file

Legge configurazione da file INI per:
- Cartelle monitorate
- Path protetti
- Parametri agent
"""

import os
import configparser
from pathlib import Path
from typing import List, Optional


def load_config(config_path: Optional[str] = None) -> configparser.ConfigParser:
    """
    Carica configurazione da file.
    
    Args:
        config_path: Path file config (default: ~/.mygest-agent.conf)
        
    Returns:
        ConfigParser con configurazione
    """
    if config_path is None:
        config_path = os.path.expanduser('~/.mygest-agent.conf')
    
    config = configparser.ConfigParser()
    
    # Defaults
    config['server'] = {
        'url': 'http://localhost:8000',
        'token': ''
    }
    config['agent'] = {
        'poll_interval': '30',
        'cache_retention_hours': '24'
    }
    config['folders'] = {}
    config['protection'] = {}
    config['logging'] = {
        'level': 'INFO',
        'file': '~/.mygest-agent.log',
        'max_size_mb': '10',
        'backup_count': '3'
    }
    
    # Leggi file se esiste
    if os.path.exists(config_path):
        config.read(config_path)
        print(f"✓ Configurazione caricata da: {config_path}")
    else:
        print(f"⚠ File config non trovato: {config_path}")
        print(f"  Usando configurazione default")
    
    return config


def get_monitored_folders(config: configparser.ConfigParser) -> List[str]:
    """
    Estrae lista cartelle monitorate da config.
    
    Returns:
        Lista path cartelle da monitorare
    """
    folders = []
    
    if 'folders' in config:
        for key, value in config['folders'].items():
            if key.startswith('monitor_') and value.strip():
                # Espandi ~
                path = os.path.expanduser(value.strip())
                
                # Converti path Windows in WSL se necessario
                path = convert_windows_to_wsl(path)
                
                if os.path.exists(path):
                    folders.append(path)
                    print(f"  ✓ Cartella monitorata: {path}")
                else:
                    print(f"  ⚠ Cartella non esiste (ignorata): {path}")
    
    if not folders:
        # Fallback cartelle default
        default_user = os.environ.get('USER', 'user')
        defaults = [
            f'/mnt/c/Users/{default_user}/Downloads',
            f'/mnt/c/Users/{default_user}/Desktop',
            f'/mnt/c/Users/{default_user}/Documents',
        ]
        folders = [f for f in defaults if os.path.exists(f)]
        print(f"  ℹ Usando cartelle default: {len(folders)} trovate")
    
    return folders


def get_protected_paths(config: configparser.ConfigParser) -> List[str]:
    """
    Estrae lista path protetti da config.
    
    Returns:
        Lista path protetti
    """
    protected = []
    
    if 'protection' in config:
        for key, value in config['protection'].items():
            if key.startswith('protected_path') and value.strip():
                path = value.strip()
                protected.append(path)
    
    if not protected:
        # Defaults sicurezza
        protected = [
            '/mnt/archivio',
            '/home',
            '/var/www',
            '/usr',
            '/bin',
            '/sbin',
            '/etc',
        ]
    
    print(f"  🛡️  {len(protected)} path protetti configurati")
    return protected


def convert_windows_to_wsl(path: str) -> str:
    """
    Converte path Windows in WSL.
    
    Args:
        path: Path potenzialmente Windows (C:\\..., G:\\...)
        
    Returns:
        Path WSL (/mnt/c/..., /mnt/g/...)
    """
    # Già WSL
    if path.startswith('/mnt/') or path.startswith('/'):
        return path
    
    # Path Windows (C:\... o C:/...)
    import re
    match = re.match(r'^([A-Za-z]):[/\\](.*)', path)
    if match:
        drive, rest_path = match.groups()
        # Sostituisci backslash con slash
        unix_path = rest_path.replace('\\', '/')
        return f'/mnt/{drive.lower()}/{unix_path}'
    
    return path


# Esempio uso nel main dell'agent
def create_agent_from_config(config_path: Optional[str] = None):
    """
    Crea dati configurazione agent da file.
    
    Args:
        config_path: Path file config
        
    Returns:
        Dict con parametri configurazione
    """
    config = load_config(config_path)
    
    # Parametri server
    server_url = config['server']['url']
    api_token = config['server']['token']
    
    if not api_token:
        raise ValueError("Token API non configurato nel file config")
    
    # Parametri agent
    poll_interval = config.getint('agent', 'poll_interval', fallback=30)
    cache_retention_hours = config.getint('agent', 'cache_retention_hours', fallback=24)
    
    # Cartelle monitorate
    monitored_folders = get_monitored_folders(config)
    
    # Path protetti
    protected_paths = get_protected_paths(config)
    
    print(f"\n{'='*60}")
    print(f"Agent configurato:")
    print(f"  Server: {server_url}")
    print(f"  Poll interval: {poll_interval}s")
    print(f"  Cache retention: {cache_retention_hours}h")
    print(f"  Cartelle monitorate: {len(monitored_folders)}")
    print(f"  Path protetti: {len(protected_paths)}")
    print(f"{'='*60}\n")
    
    return {
        'server_url': server_url,
        'api_token': api_token,
        'poll_interval': poll_interval,
        'cache_retention_hours': cache_retention_hours,
        'monitored_folders': monitored_folders,
        'protected_paths': protected_paths
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='MyGest Agent - Con supporto file configurazione'
    )
    parser.add_argument(
        '--config',
        help='Path file configurazione (default: ~/.mygest-agent.conf)'
    )
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Mostra configurazione e esce'
    )
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    if args.show_config:
        print("\n=== CONFIGURAZIONE ===\n")
        for section in config.sections():
            print(f"[{section}]")
            for key, value in config[section].items():
                print(f"  {key} = {value}")
            print()
        
        print("=== CARTELLE MONITORATE ===")
        folders = get_monitored_folders(config)
        for folder in folders:
            print(f"  ✓ {folder}")
        
        print("\n=== PATH PROTETTI ===")
        protected = get_protected_paths(config)
        for path in protected:
            print(f"  🛡️  {path}")
        
        exit(0)
    
    # Crea e avvia agent
    agent = create_agent_from_config(args.config)
    agent.run()
