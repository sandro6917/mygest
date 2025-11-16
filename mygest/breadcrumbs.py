from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from django.urls import NoReverseMatch, reverse


@dataclass(slots=True)
class Breadcrumb:
    label: str
    url: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {"label": str(self.label), "url": str(self.url) if self.url else None}


def breadcrumb(label: str, url: str | None = None) -> Breadcrumb:
    return Breadcrumb(label=label, url=url)


def _home_url() -> str:
    try:
        return reverse("home")
    except NoReverseMatch:
        return "/"


def _normalize_item(item: object) -> dict[str, str | None] | None:
    if isinstance(item, Breadcrumb):
        return item.as_dict()
    if isinstance(item, dict):
        label = item.get("label") or item.get("title")
        url = item.get("url")
    elif isinstance(item, (list, tuple)):
        if not item:
            return None
        label = item[0]
        url = item[1] if len(item) > 1 else None
    else:
        label = item
        url = None
    if label in (None, ""):
        return None
    label_str = str(label)
    url_str = str(url) if url else None
    return {"label": label_str, "url": url_str}


def set_breadcrumbs(
    request,
    items: Sequence[object] | Iterable[object],
    *,
    include_home: bool = True,
    last_is_link: bool = False,
    home_label: str = "Home",
) -> list[dict[str, str | None]]:
    resolved: list[dict[str, str | None]] = []
    for item in items:
        normalized = _normalize_item(item)
        if normalized:
            resolved.append(normalized)
    if include_home:
        home = {"label": home_label, "url": _home_url()}
        if resolved:
            if resolved[0]["label"] == home_label:
                resolved[0] = home
            else:
                resolved.insert(0, home)
        else:
            resolved.append(home)
    if resolved and not last_is_link:
        resolved[-1]["url"] = None
    request.breadcrumbs = resolved
    return resolved


def get_breadcrumbs(request) -> list[dict[str, str | None]]:
    crumbs = getattr(request, "breadcrumbs", [])
    return list(crumbs)


class BreadcrumbsMixin:
    breadcrumbs: Sequence[object] = ()
    breadcrumbs_include_home: bool = True
    breadcrumbs_last_is_link: bool = False
    breadcrumbs_home_label: str = "Home"

    def get_breadcrumbs(self) -> Sequence[object]:
        return self.breadcrumbs

    def build_breadcrumbs(self, items: Sequence[object] | Iterable[object] | None = None) -> list[dict[str, str | None]]:
        resolved_items = items if items is not None else self.get_breadcrumbs()
        return set_breadcrumbs(
            self.request,
            resolved_items,
            include_home=self.breadcrumbs_include_home,
            last_is_link=self.breadcrumbs_last_is_link,
            home_label=self.breadcrumbs_home_label,
        )

    def get_context_data(self, **kwargs):  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = self.build_breadcrumbs()
        return context


__all__ = [
    "Breadcrumb",
    "BreadcrumbsMixin",
    "breadcrumb",
    "get_breadcrumbs",
    "set_breadcrumbs",
]
