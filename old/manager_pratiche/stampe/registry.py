from __future__ import annotations

import unicodedata
from typing import Callable, Dict, Tuple, Optional, Any
from reportlab.pdfgen.canvas import Canvas

# Firma attesa dei layout: (istanza, canvas, page_width, page_height) -> None
LayoutFn = Callable[[Any, Canvas, float, float], None]

_registry: Dict[Tuple[str, str], LayoutFn] = {}


def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def _slug_component(s: str) -> str:
    s = _strip_accents(s.strip().lower())
    out = []
    prev_us = False
    for ch in s:
        if ch.isalnum():
            out.append(ch)
            prev_us = False
        elif ch in (" ", "-", "/", "."):
            if not prev_us:
                out.append("_")
                prev_us = True
        # ignora altri simboli
    return "".join(out).strip("_")


def normalize_key(app_label: str, model: str) -> Tuple[str, str]:
    return _slug_component(app_label), _slug_component(model)


def register(app_label: str, model: str, layout: LayoutFn) -> None:
    key = normalize_key(app_label, model)
    _registry[key] = layout


def register_model(model_cls_or_instance: Any, layout: LayoutFn) -> None:
    """
    Shortcut che evita errori di battitura: usa _meta.app_label e _meta.model_name.
    Accetta sia classi che istanze Django.
    """
    meta = getattr(model_cls_or_instance, "_meta", None)
    if not meta:
        raise TypeError("register_model richiede un Model (classe o istanza) Django")
    register(meta.app_label, meta.model_name, layout)


def unregister(app_label: str, model: str) -> None:
    _registry.pop(normalize_key(app_label, model), None)


def clear() -> None:
    """Utile nei test o in reload devserver."""
    _registry.clear()


def get(app_label: str, model: str, default: Optional[LayoutFn] = None) -> Optional[LayoutFn]:
    return _registry.get(normalize_key(app_label, model), default)


def get_or_generic(app_label: str, model: str) -> LayoutFn:
    from .layouts import layout_generic  # import locale per evitare cicli
    return get(app_label, model, default=layout_generic)  # type: ignore[return-value]


# Registrazioni default
from .layouts import layout_documento, layout_unita_fisica  # noqa: E402

register("documenti", "documento", layout_documento)
register("archivio_fisico", "unitafisica", layout_unita_fisica)

__all__ = [
    "LayoutFn",
    "register",
    "register_model",
    "unregister",
    "clear",
    "get",
    "get_or_generic",
    "normalize_key",
]
