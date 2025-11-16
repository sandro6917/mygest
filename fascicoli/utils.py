import os
from django.conf import settings
from typing import List, Optional

def ensure_archivio_path(cliente_code: str, titolario_path_parts: list[str], anno: int | None = None) -> str:
    """
    Crea (se non esistono) le directory dell’archivio cliente/titolario.

    Esempio:
        cliente_code = "ROSSIM"
        titolario_path_parts = ["03 - Amministrazione", "03.01 - Fatturazione clienti", "03.01.02 - Fatture ricevute"]
        anno = 2025
    Restituisce il percorso assoluto creato:
        /srv/archivio/ROSSIM/03 - Amministrazione/03.01 - Fatturazione clienti/03.01.02 - Fatture ricevute/2025
    """
    base = getattr(settings, "ARCHIVIO_BASE_PATH", "/srv/archivio")
    # crea il percorso cliente
    parts = [base, cliente_code] + titolario_path_parts
    if anno:
        parts.append(str(anno))
    path = os.path.join(*parts)
    os.makedirs(path, exist_ok=True)
    return path

def build_titolario_parts(voce) -> List[str]:
    """
    Ritorna la lista delle parti di path a partire dalla voce di titolario fino alla radice.
    Formato omogeneo: "<CODICE> - <TITOLO>" per ogni livello.
    """
    parts: List[str] = []
    node = voce
    while node:
        parts.insert(0, f"{node.codice} - {getattr(node, 'titolo', '')}")
        node = getattr(node, "parent", None)
    return parts
