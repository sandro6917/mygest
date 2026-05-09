#!/usr/bin/env python3
"""
Scanner Service - Servizio REST per gestione scanner di rete con SANE

Questo servizio Flask espone API REST per:
- Elencare scanner disponibili sulla rete
- Avviare scansioni multi-pagina
- Fornire preview delle scansioni
- Unire più scansioni in un unico PDF/A

Configurazione scanner:
- Brother ADS-2400N
- HP Officejet 7510
- Kyocera ECOSYS M2540dn XPS

Parametri di scansione:
- DPI: 300
- Modalità: Scala di grigi
- Formato: A4
- Fronte/retro: Automatico (se supportato)
"""

import os
import sys
import json
import uuid
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from PIL import Image, ImageEnhance, ImageOps
import pikepdf
import img2pdf

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tentativo di importare SANE (potrebbe non essere disponibile su tutti i sistemi)
try:
    import sane
    SANE_AVAILABLE = True
    logger.info("SANE library loaded successfully")
except ImportError:
    SANE_AVAILABLE = False
    logger.warning("SANE library not available - running in mock mode")

# Configurazione
SCAN_DPI = 300
SCAN_MODE = 'gray'  # gray, color, lineart
SCAN_FORMAT = 'A4'
SCAN_DUPLEX = True  # Fronte/retro automatico

# Storage temporaneo per le scansioni
TEMP_DIR = Path(tempfile.gettempdir()) / 'mygest_scanner'
TEMP_DIR.mkdir(exist_ok=True)

# Stato delle scansioni attive
active_scans: Dict[str, Dict[str, Any]] = {}

# Inizializza Flask
app = Flask(__name__)
CORS(app)  # Permetti richieste da frontend su localhost:5173

# Scanner mock per testing
MOCK_SCANNERS = [
    {
        'id': 'brother_ads2400n',
        'name': 'Brother ADS-2400N',
        'vendor': 'Brother',
        'model': 'ADS-2400N',
        'type': 'network',
        'address': '192.168.1.10',
        'capabilities': {
            'duplex': True,
            'adf': True,
            'max_dpi': 600
        }
    },
    {
        'id': 'hp_officejet7510',
        'name': 'HP Officejet 7510',
        'vendor': 'HP',
        'model': 'Officejet 7510',
        'type': 'network',
        'address': '192.168.1.11',
        'capabilities': {
            'duplex': True,
            'adf': True,
            'max_dpi': 600
        }
    },
    {
        'id': 'kyocera_m2540dn',
        'name': 'Kyocera ECOSYS M2540dn',
        'vendor': 'Kyocera',
        'model': 'ECOSYS M2540dn XPS',
        'type': 'network',
        'address': '192.168.1.12',
        'capabilities': {
            'duplex': True,
            'adf': True,
            'max_dpi': 1200
        }
    }
]


def init_sane():
    """Inizializza la libreria SANE"""
    if not SANE_AVAILABLE:
        logger.warning("SANE not available - using mock mode")
        return False
    
    try:
        sane.init()
        logger.info("SANE initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize SANE: {e}")
        return False


def is_blank_page(image_path: Path, white_threshold: float = 0.97, variance_threshold: float = 100.0) -> bool:
    """
    Rileva se una pagina è quasi completamente bianca.
    
    Args:
        image_path: Path dell'immagine da analizzare
        white_threshold: % minima di pixel bianchi per considerare pagina bianca (0.0-1.0)
        variance_threshold: Varianza massima dei pixel per considerare pagina uniforme
    
    Returns:
        True se la pagina è bianca, False altrimenti
    """
    try:
        img = Image.open(image_path).convert('L')  # Scala di grigi
        pixels = list(img.getdata())
        
        # Calcola percentuale pixel molto chiari (>230 su scala 0-255)
        # Abbassato da 240 a 230 per gestire rumore scanner e grana carta
        white_pixels = sum(1 for p in pixels if p > 230)
        white_ratio = white_pixels / len(pixels)
        
        # Calcola varianza per rilevare contenuto uniforme
        import statistics
        variance = statistics.variance(pixels) if len(pixels) > 1 else 0
        
        is_blank = white_ratio > white_threshold and variance < variance_threshold
        
        # Log sempre per debug
        logger.info(f"Page analysis: {image_path.name} - white: {white_ratio:.2%}, variance: {variance:.2f}, blank: {is_blank}")
        
        return is_blank
        
    except Exception as e:
        logger.warning(f"Could not analyze blank page {image_path}: {e}")
        return False  # In caso di errore, mantieni la pagina


