from __future__ import annotations


def app_name(request):
    rm = getattr(request, "resolver_match", None)
    app = ""
    if rm:
        app = rm.app_name or rm.namespace or ""
    name_map = {
        "anagrafiche": "Anagrafiche",
        "documenti": "Documenti",
        "fascicoli": "Fascicoli",
        "pratiche": "Pratiche",
    }
    return {"current_app_name": name_map.get(app, "")}


def breadcrumbs(request):
    crumbs = getattr(request, "breadcrumbs", [])
    return {"breadcrumbs": crumbs}