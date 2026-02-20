"""
Custom exceptions per il modulo documenti.
"""


class DuplicateDocumentError(Exception):
    """
    Eccezione sollevata quando viene rilevato un documento duplicato.
    
    Attributes:
        message: Messaggio di errore human-readable
        documento_esistente: Documento già presente nel sistema
        numero_cedolino: Numero cedolino duplicato (opzionale)
        data_ora_cedolino: Data/ora cedolino duplicato (opzionale)
        matched_fields: Lista campi che hanno generato il match
        confidence: Percentuale di confidence del match
    """
    
    def __init__(
        self,
        message: str,
        documento_esistente=None,
        numero_cedolino: str = None,
        data_ora_cedolino: str = None,
        matched_fields: list = None,
        confidence: float = 1.0
    ):
        self.message = message
        self.documento_esistente = documento_esistente
        self.numero_cedolino = numero_cedolino
        self.data_ora_cedolino = data_ora_cedolino
        self.matched_fields = matched_fields or []
        self.confidence = confidence
        super().__init__(self.message)
    
    def to_dict(self):
        """Restituisce rappresentazione dict per API response"""
        return {
            'error': self.message,
            'error_type': 'duplicate_document',
            'duplicate_info': {
                'codice': self.documento_esistente.codice if self.documento_esistente else None,
                'id': self.documento_esistente.id if self.documento_esistente else None,
                'numero_cedolino': self.numero_cedolino,
                'data_ora_cedolino': self.data_ora_cedolino,
                'matched_fields': self.matched_fields,
                'confidence': self.confidence,
            }
        }