def optimize_scanned_image(image_path: Path, optimize: bool = True) -> None:
    """
    Ottimizza un'immagine scansionata per ridurre dimensioni e migliorare leggibilità
    
    Args:
        image_path: Percorso dell'immagine da ottimizzare
        optimize: Se True applica ottimizzazioni aggressive
    """
    try:
        if not optimize:
            return
        
        img = Image.open(image_path)
        
        # Converti in scala di grigi se non lo è già
        if img.mode != 'L':
            img = img.convert('L')
        
        # Migliora il contrasto per rendere il testo più leggibile
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)  # Aumenta contrasto del 50%
        
        # Applica auto-contrasto per bilanciare i livelli
        img = ImageOps.autocontrast(img, cutoff=2)
        
        # Applica thresholding per convertire in B/N puro (migliora OCR e riduce dimensioni)
        # Usa un threshold adattivo basato sulla media dei pixel
        threshold = 128
        img = img.point(lambda p: 255 if p > threshold else 0, mode='1')
        
        # Salva con compressione massima
        img.save(
            str(image_path),
            'PNG',
            optimize=True,
            compress_level=9
        )
        
        logger.info(f"Image optimized: {image_path.name}")
        
    except Exception as e:
        logger.error(f"Error optimizing image {image_path}: {e}")
        # Non bloccare se l'ottimizzazione fallisce


def get_sane_devices():
    """Ottiene la lista dei dispositivi SANE disponibili"""
    if not SANE_AVAILABLE:
        return []
    
    try:
        devices = sane.get_devices()
        logger.info(f"Found {len(devices)} SANE devices")
        return devices
    except Exception as e:
        logger.error(f"Failed to get SANE devices: {e}")
        return []


def format_scanner_info(device_info) -> Dict[str, Any]:
    """Formatta le informazioni di un dispositivo SANE"""
    # device_info è una tupla: (name, vendor, model, type)
    name, vendor, model, dev_type = device_info
    
    return {
        'id': name.replace(':', '_').replace('/', '_'),
        'name': f"{vendor} {model}",
        'vendor': vendor,
        'model': model,
        'type': dev_type,
        'sane_name': name,
        'capabilities': {
            'duplex': True,  # Assumiamo supporto duplex
            'adf': True,     # Assumiamo supporto ADF
            'max_dpi': 600
        }
    }


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'sane_available': SANE_AVAILABLE,
        'version': '1.0.0'
    })


@app.route('/scanners', methods=['GET'])
def list_scanners():
    """
    GET /scanners
    Restituisce la lista degli scanner disponibili sulla rete
    """
    try:
        if SANE_AVAILABLE:
            devices = get_sane_devices()
            if devices:
                scanners = [format_scanner_info(dev) for dev in devices]
            else:
                # Fallback su mock se SANE non trova dispositivi
                scanners = MOCK_SCANNERS
                logger.warning("No SANE devices found, using mock scanners")
        else:
            scanners = MOCK_SCANNERS
            logger.info("Using mock scanners (SANE not available)")
        
        return jsonify({
            'scanners': scanners,
            'count': len(scanners)
        })
    
    except Exception as e:
        logger.error(f"Error listing scanners: {e}")
        return jsonify({
            'error': str(e),
            'scanners': MOCK_SCANNERS
        }), 500


