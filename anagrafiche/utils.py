from __future__ import annotations
from django.db import IntegrityError
from .models import Anagrafica

def _alnum_upper(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isalnum()).upper()

def _pad(s: str, length: int, fill: str = "0") -> str:
    s = (s or "")[:length]
    return s + (fill * (length - len(s)))

def build_cli_base6(cliente: Anagrafica) -> str:
    tipo = getattr(cliente, "tipo", "") or ""
    if tipo == "PG":
        denom = _alnum_upper(getattr(cliente, "ragione_sociale", "") or getattr(cliente, "denominazione", ""))
        return _pad(denom, 6, "0")
    cogn = _alnum_upper(getattr(cliente, "cognome", ""))
    nome = _alnum_upper(getattr(cliente, "nome", ""))
    return _pad(cogn, 3, "0") + _pad(nome, 3, "0")

CLI_SUFFIX_WIDTH = 2

def get_or_generate_cli(cliente: Anagrafica) -> str:
    # se già valido, usa quello (ma non se inizia per "CLI")
    code = (getattr(cliente, "codice", None) or "").strip().upper()
    if (
        code
        and len(code) == 6 + CLI_SUFFIX_WIDTH
        and code[:6].isalnum()
        and code[-CLI_SUFFIX_WIDTH:].isdigit()
        and not code.startswith("CLI")  # <-- aggiunta questa condizione
    ):
        return code

    base6 = build_cli_base6(cliente)

    # trova max suffisso per base6
    qs = Anagrafica.objects.filter(
        codice__startswith=base6,
        codice__regex=rf"^{base6}\d{{{CLI_SUFFIX_WIDTH}}}$",
    ).values_list("codice", flat=True)

    max_n = 0
    for c in qs:
        try:
            n = int(c[-CLI_SUFFIX_WIDTH:])
            if n > max_n:
                max_n = n
        except ValueError:
            continue

    # tenta salvataggio con retry su collisione unique
    tries = 5
    n = max_n
    while tries > 0:
        n += 1
        candidate = f"{base6}{n:0{CLI_SUFFIX_WIDTH}d}"
        if not code:
            try:
                cliente.codice = candidate
                cliente.save(update_fields=["codice"])
                return candidate
            except IntegrityError:
                tries -= 1
                continue
        else:
            return candidate
    # fallback: restituisci l’ultimo candidate anche se non salvato
    return f"{base6}{n:0{CLI_SUFFIX_WIDTH}d}"
