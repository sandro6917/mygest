#!/usr/bin/env python
"""
Script di avvio per Custom Agents MyGest

Usage:
    python run_agents.py                    # Carica config da configs/agents/
    python run_agents.py --config-dir PATH  # Carica config da directory custom
    python run_agents.py --agent-id ID      # Avvia solo un agent specifico
    python run_agents.py --list             # Lista agent disponibili
    python run_agents.py --create-examples  # Crea esempi di configurazione
"""

import sys
import signal
import time
import argparse
from pathlib import Path

# Aggiungi directory root al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_agents.manager import AgentManager
from custom_agents.registry import AgentRegistry
from custom_agents import examples
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Manager globale
manager: AgentManager = None


def signal_handler(sig, frame):
    """Handler per SIGINT (Ctrl+C)"""
    logger.info("\n\nInterruzione rilevata, arresto agent in corso...")
    if manager:
        manager.stop_all()
    logger.info("Tutti gli agent fermati. Uscita.")
    sys.exit(0)


def create_example_configs(output_dir: str):
    """Crea configurazioni di esempio"""
    logger.info(f"Creazione configurazioni di esempio in: {output_dir}")
    
    # Crea directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Crea agent di esempio
    example_agents = [
        examples.create_pdf_uploader_agent(),
        examples.create_cedolini_processor_agent(),
        examples.create_clienti_sync_agent(),
        examples.create_scadenze_reminder_agent(),
    ]
    
    # Salva configurazioni
    for agent in example_agents:
        # Determina tipo
        agent_type = agent.__class__.__name__.lower().replace('agent', '')
        filename = f"{agent.config.agent_id}.{agent_type}.json"
        filepath = Path(output_dir) / filename
        
        agent.config.save_to_json_file(str(filepath))
        logger.info(f"✓ Creato: {filepath}")
    
    logger.info(f"\n✅ Creati {len(example_agents)} file di configurazione")
    logger.info(f"\nPer avviare gli agent:")
    logger.info(f"  python run_agents.py --config-dir {output_dir}")


def list_available_agents():
    """Lista agent types disponibili"""
    logger.info("\n" + "="*80)
    logger.info("AGENT TYPES DISPONIBILI")
    logger.info("="*80)
    
    agent_types = AgentRegistry.list_agent_types()
    
    if not agent_types:
        logger.info("Nessun agent type registrato")
        return
    
    for i, agent_type in enumerate(agent_types, 1):
        agent_class = AgentRegistry.get_agent_type(agent_type)
        logger.info(f"\n{i}. {agent_type}")
        logger.info(f"   Classe: {agent_class.__name__}")
        if agent_class.__doc__:
            doc_lines = agent_class.__doc__.strip().split('\n')
            logger.info(f"   Descrizione: {doc_lines[0].strip()}")
    
    logger.info("\n" + "="*80 + "\n")


def main():
    """Main entry point"""
    global manager
    
    parser = argparse.ArgumentParser(
        description='MyGest Custom Agents Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  # Avvia tutti gli agent dalla directory default
  python run_agents.py
  
  # Avvia da directory custom
  python run_agents.py --config-dir /path/to/configs
  
  # Avvia solo un agent specifico
  python run_agents.py --agent-id pdf_uploader
  
  # Crea esempi di configurazione
  python run_agents.py --create-examples
  
  # Lista agent disponibili
  python run_agents.py --list
        """
    )
    
    parser.add_argument(
        '--config-dir',
        type=str,
        default='configs/agents',
        help='Directory con file di configurazione JSON (default: configs/agents)'
    )
    
    parser.add_argument(
        '--agent-id',
        type=str,
        help='Avvia solo l\'agent specificato'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='Lista agent types disponibili'
    )
    
    parser.add_argument(
        '--create-examples',
        action='store_true',
        help='Crea file di configurazione di esempio'
    )
    
    parser.add_argument(
        '--examples-dir',
        type=str,
        default='configs/agents/examples',
        help='Directory per configurazioni di esempio (default: configs/agents/examples)'
    )
    
    parser.add_argument(
        '--status-interval',
        type=int,
        default=300,
        help='Intervallo in secondi per stampare status (default: 300 = 5 minuti)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Abilita logging DEBUG'
    )
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Registra signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Lista agent types
    if args.list:
        list_available_agents()
        return
    
    # Crea esempi
    if args.create_examples:
        create_example_configs(args.examples_dir)
        return
    
    # Crea manager
    logger.info("="*80)
    logger.info("MYGEST CUSTOM AGENTS")
    logger.info("="*80)
    
    manager = AgentManager()
    
    # Carica configurazioni
    config_dir = Path(args.config_dir)
    
    if not config_dir.exists():
        logger.warning(f"Directory configurazioni non trovata: {config_dir}")
        logger.info(f"\nCrea configurazioni di esempio con:")
        logger.info(f"  python run_agents.py --create-examples")
        return
    
    loaded = manager.load_configs_from_directory(str(config_dir))
    
    if loaded == 0:
        logger.warning("Nessun agent caricato")
        logger.info(f"\nVerifica che in {config_dir} ci siano file .json")
        logger.info(f"Formato: {{agent_id}}.{{agent_type}}.json")
        return
    
    # Avvia agent
    if args.agent_id:
        # Avvia solo agent specifico
        logger.info(f"\nAvvio agent: {args.agent_id}")
        if manager.start_agent(args.agent_id):
            logger.info(f"✓ Agent {args.agent_id} avviato")
        else:
            logger.error(f"✗ Impossibile avviare agent {args.agent_id}")
            return
    else:
        # Avvia tutti
        logger.info(f"\nAvvio di {len(manager.list_agents())} agent...")
        manager.start_all()
    
    # Stampa status iniziale
    time.sleep(1)
    manager.print_status()
    
    # Main loop
    logger.info(f"\nAgent in esecuzione. Premi Ctrl+C per fermare.")
    logger.info(f"Status aggiornato ogni {args.status_interval} secondi.\n")
    
    try:
        while True:
            time.sleep(args.status_interval)
            manager.print_status()
            
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