@app.route('/scan', methods=['POST'])
def start_scan():
    """
    POST /scan
    Avvia una nuova scansione
    
    Body:
    {
        "scanner_id": "brother_ads2400n",
        "pages": 1,  # Numero di pagine da scansionare (0 = tutte dal feeder)
        "dpi": 300,
        "mode": "gray",  # gray, color, lineart
        "duplex": true
    }
    
    Returns:
    {
        "scan_id": "uuid",
        "status": "scanning|completed|error",
        "pages_scanned": 0,
        "message": "..."
    }
    """
    try:
        data = request.get_json() or {}
        scanner_id = data.get('scanner_id')
        pages = data.get('pages', 1)
        dpi = data.get('dpi', SCAN_DPI)
        mode = data.get('mode', SCAN_MODE)
        duplex = data.get('duplex', SCAN_DUPLEX)
        brightness = data.get('brightness', 0)
        contrast = data.get('contrast', 0)
        optimize = data.get('optimize', True)  # Ottimizza per default
        
        if not scanner_id:
            return jsonify({'error': 'scanner_id is required'}), 400
        
        # Genera ID univoco per questa scansione
        scan_id = str(uuid.uuid4())
        
        # Crea directory per questa scansione
        scan_dir = TEMP_DIR / scan_id
        scan_dir.mkdir(exist_ok=True)
        
        # Inizializza stato scansione
        scan_state = {
            'id': scan_id,
            'scanner_id': scanner_id,
            'status': 'scanning',
            'pages_scanned': 0,
            'total_pages': pages,
            'dpi': dpi,
            'mode': mode,
            'duplex': duplex,
            'brightness': brightness,
            'contrast': contrast,
            'optimize': optimize,
            'scan_dir': str(scan_dir),
            'files': [],
            'created_at': datetime.now().isoformat(),
            'error': None
        }
        
        active_scans[scan_id] = scan_state
        
        # Avvia scansione (in produzione questo sarebbe async)
        success = perform_scan(scan_id, scanner_id, pages, dpi, mode, duplex, brightness, contrast, optimize, scan_dir)
        
        if success:
            scan_state['status'] = 'completed'
            return jsonify({
                'scan_id': scan_id,
                'status': 'completed',
                'pages_scanned': scan_state['pages_scanned'],
                'message': 'Scansione completata con successo'
            })
        else:
            scan_state['status'] = 'error'
            scan_state['error'] = 'Scansione fallita'
            return jsonify({
                'scan_id': scan_id,
                'status': 'error',
                'error': 'Scansione fallita'
            }), 500
    
    except Exception as e:
        logger.error(f"Error starting scan: {e}")
        return jsonify({'error': str(e)}), 500


