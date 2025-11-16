from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.template import Context, Template
from django.utils.html import linebreaks, strip_tags

from .models_template import FirmaComunicazione, TemplateComunicazione


@dataclass(frozen=True)
class RenderedComunicazione:
    oggetto: str
    corpo_testo: str
    corpo_html: str | None


def _render_template_string(source: str, ctx: Context) -> str:
    tpl = Template(source or "")
    return tpl.render(ctx).strip()


def render_template_comunicazione(
    template: TemplateComunicazione,
    context_dict: dict[str, Any] | None = None,
    comunicazione=None,
) -> RenderedComunicazione:
    """Renderizza il template restituendo sia la versione testo che quella HTML.

    Se viene fornita una comunicazione, il contesto base include i dati dinamici del template.
    """

    if comunicazione is not None:
        context_data = comunicazione.get_template_context(extra=context_dict)
    else:
        context_data = context_dict or {}
    context = Context(context_data)
    oggetto = _render_template_string(template.oggetto or "", context)
    corpo_testo = _render_template_string(template.corpo_testo or "", context)
    corpo_html_raw = _render_template_string(template.corpo_html or "", context)
    corpo_html = corpo_html_raw or None
    if not corpo_testo and corpo_html:
        corpo_testo = strip_tags(corpo_html).strip()
    return RenderedComunicazione(oggetto=oggetto, corpo_testo=corpo_testo, corpo_html=corpo_html)


def render_firma_comunicazione(
    firma: FirmaComunicazione,
    context_dict: dict[str, Any] | None = None,
) -> RenderedComunicazione:
    context = Context(context_dict or {})
    corpo_testo = _render_template_string(firma.corpo_testo or "", context)
    corpo_html_raw = _render_template_string(firma.corpo_html or "", context)
    corpo_html = corpo_html_raw or None
    if not corpo_testo and corpo_html:
        corpo_testo = strip_tags(corpo_html).strip()
    return RenderedComunicazione(oggetto="", corpo_testo=corpo_testo, corpo_html=corpo_html)


def merge_contenuti(
    contenuto: RenderedComunicazione,
    firma: RenderedComunicazione | None = None,
) -> RenderedComunicazione:
    """Combina contenuto principale e firma, mantenendo testo e HTML coerenti."""

    base_testo = (contenuto.corpo_testo or "").strip()
    base_html = (contenuto.corpo_html or "").strip() if contenuto.corpo_html else None

    if firma is None:
        testo_finale = base_testo
        html_finale = base_html or (linebreaks(base_testo) if base_testo else None)
        return RenderedComunicazione(oggetto=contenuto.oggetto, corpo_testo=testo_finale, corpo_html=html_finale)

    firma_testo = (firma.corpo_testo or "").strip()
    firma_html = (firma.corpo_html or "").strip() if firma.corpo_html else None

    testo_finale = base_testo
    if firma_testo:
        testo_finale = f"{testo_finale}\n\n{firma_testo}".strip() if testo_finale else firma_testo

    html_finale = base_html or (linebreaks(base_testo) if base_testo else None)
    if firma_html:
        if html_finale:
            html_finale = f"{html_finale}\n{firma_html}".strip()
        else:
            html_finale = firma_html
    elif firma_testo:
        firma_html_convertita = linebreaks(firma_testo)
        if html_finale:
            html_finale = f"{html_finale}\n{firma_html_convertita}".strip()
        else:
            html_finale = firma_html_convertita

    if not html_finale and testo_finale:
        html_finale = linebreaks(testo_finale)

    return RenderedComunicazione(oggetto=contenuto.oggetto, corpo_testo=testo_finale, corpo_html=html_finale)
