"""
Extractor per testo da file PDF
"""
import logging
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Estrattore di testo da file PDF.
    Supporta PyPDF2 e pdfplumber (fallback automatico).
    """
    
    def __init__(self, max_pages: int = 10):
        """
        Inizializza l'estrattore PDF.
        
        Args:
            max_pages: Numero massimo di pagine da processare (per performance)
        """
        self.max_pages = max_pages
        
        # Verifica librerie disponibili
        if not PyPDF2 and not pdfplumber:
            raise ImportError(
                "Nessuna libreria PDF disponibile. "
                "Installa PyPDF2 o pdfplumber: pip install PyPDF2 pdfplumber"
            )
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Estrae testo da un PDF.
        
        Args:
            pdf_path: Path del file PDF
            
        Returns:
            Testo estratto (string)
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"File PDF non trovato: {pdf_path}")
        
        # Prova prima con pdfplumber (più accurato)
        if pdfplumber:
            try:
                return self._extract_with_pdfplumber(pdf_path)
            except Exception as e:
                logger.warning(f"pdfplumber fallito su {pdf_path}: {e}")
        
        # Fallback a PyPDF2
        if PyPDF2:
            try:
                return self._extract_with_pypdf2(pdf_path)
            except Exception as e:
                logger.error(f"PyPDF2 fallito su {pdf_path}: {e}")
                raise
        
        return ""
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """Estrazione con pdfplumber"""
        text_parts = []
        
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_process = min(len(pdf.pages), self.max_pages)
            
            for i in range(pages_to_process):
                page = pdf.pages[i]
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return "\n\n".join(text_parts)
    
    def _extract_with_pypdf2(self, pdf_path: str) -> str:
        """Estrazione con PyPDF2"""
        text_parts = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pages_to_process = min(len(pdf_reader.pages), self.max_pages)
            
            for i in range(pages_to_process):
                page = pdf_reader.pages[i]
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return "\n\n".join(text_parts)
    
    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Estrae metadata PDF (autore, creazione, titolo, etc.)
        
        Args:
            pdf_path: Path del file PDF
            
        Returns:
            Dict con metadata
        """
        metadata = {}
        
        try:
            if PyPDF2:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    pdf_info = pdf_reader.metadata
                    
                    if pdf_info:
                        metadata = {
                            'title': pdf_info.get('/Title', ''),
                            'author': pdf_info.get('/Author', ''),
                            'subject': pdf_info.get('/Subject', ''),
                            'creator': pdf_info.get('/Creator', ''),
                            'producer': pdf_info.get('/Producer', ''),
                            'creation_date': pdf_info.get('/CreationDate', ''),
                            'num_pages': len(pdf_reader.pages)
                        }
        except Exception as e:
            logger.warning(f"Impossibile estrarre metadata da {pdf_path}: {e}")
        
        return metadata
    
    def extract_text_sample(self, pdf_path: str, max_chars: int = 2000) -> str:
        """
        Estrae un campione di testo dal PDF (per preview/classificazione rapida).
        
        Args:
            pdf_path: Path del file PDF
            max_chars: Massimo numero di caratteri da estrarre
            
        Returns:
            Campione di testo
        """
        full_text = self.extract_text(pdf_path)
        return full_text[:max_chars] if full_text else ""