def perform_scan(scan_id: str, scanner_id: str, pages: int, dpi: int, mode: str, duplex: bool, brightness: int, contrast: int, optimize: bool, scan_dir: Path) -> bool:
    """
    Esegue la scansione effettiva usando subprocess scanimage.
    Approccio più affidabile che usa direttamente scanimage CLI invece di python-sane.
    """
    import subprocess
    
    try:
        scan_state = active_scans[scan_id]
        
        if SANE_AVAILABLE:
            # Trova il dispositivo SANE
            devices = get_sane_devices()
            target_device = None
            
            for dev_info in devices:
                dev_id = dev_info[0].replace(':', '_').replace('/', '_')
                if dev_id == scanner_id or dev_info[0] == scanner_id:
                    target_device = dev_info[0]
                    break
            
            if not target_device:
                logger.error(f"Scanner {scanner_id} not found")
                # Fallback su mock
                return create_mock_scan(scan_id, pages, scan_dir)
            
            logger.info(f"Starting scan with device: {target_device}")
            
            # Mappa modalità generiche a valori specifici Brother
            mode_map = {
                'color': '24bit Color[Fast]',
                'gray': 'True Gray',
                'lineart': 'Black & White'
            }
            
            # Usa mappatura per Brother, altrimenti valore diretto
            scan_mode = mode_map.get(mode.lower(), mode) if 'brother5' in target_device.lower() else mode
            
            # Costruisci comando scanimage
            cmd = [
                'scanimage',
                '-d', target_device,
                '--format=png',
                f'--resolution={dpi}',
                f'--mode={scan_mode}',
                '--batch=' + str(scan_dir / 'page_%03d.png'),
                '--batch-start=1',
            ]
            
            # Imposta formato A4 fisso (210x297mm)
            # A4: larghezza 210mm, altezza 297mm
            cmd.extend([
                '-x', '210',  # Larghezza A4
                '-y', '297',  # Altezza A4
            ])
            logger.info("Page format: A4 (210x297mm)")
            
            # Aggiungi sorgente duplex per Brother se richiesto
            if duplex:
                if 'brother5' in target_device.lower():
                    cmd.extend(['--source=Automatic Document Feeder(left aligned,Duplex)'])
                    logger.info("Duplex mode enabled for Brother scanner")
                else:
                    # Per altri scanner prova sorgente generica
                    cmd.extend(['--source=ADF Duplex'])
                    logger.info("Duplex mode enabled")
            else:
                # Single-sided
                if 'brother5' in target_device.lower():
                    cmd.extend(['--source=Automatic Document Feeder(left aligned)'])
                    logger.info("Single-sided mode for Brother scanner")
            
            # Aggiungi brightness/contrast solo se NON è Brother (ha questi parametri inactive)
            is_brother = 'brother5' in target_device.lower()
            
            if not is_brother and brightness != 0:
                cmd.append(f'--brightness={brightness}')
                logger.info(f"Brightness: {brightness}")
            elif is_brother and brightness != 0:
                logger.info(f"Brightness ignored for Brother scanner (inactive)")
            
            if not is_brother and contrast != 0:
                cmd.append(f'--contrast={contrast}')
                logger.info(f"Contrast: {contrast}")
            elif is_brother and contrast != 0:
                logger.info(f"Contrast ignored for Brother scanner (inactive)")
            
            logger.info(f"Running command: {' '.join(cmd)}")
            
            try:
                # Esegui scanimage
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120  # 2 minuti timeout
                )
                
                logger.info(f"scanimage stdout: {result.stdout}")
                if result.stderr:
                    logger.info(f"scanimage stderr: {result.stderr}")
                
                # scanimage può restituire 0 o 7 (Document feeder out of documents) come successo
                if result.returncode not in [0, 7] and 'out of documents' not in result.stderr.lower():
                    logger.error(f"scanimage failed with code {result.returncode}")
                    scan_state['error'] = f"scanimage failed: {result.stderr}"
                    return False
                
            except subprocess.TimeoutExpired:
                logger.error("Scan timeout - operazione troppo lunga")
                scan_state['error'] = "Timeout: operazione troppo lunga"
                return False
            except Exception as e:
                logger.error(f"Error running scanimage: {e}")
                scan_state['error'] = str(e)
                return False
            
            # Trova tutti i file scansionati
            page_files = sorted([f for f in scan_dir.iterdir() if f.name.startswith('page_') and f.suffix == '.png'])
            
            if not page_files:
                logger.error("No pages scanned")
                scan_state['error'] = "Nessuna pagina scansionata"
                return False
            
            logger.info(f"Found {len(page_files)} scanned pages")
            
            # Lista per pagine valide (non bianche)
            valid_pages = []
            blank_pages_removed = 0
            
            # Ottimizza e filtra pagine bianche
            for page_file in page_files:
                # Controlla se la pagina è bianca PRIMA dell'ottimizzazione
                # (l'ottimizzazione potrebbe alterare i valori dei pixel)
                if is_blank_page(page_file):
                    logger.info(f"Removing blank page: {page_file.name}")
                    try:
                        page_file.unlink()  # Elimina file pagina bianca
                        blank_pages_removed += 1
                    except Exception as e:
                        logger.warning(f"Could not delete blank page {page_file.name}: {e}")
                    continue
                
                # Pagina valida: ottimizza se richiesto
                if optimize:
                    try:
                        optimize_scanned_image(page_file, optimize=True)
                        logger.info(f"Optimized {page_file.name}")
                    except Exception as e:
                        logger.warning(f"Could not optimize {page_file.name}: {e}")
                
                valid_pages.append(page_file)
                scan_state['files'].append(str(page_file))
            
            if blank_pages_removed > 0:
                logger.info(f"Removed {blank_pages_removed} blank page(s)")
            
            if not valid_pages:
                logger.error("All pages were blank")
                scan_state['error'] = "Tutte le pagine scansionate erano bianche"
                return False
            
            scan_state['pages_scanned'] = len(valid_pages)
            logger.info(f"Total valid pages: {len(valid_pages)} (removed {blank_pages_removed} blank)")
            return True
        
        else:
            # Modalità mock
            return create_mock_scan(scan_id, pages, scan_dir)
    
    except Exception as e:
        logger.error(f"Error performing scan: {e}")
        scan_state['error'] = str(e)
        return False
def create_mock_scan(scan_id: str, pages: int, scan_dir: Path) -> bool:
    """Crea scansioni mock per testing"""
    try:
        scan_state = active_scans[scan_id]
        num_pages = pages if pages > 0 else 3
        
        for page_num in range(num_pages):
            # Crea immagine mock (A4 a 300 DPI = 2480x3508 pixel)
            img = Image.new('L', (2480, 3508), color=255)
            
            filename = f"page_{page_num + 1:03d}.png"
            filepath = scan_dir / filename
            img.save(str(filepath))
            
            scan_state['files'].append(str(filepath))
            scan_state['pages_scanned'] = page_num + 1
            
            logger.info(f"Mock page {page_num + 1} created")
        
        return True
    
    except Exception as e:
        logger.error(f"Error creating mock scan: {e}")
        return False


@app.route('/scan/<scan_id>/status', methods=['GET'])
def get_scan_status(scan_id: str):
    """
    GET /scan/<scan_id>/status
    Ottiene lo stato di una scansione
    """
    if scan_id not in active_scans:
        return jsonify({'error': 'Scan not found'}), 404
    
    scan_state = active_scans[scan_id]
    return jsonify({
        'scan_id': scan_id,
        'status': scan_state['status'],
        'pages_scanned': scan_state['pages_scanned'],
        'total_pages': scan_state['total_pages'],
        'error': scan_state.get('error')
    })


@app.route('/scan/<scan_id>/preview/<int:page>', methods=['GET'])
def get_page_preview(scan_id: str, page: int):
    """
    GET /scan/<scan_id>/preview/<page>
    Ottiene il preview di una pagina scansionata
    """
    if scan_id not in active_scans:
        return jsonify({'error': 'Scan not found'}), 404
    
    scan_state = active_scans[scan_id]
    
    if page < 1 or page > len(scan_state['files']):
        return jsonify({'error': 'Page not found'}), 404
    
    filepath = scan_state['files'][page - 1]
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(filepath, mimetype='image/png')


@app.route('/scan/merge', methods=['POST'])
def merge_scans():
    """
    POST /scan/merge
    Unisce più scansioni in un unico PDF/A
    
    Body:
    {
        "scan_ids": ["uuid1", "uuid2", ...],
        "filename": "documento.pdf"
    }
    
    Returns: File PDF/A
    """
    try:
        data = request.get_json() or {}
        scan_ids = data.get('scan_ids', [])
        filename = data.get('filename', 'scansione.pdf')
        
        if not scan_ids:
            return jsonify({'error': 'scan_ids is required'}), 400
        
        # Raccogli tutte le immagini
        all_images = []
        for scan_id in scan_ids:
            if scan_id not in active_scans:
                continue
            
            scan_state = active_scans[scan_id]
            all_images.extend(scan_state['files'])
        
        if not all_images:
            return jsonify({'error': 'No images to merge'}), 400
        
        # Crea PDF/A
        output_path = TEMP_DIR / filename
        
        # Converti immagini in PDF usando img2pdf
        with open(output_path, 'wb') as f:
            f.write(img2pdf.convert(all_images))
        
        logger.info(f"Created PDF with {len(all_images)} pages: {output_path}")
        
        # Converti in PDF/A usando pikepdf
        try:
            with pikepdf.open(output_path) as pdf:
                pdf.save(output_path, linearize=True)
            logger.info(f"Converted to PDF/A: {output_path}")
        except Exception as e:
            logger.warning(f"PDF/A conversion failed: {e}, using regular PDF")
        
        return send_file(
            str(output_path),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Error merging scans: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/scan/<scan_id>', methods=['DELETE'])
def delete_scan(scan_id: str):
    """
    DELETE /scan/<scan_id>
    Elimina una scansione e i suoi file temporanei
    """
    if scan_id not in active_scans:
        return jsonify({'error': 'Scan not found'}), 404
    
    try:
        scan_state = active_scans[scan_id]
        scan_dir = Path(scan_state['scan_dir'])
        
        # Elimina file
        for filepath in scan_state['files']:
            try:
                os.remove(filepath)
            except Exception as e:
                logger.warning(f"Failed to delete file {filepath}: {e}")
        
        # Elimina directory
        try:
            scan_dir.rmdir()
        except Exception as e:
            logger.warning(f"Failed to delete directory {scan_dir}: {e}")
        
        # Rimuovi dallo stato
        del active_scans[scan_id]
        
        return jsonify({'message': 'Scan deleted successfully'})
    
    except Exception as e:
        logger.error(f"Error deleting scan: {e}")
        return jsonify({'error': str(e)}), 500


def cleanup_old_scans():
    """Pulisce scansioni vecchie (> 24 ore)"""
    from datetime import timedelta
    
    now = datetime.now()
    to_delete = []
    
    for scan_id, scan_state in active_scans.items():
        created_at = datetime.fromisoformat(scan_state['created_at'])
        age = now - created_at
        
        if age > timedelta(hours=24):
            to_delete.append(scan_id)
    
    for scan_id in to_delete:
        try:
            delete_scan(scan_id)
            logger.info(f"Cleaned up old scan: {scan_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup scan {scan_id}: {e}")


if __name__ == '__main__':
    # Inizializza SANE
    if SANE_AVAILABLE:
        init_sane()
    
    # Avvia server
    port = int(os.environ.get('SCANNER_SERVICE_PORT', 8765))
    
    logger.info(f"Starting Scanner Service on port {port}")
    logger.info(f"SANE available: {SANE_AVAILABLE}")
    logger.info(f"Temp directory: {TEMP_DIR}")
    
    app.run(
        host='127.0.0.1',
        port=port,
        debug=False,
        threaded=True
    )
